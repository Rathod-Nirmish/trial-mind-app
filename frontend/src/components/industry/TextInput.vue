<script setup lang="ts">
defineProps<{
  modelValue?: string | number;
  placeholder?: string;
  type?: string;
  id?: string;
  disabled?: boolean;
}>();
defineEmits<{ 'update:modelValue': [value: string] }>();
</script>

<template>
  <input
    class="input"
    :type="type ?? 'text'"
    :value="modelValue"
    :placeholder="placeholder"
    :id="id"
    :disabled="disabled"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>
