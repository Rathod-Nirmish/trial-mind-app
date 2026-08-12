<script setup lang="ts" generic="T extends string">
defineProps<{
  modelValue: T;
  options: readonly { value: T; label: string; count?: number | string }[];
}>();
defineEmits<{ 'update:modelValue': [value: T] }>();
</script>

<template>
  <div class="segtabs" role="tablist">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="tab"
      :aria-selected="modelValue === opt.value"
      class="segtabs-opt"
      :class="{ 'is-active': modelValue === opt.value }"
      @click="$emit('update:modelValue', opt.value)"
    >
      <span>{{ opt.label }}</span>
      <span v-if="opt.count != null" class="segtabs-count num">{{ opt.count }}</span>
    </button>
  </div>
</template>

<style scoped>
.segtabs {
  display: inline-flex; align-items: center; gap: 2px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 99px;
  padding: 3px;
}
.segtabs-opt {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px;
  font-family: var(--font-body); font-weight: 500;
  font-size: 12.5px;
  color: var(--color-neutral-700);
  background: transparent;
  border: 0;
  border-radius: 99px;
  cursor: pointer;
  transition: background 120ms, color 120ms;
}
.segtabs-opt:hover { color: var(--color-text); background: var(--color-neutral-100); }
.segtabs-opt.is-active {
  background: var(--color-accent);
  color: #fff;
}
.segtabs-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; padding: 0 5px;
  font-size: 10.5px; font-weight: 600;
  border-radius: 99px;
  background: color-mix(in srgb, currentColor 12%, transparent);
}
.segtabs-opt.is-active .segtabs-count {
  background: color-mix(in srgb, #fff 20%, transparent);
}
</style>
