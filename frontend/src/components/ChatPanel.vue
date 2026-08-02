<script setup lang="ts">
import { ref, computed } from "vue";
import { marked } from "marked";

const props = defineProps<{
  messages: { role: "user" | "assistant"; text: string }[];
  loading: boolean;
  suggestions?: string[];
}>();
const emit = defineEmits<{
  (e: "ask", q: string): void;
  (e: "hover-citation", cid: string | null): void;
}>();

const draft = ref("");
function submit() {
  const q = draft.value.trim();
  if (!q || props.loading) return;
  emit("ask", q);
  draft.value = "";
}
function pickSuggestion(s: string) {
  if (props.loading) return;
  emit("ask", s);
}

marked.setOptions({ breaks: true, gfm: true });

function renderAssistant(text: string): string {
  const html = marked.parse(text) as string;
  // Matches [c1] or [c1, c7] or [c1,c2,c3] — splits grouped brackets into
  // adjacent single spans so hover works on each cid.
  return html.replace(
    /\[\s*(c\d+(?:\s*,\s*c\d+)*)\s*\]/g,
    (_full, group: string) => {
      const cids = group.match(/c\d+/g) ?? [];
      return cids
        .map((cid) => `<span class="cite" data-cid="${cid}">[${cid}]</span>`)
        .join("");
    },
  );
}

const rendered = computed(() =>
  props.messages.map((m) =>
    m.role === "assistant" ? { ...m, html: renderAssistant(m.text) } : { ...m, html: "" },
  ),
);

function onMouseOver(e: MouseEvent) {
  const t = e.target as HTMLElement;
  if (t?.dataset?.cid) emit("hover-citation", t.dataset.cid);
}
function onMouseOut(e: MouseEvent) {
  const t = e.target as HTMLElement;
  if (t?.dataset?.cid) emit("hover-citation", null);
}
</script>

<template>
  <div class="flex flex-col h-full border rounded-lg bg-white">
    <div class="flex-1 overflow-y-auto p-4 space-y-3"
         @mouseover="onMouseOver" @mouseout="onMouseOut">
      <div v-for="(m, i) in rendered" :key="i"
           :class="m.role === 'user' ? 'text-right' : ''">
        <div class="inline-block max-w-[85%] rounded-lg px-3 py-2 text-left"
             :class="m.role === 'user' ? 'bg-slate-900 text-white' : 'bg-slate-100'">
          <template v-if="m.role === 'assistant'">
            <div class="md-body text-sm" v-html="m.html" />
          </template>
          <template v-else>
            <pre class="whitespace-pre-wrap font-sans text-sm m-0">{{ m.text }}</pre>
          </template>
        </div>
      </div>
      <div v-if="loading" class="text-xs text-slate-500">thinking…</div>
    </div>

    <div v-if="!messages.length && suggestions?.length"
         class="border-t px-3 py-2 flex flex-wrap gap-2">
      <button v-for="s in suggestions" :key="s"
              type="button"
              class="text-xs bg-slate-100 hover:bg-slate-200 rounded-full px-3 py-1 text-slate-700"
              :disabled="loading"
              @click="pickSuggestion(s)">
        {{ s }}
      </button>
    </div>

    <form class="border-t p-3 flex gap-2" @submit.prevent="submit">
      <input v-model="draft"
             class="flex-1 border rounded px-3 py-2 text-sm"
             placeholder="Ask about clinical trials…"
             :disabled="loading" />
      <button class="bg-slate-900 text-white rounded px-4 py-2 text-sm disabled:opacity-50"
              :disabled="loading">Ask</button>
    </form>
  </div>
</template>

<style scoped>
:deep(.md-body p) { margin: 0.5rem 0; }
:deep(.md-body p:first-child) { margin-top: 0; }
:deep(.md-body p:last-child) { margin-bottom: 0; }
:deep(.md-body ul), :deep(.md-body ol) { margin: 0.5rem 0; padding-left: 1.25rem; }
:deep(.md-body ul) { list-style: disc; }
:deep(.md-body ol) { list-style: decimal; }
:deep(.md-body li) { margin: 0.15rem 0; }
:deep(.md-body strong) { font-weight: 600; }
:deep(.md-body em) { font-style: italic; }
:deep(.md-body code) {
  background: #e2e8f0;
  padding: 0 4px;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
  font-size: 0.85em;
}

:deep(.cite) {
  display: inline-block;
  padding: 0 4px;
  border-radius: 4px;
  background: #fef3c7;
  color: #92400e;
  font-family: ui-monospace, monospace;
  font-size: 0.8em;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 120ms, border-color 120ms;
}
:deep(.cite:hover) {
  background: #fde68a;
  border-color: #f59e0b;
}
</style>
