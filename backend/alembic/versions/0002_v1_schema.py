"""v1 schema: trials, ingest_jobs, agent_runs, explorations,
exploration_messages, eval_runs, eval_results, usage

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-07

Adds all v1 product tables. Backfills `trials` from distinct
`chunks.trial_id` values so existing corpora survive with source='legacy'.
"""
from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── trials ────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE trials (
            nct_id        TEXT PRIMARY KEY,
            title         TEXT NOT NULL,
            phase         TEXT CHECK (phase IN ('I','II','III','IV') OR phase IS NULL),
            status        TEXT,
            condition     TEXT,
            source        TEXT NOT NULL DEFAULT 'nct'
                          CHECK (source IN ('nct','pdf','manual','legacy')),
            content_hash  TEXT NOT NULL,
            version       INT  NOT NULL DEFAULT 1,
            raw           JSONB NOT NULL DEFAULT '{}'::jsonb,
            ingested_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX trials_ingested_idx ON trials (ingested_at DESC)")
    op.execute("CREATE INDEX trials_phase_idx    ON trials (phase)")
    op.execute("CREATE INDEX trials_status_idx   ON trials (status)")
    op.execute("""
        CREATE INDEX trials_search_idx ON trials USING GIN (
            (setweight(to_tsvector('english', coalesce(title,'')),     'A') ||
             setweight(to_tsvector('english', coalesce(condition,'')), 'B') ||
             setweight(to_tsvector('english', nct_id),                 'C'))
        )
    """)

    # Backfill from existing chunks so /corpus/trials isn't empty on day one.
    op.execute("""
        INSERT INTO trials (nct_id, title, source, content_hash, ingested_at)
        SELECT
            trial_id,
            trial_id,
            'legacy',
            'legacy-' || trial_id,
            COALESCE(MIN(created_at), NOW())
        FROM chunks
        GROUP BY trial_id
        ON CONFLICT (nct_id) DO NOTHING
    """)

    # ── ingest_jobs ───────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE ingest_jobs (
            id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id      TEXT NOT NULL DEFAULT 'local',
            kind         TEXT NOT NULL CHECK (kind IN ('nct','pdf')),
            nct_ids      TEXT[] NOT NULL,
            status       TEXT NOT NULL CHECK (status IN ('running','succeeded','failed')),
            events       JSONB NOT NULL DEFAULT '[]'::jsonb,
            error        TEXT,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at  TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX ingest_jobs_created_idx ON ingest_jobs (created_at DESC)")
    op.execute("CREATE INDEX ingest_jobs_user_idx    ON ingest_jobs (user_id, created_at DESC)")

    # ── agent_runs ────────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE agent_runs_short_seq START 1")
    op.execute("""
        CREATE TABLE agent_runs (
            id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id       TEXT NOT NULL DEFAULT 'local',
            short_id      TEXT NOT NULL UNIQUE,
            source        TEXT NOT NULL CHECK (source IN ('chat','workbench','eval')),
            question      TEXT NOT NULL,
            status        TEXT NOT NULL CHECK (status IN ('verified','refined','failed')),
            iterations    INT  NOT NULL DEFAULT 0,
            cite_pass     TEXT NOT NULL DEFAULT '0/0',
            chunk_count   INT  NOT NULL DEFAULT 0,
            latency_ms    INT  NOT NULL,
            trials        TEXT[] NOT NULL DEFAULT '{}',
            steps         JSONB NOT NULL DEFAULT '[]'::jsonb,
            answer        TEXT,
            citations     JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX agent_runs_created_idx ON agent_runs (created_at DESC)")
    op.execute("CREATE INDEX agent_runs_user_idx    ON agent_runs (user_id, created_at DESC)")
    op.execute("CREATE INDEX agent_runs_source_idx  ON agent_runs (source)")

    # ── explorations + messages ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE explorations_short_seq START 1")
    op.execute("""
        CREATE TABLE explorations (
            id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id      TEXT NOT NULL DEFAULT 'local',
            short_id     TEXT NOT NULL UNIQUE,
            title        TEXT NOT NULL,
            pinned       BOOLEAN NOT NULL DEFAULT FALSE,
            verified     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX explorations_updated_idx ON explorations (updated_at DESC)")
    op.execute("CREATE INDEX explorations_user_idx    ON explorations (user_id, updated_at DESC)")
    op.execute("CREATE INDEX explorations_pinned_idx  ON explorations (pinned) WHERE pinned = TRUE")

    op.execute("""
        CREATE TABLE exploration_messages (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            exploration_id  UUID NOT NULL REFERENCES explorations(id) ON DELETE CASCADE,
            agent_run_id    UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
            role            TEXT NOT NULL CHECK (role IN ('user','assistant')),
            content         TEXT NOT NULL,
            citations       JSONB NOT NULL DEFAULT '[]'::jsonb,
            seq             INT  NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (exploration_id, seq)
        )
    """)
    op.execute("CREATE INDEX expl_messages_expl_idx ON exploration_messages (exploration_id, seq)")

    # ── eval_runs + eval_results ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE eval_runs (
            id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at  TIMESTAMPTZ,
            arm          TEXT NOT NULL CHECK (arm IN ('with','without','both')),
            status       TEXT NOT NULL CHECK (status IN ('running','succeeded','failed')),
            config       JSONB NOT NULL DEFAULT '{}'::jsonb,
            aggregate    JSONB NOT NULL DEFAULT '{}'::jsonb
        )
    """)
    op.execute("CREATE INDEX eval_runs_started_idx ON eval_runs (started_at DESC)")

    op.execute("""
        CREATE TABLE eval_results (
            id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            run_id       UUID NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
            question_id  TEXT NOT NULL,
            arm          TEXT NOT NULL CHECK (arm IN ('with','without')),
            passed       BOOLEAN NOT NULL,
            latency_ms   INT NOT NULL,
            answer       TEXT,
            citations    JSONB NOT NULL DEFAULT '[]'::jsonb,
            agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL
        )
    """)
    op.execute("CREATE INDEX eval_results_run_idx ON eval_results (run_id)")

    # ── usage ─────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE usage (
            id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id      TEXT NOT NULL DEFAULT 'local',
            day          DATE NOT NULL DEFAULT CURRENT_DATE,
            tokens_in    BIGINT NOT NULL DEFAULT 0,
            tokens_out   BIGINT NOT NULL DEFAULT 0,
            cost_cents   INT NOT NULL DEFAULT 0,
            UNIQUE (user_id, day)
        )
    """)
    op.execute("CREATE INDEX usage_day_idx ON usage (day DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS usage")
    op.execute("DROP TABLE IF EXISTS eval_results")
    op.execute("DROP TABLE IF EXISTS eval_runs")
    op.execute("DROP TABLE IF EXISTS exploration_messages")
    op.execute("DROP TABLE IF EXISTS explorations")
    op.execute("DROP SEQUENCE IF EXISTS explorations_short_seq")
    op.execute("DROP TABLE IF EXISTS agent_runs")
    op.execute("DROP SEQUENCE IF EXISTS agent_runs_short_seq")
    op.execute("DROP TABLE IF EXISTS ingest_jobs")
    op.execute("DROP TABLE IF EXISTS trials")
