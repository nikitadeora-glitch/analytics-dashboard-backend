"""Add Event table for custom event tracking

Revision ID: add_event_table
Revises: 
Create Date: 2026-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_event_table'
down_revision = '001_initial_complete_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visit_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_events_id', 'events', ['id'])
    op.create_index('ix_events_visit_id', 'events', ['visit_id'])
    op.create_index('ix_events_event_type', 'events', ['event_type'])
    op.create_index('ix_events_timestamp', 'events', ['timestamp'])


def downgrade():
    # Drop events table
    op.drop_table('events')
