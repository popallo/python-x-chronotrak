"""merge heads

Revision ID: 59221afbf126
Revises: add_pinned_tasks, ce5f817a275a
Create Date: 2025-05-26 14:24:29.169714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59221afbf126'
down_revision = ('add_pinned_tasks', 'ce5f817a275a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
