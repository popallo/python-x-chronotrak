"""Add notification preferences

Revision ID: 1e508d20a8d9
Revises: 56597963674a
Create Date: 2025-04-23 00:01:33.265930

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e508d20a8d9'
down_revision = '56597963674a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('notification_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_status_change', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('task_comment_added', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('task_time_logged', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('project_credit_low', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_notifications_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Créer un index pour améliorer les performances
    op.create_index(op.f('ix_notification_preference_user_id'), 'notification_preference', ['user_id'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f('ix_notification_preference_user_id'), table_name='notification_preference')
    op.drop_table('notification_preference')

    # ### end Alembic commands ###
