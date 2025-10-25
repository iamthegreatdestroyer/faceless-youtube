"""
WAF Event Logger and Processor
Real-time ModSecurity audit log processing and Alertmanager integration
Processes blocked requests, tracks attack patterns, and sends notifications

Author: Faceless YouTube Automation Platform
Date: October 25, 2025
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

import aiofiles
import aiofiles.os
import requests
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


###############################################################################
# Data Models
###############################################################################

class WAFAlert(BaseModel):
    """Represents a ModSecurity WAF alert event."""

    timestamp: str
    src_ip: str
    dest_ip: str
    request_method: str
    request_uri: str
    http_version: str
    status_code: int
    rule_id: str
    rule_msg: str
    rule_tags: List[str] = Field(default_factory=list)
    rule_severity: str
    blocked: bool
    matched_content: Optional[str] = None
    user_agent: Optional[str] = None
    content_type: Optional[str] = None
    request_body_size: int = 0

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ThreatIntelligence(BaseModel):
    """Tracks threat intelligence and attack patterns."""

    ip_address: str
    attack_type: str  # sql_injection, xss, command_injection, etc.
    count: int = 0
    confidence: float = Field(ge=0.0, le=1.0)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    blocked: bool = False
    blacklist: bool = False
    rule_ids: Set[str] = Field(default_factory=set)
    attack_patterns: Dict[str, int] = Field(default_factory=dict)


@dataclass
class AlertNotification:
    """Alertmanager-compatible alert notification."""

    status: str  # 'firing' or 'resolved'
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    startsAt: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    endsAt: str = ""


###############################################################################
# WAF Event Processor
###############################################################################

class WAFEventProcessor:
    """
    Processes ModSecurity WAF events and integrates with monitoring.

    Features:
    - Real-time audit log monitoring
    - Attack pattern correlation
    - Threat intelligence tracking
    - IP reputation scoring
    - Alertmanager integration
    - Automatic blocking lists
    """

    def __init__(
        self,
        audit_log_path: str = "/var/log/modsecurity/audit.log",
        alertmanager_url: str = "http://localhost:9093",
        max_threat_age: int = 3600,
        auto_blacklist_threshold: int = 5,
        correlation_window: int = 30,
    ):
        """
        Initialize WAF event processor.

        Args:
            audit_log_path: Path to ModSecurity audit.log (JSON format)
            alertmanager_url: Alertmanager API endpoint
            max_threat_age: Maximum age of threat in seconds (default: 1 hour)
            auto_blacklist_threshold: Block after N attempts (default: 5)
            correlation_window: Correlation time window in seconds (default: 30)
        """
        self.audit_log_path = Path(audit_log_path)
        self.alertmanager_url = alertmanager_url
        self.max_threat_age = max_threat_age
        self.auto_blacklist_threshold = auto_blacklist_threshold
        self.correlation_window = correlation_window

        # Threat tracking database
        self.threat_db: Dict[str, ThreatIntelligence] = {}

        # Attack pattern history (for correlation)
        self.attack_history: List[Tuple[datetime, str, str]] = []  # (timestamp, ip, attack_type)

        # File position tracking for incremental reading
        self.last_position = 0
        self.blacklisted_ips: Set[str] = set()

        logger.info(f"WAF Event Processor initialized - audit log: {audit_log_path}")

    async def start(self) -> None:
        """Start monitoring WAF audit log in real-time."""
        logger.info("Starting WAF event processor...")

        while True:
            try:
                await self._process_audit_log()
                await self._cleanup_old_threats()
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in WAF processor loop: {e}", exc_info=True)
                await asyncio.sleep(10)  # Back off on error

    async def _process_audit_log(self) -> None:
        """Process new audit log entries incrementally."""
        if not self.audit_log_path.exists():
            logger.warning(f"Audit log not found: {self.audit_log_path}")
            return

        try:
            async with aiofiles.open(self.audit_log_path, "r") as f:
                await f.seek(self.last_position)
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Parse JSON event
                        event = json.loads(line)
                        alert = self._parse_waf_event(event)

                        if alert:
                            await self._handle_alert(alert)

                    except json.JSONDecodeError:
                        logger.debug(f"Invalid JSON in audit log: {line[:100]}")
                        continue

                    self.last_position = await f.tell()

        except Exception as e:
            logger.error(f"Error processing audit log: {e}", exc_info=True)

    def _parse_waf_event(self, event: dict) -> Optional[WAFAlert]:
        """
        Parse ModSecurity audit log event.

        Args:
            event: Raw JSON event from audit log

        Returns:
            Parsed WAFAlert or None if invalid
        """
        try:
            # Extract relevant fields from ModSecurity event
            timestamp = event.get("timestamp", datetime.utcnow().isoformat())
            src_ip = event.get("source_ip", "unknown")
            dest_ip = event.get("dest_ip", "unknown")
            request_method = event.get("request", {}).get("method", "UNKNOWN")
            request_uri = event.get("request", {}).get("uri", "/")
            http_version = event.get("request", {}).get("protocol", "HTTP/1.1")
            status_code = event.get("response", {}).get("status", 0)

            # Alert information
            alert_msg = event.get("alert_message", "Unknown alert")
            rule_id = event.get("rule_id", "0")
            rule_tags = event.get("tags", [])
            rule_severity = event.get("severity", "UNKNOWN")

            blocked = event.get("blocked", False)
            matched_content = event.get("matched_var", None)
            user_agent = event.get("request", {}).get("headers", {}).get("User-Agent")
            content_type = event.get("request", {}).get("headers", {}).get("Content-Type")
            request_body_size = event.get("request", {}).get("body_size", 0)

            alert = WAFAlert(
                timestamp=timestamp,
                src_ip=src_ip,
                dest_ip=dest_ip,
                request_method=request_method,
                request_uri=request_uri,
                http_version=http_version,
                status_code=status_code,
                rule_id=rule_id,
                rule_msg=alert_msg,
                rule_tags=rule_tags,
                rule_severity=rule_severity,
                blocked=blocked,
                matched_content=matched_content,
                user_agent=user_agent,
                content_type=content_type,
                request_body_size=request_body_size,
            )

            return alert

        except (KeyError, ValueError) as e:
            logger.debug(f"Failed to parse WAF event: {e}")
            return None

    async def _handle_alert(self, alert: WAFAlert) -> None:
        """
        Process WAF alert: track threat, check patterns, send notifications.

        Args:
            alert: Parsed WAF alert
        """
        # Classify attack type
        attack_type = self._classify_attack(alert)

        logger.info(
            f"WAF Alert: {alert.src_ip} -> {attack_type} ({alert.rule_msg}) - "
            f"URI: {alert.request_uri}"
        )

        # Track threat
        await self._track_threat(alert.src_ip, attack_type, alert)

        # Check for correlated attacks
        correlation = await self._correlate_alerts(alert.src_ip, attack_type)

        if correlation:
            logger.warning(f"Attack pattern detected from {alert.src_ip}: {correlation}")

        # Auto-blacklist if threshold exceeded
        if alert.src_ip in self.threat_db:
            threat = self.threat_db[alert.src_ip]
            if threat.count >= self.auto_blacklist_threshold and not threat.blacklist:
                await self._blacklist_ip(alert.src_ip)
                logger.warning(f"IP auto-blacklisted: {alert.src_ip} (hits: {threat.count})")

        # Send alert to Alertmanager
        if alert.blocked:
            await self._send_alert_to_alertmanager(alert, attack_type, correlation)

    def _classify_attack(self, alert: WAFAlert) -> str:
        """
        Classify attack type from rule tags and message.

        Args:
            alert: WAF alert

        Returns:
            Attack type classification
        """
        # Check rule tags first
        for tag in alert.rule_tags:
            if "sql-injection" in tag.lower():
                return "sql_injection"
            elif "xss" in tag.lower():
                return "xss"
            elif "command-injection" in tag.lower():
                return "command_injection"
            elif "path-traversal" in tag.lower():
                return "path_traversal"
            elif "rfi" in tag.lower():
                return "remote_file_inclusion"
            elif "bot" in tag.lower():
                return "bot_activity"
            elif "brute-force" in tag.lower():
                return "brute_force"
            elif "rate" in tag.lower():
                return "rate_limiting"

        # Fall back to message analysis
        msg_lower = alert.rule_msg.lower()
        if "sql" in msg_lower:
            return "sql_injection"
        elif "xss" in msg_lower or "script" in msg_lower:
            return "xss"
        elif "command" in msg_lower:
            return "command_injection"
        elif "path" in msg_lower or "traversal" in msg_lower:
            return "path_traversal"
        elif "file inclusion" in msg_lower:
            return "remote_file_inclusion"
        elif "bot" in msg_lower or "scanner" in msg_lower:
            return "bot_activity"

        return "unknown_attack"

    async def _track_threat(self, ip_address: str, attack_type: str, alert: WAFAlert) -> None:
        """
        Update threat intelligence database.

        Args:
            ip_address: Source IP address
            attack_type: Classification of attack
            alert: The WAF alert
        """
        now = datetime.utcnow()

        if ip_address not in self.threat_db:
            self.threat_db[ip_address] = ThreatIntelligence(
                ip_address=ip_address,
                attack_type=attack_type,
                count=1,
                confidence=0.8,
                last_seen=now,
            )
        else:
            threat = self.threat_db[ip_address]
            threat.count += 1
            threat.last_seen = now
            threat.rule_ids.add(alert.rule_id)

            # Increase confidence with each hit
            threat.confidence = min(0.95, threat.confidence + 0.05)

            # Track attack patterns
            if attack_type in threat.attack_patterns:
                threat.attack_patterns[attack_type] += 1
            else:
                threat.attack_patterns[attack_type] = 1

    async def _correlate_alerts(self, ip_address: str, attack_type: str) -> Optional[str]:
        """
        Detect correlated attack patterns.

        Args:
            ip_address: Source IP
            attack_type: Type of attack

        Returns:
            Correlation pattern description or None
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.correlation_window)

        # Find recent attacks from same IP
        recent_attacks = [
            (ts, ip, atype)
            for ts, ip, atype in self.attack_history
            if ip == ip_address and ts >= window_start
        ]

        if len(recent_attacks) >= 3:
            # Attacks detected within correlation window
            attack_types = [atype for _, _, atype in recent_attacks]
            return f"Multiple attacks ({len(attack_types)} in {self.correlation_window}s): {attack_types}"

        # Add current attack to history
        self.attack_history.append((now, ip_address, attack_type))

        # Cleanup old history
        self.attack_history = [
            (ts, ip, atype)
            for ts, ip, atype in self.attack_history
            if ts >= window_start
        ]

        return None

    async def _blacklist_ip(self, ip_address: str) -> None:
        """
        Blacklist an IP address after excessive attacks.

        Args:
            ip_address: IP to blacklist
        """
        if ip_address in self.threat_db:
            self.threat_db[ip_address].blacklist = True
            self.blacklisted_ips.add(ip_address)

            # Send critical alert to Alertmanager
            await self._send_blacklist_alert(ip_address)

    async def _send_alert_to_alertmanager(
        self, alert: WAFAlert, attack_type: str, correlation: Optional[str]
    ) -> None:
        """
        Send alert notification to Alertmanager.

        Args:
            alert: WAF alert
            attack_type: Attack type classification
            correlation: Optional correlation pattern
        """
        try:
            severity = self._calculate_severity(alert, correlation)
            confidence = (
                self.threat_db[alert.src_ip].confidence
                if alert.src_ip in self.threat_db
                else 0.5
            )

            notification = AlertNotification(
                status="firing",
                labels={
                    "severity": severity,
                    "component": "waf",
                    "attack_type": attack_type,
                    "source_ip": alert.src_ip,
                    "rule_id": alert.rule_id,
                },
                annotations={
                    "summary": f"WAF Alert: {attack_type.replace('_', ' ').title()}",
                    "description": f"{alert.rule_msg} from {alert.src_ip} to {alert.request_uri}",
                    "attack_type": attack_type,
                    "source_ip": alert.src_ip,
                    "confidence": f"{confidence:.1%}",
                    "blocked": str(alert.blocked),
                    "correlation": correlation or "No pattern detected",
                },
                startsAt=alert.timestamp,
            )

            await self._send_to_alertmanager([notification])

        except Exception as e:
            logger.error(f"Error sending alert to Alertmanager: {e}", exc_info=True)

    async def _send_blacklist_alert(self, ip_address: str) -> None:
        """Send critical alert when IP is blacklisted."""
        threat = self.threat_db[ip_address]

        notification = AlertNotification(
            status="firing",
            labels={
                "severity": "CRITICAL",
                "component": "waf",
                "alert_type": "ip_blacklist",
                "source_ip": ip_address,
            },
            annotations={
                "summary": f"IP Blacklisted: {ip_address}",
                "description": (
                    f"IP {ip_address} blacklisted after {threat.count} attacks. "
                    f"Patterns: {threat.attack_patterns}"
                ),
                "attack_count": str(threat.count),
                "confidence": f"{threat.confidence:.1%}",
            },
        )

        await self._send_to_alertmanager([notification])

    async def _send_to_alertmanager(self, notifications: List[AlertNotification]) -> None:
        """
        Send alerts to Alertmanager via REST API.

        Args:
            notifications: List of alert notifications
        """
        try:
            url = f"{self.alertmanager_url}/api/v1/alerts"
            payload = [asdict(n) for n in notifications]

            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()

            logger.debug(f"Sent {len(notifications)} alerts to Alertmanager")

        except requests.RequestException as e:
            logger.error(f"Failed to send alerts to Alertmanager: {e}")

    def _calculate_severity(self, alert: WAFAlert, correlation: Optional[str]) -> str:
        """
        Calculate alert severity level.

        Args:
            alert: WAF alert
            correlation: Optional correlation pattern

        Returns:
            Severity level: CRITICAL, HIGH, MEDIUM, LOW
        """
        # Check for correlation (indicates coordinated attack)
        if correlation:
            return "CRITICAL"

        # Check rule severity
        if alert.rule_severity in ("CRITICAL", "EMERGENCY"):
            return "CRITICAL"
        elif alert.rule_severity == "HIGH":
            return "HIGH"
        elif alert.rule_severity == "MEDIUM":
            return "MEDIUM"

        return "LOW"

    async def _cleanup_old_threats(self) -> None:
        """Remove expired threat intelligence entries."""
        now = datetime.utcnow()
        expired_ips = [
            ip
            for ip, threat in self.threat_db.items()
            if (now - threat.last_seen).total_seconds() > self.max_threat_age
        ]

        for ip in expired_ips:
            del self.threat_db[ip]
            logger.debug(f"Removed expired threat entry for {ip}")

    def get_threat_stats(self) -> Dict:
        """Get current threat statistics."""
        return {
            "total_threats": len(self.threat_db),
            "blacklisted_ips": len(self.blacklisted_ips),
            "threats_by_type": defaultdict(
                int,
                {t.attack_type: 1 for t in self.threat_db.values()},
            ),
            "total_attacks": sum(t.count for t in self.threat_db.values()),
        }


###############################################################################
# Main Entry Point
###############################################################################

async def main() -> None:
    """Run WAF event processor."""
    processor = WAFEventProcessor(
        audit_log_path="/var/log/modsecurity/audit.log",
        alertmanager_url="http://localhost:9093",
        max_threat_age=3600,
        auto_blacklist_threshold=5,
        correlation_window=30,
    )

    await processor.start()


if __name__ == "__main__":
    asyncio.run(main())
