"""Enable pgcrypto extension for column-level encryption

Revision ID: enable_pgcrypto_001
Revises: 6c1890fbeadb
Create Date: 2025-10-24 00:00:00.000000

This migration enables the pgcrypto PostgreSQL extension which provides:
- encrypt()/decrypt() functions for symmetric encryption
- digest() function for hashing
- random number generation
- UUID generation

pgcrypto is used for protecting sensitive data at the column level:
- API keys
- OAuth tokens
- User secrets
- Configuration values
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "enable_pgcrypto_001"
down_revision: Union[str, Sequence[str], None] = "6c1890fbeadb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable pgcrypto extension."""
    # Create pgcrypto extension if it doesn't exist
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    print("\n✓ pgcrypto extension enabled")
    print("  Available functions:")
    print("    - encrypt(bytea, bytea, text)")
    print("    - decrypt(bytea, bytea, text)")
    print("    - digest(bytea, text)")
    print("    - gen_random_bytes(int)")
    print("    - gen_random_uuid()")


def downgrade() -> None:
    """Disable pgcrypto extension."""
    # Drop pgcrypto extension
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    
    print("\n✓ pgcrypto extension disabled")
