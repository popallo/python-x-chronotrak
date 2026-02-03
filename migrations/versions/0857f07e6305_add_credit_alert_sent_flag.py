"""Add credit alert sent flag

Revision ID: 0857f07e6305
Revises: 1e508d20a8d9
Create Date: 2025-04-23 00:16:52.066362

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0857f07e6305"
down_revision = "1e508d20a8d9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("project", sa.Column("credit_alert_sent", sa.Boolean(), nullable=False, server_default="0"))

    # ### end Alembic commands ###


def downgrade():
    op.drop_column("project", "credit_alert_sent")

    # ### end Alembic commands ###
