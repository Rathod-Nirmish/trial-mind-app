<script setup lang="ts">
/**
 * Scannable row card for data-list surfaces (Runs, Agent history, Ingestion jobs).
 * Slots: kicker (RUN 0148), status (Tag), timestamp (right-aligned), default (title),
 * meta (row of stats), extra (right-side action).
 * Prefer this over <table> when each row has 5+ dimensions or a long title.
 */
defineProps<{ interactive?: boolean }>();
</script>

<template>
  <article class="rowcard" :class="{ 'is-interactive': interactive }">
    <header class="rowcard-top">
      <div class="rowcard-lead">
        <span v-if="$slots.kicker" class="rowcard-kicker num">
          <slot name="kicker" />
        </span>
        <slot name="status" />
      </div>
      <div v-if="$slots.timestamp" class="rowcard-ts num">
        <slot name="timestamp" />
      </div>
    </header>

    <div v-if="$slots.default" class="rowcard-title">
      <slot />
    </div>

    <footer v-if="$slots.meta" class="rowcard-meta">
      <slot name="meta" />
    </footer>

    <div v-if="$slots.expanded" class="rowcard-expanded">
      <slot name="expanded" />
    </div>
  </article>
</template>

<style scoped>
.rowcard {
  display: flex; flex-direction: column; gap: 8px;
  padding: 14px 18px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  transition: border-color 140ms ease, transform 140ms ease;
}
.rowcard.is-interactive { cursor: pointer; }
.rowcard.is-interactive:hover {
  border-color: color-mix(in srgb, var(--color-accent) 45%, var(--color-divider));
  transform: translateY(-1px);
}

.rowcard-top {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.rowcard-lead { display: inline-flex; align-items: center; gap: 10px; }
.rowcard-kicker {
  font-family: var(--font-body); font-weight: 600;
  font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-neutral-700);
}
.rowcard-ts {
  font-size: 12px; color: var(--color-neutral-600);
  display: inline-flex; align-items: center; gap: 6px;
}

.rowcard-title {
  font-family: var(--font-body); font-weight: 500;
  font-size: 14.5px; line-height: 1.4; color: var(--color-text);
}

.rowcard-meta {
  display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
  padding-top: 2px;
  font-size: 12px; color: var(--color-neutral-600);
}
.rowcard-meta :deep(.meta-item) {
  display: inline-flex; align-items: center; gap: 6px;
}
.rowcard-meta :deep(.meta-item .num) { color: var(--color-neutral-700); }
.rowcard-meta :deep(.meta-item svg) { color: var(--color-neutral-500); }

.rowcard-expanded {
  margin-top: 8px;
  padding-top: 14px;
  border-top: 1px solid var(--color-divider);
  display: flex; flex-direction: column; gap: 12px;
}
</style>
