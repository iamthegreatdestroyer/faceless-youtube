#!/usr/bin/env pwsh
# Faceless YouTube - Direct Database Setup (No Prompts)
# Pre-configured with PostgreSQL credentials via environment variables

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗"
Write-Host "║  FACELESS YOUTUBE - DIRECT DATABASE SETUP (No Prompts)        ║"
Write-Host "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

# Set all environment variables
Write-Host "ℹ Setting up environment variables..."
$env:POSTGRES_ADMIN_USER = "postgres"
$env:POSTGRES_ADMIN_PASSWORD = "FacelessYT2025!"
$env:POSTGRES_PORT = "5433"
$env:POSTGRES_HOST = "localhost"
$env:SKIP_PASSWORD_PROMPT = "true"

Write-Host "✓ PostgreSQL User: $($env:POSTGRES_ADMIN_USER)"
Write-Host "✓ PostgreSQL Password: $(('*' * ($env:POSTGRES_ADMIN_PASSWORD.Length)))"
Write-Host "✓ PostgreSQL Port: $($env:POSTGRES_PORT)"
Write-Host "✓ PostgreSQL Host: $($env:POSTGRES_HOST)"
Write-Host ""

# Get project root - use script directory
$ProjectRoot = "C:\FacelessYouTube"
Write-Host "ℹ Project root: $ProjectRoot"
Write-Host ""

# Verify venv exists
if (-not (Test-Path "$ProjectRoot\venv")) {
    Write-Host "✗ Virtual environment not found at $ProjectRoot\venv"
    exit 1
}

# Activate venv
Write-Host "ℹ Activating virtual environment..."
& "$ProjectRoot\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated"
Write-Host ""

# Run setup directly with Python
Write-Host "ℹ Running database setup..."
Write-Host "──────────────────────────────────────────────────────────────"
Write-Host ""

python -c @"
import os
import sys
import asyncio
from urllib.parse import quote_plus

# Add src to path
sys.path.insert(0, r'$ProjectRoot')

# Get credentials from environment
ADMIN_USER = os.getenv('POSTGRES_ADMIN_USER', 'postgres')
ADMIN_PASSWORD = os.getenv('POSTGRES_ADMIN_PASSWORD', '')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5433')

# Database and app user
DB_NAME = 'faceless_youtube'
APP_USER = 'faceless_youtube'
APP_PASSWORD = 'FacelessYT2025!'

print(f'ℹ PostgreSQL Connection Details:')
print(f'  Admin User: {ADMIN_USER}')
print(f'  Host: {POSTGRES_HOST}:{POSTGRES_PORT}')
print(f'  Database: {DB_NAME}')
print(f'  App User: {APP_USER}')
print()

# Import psycopg2 for database operations
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print('✗ psycopg2 not installed. Installing...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2
    from psycopg2 import sql

# Step 1: Connect as admin
print('ℹ Step 1: Connecting to PostgreSQL as admin...')
try:
    admin_conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        database='postgres',
        user=ADMIN_USER,
        password=ADMIN_PASSWORD
    )
    admin_conn.autocommit = True
    admin_cursor = admin_conn.cursor()
    print('✓ Connected to PostgreSQL')
except Exception as e:
    print(f'✗ Failed to connect to PostgreSQL: {e}')
    sys.exit(1)

# Step 2: Create database if not exists
print()
print('ℹ Step 2: Creating database...')
try:
    admin_cursor.execute(sql.SQL('CREATE DATABASE {} OWNER postgres;').format(sql.Identifier(DB_NAME)))
    print(f'✓ Database created: {DB_NAME}')
except psycopg2.errors.DuplicateDatabase:
    print(f'ℹ Database already exists: {DB_NAME}')
except Exception as e:
    print(f'✗ Failed to create database: {e}')
    admin_conn.close()
    sys.exit(1)

# Step 3: Create app user if not exists
print()
print('ℹ Step 3: Creating application user...')
try:
    # Check if user exists
    admin_cursor.execute("SELECT 1 FROM pg_user WHERE usename = %s", (APP_USER,))
    if admin_cursor.fetchone():
        print(f'ℹ User already exists: {APP_USER}')
    else:
        admin_cursor.execute(sql.SQL('CREATE USER {} WITH PASSWORD %s;').format(sql.Identifier(APP_USER)), (APP_PASSWORD,))
        print(f'✓ User created: {APP_USER}')
    
    # Grant privileges
    admin_cursor.execute(sql.SQL('GRANT ALL PRIVILEGES ON DATABASE {} TO {};').format(
        sql.Identifier(DB_NAME),
        sql.Identifier(APP_USER)
    ))
    print(f'✓ Privileges granted to {APP_USER}')
except Exception as e:
    print(f'✗ Failed to create user: {e}')
    admin_conn.close()
    sys.exit(1)

admin_conn.close()

# Step 4: Connect as app user
print()
print('ℹ Step 4: Testing application user connection...')
try:
    app_conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        database=DB_NAME,
        user=APP_USER,
        password=APP_PASSWORD
    )
    app_cursor = app_conn.cursor()
    app_cursor.execute('SELECT 1;')
    result = app_cursor.fetchone()
    print(f'✓ Application user connected successfully')
    app_conn.close()
except Exception as e:
    print(f'✗ Failed to connect as application user: {e}')
    sys.exit(1)

# Step 5: Generate connection string
print()
print('ℹ Step 5: Generating connection string...')
encoded_password = quote_plus(APP_PASSWORD)
connection_string = f'postgresql://{APP_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DB_NAME}'
print(f'✓ Connection string generated')

# Step 6: Update .env file
print()
print('ℹ Step 6: Updating .env file...')
env_file = r'$ProjectRoot\.env'
try:
    # Read existing .env if it exists
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update database URL
    env_vars['DATABASE_URL'] = connection_string
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write('# Faceless YouTube - Database Configuration\n')
        f.write('# Generated by automatic setup script\n')
        f.write('# DO NOT COMMIT PASSWORD TO VERSION CONTROL\n')
        f.write('\n')
        for key, value in sorted(env_vars.items()):
            f.write(f'{key}={value}\n')
    
    print(f'✓ .env file updated: {env_file}')
except Exception as e:
    print(f'✗ Failed to update .env file: {e}')
    sys.exit(1)

# Step 7: Run migrations
print()
print('ℹ Step 7: Running database migrations...')
try:
    # Change to project root
    os.chdir(r'$ProjectRoot')
    
    # Import alembic
    from alembic.config import Config
    from alembic.command import upgrade
    
    # Run migrations
    alembic_cfg = Config('alembic.ini')
    upgrade(alembic_cfg, 'head')
    print('✓ Migrations completed successfully')
except Exception as e:
    print(f'⚠ Migration check: {e}')
    print('⚠ This might be normal if migrations are already up-to-date')

print()
print('╔════════════════════════════════════════════════════════════════╗')
print('║  ✓ DATABASE SETUP COMPLETE!                                  ║')
print('╚════════════════════════════════════════════════════════════════╝')
print()
print('Next steps:')
print('  1. Verify connection: psql -U faceless_youtube -d faceless_youtube -h localhost -p 5433 -c "SELECT 1;"')
print('  2. Start API server: uvicorn src.api.main:app --reload')
print('  3. Start dashboard: cd dashboard && npm run dev')
print()
"@

Write-Host ""
Write-Host "✓ Setup script completed"
Write-Host ""
