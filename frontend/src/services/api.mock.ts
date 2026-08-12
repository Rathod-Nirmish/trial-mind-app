/* Mock API — no network. Simulates the real backend shape so screens can
 * be built and demoed without the Python service running. Toggle with
 * VITE_USE_MOCK_API=true in frontend/.env (see .env.example). */
import type {
  FinalAnswer, TraceEvent, Citation,
  CorpusStats, Trial, IngestionJob,
  Exploration, EvalRun, EvalAggregate, AgentRunSummary,
  WorkbenchChunk, WorkbenchSpec,
} from './types';

// ── helpers ────────────────────────────────────────────────────────────────
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const jitter = (base: number, spread = 0.3) =>
  Math.round(base * (1 + (Math.random() - 0.5) * 2 * spread));
const now = () => new Date().toISOString();
const daysAgo = (d: number) => new Date(Date.now() - d * 86400_000).toISOString();
const hoursAgo = (h: number) => new Date(Date.now() - h * 3600_000).toISOString();

// ── canned corpus (5 trials matching golden_qa.yaml intent) ────────────────
const TRIALS: Trial[] = [
  { nct_id: 'NCT04368728', title: 'BNT162b2 mRNA COVID-19 vaccine in adults',           phase: 'III', status: 'Completed',  condition: 'COVID-19',                source: 'nct', chunks: 412, ingested_at: daysAgo(3)  },
  { nct_id: 'NCT02015429', title: 'Semaglutide efficacy in type 2 diabetes',            phase: 'III', status: 'Completed',  condition: 'Type 2 Diabetes',         source: 'nct', chunks: 388, ingested_at: daysAgo(5)  },
  { nct_id: 'NCT04280705', title: 'Remdesivir for hospitalized COVID-19 patients',      phase: 'III', status: 'Completed',  condition: 'COVID-19',                source: 'nct', chunks: 296, ingested_at: daysAgo(4)  },
  { nct_id: 'NCT04381936', title: 'Dexamethasone in hospitalized COVID-19 (RECOVERY)',  phase: 'IV',  status: 'Completed',  condition: 'COVID-19',                source: 'nct', chunks: 231, ingested_at: daysAgo(6)  },
  { nct_id: 'NCT03485885', title: 'GLP-1 receptor agonist pharmacokinetics',            phase: 'I',   status: 'Completed',  condition: 'Type 2 Diabetes',         source: 'nct', chunks: 128, ingested_at: daysAgo(9)  },
  { nct_id: 'NCT05012345', title: 'CAR-T therapy in relapsed lymphoma',                 phase: 'II',  status: 'Recruiting', condition: 'Non-Hodgkin Lymphoma',    source: 'nct', chunks: 176, ingested_at: daysAgo(2)  },
  { nct_id: 'NCT02233445', title: 'Adherence patterns in adolescent obesity',           phase: 'II',  status: 'Recruiting', condition: 'Adolescent Obesity',      source: 'nct', chunks: 158, ingested_at: daysAgo(11) },
  { nct_id: 'NCT03344556', title: 'Statin-associated muscle symptoms in older adults',  phase: 'III', status: 'Completed',  condition: 'Cardiovascular Disease',  source: 'nct', chunks: 342, ingested_at: daysAgo(14) },
];

const MOCK_CITATIONS: Citation[] = [
  { chunk_id: 'ck-1', trial_id: 'NCT04368728', section: 'Results',     score: 0.914, text: 'The BNT162b2 vaccine demonstrated 95% efficacy against symptomatic COVID-19 in participants without prior infection (95% CI, 90.3 to 97.6).' },
  { chunk_id: 'ck-2', trial_id: 'NCT04368728', section: 'Methods',     score: 0.871, text: 'Participants aged 16 years or older were randomly assigned in a 1:1 ratio to receive two doses of BNT162b2 or placebo, 21 days apart.' },
  { chunk_id: 'ck-3', trial_id: 'NCT02015429', section: 'Results',     score: 0.842, text: 'Semaglutide 1.0 mg produced a mean HbA1c reduction of 1.6 percentage points versus 0.4 for placebo at week 30 (p<0.0001).' },
  { chunk_id: 'ck-4', trial_id: 'NCT04280705', section: 'Adverse',     score: 0.792, text: 'Remdesivir was associated with a shorter median recovery time (10 vs. 15 days) with no significant increase in serious adverse events.' },
];

// ── canned explorations ────────────────────────────────────────────────────
const EXPLORATIONS: Exploration[] = Array.from({ length: 14 }, (_, i) => {
  const idx = 42 - i;
  const templates = [
    { q: 'What were the eligibility criteria for the BNT162b2 vaccine trial?',            trials: 1 },
    { q: 'Compare primary endpoints across mRNA vaccine trials.',                          trials: 3 },
    { q: 'What adverse events were reported in the remdesivir trials?',                    trials: 2 },
    { q: 'Which trials studied dexamethasone for COVID-19?',                               trials: 1 },
    { q: 'Efficacy of GLP-1 receptor agonists in adolescent obesity.',                     trials: 3 },
    { q: 'Which trials were placebo-controlled and what were the primary endpoints?',      trials: 5 },
    { q: 'Grade 3 or higher adverse events across the corpus.',                            trials: 4 },
  ];
  const t = templates[i % templates.length];
  return {
    id: `exp-${idx}`,
    short_id: `EXP-${String(idx).padStart(4, '0')}`,
    title: t.q.replace(/\?$/, ''),
    question: t.q,
    answer_preview: 'Across the trials in the corpus, the primary endpoint was met with statistically significant improvement over placebo. Adverse events were consistent with prior safety data…',
    citations: MOCK_CITATIONS.slice(0, 2 + (i % 3)),
    scores: {
      entail: 0.85 + (Math.random() * 0.13),
      retrieve: 0.78 + (Math.random() * 0.15),
      latency_s: 2.6 + Math.random() * 5,
      iterations: i % 3 === 0 ? 1 : 0,
    },
    cite_count: 2 + (i % 3),
    trial_count: t.trials,
    verified: i % 5 !== 4,
    pinned: i < 3,
    created_at: hoursAgo(i * 6 + 1),
  };
});

// ── canned agent runs ──────────────────────────────────────────────────────
const RUNS: AgentRunSummary[] = [
  {
    id: 'run-148', short_id: 'RUN 0148', started_at: hoursAgo(2),
    question: 'What were the eligibility criteria in NCT04368728, and how do they compare with NCT02015429?',
    source: 'chat', status: 'verified', iterations: 0, cite_pass: '3/3',
    chunk_count: 8, latency_s: 3.1, trials: ['NCT04368728', 'NCT02015429'],
    steps: [
      { name: 'retriever',        status: 'ok', time_s: 0.42, summary: 'Hybrid search · 8 chunks · top score 0.91' },
      { name: 'analyzer',         status: 'ok', time_s: 1.8,  summary: 'Drafted 214 words · 3 inline citations' },
      { name: 'citation-checker', status: 'ok', time_s: 0.9,  summary: '3/3 citations entailed · 0 issues' },
    ],
  },
  {
    id: 'run-147', short_id: 'RUN 0147', started_at: hoursAgo(6),
    question: 'Which trials reported grade 3 or higher adverse events, and at what rates?',
    source: 'chat', status: 'refined', iterations: 1, cite_pass: '4/4',
    chunk_count: 12, latency_s: 7.4, trials: ['NCT04368728', 'NCT04280705', 'NCT02233445', 'NCT03344556'],
    steps: [
      { name: 'retriever',        status: 'ok',    time_s: 2.6, summary: 'Hybrid × 2 (broadened on retry) · 12 chunks' },
      { name: 'analyzer',         status: 'ok',    time_s: 2.2, summary: 'Drafted 186 words · 4 inline citations' },
      { name: 'citation-checker', status: 'retry', time_s: 2.6, summary: '4/4 entailed after retry · 1 refined', why: 'First pass flagged 1 unsupported claim; retrieval broadened and re-checked.' },
    ],
  },
  {
    id: 'run-146', short_id: 'RUN 0146', started_at: hoursAgo(8),
    question: 'Which trials in the corpus were placebo-controlled, and what were their primary endpoints?',
    source: 'chat', status: 'verified', iterations: 0, cite_pass: '5/5',
    chunk_count: 10, latency_s: 4.2, trials: ['NCT04368728', 'NCT04280705', 'NCT02015429', 'NCT04381936', 'NCT03344556'],
    steps: [
      { name: 'retriever',        status: 'ok', time_s: 0.5, summary: 'Hybrid · 10 chunks · top 0.88' },
      { name: 'analyzer',         status: 'ok', time_s: 2.6, summary: 'Drafted 240 words · 5 inline citations' },
      { name: 'citation-checker', status: 'ok', time_s: 1.1, summary: '5/5 entailed · 0 issues' },
    ],
  },
  {
    id: 'run-145', short_id: 'RUN 0145', started_at: hoursAgo(20),
    question: 'What was the median progression-free survival in the CAR-T lymphoma trial?',
    source: 'chat', status: 'failed', iterations: 2, cite_pass: '0/2',
    chunk_count: 2, latency_s: 6.8, trials: ['NCT05012345'],
    steps: [
      { name: 'retriever',        status: 'ok',   time_s: 0.6, summary: 'Hybrid · 2 chunks · top 0.42' },
      { name: 'analyzer',         status: 'warn', time_s: 3.2, summary: 'Low grounding · fallback prompt engaged', why: 'Only 2 chunks scored above threshold; escalated to checker.' },
      { name: 'citation-checker', status: 'fail', time_s: 3.0, summary: '0/2 entailed · answer withheld', why: 'Insufficient corpus evidence — answer withheld to prevent hallucination.' },
    ],
  },
];

// ── canned eval history ────────────────────────────────────────────────────
const EVAL_HISTORY = Array.from({ length: 12 }, (_, i) => ({
  at: daysAgo(11 - i),
  halluc_pct: i < 4 ? 3.2 + Math.random() * 2 : Math.max(0, 1 - i * 0.15) + Math.random() * 0.4,
}));

const EVAL_RUNS: EvalRun[] = EVAL_HISTORY.slice(-6).reverse().map((h, i) => ({
  id: `eval-${1000 + i}`,
  run_at: h.at,
  arm: i === 0 ? 'both' : 'with',
  pass: 10 - (h.halluc_pct > 1 ? 1 : 0),
  total: 10,
  halluc_pct: h.halluc_pct,
  entail: 0.9 + Math.random() * 0.06,
  retrieve: 0.85 + Math.random() * 0.08,
  p50_ms: 3800 + jitter(400),
  p95_ms: 8200 + jitter(1200),
}));

// ── mock chat SSE stream ───────────────────────────────────────────────────
type ChatHandler = (kind: 'trace' | 'final', data: TraceEvent | FinalAnswer) => void;

export async function askTrialMind(question: string, onEvent: ChatHandler): Promise<void> {
  const traceSteps: Omit<TraceEvent, 'at'>[] = [
    { agent: 'supervisor',       summary: `Received question · planning retrieval strategy`,                          payload: { question } },
    { agent: 'retriever',        summary: `Hybrid search (BM25 ⊕ vector) · 8 chunks · top score 0.91`,                 payload: { k: 8 } },
    { agent: 'analyzer',         summary: `Drafting answer from 8 chunks · target 200 words`,                          payload: {} },
    { agent: 'citation-checker', summary: `Verifying 3 citations against source chunks`,                              payload: {} },
    { agent: 'citation-checker', summary: `3/3 citations entailed · answer released`,                                 payload: { ok: true } },
  ];

  const delays = [180, 620, 1800, 900, 380];
  for (let i = 0; i < traceSteps.length; i++) {
    await sleep(delays[i]);
    onEvent('trace', { ...traceSteps[i], at: now() });
  }

  await sleep(220);

  const answer = mockAnswerFor(question);
  onEvent('final', {
    answer,
    citations: MOCK_CITATIONS,
    check_ok: true,
    issues: [],
  });
}

function mockAnswerFor(q: string): string {
  const low = q.toLowerCase();
  if (low.includes('eligibility') || low.includes('inclusion')) {
    return `The BNT162b2 trial [c2] enrolled healthy adults aged 16 years or older, randomly assigned 1:1 to two doses of vaccine or placebo 21 days apart. In contrast, the semaglutide trial [c3] enrolled adults with type 2 diabetes and inadequate glycemic control on metformin.\n\nBoth studies excluded pregnant participants and those with severe comorbidities that would compromise adherence.`;
  }
  if (low.includes('adverse') || low.includes('safety')) {
    return `Remdesivir [c4] was associated with a shorter median recovery time (10 vs. 15 days) compared to placebo, with no significant increase in serious adverse events across the trial population.\n\nMost commonly reported events were mild-to-moderate and resolved without intervention.`;
  }
  if (low.includes('efficacy') || low.includes('endpoint') || low.includes('primary')) {
    return `The BNT162b2 vaccine [c1] demonstrated 95% efficacy against symptomatic COVID-19 (95% CI, 90.3–97.6) in participants without prior SARS-CoV-2 infection.\n\nSeparately, semaglutide 1.0 mg [c3] produced a mean HbA1c reduction of **1.6 percentage points** versus 0.4 for placebo at week 30 (p<0.0001).`;
  }
  return `Based on the retrieved evidence, the primary endpoint was met with statistically significant improvement over placebo [c1] [c3]. The safety profile was consistent with prior data for this class of intervention [c4]. See citations for per-trial details.`;
}

// ── mock REST endpoints ────────────────────────────────────────────────────

export async function getCorpusStats(): Promise<CorpusStats> {
  await sleep(120);
  const by_phase = { I: 0, II: 0, III: 0, IV: 0 } as CorpusStats['by_phase'];
  TRIALS.forEach((t) => { if (t.phase !== '—') by_phase[t.phase]++; });
  return {
    trials: TRIALS.length,
    chunks: TRIALS.reduce((s, t) => s + t.chunks, 0),
    by_phase,
  };
}

export async function listTrials(_q = ''): Promise<{ items: Trial[]; total: number }> {
  await sleep(180);
  return { items: TRIALS, total: TRIALS.length };
}

export async function getTrial(nct: string): Promise<Trial> {
  await sleep(100);
  const t = TRIALS.find((x) => x.nct_id === nct);
  if (!t) throw new Error('not found');
  return t;
}

export async function startIngestNct(_nct_ids: string[]): Promise<{ job_id: string }> {
  await sleep(150);
  return { job_id: `job-${Date.now()}` };
}

export async function getIngestionJob(id: string): Promise<IngestionJob> {
  await sleep(80);
  return {
    id, kind: 'nct', status: 'succeeded',
    events: [
      { agent: 'fetcher',   at: now(), summary: 'Fetched 3 study records from ClinicalTrials.gov', payload: {} },
      { agent: 'chunker',   at: now(), summary: 'Produced 84 chunks (avg 412 tokens)',              payload: {} },
      { agent: 'embedder',  at: now(), summary: '84 vectors indexed via Gemini embedding',          payload: {} },
    ],
    created_at: now(), finished_at: now(),
  };
}

// Explorations
export async function listExplorations(_q = ''): Promise<{ items: Exploration[] }> {
  await sleep(160);
  return { items: EXPLORATIONS };
}
export async function getExploration(id: string): Promise<Exploration> {
  await sleep(120);
  const e = EXPLORATIONS.find((x) => x.id === id);
  if (!e) throw new Error('not found');
  return { ...e, answer: mockAnswerFor(e.question), trace: [] };
}
export async function saveExploration(body: Partial<Exploration>): Promise<Exploration> {
  await sleep(200);
  const created: Exploration = {
    id: `exp-new-${Date.now()}`,
    short_id: `EXP-${String(EXPLORATIONS.length + 43).padStart(4, '0')}`,
    title: body.title ?? 'Untitled',
    question: body.question ?? '',
    answer_preview: body.answer_preview ?? '',
    citations: [],
    scores: { entail: 0.9, retrieve: 0.85, latency_s: 3.4, iterations: 0 },
    cite_count: 0, trial_count: 0, verified: true, pinned: false,
    created_at: now(),
    ...body,
  } as Exploration;
  EXPLORATIONS.unshift(created);
  return created;
}
export async function patchExploration(id: string, body: Partial<Exploration>): Promise<Exploration> {
  await sleep(120);
  const e = EXPLORATIONS.find((x) => x.id === id);
  if (!e) throw new Error('not found');
  Object.assign(e, body);
  return e;
}
export async function deleteExploration(id: string): Promise<void> {
  await sleep(100);
  const i = EXPLORATIONS.findIndex((x) => x.id === id);
  if (i >= 0) EXPLORATIONS.splice(i, 1);
}

// Runs
export async function getEvalAggregate(): Promise<EvalAggregate> {
  await sleep(140);
  return {
    halluc_pct: 0.0,
    delta_pct: 100,
    entail: 0.94,
    retrieve: 0.87,
    pass: 10, total: 10,
    avg_latency_s: 4.2,
    history: EVAL_HISTORY,
  };
}
export async function listEvalRuns(): Promise<{ items: EvalRun[] }> {
  await sleep(140);
  return { items: EVAL_RUNS };
}
export async function listAgentRuns(_q = ''): Promise<{ items: AgentRunSummary[] }> {
  await sleep(160);
  return { items: RUNS };
}
export async function getAgentRun(id: string): Promise<AgentRunSummary> {
  await sleep(100);
  const r = RUNS.find((x) => x.id === id);
  if (!r) throw new Error('not found');
  return r;
}

// Workbench
export async function workbenchRetrieve(
  spec: WorkbenchSpec,
  onChunk: (c: WorkbenchChunk) => void
): Promise<void> {
  const trialPool = spec.filters.trial_id?.length
    ? TRIALS.filter((t) => spec.filters.trial_id.includes(t.nct_id))
    : TRIALS;
  const pool = trialPool.length ? trialPool : TRIALS;
  const chunks: WorkbenchChunk[] = Array.from({ length: Math.min(spec.k, 8) }, (_, i) => {
    const trial = pool[i % pool.length];
    return {
      short_id: `c${i + 1}`,
      chunk_id: `ck-${1000 + i}`,
      trial_id: trial.nct_id,
      section: ['Results', 'Methods', 'Adverse', 'Eligibility'][i % 4],
      score_hybrid: +(0.92 - i * 0.04).toFixed(3),
      score_bm25:   +(0.88 - i * 0.05 + Math.random() * 0.05).toFixed(3),
      score_vector: +(0.86 - i * 0.03 + Math.random() * 0.05).toFixed(3),
      snippet: `In the treatment arm, ${['adverse events', 'primary outcomes', 'eligibility criteria'][i % 3]} were consistent with prior evidence…`,
      full_text: `In the treatment arm of ${trial.nct_id}, ${trial.title.toLowerCase()} demonstrated ${['favorable efficacy', 'a manageable safety profile', 'clinically meaningful improvement'][i % 3]} over the comparator. Detailed results are reported in section ${['Results', 'Methods', 'Adverse'][i % 3]}.`,
      tokens: 340 + jitter(80),
    };
  });
  for (const c of chunks) {
    await sleep(120 + Math.random() * 80);
    onChunk(c);
  }
}
