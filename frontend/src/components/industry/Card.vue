<script setup lang="ts">
defineProps<{
  kicker?: string;
  title?: string;
}>();
</script>

<template>
  <div class="card">
    <div v-if="$slots.kicker || kicker" class="card-kicker">
      <slot name="kicker">{{ kicker }}</slot>
    </div>
    <div v-if="$slots.title || title" class="card-title">
      <slot name="title">{{ title }}</slot>
    </div>
    <div v-if="$slots.default" class="card-body">
      <slot />
    </div>
    <div v-if="$slots.meta" class="card-meta">
      <slot name="meta" />
    </div>
  </div>
</template>
