"""merge multiple heads

Revision ID: 4a8d0ae98384
Revises: 001_initial_complete_schema, 0d271db948d7
Create Date: 2026-02-06 12:13:11.241877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8d0ae98384'
down_revision: Union[str, None] = ('001_initial_complete_schema', '0d271db948d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
