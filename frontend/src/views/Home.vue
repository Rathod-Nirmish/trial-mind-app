<script setup lang="ts">
import { computed, ref } from 'vue';
import MessageStream from '../components/chat/MessageStream.vue';
import ComposerDock from '../components/chat/ComposerDock.vue';
import TracePanel from '../components/chat/TracePanel.vue';
import SourcesList from '../components/chat/SourcesList.vue';
import { askTrialMind } from '../services/api';
import type { Citation, TraceEvent, FinalAnswer } from '../services/types';

type Msg = {
  role: 'user' | 'assistant';
  text: string;
  at?: string;
  citations?: Citation[];
  traceEvents?: TraceEvent[];
  latencyS?: number;
  runId?: string;
  loading?: boolean;
  error?: boolean;
};

const messages = ref<Msg[]>([]);
const selectedIndex = ref<number | null>(null);
const hoveredCid = ref<string | null>(null);

const runCounter = ref(148);

const lastAssistantIndex = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant') return i;
  }
  return null;
});

const activeIndex = computed(() => selectedIndex.value ?? lastAssistantIndex.value);
const activeMsg = computed(() => (activeIndex.value != null ? messages.value[activeIndex.value] : null));
const activeCitations = computed(() => activeMsg.value?.citations ?? []);
const activeTrace = computed(() => activeMsg.value?.traceEvents ?? []);
const activeLoading = computed(() => activeMsg.value?.loading === true);

// Find the preceding user question for the active assistant message
const activeQuestion = computed(() => {
  const i = activeIndex.value;
  if (i == null) return '';
  for (let j = i - 1; j >= 0; j--) {
    if (messages.value[j].role === 'user') return messages.value[j].text;
  }
  return '';
});

const isPinned = computed(
  () => selectedIndex.value != null && selectedIndex.value !== lastAssistantIndex.value,
);
const hasNewerAnswer = computed(
  () => isPinned.value && lastAssistantIndex.value != null,
);

const verified = computed(
  () =>
    !!activeMsg.value &&
    !activeMsg.value.loading &&
    !activeMsg.value.error &&
    (activeMsg.value.citations?.length ?? 0) > 0,
);

const activeRunId = computed(() => activeMsg.value?.runId ?? `RUN ${String(runCounter.value).padStart(4, '0')}`);
const activeLatency = computed(() => activeMsg.value?.latencyS);
const retrievedTotal = computed(() =>
  activeCitations.value.length ? activeCitations.value.length + 5 : 0,
);

const suggestions = [
  'What were the eligibility criteria for the BNT162b2 vaccine trial?',
  'Compare the primary endpoints across mRNA vaccine trials.',
  'What adverse events were reported in the remdesivir trials?',
  'Which trials studied dexamethasone for COVID-19?',
];

async function onAsk(q: string) {
  messages.value.push({ role: 'user', text: q, at: new Date().toISOString() });

  runCounter.value++;
  const runId = `RUN ${String(runCounter.value).padStart(4, '0')}`;
  const placeholder: Msg = {
    role: 'assistant',
    text: '',
    at: new Date().toISOString(),
    citations: [],
    traceEvents: [],
    loading: true,
    runId,
  };
  messages.value.push(placeholder);
  const msgIndex = messages.value.length - 1;
  const startedAt = Date.now();

  try {
    await askTrialMind(q, (kind, data) => {
      const m = messages.value[msgIndex];
      if (!m) return;
      if (kind === 'trace') {
        m.traceEvents = [...(m.traceEvents ?? []), data as TraceEvent];
      } else {
        const f = data as FinalAnswer;
        m.text = f.answer;
        m.citations = f.citations;
      }
    });
  } catch (e) {
    const m = messages.value[msgIndex];
    if (m) {
      m.text = `Error: ${(e as Error).message}`;
      m.error = true;
    }
  } finally {
    const m = messages.value[msgIndex];
    if (m) {
      m.loading = false;
      m.latencyS = (Date.now() - startedAt) / 1000;
    }
  }
}

function onAction(kind: 'copy' | 'export' | 'rerun', msgIndex: number) {
  const m = messages.value[msgIndex];
  if (!m) return;
  if (kind === 'copy') {
    navigator.clipboard?.writeText(m.text);
  } else if (kind === 'rerun') {
    for (let i = msgIndex - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') {
        onAsk(messages.value[i].text);
        break;
      }
    }
  }
}

function onSelectMessage(i: number) {
  if (i === lastAssistantIndex.value) {
    selectedIndex.value = null;
  } else {
    selectedIndex.value = i;
  }
}

function onSelectCitation(payload: { index: number; cid: string }) {
  onSelectMessage(payload.index);
  hoveredCid.value = payload.cid;
}

function onUnpin() {
  selectedIndex.value = null;
}
</script>

<template>
  <div class="chat-page">
    <div class="cols">
      <!-- LEFT: Agent trace -->
      <aside class="col-trace">
        <TracePanel
          :events="activeTrace"
          :live="activeLoading"
          :run-id="activeRunId"
          :iterations="{ current: 0, max: 2 }"
          :total-latency-s="activeLatency"
          :verified="verified"
          :is-pinned="isPinned"
          :has-newer-answer="hasNewerAnswer"
          @unpin="onUnpin"
        />
      </aside>

      <!-- CENTER: Conversation + composer -->
      <section class="col-conv">
        <MessageStream
          :messages="messages"
          :loading="activeLoading && !isPinned"
          :hovered-cid="hoveredCid"
          :verified="verified"
          :selected-index="activeIndex"
          @hover-citation="(c) => (hoveredCid = c)"
          @action="onAction"
          @select-message="onSelectMessage"
          @select-citation="onSelectCitation"
        />
        <ComposerDock
          :loading="activeLoading"
          :suggestions="suggestions"
          :show-suggestions="!messages.length"
          @ask="onAsk"
        />
      </section>

      <!-- RIGHT: Sources -->
      <aside class="col-sources">
        <SourcesList
          :citations="activeCitations"
          :hovered-cid="hoveredCid"
          :retrieved-total="retrievedTotal"
          :question-text="activeQuestion"
          :is-pinned="isPinned"
          :has-newer-answer="hasNewerAnswer"
          @hover-citation="(c) => (hoveredCid = c)"
          @unpin="onUnpin"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  padding: 14px 16px 16px;
  height: 100%;
  min-height: 0;
  display: flex; flex-direction: column;
  overflow: hidden;
}

.cols {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 320px;
  gap: 6px 8px;
  flex: 1;
  min-height: 0;
}
@media (max-width: 1200px) {
  .cols { grid-template-columns: 220px minmax(0, 1fr) 300px; gap: 6px; }
}
@media (max-width: 960px) {
  .cols { grid-template-columns: 1fr; grid-auto-rows: minmax(0, auto); }
  .col-trace, .col-sources { max-height: 40vh; }
}

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
