"""add task recurrence series

Revision ID: c81b6c3e4d10
Revises: d8554cc957ca
Create Date: 2026-02-01
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c81b6c3e4d10"
down_revision = "d8554cc957ca"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    def has_table(name: str) -> bool:
        return name in insp.get_table_names()

    def has_column(table: str, column: str) -> bool:
        try:
            return any(c.get("name") == column for c in insp.get_columns(table))
        except Exception:
            return False

    # SQLite: batch_alter_table recrée la table, copie les données puis DROP l'ancienne table.
    # Si foreign_keys est ON et que d'autres tables référencent `task`, le DROP échoue.
    # On désactive temporairement la vérification (pattern recommandé pour SQLite).
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    try:
        # Si une tentative précédente a créé la table puis a échoué avant la fin,
        # on rend la migration relançable.
        if not has_table("task_recurrence_series"):
            op.create_table(
                "task_recurrence_series",
                sa.Column("id", sa.Integer(), primary_key=True),
                sa.Column("frequency", sa.String(length=20), nullable=False),
                sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
                sa.Column("start_date", sa.Date(), nullable=False),
                sa.Column("end_date", sa.Date(), nullable=True),
                sa.Column("count", sa.Integer(), nullable=True),
                sa.Column("byweekday", sa.String(length=30), nullable=True),
                sa.Column("business_days_only", sa.Boolean(), nullable=False, server_default=sa.text("0")),
                sa.Column("monthly_use_last_day", sa.Boolean(), nullable=False, server_default=sa.text("0")),
                sa.Column("monthly_day", sa.Integer(), nullable=True),
                sa.Column("created_at", sa.DateTime(), nullable=True),
                sa.Column("updated_at", sa.DateTime(), nullable=True),
                sa.Column("template_task_id", sa.Integer(), nullable=False),
                sa.ForeignKeyConstraint(["template_task_id"], ["task.id"], ondelete="CASCADE"),
                sa.UniqueConstraint("template_task_id", name="uq_task_recurrence_series_template_task_id"),
            )

        # Ne pas tenter de recréer la table task si les colonnes sont déjà là
        if not (has_column("task", "scheduled_for") and has_column("task", "recurrence_series_id")):
            with op.batch_alter_table("task", schema=None) as batch_op:
                if not has_column("task", "scheduled_for"):
                    batch_op.add_column(sa.Column("scheduled_for", sa.Date(), nullable=True))
                if not has_column("task", "recurrence_series_id"):
                    batch_op.add_column(sa.Column("recurrence_series_id", sa.Integer(), nullable=True))

                # Sur une DB "partiellement migrée", on peut tomber sur des contraintes/index déjà créés.
                # SQLite ne donne pas toujours une introspection fiable, donc on reste pragmatique.
                try:
                    batch_op.create_foreign_key(
                        "fk_task_recurrence_series_id",
                        "task_recurrence_series",
                        ["recurrence_series_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )
                except Exception:
                    pass

                try:
                    batch_op.create_unique_constraint(
                        "uq_task_recurrence_series_id_scheduled_for",
                        ["recurrence_series_id", "scheduled_for"],
                    )
                except Exception:
                    pass

                try:
                    batch_op.create_index("ix_task_scheduled_for", ["scheduled_for"])
                except Exception:
                    pass
                try:
                    batch_op.create_index("ix_task_recurrence_series_id", ["recurrence_series_id"])
                except Exception:
                    pass
    finally:
        conn.execute(sa.text("PRAGMA foreign_keys=ON"))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    try:
        with op.batch_alter_table("task", schema=None) as batch_op:
            try:
                batch_op.drop_index("ix_task_recurrence_series_id")
            except Exception:
                pass
            try:
                batch_op.drop_index("ix_task_scheduled_for")
            except Exception:
                pass
            try:
                batch_op.drop_constraint("uq_task_recurrence_series_id_scheduled_for", type_="unique")
            except Exception:
                pass
            try:
                batch_op.drop_constraint("fk_task_recurrence_series_id", type_="foreignkey")
            except Exception:
                pass
            try:
                batch_op.drop_column("recurrence_series_id")
            except Exception:
                pass
            try:
                batch_op.drop_column("scheduled_for")
            except Exception:
                pass

        try:
            op.drop_table("task_recurrence_series")
        except Exception:
            pass
    finally:
        conn.execute(sa.text("PRAGMA foreign_keys=ON"))
