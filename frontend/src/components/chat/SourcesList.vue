<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { Citation } from '../../services/types';
import { Icon } from '../industry';

const props = defineProps<{
  citations: Citation[];
  hoveredCid?: string | null;
  retrievedTotal?: number; // may exceed citations.length (uncited chunks)
}>();
defineEmits<{ (e: 'hover-citation', cid: string | null): void }>();

const shortIdOf = (idx: number) => `c${idx + 1}`;

const highlightedIdx = computed(() =>
  props.hoveredCid ? props.citations.findIndex((_, i) => shortIdOf(i) === props.hoveredCid) : -1
);

const uncitedCount = computed(() => {
  const total = props.retrievedTotal ?? props.citations.length;
  return Math.max(0, total - props.citations.length);
});

const showUncited = ref(false);
const refs = ref<(HTMLElement | null)[]>([]);

watch(highlightedIdx, (i) => {
  if (i < 0) return;
  refs.value[i]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});
</script>

<template>
  <div class="sources">
    <div class="sources-head">
      <span class="sources-title">SOURCES</span>
      <span class="sources-count mono">
        {{ citations.length }}&nbsp;CITED
        <template v-if="retrievedTotal && retrievedTotal > citations.length">
          / {{ retrievedTotal }}&nbsp;RETRIEVED
        </template>
      </span>
    </div>

    <div v-if="!citations.length" class="sources-empty">
      <Icon name="quote" :size="18" />
      <div>Sources appear here as the analyzer runs</div>
    </div>

    <div
      v-for="(c, i) in citations"
      :key="c.chunk_id"
      :ref="(el) => (refs[i] = el as HTMLElement)"
      class="src-card cited"
      :class="{ 'is-hot': highlightedIdx === i }"
      @mouseenter="$emit('hover-citation', shortIdOf(i))"
      @mouseleave="$emit('hover-citation', null)"
    >
      <div class="src-head">
        <span class="src-cid">{{ shortIdOf(i) }}</span>
        <span class="src-nct mono">{{ c.trial_id }}</span>
        <span class="src-tag cited">CITED</span>
        <span class="src-score mono">{{ c.score.toFixed(2) }}</span>
      </div>
      <div class="src-body">"{{ c.text }}"</div>
      <div class="src-foot">
        <span class="src-section">{{ (c.section ?? '—').toUpperCase() }}</span>
        <span class="src-bar"><i :style="{ width: `${Math.round(c.score * 100)}%` }" /></span>
      </div>
    </div>

    <button
      v-if="uncitedCount > 0"
      class="src-uncited"
      @click="showUncited = !showUncited"
    >
      <Icon :name="showUncited ? 'chevron-up' : 'chevron-down'" :size="12" />
      {{ showUncited ? 'Hide' : 'Show' }} {{ uncitedCount }} uncited chunk<span v-if="uncitedCount !== 1">s</span>
    </button>
  </div>
</template>

<style scoped>
.sources {
  display: flex; flex-direction: column; gap: 10px;
  padding: 14px;
  overflow-y: auto;
  height: 100%;
  min-height: 0;
  scroll-behavior: smooth;
  background:
    linear-gradient(#fff 30%, rgba(255,255,255,0)) center top,
    linear-gradient(rgba(255,255,255,0), #fff 70%) center bottom,
    radial-gradient(farthest-side at 50% 0, rgba(0,0,0,0.08), rgba(0,0,0,0)) center top,
    radial-gradient(farthest-side at 50% 100%, rgba(0,0,0,0.08), rgba(0,0,0,0)) center bottom;
  background-repeat: no-repeat;
  background-size: 100% 24px, 100% 24px, 100% 8px, 100% 8px;
  background-attachment: local, local, scroll, scroll;
}

.sources-head {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-divider);
  margin-bottom: 2px;
}
.sources-title {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.sources-count {
  font-size: 9.5px; letter-spacing: 0.08em;
  color: var(--color-neutral-500);
}

.sources-empty {
  margin: auto; text-align: center; color: var(--color-neutral-500);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  font-size: 12.5px; padding: 40px 20px;
}

.src-card {
  padding: 12px 14px;
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  background: #fff;
  display: flex; flex-direction: column; gap: 8px;
  transition: border-color 140ms, background 140ms;
}
.src-card.cited { border-color: color-mix(in srgb, var(--color-accent) 35%, var(--color-divider)); }
.src-card:hover, .src-card.is-hot {
  border-color: var(--color-accent);
  background: color-mix(in srgb, var(--color-accent) 4%, #fff);
}

.src-head { display: flex; align-items: center; gap: 7px; }
.src-cid {
  display: inline-grid; place-items: center;
  min-width: 22px; padding: 1px 7px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; font-weight: 600;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
}
.src-nct { font-size: 10.5px; color: var(--color-accent-700); font-weight: 600; }
.src-tag {
  padding: 1px 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 9.5px; font-weight: 600; letter-spacing: 0.04em;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
}
.src-score {
  margin-left: auto;
  font-size: 11px; color: var(--color-neutral-600);
}
.src-body {
  font-size: 12px; line-height: 1.55;
  color: var(--color-neutral-800);
  margin: 0;
}
.src-foot {
  display: flex; align-items: center; gap: 10px;
  padding-top: 4px;
  border-top: 1px dashed var(--color-divider);
}
.src-section {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9px; letter-spacing: 0.14em;
  color: var(--color-neutral-600);
}
.src-bar {
  flex: 1; height: 4px; background: var(--color-neutral-200);
  border-radius: 99px; overflow: hidden;
}
.src-bar i {
  display: block; height: 100%;
  background: var(--color-accent);
  border-radius: 99px;
}

.src-uncited {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 14px;
  background: transparent;
  border: 1px dashed var(--color-neutral-400);
  border-radius: 10px;
  color: var(--color-neutral-700);
  font-family: var(--font-body); font-weight: 500;
  font-size: 12px; cursor: pointer;
  transition: color 120ms, border-color 120ms, background 120ms;
}
.src-uncited:hover {
  color: var(--color-accent-700);
  border-color: var(--color-accent);
  background: var(--color-accent-100);
}
</style>
