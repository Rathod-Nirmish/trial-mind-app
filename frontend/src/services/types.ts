// ── Chat / streaming (existing) ────────────────────────────────────────────
export type TraceEvent = {
  agent: string;
  at: string;
  summary: string;
  payload: Record<string, unknown>;
};

export type Citation = {
  chunk_id: string;
  trial_id: string;
  section: string | null;
  text: string;
  score: number;
};

export type FinalAnswer = {
  answer: string;
  citations: Citation[];
  check_ok: boolean;
  issues: string[];
};

// ── Corpus ─────────────────────────────────────────────────────────────────
export type CorpusStats = {
  trials: number;
  chunks: number;
  by_phase: Record<'I' | 'II' | 'III' | 'IV', number>;
};

export type Trial = {
  nct_id: string;
  title: string;
  phase: 'I' | 'II' | 'III' | 'IV' | '—';
  status: 'Completed' | 'Recruiting' | 'Terminated' | 'Withdrawn' | 'Active';
  condition: string;
  source: 'nct' | 'pdf';
  chunks: number;
  ingested_at: string; // ISO
};

export type IngestionJob = {
  id: string;
  kind: 'nct' | 'pdf';
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  events: TraceEvent[];
  created_at: string;
  finished_at?: string;
};

// ── Explorations ───────────────────────────────────────────────────────────
export type ExplorationScore = {
  entail: number;
  retrieve: number;
  latency_s: number;
  iterations: number;
};

export type Exploration = {
  id: string;
  short_id: string; // EXP-0042
  title: string;
  question: string;
  answer_preview: string;
  answer?: string; // full — populated in detail
  citations: Citation[];
  trace?: TraceEvent[];
  scores: ExplorationScore;
  cite_count: number;
  trial_count: number;
  verified: boolean;
  pinned: boolean;
  created_at: string;
};

// ── Runs ───────────────────────────────────────────────────────────────────
export type EvalRun = {
  id: string;
  run_at: string;
  arm: 'with' | 'without' | 'both';
  pass: number;
  total: number;
  halluc_pct: number;
  entail: number;
  retrieve: number;
  p50_ms: number;
  p95_ms: number;
};

export type EvalAggregate = {
  halluc_pct: number;
  delta_pct: number; // vs no-checker
  entail: number;
  retrieve: number;
  pass: number;
  total: number;
  avg_latency_s: number;
  history: { at: string; halluc_pct: number }[];
};

export type AgentRunSummary = {
  id: string;
  short_id: string; // RUN 0148
  started_at: string;
  question: string;
  source: 'chat' | 'workbench' | 'eval';
  status: 'verified' | 'refined' | 'failed';
  iterations: number;
  cite_pass: string; // e.g. "3/3"
  chunk_count: number;
  latency_s: number;
  trials: string[];
  steps: AgentStep[];
};

export type AgentStep = {
  name: 'retriever' | 'analyzer' | 'citation-checker';
  status: 'ok' | 'warn' | 'fail' | 'retry';
  time_s: number;
  summary: string;
  why?: string;
};

// ── Workbench ──────────────────────────────────────────────────────────────
export type WorkbenchChunk = {
  short_id: string; // c1
  chunk_id: string;
  trial_id: string;
  section: string;
  score_hybrid: number;
  score_bm25: number;
  score_vector: number;
  snippet: string;
  full_text: string;
  tokens: number;
};

export type WorkbenchSpec = {
  question: string;
  filters: { phase: string[]; section: string[] };
  ranker: 'hybrid' | 'bm25' | 'vector';
  k: number;
  iterations: number;
};
