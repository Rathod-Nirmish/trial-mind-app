<script setup lang="ts">
import { computed, ref } from 'vue';
import MessageStream from '../components/chat/MessageStream.vue';
import ComposerDock from '../components/chat/ComposerDock.vue';
import TracePanel from '../components/chat/TracePanel.vue';
import SourcesList from '../components/chat/SourcesList.vue';
import { askTrialMind } from '../services/api';
import type { Citation, TraceEvent, FinalAnswer } from '../services/types';

type Msg = { role: 'user' | 'assistant'; text: string; at?: string };

const messages = ref<Msg[]>([]);
const citations = ref<Citation[]>([]);
const traceEvents = ref<TraceEvent[]>([]);
const loading = ref(false);
const hoveredCid = ref<string | null>(null);
const startedAt = ref<number | null>(null);
const totalLatencyS = ref<number | undefined>(undefined);

const runIndex = ref(148);
const runId = computed(() => `RUN ${String(runIndex.value).padStart(4, '0')}`);
const verified = computed(() => !loading.value && citations.value.length > 0 && messages.value.at(-1)?.role === 'assistant');

const suggestions = [
  'What were the eligibility criteria for the BNT162b2 vaccine trial?',
  'Compare the primary endpoints across mRNA vaccine trials.',
  'What adverse events were reported in the remdesivir trials?',
  'Which trials studied dexamethasone for COVID-19?',
];

async function onAsk(q: string) {
  messages.value.push({ role: 'user', text: q, at: new Date().toISOString() });
  citations.value = [];
  traceEvents.value = [];
  totalLatencyS.value = undefined;
  loading.value = true;
  startedAt.value = Date.now();
  try {
    await askTrialMind(q, (kind, data) => {
      if (kind === 'trace') {
        traceEvents.value.push(data as TraceEvent);
      } else {
        const f = data as FinalAnswer;
        citations.value = f.citations;
        messages.value.push({ role: 'assistant', text: f.answer, at: new Date().toISOString() });
      }
    });
  } catch (e) {
    messages.value.push({ role: 'assistant', text: `Error: ${(e as Error).message}`, at: new Date().toISOString() });
  } finally {
    loading.value = false;
    if (startedAt.value) totalLatencyS.value = (Date.now() - startedAt.value) / 1000;
    runIndex.value++;
  }
}

function onAction(kind: 'copy' | 'export' | 'rerun', msgIndex: number) {
  const m = messages.value[msgIndex];
  if (!m) return;
  if (kind === 'copy') {
    navigator.clipboard?.writeText(m.text);
  } else if (kind === 'rerun') {
    // find preceding user turn
    for (let i = msgIndex - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') { onAsk(messages.value[i].text); break; }
    }
  }
  // 'export' left for later
}
</script>

<template>
  <div class="chat-page">
    <div class="cols">
      <!-- LEFT: Agent trace -->
      <aside class="col-trace">
        <TracePanel
          :events="traceEvents"
          :live="loading"
          :run-id="runId"
          :iterations="{ current: 0, max: 2 }"
          :total-latency-s="totalLatencyS"
          :verified="verified"
        />
      </aside>

      <!-- CENTER: Conversation + composer -->
      <section class="col-conv">
        <MessageStream
          :messages="messages"
          :loading="loading"
          :hovered-cid="hoveredCid"
          :verified="verified"
          @hover-citation="(c) => (hoveredCid = c)"
          @action="onAction"
        />
        <ComposerDock
          :loading="loading"
          :suggestions="suggestions"
          :show-suggestions="!messages.length"
          @ask="onAsk"
        />
      </section>

      <!-- RIGHT: Sources -->
      <aside class="col-sources">
        <SourcesList
          :citations="citations"
          :hovered-cid="hoveredCid"
          :retrieved-total="citations.length ? citations.length + 5 : 0"
          @hover-citation="(c) => (hoveredCid = c)"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  padding: 14px 20px 20px;
  height: 100%;
  min-height: 0;
  display: flex; flex-direction: column;
  overflow: hidden;
}

.cols {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 320px;
  gap: 14px;
  flex: 1;
  min-height: 0;
}
@media (max-width: 1200px) {
  .cols { grid-template-columns: 240px minmax(0, 1fr) 300px; gap: 10px; }
}
@media (max-width: 960px) {
  .cols { grid-template-columns: 1fr; grid-auto-rows: minmax(0, auto); }
  .col-trace, .col-sources { max-height: 40vh; }
}

/* Each column is its own scroll container — rails stay pinned, only their
 * content scrolls. Center column has non-scrolling composer at the bottom. */
.col-trace,
.col-sources {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex; flex-direction: column;
}

.col-conv {
  background: var(--color-neutral-100);
  border-radius: 12px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex; flex-direction: column;
}
</style>
