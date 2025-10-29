"""Add year to BillingPeriod enum

Revision ID: 662d39c34da4
Revises: acfcbf97cd86
Create Date: 2025-10-29 12:37:05.538429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '662d39c34da4'
down_revision: Union[str, Sequence[str], None] = 'acfcbf97cd86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE billingperiod ADD VALUE IF NOT EXISTS 'year';")


def downgrade() -> None:
    """Downgrade schema."""
    pass
