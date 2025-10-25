"""
Suricata IDS Alert Processor - Faceless YouTube
Processes Suricata alerts, correlates events, and sends notifications to Alertmanager

Author: Faceless YouTube Team
Date: 2025-10-25
Status: Production
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import requests
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ============================================================================
# DATA MODELS
# ============================================================================

class SuricataAlert(BaseModel):
    """Parsed Suricata alert from eve.json"""

    timestamp: str
    event_type: str
    alert: Optional[Dict[str, Any]] = None
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    src_port: Optional[int] = None
    dest_port: Optional[int] = None
    proto: Optional[str] = None
    http: Optional[Dict[str, Any]] = None
    dns: Optional[Dict[str, Any]] = None
    tls: Optional[Dict[str, Any]] = None
    ssh: Optional[Dict[str, Any]] = None
    
    class Config:
        allow_population_by_field_name = True


class ThreatIntelligence(BaseModel):
    """Threat intelligence data for correlation"""

    ip_address: str
    threat_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    last_seen: datetime
    count: int = 0
    blocked: bool = False
    blacklist: bool = False


class AlertNotification(BaseModel):
    """Alert notification to send to Alertmanager"""

    status: str  # "firing" or "resolved"
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None


# ============================================================================
# IDS ALERT PROCESSOR
# ============================================================================

class IDSAlertProcessor:
    """
    Processes Suricata alerts and integrates with monitoring infrastructure.
    
    Responsibilities:
    - Parse Suricata eve.json logs in real-time
    - Correlate related alerts
    - Track threat indicators
    - Auto-respond to threats (IP blocking, rate limiting)
    - Send notifications to Alertmanager
    """

    def __init__(
        self,
        eve_log_path: str = "/var/log/suricata/eve.json",
        alertmanager_url: str = "http://alertmanager:9093/api/v1/alerts",
        max_threat_age_seconds: int = 3600,
        auto_blacklist_threshold: int = 5,
    ):
        """
        Initialize the IDS Alert Processor.
        
        Args:
            eve_log_path: Path to Suricata eve.json file
            alertmanager_url: URL to Alertmanager API
            max_threat_age_seconds: How long to track threat indicators
            auto_blacklist_threshold: Alert count before auto-blacklist
        """
        self.eve_log_path = Path(eve_log_path)
        self.alertmanager_url = alertmanager_url
        self.max_threat_age_seconds = max_threat_age_seconds
        self.auto_blacklist_threshold = auto_blacklist_threshold
        
        # Threat tracking
        self.threat_db: Dict[str, ThreatIntelligence] = {}
        self.alert_counts: Dict[str, int] = {}
        self.last_file_position = 0
        
        # Correlation windows (seconds)
        self.correlation_window = 30
        self.recent_alerts: List[SuricataAlert] = []
        
        logger.info(f"IDS Alert Processor initialized: {eve_log_path}")

    async def start(self, poll_interval: int = 5):
        """
        Start monitoring Suricata alerts continuously.
        
        Args:
            poll_interval: Seconds between file checks
        """
        logger.info(f"Starting IDS monitoring (poll interval: {poll_interval}s)")
        
        while True:
            try:
                await self._process_alerts()
                await self._cleanup_old_threats()
                await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}", exc_info=True)
                await asyncio.sleep(poll_interval)

    async def _process_alerts(self):
        """Read new alerts from eve.json and process them"""
        if not self.eve_log_path.exists():
            logger.warning(f"Eve log not found: {self.eve_log_path}")
            return

        try:
            async with aiofiles.open(self.eve_log_path, "r") as f:
                # Seek to last known position
                await f.seek(self.last_file_position)
                
                async for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        alert_data = json.loads(line)
                        alert = SuricataAlert(**alert_data)
                        
                        # Process different alert types
                        if alert.event_type == "alert":
                            await self._handle_alert(alert)
                        elif alert.event_type == "http":
                            await self._handle_http_event(alert)
                        elif alert.event_type == "dns":
                            await self._handle_dns_event(alert)
                        elif alert.event_type == "tls":
                            await self._handle_tls_event(alert)
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.debug(f"Failed to parse alert line: {e}")
                        continue
                
                # Update file position
                self.last_file_position = await f.tell()
                
        except IOError as e:
            logger.error(f"Error reading eve.json: {e}")

    async def _handle_alert(self, alert: SuricataAlert):
        """Handle a security alert"""
        if not alert.alert:
            return

        try:
            alert_msg = alert.alert.get("signature", "Unknown")
            sid = alert.alert.get("signature_id")
            category = alert.alert.get("category", "unknown")
            severity = self._classify_severity(sid, category)
            
            # Track threat indicator
            src_ip = alert.src_ip
            if src_ip:
                await self._track_threat(src_ip, category, severity)
                
                # Check for auto-blacklist
                if src_ip in self.threat_db:
                    threat = self.threat_db[src_ip]
                    if threat.count >= self.auto_blacklist_threshold and not threat.blacklist:
                        await self._blacklist_ip(src_ip, reason=alert_msg)
            
            # Create alert notification
            notification = await self._create_alert_notification(
                severity=severity,
                title=alert_msg,
                description=f"{category} from {src_ip}:{alert.src_port}",
                src_ip=src_ip,
                dest_ip=alert.dest_ip,
                sid=sid,
            )
            
            # Send to Alertmanager
            await self._send_to_alertmanager([notification])
            
            # Log alert
            logger.warning(
                f"[{severity}] {alert_msg} from {src_ip}:{alert.src_port} "
                f"to {alert.dest_ip}:{alert.dest_port}"
            )
            
            # Correlate with recent alerts
            self.recent_alerts.append(alert)
            await self._correlate_alerts()
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}", exc_info=True)

    async def _handle_http_event(self, alert: SuricataAlert):
        """Handle HTTP event (logging/analysis)"""
        if not alert.http:
            return

        try:
            method = alert.http.get("http_method", "UNKNOWN")
            uri = alert.http.get("uri", "")
            status = alert.http.get("status", 0)
            
            # Log suspicious HTTP patterns
            if self._is_suspicious_http(method, uri):
                logger.warning(
                    f"Suspicious HTTP: {method} {uri} from {alert.src_ip}"
                )
                
                # Create notification
                notification = await self._create_alert_notification(
                    severity="warning",
                    title="Suspicious HTTP Activity",
                    description=f"{method} {uri}",
                    src_ip=alert.src_ip,
                    dest_ip=alert.dest_ip,
                )
                await self._send_to_alertmanager([notification])
                
        except Exception as e:
            logger.error(f"Error handling HTTP event: {e}")

    async def _handle_dns_event(self, alert: SuricataAlert):
        """Handle DNS event"""
        if not alert.dns:
            return

        try:
            query = alert.dns.get("query", {}).get("rrname", "unknown")
            rtype = alert.dns.get("query", {}).get("rrtype", "A")
            
            # Check for DNS exfiltration patterns
            if self._is_suspicious_dns(query):
                logger.warning(
                    f"Suspicious DNS: {query} ({rtype}) from {alert.src_ip}"
                )
                
                notification = await self._create_alert_notification(
                    severity="warning",
                    title="Suspicious DNS Query",
                    description=f"{query} ({rtype})",
                    src_ip=alert.src_ip,
                )
                await self._send_to_alertmanager([notification])
                
        except Exception as e:
            logger.error(f"Error handling DNS event: {e}")

    async def _handle_tls_event(self, alert: SuricataAlert):
        """Handle TLS event (certificate analysis, etc)"""
        if not alert.tls:
            return

        try:
            issuer = alert.tls.get("issuerdn", "unknown")
            subject = alert.tls.get("subject", "unknown")
            
            # Check for self-signed or suspicious certificates
            if "self-signed" in issuer.lower() or not issuer:
                logger.warning(
                    f"Suspicious TLS certificate: {subject} from {alert.src_ip}"
                )
                
                notification = await self._create_alert_notification(
                    severity="warning",
                    title="Suspicious TLS Certificate",
                    description=f"Subject: {subject}",
                    src_ip=alert.src_ip,
                )
                await self._send_to_alertmanager([notification])
                
        except Exception as e:
            logger.error(f"Error handling TLS event: {e}")

    async def _track_threat(self, ip: str, threat_type: str, severity: str):
        """Track a threat indicator"""
        if ip not in self.threat_db:
            self.threat_db[ip] = ThreatIntelligence(
                ip_address=ip,
                threat_type=threat_type,
                confidence=self._calculate_confidence(severity),
                last_seen=datetime.utcnow(),
                count=0,
            )
        
        threat = self.threat_db[ip]
        threat.count += 1
        threat.last_seen = datetime.utcnow()

    async def _blacklist_ip(self, ip: str, reason: str = "Threat threshold exceeded"):
        """Mark IP for blacklisting (implement actual blocking in firewall)"""
        logger.critical(f"🚨 BLACKLISTING IP: {ip} ({reason})")
        
        if ip in self.threat_db:
            self.threat_db[ip].blacklist = True

    async def _correlate_alerts(self):
        """Correlate related alerts for pattern detection"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.correlation_window)
        
        # Remove old alerts
        self.recent_alerts = [a for a in self.recent_alerts 
                             if datetime.fromisoformat(a.timestamp.replace('Z', '+00:00')) > cutoff]
        
        # Check for attack patterns
        if len(self.recent_alerts) > 0:
            # Group by source IP
            ips = {}
            for alert in self.recent_alerts:
                if alert.src_ip:
                    ips.setdefault(alert.src_ip, []).append(alert)
            
            # Detect attack patterns
            for ip, alerts in ips.items():
                if len(alerts) >= 3:
                    alert_types = [a.alert.get("category") for a in alerts if a.alert]
                    logger.warning(
                        f"⚠️ ATTACK PATTERN DETECTED: {ip} has {len(alerts)} alerts "
                        f"in {self.correlation_window}s: {set(alert_types)}"
                    )

    async def _cleanup_old_threats(self):
        """Remove old threat indicators"""
        now = datetime.utcnow()
        to_remove = []
        
        for ip, threat in self.threat_db.items():
            age = (now - threat.last_seen).total_seconds()
            if age > self.max_threat_age_seconds:
                to_remove.append(ip)
        
        for ip in to_remove:
            del self.threat_db[ip]
            logger.debug(f"Cleaned up threat indicator: {ip}")

    async def _create_alert_notification(
        self,
        severity: str,
        title: str,
        description: str,
        src_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        sid: Optional[int] = None,
    ) -> AlertNotification:
        """Create an alert notification for Alertmanager"""
        
        labels = {
            "alertname": title,
            "severity": severity,
            "source": "suricata",
        }
        
        if src_ip:
            labels["src_ip"] = src_ip
        if dest_ip:
            labels["dest_ip"] = dest_ip
        if sid:
            labels["rule_id"] = str(sid)
        
        annotations = {
            "summary": title,
            "description": description,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return AlertNotification(
            status="firing",
            labels=labels,
            annotations=annotations,
            startsAt=datetime.utcnow().isoformat() + "Z",
        )

    async def _send_to_alertmanager(self, alerts: List[AlertNotification]):
        """Send alerts to Alertmanager"""
        try:
            payload = [json.loads(a.json()) for a in alerts]
            response = requests.post(
                self.alertmanager_url,
                json=payload,
                timeout=5,
            )
            response.raise_for_status()
            logger.debug(f"Sent {len(alerts)} alerts to Alertmanager")
        except requests.RequestException as e:
            logger.error(f"Failed to send alerts to Alertmanager: {e}")

    def _classify_severity(self, sid: Optional[int], category: str) -> str:
        """Classify alert severity"""
        if not sid:
            return "warning"
        
        # Map SID ranges to severity
        if 500001 <= sid <= 599999:  # SQL injection, XSS, etc
            return "critical"
        elif 600001 <= sid <= 699999:  # Network attacks, DoS
            return "high"
        elif 700001 <= sid <= 799999:  # Anomalies
            return "warning"
        
        return "info"

    def _calculate_confidence(self, severity: str) -> float:
        """Calculate confidence score based on severity"""
        confidence_map = {
            "critical": 0.95,
            "high": 0.85,
            "warning": 0.7,
            "info": 0.5,
        }
        return confidence_map.get(severity, 0.5)

    def _is_suspicious_http(self, method: str, uri: str) -> bool:
        """Check if HTTP request is suspicious"""
        suspicious_methods = ["TRACE", "CONNECT"]
        suspicious_patterns = [
            "../", "..\\", "%2e%2e",  # Path traversal
            "union", "select", "insert",  # SQL injection
            "<script>", "javascript:",  # XSS
        ]
        
        if method in suspicious_methods:
            return True
        
        uri_lower = uri.lower()
        for pattern in suspicious_patterns:
            if pattern.lower() in uri_lower:
                return True
        
        return False

    def _is_suspicious_dns(self, query: str) -> bool:
        """Check if DNS query is suspicious"""
        suspicious_patterns = [
            ".onion",  # TOR
            ".i2p",  # I2P
            "tunnel",
            "proxy",
            "exfil",
        ]
        
        query_lower = query.lower()
        for pattern in suspicious_patterns:
            if pattern in query_lower:
                return True
        
        return False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Run the IDS alert processor"""
    processor = IDSAlertProcessor(
        eve_log_path="/var/log/suricata/eve.json",
        alertmanager_url="http://alertmanager:9093/api/v1/alerts",
    )
    
    # Start processing alerts
    await processor.start(poll_interval=5)


if __name__ == "__main__":
    asyncio.run(main())
