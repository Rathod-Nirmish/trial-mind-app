<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

type Size = "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    name?: string;
    src?: string;
    size?: Size;
    variant?: "accent" | "neutral";
  }>(),
  { size: "md", variant: "accent" },
);

const initials = computed(() => {
  if (!props.name) return "?";
  return props.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .join("");
});

const cls = computed(() =>
  cn(
    "inline-grid place-items-center rounded-full font-heading font-semibold uppercase",
    {
      sm: "w-6 h-6 text-[10px]",
      md: "w-8 h-8 text-xs",
      lg: "w-10 h-10 text-sm",
    }[props.size],
    props.variant === "accent"
      ? "bg-accent-200 text-accent-800"
      : "bg-neutral-200 text-neutral-800",
  ),
);
</script>

<template>
  <span :class="cls" :title="name">
    <img
      v-if="src"
      :src="src"
      :alt="name ?? ''"
      class="w-full h-full object-cover rounded-full"
    />
    <template v-else>{{ initials }}</template>
  </span>
</template>
