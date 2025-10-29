"""add stripe ids to plan/subscription/driver

Revision ID: acfcbf97cd86
Revises: 9c76e7ef5a1b
Create Date: 2025-10-28 20:57:02.917191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acfcbf97cd86'
down_revision: Union[str, Sequence[str], None] = '9c76e7ef5a1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("plans", sa.Column("stripe_price_id", sa.String(length=64), nullable=True))
    op.create_index("ix_plans_stripe_price_id", "plans", ["stripe_price_id"])

    op.add_column("subscriptions", sa.Column("stripe_subscription_id", sa.String(length=64), nullable=True))
    op.create_index("ix_subs_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])

    op.add_column("drivers", sa.Column("stripe_customer_id", sa.String(length=64), nullable=True))
    op.create_index("ix_drivers_stripe_customer_id", "drivers", ["stripe_customer_id"])

def downgrade():
    op.drop_index("ix_drivers_stripe_customer_id", table_name="drivers")
    op.drop_column("drivers", "stripe_customer_id")

    op.drop_index("ix_subs_stripe_subscription_id", table_name="subscriptions")
    op.drop_column("subscriptions", "stripe_subscription_id")

    op.drop_index("ix_plans_stripe_price_id", table_name="plans")
    op.drop_column("plans", "stripe_price_id")