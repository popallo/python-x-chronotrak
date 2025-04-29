"""Add password reset tokens

Revision ID: 427a382ef06b
Revises: 0857f07e6305
Create Date: 2025-04-29 10:27:08.419248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '427a382ef06b'
down_revision = '0857f07e6305'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('password_reset_token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Créer un index pour améliorer les performances des recherches par token
    op.create_index(op.f('ix_password_reset_token_token'), 'password_reset_token', ['token'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f('ix_password_reset_token_token'), table_name='password_reset_token')
    op.drop_table('password_reset_token')

    # ### end Alembic commands ###
