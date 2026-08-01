import { ref } from "vue";

export type ToastVariant = "info" | "error";
export type ToastItem = {
  id: number;
  title?: string;
  message: string;
  variant?: ToastVariant;
  duration?: number;
};

export const toasts = ref<ToastItem[]>([]);
let nextId = 1;

export function toast(input: Omit<ToastItem, "id">): number {
  const id = nextId++;
  toasts.value = [...toasts.value, { id, ...input }];
  return id;
}

export function dismiss(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}
