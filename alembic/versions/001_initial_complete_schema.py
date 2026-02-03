"""Initial complete schema - creates all tables

Revision ID: 001_initial_complete_schema
Revises: 
Create Date: 2026-02-03 14:30:00.000000

This migration creates all the necessary tables for the analytics dashboard.
Run this migration on a fresh database to set up the complete schema.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '001_initial_complete_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for the analytics dashboard"""
    
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),  # Optional for Google users
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # 2. Create password_resets table
    op.create_table(
        'password_resets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_id'), 'password_resets', ['id'], unique=False)
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=True)
    
    # 3. Create email_verifications table
    op.create_table(
        'email_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_verifications_id'), 'email_verifications', ['id'], unique=False)
    op.create_index(op.f('ix_email_verifications_token'), 'email_verifications', ['token'], unique=True)
    
    # 4. Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('tracking_code', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_tracking_code'), 'projects', ['tracking_code'], unique=True)
    
    # 5. Create visits table
    op.create_table(
        'visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('visitor_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('isp', sa.String(), nullable=True),
        sa.Column('device', sa.String(), nullable=True),
        sa.Column('browser', sa.String(), nullable=True),
        sa.Column('os', sa.String(), nullable=True),
        sa.Column('screen_resolution', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('local_time', sa.String(), nullable=True),
        sa.Column('local_time_formatted', sa.String(), nullable=True),
        sa.Column('timezone_offset', sa.String(), nullable=True),
        sa.Column('referrer', sa.String(), nullable=True),
        sa.Column('entry_page', sa.String(), nullable=True),
        sa.Column('exit_page', sa.String(), nullable=True),
        sa.Column('session_duration', sa.Integer(), nullable=True),
        sa.Column('visited_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('is_unique', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_new_session', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_visits_id'), 'visits', ['id'], unique=False)
    op.create_index(op.f('ix_visits_visitor_id'), 'visits', ['visitor_id'], unique=False)
    op.create_index(op.f('ix_visits_session_id'), 'visits', ['session_id'], unique=False)
    op.create_index(op.f('ix_visits_visited_at'), 'visits', ['visited_at'], unique=False)
    
    # 6. Create pages table
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('total_views', sa.Integer(), nullable=True, default=0),
        sa.Column('unique_views', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_time_spent', sa.Float(), nullable=True, default=0.0),
        sa.Column('bounce_rate', sa.Float(), nullable=True, default=0.0),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pages_id'), 'pages', ['id'], unique=False)
    
    # 7. Create page_views table
    op.create_table(
        'page_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visit_id', sa.Integer(), nullable=True),
        sa.Column('page_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('time_spent', sa.Integer(), nullable=True),
        sa.Column('scroll_depth', sa.Float(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['visit_id'], ['visits.id'], ),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_page_views_id'), 'page_views', ['id'], unique=False)
    op.create_index(op.f('ix_page_views_viewed_at'), 'page_views', ['viewed_at'], unique=False)
    
    # 8. Create traffic_sources table
    op.create_table(
        'traffic_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),  # organic, direct, social, referral, ads
        sa.Column('source_name', sa.String(), nullable=True),  # google, facebook, instagram, etc.
        sa.Column('referrer_url', sa.String(), nullable=True),
        sa.Column('utm_source', sa.String(), nullable=True),
        sa.Column('utm_medium', sa.String(), nullable=True),
        sa.Column('utm_campaign', sa.String(), nullable=True),
        sa.Column('visit_count', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_traffic_sources_id'), 'traffic_sources', ['id'], unique=False)
    
    # 9. Create keywords table
    op.create_table(
        'keywords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('keyword', sa.String(), nullable=False),
        sa.Column('search_engine', sa.String(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True, default=1),
        sa.Column('last_seen', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keywords_id'), 'keywords', ['id'], unique=False)
    
    # 10. Create exit_links table
    op.create_table(
        'exit_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('from_page', sa.String(), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=True, default=1),
        sa.Column('last_clicked', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exit_links_id'), 'exit_links', ['id'], unique=False)
    
    # 11. Create exit_link_clicks table
    op.create_table(
        'exit_link_clicks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('visitor_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('from_page', sa.String(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exit_link_clicks_id'), 'exit_link_clicks', ['id'], unique=False)
    op.create_index(op.f('ix_exit_link_clicks_visitor_id'), 'exit_link_clicks', ['visitor_id'], unique=False)
    op.create_index(op.f('ix_exit_link_clicks_session_id'), 'exit_link_clicks', ['session_id'], unique=False)
    op.create_index(op.f('ix_exit_link_clicks_clicked_at'), 'exit_link_clicks', ['clicked_at'], unique=False)
    
    # 12. Create cart_actions table
    op.create_table(
        'cart_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('visit_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),  # 'add_to_cart' or 'remove_from_cart'
        sa.Column('product_id', sa.String(), nullable=True),
        sa.Column('product_name', sa.String(), nullable=True),
        sa.Column('product_url', sa.String(), nullable=True),
        sa.Column('page_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['visit_id'], ['visits.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cart_actions_id'), 'cart_actions', ['id'], unique=False)
    op.create_index(op.f('ix_cart_actions_created_at'), 'cart_actions', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop tables in reverse order (to handle foreign key constraints)
    op.drop_index(op.f('ix_cart_actions_created_at'), table_name='cart_actions')
    op.drop_index(op.f('ix_cart_actions_id'), table_name='cart_actions')
    op.drop_table('cart_actions')
    
    op.drop_index(op.f('ix_exit_link_clicks_clicked_at'), table_name='exit_link_clicks')
    op.drop_index(op.f('ix_exit_link_clicks_session_id'), table_name='exit_link_clicks')
    op.drop_index(op.f('ix_exit_link_clicks_visitor_id'), table_name='exit_link_clicks')
    op.drop_index(op.f('ix_exit_link_clicks_id'), table_name='exit_link_clicks')
    op.drop_table('exit_link_clicks')
    
    op.drop_index(op.f('ix_exit_links_id'), table_name='exit_links')
    op.drop_table('exit_links')
    
    op.drop_index(op.f('ix_keywords_id'), table_name='keywords')
    op.drop_table('keywords')
    
    op.drop_index(op.f('ix_traffic_sources_id'), table_name='traffic_sources')
    op.drop_table('traffic_sources')
    
    op.drop_index(op.f('ix_page_views_viewed_at'), table_name='page_views')
    op.drop_index(op.f('ix_page_views_id'), table_name='page_views')
    op.drop_table('page_views')
    
    op.drop_index(op.f('ix_pages_id'), table_name='pages')
    op.drop_table('pages')
    
    op.drop_index(op.f('ix_visits_visited_at'), table_name='visits')
    op.drop_index(op.f('ix_visits_session_id'), table_name='visits')
    op.drop_index(op.f('ix_visits_visitor_id'), table_name='visits')
    op.drop_index(op.f('ix_visits_id'), table_name='visits')
    op.drop_table('visits')
    
    op.drop_index(op.f('ix_projects_tracking_code'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    
    op.drop_index(op.f('ix_email_verifications_token'), table_name='email_verifications')
    op.drop_index(op.f('ix_email_verifications_id'), table_name='email_verifications')
    op.drop_table('email_verifications')
    
    op.drop_index(op.f('ix_password_resets_token'), table_name='password_resets')
    op.drop_index(op.f('ix_password_resets_id'), table_name='password_resets')
    op.drop_table('password_resets')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
