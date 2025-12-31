"""add_email_to_password_reset

Revision ID: 3b575d55f47c
Revises: 
Create Date: 2025-12-29 14:54:22.767387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b575d55f47c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email column to password_resets table
    op.add_column('password_resets', sa.Column('email', sa.String(), nullable=False))
    
    # Add used_at column to password_resets table
    op.add_column('password_resets', sa.Column('used_at', sa.DateTime(), nullable=True))
    
    # If there are existing records, we need to set a default email
    # First, check if the table exists and has data
    conn = op.get_bind()
    result = conn.execute("SELECT COUNT(*) FROM password_resets").scalar()
    
    if result > 0:
        # If there are existing records, we need to update them with a default email
        # This assumes there's a user_id column to join with users table
        try:
            conn.execute("""
                UPDATE password_resets pr
                SET email = u.email
                FROM users u
                WHERE pr.user_id = u.id
            """)
        except Exception as e:
            print(f"Warning: Could not update existing password reset records: {e}")
            # If the update fails, set a default email
            conn.execute("UPDATE password_resets SET email = 'unknown@example.com'")
    
    # Create an index on the email column for faster lookups
    op.create_index(op.f('ix_password_resets_email'), 'password_resets', ['email'], unique=False)


def downgrade() -> None:
    # Drop the index first
    op.drop_index(op.f('ix_password_resets_email'), table_name='password_resets')
    
    # Drop the columns
    op.drop_column('password_resets', 'used_at')
    op.drop_column('password_resets', 'email')
