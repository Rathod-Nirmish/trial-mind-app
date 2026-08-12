<script setup lang="ts">
import * as lucide from '@lucide/vue';
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{ name: string; size?: number }>(),
  { size: 16 }
);

function pascal(k: string) {
  return k.replace(/(^|-)([a-z])/g, (_, __, c) => c.toUpperCase());
}

const cmp = computed(() => {
  const key = pascal(props.name);
  return (lucide as Record<string, unknown>)[key] ?? (lucide as Record<string, unknown>)[`${key}Icon`] ?? null;
});
</script>

<template>
  <component
    v-if="cmp"
    :is="cmp"
    :size="size"
    :stroke-width="1.5"
    aria-hidden="true"
  />
</template>
