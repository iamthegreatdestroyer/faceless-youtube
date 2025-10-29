# Database Setup Quick Start Guide

## Overview

This guide explains how to set up PostgreSQL for the Faceless YouTube Automation Platform using the automated setup wizard.

## Prerequisites

✅ Python 3.13.7 installed  
✅ PostgreSQL 14.17+ installed and running  
✅ Python virtual environment created (`venv/` folder exists)  
✅ All Python dependencies installed

## Quick Start (Choose One Method)

### Option 1: PowerShell (Recommended for Modern Windows)

```powershell
# Open PowerShell as Administrator
# Navigate to project root
cd C:\FacelessYouTube

# Run the setup script
.\.scripts\utilities\setup_database.ps1
```

**Benefits:**

- Modern Windows shell
- Better error handling
- Colorized output
- Professional formatting

### Option 2: Command Prompt (Traditional Windows)

```cmd
# Open Command Prompt
# Navigate to project root
cd C:\FacelessYouTube

# Run the batch script
.scripts\utilities\setup_database.bat
```

**Benefits:**

- Works on all Windows systems
- Traditional command prompt interface
- Simpler syntax

### Option 3: Direct Python (Manual Control)

```powershell
# In PowerShell or Command Prompt
cd C:\FacelessYouTube

# Activate venv
.\venv\Scripts\Activate.ps1

# Run Python script directly
python .\.scripts\utilities\setup_database.py
```

**Benefits:**

- Direct control
- Easiest to debug
- Supports custom parameters

## What the Setup Wizard Does

The `setup_database.py` script will:

1. **Prompt for PostgreSQL Credentials**

   ```
   PostgreSQL Admin Username [postgres]: ___
   PostgreSQL Admin Password: ___
   ```

2. **Create Database**

   - Creates `faceless_youtube` database
   - Sets appropriate permissions

3. **Create Application User**

   - Creates `faceless_youtube` user
   - Generates secure password (or use custom)
   - Grants appropriate permissions

4. **Test Connections**

   - Verifies admin connection works
   - Verifies application user connection works
   - Reports results

5. **Update .env File**

   - Saves connection string to `DATABASE_URL`
   - Format: `postgresql://username:password@localhost:5432/database_name`
   - Password is URL-encoded for security

6. **Run Database Migrations**

   - Executes Alembic migrations
   - Creates all tables and relationships
   - Initializes database schema

7. **Cleanup**
   - Closes all connections
   - Removes temporary files
   - Displays completion status

## Expected Output

```
================================================================================

  || FACELESS YOUTUBE - DATABASE SETUP WIZARD ||

  This will guide you through setting up PostgreSQL for local development

================================================================================

ℹ Project root: C:\FacelessYouTube
✓ Virtual environment found
ℹ Activating virtual environment...
✓ Virtual environment activated

ℹ Running database setup wizard...

═══════════════════════════════════════════════════════════════════════════════
DATABASE SETUP WIZARD
═══════════════════════════════════════════════════════════════════════════════

PostgreSQL Admin Credentials
─────────────────────────────
Username [postgres]: postgres
Password: ___

Database Configuration
─────────────────────────────
Connection successful! ✓

Creating database and user...
✓ Database created: faceless_youtube
✓ User created: faceless_youtube

Connection Test
─────────────────────────────
Admin connection: SUCCESS ✓
App connection: SUCCESS ✓

Running Migrations
─────────────────────────────
✓ Migrations completed successfully

Environment File Update
─────────────────────────────
✓ Updated .env file

═══════════════════════════════════════════════════════════════════════════════
✓ DATABASE SETUP COMPLETE!
═══════════════════════════════════════════════════════════════════════════════
```

## Troubleshooting

### PostgreSQL Not Running

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**

```powershell
# Start PostgreSQL service
# Windows Services:
#   1. Open Services (services.msc)
#   2. Find "postgresql-x64-14"
#   3. Right-click → Start

# Or from command line:
net start postgresql-x64-14
```

### Wrong Password

**Error:** `authentication failed for user "postgres"`

**Solution:**

```powershell
# Reset PostgreSQL password (Windows):
# 1. Open Command Prompt as Administrator
# 2. Stop PostgreSQL: net stop postgresql-x64-14
# 3. Find pg_hba.conf (usually C:\Program Files\PostgreSQL\14\data\pg_hba.conf)
# 4. Change line: "md5" → "trust"
# 5. Start PostgreSQL: net start postgresql-x64-14
# 6. Connect and set password:
#    psql -U postgres
#    ALTER USER postgres WITH PASSWORD 'new_password';
```

### Virtual Environment Not Found

**Error:** `Python virtual environment not found`

**Solution:**

```powershell
# Create virtual environment
cd C:\FacelessYouTube
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Database Already Exists

**Error:** `database "faceless_youtube" already exists`

**Solution:**

```powershell
# If you want to use existing database, just update .env file:
# DATABASE_URL=postgresql://faceless_youtube:password@localhost:5432/faceless_youtube

# If you want to reset, drop it first:
psql -U postgres -c "DROP DATABASE faceless_youtube;"
# Then run setup wizard again
```

### Migration Errors

**Error:** `Alembic migration failed`

**Solution:**

```powershell
# Manually run migrations after setup:
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
alembic upgrade head

# Check migration status:
alembic current
```

## Verification

After setup completes, verify everything works:

```powershell
# Activate venv
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1

# Test database connection
psql -U faceless_youtube -d faceless_youtube -c "SELECT 1;"

# Should output:
# ?column?
# ----------
#         1

# Test Python connection
python -c "from src.database import get_db; print('✓ Database import successful')"
```

## Next Steps

Once database setup is complete:

### 1. Start the API Server

```powershell
# In terminal 1
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Access: http://localhost:8000/docs (Swagger UI)
```

### 2. Start the Dashboard

```powershell
# In terminal 2
cd C:\FacelessYouTube\dashboard
npm run dev

# Access: http://localhost:5173
```

### 3. (Optional) Start the Worker

```powershell
# In terminal 3
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
celery -A src.services.background_jobs.celery_app worker -l info
```

## Environment File

After setup, your `.env` file will contain:

```env
# Database Configuration (AUTO-GENERATED BY SETUP WIZARD)
DATABASE_URL=postgresql://faceless_youtube:PASSWORD@localhost:5432/faceless_youtube

# Other configurations...
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/faceless_youtube
```

⚠️ **Important:** The `.env` file contains sensitive credentials. Never commit it to git.

## Reverting Setup

If you want to start fresh:

```powershell
# 1. Drop the database (requires admin password)
psql -U postgres -c "DROP DATABASE faceless_youtube;"

# 2. Drop the user
psql -U postgres -c "DROP USER faceless_youtube;"

# 3. Remove .env file
Remove-Item .env

# 4. Create fresh .env from template
Copy-Item .env.example .env

# 5. Run setup wizard again
.\.scripts\utilities\setup_database.ps1
```

## Advanced Usage

### Custom Database Name

If you want to use a different database name, edit `.scripts/utilities/setup_database.py`:

```python
# Line ~20, change:
database_name = "faceless_youtube"  # ← Change this

# To:
database_name = "my_custom_db_name"  # ← New name
```

### Custom Connection Parameters

If your PostgreSQL is on a different host/port:

```python
# In setup_database.py, around line ~50:
POSTGRES_HOST = "localhost"      # ← Change if different
POSTGRES_PORT = 5432            # ← Change if different
```

### Environment Variables

You can pre-set credentials via environment variables:

```powershell
$env:POSTGRES_ADMIN_USER = "postgres"
$env:POSTGRES_ADMIN_PASSWORD = "your_password"
python .\.scripts\utilities\setup_database.py
```

## Support

For issues with:

- **PostgreSQL installation:** See `.documentation/INSTALLATION_IN_PROGRESS.md`
- **Python environment:** See `.documentation/INSTALLATION_IN_PROGRESS.md`
- **Database schema:** See `alembic/` folder and `alembic/env.py`
- **API errors:** Check `src/database/` for connection logic

## Files Involved

- `.scripts/utilities/setup_database.py` - Main setup wizard (interactive)
- `.scripts/utilities/setup_database.ps1` - PowerShell launcher
- `.scripts/utilities/setup_database.bat` - Batch file launcher
- `.env` - Configuration file (created/updated by wizard)
- `alembic/` - Database migration files
- `alembic.ini` - Alembic configuration

---

**Last Updated:** 2025-01-10  
**Status:** Production-Ready  
**Tested On:** Windows 10/11 + PostgreSQL 14.17
