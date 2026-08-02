<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";
import ChatPanel from "../components/ChatPanel.vue";
import CitationsPanel from "../components/CitationsPanel.vue";
import AgentTracePanel from "../components/AgentTracePanel.vue";
import { askTrialMind } from "../services/api";
import type { Citation, TraceEvent, FinalAnswer } from "../services/types";

const messages = ref<{ role: "user" | "assistant"; text: string }[]>([]);
const citations = ref<Citation[]>([]);
const traceEvents = ref<TraceEvent[]>([]);
const loading = ref(false);
const hoveredCid = ref<string | null>(null);

const suggestions = [
  "What were the eligibility criteria for the BNT162b2 vaccine trial?",
  "Compare the primary endpoints across mRNA vaccine trials.",
  "What adverse events were reported in the remdesivir trials?",
  "Which trials studied dexamethasone for COVID-19?",
];

async function onAsk(q: string) {
  messages.value.push({ role: "user", text: q });
  citations.value = [];
  traceEvents.value = [];
  loading.value = true;
  try {
    await askTrialMind(q, (kind, data) => {
      if (kind === "trace") traceEvents.value.push(data as TraceEvent);
      else {
        const f = data as FinalAnswer;
        citations.value = f.citations;
        messages.value.push({ role: "assistant", text: f.answer });
      }
    });
  } catch (e) {
    messages.value.push({ role: "assistant", text: `Error: ${(e as Error).message}` });
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50 text-slate-900">
    <header class="border-b bg-white px-6 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold">TrialMind</h1>
        <p class="text-sm text-slate-500">Multi-agent clinical research assistant</p>
      </div>
      <RouterLink to="/ui-kit" class="text-xs text-slate-500 hover:text-slate-900 underline">
        UI kit →
      </RouterLink>
    </header>
    <main class="flex-1 p-4 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">
      <div class="lg:col-span-1 min-h-[400px]">
        <ChatPanel
          :messages="messages"
          :loading="loading"
          :suggestions="suggestions"
          @ask="onAsk"
          @hover-citation="(cid) => (hoveredCid = cid)" />
      </div>
      <div class="lg:col-span-1 min-h-[400px]">
        <CitationsPanel :citations="citations" :hovered-cid="hoveredCid" />
      </div>
      <div class="lg:col-span-1 min-h-[400px]">
        <AgentTracePanel :events="traceEvents" />
      </div>
    </main>
    <footer class="border-t bg-white px-6 py-3 text-xs text-slate-500">
      TrialMind is a portfolio demo, not a medical decision-support tool.
    </footer>
  </div>
</template>
