<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '../industry';

type Cmd = {
  id: string;
  label: string;
  hint?: string;
  icon: string;
  kbd?: string;
  action: () => void;
  group: 'navigate' | 'action';
};

const open = ref(false);
const query = ref('');
const cursor = ref(0);
const inputEl = ref<HTMLInputElement | null>(null);
const router = useRouter();

function toggle() { open.value = !open.value; query.value = ''; cursor.value = 0; }
function close()  { open.value = false; }

function go(path: string) {
  router.push(path);
  close();
}

const commands = computed<Cmd[]>(() => [
  { id: 'chat',         label: 'Go to Chat',           hint: 'Ask a question', icon: 'message-square',     action: () => go('/'),              group: 'navigate' },
  { id: 'corpus',       label: 'Go to Corpus',         hint: 'Browse trials',  icon: 'database',           action: () => go('/corpus'),        group: 'navigate' },
  { id: 'explorations', label: 'Go to Explorations',   hint: 'Saved runs',     icon: 'bookmark',           action: () => go('/explorations'),  group: 'navigate' },
  { id: 'runs',         label: 'Go to Runs',           hint: 'Eval & history', icon: 'activity',           action: () => go('/runs'),          group: 'navigate' },
  { id: 'workbench',    label: 'Go to Workbench',      hint: 'Query builder',  icon: 'sliders-horizontal', action: () => go('/workbench'),     group: 'navigate' },
  { id: 'ui-kit',       label: 'Go to UI kit',         hint: 'Design system',  icon: 'palette',            action: () => go('/ui-kit'),        group: 'navigate' },
  { id: 'new-exp',      label: 'New exploration',      hint: 'Start a session',icon: 'plus',    kbd: 'N',  action: () => go('/'),              group: 'action' },
  { id: 'trigger-eval', label: 'Trigger eval run',     hint: 'Golden Q&A',     icon: 'play',               action: () => go('/runs'),          group: 'action' },
]);

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return commands.value;
  return commands.value.filter((c) =>
    c.label.toLowerCase().includes(q) || c.hint?.toLowerCase().includes(q)
  );
});

watch(filtered, () => { cursor.value = 0; });

function onKey(e: KeyboardEvent) {
  const isMod = e.metaKey || e.ctrlKey;
  if (isMod && (e.key === 'k' || e.key === 'K')) {
    e.preventDefault();
    toggle();
    if (open.value) nextTick(() => inputEl.value?.focus());
    return;
  }
  if (!open.value) return;
  if (e.key === 'Escape') { e.preventDefault(); close(); }
  else if (e.key === 'ArrowDown') { e.preventDefault(); cursor.value = (cursor.value + 1) % filtered.value.length; }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); cursor.value = (cursor.value - 1 + filtered.value.length) % filtered.value.length; }
  else if (e.key === 'Enter')     { e.preventDefault(); filtered.value[cursor.value]?.action(); }
}

onMounted(() => window.addEventListener('keydown', onKey));
onUnmounted(() => window.removeEventListener('keydown', onKey));

watch(open, (o) => {
  if (o) nextTick(() => inputEl.value?.focus());
});
</script>

<template>
  <transition name="cp">
    <div v-if="open" class="cp-backdrop" @click.self="close">
      <div class="cp" role="dialog" aria-modal="true" aria-label="Command palette">
        <div class="cp-search">
          <Icon name="search" :size="16" />
          <input
            ref="inputEl"
            v-model="query"
            type="text"
            class="cp-input"
            placeholder="Type a command or search…"
            spellcheck="false"
          />
          <span class="cp-kbd">esc</span>
        </div>

        <ul v-if="filtered.length" class="cp-list" role="listbox">
          <li
            v-for="(c, i) in filtered"
            :key="c.id"
            class="cp-item"
            :class="{ 'is-active': i === cursor }"
            role="option"
            :aria-selected="i === cursor"
            @mouseenter="cursor = i"
            @click="c.action()"
          >
            <span class="cp-item-icon"><Icon :name="c.icon" :size="14" /></span>
            <div class="cp-item-body">
              <div class="cp-item-label">{{ c.label }}</div>
              <div v-if="c.hint" class="cp-item-hint">{{ c.hint }}</div>
            </div>
            <span class="cp-item-group">{{ c.group }}</span>
            <span v-if="c.kbd" class="cp-kbd">{{ c.kbd }}</span>
          </li>
        </ul>

        <div v-else class="cp-empty">
          <Icon name="search-x" :size="16" />
          No commands match "{{ query }}"
        </div>

        <footer class="cp-foot">
          <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
          <span><kbd>↵</kbd> select</span>
          <span><kbd>esc</kbd> close</span>
        </footer>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.cp-backdrop {
  position: fixed; inset: 0; z-index: 100;
  background: color-mix(in srgb, var(--color-neutral-900) 45%, transparent);
  backdrop-filter: blur(3px);
  display: flex; justify-content: center;
  padding-top: 12vh;
}
.cp {
  width: min(560px, 92%);
  height: fit-content;
  max-height: 60vh;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 14px;
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column;
  overflow: hidden;
}

.cp-search {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-divider);
  color: var(--color-neutral-500);
}
.cp-input {
  flex: 1;
  border: 0; background: transparent; outline: none;
  font: inherit; font-size: 14px;
  color: var(--color-text);
  caret-color: var(--color-accent);
}
.cp-input::placeholder { color: color-mix(in srgb, var(--color-text) 40%, transparent); }

.cp-kbd {
  padding: 2px 7px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 10px; color: var(--color-neutral-600);
}

.cp-list {
  list-style: none; margin: 0; padding: 6px;
  overflow-y: auto; flex: 1; min-height: 0;
}
.cp-item {
  display: grid; grid-template-columns: 26px 1fr auto auto; gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 100ms;
}
.cp-item.is-active { background: var(--color-accent-100); }
.cp-item-icon {
  width: 26px; height: 26px;
  display: inline-grid; place-items: center;
  background: var(--color-neutral-100);
  border-radius: 6px;
  color: var(--color-neutral-700);
}
.cp-item.is-active .cp-item-icon { background: #fff; color: var(--color-accent-700); }

.cp-item-body { min-width: 0; }
.cp-item-label { font-size: 13px; color: var(--color-text); font-weight: 500; }
.cp-item-hint { font-size: 11px; color: var(--color-neutral-500); margin-top: 1px; }
.cp-item-group {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--color-neutral-500);
}
.cp-item.is-active .cp-item-group { color: var(--color-accent-700); }

.cp-empty {
  padding: 40px 20px; text-align: center;
  color: var(--color-neutral-500); font-size: 12.5px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}

.cp-foot {
  padding: 8px 14px;
  border-top: 1px solid var(--color-divider);
  background: var(--color-neutral-100);
  display: flex; gap: 16px;
  font-size: 10.5px; color: var(--color-neutral-600);
}
.cp-foot kbd {
  display: inline-block;
  padding: 1px 5px; margin: 0 2px;
  font-family: ui-monospace, monospace; font-size: 10px;
  border: 1px solid var(--color-divider);
  border-radius: 4px;
  background: #fff;
  color: var(--color-neutral-700);
}

.cp-enter-active, .cp-leave-active { transition: opacity 180ms ease; }
.cp-enter-active .cp, .cp-leave-active .cp { transition: transform 240ms cubic-bezier(.22,.68,.35,1); }
.cp-enter-from, .cp-leave-to { opacity: 0; }
.cp-enter-from .cp, .cp-leave-to .cp { transform: translateY(-8px); }
</style>
