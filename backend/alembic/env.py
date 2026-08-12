"""Alembic environment. Reads DATABASE_URL from app settings; no metadata autogen
for v1 — migrations are hand-written SQL. Add SQLAlchemy models later if the ORM
surface grows large enough to warrant autogen.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from trialmind.config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def _sqlalchemy_url() -> str:
    """Normalize DATABASE_URL to use the psycopg (v3) driver.
    The app uses psycopg3 directly; SQLAlchemy defaults to psycopg2 for
    `postgresql://` URLs, which we don't install.
    """
    url = get_settings().database_url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


config.set_main_option("sqlalchemy.url", _sqlalchemy_url())

target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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
