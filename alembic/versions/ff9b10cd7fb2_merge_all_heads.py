"""merge all heads

Revision ID: ff9b10cd7fb2
Revises: add_event_table, add_seo_tables_001, d69dc1679a78
Create Date: 2026-03-10 12:15:19.070100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff9b10cd7fb2'
down_revision: Union[str, None] = ('add_event_table', 'add_seo_tables_001', 'd69dc1679a78')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
