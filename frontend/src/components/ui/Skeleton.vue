<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

const props = withDefaults(
  defineProps<{
    width?: string;
    height?: string;
    rounded?: "sm" | "md" | "lg" | "full";
  }>(),
  { width: "100%", height: "1em", rounded: "md" },
);

const cls = computed(() =>
  cn(
    "block bg-neutral-200 animate-tm-pulse",
    {
      sm: "rounded-sm",
      md: "rounded-md",
      lg: "rounded-lg",
      full: "rounded-full",
    }[props.rounded],
  ),
);
</script>

<template>
  <span :class="cls" :style="{ width, height }" aria-hidden="true" />
</template>
