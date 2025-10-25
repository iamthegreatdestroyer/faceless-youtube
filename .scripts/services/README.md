# 🚀 Service Startup Scripts

**Purpose:** Individual service management and startup  
**Status:** ✅ Production Ready  
**Deployment Options:** Local (host system) or via Docker

---

## 📋 Service Overview

| Service       | Port | Purpose         | Status    |
| ------------- | ---- | --------------- | --------- |
| **API**       | 8001 | FastAPI backend | Essential |
| **Dashboard** | 3000 | React frontend  | Essential |

---

## 🔧 API Service

### Windows: `run-api.bat`

- **Purpose:** Start FastAPI backend (Windows)
- **Platform:** Windows 10/11
- **Requirements:**
  - Python 3.11+
  - Virtual environment created
  - Dependencies installed
  - `.env` configured

**Usage:**

```bash
run-api.bat
```

**What It Does:**

1. Activates virtual environment
2. Validates configuration
3. Starts FastAPI server on port 8001
4. Monitors for errors
5. Auto-restarts on failure

**Expected Output:**

```
Activating virtual environment...
Starting FastAPI server...
INFO: Uvicorn running on http://127.0.0.1:8001
```

**Access:**

- API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

### Linux/macOS: `run-api.sh`

- **Purpose:** Start FastAPI backend (Linux/macOS)
- **Platform:** Ubuntu 20.04+, Debian 11+, macOS 12+

**Usage:**

```bash
chmod +x run-api.sh
./run-api.sh
```

**Same as Windows version**, just for Unix systems.

---

## 🎨 Dashboard Service

### Windows: `run-dashboard.bat`

- **Purpose:** Start React dashboard (Windows)
- **Platform:** Windows 10/11
- **Requirements:**
  - Node.js 16+ / npm
  - Dependencies installed
  - `.env` configured

**Usage:**

```bash
run-dashboard.bat
```

**What It Does:**

1. Activates virtual environment (if needed)
2. Navigates to dashboard directory
3. Validates Node.js installation
4. Starts React dev server on port 3000
5. Monitors for errors

**Expected Output:**

```
Starting React development server...
  Ready on http://127.0.0.1:3000
```

**Access:**

- Dashboard: http://localhost:3000

---

### Linux/macOS: `run-dashboard.sh`

- **Purpose:** Start React dashboard (Linux/macOS)
- **Platform:** Ubuntu 20.04+, Debian 11+, macOS 12+

**Usage:**

```bash
chmod +x run-dashboard.sh
./run-dashboard.sh
```

**Same as Windows version**, just for Unix systems.

---

## ▶️ Universal Startup Scripts

### Windows: `start.bat`

- **Purpose:** Start all local services (Windows)
- **Starts:**
  - PostgreSQL database
  - Redis cache
  - MongoDB storage
  - FastAPI backend
  - React dashboard

**Usage:**

```bash
start.bat
```

---

### Linux/macOS: `start.sh`

- **Purpose:** Start all local services (Linux/macOS)

**Usage:**

```bash
chmod +x start.sh
./start.sh
```

---

### Python: `start.py`

- **Purpose:** Cross-platform service startup
- **Works:** Windows, Linux, macOS
- **Advantage:** Consistent behavior across platforms

**Usage:**

```bash
python start.py
```

**Features:**

- Automatic platform detection
- Parallel service startup
- Health check validation
- Error reporting

---

## 🔀 Running Multiple Services

### Option 1: Sequential (Simple)

```bash
# Start API
./run-api.sh

# In another terminal, start Dashboard
./run-dashboard.sh
```

### Option 2: Parallel (Recommended)

```bash
# Start everything at once
./start.sh
```

### Option 3: Docker (Best for Production)

```bash
cd .scripts/docker
./docker-start.sh
```

---

## 📊 Service Status

### Check if Services are Running

**Windows:**

```bash
# Check port usage
netstat -ano | findstr :8001  # API
netstat -ano | findstr :3000  # Dashboard
```

**Linux/macOS:**

```bash
# Check port usage
lsof -i :8001  # API
lsof -i :3000  # Dashboard
```

---

## 🛑 Stopping Services

### Stop Individual Service

Press `Ctrl+C` in the terminal where service is running.

### Stop All Services (Windows)

```bash
# Find and kill processes
taskkill /F /IM python.exe  # API
taskkill /F /IM node.exe    # Dashboard
```

### Stop All Services (Linux/macOS)

```bash
killall python  # API
killall node    # Dashboard
```

---

## 🔄 Restarting Services

### Quick Restart

```bash
# Stop (Ctrl+C) then start again
./run-api.sh
```

### Full Restart with Database

```bash
./start.sh
```

---

## 🆘 Troubleshooting

### Issue: Port Already in Use

**Solution:**

1. Find what's using the port
2. Stop the conflicting process
3. Start service again

```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :8001
kill -9 <PID>
```

### Issue: Python/Node Not Found

**Solution:**

```bash
# Check versions
python --version
node --version

# If not found, install:
# Python: https://python.org
# Node: https://nodejs.org
```

### Issue: Service Won't Start

**Solution:**

1. Check logs: See terminal output
2. Verify `.env` configuration
3. Verify dependencies: `pip list`, `npm list`
4. Restart computer if needed

### Issue: Cannot Connect to Service

**Solution:**

1. Verify service is running (port check)
2. Verify firewall allows port
3. Check `.env` URL configuration
4. Try localhost vs 127.0.0.1

---

## 🎯 Common Usage Patterns

### Development (API Only)

```bash
./run-api.sh
# Then open http://localhost:8001/docs in browser
```

### Development (Full Stack)

```bash
./start.sh
# API: http://localhost:8001
# Dashboard: http://localhost:3000
```

### Testing

```bash
# In Docker (recommended)
cd .scripts/docker
./docker-start.sh

# Or locally
./start.py
```

### Production

```bash
# Use Docker
cd .scripts/docker
./deploy-prod.sh
```

---

## 📈 Performance Tips

### Optimize API Performance

- Use async endpoints
- Enable caching
- Monitor resource usage

### Optimize Dashboard

- Enable production build
- Use CDN for static assets
- Enable gzip compression

### Monitor All Services

```bash
# System resource monitor
# Windows: Task Manager
# Linux: top, htop
# macOS: Activity Monitor
```

---

## 📞 For More Help

- **Service Deployment:** `.documentation/03_deployment/DEPLOYMENT_CHECKLIST.md`
- **Docker Option:** `.scripts/docker/README.md`
- **Quick Fixes:** `.documentation/02_quick_start/QUICK_FIX_GUIDE.md`
- **Full Installation:** `.documentation/01_installation/INSTALLATION_GUIDE.md`

---

**Last Updated:** October 25, 2025  
**Status:** ✅ Production Ready
