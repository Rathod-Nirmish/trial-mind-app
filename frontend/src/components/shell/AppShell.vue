<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
import { isMock } from '../../services/api';
import CommandPalette from './CommandPalette.vue';
import ToastHost from './ToastHost.vue';

const links = [
  { to: '/', label: 'Chat' },
  { to: '/corpus', label: 'Corpus' },
  { to: '/explorations', label: 'Explorations' },
  { to: '/runs', label: 'Runs' },
  { to: '/workbench', label: 'Workbench' },
];
</script>

<template>
  <div class="shell">
    <nav class="nav shell-nav">
      <RouterLink to="/" class="nav-brand">
        <span class="brand-mark" />
        TrialMind
      </RouterLink>
      <div class="nav-links">
        <RouterLink
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          :aria-current="$route.path === l.to || (l.to !== '/' && $route.path.startsWith(l.to)) ? 'page' : undefined"
        >
          {{ l.label }}
        </RouterLink>
      </div>
      <div class="nav-tail">
        <span class="kbd-chip" title="Open command palette (⌘K)">
          <kbd>⌘</kbd><kbd>K</kbd>
        </span>
        <span v-if="isMock" class="mock-chip" title="Mock data — no real backend calls. Set VITE_USE_MOCK_API=false to hit the live API.">
          <span class="mock-dot" />
          MOCK
        </span>
        <span class="status-chip">
          <span class="status-dot" />
          <span class="status-label">gemini-2.5-pro</span>
        </span>
        <RouterLink to="/ui-kit" class="nav-utility">UI kit</RouterLink>
      </div>
    </nav>

    <main class="shell-main">
      <RouterView v-slot="{ Component, route }">
        <transition name="fade" mode="out-in">
          <component
            :is="Component"
            :key="route.path"
            :class="['shell-page', { 'is-fixed': route.path === '/' }]"
          />
        </transition>
      </RouterView>
    </main>

    <CommandPalette />
    <ToastHost />

    <footer class="shell-footer">
      <span>TrialMind is a portfolio demo — not a medical decision-support tool.</span>
      <span class="footer-meta">v0.2 · <a href="https://github.com" target="_blank" rel="noopener">source</a></span>
    </footer>
  </div>
</template>

<style scoped>
.shell {
  display: flex; flex-direction: column;
  height: 100vh;
  min-height: 0;
  background: var(--color-neutral-100);
  overflow: hidden;
}

.shell-nav {
  flex: none;
  z-index: 30;
  gap: 8px;
}
.nav-brand {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 12px 4px;
}
.brand-mark {
  width: 18px; height: 18px;
  background: var(--color-accent);
  position: relative;
  border-radius: 3px;
}
.brand-mark::after {
  content: ""; position: absolute; inset: 3px;
  border: 1.5px solid #fff; border-radius: 2px;
}
.nav-links {
  display: inline-flex; align-items: center; gap: 2px;
  margin: 0 auto 0 24px;
}
.nav-tail {
  display: inline-flex; align-items: center; gap: 12px; margin-left: auto;
}

.status-chip {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 10px 5px 8px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 99px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px; color: var(--color-neutral-700);
}
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #4bb26a; box-shadow: 0 0 0 3px color-mix(in srgb, #4bb26a 24%, transparent);
}

.kbd-chip {
  display: inline-flex; align-items: center; gap: 2px;
  padding: 5px 8px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 8px;
  cursor: help;
}
.kbd-chip kbd {
  display: inline-block;
  padding: 0 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px; font-weight: 600;
  color: var(--color-neutral-700);
}

.mock-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 9px;
  background: #fdf6e0; color: #7a5a00;
  border: 1px solid #d4a017;
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 700;
  font-size: 10px; letter-spacing: 0.14em;
  cursor: help;
}
.mock-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: #d4a017;
}
.nav-utility {
  font-size: 12px; color: var(--color-neutral-600);
  padding: 8px 10px; border-radius: 6px;
}
.nav-utility:hover { color: var(--color-text); background: var(--color-neutral-100); }

.shell-main {
  flex: 1; min-height: 0;
  display: flex; flex-direction: column;
  overflow: hidden;
}

/* Routes with .is-fixed take the full viewport height and manage their own
 * scroll internally (Home). Other routes scroll the page normally. */
.shell-page {
  flex: 1; min-height: 0;
  overflow-y: auto;
}
.shell-page.is-fixed { overflow: hidden; }

.shell-footer {
  flex: none;
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 24px;
  border-top: 1px solid var(--color-divider);
  background: #fff;
  font-size: 11.5px; color: var(--color-neutral-600);
}
.footer-meta a {
  color: var(--color-neutral-600);
  border-bottom: 1px dotted var(--color-divider);
}
.footer-meta a:hover { color: var(--color-accent-700); }

.fade-enter-active, .fade-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.fade-enter-from { opacity: 0; transform: translateY(4px); }
.fade-leave-to   { opacity: 0; transform: translateY(-4px); }
</style>
