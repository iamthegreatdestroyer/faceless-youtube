# Item 2: TLS/HTTPS Enforcement - Implementation Guide

**Priority:** CRITICAL  
**Estimated Effort:** 2-3 hours  
**Status:** ⏳ READY FOR IMPLEMENTATION  
**Target:** Oct 24, 8:00-11:00 UTC

---

## Overview

This guide implements HTTPS-only enforcement for the staging environment. All HTTP traffic will redirect to HTTPS, and HSTS headers (already in place from Item 1) will enforce continued HTTPS usage.

---

## Current State

```
Staging Environment (docker-compose.staging.yml):
- API Service: Port 8001:8000 (HTTP only)
- Protocol: HTTP (unencrypted)
- Status: No TLS/HTTPS configured

Security Headers Status (from Item 1):
- ✅ Strict-Transport-Security: Present but ineffective without HTTPS
- ✅ All 8 headers properly configured
- ⏳ HSTS preload: Waiting for HTTPS enforcement
```

---

## Implementation Approach

### Phase 1: Generate Self-Signed Certificates (for staging/testing)

**Why self-signed?** For staging environment, we'll use self-signed certificates. Production deployment can use Let's Encrypt.

**Steps:**

1. Create directory for SSL certificates
2. Generate private key
3. Generate self-signed certificate
4. Add to docker-compose volume mounts

### Phase 2: Configure Docker Compose for HTTPS

**Configuration:**

- Map port 443 (HTTPS) to internal port 8000
- Keep HTTP port 8000 for internal communication
- Volume mount SSL certificates
- Environment variables for certificate paths

### Phase 3: Add HTTPS Redirect Middleware (optional)

**Why optional?** Nginx reverse proxy will handle most redirects. We can add FastAPI middleware as belt-and-suspenders approach.

### Phase 4: Test HTTPS Enforcement

**Verification:**

- Test HTTPS access: `curl -k https://localhost:8001/api/v1/health`
- Test HTTP redirect: `curl -I http://localhost:8001/api/v1/health`
- Verify certificate: `openssl s_client -connect localhost:8001`
- Performance check: Ensure P95 < 100ms maintained

---

## Implementation Steps

### STEP 1: Generate Self-Signed SSL Certificates

**Location:** Create `certs/` directory at project root

**Commands:**

```bash
# Create certs directory
mkdir -p certs

# Generate 2048-bit RSA private key (valid for 365 days)
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

# Verify certificate
openssl x509 -in certs/cert.pem -text -noout
```

**Expected Output:**

```
certs/
├── cert.pem (self-signed certificate)
└── key.pem (private key)
```

**Certificate Details:**

- Issuer: Self-signed
- Subject: CN=localhost
- Validity: 365 days from generation
- Key Type: RSA 2048-bit
- Algorithm: sha256WithRSAEncryption

### STEP 2: Create Nginx Configuration for SSL Termination

**Location:** Create `nginx/nginx.conf`

**Configuration:**

```nginx
# Nginx configuration for SSL termination and HTTPS redirect

upstream api {
    server app:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name localhost;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server block
server {
    listen 443 ssl http2;
    server_name localhost;
    
    # SSL configuration
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    
    # SSL protocol and cipher suite
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # SSL session configuration
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers (additional, headers middleware provides more)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Proxy configuration
    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### STEP 3: Update docker-compose.staging.yml

**Current Configuration:**

```yaml
services:
  api:
    image: faceless-youtube-api:staging
    container_name: api-staging
    ports:
      - "8001:8000"
    # ... rest of config
```

**Updated Configuration:**

```yaml
version: '3.8'

services:
  # Add Nginx service for SSL termination
  nginx-staging:
    image: nginx:latest
    container_name: nginx-staging
    ports:
      - "8001:443"  # HTTPS external port
      - "8080:80"   # HTTP redirect port (optional)
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
    networks:
      - staging-network
    healthcheck:
      test: ["CMD", "curl", "-f", "https://localhost/health", "--insecure"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  api:
    image: faceless-youtube-api:staging
    container_name: api-staging
    # Remove external port mapping (only internal)
    # ports: removed
    expose:
      - "8000"  # Expose only internally to nginx
    environment:
      - ENVIRONMENT=staging
      # ... other environment variables
    depends_on:
      - postgres-staging
      - redis-staging
      - mongodb-staging
    networks:
      - staging-network
    restart: unless-stopped
    # ... rest of config

  # ... other services (postgres, redis, mongodb, dashboard)
```

### STEP 4: FastAPI HTTPS Redirect Middleware (Optional)

**Location:** `src/api/middleware/https_redirect.py`

**Code:**

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Redirect HTTP requests to HTTPS.
    
    Note: This is optional when using Nginx for SSL termination.
    Nginx handles most redirects at the load balancer level.
    """
    
    async def dispatch(self, request: Request, call_next):
        # In staging/production with nginx, X-Forwarded-Proto header indicates original protocol
        if request.headers.get("X-Forwarded-Proto") == "http":
            # Extract the path and query string
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=url, status_code=307)  # Temporary redirect
        
        response = await call_next(request)
        return response
```

**Integration in main.py:**

```python
# Add this after security headers middleware (line 162 in main.py)
from src.api.middleware.https_redirect import HTTPSRedirectMiddleware

# In app setup section (around line 170):
if ENVIRONMENT == "staging":
    # Add HTTPS redirect middleware (optional with nginx)
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

## Testing & Verification

### Test 1: Generate Self-Signed Certificate

```bash
# Verify certificate was created
ls -la certs/
# Output: 
#   cert.pem (1024 bytes)
#   key.pem (1704 bytes)

# View certificate details
openssl x509 -in certs/cert.pem -text -noout | grep -A2 "Subject:"
# Output: Subject: CN=localhost
```

### Test 2: Start Docker Compose with TLS

```bash
# Stop existing containers
docker-compose -f docker-compose.staging.yml down

# Start with new configuration
docker-compose -f docker-compose.staging.yml up -d

# Verify services started
docker-compose -f docker-compose.staging.yml ps
# Expected: All services running (nginx, api, postgres, redis, mongodb, dashboard)
```

### Test 3: HTTPS Access

```bash
# Test HTTPS with self-signed cert (ignore cert warning)
curl -k -I https://localhost:8001/api/v1/health

# Expected response:
# HTTP/2 200
# strict-transport-security: max-age=31536000; includeSubDomains; preload
# x-content-type-options: nosniff
# x-frame-options: DENY
# ... (other security headers)
```

### Test 4: HTTP Redirect

```bash
# Test HTTP redirect
curl -I http://localhost:8080/api/v1/health

# Expected response:
# HTTP/1.1 301 Moved Permanently
# Location: https://localhost:443/api/v1/health
```

### Test 5: Certificate Verification

```bash
# View server certificate
openssl s_client -connect localhost:8001 -showcerts < /dev/null 2>/dev/null | \
  openssl x509 -text -noout | grep -E "Subject:|Issuer:|Not Before|Not After"

# Expected output:
# Subject: CN=localhost
# Issuer: CN=localhost
# Not Before: [generation date]
# Not After: [365 days from generation]
```

### Test 6: Performance Check

```bash
# Verify performance maintained
ab -n 100 -c 10 -k https://localhost:8001/api/v1/health

# Expected metrics (similar to pre-TLS baseline):
# Requests per second: >100
# Mean time per request: <50ms
# Failed requests: 0
```

### Test 7: API Endpoint Testing

```bash
# Test protected endpoint via HTTPS
curl -k -X POST https://localhost:8001/api/v1/videos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/video.mp4"}'

# Expected: 200 OK (or appropriate response)
```

---

## Docker Compose Port Configuration

### Port Mappings After Implementation

| Service | External Port | Internal Port | Protocol | Purpose |
|---------|---------------|---------------|----------|---------|
| Nginx | 8001 | 443 | HTTPS | API access (encrypted) |
| Nginx | 8080 | 80 | HTTP | Redirect only |
| API | N/A | 8000 | HTTP | Internal to Nginx |
| Dashboard | 3000 | 3000 | HTTP | Internal dashboard |
| PostgreSQL | N/A | 5432 | TCP | Database (internal) |
| Redis | N/A | 6379 | TCP | Cache (internal) |
| MongoDB | N/A | 27017 | TCP | MongoDB (internal) |

---

## Verification Checklist

### Before Commit

- [ ] Certificates generated in `certs/` directory
- [ ] `nginx/nginx.conf` created with SSL configuration
- [ ] `docker-compose.staging.yml` updated with nginx service
- [ ] API service ports changed to internal-only
- [ ] HTTPS redirect middleware created (optional, but recommended)
- [ ] All tests pass (HTTPS access, redirects, performance)

### After Deployment

- [ ] `curl -k https://localhost:8001/api/v1/health` returns 200
- [ ] `curl -I http://localhost:8080/health` redirects to HTTPS
- [ ] Certificate details display with `openssl s_client`
- [ ] HSTS header present: `strict-transport-security: max-age=31536000; ...`
- [ ] Performance maintained: P95 < 100ms
- [ ] All existing tests still pass
- [ ] No breaking changes to API functionality

---

## File Summary

### New Files Created

1. `certs/cert.pem` - Self-signed certificate (generated via openssl)
2. `certs/key.pem` - Private key (generated via openssl)
3. `nginx/nginx.conf` - Nginx configuration for SSL termination
4. `src/api/middleware/https_redirect.py` - Optional HTTPS redirect middleware

### Modified Files

1. `docker-compose.staging.yml` - Add nginx service, update API service
2. `src/api/main.py` - Add HTTPS redirect middleware (if using optional middleware)

### No Changes Required

- `src/api/middleware/security.py` - Already has all HSTS headers
- `src/api/main.py` (except optional middleware) - No changes needed

---

## Rollback Plan

If issues occur:

```bash
# Revert to HTTP-only configuration
git checkout HEAD -- docker-compose.staging.yml

# Restart containers
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d

# Verify HTTP access works
curl -I http://localhost:8001/api/v1/health
```

---

## Next Steps

1. ✅ Generate self-signed certificates
2. ✅ Create nginx configuration
3. ✅ Update docker-compose.staging.yml
4. ✅ Test HTTPS access and redirects
5. ✅ Verify performance maintained
6. ✅ Commit changes to git
7. ⏳ Move to Item 3: Database Hardening

---

## Timeline

- **Certificate Generation:** 5 minutes
- **Nginx Configuration:** 10 minutes
- **Docker Compose Update:** 10 minutes
- **Testing:** 20 minutes
- **Troubleshooting (if needed):** 30 minutes
- **Documentation & Commit:** 10 minutes

**Total Expected Time: 45 minutes - 1 hour 45 minutes**

---

## References

- [OpenSSL Documentation](https://www.openssl.org/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Docker Compose Volumes](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
- [FastAPI HTTPS](https://fastapi.tiangolo.com/deployment/https/)
- [HSTS Preload](https://hstspreload.org/)

---

**Status:** Ready for implementation ✅  
**Next Action:** Generate SSL certificates and begin Step 1
