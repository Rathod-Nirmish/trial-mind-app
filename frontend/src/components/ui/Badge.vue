<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

/**
 * Badge — a small status dot / count indicator, distinct from Tag.
 * Tag is a text label; Badge is a compact numeric or status marker.
 */
type Variant = "accent" | "neutral" | "dot";

const props = withDefaults(
  defineProps<{ variant?: Variant }>(),
  { variant: "accent" },
);

const cls = computed(() => {
  if (props.variant === "dot") {
    return "inline-block w-1.5 h-1.5 rounded-full bg-accent-600";
  }
  const base =
    "inline-flex items-center justify-center rounded-full text-[10px] " +
    "font-medium font-mono px-1.5 min-w-[18px] h-[18px] leading-none";
  const variants = {
    accent: "bg-accent-100 text-accent-800",
    neutral: "bg-neutral-200 text-neutral-700",
  } as const;
  return cn(base, variants[props.variant as "accent" | "neutral"]);
});
</script>

<template>
  <span :class="cls"><slot /></span>
</template>
