<script setup lang="ts" generic="T extends string | number">
import { useId } from 'vue';

const props = defineProps<{
  modelValue: T;
  options: readonly { value: T; label: string }[];
  name?: string;
}>();
defineEmits<{ 'update:modelValue': [value: T] }>();

const autoId = useId();
const groupName = () => props.name ?? `seg-${autoId}`;
</script>

<template>
  <div class="seg" role="radiogroup">
    <label v-for="opt in options" :key="String(opt.value)" class="seg-opt">
      <input
        type="radio"
        :name="groupName()"
        :value="opt.value"
        :checked="modelValue === opt.value"
        @change="$emit('update:modelValue', opt.value)"
      />
      <span>{{ opt.label }}</span>
    </label>
  </div>
</template>
