# 🚀 LOCAL INSTALLATION GUIDE - FACELESS YOUTUBE AUTOMATION PLATFORM

**Date:** October 27, 2025  
**Project:** Faceless YouTube Automation Platform v1.0.0  
**Status:** Installation In Progress ✅

---

## ⚡ QUICK START - Phase 5: Database Setup

> **🎯 YOU ARE HERE:** Automated database setup now available!

The PostgreSQL password handling issue is now **SOLVED** with automated setup scripts.

### Choose Your Setup Method:

**Option 1: PowerShell (Recommended)**

```powershell
cd C:\FacelessYouTube
.\.scripts\utilities\setup_database.ps1
```

**Option 2: Command Prompt**

```cmd
cd C:\FacelessYouTube
.scripts\utilities\setup_database.bat
```

**Option 3: Direct Python**

```powershell
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
python .\.scripts\utilities\setup_database.py
```

### What This Does:

✅ Prompts for PostgreSQL credentials (one-time)  
✅ Creates `faceless_youtube` database  
✅ Creates `faceless_youtube` user  
✅ Tests both admin and app connections  
✅ Updates `.env` with connection string  
✅ Runs database migrations automatically  
✅ **No more manual password prompts!**

### Expected Time: ~30 seconds

👉 **Run this now, then continue reading below for Phase 6-8 steps**

**For detailed troubleshooting:** See `.scripts/DATABASE_SETUP_QUICKSTART.md`

---

## ✅ COMPLETED STEPS

### 1. System Requirements Verification ✅

All prerequisites are installed and verified:

| Component      | Version  | Status       |
| -------------- | -------- | ------------ |
| **Python**     | 3.13.7   | ✅ Installed |
| **Node.js**    | v22.20.0 | ✅ Installed |
| **npm**        | 11.6.2   | ✅ Installed |
| **PostgreSQL** | 14.17    | ✅ Installed |

**Location:** `C:\FacelessYouTube`

---

### 2. Python Virtual Environment ✅

**Status:** Created and activated  
**Location:** `C:\FacelessYouTube\venv`

**Activation Command:**

```powershell
& C:\FacelessYouTube\venv\Scripts\Activate.ps1
```

---

### 3. Python Dependencies Installed ✅

**Core Packages Installed:**

- ✅ FastAPI >= 0.104.1 (REST API Framework)
- ✅ SQLAlchemy >= 2.0.23 (ORM)
- ✅ PostgreSQL & AsyncPG (Database)
- ✅ MongoDB & Motor (Document DB)
- ✅ Redis (Caching)
- ✅ Anthropic Claude API
- ✅ Google Generative AI
- ✅ OpenAI API
- ✅ Torch >= 2.6.0 (ML Framework)
- ✅ PyQt6 (Desktop UI)
- ✅ MoviePy (Video Processing)
- ✅ FFmpeg Integration
- ✅ Celery (Task Queue)
- ✅ APScheduler (Job Scheduling)

**Development Packages Installed:**

- ✅ Pytest (Testing)
- ✅ Pytest-asyncio (Async Testing)
- ✅ Pytest-cov (Coverage)
- ✅ Questionary (Interactive CLI)

**Command Used:**

```powershell
C:\FacelessYouTube\venv\Scripts\python.exe -m pip install -r requirements.txt
C:\FacelessYouTube\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

---

### 4. Node.js/Dashboard Dependencies ✅

**Status:** Installed  
**Location:** `C:\FacelessYouTube\dashboard`  
**Packages:** 420 audited

**Key Dependencies:**

- ✅ React 18.2.0
- ✅ React Router
- ✅ Vite (Build tool)
- ✅ Tailwind CSS
- ✅ Recharts (Data visualization)
- ✅ Zustand (State management)
- ✅ React Query (@tanstack/react-query)

**Command Used:**

```powershell
cd C:\FacelessYouTube\dashboard
npm install
```

---

## 🔄 NEXT STEPS

### Step 5: Database Configuration

#### Option A: Manual PostgreSQL Setup

**5.1 Open PostgreSQL psql terminal:**

```powershell
psql -U postgres -h localhost
```

**5.2 Create the database:**

```sql
CREATE DATABASE faceless_youtube
  OWNER postgres
  ENCODING 'UTF8'
  LC_COLLATE 'en_US.UTF-8'
  LC_CTYPE 'en_US.UTF-8';
```

**5.3 Create the application user:**

```sql
CREATE USER faceless_youtube WITH PASSWORD 'secure_password_here';

-- Grant privileges
ALTER ROLE faceless_youtube SET client_encoding TO 'utf8';
ALTER ROLE faceless_youtube SET default_transaction_isolation TO 'read committed';
ALTER ROLE faceless_youtube SET default_transaction_deferrable TO on;
ALTER ROLE faceless_youtube SET default_time_zone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE faceless_youtube TO faceless_youtube;
```

**5.4 Update `.env` file:**

```properties
# OLD:
DATABASE_URL=postgresql://user:password@localhost:5432/faceless_youtube

# NEW (use your actual password):
DATABASE_URL=postgresql://faceless_youtube:secure_password_here@localhost:5432/faceless_youtube
```

#### Option B: Using Setup Script

From PowerShell (in project root):

```powershell
C:\FacelessYouTube\venv\Scripts\python.exe .\.scripts\utilities\setup_database.py
```

---

### Step 6: Run Database Migrations

**6.1 Activate virtual environment:**

```powershell
& C:\FacelessYouTube\venv\Scripts\Activate.ps1
```

**6.2 Run Alembic migrations:**

```powershell
cd C:\FacelessYouTube
alembic upgrade head
```

**What this does:**

- Creates all database tables
- Sets up relationships and constraints
- Initializes application schema

---

### Step 7: Verify Installation

**7.1 Run health checks:**

```powershell
# Test Python environment
python -c "import fastapi, sqlalchemy, torch; print('All core packages OK')"

# Test database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://...'); print(engine.execute('SELECT 1'))"

# Test Node.js/npm
npm --version
```

**7.2 Run pytest:**

```powershell
pytest tests/ -v --tb=short
```

---

### Step 8: Start Services

#### 8.1 Start the Backend API

**Terminal 1 - API Server:**

```powershell
& C:\FacelessYouTube\venv\Scripts\Activate.ps1
cd C:\FacelessYouTube
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Access at: http://localhost:8000/docs (Swagger UI)

#### 8.2 Start the Dashboard

**Terminal 2 - Dashboard Dev Server:**

```powershell
cd C:\FacelessYouTube\dashboard
npm run dev
```

Expected output:

```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

Access at: http://localhost:5173

#### 8.3 Start Background Worker (Optional)

**Terminal 3 - Celery Worker:**

```powershell
& C:\FacelessYouTube\venv\Scripts\Activate.ps1
cd C:\FacelessYouTube
celery -A src.services.background_jobs.celery_app worker -l info
```

---

## 📋 INSTALLATION CHECKLIST

Print this and check off as you complete each step:

```
SYSTEM SETUP
☐ Python 3.13+ installed
☐ Node.js v18+ installed
☐ PostgreSQL 14+ installed
☐ Project cloned to C:\FacelessYouTube

PYTHON ENVIRONMENT
☐ Virtual environment created (venv/)
☐ Virtual environment activated
☐ Requirements.txt installed
☐ Requirements-dev.txt installed

NODEJS/FRONTEND
☐ npm install completed in dashboard/
☐ No critical vulnerabilities

DATABASE
☐ PostgreSQL service running
☐ faceless_youtube database created
☐ faceless_youtube user created
☐ Permissions granted
☐ .env file updated with correct credentials
☐ Alembic migrations run (alembic upgrade head)

SERVICES
☐ Backend API starts (port 8000)
☐ Dashboard loads (port 5173)
☐ Health checks pass
☐ Tests run successfully

READY FOR USE
☐ All services running
☐ Swagger UI accessible at http://localhost:8000/docs
☐ Dashboard accessible at http://localhost:5173
☐ Application ready for development/testing
```

---

## 🆘 TROUBLESHOOTING

### Issue: PostgreSQL password authentication failed

**Solution:**

1. Reset PostgreSQL password (Windows):

   ```powershell
   # Run as Administrator
   psql -U postgres -h localhost -d postgres
   ALTER USER postgres WITH PASSWORD 'new_password';
   \q
   ```

2. Update `.env`:
   ```properties
   DATABASE_URL=postgresql://postgres:new_password@localhost:5432/faceless_youtube
   ```

### Issue: Python venv fails to activate

**Solution:**

```powershell
# Check if venv exists
Test-Path C:\FacelessYouTube\venv

# If not, create it (may need admin):
python -m venv C:\FacelessYouTube\venv

# Activate with explicit path
& C:\FacelessYouTube\venv\Scripts\Activate.ps1
```

### Issue: npm install shows vulnerabilities

**Solution:**

```powershell
cd C:\FacelessYouTube\dashboard
npm audit fix --force
npm install
```

### Issue: Port 8000 or 5173 already in use

**Solution:**

```powershell
# Find process using port
netstat -ano | Select-String ":8000"
netstat -ano | Select-String ":5173"

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or use different ports:
# Backend: uvicorn src.api.main:app --port 8001
# Dashboard: npm run dev -- --port 5174
```

### Issue: Database migration fails

**Solution:**

```powershell
# Check Alembic status
alembic current

# Show migration history
alembic history

# Downgrade and upgrade
alembic downgrade base
alembic upgrade head

# Check database directly
psql -U faceless_youtube -d faceless_youtube -c "\dt"
```

---

## 📞 SUPPORT

**Quick Reference:**

- **Project Root:** `C:\FacelessYouTube`
- **Python:** `C:\FacelessYouTube\venv\Scripts\python.exe`
- **Dashboard:** `C:\FacelessYouTube\dashboard`
- **API Docs:** http://localhost:8000/docs
- **Dashboard UI:** http://localhost:5173

**Documentation:**

- `.documentation/01_installation/` - Setup guides
- `.documentation/02_quick_start/` - Getting started
- `.scripts/installation/README.md` - Installation scripts
- `.scripts/services/README.md` - Service management

**Common Commands:**

```powershell
# Activate environment
& C:\FacelessYouTube\venv\Scripts\Activate.ps1

# Run API tests
pytest tests/unit/test_api.py -v

# Run all tests
pytest tests/ -v --cov=src

# Format code
black src/ tests/

# Type check
mypy src/

# Run database migrations
alembic upgrade head

# Start API server
uvicorn src.api.main:app --reload

# Start dashboard
npm run dev
```

---

## ✨ WHAT'S NEXT

Once installation is complete:

1. **Configure OAuth** - Add YouTube API credentials
2. **Setup AI Models** - Configure Claude/GPT-4 API keys
3. **Create First Video** - Use dashboard to create video
4. **Deploy** - Use Docker/Kubernetes for production

---

**Status:** Installation proceeding step-by-step  
**Last Updated:** October 27, 2025  
**Version:** 1.0.0
