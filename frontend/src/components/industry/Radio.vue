<script setup lang="ts">
defineProps<{
  modelValue?: string;
  value: string;
  name: string;
  label?: string;
}>();
defineEmits<{ 'update:modelValue': [value: string] }>();
</script>

<template>
  <label class="radio">
    <input
      type="radio"
      :name="name"
      :value="value"
      :checked="modelValue === value"
      @change="$emit('update:modelValue', value)"
    />
    <span class="dot" />
    <span><slot>{{ label }}</slot></span>
  </label>
</template>
