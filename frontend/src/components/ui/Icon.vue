<script setup lang="ts">
/**
 * Icon — a thin SVG wrapper matching the Industry DS convention:
 * Lucide-style 24x24 viewBox, stroke-width 1.5, currentColor stroke.
 *
 * Usage: pass the raw <path>/<circle>/... children as the default slot.
 *   <Icon><path d="..." /></Icon>
 *
 * For strokeWidth 2/2.5 (small chips, emphasis), override via prop.
 */
withDefaults(
  defineProps<{
    size?: number | string;
    strokeWidth?: number | string;
  }>(),
  { size: 16, strokeWidth: 1.5 },
);
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <slot />
  </svg>
</template>
