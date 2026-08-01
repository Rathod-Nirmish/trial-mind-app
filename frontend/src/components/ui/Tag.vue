<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

type Variant = "accent" | "neutral" | "outline" | "success" | "warning";

const props = withDefaults(
  defineProps<{
    variant?: Variant;
    pill?: boolean;
    uppercase?: boolean;
    mono?: boolean;
  }>(),
  { variant: "neutral", pill: true, uppercase: false, mono: false },
);

const cls = computed(() => {
  const base =
    "inline-flex items-center gap-1.5 text-[10px] font-medium leading-none " +
    "px-2 py-1 whitespace-nowrap";
  const variants: Record<Variant, string> = {
    accent: "bg-accent-100 text-accent-800",
    neutral: "bg-neutral-200 text-neutral-700",
    outline: "border border-accent-700 text-accent-800 bg-white",
    success: "bg-accent-100 text-accent-800",
    warning: "border border-accent-700 text-accent-800 bg-white",
  };
  return cn(
    base,
    variants[props.variant],
    props.pill ? "rounded-full" : "rounded-md",
    props.uppercase && "uppercase tracking-wider",
    props.mono && "font-mono",
  );
});
</script>

<template>
  <span :class="cls">
    <slot />
  </span>
</template>
