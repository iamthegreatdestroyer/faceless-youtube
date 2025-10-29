# 🚀 Faceless YouTube - Setup Scripts

This directory contains automated setup scripts for the Faceless YouTube Automation Platform.

## Quick Start

### Database Setup (Phase 5 of Installation)

The easiest way to set up PostgreSQL:

```powershell
# PowerShell (Recommended for modern Windows)
..\utilities\setup_database.ps1

# OR Command Prompt (Traditional Windows)
..\utilities\setup_database.bat

# OR Direct Python
.\venv\Scripts\Activate.ps1
python ..\utilities\setup_database.py
```

This script will:

- ✅ Prompt for PostgreSQL credentials (one time only)
- ✅ Create the database and application user
- ✅ Test database connections
- ✅ Update `.env` file with connection string
- ✅ Run all database migrations
- ✅ Report status and next steps

**Time required:** ~30 seconds

## Scripts Directory Structure

```
.scripts/
├── README.md (this file)
├── DATABASE_SETUP_QUICKSTART.md (detailed guide + troubleshooting)
├── utilities/
│   ├── setup_database.py (main Python wizard - interactive)
│   ├── setup_database.ps1 (PowerShell launcher)
│   ├── setup_database.bat (Command Prompt launcher)
│   └── ... (other utilities)
└── ... (other script directories)
```

## After Database Setup

Once the database is configured:

### 1. Start the API Server

```powershell
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Access the Swagger API documentation: http://localhost:8000/docs

### 2. Start the Dashboard

```powershell
cd C:\FacelessYouTube\dashboard
npm run dev
```

Access the dashboard: http://localhost:5173

### 3. (Optional) Start the Background Worker

```powershell
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
celery -A src.services.background_jobs.celery_app worker -l info
```

## Common Issues

### PostgreSQL Not Running

```powershell
# Start PostgreSQL service
net start postgresql-x64-14
```

### Virtual Environment Not Found

```powershell
# Create it
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Database Already Exists

Update `.env` with existing credentials, or drop and recreate:

```powershell
psql -U postgres -c "DROP DATABASE faceless_youtube;"
# Then run setup script again
```

## More Information

📖 **Full Installation Guide:** `.documentation/01_installation/INSTALLATION_IN_PROGRESS.md`  
🔍 **Database Setup Details:** `.scripts/DATABASE_SETUP_QUICKSTART.md`  
📋 **Project Instructions:** `Project-Instructions.md`  
🐍 **Python Scripts:** `utilities/` directory

## Support

If you encounter issues:

1. Check `.scripts/DATABASE_SETUP_QUICKSTART.md` for troubleshooting
2. Review `.documentation/01_installation/INSTALLATION_IN_PROGRESS.md`
3. Check PostgreSQL service is running: `net start postgresql-x64-14`
4. Verify Python virtual environment is activated: `(venv) PS C:\FacelessYouTube>`

---

**Status:** Production Ready ✅  
**Last Updated:** January 10, 2025  
**Tested On:** Windows 10/11 + PostgreSQL 14.17
