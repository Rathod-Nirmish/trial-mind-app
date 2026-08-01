<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    type?: string;
    placeholder?: string;
    disabled?: boolean;
    invalid?: boolean;
    id?: string;
  }>(),
  { type: "text", disabled: false, invalid: false },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const cls = computed(() =>
  cn(
    "w-full rounded-md border bg-white px-3 py-2 text-sm text-text font-body",
    "placeholder:text-neutral-500 caret-accent",
    "outline-none transition-colors",
    "hover:border-neutral-400",
    "focus:border-accent focus:ring-2 focus:ring-accent/20",
    "disabled:bg-neutral-100 disabled:opacity-60 disabled:cursor-not-allowed",
    props.invalid ? "border-accent-700" : "border-divider",
  ),
);
</script>

<template>
  <input
    :id="id"
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :aria-invalid="invalid || undefined"
    :class="cls"
    @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>
