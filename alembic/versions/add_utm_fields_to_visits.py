"""
Add UTM fields to visits table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_utm_fields_to_visits'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add UTM fields to visits table
    op.add_column('visits', sa.Column('utm_source', sa.String(), nullable=True))
    op.add_column('visits', sa.Column('utm_medium', sa.String(), nullable=True))
    op.add_column('visits', sa.Column('utm_campaign', sa.String(), nullable=True))

def downgrade():
    # Remove UTM fields from visits table
    op.drop_column('visits', 'utm_campaign')
    op.drop_column('visits', 'utm_medium')
    op.drop_column('visits', 'utm_source')
