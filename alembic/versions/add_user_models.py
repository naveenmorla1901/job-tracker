"""Add user authentication models

Revision ID: b982f4a72ef3
Revises: 
Create Date: 2025-03-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import enum

# Define UserRole enum for the migration
class UserRole(enum.Enum):
    REGULAR = "regular"
    PREMIUM = "premium"
    ADMIN = "admin"

# revision identifiers, used by Alembic
revision = 'b982f4a72ef3'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create enum type for UserRole
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum(UserRole), nullable=False, server_default='REGULAR'),
        sa.Column('registration_date', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Create UserJob junction table
    op.create_table(
        'user_jobs',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('is_applied', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('date_saved', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('date_updated', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'job_id'),
        sa.UniqueConstraint('user_id', 'job_id', name='uix_user_job')
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('user_jobs')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Try to drop the enum type
    op.execute('DROP TYPE IF EXISTS userrole;')
