<script setup lang="ts">
defineProps<{ label?: string; help?: string; for?: string }>();
</script>

<template>
  <div class="field">
    <label v-if="label" :for="$props.for">{{ label }}</label>
    <slot />
    <div v-if="help" class="help">{{ help }}</div>
  </div>
</template>
