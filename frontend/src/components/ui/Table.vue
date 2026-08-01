<script setup lang="ts">
/**
 * Table — a light wrapper providing the DS's themed header and row rules.
 * Use with plain <thead>, <tbody>, <tr>, <th>, <td> children, or
 * with the Th/Td helpers exposed via the sibling components.
 */
</script>

<template>
  <div class="border border-divider rounded-lg bg-white shadow-sm overflow-hidden">
    <table class="w-full text-sm border-collapse">
      <slot />
    </table>
  </div>
</template>

<style scoped>
:deep(thead) {
  background: var(--color-neutral-100);
}
:deep(thead th) {
  text-align: left;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-neutral-600);
  font-weight: 500;
  padding: 10px 18px;
  border-bottom: 1px solid var(--color-divider);
}
:deep(tbody td) {
  padding: 13px 18px;
  border-bottom: 1px solid var(--color-divider);
  vertical-align: middle;
}
:deep(tbody tr:last-child td) {
  border-bottom: 0;
}
:deep(tbody tr[data-interactive]) {
  cursor: pointer;
  transition: background-color 0.15s ease;
}
:deep(tbody tr[data-interactive]:hover) {
  background: var(--color-neutral-100);
}
</style>
