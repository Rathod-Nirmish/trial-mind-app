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
