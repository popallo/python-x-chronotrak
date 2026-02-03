"""add user pinned task table

Revision ID: add_user_pinned_task
Revises: 59221afbf126
Create Date: 2024-05-26 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_user_pinned_task"
down_revision = "59221afbf126"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_pinned_task",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("task.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("user_pinned_task")
