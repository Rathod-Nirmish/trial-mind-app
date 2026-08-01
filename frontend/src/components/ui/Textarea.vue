<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    placeholder?: string;
    rows?: number;
    disabled?: boolean;
    invalid?: boolean;
    id?: string;
    resize?: "none" | "vertical" | "horizontal" | "both";
    mono?: boolean;
  }>(),
  { rows: 4, disabled: false, invalid: false, resize: "vertical", mono: false },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const cls = computed(() =>
  cn(
    "w-full rounded-md border bg-white px-3 py-2 text-sm text-text",
    props.mono ? "font-mono" : "font-body",
    "placeholder:text-neutral-500 caret-accent",
    "outline-none transition-colors",
    "hover:border-neutral-400",
    "focus:border-accent focus:ring-2 focus:ring-accent/20",
    "disabled:bg-neutral-100 disabled:opacity-60",
    props.invalid ? "border-accent-700" : "border-divider",
    {
      none: "resize-none",
      vertical: "resize-y",
      horizontal: "resize-x",
      both: "resize",
    }[props.resize],
  ),
);
</script>

<template>
  <textarea
    :id="id"
    :value="modelValue"
    :placeholder="placeholder"
    :rows="rows"
    :disabled="disabled"
    :aria-invalid="invalid || undefined"
    :class="cls"
    @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>
