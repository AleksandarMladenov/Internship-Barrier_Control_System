"""RBAC: admin_role enum + is_active + timestamps

Revision ID: d9658808c4e4
Revises: c715fd30adc0
Create Date: 2025-10-27 09:34:10.365350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9658808c4e4'
down_revision: Union[str, Sequence[str], None] = 'c715fd30adc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # 1) Create the enum type first (idempotent)
    admin_role = sa.Enum('owner', 'admin', 'viewer', name='admin_role')
    admin_role.create(bind, checkfirst=True)

    # 2) Add columns
    op.add_column(
        'admins',
        sa.Column('role', admin_role, nullable=False, server_default='viewer')
    )
    op.add_column('admins', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('admins', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('admins', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('admins', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))

    # 3) Index
    op.create_index(op.f('ix_admins_role'), 'admins', ['role'], unique=False)

    # 4) Drop server defaults
    op.alter_column('admins', 'role', server_default=None)
    op.alter_column('admins', 'is_active', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    admin_role = sa.Enum('owner', 'admin', 'viewer', name='admin_role')

    op.drop_index(op.f('ix_admins_role'), table_name='admins')
    op.drop_column('admins', 'last_login_at')
    op.drop_column('admins', 'updated_at')
    op.drop_column('admins', 'created_at')
    op.drop_column('admins', 'is_active')
    op.drop_column('admins', 'role')

    # drop enum type last
    admin_role.drop(bind, checkfirst=True)
