"""Merge UTM fields with existing migrations

Revision ID: 4a4a9aed9292
Revises: add_utm_fields_to_visits, fe59bf49ce6a
Create Date: 2026-02-20 17:47:17.031463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a4a9aed9292'
down_revision: Union[str, None] = ('add_utm_fields_to_visits', 'fe59bf49ce6a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
