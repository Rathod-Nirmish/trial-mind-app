<script setup lang="ts">
defineProps<{ elevation?: 'sm' | 'md' | 'lg'; noHover?: boolean }>();
</script>

<template>
  <div
    class="blueprint"
    :class="[elevation && `elev-${elevation}`, { 'no-hover': noHover }]"
  >
    <slot />
  </div>
</template>
