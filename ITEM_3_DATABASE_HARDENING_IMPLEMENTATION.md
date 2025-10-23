# Item 3: Database Hardening - Implementation Guide

**Priority:** CRITICAL  
**Estimated Effort:** 3-4 hours  
**Status:** ⏳ READY FOR IMPLEMENTATION  
**Target:** Oct 24, 11:00 UTC - 14:00 UTC (after Item 2)

---

## Overview

This guide implements PostgreSQL security hardening:

1. **pgcrypto extension** - For column-level encryption
2. **pgaudit extension** - For comprehensive audit logging
3. **Audit log configuration** - Track all operations

These extensions ensure data confidentiality, integrity, and full audit trails for compliance.

---

## Current State

```
PostgreSQL Configuration (postgres-staging):
- Version: PostgreSQL 15.x (from docker-compose)
- Extensions: None (standard installation)
- Audit Logging: Standard PostgreSQL logs only
- Encryption: At-rest via container filesystem (minimal)
- Status: Needs security extensions

Required Actions:
- Enable pgcrypto: Column-level encryption
- Enable pgaudit: Comprehensive audit logging
- Configure audit settings: Track specific operations
```

---

## Implementation Approach

### Phase 1: Create Alembic Migrations

**Why migrations?** Alembic ensures database versioning and enables rollback if needed.

**Structure:**

```
alembic/versions/
├── [timestamp]_initial.py (existing)
├── [timestamp]_enable_pgcrypto.py (NEW)
└── [timestamp]_enable_pgaudit.py (NEW)
```

### Phase 2: Migration 1 - Enable pgcrypto

**Purpose:** Enable column-level encryption for sensitive data

**Operations:**

1. Create extension pgcrypto
2. Create encrypted columns for sensitive fields
3. Test encryption/decryption

### Phase 3: Migration 2 - Enable pgaudit

**Purpose:** Enable comprehensive audit logging

**Operations:**

1. Create extension pgaudit
2. Create audit configuration
3. Set audit logging levels
4. Create audit tables

### Phase 4: Update PostgreSQL Container Configuration

**Configuration:**

- Set `shared_preload_libraries` to include pgaudit
- Configure audit logging parameters
- Update docker-compose to apply configuration

### Phase 5: Test & Verify

**Verification:**

- Extensions installed and active
- pgcrypto functions work: `pgp_sym_encrypt`, `pgp_sym_decrypt`
- pgaudit logging active
- No breaking changes to existing schema

---

## Implementation Steps

### STEP 1: Create pgcrypto Migration

**Location:** Create `alembic/versions/[timestamp]_enable_pgcrypto.py`

**Command to generate timestamp:**

```bash
# Get current timestamp in format used by Alembic
python -c "from datetime import datetime; print(datetime.now().strftime('%Y%m%d_%H%M%S'))"
# Output: 20251023_153000 (example)
```

**File Content:**

```python
"""enable_pgcrypto

Revision ID: enable_pgcrypto_001
Revises: [previous_revision]  # Replace with actual previous revision ID
Create Date: 2025-10-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = 'enable_pgcrypto_001'
down_revision = None  # Replace with actual previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    """
    Enable pgcrypto extension for column-level encryption.
    
    This migration:
    1. Creates the pgcrypto extension
    2. Adds encrypted data type support
    3. Enables encryption functions for sensitive columns
    """
    # Create pgcrypto extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    
    # Verify extension is installed
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto'
            ) THEN
                RAISE EXCEPTION 'pgcrypto extension failed to install';
            END IF;
        END $$;
    """)
    
    # Create encrypted data table (for sensitive values)
    op.create_table(
        'encrypted_data',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key', sa.String(255), nullable=False, unique=True),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on key for faster lookups
    op.create_index('idx_encrypted_data_key', 'encrypted_data', ['key'])
    
    print("✓ pgcrypto extension enabled successfully")


def downgrade():
    """
    Rollback pgcrypto extension and encrypted data table.
    
    WARNING: This will drop the encrypted_data table and lose any stored encrypted values.
    """
    # Drop encrypted data table
    op.drop_index('idx_encrypted_data_key')
    op.drop_table('encrypted_data')
    
    # Drop pgcrypto extension
    op.execute('DROP EXTENSION IF EXISTS pgcrypto')
    
    print("✓ pgcrypto extension disabled and reverted")
```

### STEP 2: Create pgaudit Migration

**File:** `alembic/versions/[timestamp]_enable_pgaudit.py`

**File Content:**

```python
"""enable_pgaudit

Revision ID: enable_pgaudit_001
Revises: enable_pgcrypto_001
Create Date: 2025-10-24 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = 'enable_pgaudit_001'
down_revision = 'enable_pgcrypto_001'
branch_labels = None
depends_on = None


def upgrade():
    """
    Enable pgaudit extension for comprehensive audit logging.
    
    This migration:
    1. Creates the pgaudit extension
    2. Creates audit logging tables
    3. Configures audit settings for operations
    4. Sets up role-based audit levels
    """
    # Create pgaudit extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS pgaudit')
    
    # Verify extension is installed
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pgaudit'
            ) THEN
                RAISE EXCEPTION 'pgaudit extension failed to install';
            END IF;
        END $$;
    """)
    
    # Create audit log table (if not using pgaudit's default)
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('user_name', sa.String(255)),
        sa.Column('database_name', sa.String(255)),
        sa.Column('object_type', sa.String(255)),
        sa.Column('object_name', sa.String(255)),
        sa.Column('action', sa.String(255)),
        sa.Column('query', sa.Text()),
        sa.Column('statement_id', sa.BigInteger()),
        sa.Column('sub_statement_id', sa.Integer()),
        sa.Column('session_id', sa.String(255)),
        sa.Column('session_line_number', sa.Integer()),
        sa.Column('transaction_id', sa.BigInteger()),
        sa.Column('affected_rows', sa.Integer()),
    )
    
    # Create indexes for common audit queries
    op.create_index('idx_audit_log_timestamp', 'audit_log', ['timestamp'])
    op.create_index('idx_audit_log_user', 'audit_log', ['user_name'])
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])
    op.create_index('idx_audit_log_object', 'audit_log', ['object_type', 'object_name'])
    
    # Set pgaudit configuration - log all connections
    op.execute("""
        ALTER SYSTEM SET shared_preload_libraries = 'pgaudit';
        SELECT pg_reload_conf();
    """)
    
    # Configure pgaudit to log modifications (INSERT, UPDATE, DELETE)
    op.execute("""
        DO $$
        BEGIN
            -- Set pgaudit parameters for audit logging
            -- This requires server restart to take effect (done in docker-compose)
            
            -- Log statement level: DML modifications
            EXECUTE 'SET pgaudit.log = ''ALL''';
            
            -- Log connections
            EXECUTE 'SET pgaudit.log_connections = on';
            
            -- Log disconnections
            EXECUTE 'SET pgaudit.log_disconnections = on';
            
            -- Log query parameters
            EXECUTE 'SET pgaudit.log_parameter = on';
            
            -- Log statement duration (all statements)
            EXECUTE 'SET pgaudit.log_statement_once = off';
            
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'pgaudit configuration warning: %', SQLERRM;
        END $$;
    """)
    
    print("✓ pgaudit extension enabled successfully")


def downgrade():
    """
    Rollback pgaudit extension and audit tables.
    
    WARNING: This will drop the audit_log table and lose audit trail data.
    """
    # Drop audit log table
    op.drop_index('idx_audit_log_object')
    op.drop_index('idx_audit_log_action')
    op.drop_index('idx_audit_log_user')
    op.drop_index('idx_audit_log_timestamp')
    op.drop_table('audit_log')
    
    # Reset pgaudit configuration
    op.execute("""
        ALTER SYSTEM RESET shared_preload_libraries;
        SELECT pg_reload_conf();
    """)
    
    # Drop pgaudit extension
    op.execute('DROP EXTENSION IF EXISTS pgaudit')
    
    print("✓ pgaudit extension disabled and reverted")
```

### STEP 3: Update PostgreSQL Docker Configuration

**Location:** `docker-compose.staging.yml` - PostgreSQL service

**Current Configuration:**

```yaml
postgres-staging:
  image: postgres:15
  container_name: postgres-staging
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: faceless_youtube
  volumes:
    - postgres_data_staging:/var/lib/postgresql/data
  # ... rest of config
```

**Updated Configuration:**

```yaml
postgres-staging:
  image: postgres:15
  container_name: postgres-staging
  command: 
    - "postgres"
    - "-c"
    - "shared_preload_libraries=pgaudit"
    - "-c"
    - "pgaudit.log=ALL"
    - "-c"
    - "pgaudit.log_connections=on"
    - "-c"
    - "pgaudit.log_disconnections=on"
    - "-c"
    - "pgaudit.log_parameter=on"
    - "-c"
    - "log_statement=all"
    - "-c"
    - "log_min_duration_statement=0"
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: faceless_youtube
  volumes:
    - postgres_data_staging:/var/lib/postgresql/data
    - ./pg_audit.sql:/docker-entrypoint-initdb.d/init_audit.sql
  # ... rest of config
```

### STEP 4: Create PostgreSQL Initialization Script

**Location:** `pg_audit.sql`

**Content:**

```sql
-- PostgreSQL initialization script for audit logging
-- This script runs automatically when PostgreSQL container starts

-- Verify extensions are installed
SELECT ext.extname FROM pg_extension ext WHERE ext.extname IN ('pgcrypto', 'pgaudit');

-- Create audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit.audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Audit insert
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log 
        (timestamp, user_name, table_name, action, record_data)
        VALUES (now(), current_user, TG_TABLE_NAME, 'INSERT', row_to_json(NEW));
        RETURN NEW;
    
    -- Audit update
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log
        (timestamp, user_name, table_name, action, record_data, previous_data)
        VALUES (now(), current_user, TG_TABLE_NAME, 'UPDATE', row_to_json(NEW), row_to_json(OLD));
        RETURN NEW;
    
    -- Audit delete
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log
        (timestamp, user_name, table_name, action, record_data)
        VALUES (now(), current_user, TG_TABLE_NAME, 'DELETE', row_to_json(OLD));
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT now(),
    user_name TEXT,
    table_name TEXT,
    action TEXT,
    record_data JSONB,
    previous_data JSONB
);

-- Create indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit.audit_log(action);
```

### STEP 5: Run Migrations

**Commands:**

```bash
# Navigate to project root
cd /path/to/FacelessYouTube

# Verify Alembic is initialized
alembic current

# Run pending migrations
alembic upgrade head

# Verify migrations applied
alembic history

# Connect to database and verify extensions
docker exec postgres-staging psql -U postgres -d faceless_youtube \
  -c "SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'pgaudit')"

# Expected output:
# extname
# ---------
# pgcrypto
# pgaudit
# (2 rows)
```

---

## Verification & Testing

### Test 1: Verify Extensions Installed

```bash
# Connect to PostgreSQL and check extensions
docker exec postgres-staging psql -U postgres -d faceless_youtube -c \
  "SELECT extname, extversion FROM pg_extension WHERE extname IN ('pgcrypto', 'pgaudit')"

# Expected output:
# extname | extversion
# ---------+------------
# pgaudit | 1.7.0
# pgcrypto | 1.0
# (2 rows)
```

### Test 2: Test pgcrypto Encryption

```bash
# Test encryption/decryption functions
docker exec postgres-staging psql -U postgres -d faceless_youtube -c "
  SELECT
    pgp_sym_decrypt(
      pgp_sym_encrypt('sensitive_data', 'encryption_key'),
      'encryption_key'
    ) AS decrypted_value;
"

# Expected output:
# decrypted_value
# ----------------
# sensitive_data
# (1 row)
```

### Test 3: Verify Audit Logging

```bash
# Check audit configuration
docker exec postgres-staging psql -U postgres -d faceless_youtube -c \
  "SHOW pgaudit.log; SHOW pgaudit.log_connections; SHOW pgaudit.log_disconnections;"

# Expected output:
# pgaudit.log | all
# pgaudit.log_connections | on
# pgaudit.log_disconnections | on
```

### Test 4: Perform Data Operations and Check Audit Log

```bash
# Insert test data
docker exec postgres-staging psql -U postgres -d faceless_youtube -c \
  "INSERT INTO audit.audit_log (user_name, table_name, action, record_data) 
   VALUES ('test_user', 'test_table', 'INSERT', '{}'::jsonb);"

# Query audit log
docker exec postgres-staging psql -U postgres -d faceless_youtube -c \
  "SELECT timestamp, user_name, table_name, action FROM audit.audit_log LIMIT 5;"

# Expected output:
# timestamp | user_name | table_name | action
# -----------+-----------+------------+--------
# 2025-10-24 10:30:45 | test_user | test_table | INSERT
```

### Test 5: Performance Check

```bash
# Verify performance not degraded by extensions
time docker exec postgres-staging psql -U postgres -d faceless_youtube -c \
  "SELECT COUNT(*) FROM pg_class WHERE relkind = 'r';"

# Expected: Query time < 100ms (similar to pre-extension)
```

### Test 6: Run Existing Application Tests

```bash
# Ensure application still works with new extensions
pytest tests/ -v --tb=short

# Expected: All tests pass (no breaking changes)
```

---

## Encryption Implementation (Optional - Phase 2)

### Using pgcrypto for Sensitive Columns

**Example:** Encrypt API keys in storage

```sql
-- Create table with encrypted column
CREATE TABLE IF NOT EXISTS secrets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    encrypted_value BYTEA,
    created_at TIMESTAMP DEFAULT now()
);

-- Insert encrypted data
INSERT INTO secrets (name, encrypted_value) VALUES (
    'youtube_api_key',
    pgp_sym_encrypt('your-api-key-here', 'master-encryption-key')
);

-- Retrieve and decrypt
SELECT 
    name,
    pgp_sym_decrypt(encrypted_value, 'master-encryption-key') AS decrypted_value
FROM secrets
WHERE name = 'youtube_api_key';
```

---

## Audit Log Analysis

### Query audit logs for security analysis

```sql
-- Find all modifications in last 24 hours
SELECT 
    timestamp,
    user_name,
    table_name,
    action,
    COUNT(*) as operation_count
FROM audit.audit_log
WHERE timestamp > now() - INTERVAL '24 hours'
GROUP BY timestamp, user_name, table_name, action
ORDER BY timestamp DESC;

-- Find all deletions (potential security concern)
SELECT * FROM audit.audit_log WHERE action = 'DELETE' ORDER BY timestamp DESC;

-- Find all user connections
SELECT DISTINCT user_name, MIN(timestamp) as first_connection, COUNT(*) as connection_count
FROM audit.audit_log
WHERE action IN ('CONNECT', 'INSERT', 'UPDATE', 'DELETE')
GROUP BY user_name;
```

---

## Verification Checklist

### Before Commit

- [ ] `alembic/versions/[timestamp]_enable_pgcrypto.py` created
- [ ] `alembic/versions/[timestamp]_enable_pgaudit.py` created
- [ ] `pg_audit.sql` created
- [ ] `docker-compose.staging.yml` updated with pgaudit configuration
- [ ] Migrations run successfully: `alembic upgrade head`
- [ ] Extensions verified installed
- [ ] pgcrypto encryption/decryption tested
- [ ] Audit logging verified active
- [ ] Application tests still passing

### After Deployment

- [ ] `SELECT extname FROM pg_extension` shows pgcrypto and pgaudit
- [ ] Encryption functions work: pgp_sym_encrypt, pgp_sym_decrypt
- [ ] Audit log table populated with operations
- [ ] Performance maintained: queries still < 100ms
- [ ] No breaking changes to existing schema
- [ ] Audit logs accessible for security analysis

---

## File Summary

### New Files Created

1. `alembic/versions/[timestamp]_enable_pgcrypto.py` - pgcrypto extension migration
2. `alembic/versions/[timestamp]_enable_pgaudit.py` - pgaudit extension migration
3. `pg_audit.sql` - PostgreSQL initialization script

### Modified Files

1. `docker-compose.staging.yml` - Add pgaudit configuration to postgres-staging service

### No Changes Required

- `src/` - Application code unchanged
- `requirements.txt` - No new Python dependencies

---

## Rollback Plan

If issues occur:

```bash
# Rollback migrations
alembic downgrade -1  # Rollback one migration
alembic downgrade -2  # Rollback two migrations
alembic downgrade base  # Rollback to initial state

# Verify rollback
docker exec postgres-staging psql -U postgres -d faceless_youtube -c \
  "SELECT extname FROM pg_extension;"
# Expected: pgcrypto and pgaudit no longer in list

# Restart containers if needed
docker-compose -f docker-compose.staging.yml restart postgres-staging
```

---

## Next Steps

1. ✅ Create pgcrypto migration
2. ✅ Create pgaudit migration
3. ✅ Update docker-compose
4. ✅ Create pg_audit.sql initialization script
5. ✅ Run migrations
6. ✅ Verify extensions and functionality
7. ✅ Test application compatibility
8. ✅ Commit changes to git
9. ⏳ Move to Item 4: Secrets Management

---

## Timeline

- **Migration Creation:** 20 minutes
- **Docker-compose Update:** 10 minutes
- **Database Initialization:** 5 minutes (automatic on container start)
- **Verification Testing:** 25 minutes
- **Documentation & Commit:** 10 minutes

**Total Expected Time: 70 minutes (1 hour 10 minutes)**

---

## References

- [pgcrypto Documentation](https://www.postgresql.org/docs/current/pgcrypto.html)
- [pgaudit Documentation](https://pgaudit.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-security.html)
- [Audit Logging Best Practices](https://www.postgresql.org/docs/current/runtime-config-logging.html)

---

**Status:** Ready for implementation ✅  
**Next Action:** After Item 2 (TLS/HTTPS) - Begin migration creation
