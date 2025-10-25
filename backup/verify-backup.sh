#!/bin/bash
# PostgreSQL Backup Verification Script
# Verifies backup integrity and creates verification reports

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"

echo "=================================================="
echo "PostgreSQL Backup Verification"
echo "=================================================="
echo "Backup Directory: $BACKUP_DIR"
echo "Scan Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "✗ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# Initialize counters
TOTAL_BACKUPS=0
VERIFIED_BACKUPS=0
FAILED_BACKUPS=0
TOTAL_SIZE=0

# Scan and verify all backups
echo "Scanning backup files..."
echo ""

for backup_file in $(find "$BACKUP_DIR" -name "*.sql.gz" -type f | sort -r); do
    TOTAL_BACKUPS=$((TOTAL_BACKUPS + 1))
    
    # Get file information
    FILE_NAME=$(basename "$backup_file")
    FILE_SIZE=$(du -h "$backup_file" | cut -f1)
    TOTAL_SIZE=$((TOTAL_SIZE + $(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")))
    FILE_DATE=$(stat -f %Sm -t "%Y-%m-%d %H:%M:%S" "$backup_file" 2>/dev/null || stat -c %y "$backup_file" | cut -d. -f1)
    
    # Verify backup integrity
    if gzip -t "$backup_file" 2>/dev/null; then
        VERIFIED_BACKUPS=$((VERIFIED_BACKUPS + 1))
        echo "✓ $FILE_NAME ($FILE_SIZE) - $FILE_DATE"
    else
        FAILED_BACKUPS=$((FAILED_BACKUPS + 1))
        echo "✗ $FILE_NAME ($FILE_SIZE) - CORRUPTED!"
    fi
done

echo ""
echo "=================================================="
echo "Verification Report"
echo "=================================================="
echo "Total Backups: $TOTAL_BACKUPS"
echo "Verified: $VERIFIED_BACKUPS"
echo "Failed: $FAILED_BACKUPS"
echo "Total Size: $(numfmt --to=iec $TOTAL_SIZE 2>/dev/null || du -h "$BACKUP_DIR" | tail -1 | cut -f1)"
echo "=================================================="

# Check backup age
echo ""
echo "Checking backup recency..."

LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f -printf '%T@\n' | sort -n | tail -1)
if [ -z "$LATEST_BACKUP" ]; then
    echo "✗ No backups found!"
    exit 1
fi

BACKUP_AGE=$(($(date +%s) - ${LATEST_BACKUP%.*}))
BACKUP_AGE_HOURS=$((BACKUP_AGE / 3600))
BACKUP_AGE_DAYS=$((BACKUP_AGE / 86400))

if [ $BACKUP_AGE_DAYS -eq 0 ]; then
    echo "✓ Latest backup is $BACKUP_AGE_HOURS hours old"
elif [ $BACKUP_AGE_DAYS -le 1 ]; then
    echo "✓ Latest backup is 1 day old"
else
    echo "⚠ Latest backup is $BACKUP_AGE_DAYS days old"
fi

# Final status
echo ""
if [ $FAILED_BACKUPS -eq 0 ]; then
    echo "✓ All backups verified successfully!"
    exit 0
else
    echo "✗ $FAILED_BACKUPS backup(s) failed verification!"
    exit 1
fi
