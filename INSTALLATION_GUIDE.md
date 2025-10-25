# 📦 FACELESS YOUTUBE - INSTALLATION GUIDE

Complete setup instructions for Faceless YouTube on Windows, Linux, and macOS.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start (Recommended)](#quick-start-recommended)
3. [Platform-Specific Installation](#platform-specific-installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Deployment Options](#deployment-options)
8. [Next Steps](#next-steps)

---

## 🖥️ System Requirements

### Minimum Requirements

| Component      | Minimum | Recommended |
| -------------- | ------- | ----------- |
| **RAM**        | 4 GB    | 8 GB        |
| **Disk Space** | 5 GB    | 20 GB       |
| **CPU**        | 2 cores | 4+ cores    |
| **Python**     | 3.9+    | 3.11+       |
| **Node.js**    | 14+     | 18+         |

### Software Requirements

#### For Local Installation:

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend build system
- **Git** - Version control
- **PostgreSQL 14+** - Database (can use Docker)
- **Redis 7+** - Cache (can use Docker)

#### For Docker Installation (Recommended):

- **Docker** - Desktop application (includes Docker Compose)
- **2 GB available memory** for containers

### Internet Requirements

- Initial setup: ~2 GB download (dependencies + Docker images)
- Minimal after setup: ~100 MB (API updates)

---

## ⚡ Quick Start (Recommended)

### Option 1: Docker (Easiest - All Platforms)

**Prerequisites:** Docker Desktop installed and running

```bash
# Windows
setup.bat

# Linux/macOS
bash setup.sh
```

**What happens:**

1. ✅ Checks system requirements
2. ✅ Creates virtual environment (Python)
3. ✅ Installs dependencies
4. ✅ Launches interactive configuration wizard
5. ✅ Generates .env file with your settings

**Then start services:**

```bash
# Windows
docker-start.bat

# Linux/macOS
bash docker-start.sh
```

**Access the application:**

- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Swagger UI:** http://localhost:8000/swagger

### Option 2: Local Installation (Advanced)

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL 14+, Redis 7+

```bash
# Windows
setup.bat

# Linux/macOS
bash setup.sh
```

Follow the wizard prompts, selecting "Local Installation" when asked.

---

## 🔧 Platform-Specific Installation

### Windows Installation

#### Step 1: Prerequisites

Download and install:

1. **Docker Desktop:** https://www.docker.com/products/docker-desktop

   - Or **Python 3.11:** https://www.python.org/downloads/
   - Or **Node.js 18:** https://nodejs.org/

2. **Git (optional):** https://git-scm.com/download/win

#### Step 2: Run Setup

```batch
REM Navigate to project directory
cd C:\path\to\FacelessYouTube

REM Run setup script
setup.bat
```

**What the script does:**

```
┌─ Step 1: System Requirements Check
│  ✓ Verifies Python/Node.js/Docker
│  ✓ Checks available disk space
│
├─ Step 2: Environment Setup
│  ✓ Creates virtual environment
│  ✓ Activates venv
│
├─ Step 3: Dependency Installation
│  ✓ Runs pip install (Python packages)
│  ✓ Runs npm install (Node.js packages)
│
├─ Step 4: Configuration Wizard
│  ✓ Prompts for API keys
│  ✓ Configures database connection
│  ✓ Sets up Redis connection
│  ✓ Generates .env file
│
└─ Step 5: Completion
   ✓ Ready to start application
```

#### Step 3: Start Application

**Using Docker (Recommended):**

```batch
docker-start.bat
```

**Or manually (Local):**

```batch
REM Terminal 1 - Start Backend
venv\Scripts\activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

REM Terminal 2 - Start Frontend
cd dashboard
npm start
```

---

### Linux Installation

#### Step 1: Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip \
    nodejs npm git docker.io docker-compose

# Or use Docker Desktop: https://www.docker.com/products/docker-desktop
```

#### Step 2: Run Setup

```bash
cd /path/to/FacelessYouTube
bash setup.sh
```

**The script will:**

- ✅ Detect your OS and dependencies
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Launch configuration wizard
- ✅ Generate .env file

#### Step 3: Start Application

**Using Docker (Recommended):**

```bash
bash docker-start.sh
```

**Or manually (Local):**

```bash
# Terminal 1 - Start Backend
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Start Frontend
cd dashboard
npm start
```

---

### macOS Installation

#### Step 1: Prerequisites

```bash
# Using Homebrew (https://brew.sh)
brew install python@3.11 node git

# For Docker (recommended):
# Download Docker Desktop: https://www.docker.com/products/docker-desktop
```

#### Step 2: Run Setup

```bash
cd /path/to/FacelessYouTube
bash setup.sh
```

#### Step 3: Start Application

**Using Docker (Recommended):**

```bash
bash docker-start.sh
```

**Or manually (Local):**

```bash
# Terminal 1 - Backend
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd dashboard
npm start
```

---

## ⚙️ Configuration

### Configuration File: .env

After running `setup.bat` or `setup.sh`, a `.env` file is created with:

```env
# API Configuration
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/faceless_youtube
POSTGRES_USER=faceless_user
POSTGRES_PASSWORD=your_secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=faceless_youtube

# API Keys (YouTube, OpenAI, etc.)
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Dashboard Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
```

### Editing Configuration

Edit `.env` file in your text editor:

```bash
# Windows (Notepad)
notepad .env

# Linux/macOS (nano)
nano .env

# Or use your preferred editor (VSCode, Sublime, etc.)
```

### Required API Keys

1. **YouTube API:**

   - Visit: https://console.cloud.google.com
   - Create project → Enable YouTube Data API v3
   - Create credentials (API Key)

2. **OpenAI API:**

   - Visit: https://platform.openai.com/api-keys
   - Create API key
   - Set billing information

3. **ElevenLabs API (Text-to-Speech):**
   - Visit: https://elevenlabs.io
   - Create account → Get API key

---

## ✅ Verification

### Docker Installation

```bash
# Verify all services are running
docker-compose ps

# Expected output:
# NAME                COMMAND             STATUS              PORTS
# faceless-api        "uvicorn src.api..." Up (healthy)        0.0.0.0:8000->8000/tcp
# faceless-dashboard  "npm start"         Up (healthy)        0.0.0.0:3000->3000/tcp
# postgres            "postgres"          Up (healthy)        5432/tcp
# redis               "redis-server"      Up (healthy)        6379/tcp
```

### Local Installation

```bash
# Check Python
python --version
# Expected: Python 3.11.x

# Check Node.js
node --version
# Expected: v18.x.x or higher

# Check virtual environment
where python  # Windows
which python  # Linux/macOS
# Should show path in venv/

# Check dependencies
pip list | grep -E "fastapi|sqlalchemy|uvicorn"
```

### API Health Check

```bash
curl http://localhost:8000/health
# Expected response: {"status": "healthy", "timestamp": "..."}
```

### Dashboard Access

Open browser and navigate to:

```
http://localhost:3000
```

You should see the Faceless YouTube dashboard.

---

## 🐛 Troubleshooting

### Port Already in Use

**Error:** "Port 8000/3000 is already in use"

**Solution:**

```bash
# Windows - Find what's using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port in docker-compose.override.yml
```

```bash
# Linux/macOS - Find process using port
lsof -i :8000
kill -9 <PID>
```

### Docker Services Won't Start

**Error:** "Cannot connect to Docker daemon"

**Solution:**

1. Ensure Docker Desktop is running
2. Restart Docker Desktop
3. Check Docker status: `docker ps`
4. View logs: `docker-compose logs`

### Python Virtual Environment Issues

**Error:** "Cannot find Python interpreter"

**Solution:**

```bash
# Windows - Recreate venv
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3.11 -m venv venv
source venv/bin/activate
```

### Database Connection Failed

**Error:** "Cannot connect to PostgreSQL"

**Solution:**

```bash
# Docker - Check PostgreSQL logs
docker-compose logs postgres

# Local - Check PostgreSQL is running
psql --version
sudo service postgresql status  # Linux

# Verify credentials in .env
cat .env | grep DATABASE_URL
```

### npm Install Fails

**Error:** "npm ERR! code ERESOLVE"

**Solution:**

```bash
# Clear npm cache
npm cache clean --force

# Install with legacy peer deps
npm install --legacy-peer-deps

# Or upgrade Node.js
node --version  # Should be 18+
```

### Setup Script Permission Denied (Linux/macOS)

**Error:** "Permission denied: ./setup.sh"

**Solution:**

```bash
chmod +x setup.sh
bash setup.sh
```

### Dashboard Shows Blank Page

**Error:** Dashboard loads but shows nothing

**Solution:**

```bash
# Check API is running
curl http://localhost:8000/health

# Check browser console for errors (F12)
# Clear browser cache (Ctrl+Shift+Delete)
# Rebuild React app
cd dashboard
npm run build
npm start
```

### Out of Memory Error

**Error:** "Docker container killed due to OOM"

**Solution:**

```bash
# Increase Docker memory limit
# Docker Desktop Settings → Resources → Memory: 8GB+

# Or reduce service memory requirements
# Edit docker-compose.yml:
# services:
#   api:
#     mem_limit: 1g
```

### API Returns 500 Error

**Error:** "Internal Server Error"

**Solution:**

```bash
# Check API logs
docker-compose logs -f api

# Or local logs
tail -f logs/api.log

# Check database connectivity
docker-compose exec postgres psql -U faceless_user -d faceless_youtube

# Verify API key configuration
grep "OPENAI_API_KEY" .env
```

### Changes Not Reflecting (Hot Reload Not Working)

**Error:** "Code changes aren't visible"

**Solution:**

```bash
# Restart services
docker-compose restart api

# Or if running locally
# Exit uvicorn (Ctrl+C)
# Run again: uvicorn src.api.main:app --reload
```

---

## 🐳 Deployment Options

### Option 1: Docker (Recommended - Production-Ready)

**Pros:**

- ✅ Single command deployment
- ✅ Isolated environments
- ✅ Consistent across machines
- ✅ Easy to scale
- ✅ Automatic health checks

**Cons:**

- Requires Docker Desktop
- Slightly higher resource usage

**Start:**

```bash
docker-start.bat  # Windows
bash docker-start.sh  # Linux/macOS
```

### Option 2: Local Installation (Development)

**Pros:**

- ✅ Direct OS integration
- ✅ Faster iteration
- ✅ Easier debugging
- ✅ Lower resource overhead

**Cons:**

- Requires manual service management
- Platform-specific setup
- Dependency conflicts possible

**Start Backend:**

```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
uvicorn src.api.main:app --reload
```

**Start Frontend:**

```bash
cd dashboard
npm start
```

### Option 3: Hybrid (Docker Services + Local API)

**Pros:**

- ✅ Database/Redis in containers
- ✅ Direct API debugging
- ✅ Fast dashboard reload

**Setup:**

```bash
# Start only infrastructure services
docker-compose up postgres redis mongodb -d

# Run API locally
source venv/bin/activate
uvicorn src.api.main:app --reload

# Run dashboard locally
cd dashboard
npm start
```

---

## 🚀 Next Steps

### After Installation

1. **Log In**

   - Navigate to http://localhost:3000
   - Create first user account

2. **Configure API Keys**

   - Go to Settings → API Configuration
   - Enter YouTube, OpenAI, ElevenLabs keys
   - Test connections

3. **Review Security**

   - Change default passwords
   - Set up 2FA if available
   - Review access logs

4. **Run Health Check**

   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/docs  # API documentation
   ```

5. **Set Up Automated Backups**
   ```bash
   # Docker database backup
   docker-compose exec postgres pg_dump -U faceless_user faceless_youtube > backup.sql
   ```

### Monitoring & Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
docker-compose logs -f dashboard

# API logs (local)
tail -f logs/api.log

# Dashboard build
cd dashboard
npm run build  # Production build
```

### Common Commands

```bash
# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# Database backup
docker-compose exec postgres pg_dump -U faceless_user faceless_youtube > backup.sql

# Database restore
docker-compose exec -T postgres psql -U faceless_user faceless_youtube < backup.sql

# Clear volumes (WARNING: Deletes data)
docker-compose down -v
```

---

## 📞 Support

### Getting Help

1. **Check Troubleshooting Section** (above)
2. **Review API Logs:**
   ```bash
   docker-compose logs api
   ```
3. **Check Docker Status:**
   ```bash
   docker ps
   docker-compose ps
   ```
4. **Verify Configuration:**
   ```bash
   cat .env
   ```

### Common Issues & Quick Fixes

| Issue              | Quick Fix                                    |
| ------------------ | -------------------------------------------- |
| Port in use        | `lsof -i :8000` (find) or use different port |
| Docker won't start | Restart Docker Desktop                       |
| API returns 500    | Check logs with `docker-compose logs api`    |
| Dashboard blank    | Clear cache (Ctrl+Shift+Del) & reload        |
| Out of memory      | Increase Docker memory in Settings           |
| .env not found     | Run setup.bat or setup.sh first              |

---

## 📋 Verification Checklist

- [ ] System requirements met (Python 3.11+, Node 18+)
- [ ] .env file created with API keys
- [ ] `docker-compose ps` shows all services running (if using Docker)
- [ ] API responds to `curl http://localhost:8000/health`
- [ ] Dashboard loads at http://localhost:3000
- [ ] API documentation visible at http://localhost:8000/docs
- [ ] Can log in to dashboard
- [ ] Database contains tables (checked via logs or psql)

---

## 🎯 Deployment Flow

```
Installation Started
    ↓
[1] System Check (Python/Node/Docker)
    ↓
[2] Environment Setup (venv creation)
    ↓
[3] Dependencies (pip/npm install)
    ↓
[4] Configuration Wizard (API keys, DB)
    ↓
[5] Start Services (Docker or local)
    ↓
[6] Verify Health (ping API/Dashboard)
    ↓
Installation Complete ✓
```

---

## 📝 Version Information

- **Installation Guide Version:** 1.0
- **Supported Python:** 3.11+
- **Supported Node.js:** 18+
- **Supported Docker:** 20.10+
- **Last Updated:** 2025-01-XX

---

**Ready to get started? Run `setup.bat` (Windows) or `bash setup.sh` (Linux/macOS)!**
