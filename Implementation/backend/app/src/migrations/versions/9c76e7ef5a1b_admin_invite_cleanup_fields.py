"""admin invite + cleanup fields

Revision ID: 9c76e7ef5a1b
Revises: d9658808c4e4
Create Date: 2025-10-27 22:19:54.500045
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "9c76e7ef5a1b"
down_revision: Union[str, Sequence[str], None] = "d9658808c4e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(bind, table, column) -> bool:
    insp = Inspector.from_engine(bind)
    return column in [c["name"] for c in insp.get_columns(table)]


def _has_enum(bind, enum_name) -> bool:
    return bool(
        bind.execute(
            text("SELECT 1 FROM pg_type WHERE typname = :n"),
            {"n": enum_name},
        ).scalar()
    )


def upgrade():
    bind = op.get_bind()

    # 1) Ensure enum exists
    if not _has_enum(bind, "admin_status"):
        sa.Enum("invited", "active", "disabled", name="admin_status").create(bind)

    # 2) Alter admins table in batch
    with op.batch_alter_table("admins") as batch:
        # Drop legacy columns if present
        if _has_column(bind, "admins", "verified"):
            batch.drop_column("verified")
        if _has_column(bind, "admins", "is_accountant"):
            batch.drop_column("is_accountant")

        # Add new columns if missing
        if not _has_column(bind, "admins", "status"):
            batch.add_column(
                sa.Column(
                    "status",
                    sa.Enum(name="admin_status"),
                    nullable=False,
                    server_default="active",
                )
            )
        if not _has_column(bind, "admins", "invited_token"):
            batch.add_column(sa.Column("invited_token", sa.String(255), nullable=True, unique=True))
        if not _has_column(bind, "admins", "invited_expires_at"):
            batch.add_column(sa.Column("invited_expires_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column(bind, "admins", "invited_by_id"):
            batch.add_column(sa.Column("invited_by_id", sa.Integer(), nullable=True))

        # Create FK inside the same batch so the column exists in this context
        # Safe-guard with try: if FK already exists for some reason, ignore.
        try:
            batch.create_foreign_key(
                "fk_admins_invited_by_id_admins",
                referent_table="admins",
                local_cols=["invited_by_id"],
                remote_cols=["id"],
                ondelete="SET NULL",
            )
        except Exception:
            pass

    # 3) Index for invited_by_id (done outside batch)
    try:
        op.create_index("ix_admins_invited_by_id", "admins", ["invited_by_id"], unique=False)
    except Exception:
        pass

    # 4) Remove server_default from status for future inserts
    with op.batch_alter_table("admins") as batch:
        batch.alter_column("status", server_default=None)


def downgrade():
    bind = op.get_bind()

    # Drop FK & index first
    try:
        with op.batch_alter_table("admins") as batch:
            batch.drop_constraint("fk_admins_invited_by_id_admins", type_="foreignkey")
    except Exception:
        pass
    try:
        op.drop_index("ix_admins_invited_by_id", table_name="admins")
    except Exception:
        pass

    # Drop new columns, restore old ones
    with op.batch_alter_table("admins") as batch:
        if _has_column(bind, "admins", "invited_token"):
            batch.drop_column("invited_token")
        if _has_column(bind, "admins", "invited_expires_at"):
            batch.drop_column("invited_expires_at")
        if _has_column(bind, "admins", "invited_by_id"):
            batch.drop_column("invited_by_id")
        if _has_column(bind, "admins", "status"):
            batch.drop_column("status")

        # restore legacy columns (nullable to be safe)
        if not _has_column(bind, "admins", "verified"):
            batch.add_column(sa.Column("verified", sa.Boolean(), nullable=True))
        if not _has_column(bind, "admins", "is_accountant"):
            batch.add_column(sa.Column("is_accountant", sa.Boolean(), nullable=True))

    # Drop enum type if unused
    try:
        sa.Enum(name="admin_status").drop(bind, checkfirst=True)
    except Exception:
        pass
