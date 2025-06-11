#!/bin/bash
# Nightly PostgreSQL database backup script for Dear Teddy
# Backs up the database to S3 bucket using AWS credentials

set -e

# Configuration
BACKUP_DIR="/tmp/db_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="dearteddy_backup_${DATE}.sql"
S3_BUCKET="dearteddy-backups"
RETENTION_DAYS=30

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting database backup process..."

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Extract database connection details from DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    log "ERROR: DATABASE_URL environment variable not set"
    exit 1
fi

# Parse DATABASE_URL (format: postgresql://user:password@host:port/dbname)
DB_URL_PARSED=$(echo $DATABASE_URL | sed 's|postgresql://||' | sed 's|postgres://||')
DB_USER=$(echo $DB_URL_PARSED | cut -d: -f1)
DB_PASS=$(echo $DB_URL_PARSED | cut -d: -f2 | cut -d@ -f1)
DB_HOST=$(echo $DB_URL_PARSED | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo $DB_URL_PARSED | cut -d: -f3 | cut -d/ -f1)
DB_NAME=$(echo $DB_URL_PARSED | cut -d/ -f2)

log "Database: $DB_NAME on $DB_HOST:$DB_PORT"

# Set PostgreSQL password
export PGPASSWORD="$DB_PASS"

# Create database dump
log "Creating database dump..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --clean --if-exists --create \
    --format=plain \
    --file="${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    log "Database dump created successfully: ${BACKUP_FILE}"
    
    # Compress the backup
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    
    log "Backup compressed: ${COMPRESSED_FILE}"
    
    # Upload to S3
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        log "Uploading backup to S3..."
        
        # Use aws cli to upload
        aws s3 cp "${BACKUP_DIR}/${COMPRESSED_FILE}" \
            "s3://${S3_BUCKET}/backups/${COMPRESSED_FILE}" \
            --region us-east-1
        
        if [ $? -eq 0 ]; then
            log "Backup uploaded to S3 successfully"
            
            # Clean up old backups (keep last 30 days)
            log "Cleaning up old backups..."
            aws s3 ls "s3://${S3_BUCKET}/backups/" | \
                awk '{print $4}' | \
                grep "dearteddy_backup_" | \
                sort -r | \
                tail -n +$((RETENTION_DAYS + 1)) | \
                while read backup; do
                    aws s3 rm "s3://${S3_BUCKET}/backups/$backup"
                    log "Removed old backup: $backup"
                done
        else
            log "ERROR: Failed to upload backup to S3"
            exit 1
        fi
    else
        log "WARNING: AWS credentials not found, backup saved locally only"
    fi
    
    # Clean up local backup
    rm -f "${BACKUP_DIR}/${COMPRESSED_FILE}"
    log "Local backup file cleaned up"
    
else
    log "ERROR: Database dump failed"
    exit 1
fi

log "Database backup process completed successfully"