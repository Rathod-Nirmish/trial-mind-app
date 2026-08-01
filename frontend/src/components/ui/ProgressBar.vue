<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

const props = withDefaults(
  defineProps<{
    value: number;
    max?: number;
    size?: "sm" | "md";
    indeterminate?: boolean;
    label?: string;
  }>(),
  { max: 100, size: "sm", indeterminate: false },
);

const pct = computed(() => {
  const p = (props.value / props.max) * 100;
  return Math.max(0, Math.min(100, p));
});

const trackCls = computed(() =>
  cn(
    "w-full rounded-full bg-neutral-200 overflow-hidden",
    props.size === "sm" ? "h-1" : "h-1.5",
  ),
);
</script>

<template>
  <div
    :class="trackCls"
    role="progressbar"
    :aria-valuenow="indeterminate ? undefined : value"
    :aria-valuemax="max"
    :aria-valuemin="0"
    :aria-label="label"
  >
    <div
      v-if="!indeterminate"
      class="h-full bg-accent transition-[width] duration-300"
      :style="{ width: `${pct}%` }"
    />
    <div
      v-else
      class="h-full w-1/3 bg-accent animate-tm-pulse"
      style="animation: tm-pulse 1.4s ease-in-out infinite"
    />
  </div>
</template>
