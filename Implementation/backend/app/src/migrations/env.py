from __future__ import annotations


import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Make sure Python can import the local 'src' package --------------------
# env.py file path: .../app/src/migrations/env.py
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# --- App imports: metadata + settings --------------------------------------
from src.models import Base  # Base is re-exported in src/models/__init__.py

import src.models
# Try to get the DB URL from app settings; fall back to alembic.ini if missing
DATABASE_URL: str | None = None
try:
    from src.core.settings import settings  # your Settings() instance
    DATABASE_URL = settings.DATABASE_URL
except Exception:
    DATABASE_URL = None

# Alembic Config object (reads alembic.ini)
config = context.config

# If we have a runtime DATABASE_URL, use it; otherwise stick with alembic.ini
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configure logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
