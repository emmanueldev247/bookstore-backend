"""Add DELIVERED to order_status_enum

Revision ID: 46fdf236d2ba
Revises: f0b085baaca7
Create Date: 2025-06-04 09:48:50.420517

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "46fdf236d2ba"
down_revision = "f0b085baaca7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE order_status_enum ADD VALUE 'DELIVERED'")


def downgrade():
    pass
