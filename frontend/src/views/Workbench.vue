<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from '../composables/useToast';
import { PageHeader, Btn, Icon, Field, TextArea, Checkbox, Seg } from '../components/industry';
import Loader from '../components/industry/Loader.vue';
import { workbenchRetrieve } from '../services/api';
import type { WorkbenchChunk, WorkbenchSpec } from '../services/types';

const question = ref('What were the eligibility criteria for the BNT162b2 vaccine trial?');
const trialFilter = ref<string[]>([]);
const phaseFilter = ref({ I: false, II: false, III: true, IV: false });
const sectionFilter = ref<'all' | 'results' | 'adverse' | 'methods' | 'eligibility'>('all');
const ranker = ref<'hybrid' | 'bm25' | 'vector'>('hybrid');
const k = ref(8);
const iterations = ref(2);

const chunks = ref<WorkbenchChunk[]>([]);
const running = ref(false);
const hasRun = ref(false);
const focusedChunkId = ref<string | null>(null);
const inspectorTab = ref<'chunk' | 'analyzer' | 'trace' | 'prompt'>('chunk');
const elapsedMs = ref(0);

const focusedChunk = computed(() =>
  chunks.value.find((c) => c.chunk_id === focusedChunkId.value) ?? chunks.value[0] ?? null
);

const groupedByTrial = ref<'ranked' | 'grouped'>('ranked');

async function run() {
  running.value = true;
  chunks.value = [];
  focusedChunkId.value = null;
  const t0 = performance.now();
  const spec: WorkbenchSpec = {
    question: question.value,
    filters: {
      phase: Object.entries(phaseFilter.value).filter(([, v]) => v).map(([k]) => k),
      section: sectionFilter.value === 'all' ? [] : [sectionFilter.value],
      trial_id: trialFilter.value,
    },
    ranker: ranker.value,
    k: k.value,
    iterations: iterations.value,
  };
  try {
    await workbenchRetrieve(spec, (c) => {
      chunks.value.push(c);
      if (!focusedChunkId.value) focusedChunkId.value = c.chunk_id;
      elapsedMs.value = performance.now() - t0;
    });
  } finally {
    running.value = false;
    hasRun.value = true;
    elapsedMs.value = performance.now() - t0;
  }
}

const displayChunks = computed(() => {
  if (groupedByTrial.value === 'ranked') return chunks.value;
  const groups = new Map<string, WorkbenchChunk[]>();
  for (const c of chunks.value) {
    if (!groups.has(c.trial_id)) groups.set(c.trial_id, []);
    groups.get(c.trial_id)!.push(c);
  }
  return Array.from(groups.values()).flat();
});

function highlightSnippet(text: string): string {
  const terms = question.value
    .toLowerCase()
    .split(/\W+/)
    .filter((t) => t.length > 3);
  let out = text;
  for (const term of terms) {
    const re = new RegExp(`\\b(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'ig');
    out = out.replace(re, '<mark>$1</mark>');
  }
  return out;
}

const { push: toast } = useToast();

function copyPrompt() {
  const p = buildPrompt();
  navigator.clipboard?.writeText(p);
  toast('Prompt copied to clipboard', 'success');
}

function onKey(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && !running.value && question.value.trim()) {
    e.preventDefault();
    run();
  }
}
const route = useRoute();
onMounted(() => {
  window.addEventListener('keydown', onKey);
  const nct = typeof route.query.nct === 'string' ? route.query.nct : null;
  if (nct) {
    trialFilter.value = [nct];
    phaseFilter.value = { I: false, II: false, III: false, IV: false };
    sectionFilter.value = 'all';
    question.value = `Summarize trial ${nct}: eligibility, endpoints, and key results.`;
    void run();
  }
});
onUnmounted(() => window.removeEventListener('keydown', onKey));

function buildPrompt(): string {
  return `SYSTEM: You are a clinical-trial evidence analyzer. Draft an answer using only the retrieved chunks below. Cite every claim with [cN] short IDs.

QUESTION:
${question.value}

RETRIEVED CHUNKS (${chunks.value.length}):
${chunks.value.map((c, i) => `[c${i + 1}] ${c.trial_id} · ${c.section} (score ${c.score_hybrid})\n${c.full_text}`).join('\n\n')}`;
}
</script>

<template>
  <div class="page tm-enter">
    <PageHeader style="--i: 0" kicker="WORKBENCH" title="Query builder">
      <template #subtitle>
        Every retrieval knob · live chunk stream · analyzer preview · raw prompt
      </template>
      <template #actions>
        <Btn variant="ghost"><Icon name="folder-open" :size="14" /> Load…</Btn>
        <Btn variant="secondary" :disabled="!chunks.length"><Icon name="save" :size="14" /> Save as exploration</Btn>
        <Btn variant="primary" :disabled="running || !question.trim()" @click="run">
          <Icon name="play" :size="14" /> Run
          <span class="kbd">⌘⏎</span>
        </Btn>
      </template>
    </PageHeader>

    <div class="wb" style="--i: 1">
      <!-- ═══════════ LEFT: QUERY PANEL ═══════════ -->
      <aside class="wb-query">
        <div class="wb-block-head">
          <span>QUERY</span>
          <span v-if="chunks.length" class="text-muted num">{{ chunks.length }} chunks · {{ (elapsedMs / 1000).toFixed(2) }}s</span>
        </div>

        <Field label="Question">
          <TextArea v-model="question" :rows="4" autosize placeholder="Ask a structured question about the corpus…" />
        </Field>

        <Field label="Phase">
          <div class="stack">
            <Checkbox v-model="phaseFilter.I" label="Phase I" />
            <Checkbox v-model="phaseFilter.II" label="Phase II" />
            <Checkbox v-model="phaseFilter.III" label="Phase III" />
            <Checkbox v-model="phaseFilter.IV" label="Phase IV" />
          </div>
        </Field>

        <Field label="Section">
          <Seg
            v-model="sectionFilter"
            :options="[
              { value: 'all',         label: 'All' },
              { value: 'results',     label: 'Results' },
              { value: 'adverse',     label: 'Adverse' },
              { value: 'methods',     label: 'Methods' },
              { value: 'eligibility', label: 'Eligib' },
            ]"
          />
        </Field>

        <Field label="Ranker">
          <Seg
            v-model="ranker"
            :options="[
              { value: 'hybrid', label: 'Hybrid' },
              { value: 'bm25',   label: 'BM25' },
              { value: 'vector', label: 'Vector' },
            ]"
          />
        </Field>

        <Field label="k (top chunks)">
          <div class="slider-row">
            <input type="range" min="1" max="20" step="1" v-model.number="k" class="slider" />
            <span class="slider-val num">{{ k }}</span>
          </div>
        </Field>

        <Field label="Max iterations">
          <div class="slider-row">
            <input type="range" min="0" max="3" step="1" v-model.number="iterations" class="slider" />
            <span class="slider-val num">{{ iterations }}</span>
          </div>
        </Field>
      </aside>

      <!-- ═══════════ CENTER: RESULTS ═══════════ -->
      <section class="wb-results">
        <div class="wb-block-head sticky">
          <span>RESULTS</span>
          <div class="results-controls">
            <span class="text-muted"><span class="num">{{ chunks.length }}</span> chunks</span>
            <Seg
              v-model="groupedByTrial"
              :options="[
                { value: 'ranked',  label: 'Ranked' },
                { value: 'grouped', label: 'Grouped' },
              ]"
            />
          </div>
        </div>

        <div v-if="running && !chunks.length" class="wb-loading">
          <Loader variant="trace" tone="accent" />
          <span class="text-muted">Retrieving from corpus…</span>
        </div>

        <div v-else-if="!chunks.length && hasRun" class="wb-empty">
          <Icon name="search-x" :size="22" />
          <div class="wb-empty-title">No chunks matched</div>
          <div class="wb-empty-body">
            <template v-if="trialFilter.length">
              No chunks are ingested for <span class="mono">{{ trialFilter.join(', ') }}</span>. Try clearing the trial filter or a different question.
            </template>
            <template v-else>
              Retrieval returned nothing for this query and filter set. Loosen filters or rephrase the question.
            </template>
          </div>
        </div>

        <div v-else-if="!chunks.length" class="wb-empty">
          <Icon name="sliders-horizontal" :size="22" />
          <div class="wb-empty-title">Configure a query and press Run</div>
          <div class="wb-empty-body">
            Every knob on the left maps 1:1 to a backend parameter. Retrieved chunks stream here as they arrive.
          </div>
        </div>

        <div v-else class="chunk-list">
          <button
            v-for="c in displayChunks"
            :key="c.chunk_id"
            type="button"
            class="chunk-card"
            :class="{ 'is-focused': focusedChunkId === c.chunk_id }"
            @click="focusedChunkId = c.chunk_id"
          >
            <div class="ck-head">
              <span class="ck-cid mono">{{ c.short_id }}</span>
              <span class="ck-nct mono">{{ c.trial_id }}</span>
              <span class="ck-section">{{ c.section }}</span>
              <span class="ck-score num">{{ c.score_hybrid.toFixed(3) }}</span>
            </div>
            <div class="ck-snippet" v-html="highlightSnippet(c.snippet)" />
            <div class="ck-scores">
              <div class="ck-score-item">
                <span class="ck-lbl">BM25</span>
                <span class="ck-bar"><i :style="{ width: `${c.score_bm25 * 100}%` }" /></span>
                <span class="ck-num num">{{ c.score_bm25.toFixed(2) }}</span>
              </div>
              <div class="ck-score-item">
                <span class="ck-lbl">Vector</span>
                <span class="ck-bar"><i :style="{ width: `${c.score_vector * 100}%` }" /></span>
                <span class="ck-num num">{{ c.score_vector.toFixed(2) }}</span>
              </div>
            </div>
          </button>

          <div v-if="running" class="chunk-loading">
            <Loader variant="dots" :size="10" tone="accent" />
            <span>More chunks arriving…</span>
          </div>
        </div>
      </section>

      <!-- ═══════════ RIGHT: INSPECTOR ═══════════ -->
      <aside class="wb-inspector">
        <div class="ins-tabs">
          <button
            v-for="t in ['chunk', 'analyzer', 'trace', 'prompt'] as const"
            :key="t"
            type="button"
            class="ins-tab"
            :class="{ 'is-active': inspectorTab === t }"
            @click="inspectorTab = t"
          >{{ t }}</button>
        </div>

        <div v-if="!focusedChunk" class="ins-empty">
          <Icon name="mouse-pointer-click" :size="18" />
          <div>Select a chunk to inspect</div>
        </div>

        <!-- CHUNK TAB -->
        <div v-else-if="inspectorTab === 'chunk'" class="ins-body">
          <div class="ins-head">
            <span class="ck-cid mono">{{ focusedChunk.short_id }}</span>
            <span class="ck-nct mono">{{ focusedChunk.trial_id }}</span>
            <span class="ck-section">{{ focusedChunk.section }}</span>
          </div>
          <div class="ins-scores">
            <div class="ins-score">
              <div class="ins-score-label">HYBRID</div>
              <div class="ins-score-value num">{{ focusedChunk.score_hybrid.toFixed(3) }}</div>
            </div>
            <div class="ins-score">
              <div class="ins-score-label">BM25</div>
              <div class="ins-score-value num">{{ focusedChunk.score_bm25.toFixed(3) }}</div>
            </div>
            <div class="ins-score">
              <div class="ins-score-label">VECTOR</div>
              <div class="ins-score-value num">{{ focusedChunk.score_vector.toFixed(3) }}</div>
            </div>
            <div class="ins-score">
              <div class="ins-score-label">TOKENS</div>
              <div class="ins-score-value num">{{ focusedChunk.tokens }}</div>
            </div>
          </div>
          <div class="ins-section">
            <div class="ins-section-head">FULL TEXT</div>
            <div class="ins-text" v-html="highlightSnippet(focusedChunk.full_text)" />
          </div>
        </div>

        <!-- ANALYZER TAB -->
        <div v-else-if="inspectorTab === 'analyzer'" class="ins-body">
          <div class="ins-section">
            <div class="ins-section-head">PER-SENTENCE DRAFT (preview)</div>
            <div class="analyzer-sentence">
              <div class="as-text">The BNT162b2 trial enrolled healthy adults aged 16 years or older, randomly assigned 1:1 to two doses of vaccine or placebo 21 days apart.</div>
              <div class="as-cites">
                <span class="mock-cid">c1</span>
                <span class="mock-cid">c2</span>
              </div>
            </div>
            <div class="analyzer-sentence">
              <div class="as-text">Both studies excluded pregnant participants and those with severe comorbidities.</div>
              <div class="as-cites">
                <span class="mock-cid">c3</span>
              </div>
            </div>
            <div class="analyzer-hint">
              <Icon name="info" :size="12" />
              Run analyzer to draft answer over the retrieved chunks
            </div>
          </div>
          <Btn variant="primary" block>
            <Icon name="pen-tool" :size="12" /> Run analyzer
          </Btn>
        </div>

        <!-- TRACE TAB -->
        <div v-else-if="inspectorTab === 'trace'" class="ins-body">
          <div class="ins-section">
            <div class="ins-section-head">RETRIEVAL TRACE</div>
            <div class="trace-line">
              <span class="tl-node"><Icon name="search" :size="10" /></span>
              <div>
                <div class="tl-name">RETRIEVER</div>
                <div class="tl-note">{{ ranker }} · k={{ k }} · {{ chunks.length }} chunks · {{ (elapsedMs / 1000).toFixed(2) }}s</div>
              </div>
            </div>
            <div v-if="chunks.length" class="trace-line">
              <span class="tl-node pending"><Icon name="pen-tool" :size="10" /></span>
              <div>
                <div class="tl-name">ANALYZER</div>
                <div class="tl-note text-muted">Not run yet</div>
              </div>
            </div>
            <div v-if="chunks.length" class="trace-line">
              <span class="tl-node pending"><Icon name="shield-check" :size="10" /></span>
              <div>
                <div class="tl-name">CITATION-CHECKER</div>
                <div class="tl-note text-muted">Not run yet</div>
              </div>
            </div>
          </div>
        </div>

        <!-- PROMPT TAB -->
        <div v-else-if="inspectorTab === 'prompt'" class="ins-body">
          <div class="ins-section">
            <div class="ins-section-head">
              <span>RAW ANALYZER PROMPT</span>
              <button type="button" class="copy-btn" @click="copyPrompt">
                <Icon name="copy" :size="11" /> Copy
              </button>
            </div>
            <pre class="prompt-block">{{ buildPrompt() }}</pre>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 20px 30px 40px;
  max-width: 1600px; margin: 0 auto;
  display: flex; flex-direction: column; gap: 20px;
}

.kbd {
  padding: 1px 6px; margin-left: 6px;
  font-family: ui-monospace, monospace; font-size: 10px;
  border: 1px solid color-mix(in srgb, currentColor 30%, transparent);
  border-radius: 4px;
  color: color-mix(in srgb, currentColor 70%, transparent);
  background: color-mix(in srgb, currentColor 8%, transparent);
}

/* ── 3-region layout ──────────────────────────────────────── */
.wb {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 380px;
  gap: 16px;
  min-height: 600px;
}
@media (max-width: 1200px) {
  .wb { grid-template-columns: 260px minmax(0, 1fr) 340px; gap: 12px; }
}
@media (max-width: 960px) {
  .wb { grid-template-columns: 1fr; }
}

.wb-query,
.wb-results,
.wb-inspector {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  min-width: 0;
  display: flex; flex-direction: column;
  min-height: 0;
}

.wb-query {
  padding: 18px;
  gap: 14px;
  align-self: start;
  position: sticky; top: 20px;
}

.wb-block-head {
  display: flex; align-items: center; justify-content: space-between;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-divider);
}
.wb-block-head.sticky {
  position: sticky; top: 0; z-index: 1;
  background: #fff; padding: 14px 18px;
  border-radius: 12px 12px 0 0;
  margin: 0;
}
.results-controls { display: inline-flex; align-items: center; gap: 12px; }

.stack { display: flex; flex-direction: column; gap: 6px; }

.slider-row {
  display: flex; align-items: center; gap: 12px;
}
.slider {
  flex: 1;
  height: 3px;
  border-radius: 99px;
  background: var(--color-neutral-200);
  -webkit-appearance: none; appearance: none;
  outline: none;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px var(--color-accent);
  cursor: pointer;
}
.slider::-moz-range-thumb {
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px var(--color-accent);
  cursor: pointer;
}
.slider-val {
  min-width: 26px; text-align: center;
  padding: 2px 8px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-size: 11px; font-weight: 600;
}

/* ── Results ──────────────────────────────────────────── */
.wb-results { overflow: hidden; }
.wb-loading,
.wb-empty {
  padding: 60px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  color: var(--color-neutral-500);
  text-align: center;
}
.wb-empty-title { font-family: var(--font-heading); font-weight: 600; font-size: 17px; color: var(--color-neutral-700); }
.wb-empty-body { font-size: 12.5px; max-width: 340px; }

.chunk-list { padding: 12px 14px 16px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }

.chunk-card {
  display: flex; flex-direction: column; gap: 8px;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-left: 3px solid var(--color-divider);
  border-radius: 10px;
  text-align: left; cursor: pointer;
  font-family: var(--font-body);
  transition: border-color 140ms, background 140ms;
  animation: chunk-in 220ms ease-out both;
}
@keyframes chunk-in { from { opacity: 0; transform: translateX(-3px); } to { opacity: 1; transform: none; } }
.chunk-card:hover {
  border-color: color-mix(in srgb, var(--color-accent) 45%, var(--color-divider));
  border-left-color: color-mix(in srgb, var(--color-accent) 60%, var(--color-divider));
}
.chunk-card.is-focused {
  border-color: var(--color-accent);
  border-left-color: var(--color-accent);
  background: color-mix(in srgb, var(--color-accent) 4%, #fff);
}

.ck-head { display: flex; align-items: center; gap: 8px; }
.ck-cid {
  display: inline-grid; place-items: center;
  min-width: 22px; padding: 1px 7px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-size: 10px; font-weight: 700;
}
.ck-nct { font-size: 11px; color: var(--color-accent-700); font-weight: 600; }
.ck-section {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9.5px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.ck-score { margin-left: auto; font-size: 12px; color: var(--color-neutral-800); font-weight: 600; }

.ck-snippet {
  font-size: 12.5px; line-height: 1.55;
  color: var(--color-neutral-800);
}
.ck-snippet :deep(mark) {
  background: transparent;
  color: var(--color-accent-800);
  border-bottom: 1.5px solid var(--color-accent);
  padding: 0 1px;
  font-weight: 500;
}

.ck-scores {
  display: flex; gap: 12px;
  padding-top: 6px;
  border-top: 1px dashed var(--color-divider);
}
.ck-score-item {
  display: flex; align-items: center; gap: 6px;
  flex: 1; min-width: 0;
}
.ck-lbl {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-500);
  min-width: 40px;
}
.ck-bar {
  flex: 1; height: 3px;
  background: var(--color-neutral-200);
  border-radius: 99px; overflow: hidden;
}
.ck-bar i { display: block; height: 100%; background: var(--color-accent); border-radius: 99px; }
.ck-num { font-size: 10.5px; color: var(--color-neutral-700); min-width: 32px; text-align: right; }

.chunk-loading {
  padding: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;
  color: var(--color-neutral-500); font-size: 11px;
}

/* ── Inspector ────────────────────────────────────────── */
.wb-inspector { overflow: hidden; }
.ins-tabs {
  display: flex;
  padding: 10px 12px 0;
  gap: 4px;
  border-bottom: 1px solid var(--color-divider);
  background: var(--color-neutral-100);
}
.ins-tab {
  padding: 8px 14px 10px;
  background: transparent; border: 0;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 120ms, border-color 120ms;
}
.ins-tab:hover { color: var(--color-text); }
.ins-tab.is-active {
  color: var(--color-accent-800);
  border-bottom-color: var(--color-accent);
}

.ins-empty {
  padding: 60px 20px; text-align: center;
  color: var(--color-neutral-500);
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  font-size: 12.5px;
}

.ins-body {
  padding: 16px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 14px;
  flex: 1; min-height: 0;
}

.ins-head { display: flex; align-items: center; gap: 8px; padding-bottom: 4px; }

.ins-scores {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
}
.ins-score {
  padding: 8px 10px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
  display: flex; flex-direction: column; gap: 2px;
}
.ins-score-label {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.ins-score-value {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 15px; color: var(--color-text);
}

.ins-section {
  display: flex; flex-direction: column; gap: 8px;
}
.ins-section-head {
  display: flex; align-items: center; justify-content: space-between;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.copy-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 8px;
  background: transparent; border: 1px solid var(--color-divider);
  border-radius: 6px;
  color: var(--color-neutral-700);
  font-family: var(--font-body); font-size: 10.5px;
  cursor: pointer;
  transition: background 120ms;
}
.copy-btn:hover { background: var(--color-neutral-100); color: var(--color-text); }

.ins-text {
  font-size: 13px; line-height: 1.65;
  color: var(--color-neutral-800);
  padding: 12px 14px;
  background: var(--color-neutral-100);
  border-radius: 8px;
  border: 1px solid var(--color-divider);
}
.ins-text :deep(mark) {
  background: transparent;
  color: var(--color-accent-800);
  border-bottom: 1.5px solid var(--color-accent);
  padding: 0 1px;
  font-weight: 500;
}

.analyzer-sentence {
  padding: 10px 12px;
  border: 1px solid var(--color-divider);
  border-left: 3px solid var(--color-accent);
  border-radius: 8px;
  display: flex; flex-direction: column; gap: 6px;
  background: #fff;
}
.as-text { font-size: 12.5px; line-height: 1.55; color: var(--color-text); }
.as-cites { display: inline-flex; gap: 4px; }
.mock-cid {
  display: inline-block; padding: 1px 7px;
  font-family: ui-monospace, monospace; font-size: 10px; font-weight: 700;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
}
.analyzer-hint {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 10px;
  background: var(--color-neutral-100);
  border: 1px dashed var(--color-divider);
  border-radius: 8px;
  font-size: 11.5px; color: var(--color-neutral-600);
}

.trace-line {
  display: grid; grid-template-columns: 22px 1fr; gap: 10px; align-items: start;
  padding: 8px 0;
  border-bottom: 1px dashed var(--color-divider);
}
.trace-line:last-child { border-bottom: 0; }
.tl-node {
  width: 22px; height: 22px; border-radius: 6px;
  background: var(--color-accent-100); color: var(--color-accent-700);
  border: 1px solid color-mix(in srgb, var(--color-accent) 30%, transparent);
  display: inline-grid; place-items: center;
}
.tl-node.pending { background: #fff; border-color: var(--color-divider); color: var(--color-neutral-500); }
.tl-name {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-accent-800);
}
.tl-node.pending + div .tl-name { color: var(--color-neutral-500); }
.tl-note { font-size: 11.5px; line-height: 1.5; color: var(--color-neutral-700); margin-top: 2px; }

.prompt-block {
  padding: 12px 14px;
  background: var(--color-neutral-900); color: #e7e7ea;
  border-radius: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px; line-height: 1.55;
  white-space: pre-wrap; word-wrap: break-word;
  margin: 0;
  max-height: 400px; overflow-y: auto;
}
</style>
