/* Real HTTP client — talks to the FastAPI backend on VITE_API_BASE. */
import type {
  FinalAnswer, TraceEvent,
  CorpusStats, Trial, IngestionJob,
  Exploration, EvalRun, EvalAggregate, AgentRunSummary,
  WorkbenchChunk, WorkbenchSpec,
} from './types';

const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

type ChatHandler = (kind: 'trace' | 'final', data: TraceEvent | FinalAnswer) => void;

export async function askTrialMind(question: string, onEvent: ChatHandler): Promise<void> {
  const resp = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ question }),
  });
  if (!resp.body) throw new Error('no response body');

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const normalized = () => buffer.replace(/\r\n/g, '\n');
    let idx: number;
    while ((idx = normalized().indexOf('\n\n')) !== -1) {
      buffer = normalized();
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      let eventName = 'message';
      let dataLine = '';
      for (const line of raw.split('\n')) {
        if (line.startsWith(':')) continue;
        if (line.startsWith('event:')) eventName = line.slice(6).trim();
        else if (line.startsWith('data:')) dataLine += line.slice(5).trim();
      }
      if (!dataLine) continue;
      try {
        const parsed = JSON.parse(dataLine);
        if (eventName === 'trace') onEvent('trace', parsed as TraceEvent);
        else if (eventName === 'final') onEvent('final', parsed as FinalAnswer);
      } catch (e) {
        console.warn('[SSE] parse failed:', dataLine, e);
      }
    }
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public detail: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, init);
  if (!r.ok) {
    let code = 'HTTP_ERROR';
    let message = `${r.status} ${r.statusText}`;
    let detail: Record<string, unknown> = {};
    try {
      const body = await r.json();
      if (body?.error) {
        code = body.error.code ?? code;
        message = body.error.message ?? message;
        detail = body.error.detail ?? {};
      }
    } catch { /* non-JSON error body */ }
    throw new ApiError(r.status, code, message, detail);
  }
  return r.json() as Promise<T>;
}

// Corpus
export const getCorpusStats = () => j<CorpusStats>('/corpus/stats');
// Default limit intentionally high — Corpus.vue filters client-side over the full list.
// Callers that want server-side paging can pass `q` = 'limit=25&offset=0&q=foo'.
export const listTrials    = (q = 'limit=200') =>
  j<{ items: Trial[]; total: number; limit: number; offset: number }>(`/corpus/trials?${q}`);
export const getTrial      = (nct: string) => j<Trial>(`/corpus/trials/${nct}`);
export const startIngestNct = (nct_ids: string[]) =>
  j<{ job_id: string }>('/corpus/ingest/nct', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nct_ids }),
  });
export const getIngestionJob = (id: string) => j<IngestionJob>(`/corpus/ingest/${id}`);

// Explorations
export const listExplorations = (q = '') => j<{ items: Exploration[] }>(`/explorations?${q}`);
export const getExploration   = (id: string) => j<Exploration>(`/explorations/${id}`);
export const saveExploration  = (body: Partial<Exploration>) =>
  j<Exploration>('/explorations', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
export const patchExploration = (id: string, body: Partial<Exploration>) =>
  j<Exploration>(`/explorations/${id}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
export const deleteExploration = (id: string) =>
  fetch(`${BASE}/explorations/${id}`, { method: 'DELETE' }).then(() => undefined);

// Runs
export const getEvalAggregate = () => j<EvalAggregate>('/runs/evals/aggregate');
export const listEvalRuns     = () => j<{ items: EvalRun[] }>('/runs/evals');
export const listAgentRuns    = (q = '') => j<{ items: AgentRunSummary[] }>(`/runs/agents?${q}`);
export const getAgentRun      = (id: string) => j<AgentRunSummary>(`/runs/agents/${id}`);

// Workbench
export async function workbenchRetrieve(
  spec: WorkbenchSpec,
  onChunk: (c: WorkbenchChunk) => void
): Promise<void> {
  const resp = await fetch(`${BASE}/workbench/retrieve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(spec),
  });
  if (!resp.body) throw new Error('no response body');
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let eventName = 'message';
      let dataLine = '';
      for (const line of raw.split('\n')) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim();
        else if (line.startsWith('data:')) dataLine += line.slice(5).trim();
      }
      if (eventName === 'chunk' && dataLine) {
        try { onChunk(JSON.parse(dataLine) as WorkbenchChunk); } catch { /* noop */ }
      }
    }
  }
}
