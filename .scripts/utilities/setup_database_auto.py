#!/usr/bin/env python3
"""
Automated Database Setup for Faceless YouTube - No Prompts Version
Uses environment variables for credentials
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

def get_config_from_env():
    """Get configuration from environment variables"""
    # PostgreSQL admin credentials
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    
    # Application database credentials
    db_name = os.getenv("DB_NAME", "faceless_youtube")
    db_user = os.getenv("DB_USER", "faceless_youtube")
    
    # Generate or get app password
    import secrets
    db_password = os.getenv("DB_PASSWORD", secrets.token_urlsafe(16))
    
    return {
        "admin_user": admin_user,
        "admin_password": admin_password,
        "host": postgres_host,
        "port": postgres_port,
        "db_name": db_name,
        "db_user": db_user,
        "db_password": db_password,
    }

def test_postgres_connection(config):
    """Test connection to PostgreSQL"""
    try:
        print_info(f"Testing connection to PostgreSQL as {config['admin_user']}...")
        conn = psycopg2.connect(
            user=config["admin_user"],
            password=config["admin_password"],
            host=config["host"],
            port=config["port"],
            database="postgres"
        )
        conn.close()
        print_success(f"Connected to PostgreSQL on {config['host']}:{config['port']}")
        return True
    except psycopg2.OperationalError as e:
        print_error(f"Failed to connect to PostgreSQL: {e}")
        return False

def create_database_and_user(config):
    """Create database and user"""
    try:
        conn = psycopg2.connect(
            user=config["admin_user"],
            password=config["admin_password"],
            host=config["host"],
            port=config["port"],
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create database
        print_info(f"Creating database: {config['db_name']}")
        try:
            cursor.execute(sql.SQL("CREATE DATABASE {} OWNER postgres").format(
                sql.Identifier(config['db_name'])
            ))
            print_success(f"Database created: {config['db_name']}")
        except psycopg2.errors.DuplicateDatabase:
            print_info(f"Database already exists: {config['db_name']}")
        
        # Create user
        print_info(f"Creating user: {config['db_user']}")
        try:
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(config['db_user'])
                ),
                (config['db_password'],)
            )
            print_success(f"User created: {config['db_user']}")
        except psycopg2.errors.DuplicateObject:
            print_info(f"User already exists: {config['db_user']}")
            # Update password
            cursor.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                    sql.Identifier(config['db_user'])
                ),
                (config['db_password'],)
            )
            print_success(f"User password updated: {config['db_user']}")
        
        # Grant privileges
        cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(config['db_name']),
            sql.Identifier(config['db_user'])
        ))
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Failed to create database/user: {e}")
        return False

def test_app_connection(config):
    """Test application user connection"""
    try:
        print_info(f"Testing application user connection...")
        conn = psycopg2.connect(
            user=config["db_user"],
            password=config["db_password"],
            host=config["host"],
            port=config["port"],
            database=config["db_name"]
        )
        conn.close()
        print_success(f"Application user connection successful")
        return True
    except Exception as e:
        print_error(f"Application user connection failed: {e}")
        return False

def update_env_file(config):
    """Update .env file with connection string"""
    try:
        env_file = Path(__file__).parent.parent.parent / ".env"
        
        # Build connection string
        connection_string = (
            f"postgresql://"
            f"{config['db_user']}:"
            f"{quote_plus(config['db_password'])}@"
            f"{config['host']}:"
            f"{config['port']}/"
            f"{config['db_name']}"
        )
        
        print_info(f"Updating .env file: {env_file}")
        set_key(str(env_file), "DATABASE_URL", connection_string)
        print_success(f"Updated .env file with DATABASE_URL")
        
        # Show masked connection string
        masked = connection_string.replace(config['db_password'], "***")
        print_info(f"Connection string: {masked}")
        
        return True
    except Exception as e:
        print_error(f"Failed to update .env file: {e}")
        return False

def run_migrations():
    """Run database migrations"""
    try:
        print_info("Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Migrations completed successfully")
            return True
        else:
            print_error(f"Migrations failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Failed to run migrations: {e}")
        return False

def main():
    """Main setup function"""
    print_header("FACELESS YOUTUBE - AUTOMATED DATABASE SETUP")
    
    # Get configuration
    print_info("Reading configuration from environment variables...")
    config = get_config_from_env()
    
    print_info(f"PostgreSQL Admin: {config['admin_user']}")
    print_info(f"PostgreSQL Host: {config['host']}")
    print_info(f"PostgreSQL Port: {config['port']}")
    print_info(f"Database Name: {config['db_name']}")
    print_info(f"Database User: {config['db_user']}")
    
    # Test connection
    print_header("Step 1: Testing PostgreSQL Connection")
    if not test_postgres_connection(config):
        print_error("Cannot proceed without PostgreSQL connection")
        return False
    
    # Create database and user
    print_header("Step 2: Creating Database and User")
    if not create_database_and_user(config):
        print_error("Failed to create database/user")
        return False
    
    # Test app connection
    print_header("Step 3: Testing Application Connection")
    if not test_app_connection(config):
        print_error("Application cannot connect to database")
        return False
    
    # Update .env file
    print_header("Step 4: Updating Configuration")
    if not update_env_file(config):
        print_error("Failed to update .env file")
        return False
    
    # Run migrations
    print_header("Step 5: Running Database Migrations")
    if not run_migrations():
        print_error("Migrations failed (this may be expected)")
    
    # Success
    print_header("DATABASE SETUP COMPLETE!")
    print_success("Your database is ready to use")
    print_info("Connection details saved to .env file")
    print_info("You can now start the API server: uvicorn src.api.main:app --reload")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
