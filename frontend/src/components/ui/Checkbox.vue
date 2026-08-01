<script setup lang="ts">
import { CheckboxRoot, CheckboxIndicator } from "reka-ui";
import Icon from "./Icon.vue";

const props = withDefaults(
  defineProps<{
    modelValue?: boolean | "indeterminate";
    disabled?: boolean;
    id?: string;
    label?: string;
  }>(),
  { disabled: false },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean | "indeterminate"): void;
}>();
</script>

<template>
  <label class="inline-flex items-center gap-2 text-sm cursor-pointer select-none">
    <CheckboxRoot
      :id="id"
      :model-value="modelValue"
      :disabled="disabled"
      class="w-4 h-4 grid place-items-center rounded-sm border border-divider bg-white transition-colors
             hover:border-accent-400
             data-[state=checked]:bg-accent data-[state=checked]:border-accent
             data-[state=indeterminate]:bg-accent data-[state=indeterminate]:border-accent
             focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent
             disabled:opacity-45"
      @update:model-value="(v) => emit('update:modelValue', v)"
    >
      <CheckboxIndicator class="text-white grid place-items-center">
        <Icon v-if="modelValue === true" :size="11" :stroke-width="3">
          <path d="M20 6 9 17l-5-5" />
        </Icon>
        <Icon v-else-if="modelValue === 'indeterminate'" :size="11" :stroke-width="3">
          <path d="M5 12h14" />
        </Icon>
      </CheckboxIndicator>
    </CheckboxRoot>
    <span v-if="label || $slots.default" class="text-neutral-800">
      <slot>{{ label }}</slot>
    </span>
  </label>
</template>
