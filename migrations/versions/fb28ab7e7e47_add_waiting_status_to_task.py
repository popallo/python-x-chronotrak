"""add_waiting_status_to_task

Revision ID: fb28ab7e7e47
Revises: c81b6c3e4d10
Create Date: 2026-10-22 21:25:48.012953

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fb28ab7e7e47"
down_revision = "c81b6c3e4d10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(sa.Column("waiting_status", sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_column("waiting_status")
