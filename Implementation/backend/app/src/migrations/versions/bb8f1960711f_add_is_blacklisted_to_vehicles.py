"""add is_blacklisted to vehicles

Revision ID: bb8f1960711f
Revises: bd17c7495a72
Create Date: 2025-10-07 09:44:25.860999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb8f1960711f'
down_revision: Union[str, Sequence[str], None] = 'bd17c7495a72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():

    op.add_column(
        'vehicles',
        sa.Column('is_blacklisted', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
   
    op.alter_column('vehicles', 'is_blacklisted', server_default=None)

def downgrade():
    op.drop_column('vehicles', 'is_blacklisted')
