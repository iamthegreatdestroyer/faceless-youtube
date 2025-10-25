# Phase 2: Operational Hardening Plan

**Status:** In Progress  
**Start Date:** October 25, 2025  
**Target Completion:** October 25, 2025 (6-8 hours)  
**Previous Phase:** Phase 1 Security Hardening (✅ 100% Complete)

---

## 🎯 Phase 2 Objective

Transform the staging environment from **Secure-but-Blind** to **Secure-Aware** by implementing comprehensive operational visibility:

- **Logs:** Centralized collection, parsing, searching (Loki + Promtail)
- **Metrics:** Real-time performance monitoring (Prometheus)
- **Alerts:** Proactive issue detection (Alertmanager)
- **Dashboards:** Unified visibility (Grafana)
- **Backups:** Disaster recovery readiness (PostgreSQL automated backups)

**Result:** Complete observability of security posture and operational health.

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     STAGING ENVIRONMENT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │   Nginx    │  │  FastAPI   │  │ PostgreSQL │               │
│  │ (TLS/SSL)  │  │   (API)    │  │ (Database) │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│         │              │                │                       │
│         ├──────────────┼────────────────┤                       │
│         │              │                │                       │
│    [HTTP/HTTPS]   [FastAPI Logs]  [PostgreSQL Logs]           │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │          LOG AGGREGATION LAYER (Loki + Promtail)      │   │
│  │  - Ingests logs from all sources                       │   │
│  │  - Label-based indexing for fast queries               │   │
│  │  - Volume mount: logs/loki                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────┼────────────────────────────────┐   │
│  │   METRICS COLLECTION (Prometheus)                      │   │
│  │  - Scrapes metrics from exporters                       │   │
│  │  - Stores time-series data                              │   │
│  │  - Volume mount: prometheus-data                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────┼────────────────────────────────┐   │
│  │  ALERTING (Alertmanager)                               │   │
│  │  - Triggers on metric thresholds                        │   │
│  │  - Routes to notification channels                      │   │
│  │  - Config: alertmanager.yml                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────┴────────────────────────────────┐   │
│  │  VISUALIZATION (Grafana)                               │   │
│  │  - Operational Health Dashboard                         │   │
│  │  - Security Metrics Dashboard                           │   │
│  │  - Performance Dashboard                                │   │
│  │  - System Resources Dashboard                           │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Tasks

### Task 1: Log Aggregation Setup (Loki)

**Estimate:** 90 minutes | **Status:** ⏳ Not Started

**Deliverables:**

1. `loki/loki-config.yml` - Loki configuration
2. `promtail/promtail-config.yml` - Promtail configuration
3. `src/core/logging.py` - Structured logging setup
4. Updated `docker-compose.staging.yml` - Loki + Promtail services
5. Volume mounts for log persistence

**Key Features:**

- JSON-structured logging (FastAPI requests, responses, errors)
- PostgreSQL query logs
- Nginx access/error logs
- Label-based indexing (service, environment, level)
- 30-day retention policy

**Implementation Steps:**

```
1. Create Loki configuration (label extraction, retention)
2. Create Promtail configuration (log pipeline, parsers)
3. Add structured logging to FastAPI
4. Add Loki + Promtail containers to docker-compose
5. Configure log volume mounts
6. Test log ingestion and querying
```

---

### Task 2: Metrics Collection (Prometheus)

**Estimate:** 75 minutes | **Status:** ⏳ Not Started

**Deliverables:**

1. `prometheus/prometheus.yml` - Prometheus configuration
2. `src/core/metrics.py` - Prometheus client setup
3. FastAPI metrics endpoints (using prometheus-client)
4. PostgreSQL exporter configuration
5. Redis exporter configuration
6. Updated `docker-compose.staging.yml` - Prometheus service

**Key Features:**

- FastAPI metrics (requests, latency, errors, by endpoint)
- PostgreSQL metrics (connections, queries, cache hit ratio)
- Redis metrics (commands, memory, evictions)
- System metrics (CPU, memory, disk, network)
- 15-second scrape interval
- 30-day data retention

**Metrics to Collect:**

```
FastAPI:
- request_count{method, endpoint, status}
- request_duration_seconds{method, endpoint}
- active_connections
- connection_errors

PostgreSQL:
- pg_stat_statements (query timing)
- pg_database_size
- pg_connections_used
- pg_cache_hit_ratio

Redis:
- redis_connected_clients
- redis_used_memory
- redis_commands_total
- redis_evicted_keys

System:
- node_cpu_seconds_total
- node_memory_bytes_total
- node_disk_bytes_free
```

**Implementation Steps:**

```
1. Create prometheus.yml with scrape configs
2. Add prometheus-client to FastAPI
3. Set up PostgreSQL exporter
4. Set up Redis exporter
5. Add Prometheus container to docker-compose
6. Configure metric retention and compression
7. Test metric scraping
```

---

### Task 3: Alert Configuration (Alertmanager)

**Estimate:** 60 minutes | **Status:** ⏳ Not Started

**Deliverables:**

1. `alertmanager/alertmanager.yml` - Alert routing and grouping
2. `prometheus/alert-rules.yml` - Alert rule definitions
3. Notification templates (email, webhook, Slack)
4. Updated `docker-compose.staging.yml` - Alertmanager service

**Alert Categories:**

**Security Alerts:**

- Unauthorized API access attempts
- Database connection failures
- SSL certificate expiration
- Rate limit threshold exceeded

**Performance Alerts:**

- High request latency (>1000ms P95)
- High error rate (>1%)
- Database slow queries
- Redis memory usage >80%

**Operational Alerts:**

- Service health check failures
- Disk space <10% free
- Memory usage >90%
- Backup job failures

**Implementation Steps:**

```
1. Define alert rules (thresholds, durations)
2. Create alertmanager configuration
3. Set up notification channels (webhook for staging)
4. Create alert templates
5. Add Alertmanager container to docker-compose
6. Test alert triggering and routing
7. Document runbooks for each alert
```

---

### Task 4: Monitoring Dashboards (Grafana)

**Estimate:** 90 minutes | **Status:** ⏳ Not Started

**Deliverables:**

1. `grafana/dashboards/operational-health.json` - Operational overview
2. `grafana/dashboards/security-metrics.json` - Security monitoring
3. `grafana/dashboards/performance.json` - Performance analysis
4. `grafana/dashboards/system-resources.json` - System metrics
5. `grafana/provisioning/datasources.yml` - Data source config
6. Updated `docker-compose.staging.yml` - Grafana service

**Dashboards:**

**1. Operational Health Dashboard:**

- Service status indicators (API, Database, Redis, Nginx)
- Request throughput (RPS)
- Error rate trends
- Active connections
- Last 24h timeline

**2. Security Metrics Dashboard:**

- Failed auth attempts
- Rate-limited requests
- SSL certificate validity
- Database audit logs
- Security alerts fired

**3. Performance Dashboard:**

- Request latency (P50, P95, P99)
- Database query timing
- Cache hit ratios
- CPU/Memory usage
- Network throughput

**4. System Resources Dashboard:**

- Node CPU utilization
- Memory usage trends
- Disk space free
- Network I/O
- Container resource usage

**Implementation Steps:**

```
1. Create Grafana datasource configs
2. Create operational health dashboard
3. Create security metrics dashboard
4. Create performance dashboard
5. Create system resources dashboard
6. Set up dashboard provisioning
7. Add Grafana container to docker-compose
8. Test dashboard updates and drill-down
```

---

### Task 5: Database Backups & Disaster Recovery

**Estimate:** 45 minutes | **Status:** ⏳ Not Started

**Deliverables:**

1. `backup/backup-postgres.sh` - Automated backup script
2. `backup/restore-postgres.sh` - Restore procedure
3. `backup/verify-backup.sh` - Backup validation
4. `docker-compose.staging.yml` - Backup service with cron
5. `.env.backup` - Backup configuration template

**Backup Strategy:**

**Daily Full Backups:**

- Time: 02:00 UTC (off-peak)
- Format: SQL dump (compressed)
- Location: `backups/postgres/daily/`
- Retention: 7 days (1 week)

**Weekly Archive Backups:**

- Time: Sunday 03:00 UTC
- Format: SQL dump (compressed, encrypted)
- Location: `backups/postgres/archives/`
- Retention: 12 weeks (3 months)

**Backup Verification:**

- Automatic: After each backup
- Check: File size, compression, integrity
- Restore test: Weekly (sample data)

**Implementation Steps:**

```
1. Create backup script with rotation
2. Create restore procedure with verification
3. Set up PostgreSQL backup container
4. Configure cron-based scheduling
5. Test backup and restore cycle
6. Verify backup integrity
7. Document disaster recovery procedure
```

---

## 🔄 Execution Sequence

```
PHASE 2 EXECUTION TIMELINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

09:00 - 10:30  [Task 1] Log Aggregation (Loki)
               └─ Create configs, add containers, test ingestion

10:30 - 11:45  [Task 2] Metrics Collection (Prometheus)
               └─ Set up scrape configs, exporters, test metrics

11:45 - 12:45  [Task 3] Alerting (Alertmanager)
               └─ Create rules, routes, notification templates

12:45 - 14:15  [Task 4] Dashboards (Grafana)
               └─ Create all 4 dashboards, test updates

14:15 - 15:00  [Task 5] Backups & DR (PostgreSQL)
               └─ Automated backups, restore procedures

15:00 - 15:30  [Validation] End-to-end testing
               └─ All services operational, data flowing

15:30 - 16:00  [Documentation] Create guides & complete
               └─ Comprehensive documentation, final commits

TOTAL: 6-7 hours
```

---

## ✅ Success Criteria

### By End of Phase 2, All Must Be True:

**Logging:**

- ✅ Loki receives logs from all sources
- ✅ Promtail parses structured logs
- ✅ Can search logs by label and time range
- ✅ Log retention working (30-day policy)

**Metrics:**

- ✅ Prometheus scrapes all targets every 15 seconds
- ✅ Metrics accessible via Prometheus API
- ✅ FastAPI, PostgreSQL, Redis metrics collected
- ✅ System metrics visible

**Alerting:**

- ✅ Alertmanager running and receiving alerts
- ✅ All alert rules defined and evaluating
- ✅ Notification channels configured and tested
- ✅ Alerts firing and routing correctly

**Dashboards:**

- ✅ Grafana connected to Prometheus and Loki
- ✅ All 4 dashboards created and operational
- ✅ Charts auto-refresh and display live data
- ✅ Dashboard drill-down working

**Backups:**

- ✅ Daily backups created automatically
- ✅ Backup verification running successfully
- ✅ Restore procedure tested and documented
- ✅ Backup retention policies enforced

**Performance:**

- ✅ No latency degradation from Phase 1 (still <15ms P95)
- ✅ Monitoring overhead <5% CPU
- ✅ Memory usage within limits
- ✅ Disk space for logs/metrics sufficient

**Documentation:**

- ✅ All operational procedures documented
- ✅ Troubleshooting guides included
- ✅ Runbooks for each alert created
- ✅ Git commits with detailed messages

---

## 🛠️ Technical Specifications

### Container Specifications

**Loki Container:**

- Image: `grafana/loki:latest`
- Memory: 256MB
- CPU: 0.5
- Volumes: logs/loki (5GB)
- Ports: 3100 (internal only)

**Promtail Container:**

- Image: `grafana/promtail:latest`
- Memory: 128MB
- CPU: 0.25
- Volumes: logs (all container logs)
- Ports: 9080 (internal only)

**Prometheus Container:**

- Image: `prom/prometheus:latest`
- Memory: 512MB
- CPU: 0.5
- Volumes: prometheus-data (10GB), prometheus.yml
- Ports: 9090
- Retention: 30 days

**Alertmanager Container:**

- Image: `prom/alertmanager:latest`
- Memory: 256MB
- CPU: 0.25
- Volumes: alertmanager.yml
- Ports: 9093 (internal only)

**Grafana Container:**

- Image: `grafana/grafana:latest`
- Memory: 512MB
- CPU: 0.5
- Volumes: grafana-storage (2GB), provisioning
- Ports: 3000
- Root URL: https://localhost/grafana

**PostgreSQL Backup Sidecar:**

- Image: Custom (backup script)
- Memory: 256MB
- CPU: 0.25
- Cron: 02:00 UTC daily
- Volumes: backups (50GB for 3 months retention)

---

## 📦 File Structure

```
Phase 2 Deliverables:
├── loki/
│   ├── loki-config.yml
│   └── loki-alerts.yml
├── promtail/
│   └── promtail-config.yml
├── prometheus/
│   ├── prometheus.yml
│   └── alert-rules.yml
├── alertmanager/
│   ├── alertmanager.yml
│   └── notification-templates.yml
├── grafana/
│   ├── dashboards/
│   │   ├── operational-health.json
│   │   ├── security-metrics.json
│   │   ├── performance.json
│   │   └── system-resources.json
│   └── provisioning/
│       └── datasources.yml
├── backup/
│   ├── backup-postgres.sh
│   ├── restore-postgres.sh
│   └── verify-backup.sh
├── src/core/
│   ├── logging.py (UPDATED)
│   └── metrics.py (NEW)
├── docker-compose.staging.yml (UPDATED)
└── .env.backup (NEW template)
```

---

## 🚀 Next Steps

1. **Immediate:** Begin Task 1 (Log Aggregation)
2. **Sequential:** Complete Tasks 2-5 in order
3. **Parallel Possible:** After Task 1, Tasks 2 & 5 can run in parallel
4. **Integration:** Test all services together after each major task
5. **Validation:** Run comprehensive E2E tests
6. **Documentation:** Create operational guides and runbooks

---

## 📞 Risk Mitigation

| Risk                    | Mitigation                               | Owner               |
| ----------------------- | ---------------------------------------- | ------------------- |
| Disk space exhaustion   | 30-day log/metric retention + monitoring | Loki config         |
| Performance degradation | Benchmark current state first            | Metrics collection  |
| Alert fatigue           | Tuned thresholds + grouping              | Alertmanager config |
| Backup failures         | Automated verification + testing         | Backup script       |
| Dashboard outdated data | Auto-refresh every 30s                   | Grafana config      |

---

## ✨ Phase 2 Completion Signals

**When complete, you will see:**

```
✅ Loki: Receiving logs from all sources
✅ Prometheus: Scraping metrics every 15s
✅ Alertmanager: Alert rules evaluating
✅ Grafana: All dashboards displaying live data
✅ Backups: Daily automation working
✅ Documentation: Complete operational guides
✅ Git: All changes committed with detailed messages
✅ Performance: No degradation from Phase 1
```

**Expected Timeline:** 6-8 hours to complete all tasks  
**Target Completion:** October 25, 2025 (end of business)

---

**Ready to begin? Starting Task 1: Log Aggregation (Loki) immediately.** 🚀
