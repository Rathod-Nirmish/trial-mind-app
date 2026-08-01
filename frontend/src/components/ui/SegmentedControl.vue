<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/cn";

type Option<T extends string> = { value: T; label: string };

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: Option<string>[];
    size?: "sm" | "md";
  }>(),
  { size: "md" },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const wrapCls = computed(() =>
  cn(
    "inline-flex gap-0.5 bg-white border border-divider rounded-full",
    props.size === "sm" ? "p-0.5" : "p-1",
  ),
);
const btnCls = (active: boolean) =>
  cn(
    "font-body font-medium rounded-full transition whitespace-nowrap active:scale-[.95]",
    props.size === "sm" ? "text-xs px-3 py-1 min-h-[24px]" : "text-sm px-4 py-1.5 min-h-[30px]",
    active ? "bg-accent text-white shadow-sm" : "text-neutral-700 hover:text-neutral-900",
  );
</script>

<template>
  <div :class="wrapCls" role="tablist">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="tab"
      :aria-selected="modelValue === opt.value"
      :class="btnCls(modelValue === opt.value)"
      @click="emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
