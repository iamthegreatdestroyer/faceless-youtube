#!/bin/bash
# PostgreSQL Automated Backup Script
# Backs up PostgreSQL database with compression and retention

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
DB_HOST="${DB_HOST:-postgres-staging}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-faceless_youtube_staging}"

# Backup frequency
DAILY_RETENTION=7  # Keep 7 daily backups
WEEKLY_RETENTION=12  # Keep 12 weekly backups (3 months)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)
CURRENT_DAY=$(date +%w)  # 0=Sunday, 6=Saturday
CURRENT_TIME=$(date +%Y-%m-%d_%H-%M-%S)

# Determine backup type and path
if [ "$CURRENT_DAY" = "0" ]; then
    # Sunday = Weekly backup
    BACKUP_TYPE="weekly"
    BACKUP_PATH="$BACKUP_DIR/weekly"
else
    # Daily backup
    BACKUP_TYPE="daily"
    BACKUP_PATH="$BACKUP_DIR/daily"
fi

# Backup filename
BACKUP_FILE="${BACKUP_PATH}/${DB_NAME}_${BACKUP_TYPE}_${CURRENT_DATE}.sql.gz"

echo "=================================================="
echo "PostgreSQL Automated Backup"
echo "=================================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Type: $BACKUP_TYPE"
echo "Output: $BACKUP_FILE"
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

# Perform backup with error handling
if PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --compress=9 \
    > "$BACKUP_FILE" 2>&1; then
    
    # Get backup file size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    
    echo "✓ Backup completed successfully"
    echo "  File: $BACKUP_FILE"
    echo "  Size: $BACKUP_SIZE"
    echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Verify backup integrity
    if gzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo "✓ Backup integrity verified"
    else
        echo "✗ Backup integrity check failed!"
        exit 1
    fi
    
    # Clean up old backups based on retention policy
    echo ""
    echo "Applying retention policy..."
    
    if [ "$BACKUP_TYPE" = "weekly" ]; then
        # Remove old weekly backups
        find "$BACKUP_DIR/weekly" -name "${DB_NAME}_weekly_*.sql.gz" -type f -mtime +$((WEEKLY_RETENTION * 7)) -delete
        echo "✓ Removed weekly backups older than $WEEKLY_RETENTION weeks"
    else
        # Remove old daily backups
        find "$BACKUP_DIR/daily" -name "${DB_NAME}_daily_*.sql.gz" -type f -mtime +$DAILY_RETENTION -delete
        echo "✓ Removed daily backups older than $DAILY_RETENTION days"
    fi
    
    echo "=================================================="
    echo "✓ Backup process completed successfully"
    echo "=================================================="
    exit 0
    
else
    echo "✗ Backup failed!"
    echo "Error occurred during pg_dump"
    exit 1
fi
