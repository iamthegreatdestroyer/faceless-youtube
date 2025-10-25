# 🐳 Docker Orchestration Scripts

**Purpose:** Container management and service orchestration  
**Status:** ✅ Production Ready  
**Environment Support:** Windows, Linux, macOS

---

## 🚀 Quick Start

### Start All Services (Docker)

**Windows:**

```bash
docker-start.bat
```

**Linux/macOS:**

```bash
chmod +x docker-start.sh
./docker-start.sh
```

**What It Does:**

1. Validates Docker installation
2. Builds images if needed
3. Starts all services (FastAPI, React, PostgreSQL, Redis, MongoDB)
4. Waits for health checks
5. Reports status

**Typical Output:**

```
✓ Docker validated
✓ Building images...
✓ Starting services...
✓ API: http://localhost:8001 ✓
✓ Dashboard: http://localhost:3000 ✓
✓ All services healthy
```

**Time:** 1-2 minutes

---

## 📋 Docker Configuration Files

### `docker-compose.yml`

- **Purpose:** Development/testing docker configuration
- **Services:** API, Dashboard, PostgreSQL, Redis, MongoDB
- **Port Mappings:**
  - FastAPI: 8001
  - React: 3000
  - PostgreSQL: 5432
  - Redis: 6379
  - MongoDB: 27017

**Usage:**

```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f
```

---

### `docker-compose.staging.yml`

- **Purpose:** Staging environment configuration
- **Services:** Production-like setup with health checks
- **Resource Limits:** Defined for staging
- **Volume Mounts:** Production directories

**Usage:**

```bash
docker-compose -f docker-compose.staging.yml up -d
```

---

### `docker-compose.prod.yml`

- **Purpose:** Production environment configuration
- **Services:** Optimized for performance
- **Resource Limits:** Production specs
- **Health Checks:** Aggressive monitoring

**Usage:**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔧 Deployment & Production

### `deploy-prod.sh`

- **Purpose:** Production deployment automation
- **Platform:** Linux/macOS
- **Features:**
  - Pre-deployment validation
  - Zero-downtime deployment
  - Automated backups
  - Health check validation
  - Rollback support

**Usage:**

```bash
chmod +x deploy-prod.sh
./deploy-prod.sh
```

**Prerequisites:**

- Linux/macOS environment
- Docker & Docker Compose installed
- SSH access to production server
- Environment variables configured

**What It Does:**

1. Validates production environment
2. Backs up current deployment
3. Pulls latest images
4. Updates containers
5. Verifies health checks
6. Reports deployment status

---

## 📊 Service Status

### Check Service Status

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f dashboard
```

### Service Health

All services include health checks:

- **API:** HTTP 200 on /health
- **Dashboard:** HTTP 200 on /
- **PostgreSQL:** TCP 5432
- **Redis:** TCP 6379
- **MongoDB:** TCP 27017

---

## 🛑 Stop Services

### Graceful Shutdown

```bash
docker-compose down
```

### Force Stop

```bash
docker-compose kill
```

---

## 🔄 Restart Services

### Restart All

```bash
docker-compose restart
```

### Restart Specific Service

```bash
docker-compose restart api
docker-compose restart dashboard
```

---

## 🧹 Cleanup

### Remove Containers (Keep Volumes)

```bash
docker-compose down
```

### Remove Everything (Including Data!)

```bash
docker-compose down -v
```

### Prune Unused Images

```bash
docker image prune -a
```

---

## 🆘 Troubleshooting

### Issue: Port already in use

**Solution:**

```bash
# Find what's using the port
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux/macOS

# Stop conflicting service or use different port
```

### Issue: Services won't start

**Solution:**

1. Check Docker: `docker --version`
2. Check logs: `docker-compose logs`
3. Verify volumes: `docker volume ls`
4. Review `.env` configuration

### Issue: Health checks failing

**Solution:**

1. Check service logs: `docker-compose logs api`
2. Increase health check timeout in docker-compose.yml
3. Ensure ports are accessible
4. Verify resource availability

---

## 📈 Performance Tips

### Resource Allocation

Configure in docker-compose.yml:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
```

### Volume Performance

Use named volumes for databases:

```yaml
volumes:
  postgres_data:
  redis_data:
  mongodb_data:
```

---

## 📞 For More Help

- **Full Deployment Guide:** `.documentation/03_deployment/DEPLOYMENT_CHECKLIST.md`
- **Docker Commands:** `.documentation/03_deployment/docker-compose.yml`
- **Troubleshooting:** `.documentation/02_quick_start/QUICK_FIX_GUIDE.md`

---

**Last Updated:** October 25, 2025  
**Status:** ✅ Production Ready
