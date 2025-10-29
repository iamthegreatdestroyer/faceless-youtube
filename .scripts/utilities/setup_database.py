#!/usr/bin/env python3
"""
Database Setup Wizard for Faceless YouTube Automation Platform

This script:
1. Prompts for PostgreSQL credentials
2. Creates the database and user if they don't exist
3. Updates the .env file with the correct connection string
4. Tests the connection
5. Runs database migrations
"""

import os
import sys
import subprocess
from pathlib import Path
from urllib.parse import quote_plus
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv, set_key

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def get_postgres_credentials():
    """Get PostgreSQL admin credentials from user"""
    print_info("PostgreSQL Admin Credentials (for setup)")
    print_info("Default user is usually 'postgres'")
    
    admin_user = input(f"{BLUE}PostgreSQL admin username [{GREEN}postgres{BLUE}]:{RESET} ").strip() or "postgres"
    admin_password = input(f"{BLUE}PostgreSQL admin password: {RESET}").strip()
    postgres_host = input(f"{BLUE}PostgreSQL host [{GREEN}localhost{BLUE}]:{RESET} ").strip() or "localhost"
    postgres_port = input(f"{BLUE}PostgreSQL port [{GREEN}5432{BLUE}]:{RESET} ").strip() or "5432"
    
    return admin_user, admin_password, postgres_host, postgres_port

def get_app_credentials():
    """Get application database credentials"""
    print_info("\nApplication Database Credentials")
    print_info("These will be stored in .env file")
    
    db_name = input(f"{BLUE}Database name [{GREEN}faceless_youtube{BLUE}]:{RESET} ").strip() or "faceless_youtube"
    db_user = input(f"{BLUE}Database user [{GREEN}faceless_youtube{BLUE}]:{RESET} ").strip() or "faceless_youtube"
    
    # Generate a secure password if not provided
    import secrets
    suggested_pass = secrets.token_urlsafe(16)
    db_password = input(f"{BLUE}Database password [{GREEN}{suggested_pass}{BLUE}]:{RESET} ").strip() or suggested_pass
    
    return db_name, db_user, db_password

def test_postgres_connection(admin_user, admin_password, host, port):
    """Test connection to PostgreSQL"""
    try:
        print_info(f"Testing connection to PostgreSQL as {admin_user}...")
        conn = psycopg2.connect(
            user=admin_user,
            password=admin_password,
            host=host,
            port=port,
            database="postgres"
        )
        conn.close()
        print_success(f"Connected to PostgreSQL on {host}:{port}")
        return True
    except psycopg2.OperationalError as e:
        print_error(f"Failed to connect to PostgreSQL: {e}")
        return False

def create_database_and_user(admin_user, admin_password, host, port, db_name, db_user, db_password):
    """Create database and user"""
    try:
        conn = psycopg2.connect(
            user=admin_user,
            password=admin_password,
            host=host,
            port=port,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print_info(f"Creating database '{db_name}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(
                sql.Identifier(db_name)
            ))
            print_success(f"Database '{db_name}' created")
        else:
            print_warning(f"Database '{db_name}' already exists")
        
        # Check if user exists
        cursor.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_user}'")
        user_exists = cursor.fetchone()
        
        if not user_exists:
            print_info(f"Creating user '{db_user}'...")
            cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                sql.Identifier(db_user)
            ), (db_password,))
            print_success(f"User '{db_user}' created")
        else:
            print_warning(f"User '{db_user}' already exists, updating password...")
            cursor.execute(sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                sql.Identifier(db_user)
            ), (db_password,))
            print_success(f"Password updated for '{db_user}'")
        
        # Grant privileges
        print_info(f"Granting privileges on '{db_name}' to '{db_user}'...")
        cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(db_name),
            sql.Identifier(db_user)
        ))
        
        cursor.close()
        conn.close()
        print_success("Privileges granted")
        return True
        
    except Exception as e:
        print_error(f"Failed to create database/user: {e}")
        return False

def test_app_connection(db_user, db_password, host, port, db_name):
    """Test connection with app credentials"""
    try:
        print_info(f"Testing connection as application user '{db_user}'...")
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=host,
            port=port,
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print_success(f"Application connection successful! PostgreSQL: {version[0].split(',')[0]}")
        return True
    except Exception as e:
        print_error(f"Application connection failed: {e}")
        return False

def update_env_file(db_user, db_password, host, port, db_name):
    """Update .env file with database connection string"""
    try:
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        
        # Escape password for URL
        escaped_password = quote_plus(db_password)
        
        database_url = f"postgresql://{db_user}:{escaped_password}@{host}:{port}/{db_name}"
        
        print_info(f"Updating {env_file}...")
        set_key(str(env_file), "DATABASE_URL", database_url)
        print_success(f"Updated DATABASE_URL in .env")
        
        # Show the connection string (without showing full password)
        masked_url = f"postgresql://{db_user}:{'*' * len(db_password)}@{host}:{port}/{db_name}"
        print_info(f"Connection string: {masked_url}")
        
        return True
    except Exception as e:
        print_error(f"Failed to update .env file: {e}")
        return False

def run_migrations():
    """Run Alembic database migrations"""
    try:
        print_info("Running database migrations with Alembic...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Database migrations completed successfully")
            return True
        else:
            print_warning("Alembic output:")
            print(result.stdout)
            if result.stderr:
                print_error(f"Alembic errors:\n{result.stderr}")
            return False
            
    except FileNotFoundError:
        print_warning("Alembic not found, skipping migrations")
        print_info("You can run migrations manually with: alembic upgrade head")
        return True
    except Exception as e:
        print_error(f"Failed to run migrations: {e}")
        return False

def main():
    """Main setup flow"""
    print_header("FACELESS YOUTUBE - DATABASE SETUP WIZARD")
    
    # Step 1: Get credentials
    print_info("Step 1: PostgreSQL Administrator Credentials")
    print_warning("You need PostgreSQL admin credentials to create the database and user")
    admin_user, admin_password, host, port = get_postgres_credentials()
    
    # Step 2: Test admin connection
    print_info("\nStep 2: Testing PostgreSQL Connection")
    if not test_postgres_connection(admin_user, admin_password, host, port):
        print_error("Cannot proceed without PostgreSQL connection")
        sys.exit(1)
    
    # Step 3: Get app credentials
    print_info("\nStep 3: Application Database Credentials")
    db_name, db_user, db_password = get_app_credentials()
    
    # Step 4: Create database and user
    print_info("\nStep 4: Creating Database and User")
    if not create_database_and_user(admin_user, admin_password, host, port, db_name, db_user, db_password):
        print_error("Failed to create database/user")
        sys.exit(1)
    
    # Step 5: Test app connection
    print_info("\nStep 5: Testing Application Connection")
    if not test_app_connection(db_user, db_password, host, port, db_name):
        print_error("Failed to test application connection")
        sys.exit(1)
    
    # Step 6: Update .env file
    print_info("\nStep 6: Updating Configuration")
    if not update_env_file(db_user, db_password, host, port, db_name):
        print_error("Failed to update .env file")
        sys.exit(1)
    
    # Step 7: Run migrations
    print_info("\nStep 7: Running Database Migrations")
    run_migrations()
    
    # Success!
    print_header("DATABASE SETUP COMPLETE! ✓")
    print_success("Your database is ready to use!")
    print_info("Connection details have been saved to .env")
    print_info("\nNext steps:")
    print_info("1. Start the API server: uvicorn src.api.main:app --reload")
    print_info("2. In another terminal, start the dashboard: npm run dev (in dashboard folder)")
    print_info("3. Visit http://localhost:8000/docs for API documentation")
    print_info("4. Visit http://localhost:5173 for the dashboard")

if __name__ == "__main__":
    main()
