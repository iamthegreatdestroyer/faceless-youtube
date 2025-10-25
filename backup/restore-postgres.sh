#!/bin/bash
# PostgreSQL Restore Script
# Restores PostgreSQL database from backup file

set -e

# Configuration
DB_HOST="${DB_HOST:-postgres-staging}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-faceless_youtube_staging}"

# Validate arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file> [target_database]"
    echo ""
    echo "Example:"
    echo "  $0 /backups/postgres/daily/faceless_youtube_staging_daily_2025-10-25.sql.gz"
    echo "  $0 /backups/postgres/daily/faceless_youtube_staging_daily_2025-10-25.sql.gz restore_test"
    echo ""
    echo "If target_database is not specified, restores to original database."
    exit 1
fi

BACKUP_FILE="$1"
TARGET_DB="${2:-$DB_NAME}"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Verify backup file is readable
if [ ! -r "$BACKUP_FILE" ]; then
    echo "✗ Backup file is not readable: $BACKUP_FILE"
    exit 1
fi

# Check if backup file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    BACKUP_CMD="gzip -dc"
    echo "✓ Backup file is compressed (gzip)"
else
    BACKUP_CMD="cat"
    echo "✓ Backup file is uncompressed"
fi

echo "=================================================="
echo "PostgreSQL Restore Script"
echo "=================================================="
echo "Backup File: $BACKUP_FILE"
echo "Backup Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "Target Host: $DB_HOST:$DB_PORT"
echo "Target User: $DB_USER"
echo "Target Database: $TARGET_DB"
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

# Verify backup integrity
echo "Verifying backup integrity..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    if ! gzip -t "$BACKUP_FILE"; then
        echo "✗ Backup file is corrupted!"
        exit 1
    fi
fi
echo "✓ Backup integrity verified"
echo ""

# If target database differs from source, create it
if [ "$TARGET_DB" != "$DB_NAME" ]; then
    echo "Creating target database: $TARGET_DB"
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '$TARGET_DB'" | grep -q 1; then
        echo "⚠ Database $TARGET_DB already exists. Dropping..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $TARGET_DB;"
    fi
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $TARGET_DB;"
    echo "✓ Database $TARGET_DB created"
    echo ""
fi

# Perform restore with verbose output
echo "Restoring database from backup..."
echo "(This may take several minutes depending on backup size)"
echo ""

if $BACKUP_CMD "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$TARGET_DB" \
    --echo-errors \
    2>&1 | grep -v "^$"; then
    
    echo ""
    echo "=================================================="
    echo "✓ Restore completed successfully!"
    echo "=================================================="
    echo "Target Database: $TARGET_DB"
    echo "End Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================================="
    
    # Verify restore by counting tables
    echo ""
    echo "Verifying restored data..."
    TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TARGET_DB" -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
    echo "✓ Restored database contains $TABLE_COUNT tables"
    
    exit 0
else
    echo ""
    echo "=================================================="
    echo "✗ Restore failed!"
    echo "=================================================="
    exit 1
fi
