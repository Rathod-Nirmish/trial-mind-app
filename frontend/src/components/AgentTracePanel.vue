<script setup lang="ts">
import type { TraceEvent } from "../services/types";
defineProps<{ events: TraceEvent[] }>();
</script>

<template>
  <div class="h-full border rounded-lg bg-white p-4 overflow-y-auto">
    <h2 class="font-semibold text-sm mb-3">Agent trace</h2>
    <p v-if="!events.length" class="text-xs text-slate-500">
      Trace will appear here as agents run.
    </p>
    <ol class="space-y-2 text-xs">
      <li v-for="(ev, i) in events" :key="i"
          class="border rounded p-2 bg-slate-50">
        <div class="flex justify-between">
          <span class="font-mono font-semibold">{{ ev.agent }}</span>
          <span class="text-slate-400">{{ new Date(ev.at).toLocaleTimeString() }}</span>
        </div>
        <div class="mt-1">{{ ev.summary }}</div>
      </li>
    </ol>
  </div>
</template>
