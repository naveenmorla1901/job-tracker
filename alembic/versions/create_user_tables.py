"""create user tables

Revision ID: a5cd1fe3dac1
Revises: 
Create Date: 2025-03-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a5cd1fe3dac1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for user roles
    user_role = postgresql.ENUM('regular', 'premium', 'admin', name='userrole')
    user_role.create(op.get_bind())
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('regular', 'premium', 'admin', name='userrole'), nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create user_jobs junction table
    op.create_table(
        'user_jobs',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('is_applied', sa.Boolean(), nullable=False),
        sa.Column('date_saved', sa.DateTime(), nullable=False),
        sa.Column('date_updated', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'job_id'),
        sa.UniqueConstraint('user_id', 'job_id', name='uix_user_job')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('user_jobs')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enum type
    op.execute('DROP TYPE userrole')
