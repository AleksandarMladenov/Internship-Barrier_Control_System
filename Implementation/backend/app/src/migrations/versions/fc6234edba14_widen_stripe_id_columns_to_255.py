"""widen stripe id columns to 255

Revision ID: fc6234edba14
Revises: c8f0d4256966
Create Date: 2025-11-12 12:11:13.437868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc6234edba14'
down_revision: Union[str, Sequence[str], None] = 'c8f0d4256966'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.alter_column("payments", "stripe_checkout_id",
                    existing_type=sa.String(length=64),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column("payments", "stripe_payment_intent_id",
                    existing_type=sa.String(length=64),
                    type_=sa.String(length=255),
                    existing_nullable=True)

def downgrade():
    op.alter_column("payments", "stripe_checkout_id",
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=64),
                    existing_nullable=True)
    op.alter_column("payments", "stripe_payment_intent_id",
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=64),
                    existing_nullable=True)
