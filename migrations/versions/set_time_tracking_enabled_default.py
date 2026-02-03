"""Set time_tracking_enabled default value

Revision ID: set_time_tracking_enabled_default
Revises: d1a7cda8cd78
Create Date: 2024-03-19 20:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "set_time_tracking_enabled_default"
down_revision = "d1a7cda8cd78"
branch_labels = None
depends_on = None


def upgrade():
    # Mettre à jour tous les projets existants pour activer la gestion du temps
    op.execute("UPDATE project SET time_tracking_enabled = 1 WHERE time_tracking_enabled IS NULL")

    # Modifier la colonne pour qu'elle ne soit plus nullable et ait une valeur par défaut
    with op.batch_alter_table("project", schema=None) as batch_op:
        batch_op.alter_column(
            "time_tracking_enabled", existing_type=sa.Boolean(), nullable=False, server_default=sa.text("1")
        )


def downgrade():
    # Supprimer la valeur par défaut et rendre la colonne nullable
    with op.batch_alter_table("project", schema=None) as batch_op:
        batch_op.alter_column("time_tracking_enabled", existing_type=sa.Boolean(), nullable=True, server_default=None)
