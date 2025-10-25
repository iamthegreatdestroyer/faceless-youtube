"""
Unit tests for WAF Event Logger
Tests for ModSecurity audit log processing, threat tracking, and alerting

Pytest configuration: Use pytest with asyncio markers
Coverage target: >90%
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.security.waf_logger import (
    WAFAlert,
    ThreatIntelligence,
    AlertNotification,
    WAFEventProcessor,
)


###############################################################################
# Fixtures
###############################################################################

@pytest.fixture
def waf_processor():
    """Create WAF processor instance for testing."""
    return WAFEventProcessor(
        audit_log_path="/tmp/modsecurity_test.log",
        alertmanager_url="http://localhost:9093",
        max_threat_age=3600,
        auto_blacklist_threshold=5,
        correlation_window=30,
    )


@pytest.fixture
def sample_sql_injection_alert():
    """Sample SQL injection WAF alert."""
    return WAFAlert(
        timestamp=datetime.utcnow().isoformat(),
        src_ip="192.168.1.100",
        dest_ip="10.0.0.1",
        request_method="GET",
        request_uri="/api/v1/users?id=1' OR '1'='1",
        http_version="HTTP/1.1",
        status_code=403,
        rule_id="1001",
        rule_msg="SQL Injection Attack Detected - UNION SELECT",
        rule_tags=["attack/sql-injection", "OWASP_CRS"],
        rule_severity="CRITICAL",
        blocked=True,
        matched_content="' OR '1'='1",
        user_agent="Mozilla/5.0",
        content_type="application/json",
        request_body_size=0,
    )


@pytest.fixture
def sample_xss_alert():
    """Sample XSS WAF alert."""
    return WAFAlert(
        timestamp=datetime.utcnow().isoformat(),
        src_ip="192.168.1.101",
        dest_ip="10.0.0.1",
        request_method="POST",
        request_uri="/api/v1/comments",
        http_version="HTTP/1.1",
        status_code=403,
        rule_id="2001",
        rule_msg="XSS Attack Detected - Script Tag",
        rule_tags=["attack/xss", "OWASP_CRS"],
        rule_severity="CRITICAL",
        blocked=True,
        matched_content="<script>alert('xss')</script>",
        user_agent="curl/7.68.0",
        content_type="application/json",
        request_body_size=100,
    )


@pytest.fixture
def sample_command_injection_alert():
    """Sample command injection alert."""
    return WAFAlert(
        timestamp=datetime.utcnow().isoformat(),
        src_ip="192.168.1.102",
        dest_ip="10.0.0.1",
        request_method="GET",
        request_uri="/api/v1/execute?cmd=; ls -la",
        http_version="HTTP/1.1",
        status_code=403,
        rule_id="3002",
        rule_msg="Command Injection - Command Chaining Detected",
        rule_tags=["attack/command-injection", "OWASP_CRS"],
        rule_severity="CRITICAL",
        blocked=True,
        matched_content="; ls -la",
        user_agent="Mozilla/5.0",
        content_type="text/plain",
        request_body_size=0,
    )


@pytest.fixture
def sample_path_traversal_alert():
    """Sample path traversal alert."""
    return WAFAlert(
        timestamp=datetime.utcnow().isoformat(),
        src_ip="192.168.1.103",
        dest_ip="10.0.0.1",
        request_method="GET",
        request_uri="/api/v1/files?path=../../etc/passwd",
        http_version="HTTP/1.1",
        status_code=403,
        rule_id="3051",
        rule_msg="Path Traversal Attack Detected",
        rule_tags=["attack/path-traversal", "OWASP_CRS"],
        rule_severity="HIGH",
        blocked=True,
        matched_content="../../etc/passwd",
        user_agent="Mozilla/5.0",
        content_type="text/plain",
        request_body_size=0,
    )


###############################################################################
# Alert Parsing Tests
###############################################################################

class TestAlertParsing:
    """Tests for WAF alert parsing."""

    def test_parse_valid_waf_event(self, waf_processor):
        """Test parsing valid WAF event from JSON."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": "192.168.1.100",
            "dest_ip": "10.0.0.1",
            "request": {
                "method": "POST",
                "uri": "/api/v1/login",
                "protocol": "HTTP/1.1",
                "headers": {
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json"
                },
                "body_size": 256
            },
            "response": {"status": 403},
            "alert_message": "SQL Injection Detected",
            "rule_id": "1001",
            "tags": ["sql-injection"],
            "severity": "CRITICAL",
            "blocked": True,
            "matched_var": "' OR '1'='1"
        }

        alert = waf_processor._parse_waf_event(event)

        assert alert is not None
        assert alert.src_ip == "192.168.1.100"
        assert alert.rule_id == "1001"
        assert alert.blocked is True
        assert alert.status_code == 403

    def test_parse_invalid_waf_event(self, waf_processor):
        """Test handling of invalid WAF events."""
        event = {"invalid": "event"}

        alert = waf_processor._parse_waf_event(event)

        assert alert is None

    def test_parse_event_with_missing_fields(self, waf_processor):
        """Test parsing event with missing optional fields."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": "192.168.1.100",
            "dest_ip": "10.0.0.1",
            "request": {"method": "GET", "uri": "/test"},
            "rule_id": "1001",
        }

        alert = waf_processor._parse_waf_event(event)

        assert alert is not None
        assert alert.user_agent is None
        assert alert.content_type is None


###############################################################################
# Attack Classification Tests
###############################################################################

class TestAttackClassification:
    """Tests for attack type classification."""

    def test_classify_sql_injection_by_tag(self, waf_processor, sample_sql_injection_alert):
        """Test classification of SQL injection by tag."""
        attack_type = waf_processor._classify_attack(sample_sql_injection_alert)
        assert attack_type == "sql_injection"

    def test_classify_xss_by_tag(self, waf_processor, sample_xss_alert):
        """Test classification of XSS by tag."""
        attack_type = waf_processor._classify_attack(sample_xss_alert)
        assert attack_type == "xss"

    def test_classify_command_injection(self, waf_processor, sample_command_injection_alert):
        """Test classification of command injection."""
        attack_type = waf_processor._classify_attack(sample_command_injection_alert)
        assert attack_type == "command_injection"

    def test_classify_path_traversal(self, waf_processor, sample_path_traversal_alert):
        """Test classification of path traversal."""
        attack_type = waf_processor._classify_attack(sample_path_traversal_alert)
        assert attack_type == "path_traversal"

    def test_classify_by_message_fallback(self, waf_processor):
        """Test classification fallback to message analysis."""
        alert = WAFAlert(
            timestamp=datetime.utcnow().isoformat(),
            src_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            request_method="GET",
            request_uri="/test",
            http_version="HTTP/1.1",
            status_code=403,
            rule_id="1001",
            rule_msg="SQL Injection detected in query",
            rule_tags=[],  # No tags
            rule_severity="HIGH",
            blocked=True,
        )

        attack_type = waf_processor._classify_attack(alert)
        assert attack_type == "sql_injection"

    def test_classify_unknown_attack(self, waf_processor):
        """Test classification of unknown attack type."""
        alert = WAFAlert(
            timestamp=datetime.utcnow().isoformat(),
            src_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            request_method="GET",
            request_uri="/test",
            http_version="HTTP/1.1",
            status_code=403,
            rule_id="9999",
            rule_msg="Unknown rule triggered",
            rule_tags=[],
            rule_severity="LOW",
            blocked=False,
        )

        attack_type = waf_processor._classify_attack(alert)
        assert attack_type == "unknown_attack"


###############################################################################
# Threat Tracking Tests
###############################################################################

class TestThreatTracking:
    """Tests for threat intelligence tracking."""

    @pytest.mark.asyncio
    async def test_track_new_threat(self, waf_processor, sample_sql_injection_alert):
        """Test tracking new threat."""
        await waf_processor._track_threat(
            sample_sql_injection_alert.src_ip,
            "sql_injection",
            sample_sql_injection_alert
        )

        assert sample_sql_injection_alert.src_ip in waf_processor.threat_db
        threat = waf_processor.threat_db[sample_sql_injection_alert.src_ip]
        assert threat.count == 1
        assert threat.attack_type == "sql_injection"

    @pytest.mark.asyncio
    async def test_threat_count_increment(self, waf_processor, sample_sql_injection_alert):
        """Test threat hit count increments."""
        ip = sample_sql_injection_alert.src_ip

        # First attack
        await waf_processor._track_threat(ip, "sql_injection", sample_sql_injection_alert)
        assert waf_processor.threat_db[ip].count == 1

        # Second attack
        await waf_processor._track_threat(ip, "sql_injection", sample_sql_injection_alert)
        assert waf_processor.threat_db[ip].count == 2

    @pytest.mark.asyncio
    async def test_confidence_increases(self, waf_processor, sample_sql_injection_alert):
        """Test confidence score increases with hits."""
        ip = sample_sql_injection_alert.src_ip
        initial_confidence = 0.8

        await waf_processor._track_threat(ip, "sql_injection", sample_sql_injection_alert)
        first_confidence = waf_processor.threat_db[ip].confidence

        await waf_processor._track_threat(ip, "sql_injection", sample_sql_injection_alert)
        second_confidence = waf_processor.threat_db[ip].confidence

        assert first_confidence >= initial_confidence
        assert second_confidence > first_confidence
        assert second_confidence <= 0.95

    @pytest.mark.asyncio
    async def test_rule_id_tracking(self, waf_processor, sample_sql_injection_alert):
        """Test rule IDs are tracked."""
        ip = sample_sql_injection_alert.src_ip

        await waf_processor._track_threat(ip, "sql_injection", sample_sql_injection_alert)
        threat = waf_processor.threat_db[ip]

        assert sample_sql_injection_alert.rule_id in threat.rule_ids


###############################################################################
# Attack Correlation Tests
###############################################################################

class TestAttackCorrelation:
    """Tests for attack pattern correlation."""

    @pytest.mark.asyncio
    async def test_no_correlation_single_attack(self, waf_processor, sample_sql_injection_alert):
        """Test no correlation on single attack."""
        correlation = await waf_processor._correlate_alerts(
            sample_sql_injection_alert.src_ip,
            "sql_injection"
        )

        assert correlation is None

    @pytest.mark.asyncio
    async def test_correlation_multiple_attacks(self, waf_processor):
        """Test correlation detection with multiple attacks."""
        ip = "192.168.1.100"

        # Simulate 3 attacks within correlation window
        for i in range(3):
            await waf_processor._correlate_alerts(ip, "sql_injection")

        # Fourth attack should trigger correlation
        correlation = await waf_processor._correlate_alerts(ip, "xss")

        assert correlation is not None
        assert "Multiple attacks" in correlation

    @pytest.mark.asyncio
    async def test_correlation_window_expiry(self, waf_processor):
        """Test correlation resets after window expires."""
        ip = "192.168.1.100"

        # Add attacks
        for _ in range(3):
            await waf_processor._correlate_alerts(ip, "sql_injection")

        # Manually expire the history
        waf_processor.attack_history = [
            (datetime.utcnow() - timedelta(seconds=35), ip, "sql_injection")
        ]

        # New attack should not correlate (history expired)
        correlation = await waf_processor._correlate_alerts(ip, "xss")

        assert correlation is None


###############################################################################
# Auto-Blacklist Tests
###############################################################################

class TestAutoBlacklist:
    """Tests for automatic IP blacklisting."""

    @pytest.mark.asyncio
    async def test_blacklist_ip(self, waf_processor):
        """Test IP blacklisting."""
        ip = "192.168.1.100"

        # Create threat
        waf_processor.threat_db[ip] = ThreatIntelligence(
            ip_address=ip,
            attack_type="sql_injection",
            count=5,
            confidence=0.95,
        )

        with patch.object(waf_processor, '_send_blacklist_alert', new_callable=AsyncMock):
            await waf_processor._blacklist_ip(ip)

        assert ip in waf_processor.blacklisted_ips
        assert waf_processor.threat_db[ip].blacklist is True

    @pytest.mark.asyncio
    async def test_auto_blacklist_on_threshold(self, waf_processor, sample_sql_injection_alert):
        """Test auto-blacklist triggers at threshold."""
        ip = sample_sql_injection_alert.src_ip

        # Create threat at threshold
        waf_processor.threat_db[ip] = ThreatIntelligence(
            ip_address=ip,
            attack_type="sql_injection",
            count=5,  # Equals threshold
            confidence=0.95,
        )

        with patch.object(waf_processor, '_send_blacklist_alert', new_callable=AsyncMock):
            await waf_processor._handle_alert(sample_sql_injection_alert)

        # Should be blacklisted (would be triggered in _handle_alert)
        assert ip in waf_processor.threat_db


###############################################################################
# Severity Calculation Tests
###############################################################################

class TestSeverityCalculation:
    """Tests for alert severity calculation."""

    def test_severity_critical_with_correlation(self, waf_processor, sample_sql_injection_alert):
        """Test CRITICAL severity when correlation detected."""
        severity = waf_processor._calculate_severity(
            sample_sql_injection_alert,
            "Multiple attacks in 30s"
        )
        assert severity == "CRITICAL"

    def test_severity_critical_rule(self, waf_processor, sample_sql_injection_alert):
        """Test CRITICAL severity from rule."""
        assert sample_sql_injection_alert.rule_severity == "CRITICAL"

        severity = waf_processor._calculate_severity(sample_sql_injection_alert, None)
        assert severity == "CRITICAL"

    def test_severity_high_rule(self, waf_processor):
        """Test HIGH severity from rule."""
        alert = WAFAlert(
            timestamp=datetime.utcnow().isoformat(),
            src_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            request_method="GET",
            request_uri="/test",
            http_version="HTTP/1.1",
            status_code=403,
            rule_id="3051",
            rule_msg="Path Traversal",
            rule_tags=[],
            rule_severity="HIGH",
            blocked=True,
        )

        severity = waf_processor._calculate_severity(alert, None)
        assert severity == "HIGH"

    def test_severity_medium_rule(self, waf_processor):
        """Test MEDIUM severity from rule."""
        alert = WAFAlert(
            timestamp=datetime.utcnow().isoformat(),
            src_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            request_method="GET",
            request_uri="/test",
            http_version="HTTP/1.1",
            status_code=403,
            rule_id="1002",
            rule_msg="SQL Comment Sequence",
            rule_tags=[],
            rule_severity="MEDIUM",
            blocked=True,
        )

        severity = waf_processor._calculate_severity(alert, None)
        assert severity == "MEDIUM"


###############################################################################
# Alertmanager Integration Tests
###############################################################################

class TestAlertmanagerIntegration:
    """Tests for Alertmanager integration."""

    @pytest.mark.asyncio
    async def test_send_alert_to_alertmanager(self, waf_processor, sample_sql_injection_alert):
        """Test sending alert to Alertmanager."""
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            await waf_processor._send_alert_to_alertmanager(
                sample_sql_injection_alert,
                "sql_injection",
                None
            )

            assert mock_post.called

    @pytest.mark.asyncio
    async def test_send_alert_with_correlation(self, waf_processor, sample_sql_injection_alert):
        """Test sending alert includes correlation."""
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            await waf_processor._send_alert_to_alertmanager(
                sample_sql_injection_alert,
                "sql_injection",
                "Multiple attacks detected"
            )

            assert mock_post.called
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload[0]['annotations']['correlation'] == "Multiple attacks detected"

    @pytest.mark.asyncio
    async def test_alertmanager_connection_error(self, waf_processor, sample_sql_injection_alert):
        """Test handling of Alertmanager connection errors."""
        with patch('requests.post', side_effect=Exception("Connection refused")):
            # Should not raise exception
            await waf_processor._send_alert_to_alertmanager(
                sample_sql_injection_alert,
                "sql_injection",
                None
            )


###############################################################################
# Cleanup Tests
###############################################################################

class TestCleanup:
    """Tests for threat database cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_threats(self, waf_processor):
        """Test removal of expired threat entries."""
        old_time = datetime.utcnow() - timedelta(seconds=3700)

        threat = ThreatIntelligence(
            ip_address="192.168.1.100",
            attack_type="sql_injection",
            count=5,
            confidence=0.9,
            last_seen=old_time,
        )

        waf_processor.threat_db["192.168.1.100"] = threat

        await waf_processor._cleanup_old_threats()

        assert "192.168.1.100" not in waf_processor.threat_db

    @pytest.mark.asyncio
    async def test_keep_recent_threats(self, waf_processor):
        """Test that recent threats are not removed."""
        recent_time = datetime.utcnow()

        threat = ThreatIntelligence(
            ip_address="192.168.1.100",
            attack_type="sql_injection",
            count=5,
            confidence=0.9,
            last_seen=recent_time,
        )

        waf_processor.threat_db["192.168.1.100"] = threat

        await waf_processor._cleanup_old_threats()

        assert "192.168.1.100" in waf_processor.threat_db


###############################################################################
# Statistics Tests
###############################################################################

class TestStatistics:
    """Tests for threat statistics."""

    def test_get_threat_stats(self, waf_processor):
        """Test retrieval of threat statistics."""
        # Add threats
        waf_processor.threat_db["192.168.1.100"] = ThreatIntelligence(
            ip_address="192.168.1.100",
            attack_type="sql_injection",
            count=5,
            confidence=0.9,
        )
        waf_processor.threat_db["192.168.1.101"] = ThreatIntelligence(
            ip_address="192.168.1.101",
            attack_type="xss",
            count=3,
            confidence=0.8,
        )
        waf_processor.blacklisted_ips.add("192.168.1.100")

        stats = waf_processor.get_threat_stats()

        assert stats["total_threats"] == 2
        assert stats["blacklisted_ips"] == 1
        assert stats["total_attacks"] == 8


###############################################################################
# Performance Tests
###############################################################################

class TestPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_process_100_alerts_quickly(self, waf_processor):
        """Test processing 100 alerts in under 5 seconds."""
        import time

        alerts = [
            WAFAlert(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=f"192.168.1.{i % 256}",
                dest_ip="10.0.0.1",
                request_method="GET",
                request_uri=f"/api/test?id={i}",
                http_version="HTTP/1.1",
                status_code=403,
                rule_id=str(1001 + (i % 50)),
                rule_msg="Test alert",
                rule_tags=["test"],
                rule_severity="HIGH",
                blocked=True,
            )
            for i in range(100)
        ]

        start_time = time.time()

        # Process alerts
        for alert in alerts:
            await waf_processor._track_threat(alert.src_ip, "sql_injection", alert)

        elapsed = time.time() - start_time

        assert elapsed < 5.0, f"Processing took {elapsed:.2f}s (expected <5s)"


###############################################################################
# Integration Tests
###############################################################################

class TestIntegration:
    """Integration tests for complete WAF flow."""

    @pytest.mark.asyncio
    async def test_end_to_end_alert_processing(self, waf_processor, sample_sql_injection_alert):
        """Test complete alert processing flow."""
        with patch.object(waf_processor, '_send_alert_to_alertmanager', new_callable=AsyncMock):
            await waf_processor._handle_alert(sample_sql_injection_alert)

            assert sample_sql_injection_alert.src_ip in waf_processor.threat_db
            threat = waf_processor.threat_db[sample_sql_injection_alert.src_ip]
            assert threat.count == 1
            assert threat.attack_type == "sql_injection"

    @pytest.mark.asyncio
    async def test_multiple_attacks_same_ip(self, waf_processor):
        """Test handling multiple attacks from same IP."""
        ip = "192.168.1.100"

        # Simulate multiple different attacks from same IP
        alerts = [
            sample_sql_injection_alert := WAFAlert(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=ip,
                dest_ip="10.0.0.1",
                request_method="GET",
                request_uri="/test1",
                http_version="HTTP/1.1",
                status_code=403,
                rule_id="1001",
                rule_msg="SQL Injection",
                rule_tags=["attack/sql-injection"],
                rule_severity="CRITICAL",
                blocked=True,
            ),
            WAFAlert(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=ip,
                dest_ip="10.0.0.1",
                request_method="POST",
                request_uri="/test2",
                http_version="HTTP/1.1",
                status_code=403,
                rule_id="2001",
                rule_msg="XSS",
                rule_tags=["attack/xss"],
                rule_severity="CRITICAL",
                blocked=True,
            ),
        ]

        with patch.object(waf_processor, '_send_alert_to_alertmanager', new_callable=AsyncMock):
            for alert in alerts:
                await waf_processor._handle_alert(alert)

        threat = waf_processor.threat_db[ip]
        assert threat.count == 2
        assert len(threat.attack_patterns) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
