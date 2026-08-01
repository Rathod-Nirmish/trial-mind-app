<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    variant?: Variant;
    size?: Size;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    block?: boolean;
  }>(),
  { variant: "primary", size: "md", type: "button", disabled: false, block: false },
);

const cls = computed(() => {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-md font-body font-medium transition " +
    "transition-transform duration-100 active:scale-[.97] " +
    "disabled:opacity-45 disabled:pointer-events-none";

  const sizes: Record<Size, string> = {
    sm: "text-xs px-3 py-1.5 min-h-[28px]",
    md: "text-sm px-4 py-2 min-h-[36px]",
    lg: "text-base px-5 py-2.5 min-h-[44px]",
  };

  const variants: Record<Variant, string> = {
    primary:
      "bg-accent text-white shadow-sm hover:bg-accent-600 active:bg-accent-700",
    secondary:
      "bg-white text-text border border-divider hover:border-accent-400 hover:shadow-sm",
    ghost:
      "bg-transparent text-neutral-800 hover:bg-neutral-200",
  };

  return cn(base, sizes[props.size], variants[props.variant], props.block && "w-full");
});
</script>

<template>
  <button :type="type" :disabled="disabled" :class="cls">
    <slot />
  </button>
</template>
