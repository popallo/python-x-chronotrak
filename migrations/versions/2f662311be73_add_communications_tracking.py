"""Add communications tracking

Revision ID: 2f662311be73
Revises: 4719aa97706b
Create Date: 2025-05-05 16:57:30.094380

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2f662311be73"
down_revision = "4719aa97706b"
branch_labels = None
depends_on = None


def upgrade():
    # Utiliser des types SQLAlchemy standard au lieu de EncryptedType
    op.create_table(
        "communication",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient", sa.String(length=120), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=True),  # Utiliser Text au lieu de EncryptedType
        sa.Column("content_text", sa.Text(), nullable=True),  # Utiliser Text au lieu de EncryptedType
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("triggered_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.ForeignKeyConstraint(
            ["triggered_by_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ### end Alembic commands ###


def downgrade():
    op.drop_table("communication")
    # ### end Alembic commands ###
