<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useToast } from '../composables/useToast';
import { PageHeader, Btn, Icon, Field, TextInput, Seg } from '../components/industry';
import Loader from '../components/industry/Loader.vue';
import { listExplorations, patchExploration, deleteExploration } from '../services/api';
import type { Exploration } from '../services/types';

const items = ref<Exploration[]>([]);
const loading = ref(true);

const search = ref('');
const scope = ref<'all' | 'mine' | 'shared'>('all');
const sort = ref<'recent' | 'pinned' | 'az'>('recent');

const openMenuId = ref<string | null>(null);
const openId = ref<string | null>(null);
const { push: toast } = useToast();

function onEsc(e: KeyboardEvent) {
  if (e.key !== 'Escape') return;
  if (openMenuId.value) { openMenuId.value = null; e.preventDefault(); return; }
  if (openId.value)     { openId.value = null;     e.preventDefault(); return; }
}
onMounted(() => window.addEventListener('keydown', onEsc));
onUnmounted(() => window.removeEventListener('keydown', onEsc));

onMounted(async () => {
  loading.value = true;
  try {
    const r = await listExplorations();
    items.value = r.items;
  } finally {
    loading.value = false;
  }
});

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  let list = items.value.filter((e) =>
    !q || `${e.short_id} ${e.title} ${e.question}`.toLowerCase().includes(q)
  );
  if (sort.value === 'pinned') {
    list = [...list].sort((a, b) => Number(b.pinned) - Number(a.pinned));
  } else if (sort.value === 'az') {
    list = [...list].sort((a, b) => a.title.localeCompare(b.title));
  } else {
    list = [...list].sort((a, b) => {
      const p = Number(b.pinned) - Number(a.pinned);
      if (p !== 0) return p;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }
  return list;
});

const pinnedCount = computed(() => items.value.filter((e) => e.pinned).length);

async function togglePin(e: Exploration) {
  e.pinned = !e.pinned;
  await patchExploration(e.id, { pinned: e.pinned });
  toast(e.pinned ? `Pinned "${e.short_id}"` : `Unpinned "${e.short_id}"`, 'success');
}

async function removeExploration(e: Exploration) {
  openMenuId.value = null;
  items.value = items.value.filter((x) => x.id !== e.id);
  await deleteExploration(e.id);
  toast(`Deleted "${e.short_id}"`, 'success');
}

function shareLink(e: Exploration) {
  navigator.clipboard?.writeText(`${location.origin}/explorations/${e.id}`);
  openMenuId.value = null;
  toast('Link copied to clipboard', 'success');
}

function ago(iso: string) {
  const dt = (Date.now() - new Date(iso).getTime()) / 3600_000;
  if (dt < 1) return `${Math.max(1, Math.round(dt * 60))}m ago`;
  if (dt < 24) return `${Math.round(dt)}h ago`;
  const d = Math.round(dt / 24);
  return `${d}d ago`;
}

// Miniature sparkline path for entail scores (deterministic mock per exploration)
function sparkPath(seed: string): string {
  let h = 0;
  for (const c of seed) h = (h * 31 + c.charCodeAt(0)) & 0xffff;
  const pts = Array.from({ length: 8 }, (_, i) => {
    const y = 20 - ((h >> ((i * 3) % 12)) & 15);
    return `${i * 8},${y}`;
  });
  return `M${pts.join(' L')}`;
}
</script>

<template>
  <div class="page tm-enter">
    <PageHeader style="--i: 0" kicker="EXPLORATIONS" title="Saved investigations">
      <template #subtitle>
        <span class="num">{{ items.length }}</span> saved
        <template v-if="pinnedCount">
          · <span class="num">{{ pinnedCount }}</span> pinned
        </template>
      </template>
      <template #actions>
        <Btn variant="primary" as="a" href="/">
          <Icon name="plus" :size="14" /> New exploration
        </Btn>
      </template>
    </PageHeader>

    <div class="toolbar" style="--i: 1">
      <div class="toolbar-search">
        <Field label="Search">
          <TextInput v-model="search" placeholder="Title, question, tag…" />
        </Field>
      </div>
      <div class="toolbar-seg">
        <Field label="Scope">
          <Seg
            v-model="scope"
            :options="[
              { value: 'all', label: 'All' },
              { value: 'mine', label: 'Mine' },
              { value: 'shared', label: 'Shared' },
            ]"
          />
        </Field>
        <Field label="Sort">
          <Seg
            v-model="sort"
            :options="[
              { value: 'recent', label: 'Recent' },
              { value: 'pinned', label: 'Pinned' },
              { value: 'az', label: 'A–Z' },
            ]"
          />
        </Field>
      </div>
    </div>

    <div v-if="loading" class="loading" style="--i: 2">
      <Loader variant="spinner" :size="20" label="Loading explorations…" />
    </div>

    <div v-else-if="!filtered.length" class="empty" style="--i: 2">
      <Icon name="bookmark" :size="24" />
      <div class="empty-title">No explorations{{ search ? ' match your search' : ' saved yet' }}</div>
      <div class="empty-body">Start a new investigation on the Chat screen — you'll be prompted to save it.</div>
      <Btn variant="primary" as="a" href="/">
        <Icon name="arrow-right" :size="12" /> Go to Chat
      </Btn>
    </div>

    <div v-else class="grid" style="--i: 2">
      <article
        v-for="(e, i) in filtered"
        :key="e.id"
        class="ex-card"
        :class="{ 'is-pinned': e.pinned }"
        :style="{ '--i': i + 2 }"
        @click="openId = e.id"
      >
        <header class="ex-head">
          <div class="ex-kicker">
            <span class="ex-id mono">{{ e.short_id }}</span>
            <span class="ex-dot" />
            <span class="ex-time">{{ ago(e.created_at) }}</span>
          </div>
          <div class="ex-head-actions">
            <button
              type="button"
              class="ex-icon-btn"
              :class="{ 'is-active': e.pinned }"
              :aria-pressed="e.pinned"
              :aria-label="e.pinned ? 'Unpin' : 'Pin'"
              @click.stop="togglePin(e)"
            >
              <Icon :name="e.pinned ? 'pin' : 'pin'" :size="13" />
            </button>
            <div class="ex-menu-wrap" @click.stop>
              <button
                type="button"
                class="ex-icon-btn"
                aria-label="More"
                @click="openMenuId = openMenuId === e.id ? null : e.id"
              >
                <Icon name="more-horizontal" :size="14" />
              </button>
              <div v-if="openMenuId === e.id" class="ex-menu" role="menu">
                <button type="button" class="ex-menu-item" @click="openId = e.id; openMenuId = null">
                  <Icon name="eye" :size="12" /> Open
                </button>
                <button type="button" class="ex-menu-item" @click="shareLink(e)">
                  <Icon name="link" :size="12" /> Copy link
                </button>
                <button type="button" class="ex-menu-item">
                  <Icon name="copy" :size="12" /> Duplicate
                </button>
                <button type="button" class="ex-menu-item">
                  <Icon name="download" :size="12" /> Export JSON
                </button>
                <div class="ex-menu-sep" />
                <button type="button" class="ex-menu-item is-danger" @click="removeExploration(e)">
                  <Icon name="trash-2" :size="12" /> Delete
                </button>
              </div>
            </div>
          </div>
        </header>

        <h3 class="ex-title">{{ e.title }}</h3>
        <p class="ex-body">{{ e.answer_preview }}</p>

        <footer class="ex-foot">
          <div class="ex-meta">
            <span class="meta-item">
              <Icon name="quote" :size="11" />
              <span class="num">{{ e.cite_count }}</span> cites
            </span>
            <span class="meta-item">
              <Icon name="flask-conical" :size="11" />
              <span class="num">{{ e.trial_count }}</span> trials
            </span>
            <span v-if="e.verified" class="verified-badge">
              <Icon name="check" :size="10" /> Verified
            </span>
            <span v-else class="unverified-badge">
              <Icon name="alert-triangle" :size="10" /> Unverified
            </span>
          </div>
          <div class="ex-scores">
            <div class="score">
              <span class="score-label">Entail</span>
              <span class="score-val num">{{ e.scores.entail.toFixed(2) }}</span>
            </div>
            <div class="score">
              <span class="score-label">Retrieve</span>
              <span class="score-val num">{{ e.scores.retrieve.toFixed(2) }}</span>
            </div>
            <div class="score">
              <span class="score-label">Latency</span>
              <span class="score-val num">{{ e.scores.latency_s.toFixed(1) }}s</span>
            </div>
            <svg class="spark" viewBox="0 0 56 20" preserveAspectRatio="none" aria-hidden="true">
              <path :d="sparkPath(e.id)" fill="none" stroke="currentColor" stroke-width="0.75" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </div>
        </footer>
      </article>
    </div>

    <!-- ═══════════ DETAIL DRAWER (lightweight preview; full detail route is a v2) ═══════════ -->
    <transition name="drawer">
      <div v-if="openId" class="drawer-backdrop" @click.self="openId = null">
        <aside class="drawer">
          <template v-if="items.find((x) => x.id === openId)">
            <header class="drawer-head">
              <div class="drawer-titles">
                <div class="drawer-kicker mono">{{ items.find((x) => x.id === openId)!.short_id }}</div>
                <h3 class="drawer-title">{{ items.find((x) => x.id === openId)!.title }}</h3>
              </div>
              <button type="button" class="drawer-close" @click="openId = null" aria-label="Close">
                <Icon name="x" :size="16" />
              </button>
            </header>
            <div class="drawer-body">
              <div class="drawer-section">
                <div class="section-head">QUESTION</div>
                <div class="drawer-question">{{ items.find((x) => x.id === openId)!.question }}</div>
              </div>
              <div class="drawer-section">
                <div class="section-head">ANSWER PREVIEW</div>
                <div class="drawer-answer">{{ items.find((x) => x.id === openId)!.answer_preview }}</div>
              </div>
              <div class="drawer-scores">
                <div class="d-score">
                  <div class="d-score-label">Entail</div>
                  <div class="d-score-val num">{{ items.find((x) => x.id === openId)!.scores.entail.toFixed(2) }}</div>
                </div>
                <div class="d-score">
                  <div class="d-score-label">Retrieve</div>
                  <div class="d-score-val num">{{ items.find((x) => x.id === openId)!.scores.retrieve.toFixed(2) }}</div>
                </div>
                <div class="d-score">
                  <div class="d-score-label">Latency</div>
                  <div class="d-score-val num">{{ items.find((x) => x.id === openId)!.scores.latency_s.toFixed(1) }}s</div>
                </div>
                <div class="d-score">
                  <div class="d-score-label">Iterations</div>
                  <div class="d-score-val num">{{ items.find((x) => x.id === openId)!.scores.iterations }}</div>
                </div>
              </div>
              <div class="drawer-section">
                <div class="section-head">CITATIONS · {{ items.find((x) => x.id === openId)!.citations.length }}</div>
                <div class="d-cites">
                  <div
                    v-for="(c, i) in items.find((x) => x.id === openId)!.citations"
                    :key="c.chunk_id"
                    class="d-cite"
                  >
                    <span class="d-cid mono">c{{ i + 1 }}</span>
                    <div class="d-cite-body">
                      <div class="d-cite-head">
                        <span class="mono">{{ c.trial_id }}</span>
                        <span class="text-muted">{{ c.section }}</span>
                        <span class="num d-cite-score">{{ c.score.toFixed(2) }}</span>
                      </div>
                      <div class="d-cite-text">"{{ c.text }}"</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <footer class="drawer-foot">
              <Btn variant="secondary"><Icon name="copy" :size="12" /> Duplicate</Btn>
              <Btn variant="primary" as="a" href="/"><Icon name="message-square" :size="12" /> Re-open in Chat</Btn>
            </footer>
          </template>
        </aside>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.page {
  padding: 20px 30px 40px;
  max-width: 1400px; margin: 0 auto;
  display: flex; flex-direction: column; gap: 20px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px; align-items: end;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: var(--shadow-sm);
}
.toolbar-seg {
  display: inline-flex; gap: 16px; align-items: end;
}
@media (max-width: 900px) {
  .toolbar { grid-template-columns: 1fr; }
  .toolbar-seg { flex-wrap: wrap; }
}

.loading {
  padding: 60px 20px; display: flex; justify-content: center;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 12px;
}
.empty {
  padding: 60px 20px; text-align: center;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  color: var(--color-neutral-500);
}
.empty-title { font-family: var(--font-heading); font-weight: 600; font-size: 18px; color: var(--color-neutral-700); }
.empty-body { font-size: 13px; max-width: 400px; }

/* ── Card grid ─────────────────────────────────────────── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.ex-card {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  padding: 16px 18px;
  display: flex; flex-direction: column; gap: 10px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  min-height: 220px;
  transition: border-color 140ms, transform 140ms, box-shadow 140ms;
  animation: card-in 320ms cubic-bezier(.22,.68,.35,1) both;
  animation-delay: calc(min(var(--i, 0), 12) * 30ms);
  position: relative;
}
@keyframes card-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

.ex-card:hover {
  border-color: color-mix(in srgb, var(--color-accent) 45%, var(--color-divider));
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
.ex-card.is-pinned {
  border-left: 3px solid var(--color-accent);
  padding-left: calc(18px - 2px);
}

.ex-head {
  display: flex; align-items: center; justify-content: space-between;
}
.ex-kicker {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.ex-id { color: var(--color-accent-700); }
.ex-dot { width: 3px; height: 3px; border-radius: 50%; background: var(--color-neutral-400); }
.ex-time { color: var(--color-neutral-500); letter-spacing: 0.06em; text-transform: none; font-weight: 500; }

.ex-head-actions { display: inline-flex; gap: 2px; }
.ex-icon-btn {
  width: 26px; height: 26px; padding: 0;
  border: 1px solid transparent; background: transparent;
  color: var(--color-neutral-500);
  border-radius: 6px; cursor: pointer;
  display: inline-grid; place-items: center;
  transition: background 120ms, color 120ms, border-color 120ms;
}
.ex-icon-btn:hover {
  background: var(--color-neutral-100); color: var(--color-text);
  border-color: var(--color-divider);
}
.ex-icon-btn.is-active { color: var(--color-accent-700); background: var(--color-accent-100); }

.ex-menu-wrap { position: relative; }
.ex-menu {
  position: absolute; top: calc(100% + 4px); right: 0; z-index: 10;
  min-width: 180px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  box-shadow: var(--shadow-md);
  padding: 4px;
  animation: menu-in 160ms ease-out both;
}
@keyframes menu-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
.ex-menu-item {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 8px 10px;
  border: 0; background: transparent;
  font-family: var(--font-body); font-size: 12.5px;
  color: var(--color-text); text-align: left;
  border-radius: 6px; cursor: pointer;
  transition: background 100ms;
}
.ex-menu-item:hover { background: var(--color-neutral-100); }
.ex-menu-item.is-danger { color: #8b3025; }
.ex-menu-item.is-danger:hover { background: #fbeceb; }
.ex-menu-sep { height: 1px; background: var(--color-divider); margin: 4px 2px; }

.ex-title {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 17px; line-height: 1.25;
  color: var(--color-text); margin: 0;
  text-wrap: pretty;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.ex-body {
  margin: 0; font-size: 12.5px; line-height: 1.55;
  color: var(--color-neutral-600);
  display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.ex-foot {
  padding-top: 10px;
  border-top: 1px dashed var(--color-divider);
  display: flex; flex-direction: column; gap: 8px;
}
.ex-meta {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  font-size: 11px; color: var(--color-neutral-600);
}
.meta-item { display: inline-flex; align-items: center; gap: 4px; }
.meta-item :deep(svg) { color: var(--color-neutral-500); }

.verified-badge, .unverified-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 99px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 9.5px; letter-spacing: 0.08em; text-transform: uppercase;
}
.verified-badge   { background: var(--color-accent-100); color: var(--color-accent-800); }
.unverified-badge { background: #fdf7e5;                 color: #7a5a00; }

.ex-scores {
  display: flex; align-items: center; gap: 12px;
  padding-top: 2px;
}
.score { display: inline-flex; flex-direction: column; gap: 1px; min-width: 50px; }
.score-label {
  font-family: var(--font-body); font-weight: 600;
  font-size: 8.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-500);
}
.score-val { font-size: 12px; color: var(--color-neutral-800); }
.spark {
  margin-left: auto;
  width: 56px; height: 20px;
  color: var(--color-accent-700);
  flex: none;
}

/* ── Drawer (shared style with Corpus drawer) ────────────── */
.drawer-backdrop {
  position: fixed; inset: 0; z-index: 50;
  background: color-mix(in srgb, var(--color-neutral-900) 40%, transparent);
  backdrop-filter: blur(2px);
  display: flex; justify-content: flex-end;
}
.drawer {
  width: min(600px, 100%); height: 100%;
  background: #fff;
  border-left: 1px solid var(--color-divider);
  display: flex; flex-direction: column;
  box-shadow: -18px 0 40px color-mix(in srgb, #2b2b2d 20%, transparent);
}
.drawer-head {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 20px 22px 16px;
  border-bottom: 1px solid var(--color-divider);
}
.drawer-titles { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.drawer-kicker { font-size: 11px; letter-spacing: 0.08em; color: var(--color-accent-700); font-weight: 600; }
.drawer-title {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 22px; line-height: 1.25; color: var(--color-text); margin: 0;
}
.drawer-close {
  flex: none; width: 32px; height: 32px;
  border: 1px solid var(--color-divider); border-radius: 8px;
  background: #fff; color: var(--color-neutral-700);
  cursor: pointer; display: grid; place-items: center;
  transition: background 120ms, border-color 120ms;
}
.drawer-close:hover { background: var(--color-neutral-100); border-color: color-mix(in srgb, var(--color-text) 30%, transparent); }

.drawer-body {
  flex: 1; min-height: 0; overflow-y: auto;
  padding: 20px 22px;
  display: flex; flex-direction: column; gap: 20px;
}
.drawer-section { display: flex; flex-direction: column; gap: 8px; }
.section-head {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
}
.drawer-question {
  padding: 12px 14px;
  background: var(--color-accent-100);
  border-left: 3px solid var(--color-accent);
  border-radius: 8px;
  font-size: 14px; line-height: 1.55;
  color: var(--color-accent-900);
}
.drawer-answer {
  font-size: 13.5px; line-height: 1.7;
  color: var(--color-text);
  text-wrap: pretty;
}

.drawer-scores {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
}
.d-score {
  padding: 10px 12px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  display: flex; flex-direction: column; gap: 3px;
}
.d-score-label { font-size: 9.5px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--color-neutral-600); font-weight: 600; }
.d-score-val { font-family: var(--font-heading); font-size: 20px; font-weight: 600; color: var(--color-text); }

.d-cites { display: flex; flex-direction: column; gap: 8px; }
.d-cite {
  display: grid; grid-template-columns: 30px 1fr; gap: 10px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-left: 3px solid var(--color-accent);
  border-radius: 8px;
}
.d-cid {
  display: inline-grid; place-items: center;
  padding: 1px 6px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-size: 10px; font-weight: 700;
}
.d-cite-body { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.d-cite-head { display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--color-neutral-600); }
.d-cite-score { margin-left: auto; color: var(--color-neutral-700); }
.d-cite-text { font-size: 12.5px; line-height: 1.55; color: var(--color-neutral-800); }

.drawer-foot {
  padding: 14px 22px; border-top: 1px solid var(--color-divider);
  background: var(--color-neutral-100);
  display: flex; justify-content: flex-end; gap: 8px;
}

.drawer-enter-active, .drawer-leave-active { transition: opacity 200ms ease; }
.drawer-enter-active .drawer, .drawer-leave-active .drawer { transition: transform 240ms cubic-bezier(.32,.72,.33,1); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }
</style>
