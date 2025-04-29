"""Add user last login

Revision ID: 4719aa97706b
Revises: 427a382ef06b
Create Date: 2025-04-29 10:50:13.188857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4719aa97706b'
down_revision = '427a382ef06b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    op.drop_column('user', 'last_login')

    # ### end Alembic commands ###
