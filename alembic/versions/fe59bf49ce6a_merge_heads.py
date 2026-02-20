"""Merge heads

Revision ID: fe59bf49ce6a
Revises: 001_initial_complete_schema, 0d271db948d7
Create Date: 2026-02-17 11:07:29.875638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe59bf49ce6a'
down_revision: Union[str, None] = ('001_initial_complete_schema', '0d271db948d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
