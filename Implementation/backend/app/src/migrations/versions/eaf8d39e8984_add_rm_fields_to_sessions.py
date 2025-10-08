"""add RM fields to sessions

Revision ID: eaf8d39e8984
Revises: bb8f1960711f
Create Date: 2025-10-08 08:58:01.444978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaf8d39e8984'
down_revision: Union[str, Sequence[str], None] = 'bb8f1960711f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("sessions", sa.Column("plan_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sessions_plan_id_plans",
        "sessions", "plans",
        ["plan_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("sessions", sa.Column("status", sa.String(24), nullable=True))
    op.add_column("sessions", sa.Column("duration", sa.Integer(), nullable=True))
    op.add_column("sessions", sa.Column("amount_charged", sa.Integer(), nullable=True))

def downgrade():
    op.drop_column("sessions", "amount_charged")
    op.drop_column("sessions", "duration")
    op.drop_column("sessions", "status")
    op.drop_constraint("fk_sessions_plan_id_plans", "sessions", type_="foreignkey")
    op.drop_column("sessions", "plan_id")