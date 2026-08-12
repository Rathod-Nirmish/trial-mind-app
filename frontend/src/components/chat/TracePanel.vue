<script setup lang="ts">
import { computed } from 'vue';
import type { TraceEvent } from '../../services/types';
import { Icon } from '../industry';
import Loader from '../industry/Loader.vue';

const props = defineProps<{
  events: TraceEvent[];
  live?: boolean;
  runId?: string;
  model?: string;
  iterations?: { current: number; max: number };
  totalLatencyS?: number;
  verified?: boolean;
  isPinned?: boolean;
  hasNewerAnswer?: boolean;
}>();
defineEmits<{ (e: 'unpin'): void }>();

// Fold multiple events per agent into a single step. Ordering is fixed.
const steps = computed(() => {
  const order = ['retriever', 'analyzer', 'citation-checker'];
  const iconFor: Record<string, string> = {
    retriever: 'search',
    analyzer: 'pen-tool',
    'citation-checker': 'shield-check',
  };
  const grouped = new Map<string, TraceEvent[]>();
  for (const ev of props.events) {
    const key = ev.agent.toLowerCase();
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(ev);
  }
  return order
    .filter((k) => grouped.has(k))
    .map((k) => {
      const list = grouped.get(k)!;
      const t0 = new Date(list[0].at).getTime();
      const t1 = new Date(list[list.length - 1].at).getTime();
      const dt = (t1 - t0) / 1000;
      return {
        key: k,
        name: k.replace(/-/g, ' ').toUpperCase(),
        icon: iconFor[k] ?? 'circle',
        time: dt > 0 ? `${dt.toFixed(1)}s` : '—',
        summary: list[list.length - 1].summary,
        done: true,
      };
    });
});

const activeAgent = computed(() => {
  if (!props.live) return null;
  const known = new Set(steps.value.map((s) => s.key));
  if (!known.has('retriever')) return 'retriever';
  if (!known.has('analyzer')) return 'analyzer';
  if (!known.has('citation-checker')) return 'citation-checker';
  return null;
});
</script>

<template>
  <div class="tp">
    <div class="tp-head">
      <div class="tp-head-row">
        <span class="tp-title">AGENT TRACE</span>
        <span v-if="runId" class="tp-run mono">{{ runId }}</span>
      </div>
      <div v-if="isPinned" class="tp-pins">
        <button class="pin-chip" @click="$emit('unpin')" title="Return to latest answer">
          <Icon name="arrow-left" :size="10" /> latest
        </button>
        <button
          v-if="hasNewerAnswer"
          class="pin-chip pin-chip-new"
          @click="$emit('unpin')"
          title="A newer answer is available"
        >
          new answer <Icon name="arrow-down" :size="10" />
        </button>
      </div>
    </div>

    <div v-if="!events.length && !live" class="tp-empty">
      <Icon name="workflow" :size="18" />
      <div>Trace appears here as the graph runs</div>
    </div>

    <template v-else>
      <div v-for="s in steps" :key="s.key" class="tp-step">
        <span class="tp-step-icon">
          <Icon :name="s.icon" :size="14" />
        </span>
        <div class="tp-step-body">
          <div class="tp-step-head">
            <span class="tp-step-name">{{ s.name }}</span>
            <Icon name="check" :size="12" class="tp-step-check" />
            <span class="tp-step-time mono">{{ s.time }}</span>
          </div>
          <div class="tp-step-note">{{ s.summary }}</div>
        </div>
      </div>

      <div v-if="activeAgent" class="tp-step is-live">
        <span class="tp-step-icon is-live">
          <Loader variant="dots" :size="9" tone="accent" />
        </span>
        <div class="tp-step-body">
          <div class="tp-step-head">
            <span class="tp-step-name">{{ activeAgent.replace('-', ' ').toUpperCase() }}</span>
            <span class="tp-step-time mono">…</span>
          </div>
          <div class="tp-step-note">Running…</div>
        </div>
      </div>
    </template>

    <div class="tp-meta" v-if="events.length || live">
      <div class="tp-meta-row">
        <span>Iterations</span>
        <span class="mono">{{ iterations?.current ?? 0 }} / {{ iterations?.max ?? 2 }}</span>
      </div>
      <div class="tp-meta-row">
        <span>Model</span>
        <span class="mono">{{ model ?? 'gemini-2.5-pro' }}</span>
      </div>
      <div class="tp-meta-row">
        <span>Total latency</span>
        <span class="mono">{{ totalLatencyS ? `${totalLatencyS.toFixed(1)}s` : '—' }}</span>
      </div>
    </div>

    <div v-if="verified" class="tp-verified">
      <Icon name="check" :size="11" />
      ANSWER VERIFIED
    </div>
  </div>
</template>

<style scoped>
.tp {
  display: flex; flex-direction: column; gap: 10px;
  padding: 14px;
  overflow-y: auto;
  height: 100%;
  min-height: 0;
  scroll-behavior: smooth;
  /* Scroll-shadow — hints there's more content */
  background:
    linear-gradient(#fff 30%, rgba(255,255,255,0)) center top,
    linear-gradient(rgba(255,255,255,0), #fff 70%) center bottom,
    radial-gradient(farthest-side at 50% 0, rgba(0,0,0,0.08), rgba(0,0,0,0)) center top,
    radial-gradient(farthest-side at 50% 100%, rgba(0,0,0,0.08), rgba(0,0,0,0)) center bottom;
  background-repeat: no-repeat;
  background-size: 100% 24px, 100% 24px, 100% 8px, 100% 8px;
  background-attachment: local, local, scroll, scroll;
}

.tp-head {
  display: flex; flex-direction: column; gap: 6px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-divider);
  margin-bottom: 2px;
}
.tp-head-row {
  display: flex; align-items: center; justify-content: space-between;
}
.tp-pins {
  display: flex; gap: 6px; flex-wrap: wrap;
  margin-top: 2px;
}
.pin-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--color-accent-800);
  background: var(--color-accent-100);
  border: 1px solid var(--color-accent-300);
  border-radius: 99px;
  cursor: pointer;
  transition: background 120ms, color 120ms, border-color 120ms;
}
.pin-chip:hover {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
}
.pin-chip-new {
  background: #fff;
  border-color: var(--color-accent);
}
.tp-title {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.tp-run {
  font-size: 9.5px; letter-spacing: 0.08em;
  color: var(--color-neutral-500);
}

.tp-empty {
  margin: auto; text-align: center; color: var(--color-neutral-500);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  font-size: 12.5px; padding: 40px 12px;
}

.tp-step {
  display: grid; grid-template-columns: 28px 1fr; gap: 10px;
  padding: 10px 2px;
  border-bottom: 1px solid var(--color-divider);
  animation: step-in 220ms ease-out both;
}
.tp-step:last-of-type { border-bottom: 0; }
@keyframes step-in { from { opacity: 0; transform: translateX(-3px); } to { opacity: 1; transform: none; } }

.tp-step-icon {
  width: 28px; height: 28px; border-radius: 8px;
  background: var(--color-accent-100);
  color: var(--color-accent-700);
  display: inline-grid; place-items: center;
}
.tp-step-icon.is-live {
  background: #fff;
  border: 1px dashed var(--color-accent);
}

.tp-step-body { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.tp-step-head { display: flex; align-items: center; gap: 6px; }
.tp-step-name {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-accent-800);
}
.tp-step-check { color: var(--color-accent-700); flex: none; }
.tp-step-time {
  margin-left: auto;
  font-size: 11px; color: var(--color-neutral-600);
}
.tp-step-note {
  font-size: 11.5px; line-height: 1.5; color: var(--color-neutral-700);
}

.tp-meta {
  margin-top: 8px; padding: 12px 14px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  display: flex; flex-direction: column; gap: 8px;
}
.tp-meta-row {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: 11px; color: var(--color-neutral-600);
}
.tp-meta-row .mono {
  color: var(--color-neutral-800); font-size: 11.5px;
}

.tp-verified {
  align-self: flex-start;
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 700;
  font-size: 10px; letter-spacing: 0.14em;
  margin-top: 6px;
}
</style>
