import { ref } from 'vue';

export type Toast = {
  id: number;
  message: string;
  kind?: 'info' | 'success' | 'warn';
  duration?: number;
};

const toasts = ref<Toast[]>([]);
let seq = 1;

export function useToast() {
  function push(message: string, kind: Toast['kind'] = 'info', duration = 2600) {
    const id = seq++;
    toasts.value.push({ id, message, kind, duration });
    setTimeout(() => dismiss(id), duration);
  }
  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }
  return { toasts, push, dismiss };
}
