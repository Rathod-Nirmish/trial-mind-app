<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';
import { Btn, Icon } from '../industry';

const props = defineProps<{
  loading: boolean;
  suggestions?: string[];
  showSuggestions?: boolean;
}>();
const emit = defineEmits<{ (e: 'ask', q: string): void }>();

const draft = ref('');
const el = ref<HTMLTextAreaElement | null>(null);

function resize() {
  if (!el.value) return;
  el.value.style.height = 'auto';
  el.value.style.height = `${Math.min(el.value.scrollHeight, 180)}px`;
}

watch(draft, () => nextTick(resize));

function submit() {
  const q = draft.value.trim();
  if (!q || props.loading) return;
  emit('ask', q);
  draft.value = '';
  nextTick(resize);
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submit();
  }
}

function pickSuggestion(s: string) {
  if (props.loading) return;
  emit('ask', s);
}
</script>

<template>
  <div class="dock">
    <div v-if="showSuggestions && suggestions?.length" class="suggest">
      <div class="suggest-label">Try one</div>
      <div class="suggest-list">
        <button
          v-for="s in suggestions"
          :key="s"
          type="button"
          class="suggest-chip"
          :disabled="loading"
          @click="pickSuggestion(s)"
        >
          {{ s }}
        </button>
      </div>
    </div>

    <form class="composer" @submit.prevent="submit">
      <div class="composer-inner">
        <Icon name="search" :size="16" class="composer-search" />
        <textarea
          ref="el"
          v-model="draft"
          rows="1"
          class="composer-input"
          placeholder="Ask across the corpus — adverse events, outcomes, eligibility…"
          :disabled="loading"
          @keydown="onKeydown"
        />
        <Btn
          type="submit"
          variant="primary"
          :disabled="loading || !draft.trim()"
        >
          <Icon name="send" :size="12" />
          Ask
        </Btn>
      </div>
      <span class="composer-hint mono">
        <kbd>⇧</kbd><kbd>⏎</kbd> newline · <kbd>⏎</kbd> send
      </span>
    </form>
  </div>
</template>

<style scoped>
.dock {
  display: flex; flex-direction: column; gap: 10px;
  padding: 14px 22px 20px;
  background: var(--color-neutral-100);
  border-top: 1px solid var(--color-divider);
}

.suggest {
  display: flex; align-items: center; gap: 10px;
  padding: 4px 0 2px;
  overflow-x: auto;
}
.suggest-label {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-neutral-600); flex: none;
}
.suggest-list { display: inline-flex; gap: 6px; }
.suggest-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; font-size: 12px;
  background: #fff; border: 1px solid var(--color-divider);
  border-radius: 99px; color: var(--color-neutral-700);
  cursor: pointer; white-space: nowrap;
  font-family: var(--font-body); font-weight: 500;
  transition: border-color 120ms, background 120ms, color 120ms;
}
.suggest-chip:hover:not(:disabled) {
  border-color: var(--color-accent); color: var(--color-accent-800);
  background: var(--color-accent-100);
}

.composer {
  display: flex; flex-direction: column; gap: 6px;
}
.composer-inner {
  display: flex; align-items: flex-end; gap: 10px;
  padding: 6px 6px 6px 16px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  transition: border-color 120ms, box-shadow 120ms;
}
.composer-inner:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-accent) 15%, transparent);
}
.composer-search {
  color: var(--color-neutral-500); flex: none;
  padding: 10px 0;
}
.composer-input {
  flex: 1; min-width: 0;
  min-height: 40px; max-height: 180px; resize: none;
  padding: 10px 0; font: inherit;
  font-size: 14px; line-height: 1.5;
  color: var(--color-text); caret-color: var(--color-accent);
  background: transparent;
  border: 0; outline: none;
}
.composer-input::placeholder { color: color-mix(in srgb, var(--color-text) 40%, transparent); }

.composer-hint {
  display: inline-flex; align-items: center; gap: 4px;
  padding-left: 4px;
  font-size: 10.5px; color: var(--color-neutral-500);
}
.composer-hint kbd {
  display: inline-block;
  padding: 1px 5px; margin: 0 1px;
  font: inherit; font-size: 10px;
  border: 1px solid var(--color-divider);
  border-radius: 4px;
  background: #fff;
  color: var(--color-neutral-700);
}
</style>
