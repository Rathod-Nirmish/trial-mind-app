<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { PageHeader, Blueprint, Btn, Icon, Tag, Field, TextInput, Checkbox, Seg } from '../components/industry';
import Loader from '../components/industry/Loader.vue';
import { getCorpusStats, listTrials } from '../services/api';
import type { CorpusStats, Trial } from '../services/types';

const stats = ref<CorpusStats | null>(null);
const trials = ref<Trial[]>([]);
const loading = ref(true);

const search = ref('');
const phase = ref({ I: false, II: false, III: false, IV: false });
const status = ref({ recruiting: false, completed: false });
const source = ref<'all' | 'nct' | 'pdf'>('all');
const view = ref<'table' | 'grid'>('table');

const selectedTrial = ref<Trial | null>(null);

onMounted(async () => {
  loading.value = true;
  try {
    const [s, t] = await Promise.all([getCorpusStats(), listTrials()]);
    stats.value = s;
    trials.value = t.items;
  } finally {
    loading.value = false;
  }
});

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  const activePhase = new Set(
    Object.entries(phase.value).filter(([, v]) => v).map(([k]) => k)
  );
  const activeStatus = new Set(
    Object.entries(status.value).filter(([, v]) => v).map(([k]) => k)
  );
  return trials.value.filter((t) => {
    if (q && !`${t.nct_id} ${t.title} ${t.condition}`.toLowerCase().includes(q)) return false;
    if (activePhase.size && !activePhase.has(t.phase)) return false;
    if (activeStatus.size && !activeStatus.has(t.status.toLowerCase())) return false;
    if (source.value !== 'all' && t.source !== source.value) return false;
    return true;
  });
});

const activeFilterCount = computed(() =>
  Object.values(phase.value).filter(Boolean).length +
  Object.values(status.value).filter(Boolean).length +
  (source.value !== 'all' ? 1 : 0) +
  (search.value.trim() ? 1 : 0)
);

function clearFilters() {
  search.value = '';
  Object.keys(phase.value).forEach((k) => (phase.value[k as keyof typeof phase.value] = false));
  Object.keys(status.value).forEach((k) => (status.value[k as keyof typeof status.value] = false));
  source.value = 'all';
}

function onEsc(e: KeyboardEvent) {
  if (e.key === 'Escape' && selectedTrial.value) {
    e.preventDefault();
    selectedTrial.value = null;
  }
}
onMounted(() => window.addEventListener('keydown', onEsc));
onUnmounted(() => window.removeEventListener('keydown', onEsc));

const router = useRouter();

function openOnClinicalTrials(nctId: string) {
  window.open(`https://clinicaltrials.gov/study/${nctId}`, '_blank', 'noopener,noreferrer');
}

function openInWorkbench(nctId: string) {
  router.push({ name: 'workbench', query: { nct: nctId } });
}

function daysAgoLabel(iso: string) {
  const d = (Date.now() - new Date(iso).getTime()) / 86400_000;
  if (d < 1)  return 'today';
  if (d < 2)  return 'yesterday';
  return `${Math.floor(d)}d ago`;
}
</script>

<template>
  <div class="page tm-enter">
    <PageHeader style="--i: 0" kicker="CORPUS" title="Trials library">
      <template #subtitle>
        <template v-if="stats">
          <span class="num">{{ stats.trials.toLocaleString() }}</span> trials ·
          <span class="num">{{ stats.chunks.toLocaleString() }}</span> chunks ·
          phase I <span class="num">{{ stats.by_phase.I }}</span>
          · II <span class="num">{{ stats.by_phase.II }}</span>
          · III <span class="num">{{ stats.by_phase.III }}</span>
          · IV <span class="num">{{ stats.by_phase.IV }}</span>
        </template>
        <template v-else>Loading corpus statistics…</template>
      </template>
      <template #actions>
        <Btn variant="secondary"><Icon name="upload" :size="14" /> Import PDFs</Btn>
        <Btn variant="primary"><Icon name="download-cloud" :size="14" /> Ingest from NCT</Btn>
      </template>
    </PageHeader>

    <div class="body" style="--i: 1">
      <!-- ═══════════ FILTER RAIL ═══════════ -->
      <aside class="rail">
        <div class="rail-head">
          <span class="rail-title">FILTERS</span>
          <button v-if="activeFilterCount" class="rail-clear" @click="clearFilters">
            <Icon name="x" :size="11" /> Clear
          </button>
        </div>

        <Field label="Search">
          <TextInput v-model="search" placeholder="NCT ID, condition, sponsor…" />
        </Field>

        <Field label="Phase">
          <div class="stack">
            <Checkbox v-model="phase.I" label="Phase I" />
            <Checkbox v-model="phase.II" label="Phase II" />
            <Checkbox v-model="phase.III" label="Phase III" />
            <Checkbox v-model="phase.IV" label="Phase IV" />
          </div>
        </Field>

        <Field label="Status">
          <div class="stack">
            <Checkbox v-model="status.recruiting" label="Recruiting" />
            <Checkbox v-model="status.completed" label="Completed" />
          </div>
        </Field>

        <Field label="Source">
          <Seg
            v-model="source"
            :options="[
              { value: 'all', label: 'All' },
              { value: 'nct', label: 'NCT' },
              { value: 'pdf', label: 'PDF' },
            ]"
          />
        </Field>
      </aside>

      <!-- ═══════════ TABLE ═══════════ -->
      <section class="results">
        <div class="toolbar">
          <div class="toolbar-left">
            <span class="chip">
              <span class="num">{{ filtered.length }}</span>
              <span class="chip-sep">/</span>
              <span class="num">{{ trials.length }}</span>
              trials
            </span>
            <span v-if="activeFilterCount" class="chip chip-accent">
              <Icon name="filter" :size="11" />
              <span class="num">{{ activeFilterCount }}</span>
              filter{{ activeFilterCount === 1 ? '' : 's' }} active
            </span>
          </div>
          <div class="toolbar-right">
            <Seg
              v-model="view"
              :options="[
                { value: 'table', label: 'Table' },
                { value: 'grid', label: 'Grid' },
              ]"
            />
          </div>
        </div>

        <div v-if="loading" class="loading">
          <Loader variant="spinner" :size="20" label="Loading trials…" />
        </div>

        <template v-else>
          <!-- Table view — native <table>: guarantees column alignment across all rows. -->
          <Blueprint v-if="view === 'table'" no-hover class="tbl-wrap">
            <table class="tbl">
              <colgroup>
                <col class="col-nct" />
                <col class="col-title" />
                <col class="col-cond" />
                <col class="col-phase" />
                <col class="col-status" />
                <col class="col-chunks" />
                <col class="col-ingested" />
              </colgroup>
              <thead>
                <tr>
                  <th>NCT ID</th>
                  <th>Title</th>
                  <th>Condition</th>
                  <th class="center">Phase</th>
                  <th>Status</th>
                  <th class="right">Chunks</th>
                  <th class="right">Ingested</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!filtered.length" class="empty-row">
                  <td colspan="7">
                    <div class="empty-panel">
                      <div class="empty-badge"><Icon name="search-x" :size="26" /></div>
                      <div class="empty-title">No matching trials</div>
                      <div class="empty-sub">Try removing a filter or broadening your search to see more results.</div>
                      <Btn variant="secondary" @click="clearFilters">
                        <Icon name="x" :size="12" /> Clear filters
                      </Btn>
                    </div>
                  </td>
                </tr>
                <tr
                  v-for="t in filtered"
                  :key="t.nct_id"
                  tabindex="0"
                  @click="selectedTrial = t"
                  @keydown.enter="selectedTrial = t"
                >
                  <td class="mono nct">{{ t.nct_id }}</td>
                  <td class="ttl">{{ t.title }}</td>
                  <td class="cond text-muted">{{ t.condition }}</td>
                  <td class="phase-cell center">{{ t.phase }}</td>
                  <td>
                    <span class="status-pill" :class="`is-${t.status.toLowerCase()}`">{{ t.status }}</span>
                  </td>
                  <td class="num right">{{ t.chunks }}</td>
                  <td class="text-muted right">{{ daysAgoLabel(t.ingested_at) }}</td>
                </tr>
              </tbody>
            </table>
          </Blueprint>

          <!-- Grid view -->
          <div v-else class="grid-view">
            <button
              v-for="t in filtered"
              :key="t.nct_id"
              type="button"
              class="grid-card"
              @click="selectedTrial = t"
            >
              <div class="gc-head">
                <span class="mono nct">{{ t.nct_id }}</span>
                <span class="phase-cell">Phase {{ t.phase }}</span>
              </div>
              <div class="gc-title">{{ t.title }}</div>
              <div class="gc-cond text-muted">{{ t.condition }}</div>
              <div class="gc-meta">
                <span class="status-pill" :class="`is-${t.status.toLowerCase()}`">{{ t.status }}</span>
                <span class="num text-muted">{{ t.chunks }} chunks</span>
              </div>
            </button>
            <div v-if="!filtered.length" class="empty-panel grid-empty">
              <div class="empty-badge"><Icon name="search-x" :size="26" /></div>
              <div class="empty-title">No matching trials</div>
              <div class="empty-sub">Try removing a filter or broadening your search to see more results.</div>
              <Btn variant="secondary" @click="clearFilters">
                <Icon name="x" :size="12" /> Clear filters
              </Btn>
            </div>
          </div>
        </template>
      </section>
    </div>

    <!-- ═══════════ TRIAL DRAWER ═══════════ -->
    <transition name="drawer">
      <div v-if="selectedTrial" class="drawer-backdrop" @click.self="selectedTrial = null">
        <aside class="drawer">
          <header class="drawer-head">
            <div class="drawer-titles">
              <div class="drawer-kicker mono">{{ selectedTrial.nct_id }}</div>
              <h3 class="drawer-title">{{ selectedTrial.title }}</h3>
            </div>
            <button type="button" class="drawer-close" @click="selectedTrial = null" aria-label="Close">
              <Icon name="x" :size="16" />
            </button>
          </header>

          <div class="drawer-body">
            <div class="drawer-stats">
              <div class="stat">
                <div class="stat-label">Phase</div>
                <div class="stat-value">{{ selectedTrial.phase }}</div>
              </div>
              <div class="stat">
                <div class="stat-label">Status</div>
                <div class="stat-value">
                  <span class="status-pill" :class="`is-${selectedTrial.status.toLowerCase()}`">
                    {{ selectedTrial.status }}
                  </span>
                </div>
              </div>
              <div class="stat">
                <div class="stat-label">Condition</div>
                <div class="stat-value">{{ selectedTrial.condition }}</div>
              </div>
              <div class="stat">
                <div class="stat-label">Source</div>
                <div class="stat-value uppercase">{{ selectedTrial.source }}</div>
              </div>
              <div class="stat">
                <div class="stat-label">Chunks</div>
                <div class="stat-value num">{{ selectedTrial.chunks }}</div>
              </div>
              <div class="stat">
                <div class="stat-label">Ingested</div>
                <div class="stat-value">{{ new Date(selectedTrial.ingested_at).toLocaleDateString() }}</div>
              </div>
            </div>

            <div class="drawer-section">
              <div class="section-head">
                <span>CHUNK BREAKDOWN</span>
                <Tag variant="ghost"><span class="num">{{ selectedTrial.chunks }}</span> total</Tag>
              </div>
              <div class="chunk-samples">
                <div v-for="i in Math.min(4, Math.ceil(selectedTrial.chunks / 100))" :key="i" class="chunk-item">
                  <span class="mono chunk-id">ck-{{ 1000 + i }}</span>
                  <span class="chunk-section">{{ ['Results', 'Methods', 'Adverse', 'Eligibility'][i - 1] }}</span>
                  <span class="num chunk-tokens">{{ 380 + i * 24 }} tok</span>
                  <span class="chunk-bar"><i :style="{ width: `${60 + i * 8}%` }" /></span>
                </div>
              </div>
              <div class="drawer-hint">
                <Icon name="info" :size="12" />
                Chunk-level inspection available in Workbench
              </div>
            </div>
          </div>

          <footer class="drawer-foot">
            <Btn variant="secondary" @click="openOnClinicalTrials(selectedTrial.nct_id)"><Icon name="external-link" :size="12" /> View on ClinicalTrials.gov</Btn>
            <Btn variant="primary" @click="openInWorkbench(selectedTrial.nct_id)"><Icon name="sliders-horizontal" :size="12" /> Open in Workbench</Btn>
          </footer>
        </aside>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.page {
  padding: 20px 30px 40px;
  max-width: 1400px; margin: 0 auto;
  display: flex; flex-direction: column; gap: 20px;
  width: 100%;
}

.body {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
@media (max-width: 900px) { .body { grid-template-columns: 1fr; } }

/* ── Filter rail ─────────────────────────────────────────── */
.rail {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  padding: 16px;
  display: flex; flex-direction: column; gap: 16px;
  box-shadow: var(--shadow-sm);
  position: sticky; top: 20px;
  max-height: calc(100vh - 40px);
  overflow-y: auto;
}
.rail-head {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-divider);
}
.rail-title {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.rail-clear {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 8px;
  background: transparent; border: 0;
  color: var(--color-accent-700);
  font-family: var(--font-body); font-weight: 500;
  font-size: 11px;
  cursor: pointer; border-radius: 6px;
}
.rail-clear:hover { background: var(--color-accent-100); }
.stack { display: flex; flex-direction: column; gap: 6px; }

/* ── Results section ─────────────────────────────────────── */
.results { display: flex; flex-direction: column; gap: 12px; min-width: 0; }

.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 2px;
}
.toolbar-left, .toolbar-right {
  display: inline-flex; align-items: center; gap: 8px;
}

.loading {
  padding: 60px 20px;
  display: flex; justify-content: center;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
}

/* ── Table — native <table> with fixed layout so columns are guaranteed
 *     to align across all rows. ─────────────────────────────────────── */
.tbl-wrap { padding: 0; overflow: hidden; }

.tbl {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
  font-family: var(--font-body);
  font-size: 13.5px;
}

/* Column widths defined once, apply to every row. */
.tbl .col-nct      { width: 118px; }
.tbl .col-title    { width: auto; }              /* takes remaining space */
.tbl .col-cond     { width: 172px; }
.tbl .col-phase    { width: 68px; }
.tbl .col-status   { width: 132px; }
.tbl .col-chunks   { width: 76px; }
.tbl .col-ingested { width: 96px; }

.tbl thead th {
  padding: 12px 16px;
  background: var(--color-neutral-100);
  border-bottom: 1px solid var(--color-divider);
  font-family: var(--font-body); font-weight: 600;
  font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
  text-align: left;
  white-space: nowrap;
}

.tbl tbody td {
  padding: 14px 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-text) 6%, transparent);
  color: var(--color-neutral-800);
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tbl tbody tr:last-child td { border-bottom: 0; }

.tbl tbody tr {
  cursor: pointer;
  transition: background 100ms ease;
}
.tbl tbody tr:hover {
  background: color-mix(in srgb, var(--color-accent) 5%, transparent);
}
.tbl tbody tr:focus-visible {
  outline: 2px solid var(--color-accent); outline-offset: -2px;
}
.tbl tbody tr.empty-row { cursor: default; }
.tbl tbody tr.empty-row:hover { background: transparent; }

/* Per-column alignment — header + cell share the same axis. */
.tbl th.right,  .tbl td.right  { text-align: right; }
.tbl th.center, .tbl td.center { text-align: center; }

.tbl .nct { font-size: 12px; color: var(--color-neutral-700); }
.tbl .ttl {
  color: var(--color-text); font-weight: 500;
}
.tbl .cond { font-size: 12px; }

/* Unified pill system — 99px filled tinted rounded rectangles.
 * All data-cell pills share the same shape, size, and typography.
 * Only the tint changes per meaning. */
/* Phase — bare Roman numeral, uppercase, tabular. No pill (a pill would
 * fight for visual weight with the far busier Status pill next to it).
 * Just typography carrying the meaning. */
.phase-cell {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 12.5px; letter-spacing: 0.08em;
  color: var(--color-neutral-700);
  font-variant-numeric: tabular-nums;
}

/* Status pill — the ONE pill in the row, so it earns its visual weight.
 * Fixed width so all statuses share a common baseline column. */
.status-pill {
  display: inline-flex; align-items: center; justify-content: center;
  width: 108px; padding: 3px 10px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.06em; text-transform: uppercase;
  border-radius: 99px;
  white-space: nowrap;
  line-height: 1.4;
}

.status-pill.is-completed  { background: color-mix(in srgb, #4bb26a 14%, #fff); color: #1e6934; }
.status-pill.is-recruiting { background: var(--color-accent-100);                color: var(--color-accent-800); }
.status-pill.is-terminated { background: #fbeceb;                                color: #8b3025; }
.status-pill.is-withdrawn  { background: var(--color-neutral-200);               color: var(--color-neutral-700); }
.status-pill.is-active     { background: color-mix(in srgb, #4bb26a 14%, #fff); color: #1e6934; }

/* Toolbar chips — same pill shape, tone by meaning */
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 500;
  font-size: 11.5px; color: var(--color-neutral-700);
  white-space: nowrap;
}
.chip .chip-sep { color: var(--color-neutral-400); margin: 0 -2px; }
.chip-accent {
  background: var(--color-accent-100);
  border-color: transparent;
  color: var(--color-accent-800);
  font-weight: 600;
}
.chip-accent :deep(svg) { color: var(--color-accent-700); }

/* Empty state — a real panel, not a shrunken card. Shared across table
 * (rendered inside a full-width <td colspan>) and grid (spans all columns). */
.empty-panel {
  min-height: 360px;
  padding: 48px 24px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px;
  color: var(--color-neutral-600);
  font-family: var(--font-body);
  text-align: center;
  white-space: normal;
}
.empty-badge {
  width: 56px; height: 56px;
  display: grid; place-items: center;
  border-radius: 99px;
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
  margin-bottom: 4px;
}
.empty-title {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 16px;
  color: var(--color-text);
}
.empty-sub {
  font-size: 12.5px;
  color: var(--color-neutral-600);
  max-width: 320px; line-height: 1.5;
  margin-bottom: 6px;
}

/* ── Grid view ───────────────────────────────────────────── */
.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  align-content: start;
}
.grid-empty {
  grid-column: 1 / -1;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}

.grid-card {
  display: flex; flex-direction: column; gap: 8px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  text-align: left; cursor: pointer;
  transition: border-color 140ms, transform 140ms;
  font-family: var(--font-body);
}
.grid-card:hover {
  border-color: color-mix(in srgb, var(--color-accent) 45%, var(--color-divider));
  transform: translateY(-1px);
}
.gc-head { display: flex; align-items: center; justify-content: space-between; }
.gc-title { font-size: 14px; font-weight: 500; line-height: 1.4; color: var(--color-text); }
.gc-cond { font-size: 12px; }
.gc-meta {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 8px; border-top: 1px dashed var(--color-divider);
  font-size: 11.5px;
}

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-backdrop {
  position: fixed; inset: 0; z-index: 50;
  background: color-mix(in srgb, var(--color-neutral-900) 40%, transparent);
  backdrop-filter: blur(2px);
  display: flex; justify-content: flex-end;
}
.drawer {
  width: min(520px, 100%); height: 100%;
  background: #fff;
  border-left: 1px solid var(--color-divider);
  display: flex; flex-direction: column;
  box-shadow: -18px 0 40px color-mix(in srgb, #2b2b2d 20%, transparent);
}

.drawer-head {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 20px 22px 16px;
  border-bottom: 1px solid var(--color-divider);
}
.drawer-titles { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.drawer-kicker {
  font-size: 11px; letter-spacing: 0.08em;
  color: var(--color-accent-700); font-weight: 600;
}
.drawer-title {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 22px; line-height: 1.25;
  color: var(--color-text); margin: 0;
}
.drawer-close {
  flex: none; width: 32px; height: 32px;
  border: 1px solid var(--color-divider); border-radius: 8px;
  background: #fff; color: var(--color-neutral-700);
  cursor: pointer;
  display: grid; place-items: center;
  transition: background 120ms, border-color 120ms;
}
.drawer-close:hover { background: var(--color-neutral-100); border-color: color-mix(in srgb, var(--color-text) 30%, transparent); }

.drawer-body {
  flex: 1; min-height: 0; overflow-y: auto;
  padding: 20px 22px;
  display: flex; flex-direction: column; gap: 24px;
}

.drawer-stats {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
}
.stat {
  padding: 12px 14px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  display: flex; flex-direction: column; gap: 4px;
}
.stat-label {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.stat-value { font-size: 14px; color: var(--color-text); font-weight: 500; }
.stat-value.uppercase { text-transform: uppercase; letter-spacing: 0.08em; font-size: 12px; }

.drawer-section { display: flex; flex-direction: column; gap: 10px; }
.section-head {
  display: flex; align-items: center; justify-content: space-between;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}

.chunk-samples { display: flex; flex-direction: column; gap: 6px; }
.chunk-item {
  display: grid; grid-template-columns: 60px 90px 60px 1fr; gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border: 1px solid var(--color-divider);
  border-radius: 8px;
  font-size: 11.5px;
}
.chunk-id { color: var(--color-neutral-700); font-size: 10.5px; }
.chunk-section { color: var(--color-accent-800); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
.chunk-tokens { color: var(--color-neutral-600); text-align: right; }
.chunk-bar {
  height: 3px; background: var(--color-neutral-200);
  border-radius: 99px; overflow: hidden;
}
.chunk-bar i { display: block; height: 100%; background: var(--color-accent); border-radius: 99px; }

.drawer-hint {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 10px;
  background: var(--color-accent-100);
  border: 1px solid var(--color-accent-300);
  border-radius: 8px;
  font-size: 11.5px; color: var(--color-accent-800);
}

.drawer-foot {
  padding: 14px 22px;
  border-top: 1px solid var(--color-divider);
  background: var(--color-neutral-100);
  display: flex; justify-content: flex-end; gap: 8px;
}

/* Drawer transitions */
.drawer-enter-active, .drawer-leave-active {
  transition: opacity 200ms ease;
}
.drawer-enter-active .drawer, .drawer-leave-active .drawer {
  transition: transform 240ms cubic-bezier(.32,.72,.33,1);
}
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }
</style>
