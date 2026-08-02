CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trial_id TEXT NOT NULL,
    section TEXT,
    text TEXT NOT NULL,
    embedding VECTOR(768),
    tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ivfflat index deliberately omitted: sequential scan is faster and correct
-- for corpora under ~10k rows. Add ivfflat back with `lists = sqrt(rows)` once
-- the corpus is large enough to benefit from ANN.
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN (tsv);
CREATE INDEX IF NOT EXISTS chunks_trial_idx ON chunks (trial_id);
