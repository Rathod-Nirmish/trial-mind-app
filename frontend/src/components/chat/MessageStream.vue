<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { marked } from 'marked';
import { Icon } from '../industry';
import Loader from '../industry/Loader.vue';
import type { Citation, TraceEvent } from '../../services/types';

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

const props = defineProps<{
  messages: Msg[];
  loading: boolean;
  hoveredCid?: string | null;
  verified?: boolean;
  selectedIndex?: number | null;
}>();
const emit = defineEmits<{
  (e: 'hover-citation', cid: string | null): void;
  (e: 'action', kind: 'copy' | 'export' | 'rerun', msgIndex: number): void;
  (e: 'select-message', index: number): void;
  (e: 'select-citation', payload: { index: number; cid: string }): void;
}>();

marked.setOptions({ breaks: true, gfm: true });

function renderAssistant(text: string): string {
  const html = marked.parse(text) as string;
  return html.replace(
    /\[\s*(c\d+(?:\s*,\s*c\d+)*)\s*\]/g,
    (_full, group: string) => {
      const cids = group.match(/c\d+/g) ?? [];
      return cids
        .map((cid) => `<span class="cite" data-cid="${cid}">${cid}</span>`)
        .join('');
    },
  );
}

const rendered = computed(() =>
  props.messages.map((m) =>
    m.role === 'assistant' ? { ...m, html: renderAssistant(m.text) } : { ...m, html: '' },
  ),
);

function timeOf(m: Msg): string {
  const d = m.at ? new Date(m.at) : new Date();
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

function findCardIndex(target: EventTarget | null): number | null {
  let el = target as HTMLElement | null;
  while (el) {
    if (el.dataset && el.dataset.msgIndex != null) return Number(el.dataset.msgIndex);
    el = el.parentElement;
  }
  return null;
}

function onMouseOver(e: MouseEvent) {
  const t = e.target as HTMLElement;
  if (t?.dataset?.cid) {
    const i = findCardIndex(t);
    if (i != null && i === props.selectedIndex) emit('hover-citation', t.dataset.cid);
  }
}
function onMouseOut(e: MouseEvent) {
  const t = e.target as HTMLElement;
  if (t?.dataset?.cid) emit('hover-citation', null);
}
function onClickBody(e: MouseEvent) {
  const t = e.target as HTMLElement;
  if (t?.dataset?.cid) {
    const i = findCardIndex(t);
    if (i != null) {
      emit('select-citation', { index: i, cid: t.dataset.cid });
      e.stopPropagation();
    }
  }
}

function onCardClick(i: number) {
  emit('select-message', i);
}
function onCardKey(e: KeyboardEvent, i: number) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    emit('select-message', i);
  }
}

const scrollEl = ref<HTMLElement | null>(null);
watch(() => props.messages.length, async () => {
  await nextTick();
  scrollEl.value?.scrollTo({ top: scrollEl.value.scrollHeight, behavior: 'smooth' });
});
</script>

<template>
  <div ref="scrollEl" class="stream" @mouseover="onMouseOver" @mouseout="onMouseOut">
    <div v-if="!messages.length" class="stream-empty">
      <div class="stream-empty-mark">
        <Icon name="brain" :size="26" />
      </div>
      <div class="stream-empty-title">Ask a question about your corpus</div>
      <div class="stream-empty-body">
        The assistant retrieves supporting chunks, drafts an answer, and validates
        every citation before you see it. Try a suggestion below or type your own.
      </div>
    </div>

    <template v-for="(m, i) in rendered" :key="i">
      <!-- USER TURN -->
      <div v-if="m.role === 'user'" class="turn turn-user">
        <div class="user-bubble">{{ m.text }}</div>
        <div class="avatar avatar-user">
          <Icon name="user" :size="14" />
        </div>
      </div>

      <!-- ASSISTANT TURN -->
      <div v-else class="turn turn-assist">
        <div class="avatar avatar-assist">
          <Icon name="brain" :size="18" />
        </div>
        <div
          class="assist-card"
          :class="{ 'is-selected': i === selectedIndex, 'is-live': m.loading, 'is-error': m.error }"
          :data-msg-index="i"
          role="button"
          tabindex="0"
          :aria-pressed="i === selectedIndex"
          @click="onCardClick(i)"
          @keydown="(e) => onCardKey(e, i)"
        >
          <div class="assist-head">
            <span class="assist-name">TRIALMIND</span>
            <span v-if="m.loading" class="live-badge">
              <span class="live-dot" />
              LIVE
            </span>
            <span v-else-if="i === selectedIndex && verified" class="verified-badge">
              <Icon name="check" :size="10" />
              VERIFIED
            </span>
            <span class="assist-time mono">{{ timeOf(m) }}</span>
          </div>

          <div
            v-if="m.loading && !m.text"
            class="thinking"
          >
            <Loader variant="dots" :size="14" />
            <span>Retrieving · analyzing · verifying citations…</span>
          </div>
          <div
            v-else
            class="assist-body"
            :class="{ 'has-hover': hoveredCid && i === selectedIndex }"
            v-html="m.html"
            @click="onClickBody"
          />

          <div v-if="!m.loading" class="assist-actions" @click.stop>
            <button class="mini-btn" @click="$emit('action', 'copy', i)"><Icon name="copy" :size="12" /> Copy</button>
            <button class="mini-btn" @click="$emit('action', 'export', i)"><Icon name="download" :size="12" /> Export</button>
            <button class="mini-btn" @click="$emit('action', 'rerun', i)"><Icon name="refresh-cw" :size="12" /> Re-run</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.stream {
  flex: 1; overflow-y: auto;
  min-height: 0;
  padding: 22px 14px;
  display: flex; flex-direction: column; gap: 22px;
  scroll-behavior: smooth;
}

.stream-empty {
  margin: auto; text-align: center; max-width: 520px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  color: var(--color-neutral-600);
  padding: 40px 20px;
}
.stream-empty-mark {
  width: 48px; height: 48px; display: grid; place-items: center;
  border-radius: 12px;
  background: linear-gradient(160deg, #7ba7d9 0%, #3d6fa8 55%, #2a5590 100%);
  color: #fff; margin-bottom: 6px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 2px 6px rgba(30, 60, 110, 0.25);
}
.stream-empty-title {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 22px; letter-spacing: 0.01em; color: var(--color-text);
}
.stream-empty-body { font-size: 13.5px; line-height: 1.6; }

.turn {
  display: flex; gap: 10px;
  animation: turn-in 260ms cubic-bezier(.22,.68,.35,1) both;
}
@keyframes turn-in { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }

.turn-user  { align-self: flex-end;   max-width: 96%; }
.turn-assist { align-self: flex-start; max-width: 100%; width: 100%; }

.avatar {
  width: 34px; height: 34px; flex: none;
  border-radius: 10px;
  display: inline-grid; place-items: center;
}
.avatar-user   { background: var(--color-neutral-200); color: var(--color-neutral-700); }
.avatar-assist {
  background: linear-gradient(160deg, #7ba7d9 0%, #3d6fa8 55%, #2a5590 100%);
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 1px 2px rgba(30, 60, 110, 0.25);
}

.user-bubble {
  background: var(--color-accent); color: #fff;
  padding: 12px 16px;
  border-radius: 14px 14px 3px 14px;
  box-shadow: var(--shadow-sm);
  font-size: 14px; line-height: 1.6;
}
.assist-card {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-left: 3px solid transparent;
  border-radius: 3px 14px 14px 14px;
  padding: 18px 22px;
  display: flex; flex-direction: column; gap: 12px;
  box-shadow: var(--shadow-md);
  min-width: 0;
  cursor: pointer;
  transition: border-color 140ms, box-shadow 140ms;
  outline: none;
}
.assist-card:focus-visible {
  box-shadow: var(--shadow-md), 0 0 0 2px color-mix(in srgb, var(--color-accent) 40%, transparent);
}
.assist-card.is-selected {
  border-left-color: var(--color-accent);
}
.assist-card.is-error { border-left-color: #c94a4a; }

.assist-head {
  display: flex; align-items: center; gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-divider);
}
.assist-name {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 13px; letter-spacing: 0.06em;
  color: var(--color-accent-800);
}
.verified-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 9px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 500;
  font-size: 10px; letter-spacing: 0.06em;
}
.live-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 9px;
  background: color-mix(in srgb, var(--color-accent) 14%, #fff);
  color: var(--color-accent-800);
  border: 1px solid var(--color-accent-300);
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 9.5px; letter-spacing: 0.14em;
}
.live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--color-accent);
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.4); opacity: 0.5; } }

.assist-time {
  margin-left: auto;
  font-size: 11px; color: var(--color-neutral-500);
}
.assist-body {
  font-size: 14px; line-height: 1.7;
  color: var(--color-text);
  text-wrap: pretty;
}

.assist-actions {
  display: flex; gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--color-divider);
}
.mini-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 8px;
  background: transparent; border: 1px solid var(--color-divider);
  color: var(--color-neutral-700);
  font-family: var(--font-body); font-weight: 500;
  font-size: 12px; cursor: pointer;
  transition: background 120ms, border-color 120ms, color 120ms;
}
.mini-btn:hover {
  background: var(--color-neutral-100);
  border-color: color-mix(in srgb, var(--color-text) 25%, transparent);
  color: var(--color-text);
}

.thinking {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 12.5px; color: var(--color-neutral-600);
  padding: 4px 2px;
}

:deep(.assist-body p) { margin: 0 0 12px; }
:deep(.assist-body p:last-child) { margin-bottom: 0; }
:deep(.assist-body ul), :deep(.assist-body ol) { margin: 0.5em 0; padding-left: 1.4em; }
:deep(.assist-body ul) { list-style: disc; }
:deep(.assist-body ol) { list-style: decimal; }
:deep(.assist-body li) { margin: 0.2em 0; }
:deep(.assist-body strong) { font-weight: 600; }
:deep(.assist-body em) { font-style: italic; }
:deep(.assist-body code) {
  background: var(--color-neutral-100);
  padding: 1px 5px; border-radius: 4px;
  font-family: ui-monospace, monospace; font-size: 0.9em;
}

:deep(.cite) {
  display: inline-block;
  padding: 1px 7px; margin: 0 2px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; font-weight: 600;
  color: var(--color-accent-800);
  background: var(--color-accent-100);
  border-radius: 99px;
  vertical-align: 1px;
  cursor: pointer;
  transition: background 120ms, color 120ms;
}
:deep(.cite:hover) { background: var(--color-accent); color: #fff; }
</style>
