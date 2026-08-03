<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'accent' | 'accent-2' | 'neutral' | 'outline' | 'warn' | 'ghost';
  }>(),
  { variant: 'neutral' }
);
</script>

<template>
  <span class="tag" :class="`tag-${variant}`"><slot /></span>
</template>
