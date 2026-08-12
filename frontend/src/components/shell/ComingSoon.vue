<script setup lang="ts">
import { PageHeader, Blueprint, Icon } from '../industry';

defineProps<{
  kicker: string;
  title: string;
  subtitle?: string;
  icon: string;
  phase: string;
  body: string;
}>();
</script>

<template>
  <div class="page">
    <div class="page-inner tm-enter">
      <PageHeader style="--i: 0" :kicker="kicker" :title="title">
        <template v-if="subtitle" #subtitle>{{ subtitle }}</template>
      </PageHeader>
      <Blueprint style="--i: 1" no-hover class="coming-soon">
        <div class="cs-inner">
          <Icon :name="icon" :size="28" />
          <div class="cs-title">Coming in {{ phase }}</div>
          <div class="cs-body">{{ body }}</div>
        </div>
      </Blueprint>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 0 30px 40px; }
.page-inner { max-width: 1180px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
.coming-soon { padding: 60px 20px; }
.cs-inner {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  color: var(--color-neutral-500);
}
.cs-title {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 20px; color: var(--color-neutral-700);
}
.cs-body { font-size: 13px; max-width: 480px; text-align: center; line-height: 1.55; }
</style>
