<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { PageHeader, Blueprint, Btn, Icon, Tag, Seg, TextInput, Field, RowCard } from '../components/industry';
import Loader from '../components/industry/Loader.vue';
import { getEvalAggregate, listEvalRuns, listAgentRuns } from '../services/api';
import type { EvalAggregate, EvalRun, AgentRunSummary } from '../services/types';

const tab = ref<'evals' | 'agents'>('evals');
const loading = ref(true);

const aggregate = ref<EvalAggregate | null>(null);
const evalRuns = ref<EvalRun[]>([]);
const agentRuns = ref<AgentRunSummary[]>([]);

const search = ref('');
const statusFilter = ref<'all' | 'verified' | 'refined' | 'failed'>('all');
const expanded = ref<Record<string, boolean>>({});

onMounted(async () => {
  loading.value = true;
  try {
    const [agg, evs, runs] = await Promise.all([
      getEvalAggregate(),
      listEvalRuns(),
      listAgentRuns(),
    ]);
    aggregate.value = agg;
    evalRuns.value = evs.items;
    agentRuns.value = runs.items;
  } finally {
    loading.value = false;
  }
});

const filteredRuns = computed(() => {
  const q = search.value.trim().toLowerCase();
  return agentRuns.value.filter((r) => {
    if (statusFilter.value !== 'all' && r.status !== statusFilter.value) return false;
    if (q && !r.question.toLowerCase().includes(q)) return false;
    return true;
  });
});

// Sparkline path from history points
function sparkPath(hist: { at: string; halluc_pct: number }[]): string {
  if (!hist.length) return '';
  const w = 100, h = 40;
  const max = Math.max(...hist.map((p) => p.halluc_pct), 1);
  const step = w / (hist.length - 1);
  return hist
    .map((p, i) => {
      const x = i * step;
      const y = h - (p.halluc_pct / max) * (h - 4) - 2;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}
function sparkFillPath(hist: { at: string; halluc_pct: number }[]): string {
  if (!hist.length) return '';
  const line = sparkPath(hist);
  const w = 100, h = 40;
  return `${line} L${w},${h} L0,${h} Z`;
}

function ago(iso: string) {
  const dt = (Date.now() - new Date(iso).getTime()) / 3600_000;
  if (dt < 1) return `${Math.max(1, Math.round(dt * 60))}m ago`;
  if (dt < 24) return `${Math.round(dt)}h ago`;
  return `${Math.round(dt / 24)}d ago`;
}
function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function statusVariant(s: AgentRunSummary['status']): 'accent' | 'neutral' | 'warn' {
  if (s === 'verified') return 'accent';
  if (s === 'refined')  return 'neutral';
  return 'warn';
}
function statusLabel(s: AgentRunSummary['status']) {
  if (s === 'verified') return 'Verified';
  if (s === 'refined')  return 'Verified after retry';
  return 'Answer withheld';
}
function statusIcon(s: AgentRunSummary['status']) {
  if (s === 'verified') return 'check';
  if (s === 'refined')  return 'refresh-cw';
  return 'alert-triangle';
}
function stepIcon(name: string) {
  if (name === 'retriever')        return 'search';
  if (name === 'analyzer')         return 'pen-tool';
  if (name === 'citation-checker') return 'shield-check';
  return 'circle';
}
function stepClass(status: 'ok' | 'warn' | 'fail' | 'retry') {
  return status === 'ok' ? '' : `is-${status}`;
}
</script>

<template>
  <div class="page tm-enter">
    <PageHeader style="--i: 0" kicker="RUNS" title="Evaluation & agent history">
      <template #subtitle>
        Golden-QA regression eval · every chat invocation logged · hallucination rate over time
      </template>
      <template #actions>
        <Btn variant="secondary"><Icon name="download" :size="14" /> Export CSV</Btn>
        <Btn variant="primary"><Icon name="play" :size="14" /> Trigger eval</Btn>
      </template>
    </PageHeader>

    <div class="tabs-row" style="--i: 1">
      <div class="segtabs" role="tablist">
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'evals'"
          class="segtab"
          :class="{ 'is-active': tab === 'evals' }"
          @click="tab = 'evals'"
        >Evaluations</button>
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'agents'"
          class="segtab"
          :class="{ 'is-active': tab === 'agents' }"
          @click="tab = 'agents'"
        >
          Agent runs
          <span v-if="agentRuns.length" class="segtab-count num">{{ agentRuns.length }}</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading" style="--i: 2">
      <Loader variant="spinner" :size="20" label="Loading runs…" />
    </div>

    <!-- ═══════════ EVALUATIONS TAB ═══════════ -->
    <template v-else-if="tab === 'evals'">
      <div class="ev-grid" style="--i: 2">
        <!-- Headline metric plate -->
        <Blueprint no-hover class="metric-plate">
          <div class="mp-kicker">
            LATEST · {{ evalRuns[0] ? shortDate(evalRuns[0].run_at) : '—' }}
          </div>
          <div class="mp-value num">
            {{ aggregate ? aggregate.halluc_pct.toFixed(1) : '—' }}<span class="mp-unit">%</span>
          </div>
          <div class="mp-sub">hallucinated citations</div>
          <div v-if="aggregate" class="mp-delta">
            <Icon name="trending-down" :size="13" />
            <span class="num">{{ aggregate.delta_pct }}%</span> reduction vs no-checker
          </div>
          <div v-if="aggregate" class="mp-meta">
            <span>entail <b class="num">{{ aggregate.entail.toFixed(2) }}</b></span>
            <span class="mp-meta-dot" />
            <span>retrieve <b class="num">{{ aggregate.retrieve.toFixed(2) }}</b></span>
            <span class="mp-meta-dot" />
            <span><b class="num">{{ aggregate.pass }}/{{ aggregate.total }}</b> pass</span>
            <span class="mp-meta-dot" />
            <span><b class="num">{{ aggregate.avg_latency_s.toFixed(1) }}s</b> avg</span>
          </div>
        </Blueprint>

        <!-- Sparkline history -->
        <Blueprint no-hover class="hist">
          <div class="hist-head">
            <span class="hist-title">HALLUCINATION RATE · LAST 12 RUNS</span>
            <span v-if="aggregate" class="hist-legend num">
              max <b>{{ Math.max(...aggregate.history.map((p) => p.halluc_pct)).toFixed(1) }}%</b>
              · now <b>{{ aggregate.halluc_pct.toFixed(1) }}%</b>
            </span>
          </div>
          <svg v-if="aggregate" class="spark" viewBox="0 0 100 40" preserveAspectRatio="none">
            <defs>
              <linearGradient id="fadefill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--color-accent)" stop-opacity="0.25" />
                <stop offset="100%" stop-color="var(--color-accent)" stop-opacity="0" />
              </linearGradient>
            </defs>
            <path :d="sparkFillPath(aggregate.history)" fill="url(#fadefill)" />
            <path :d="sparkPath(aggregate.history)" fill="none"
              stroke="var(--color-accent)" stroke-width="1.25"
              stroke-linecap="round" stroke-linejoin="round" />
            <g v-for="(p, i) in aggregate.history" :key="i">
              <circle
                :cx="(i / (aggregate.history.length - 1)) * 100"
                :cy="40 - (p.halluc_pct / Math.max(...aggregate.history.map((x) => x.halluc_pct), 1)) * 36 - 2"
                r="1.5"
                fill="var(--color-accent-700)"
              />
            </g>
          </svg>
          <div v-if="aggregate" class="hist-axis num">
            <span>{{ shortDate(aggregate.history[0].at) }}</span>
            <span>today</span>
          </div>
        </Blueprint>
      </div>

      <!-- Eval runs table -->
      <div class="section-title" style="--i: 3">
        <span>EVAL RUNS</span>
        <span class="text-muted"><span class="num">{{ evalRuns.length }}</span> total</span>
      </div>
      <Blueprint no-hover class="tbl-wrap" style="--i: 4">
        <table class="tbl">
          <colgroup>
            <col class="col-date" />
            <col class="col-arm" />
            <col class="col-pass" />
            <col class="col-halluc" />
            <col class="col-entail" />
            <col class="col-retrieve" />
            <col class="col-p50" />
            <col class="col-p95" />
          </colgroup>
          <thead>
            <tr>
              <th>Date</th>
              <th>Arm</th>
              <th class="right">Pass</th>
              <th class="right">Halluc %</th>
              <th class="right">Entail</th>
              <th class="right">Retrieve</th>
              <th class="right">P50</th>
              <th class="right">P95</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in evalRuns" :key="r.id">
              <td>{{ new Date(r.run_at).toLocaleDateString() }}</td>
              <td><span class="arm-pill" :class="`arm-${r.arm}`">{{ r.arm }}</span></td>
              <td class="num right">{{ r.pass }}/{{ r.total }}</td>
              <td class="num right">
                <span :class="r.halluc_pct === 0 ? 'good' : 'meh'">{{ r.halluc_pct.toFixed(1) }}%</span>
              </td>
              <td class="num right">{{ r.entail.toFixed(2) }}</td>
              <td class="num right">{{ r.retrieve.toFixed(2) }}</td>
              <td class="num right">{{ (r.p50_ms / 1000).toFixed(2) }}s</td>
              <td class="num right">{{ (r.p95_ms / 1000).toFixed(2) }}s</td>
            </tr>
          </tbody>
        </table>
      </Blueprint>
    </template>

    <!-- ═══════════ AGENT RUNS TAB ═══════════ -->
    <template v-else>
      <div class="agents-toolbar" style="--i: 2">
        <div class="atb-search">
          <Field label="Search">
            <TextInput v-model="search" placeholder="Question, NCT, keyword…" />
          </Field>
        </div>
        <div class="atb-seg">
          <Field label="Status">
            <Seg
              v-model="statusFilter"
              :options="[
                { value: 'all', label: 'All' },
                { value: 'verified', label: 'Verified' },
                { value: 'refined', label: 'Refined' },
                { value: 'failed', label: 'Failed' },
              ]"
            />
          </Field>
        </div>
      </div>

      <div v-if="!filteredRuns.length" class="empty" style="--i: 3">
        <Icon name="search-x" :size="24" />
        <div class="empty-title">No agent runs match</div>
        <div class="empty-body">Try adjusting the search or status filter.</div>
      </div>

      <div v-else class="rowlist" style="--i: 3">
        <RowCard
          v-for="r in filteredRuns"
          :key="r.id"
          interactive
          @click="expanded[r.id] = !expanded[r.id]"
        >
          <template #kicker>{{ r.short_id }}</template>
          <template #status>
            <Tag :variant="statusVariant(r.status)">
              <Icon :name="statusIcon(r.status)" :size="11" />&nbsp;{{ statusLabel(r.status) }}
            </Tag>
          </template>
          <template #timestamp>
            {{ ago(r.started_at) }}
            <Icon :name="expanded[r.id] ? 'chevron-up' : 'chevron-down'" :size="14" />
          </template>
          {{ r.question }}
          <template #meta>
            <span class="meta-item">
              <Icon name="quote" :size="12" />
              <span class="num">{{ r.cite_pass }}</span> citations
              <template v-if="r.status === 'refined'"> entailed after retry</template>
              <template v-else-if="r.status === 'failed'"> entailed (withheld)</template>
              <template v-else> entailed</template>
            </span>
            <span class="meta-item">
              <Icon name="refresh-cw" :size="12" />
              <span class="num">{{ r.iterations }}</span> retr{{ r.iterations === 1 ? 'y' : 'ies' }}
            </span>
            <span class="meta-item">
              <Icon name="clock" :size="12" />
              <span class="num">{{ r.latency_s.toFixed(1) }}s</span>
            </span>
            <span class="meta-item mono trials">{{ r.trials.join(' · ') }}</span>
          </template>

          <template v-if="expanded[r.id]" #expanded>
            <div class="agent-grid">
              <div
                v-for="s in r.steps"
                :key="s.name"
                class="agent-step"
                :class="stepClass(s.status)"
              >
                <div class="agent-step-head">
                  <span class="agent-step-name">
                    <Icon :name="s.status === 'ok' ? stepIcon(s.name) : (s.status === 'warn' ? 'alert-triangle' : s.status === 'fail' ? 'x' : 'refresh-cw')" :size="11" />
                    {{ s.name.toUpperCase().replace('-', ' ') }}
                  </span>
                  <span class="num agent-step-time">{{ s.time_s.toFixed(1) }}s</span>
                </div>
                <div class="agent-step-body">{{ s.summary }}</div>
                <div v-if="s.why" class="agent-step-why">{{ s.why }}</div>
              </div>
            </div>
            <div class="agent-actions">
              <Btn variant="primary" as="a" href="/workbench">
                <Icon name="arrow-right" :size="14" /> Open in Workbench
              </Btn>
              <Btn variant="secondary"><Icon name="refresh-cw" :size="14" /> Re-run</Btn>
              <Btn variant="ghost"><Icon name="file-text" :size="14" /> Raw trace</Btn>
            </div>
          </template>
        </RowCard>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page {
  padding: 20px 30px 40px;
  max-width: 1400px; margin: 0 auto;
  display: flex; flex-direction: column; gap: 20px;
}

.tabs-row { display: flex; align-items: center; }
.segtabs {
  display: inline-flex; gap: 2px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 99px;
  padding: 4px;
}
.segtab {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 16px;
  background: transparent; border: 0;
  font-family: var(--font-body); font-weight: 500;
  font-size: 13px; color: var(--color-neutral-700);
  border-radius: 99px; cursor: pointer;
  transition: background 120ms, color 120ms;
}
.segtab:hover { color: var(--color-text); background: var(--color-neutral-100); }
.segtab.is-active { background: var(--color-accent); color: #fff; }
.segtab-count {
  padding: 1px 6px; border-radius: 99px;
  font-size: 10.5px; font-weight: 600;
  background: color-mix(in srgb, currentColor 14%, transparent);
}
.segtab.is-active .segtab-count { background: color-mix(in srgb, #fff 22%, transparent); }

.loading, .empty {
  padding: 60px 20px;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  color: var(--color-neutral-500);
}
.empty-title { font-family: var(--font-heading); font-weight: 600; font-size: 18px; color: var(--color-neutral-700); }
.empty-body { font-size: 13px; }

/* ── Evaluations tab ─────────────────────────────────────── */
.ev-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 16px;
}
@media (max-width: 900px) { .ev-grid { grid-template-columns: 1fr; } }

.metric-plate {
  padding: 22px 24px 20px;
  display: flex; flex-direction: column; gap: 6px;
}
.mp-kicker {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-accent-700);
}
.mp-value {
  font-family: var(--font-heading); font-weight: 700;
  font-size: 88px; line-height: 1; color: var(--color-text);
  letter-spacing: -0.01em;
}
.mp-unit { font-size: 38px; margin-left: 4px; color: var(--color-accent-700); font-weight: 600; }
.mp-sub {
  font-size: 13px; color: var(--color-neutral-600);
  margin-top: 4px;
}
.mp-delta {
  display: inline-flex; align-items: center; gap: 5px; margin-top: 8px;
  color: var(--color-accent-800); font-size: 12px;
  padding: 4px 10px;
  background: var(--color-accent-100);
  border-radius: 99px;
  align-self: flex-start;
}
.mp-meta {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--color-divider);
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-size: 11px; color: var(--color-neutral-600);
  font-variant-numeric: tabular-nums;
}
.mp-meta b { color: var(--color-neutral-800); font-weight: 600; }
.mp-meta-dot { width: 3px; height: 3px; border-radius: 50%; background: var(--color-neutral-300); }

.hist {
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 10px;
}
.hist-head {
  display: flex; align-items: center; justify-content: space-between;
}
.hist-title {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.hist-legend { font-size: 10.5px; color: var(--color-neutral-500); }
.hist-legend b { color: var(--color-neutral-800); font-weight: 600; margin: 0 2px; }
.spark {
  width: 100%; height: 140px;
  display: block;
}
.hist-axis {
  display: flex; justify-content: space-between;
  font-size: 10px; color: var(--color-neutral-500);
  letter-spacing: 0.06em;
}

/* Eval runs table */
.section-title {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 4px 0;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}

.tbl-wrap { padding: 0; overflow: hidden; }
.tbl {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate; border-spacing: 0;
  font-family: var(--font-body); font-size: 13px;
}
.tbl .col-date     { width: 108px; }
.tbl .col-arm      { width: 108px; }
.tbl .col-pass     { width: 84px; }
.tbl .col-halluc   { width: 100px; }
.tbl .col-entail   { width: 96px; }
.tbl .col-retrieve { width: 96px; }
.tbl .col-p50      { width: 84px; }
.tbl .col-p95      { width: 84px; }

.tbl thead th {
  padding: 11px 16px;
  background: var(--color-neutral-100);
  border-bottom: 1px solid var(--color-divider);
  font-family: var(--font-body); font-weight: 600;
  font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
  text-align: left; white-space: nowrap;
}
.tbl tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-text) 6%, transparent);
  color: var(--color-neutral-800);
  vertical-align: middle;
}
.tbl tbody tr:last-child td { border-bottom: 0; }
.tbl th.right, .tbl td.right { text-align: right; }
.good { color: #1e6934; font-weight: 600; }
.meh  { color: #7a5a00; font-weight: 600; }

.arm-pill {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 72px; padding: 3px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em;
  border-radius: 99px;
  text-transform: uppercase;
}
.arm-with    { background: var(--color-accent-100); color: var(--color-accent-800); }
.arm-without { background: var(--color-neutral-200); color: var(--color-neutral-700); }
.arm-both    { background: color-mix(in srgb, #4bb26a 14%, #fff); color: #1e6934; }

/* ── Agent runs tab ──────────────────────────────────────── */
.agents-toolbar {
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 20px;
  align-items: end;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 12px;
  padding: 16px 18px;
  box-shadow: var(--shadow-sm);
}
.atb-seg { display: inline-flex; gap: 16px; align-items: end; }
@media (max-width: 900px) { .agents-toolbar { grid-template-columns: 1fr; } }

.rowlist { display: flex; flex-direction: column; gap: 10px; }

.meta-item :deep(svg) { color: var(--color-neutral-500); }
.trials { color: var(--color-neutral-500); font-size: 11px; }

/* Expanded agent-step cards (same rules as ui-kit) */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.agent-step {
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  padding: 11px 14px;
  display: flex; flex-direction: column; gap: 4px;
  border-left: 3px solid transparent;
}
.agent-step.is-warn { background: #fdf7e5; border-color: #d4a017; border-left-color: #d4a017; }
.agent-step.is-fail { background: #fbeceb; border-color: #c26b60; border-left-color: #c26b60; }
.agent-step.is-retry { border-left-color: var(--color-accent); }
.agent-step-head {
  display: flex; align-items: center; justify-content: space-between;
}
.agent-step-name {
  display: inline-flex; align-items: center; gap: 5px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-accent-800);
}
.agent-step.is-warn .agent-step-name { color: #7a5a00; }
.agent-step.is-fail .agent-step-name { color: #8b3025; }
.agent-step-time { font-size: 11.5px; color: var(--color-neutral-600); }
.agent-step-body { font-size: 12.5px; color: var(--color-neutral-700); }
.agent-step-why {
  margin-top: 4px; padding-top: 6px;
  border-top: 1px dashed var(--color-divider);
  font-size: 11.5px; line-height: 1.45; color: var(--color-neutral-600);
}
.agent-step.is-warn .agent-step-why { color: #7a5a00; border-top-color: color-mix(in srgb, #d4a017 30%, transparent); }
.agent-step.is-fail .agent-step-why { color: #8b3025; border-top-color: color-mix(in srgb, #c26b60 30%, transparent); }

.agent-actions { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
