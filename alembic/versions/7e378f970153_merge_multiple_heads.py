"""merge multiple heads

Revision ID: 7e378f970153
Revises: 4a8d0ae98384, add_utm_fields_to_visits, fe59bf49ce6a
Create Date: 2026-02-20 04:46:26.823639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e378f970153'
down_revision: Union[str, None] = ('4a8d0ae98384', 'add_utm_fields_to_visits', 'fe59bf49ce6a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
