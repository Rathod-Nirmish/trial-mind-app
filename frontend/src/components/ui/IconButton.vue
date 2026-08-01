<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

type Variant = "solid" | "ghost" | "outline";
type Size = "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    variant?: Variant;
    size?: Size;
    disabled?: boolean;
    label: string;
  }>(),
  { variant: "ghost", size: "md", disabled: false },
);

const cls = computed(() => {
  const base =
    "inline-grid place-items-center rounded-md transition " +
    "transition-transform duration-100 active:scale-[.95] " +
    "disabled:opacity-45 disabled:pointer-events-none";
  const sizes: Record<Size, string> = {
    sm: "w-7 h-7",
    md: "w-9 h-9",
    lg: "w-11 h-11",
  };
  const variants: Record<Variant, string> = {
    solid: "bg-accent text-white hover:bg-accent-600",
    ghost: "bg-transparent text-neutral-700 hover:bg-neutral-200",
    outline:
      "bg-white text-neutral-700 border border-divider hover:border-accent-400",
  };
  return cn(base, sizes[props.size], variants[props.variant]);
});
</script>

<template>
  <button type="button" :disabled="disabled" :aria-label="label" :class="cls">
    <slot />
  </button>
</template>
