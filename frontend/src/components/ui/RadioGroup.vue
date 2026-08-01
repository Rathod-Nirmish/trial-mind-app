<script setup lang="ts">
import { RadioGroupRoot, RadioGroupItem, RadioGroupIndicator } from "reka-ui";

type Option = { value: string; label: string; disabled?: boolean };

const props = defineProps<{
  modelValue?: string;
  options: Option[];
  name?: string;
  orientation?: "vertical" | "horizontal";
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();
</script>

<template>
  <RadioGroupRoot
    :model-value="modelValue"
    :name="name"
    :orientation="orientation ?? 'vertical'"
    :class="[
      'flex gap-3',
      (orientation ?? 'vertical') === 'vertical' ? 'flex-col' : 'flex-row flex-wrap',
    ]"
    @update:model-value="(v) => emit('update:modelValue', v as string)"
  >
    <label
      v-for="opt in options"
      :key="opt.value"
      class="inline-flex items-center gap-2 text-sm cursor-pointer select-none"
      :class="opt.disabled && 'opacity-45 cursor-not-allowed'"
    >
      <RadioGroupItem
        :value="opt.value"
        :disabled="opt.disabled"
        class="w-4 h-4 grid place-items-center rounded-full border border-divider bg-white transition-colors
               hover:border-accent-400
               data-[state=checked]:border-accent
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <RadioGroupIndicator class="w-2 h-2 rounded-full bg-accent" />
      </RadioGroupItem>
      <span class="text-neutral-800">{{ opt.label }}</span>
    </label>
  </RadioGroupRoot>
</template>
