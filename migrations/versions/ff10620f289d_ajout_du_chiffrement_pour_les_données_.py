"""Ajout du chiffrement pour les données clients

Revision ID: ff10620f289d
Revises: cef9865047a2
Create Date: 2025-04-22 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff10620f289d"
down_revision = "cef9865047a2"
branch_labels = None
depends_on = None


def upgrade():
    # Pour SQLite, nous devons utiliser batch_alter_table car
    # SQLite ne supporte pas ALTER COLUMN directement
    with op.batch_alter_table("client") as batch_op:
        # email: augmenter de 120 caractères à 500
        batch_op.alter_column(
            "email", existing_type=sa.String(length=120), type_=sa.String(length=500), existing_nullable=True
        )

        # phone: augmenter de 20 caractères à 500
        batch_op.alter_column(
            "phone", existing_type=sa.String(length=20), type_=sa.String(length=500), existing_nullable=True
        )

        # address: augmenter de 200 caractères à 500
        batch_op.alter_column(
            "address", existing_type=sa.String(length=200), type_=sa.String(length=500), existing_nullable=True
        )

        # notes: déjà de type Text, qui devrait être suffisant pour les données chiffrées


def downgrade():
    # Pour SQLite, nous devons utiliser batch_alter_table
    with op.batch_alter_table("client") as batch_op:
        # Réduire la taille des colonnes (attention: peut causer des pertes de données)
        batch_op.alter_column(
            "email", existing_type=sa.String(length=500), type_=sa.String(length=120), existing_nullable=True
        )

        batch_op.alter_column(
            "phone", existing_type=sa.String(length=500), type_=sa.String(length=20), existing_nullable=True
        )

        batch_op.alter_column(
            "address", existing_type=sa.String(length=500), type_=sa.String(length=200), existing_nullable=True
        )
