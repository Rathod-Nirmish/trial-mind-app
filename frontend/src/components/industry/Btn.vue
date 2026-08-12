<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'icon';
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
    block?: boolean;
    kbd?: string;
    as?: 'button' | 'a';
    href?: string;
  }>(),
  { variant: 'secondary', type: 'button', as: 'button' }
);
</script>

<template>
  <component
    :is="as"
    :type="as === 'button' ? type : undefined"
    :href="href"
    :disabled="as === 'button' ? disabled : undefined"
    class="btn"
    :class="[`btn-${variant}`, { 'btn-block': block }]"
  >
    <slot />
    <span v-if="kbd" class="kbd">{{ kbd }}</span>
  </component>
</template>
