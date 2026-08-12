"""baseline: chunks + extensions (matches pre-alembic init_db.sql)

Revision ID: 0001
Revises:
Create Date: 2026-08-07

Idempotent so it can be stamped over an existing DB that already has the
chunks table from the hand-run init_db.sql. Use `alembic stamp 0001` on
existing deployments, then run `alembic upgrade head` for 0002+.
"""
from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            trial_id TEXT NOT NULL,
            section TEXT,
            text TEXT NOT NULL,
            embedding VECTOR(768),
            tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN (tsv)")
    op.execute("CREATE INDEX IF NOT EXISTS chunks_trial_idx ON chunks (trial_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chunks")
