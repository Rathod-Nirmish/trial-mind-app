<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';

const props = defineProps<{
  modelValue?: string;
  placeholder?: string;
  rows?: number;
  autosize?: boolean;
  id?: string;
}>();
defineEmits<{ 'update:modelValue': [value: string] }>();

const el = ref<HTMLTextAreaElement | null>(null);

async function resize() {
  if (!props.autosize || !el.value) return;
  el.value.style.height = 'auto';
  el.value.style.height = `${el.value.scrollHeight}px`;
}

watch(() => props.modelValue, () => nextTick(resize));
</script>

<template>
  <textarea
    ref="el"
    class="input"
    :rows="rows ?? 4"
    :value="modelValue"
    :placeholder="placeholder"
    :id="id"
    @input="(e) => { $emit('update:modelValue', (e.target as HTMLTextAreaElement).value); resize(); }"
  />
</template>
