"""
Unit tests for Suricata IDS Alert Processor
Tests alert detection, correlation, threat tracking, and alertmanager integration

Author: Faceless YouTube Team
Date: 2025-10-25
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.security.ids_alerter import (
    AlertNotification,
    IDSAlertProcessor,
    SuricataAlert,
    ThreatIntelligence,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def ids_processor():
    """Create an IDS processor instance for testing"""
    return IDSAlertProcessor(
        eve_log_path="/tmp/test_eve.json",
        alertmanager_url="http://alertmanager:9093/api/v1/alerts",
        max_threat_age_seconds=3600,
        auto_blacklist_threshold=5,
    )


@pytest.fixture
def sample_sql_injection_alert():
    """Sample SQL injection alert"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "alert",
        "src_ip": "192.168.1.100",
        "dest_ip": "10.0.0.5",
        "src_port": 54321,
        "dest_port": 80,
        "proto": "tcp",
        "alert": {
            "action": "alert",
            "signature": "SQL Injection - Common SQLi Patterns in HTTP GET",
            "signature_id": 500001,
            "severity": 1,
            "category": "Web Application Attack",
        },
    }


@pytest.fixture
def sample_xss_alert():
    """Sample XSS alert"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "alert",
        "src_ip": "192.168.1.101",
        "dest_ip": "10.0.0.5",
        "src_port": 54322,
        "dest_port": 443,
        "proto": "tcp",
        "alert": {
            "action": "alert",
            "signature": "XSS - Script Tag Injection Detected",
            "signature_id": 510001,
            "severity": 1,
            "category": "Web Application Attack",
        },
    }


@pytest.fixture
def sample_dos_alert():
    """Sample DoS attack alert"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "alert",
        "src_ip": "203.0.113.50",
        "dest_ip": "10.0.0.5",
        "src_port": 12345,
        "dest_port": 443,
        "proto": "tcp",
        "alert": {
            "action": "alert",
            "signature": "DoS Attack - TCP SYN Flood Detected",
            "signature_id": 610001,
            "severity": 1,
            "category": "Denial of Service",
        },
    }


# ============================================================================
# TESTS: ALERT PARSING & HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_alert_parsing(ids_processor, sample_sql_injection_alert):
    """Test parsing of Suricata alerts"""
    alert = SuricataAlert(**sample_sql_injection_alert)
    
    assert alert.src_ip == "192.168.1.100"
    assert alert.dest_ip == "10.0.0.5"
    assert alert.src_port == 54321
    assert alert.alert["signature_id"] == 500001


@pytest.mark.asyncio
async def test_handle_alert_classification(ids_processor, sample_sql_injection_alert):
    """Test that alerts are classified with correct severity"""
    severity = ids_processor._classify_severity(
        sid=500001,
        category="Web Application Attack"
    )
    
    assert severity == "critical"


@pytest.mark.asyncio
async def test_handle_alert_dos_severity(ids_processor, sample_dos_alert):
    """Test DoS alert severity classification"""
    severity = ids_processor._classify_severity(
        sid=610001,
        category="Denial of Service"
    )
    
    assert severity == "high"


@pytest.mark.asyncio
async def test_handle_alert_tracking(ids_processor, sample_sql_injection_alert):
    """Test that alerts are tracked in threat database"""
    alert = SuricataAlert(**sample_sql_injection_alert)
    
    with patch.object(ids_processor, '_send_to_alertmanager', new_callable=AsyncMock):
        await ids_processor._handle_alert(alert)
    
    # Check threat was tracked
    assert sample_sql_injection_alert["src_ip"] in ids_processor.threat_db


# ============================================================================
# TESTS: THREAT TRACKING & CORRELATION
# ============================================================================

@pytest.mark.asyncio
async def test_threat_tracking(ids_processor, sample_sql_injection_alert):
    """Test threat indicator tracking"""
    ip = sample_sql_injection_alert["src_ip"]
    
    await ids_processor._track_threat(
        ip=ip,
        threat_type="Web Application Attack",
        severity="critical"
    )
    
    assert ip in ids_processor.threat_db
    assert ids_processor.threat_db[ip].count == 1
    
    # Track same IP again
    await ids_processor._track_threat(
        ip=ip,
        threat_type="Web Application Attack",
        severity="critical"
    )
    
    assert ids_processor.threat_db[ip].count == 2


@pytest.mark.asyncio
async def test_threat_cleanup(ids_processor):
    """Test that old threats are cleaned up"""
    ip = "192.168.1.100"
    
    # Add old threat
    old_time = datetime.utcnow() - timedelta(hours=2)
    threat = ThreatIntelligence(
        ip_address=ip,
        threat_type="test",
        confidence=0.9,
        last_seen=old_time,
        count=1,
    )
    ids_processor.threat_db[ip] = threat
    
    # Cleanup
    await ids_processor._cleanup_old_threats()
    
    # Old threat should be removed
    assert ip not in ids_processor.threat_db


@pytest.mark.asyncio
async def test_auto_blacklist_threshold(ids_processor):
    """Test automatic blacklist when threshold is exceeded"""
    ip = "192.168.1.100"
    
    # Add threat at threshold
    threat = ThreatIntelligence(
        ip_address=ip,
        threat_type="Web Application Attack",
        confidence=0.95,
        last_seen=datetime.utcnow(),
        count=5,  # At threshold
    )
    ids_processor.threat_db[ip] = threat
    
    # Blacklist should not be set yet
    assert not threat.blacklist
    
    with patch.object(ids_processor, '_send_to_alertmanager', new_callable=AsyncMock):
        await ids_processor._blacklist_ip(ip)
    
    # Now blacklist should be set
    assert ids_processor.threat_db[ip].blacklist


@pytest.mark.asyncio
async def test_alert_correlation(ids_processor, sample_sql_injection_alert, sample_xss_alert):
    """Test correlation of related alerts"""
    alert1 = SuricataAlert(**sample_sql_injection_alert)
    alert2 = SuricataAlert(**sample_xss_alert)
    
    # Both from different IPs, should not correlate
    ids_processor.recent_alerts = [alert1, alert2]
    
    await ids_processor._correlate_alerts()
    
    # No attack pattern should be detected (different IPs)
    assert len(ids_processor.recent_alerts) == 2


@pytest.mark.asyncio
async def test_attack_pattern_detection(ids_processor):
    """Test detection of attack patterns from same IP"""
    ip = "192.168.1.100"
    
    # Create multiple alerts from same IP
    alerts = []
    for i in range(3):
        alert_data = {
            "timestamp": (datetime.utcnow() + timedelta(seconds=i)).isoformat() + "Z",
            "event_type": "alert",
            "src_ip": ip,
            "dest_ip": "10.0.0.5",
            "src_port": 54321 + i,
            "dest_port": 80,
            "proto": "tcp",
            "alert": {
                "action": "alert",
                "signature": f"Attack {i}",
                "signature_id": 500001 + i,
                "severity": 1,
                "category": "Web Application Attack",
            },
        }
        alerts.append(SuricataAlert(**alert_data))
    
    ids_processor.recent_alerts = alerts
    
    with patch.object(ids_processor, '_send_to_alertmanager', new_callable=AsyncMock):
        await ids_processor._correlate_alerts()
    
    # Should detect pattern
    assert len(ids_processor.recent_alerts) == 3


# ============================================================================
# TESTS: ALERT NOTIFICATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_create_alert_notification(ids_processor):
    """Test creation of alert notifications"""
    notification = await ids_processor._create_alert_notification(
        severity="critical",
        title="SQL Injection Detected",
        description="SQL injection from 192.168.1.100",
        src_ip="192.168.1.100",
        dest_ip="10.0.0.5",
        sid=500001,
    )
    
    assert notification.status == "firing"
    assert notification.labels["severity"] == "critical"
    assert notification.labels["src_ip"] == "192.168.1.100"
    assert notification.annotations["summary"] == "SQL Injection Detected"


@pytest.mark.asyncio
async def test_send_to_alertmanager(ids_processor):
    """Test sending alerts to Alertmanager"""
    notification = await ids_processor._create_alert_notification(
        severity="critical",
        title="Test Alert",
        description="Test description",
    )
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        await ids_processor._send_to_alertmanager([notification])
        
        mock_post.assert_called_once()


# ============================================================================
# TESTS: SUSPICIOUS TRAFFIC DETECTION
# ============================================================================

def test_is_suspicious_http(ids_processor):
    """Test detection of suspicious HTTP requests"""
    # Normal requests
    assert not ids_processor._is_suspicious_http("GET", "/api/users")
    assert not ids_processor._is_suspicious_http("POST", "/api/login")
    
    # Suspicious methods
    assert ids_processor._is_suspicious_http("TRACE", "/")
    assert ids_processor._is_suspicious_http("CONNECT", "/")
    
    # Suspicious patterns
    assert ids_processor._is_suspicious_http("GET", "/../../../etc/passwd")
    assert ids_processor._is_suspicious_http("GET", "/api?id=1 UNION SELECT")
    assert ids_processor._is_suspicious_http("POST", "<script>alert('xss')</script>")


def test_is_suspicious_dns(ids_processor):
    """Test detection of suspicious DNS queries"""
    # Normal queries
    assert not ids_processor._is_suspicious_dns("example.com")
    assert not ids_processor._is_suspicious_dns("api.example.com")
    
    # Suspicious TLDs
    assert ids_processor._is_suspicious_dns("malicious.onion")
    assert ids_processor._is_suspicious_dns("hidden.i2p")
    
    # Suspicious patterns
    assert ids_processor._is_suspicious_dns("dns-tunnel.example.com")
    assert ids_processor._is_suspicious_dns("data-exfil.example.com")


# ============================================================================
# TESTS: CONFIDENCE SCORING
# ============================================================================

def test_calculate_confidence(ids_processor):
    """Test confidence score calculation"""
    assert ids_processor._calculate_confidence("critical") == 0.95
    assert ids_processor._calculate_confidence("high") == 0.85
    assert ids_processor._calculate_confidence("warning") == 0.7
    assert ids_processor._calculate_confidence("info") == 0.5
    assert ids_processor._calculate_confidence("unknown") == 0.5


# ============================================================================
# TESTS: SEVERITY CLASSIFICATION
# ============================================================================

def test_classify_severity(ids_processor):
    """Test severity classification by rule ID"""
    # SQL injection range
    assert ids_processor._classify_severity(500001, "SQLi") == "critical"
    
    # Network attack range
    assert ids_processor._classify_severity(610001, "DoS") == "high"
    
    # Anomaly range
    assert ids_processor._classify_severity(700001, "Anomaly") == "warning"
    
    # Unknown
    assert ids_processor._classify_severity(None, "unknown") == "warning"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_alert_processing(ids_processor, sample_sql_injection_alert):
    """End-to-end test of alert processing"""
    alert = SuricataAlert(**sample_sql_injection_alert)
    
    with patch.object(ids_processor, '_send_to_alertmanager', new_callable=AsyncMock):
        await ids_processor._handle_alert(alert)
    
    # Verify alert was processed
    assert sample_sql_injection_alert["src_ip"] in ids_processor.threat_db
    assert ids_processor.threat_db[sample_sql_injection_alert["src_ip"]].count >= 1


@pytest.mark.asyncio
async def test_multiple_attacks_from_same_ip(ids_processor):
    """Test handling multiple attacks from same IP"""
    ip = "192.168.1.100"
    
    for i in range(6):  # Exceed threshold of 5
        alert_data = {
            "timestamp": (datetime.utcnow() + timedelta(seconds=i)).isoformat() + "Z",
            "event_type": "alert",
            "src_ip": ip,
            "dest_ip": "10.0.0.5",
            "src_port": 54321 + i,
            "dest_port": 80 + i,
            "proto": "tcp",
            "alert": {
                "action": "alert",
                "signature": f"Attack {i}",
                "signature_id": 500001,
                "severity": 1,
                "category": "Web Application Attack",
            },
        }
        alert = SuricataAlert(**alert_data)
        
        with patch.object(ids_processor, '_send_to_alertmanager', new_callable=AsyncMock):
            with patch.object(ids_processor, '_blacklist_ip', new_callable=AsyncMock) as mock_blacklist:
                await ids_processor._handle_alert(alert)
                
                if i >= 4:  # After 5th alert
                    assert mock_blacklist.called
    
    # Verify IP is in threat database
    assert ip in ids_processor.threat_db
    assert ids_processor.threat_db[ip].count == 6


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_performance_alert_processing(ids_processor):
    """Test performance with high alert volume"""
    import time
    
    start = time.time()
    
    # Process 100 alerts
    for i in range(100):
        alert_data = {
            "timestamp": (datetime.utcnow() + timedelta(seconds=i)).isoformat() + "Z",
            "event_type": "alert",
            "src_ip": f"192.168.{i // 256}.{i % 256}",
            "dest_ip": "10.0.0.5",
            "src_port": 54321,
            "dest_port": 80,
            "proto": "tcp",
            "alert": {
                "action": "alert",
                "signature": "Test Alert",
                "signature_id": 500001,
                "severity": 1,
                "category": "Test",
            },
        }
        alert = SuricataAlert(**alert_data)
        
        with patch.object(ids_processor, '_send_to_alertmanager', new_callable=AsyncMock):
            await ids_processor._handle_alert(alert)
    
    elapsed = time.time() - start
    
    # Should process 100 alerts in less than 5 seconds
    assert elapsed < 5.0
    assert len(ids_processor.threat_db) <= 100
