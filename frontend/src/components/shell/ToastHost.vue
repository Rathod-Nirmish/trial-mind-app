<script setup lang="ts">
import { useToast } from '../../composables/useToast';
import { Icon } from '../industry';

const { toasts, dismiss } = useToast();

function iconFor(k?: string) {
  if (k === 'success') return 'check';
  if (k === 'warn')    return 'alert-triangle';
  return 'info';
}
</script>

<template>
  <div class="toast-host" aria-live="polite">
    <transition-group name="toast" tag="div" class="toast-stack">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="toast"
        :class="`is-${t.kind ?? 'info'}`"
      >
        <span class="toast-icon"><Icon :name="iconFor(t.kind)" :size="14" /></span>
        <span class="toast-msg">{{ t.message }}</span>
        <button type="button" class="toast-close" @click="dismiss(t.id)" aria-label="Dismiss">
          <Icon name="x" :size="12" />
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed; z-index: 200;
  bottom: 24px; left: 50%; transform: translateX(-50%);
  pointer-events: none;
}
.toast-stack { display: flex; flex-direction: column; gap: 8px; align-items: center; }
.toast {
  pointer-events: auto;
  display: inline-flex; align-items: center; gap: 10px;
  padding: 10px 14px 10px 12px;
  background: var(--color-neutral-900); color: #fff;
  border-radius: 10px;
  box-shadow: var(--shadow-lg);
  font-family: var(--font-body); font-weight: 500;
  font-size: 13px;
  max-width: 480px;
}
.toast.is-success { background: #1e6934; }
.toast.is-warn    { background: #7a5a00; }
.toast-icon { display: inline-grid; place-items: center; color: color-mix(in srgb, #fff 80%, transparent); }
.toast-msg { flex: 1; }
.toast-close {
  width: 22px; height: 22px; padding: 0;
  background: transparent; border: 0;
  color: color-mix(in srgb, #fff 65%, transparent);
  border-radius: 4px; cursor: pointer;
  display: inline-grid; place-items: center;
  transition: background 120ms, color 120ms;
}
.toast-close:hover { background: color-mix(in srgb, #fff 12%, transparent); color: #fff; }

.toast-enter-active, .toast-leave-active { transition: opacity 200ms, transform 240ms cubic-bezier(.22,.68,.35,1); }
.toast-enter-from { opacity: 0; transform: translateY(12px); }
.toast-leave-to   { opacity: 0; transform: translateY(-6px); }
</style>
