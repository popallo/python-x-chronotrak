"""Ajout du chiffrement pour les commentaires

Revision ID: 56597963674a
Revises: ff10620f289d
Create Date: 2025-04-22 23:35:44.653023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56597963674a'
down_revision = 'ff10620f289d'
branch_labels = None
depends_on = None


def upgrade():
    # Pour SQLite, nous devons utiliser batch_alter_table
    with op.batch_alter_table('comment') as batch_op:
        # Modifier la colonne content pour accommoder les données chiffrées
        # qui sont généralement plus volumineuses que les données en clair
        batch_op.alter_column('content',
                             existing_type=sa.Text(),
                             type_=sa.String(length=1000),  # Augmenter la taille pour les données chiffrées
                             existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # Pour SQLite, nous devons utiliser batch_alter_table
    with op.batch_alter_table('comment') as batch_op:
        # Rétablir le type d'origine
        batch_op.alter_column('content',
                             existing_type=sa.String(length=1000),
                             type_=sa.Text(),
                             existing_nullable=False)

    # ### end Alembic commands ###
