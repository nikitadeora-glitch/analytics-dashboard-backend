"""Merge verification fields



Revision ID: 1b3088a88a8f

Revises: 4a4a9aed9292, create_script_verifications_table

Create Date: 2026-02-23 16:37:48.481589



"""

from typing import Sequence, Union



from alembic import op

import sqlalchemy as sa





# revision identifiers, used by Alembic.

revision: str = '1b3088a88a8f'

down_revision: Union[str, None] = ('4a4a9aed9292', 'create_script_verifications_table')

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None





def upgrade() -> None:

    pass





def downgrade() -> None:

    pass

