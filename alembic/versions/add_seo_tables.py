"""Add SEO tables

Revision ID: add_seo_tables_001
Revises: 
Create Date: 2026-02-27 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_seo_tables_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create seo_connections table
    op.create_table(
        'seo_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('google_email', sa.String(), nullable=False),
        sa.Column('site_url', sa.String(), nullable=True),
        sa.Column('is_connected', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seo_connections_id'), 'seo_connections', ['id'], unique=False)

    # Create seo_tokens table
    op.create_table(
        'seo_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('expiry_datetime', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['seo_connections.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id')
    )
    op.create_index(op.f('ix_seo_tokens_id'), 'seo_tokens', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_seo_tokens_id'), table_name='seo_tokens')
    op.drop_table('seo_tokens')
    op.drop_index(op.f('ix_seo_connections_id'), table_name='seo_connections')
    op.drop_table('seo_connections')
