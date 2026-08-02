<script setup lang="ts">
import { computed } from "vue";
import type { Citation } from "../services/types";

const props = defineProps<{
  citations: Citation[];
  hoveredCid?: string | null;
}>();

// The assistant emits short IDs (c1, c2, ...) matched by position in the citations array.
const shortIdOf = (idx: number) => `c${idx + 1}`;

const highlightedIdx = computed(() => {
  if (!props.hoveredCid) return -1;
  return props.citations.findIndex((_, i) => shortIdOf(i) === props.hoveredCid);
});
</script>

<template>
  <div class="h-full border rounded-lg bg-white p-4 overflow-y-auto">
    <h2 class="font-semibold text-sm mb-3">Citations</h2>
    <p v-if="!citations.length" class="text-xs text-slate-500">
      No citations yet.
    </p>
    <ul class="space-y-3">
      <li v-for="(c, i) in citations" :key="c.chunk_id"
          class="border-l-2 pl-3 text-xs transition-colors rounded-r"
          :class="highlightedIdx === i
            ? 'border-amber-400 bg-amber-50'
            : 'border-slate-300'">
        <div class="font-mono text-slate-500 flex items-center gap-2">
          <span class="inline-block bg-amber-100 text-amber-800 rounded px-1.5 py-0.5">
            [{{ shortIdOf(i) }}]
          </span>
          <span>{{ c.trial_id }} · {{ c.section ?? "—" }} · score {{ c.score.toFixed(2) }}</span>
        </div>
        <div class="mt-1 text-slate-700">{{ c.text }}</div>
      </li>
    </ul>
  </div>
</template>
