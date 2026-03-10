"""merge two heads

Revision ID: d69dc1679a78
Revises: 7e378f970153, d14fd30cc580
Create Date: 2026-02-26 04:19:41.622374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd69dc1679a78'
down_revision: Union[str, None] = ('7e378f970153', 'd14fd30cc580')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
