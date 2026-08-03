<script setup lang="ts">
defineProps<{
  modelValue?: boolean;
  label?: string;
  disabled?: boolean;
}>();
defineEmits<{ 'update:modelValue': [value: boolean] }>();
</script>

<template>
  <label class="checkbox">
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <span class="box" />
    <span><slot>{{ label }}</slot></span>
  </label>
</template>
