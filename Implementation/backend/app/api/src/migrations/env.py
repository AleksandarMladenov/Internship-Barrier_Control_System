from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# --- App imports: load env + metadata ---
from src.core.settings import settings
from src.db.database import Base

# If you keep models in src/models, import them so Base.metadata is populated
# (adjust/remove if your models live elsewhere)
import src.models  # noqa: F401

# Alembic Config object (reads alembic.ini)
config = context.config

# Provide DB URL from app settings (env/.env), not hardcoded in alembic.ini
# Make sure in alembic.ini you leave: sqlalchemy.url =
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'alembic revision --autogenerate'
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
