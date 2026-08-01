<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

type Elev = "none" | "sm" | "md" | "lg";
type Padding = "none" | "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    elevation?: Elev;
    padding?: Padding;
    interactive?: boolean;
    as?: string;
  }>(),
  { elevation: "sm", padding: "md", interactive: false, as: "div" },
);

const cls = computed(() =>
  cn(
    "bg-white border border-divider rounded-lg",
    { none: "", sm: "shadow-sm", md: "shadow-md", lg: "shadow-lg" }[
      props.elevation
    ],
    { none: "", sm: "p-3", md: "p-4", lg: "p-6" }[props.padding],
    props.interactive &&
      "cursor-pointer transition hover:border-accent-400 hover:shadow-md",
  ),
);
</script>

<template>
  <component :is="as" :class="cls">
    <slot />
  </component>
</template>
