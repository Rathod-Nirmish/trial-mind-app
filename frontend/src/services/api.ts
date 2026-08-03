/* API router — picks mock vs real per VITE_USE_MOCK_API.
 * Both modules export the same function signatures (defined in types.ts). */
import * as real from './api.real';
import * as mock from './api.mock';

const USE_MOCK = (import.meta.env.VITE_USE_MOCK_API ?? 'false').toString().toLowerCase() === 'true';

if (import.meta.env.DEV) {
  console.info(`[api] using ${USE_MOCK ? 'MOCK' : 'REAL'} backend`);
}

const impl = USE_MOCK ? mock : real;

export const isMock = USE_MOCK;

// Chat
export const askTrialMind = impl.askTrialMind;

// Corpus
export const getCorpusStats  = impl.getCorpusStats;
export const listTrials      = impl.listTrials;
export const getTrial        = impl.getTrial;
export const startIngestNct  = impl.startIngestNct;
export const getIngestionJob = impl.getIngestionJob;

// Explorations
export const listExplorations = impl.listExplorations;
export const getExploration   = impl.getExploration;
export const saveExploration  = impl.saveExploration;
export const patchExploration = impl.patchExploration;
export const deleteExploration = impl.deleteExploration;

// Runs
export const getEvalAggregate = impl.getEvalAggregate;
export const listEvalRuns     = impl.listEvalRuns;
export const listAgentRuns    = impl.listAgentRuns;
export const getAgentRun      = impl.getAgentRun;

// Workbench
export const workbenchRetrieve = impl.workbenchRetrieve;
