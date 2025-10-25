"""Enable pgaudit extension for comprehensive audit logging

Revision ID: enable_pgaudit_002
Revises: enable_pgcrypto_001
Create Date: 2025-10-24 00:00:00.000000

This migration enables the pgaudit PostgreSQL extension which provides:
- Comprehensive logging of all database operations
- Audit trails for compliance requirements
- Session logging and statement logging
- Object-level auditing

pgaudit configuration (set via environment or postgresql.conf):
- pgaudit.log = 'ALL' - Log all statements
- pgaudit.log_rows = on - Log affected rows
- pgaudit.log_statement = off - Don't log PREPARE/EXECUTE
- pgaudit.role = 'pgaudit_admin' - Auditor role

Audit logs go to PostgreSQL log file and can be forwarded to:
- System log (syslog)
- Application logs
- SIEM systems
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "enable_pgaudit_002"
down_revision: Union[str, Sequence[str], None] = "enable_pgcrypto_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable pgaudit extension."""
    # Create pgaudit extension if it doesn't exist
    # Note: pgaudit requires shared_preload_libraries in postgresql.conf
    # If not already loaded, this will fail with helpful error message
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgaudit")
        print("\n✓ pgaudit extension enabled")
        print("  Audit logging will capture:")
        print("    - INSERT operations")
        print("    - UPDATE operations")
        print("    - DELETE operations")
        print("    - SELECT operations (if enabled)")
        print("    - DDL operations")
        print("    - FUNCTION calls")
    except Exception as e:
        print(f"\n⚠ pgaudit extension creation note: {e}")
        print("  pgaudit requires shared_preload_libraries configuration")
        print("  Restart PostgreSQL with updated postgresql.conf")


def downgrade() -> None:
    """Disable pgaudit extension."""
    # Drop pgaudit extension
    op.execute("DROP EXTENSION IF EXISTS pgaudit")
    
    print("\n✓ pgaudit extension disabled")
