<script setup lang="ts">
defineProps<{ kicker?: string; title?: string }>();
</script>

<template>
  <header class="page-header">
    <div class="page-header-text">
      <div v-if="kicker" class="page-header-kicker">{{ kicker }}</div>
      <h1 v-if="title" class="page-header-title num">{{ title }}</h1>
      <div v-if="$slots.subtitle" class="page-header-sub">
        <slot name="subtitle" />
      </div>
    </div>
    <div v-if="$slots.actions" class="page-header-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: var(--space-6);
  padding: var(--space-8) 0 var(--space-6);
  border-bottom: 1px solid var(--color-divider);
}
.page-header-kicker {
  font-family: var(--font-heading); font-weight: var(--font-heading-weight);
  font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--color-accent-700);
  margin-bottom: var(--space-2);
}
.page-header-title {
  font-family: var(--font-heading); font-weight: var(--font-heading-weight);
  font-size: 34px; line-height: 1.1; letter-spacing: 0.005em;
  color: var(--color-text);
}
.page-header-sub {
  font-size: 13px; color: color-mix(in srgb, var(--color-text) 60%, transparent);
  margin-top: var(--space-2);
}
.page-header-actions {
  display: flex; gap: var(--space-2); align-items: center;
}
</style>
