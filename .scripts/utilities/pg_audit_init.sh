#!/bin/bash
# PostgreSQL Audit Logging Configuration
# This script configures PostgreSQL for comprehensive audit logging

set -e

echo "🔒 Configuring PostgreSQL Audit Logging..."

# Wait for PostgreSQL to start
echo "⏳ Waiting for PostgreSQL to become ready..."
until pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; do
    sleep 1
done

echo "✓ PostgreSQL is ready"

# Enable pgcrypto extension
echo "  → Enabling pgcrypto extension for encryption..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SELECT 'pgcrypto' as extension_name, extversion as version 
FROM pg_extension WHERE extname = 'pgcrypto';
EOF

echo "  ✓ pgcrypto enabled"

# Enable pgaudit extension
echo "  → Enabling pgaudit extension for audit logging..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
CREATE EXTENSION IF NOT EXISTS pgaudit;
SELECT 'pgaudit' as extension_name, extversion as version 
FROM pg_extension WHERE extname = 'pgaudit';
EOF

echo "  ✓ pgaudit enabled"

# Configure audit logging
echo "  → Configuring audit logging..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
-- Create auditor role for managing audit logs
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pgaudit_admin') THEN
        CREATE ROLE pgaudit_admin;
    END IF;
END
\$\$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO pgaudit_admin;
GRANT USAGE ON SCHEMA public TO pgaudit_admin;
GRANT SELECT ON pg_stat_statements TO pgaudit_admin;

-- Create audit logging function
CREATE OR REPLACE FUNCTION public.audit_trigger()
RETURNS TRIGGER AS \$\$
BEGIN
    -- This function is called when pgaudit logs events
    -- Audit logs are written to PostgreSQL log files
    RETURN NEW;
END;
\$\$ LANGUAGE plpgsql SECURITY DEFINER;

-- Log important audit events
-- Note: pgaudit.log must be set in postgresql.conf to enable logging
-- Example: pgaudit.log = 'ALL'

-- Display current configuration
SHOW pgaudit.log;
SHOW pgaudit.log_rows;
SHOW pgaudit.log_statement;

-- Display enabled extensions
SELECT extname, extversion 
FROM pg_extension 
WHERE extname IN ('pgcrypto', 'pgaudit')
ORDER BY extname;
EOF

echo "✓ PostgreSQL audit logging configured successfully"
echo ""
echo "📋 Audit Configuration Summary:"
echo "   • pgcrypto: Enabled (encryption support)"
echo "   • pgaudit: Enabled (audit logging)"
echo "   • pgaudit_admin role: Created"
echo ""
echo "🔐 Encryption Ready:"
echo "   Use: SELECT pgp_sym_encrypt('secret', 'password')"
echo "        SELECT pgp_sym_decrypt(encrypted_data, 'password')"
echo ""
