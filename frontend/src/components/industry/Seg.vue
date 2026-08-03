<script setup lang="ts" generic="T extends string | number">
defineProps<{
  modelValue: T;
  options: readonly { value: T; label: string }[];
  name?: string;
}>();
defineEmits<{ 'update:modelValue': [value: T] }>();
</script>

<template>
  <div class="seg" role="radiogroup">
    <label v-for="opt in options" :key="String(opt.value)" class="seg-opt">
      <input
        type="radio"
        :name="name ?? 'seg'"
        :value="opt.value"
        :checked="modelValue === opt.value"
        @change="$emit('update:modelValue', opt.value)"
      />
      <span>{{ opt.label }}</span>
    </label>
  </div>
</template>
