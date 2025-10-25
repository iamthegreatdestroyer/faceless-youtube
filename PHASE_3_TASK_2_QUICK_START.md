# Phase 3, Task 2: Web Application Firewall (WAF) - QUICK START

**Status:** READY TO START  
**Estimated Duration:** 2.5-3 hours  
**Priority:** CRITICAL  
**Can Run In Parallel:** Yes (with other foundation tasks)

---

## 🎯 Task 2 Overview

Deploy ModSecurity Web Application Firewall (WAF) with OWASP Core Rule Set v4.0 to provide application-layer attack prevention.

**Key Objectives:**
1. Configure ModSecurity as Nginx module
2. Deploy OWASP Core Rule Set v4.0 (300+ rules)
3. Implement audit logging and forensics
4. Create WAF event processor
5. Build Grafana dashboard

**Success Criteria:**
- ✅ Block all OWASP Top 10 attacks
- ✅ 0% legitimate request blocking
- ✅ <10ms latency added
- ✅ Full audit trail for all blocks
- ✅ Real-time alerting

---

## 📋 Deliverables Checklist

**Primary Deliverables:**
- [ ] `modsecurity/modsecurity.conf` - Core WAF configuration
- [ ] `modsecurity/crs-setup.conf` - OWASP CRS v4.0 setup
- [ ] `modsecurity/crs/rules/` - CRS rule files
- [ ] Updated `nginx/nginx.conf` - WAF integration
- [ ] `src/security/waf_logger.py` - Event processing
- [ ] `tests/security/test_waf_logger.py` - Unit tests
- [ ] Grafana WAF dashboard JSON

**Support Files:**
- [ ] `modsecurity/modsecurity-custom-rules.conf` - Application-specific rules
- [ ] `nginx/modsecurity-locations.conf` - URL-based WAF tuning
- [ ] `docker-compose.staging.yml` - Nginx update

---

## 🚀 Implementation Steps

### Step 1: Create ModSecurity Configuration (30 min)
```
File: modsecurity/modsecurity.conf
Tasks:
- Core settings (mode, logging, rule engine)
- Request body limits (10MB)
- Response body limits (512KB)
- Audit logging configuration
- Exceptions and exclusions
- Performance tuning
```

### Step 2: Setup OWASP CRS (45 min)
```
File: modsecurity/crs-setup.conf
Tasks:
- Include CRS rules directory
- Configure paranoia level (default: 1)
- Set anomaly thresholds
- Enable specific rule groups
- Database drivers
- Argument limits
```

### Step 3: Nginx Integration (45 min)
```
File: nginx/nginx.conf
Tasks:
- Load ModSecurity module
- Connect main config
- Configure logging location
- Set up SSL/TLS
- Add security headers
```

### Step 4: WAF Event Processor (30 min)
```
File: src/security/waf_logger.py
Tasks:
- Parse ModSecurity audit logs
- Classify attack types
- Create Alertmanager notifications
- Track blocked IPs
- Generate metrics
```

### Step 5: Testing & Validation (20 min)
```
Tasks:
- Test attack scenarios
- Validate legitimate traffic
- Measure performance impact
- Verify alert routing
```

---

## 🛡️ Attack Coverage

**OWASP Top 10 Coverage (via CRS):**

1. **SQL Injection** - 50+ rules
2. **Broken Authentication** - 20+ rules
3. **Sensitive Data Exposure** - 30+ rules
4. **XML External Entities (XXE)** - 15+ rules
5. **Broken Access Control** - 25+ rules
6. **Security Misconfiguration** - 20+ rules
7. **Cross-Site Scripting (XSS)** - 60+ rules
8. **Insecure Deserialization** - 15+ rules
9. **Using Components with Known Vulnerabilities** - 40+ rules
10. **Insufficient Logging/Monitoring** - 10+ rules

**Additional Protections:**
- Protocol enforcement (HTTP/2, TLS validation)
- Scanner detection (Nmap, Nikto, etc.)
- Bot detection (unusual behavior)
- Session fixation prevention
- CSRF token validation
- Local file inclusion (LFI) prevention
- Remote code execution (RCE) prevention
- HTTP response splitting prevention

---

## 📊 Configuration Details

### ModSecurity Modes
```
SecRuleEngine On        # Full blocking mode
SecAuditLogRelevantOnly # Only log relevant events
SecAuditLogStatus       # Log based on HTTP status
```

### Paranoia Levels
```
PL1: 0-2 false positives per 1000 requests (default)
PL2: More sensitive, slight FP increase
PL3: High sensitivity, more maintenance
PL4: Maximum sensitivity, tuning required
```

### Rule Actions
```
ALLOW   - Allow request
DENY    - Block request (403)
DROP    - Close connection
PASS    - Log but don't block
```

---

## 🔍 Testing Scenarios

**Test Cases:**
1. SQL Injection: `' OR '1'='1`
2. XSS: `<script>alert('xss')</script>`
3. Command Injection: `; ls -la`
4. Path Traversal: `../../etc/passwd`
5. XXE: `<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>`
6. CSRF: Missing/invalid token
7. Authentication Bypass: Default credentials

---

## 📈 Performance Targets

| Metric | Target | Notes |
| --- | --- | --- |
| **Latency Added** | <10ms | Per request overhead |
| **Throughput** | >1000 req/s | Staging benchmark |
| **Memory** | <100MB | ModSecurity + CRS |
| **CPU** | <5% per core | At 100 req/s |
| **Block Latency** | <1ms | Decision time |
| **Audit Logging** | <2ms | Per blocked request |

---

## 🔗 Integration Points

**Upstream:**
- Nginx receiving client requests

**Downstream:**
- ModSecurity audit logs
- WAF event processor
- Alertmanager notifications
- Prometheus metrics
- Grafana dashboard

---

## 📚 Reference Files

**From Task 1 (Already Complete):**
- IDS processor pattern: `src/security/ids_alerter.py`
- Alert notification format: `AlertNotification` model
- Docker compose structure: `docker-compose.staging.yml`
- Test patterns: `tests/security/test_ids_alerter.py`

**For Task 2:**
- Use similar async logging patterns
- Reuse alert models from Task 1
- Follow same Docker integration approach
- Use same test structure

---

## ⏱️ Time Breakdown

| Component | Time | Status |
| --- | --- | --- |
| ModSecurity config | 30 min | ⏳ |
| OWASP CRS setup | 45 min | ⏳ |
| Nginx integration | 45 min | ⏳ |
| WAF event processor | 30 min | ⏳ |
| Testing & validation | 20 min | ⏳ |
| **TOTAL** | **2.5-3 hours** | **READY** |

---

## ✅ Ready to Begin?

**Prerequisites Met:**
- ✅ Task 1 complete (IDS/IPS)
- ✅ Docker compose configured
- ✅ Monitoring stack operational
- ✅ Alert infrastructure ready
- ✅ Test patterns established

**Command to Start Task 2:**
```bash
# When ready, proceed with WAF implementation
# All specifications in PHASE_3_ADVANCED_SECURITY_PLAN.md
```

---

**Task 2 is ready to begin immediately after Task 1 completion.**  
*Estimated completion: 2.5-3 hours from start*  
*Target completion: Oct 25, 18:00 UTC (alongside other foundation tasks)*

---

**Next Phase 3 Tasks After Task 2:**
- Task 3: Vulnerability Scanning (2-2.5h)
- Task 4: Compliance Monitoring (2-2.5h)
- Task 5: Rate Limiting (1.5-2h)
- Task 6: Secrets Rotation (1.5h)
- Task 7: Testing & Documentation (4-5h)
