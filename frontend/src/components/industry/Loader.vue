<script setup lang="ts">
/**
 * Loader family — 5 variants tuned to the Industry aesthetic.
 *   spinner : classic arc (default) — best for < 2s ops next to an action
 *   dots    : 3 bouncing dots — best for streaming / "thinking" states
 *   bar     : indeterminate progress bar — best for full-region loads
 *   pulse   : soft square pulse — best next to text, unobtrusive
 *   trace   : the agent-timeline "scan" — best inside a container that has steps
 * label prop appears next to the loader in small caps.
 */
withDefaults(
  defineProps<{
    variant?: 'spinner' | 'dots' | 'bar' | 'pulse' | 'trace';
    size?: number;
    label?: string;
    tone?: 'accent' | 'neutral';
  }>(),
  { variant: 'spinner', size: 16, tone: 'accent' }
);
</script>

<template>
  <span class="ldr" :class="[`ldr-${variant}`, `ldr-${tone}`]" role="status">
    <!-- SPINNER -->
    <svg v-if="variant === 'spinner'" :width="size" :height="size" viewBox="0 0 24 24" class="ldr-svg">
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.18" />
      <path d="M12 3 a9 9 0 0 1 9 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    </svg>

    <!-- DOTS -->
    <span v-else-if="variant === 'dots'" class="ldr-dots" :style="{ '--sz': `${Math.max(4, size / 3)}px` }">
      <i /><i /><i />
    </span>

    <!-- BAR -->
    <span v-else-if="variant === 'bar'" class="ldr-bar"><i /></span>

    <!-- PULSE -->
    <span v-else-if="variant === 'pulse'" class="ldr-pulse" :style="{ width: `${size}px`, height: `${size}px` }" />

    <!-- TRACE (scan line) -->
    <span v-else-if="variant === 'trace'" class="ldr-trace"><i /></span>

    <span v-if="label" class="ldr-label">{{ label }}</span>
  </span>
</template>

<style scoped>
.ldr { display: inline-flex; align-items: center; gap: 8px; }
.ldr-accent  { color: var(--color-accent-700); }
.ldr-neutral { color: var(--color-neutral-500); }

.ldr-label {
  font-family: var(--font-body); font-weight: 500;
  font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
  color: inherit;
}

/* SPINNER */
.ldr-svg { display: block; animation: ldr-spin 900ms linear infinite; }
@keyframes ldr-spin { to { transform: rotate(360deg); } }

/* DOTS */
.ldr-dots { display: inline-flex; gap: 3px; align-items: center; }
.ldr-dots i {
  width: var(--sz, 5px); height: var(--sz, 5px);
  background: currentColor; border-radius: 50%;
  animation: ldr-dot 900ms ease-in-out infinite;
}
.ldr-dots i:nth-child(2) { animation-delay: 120ms; }
.ldr-dots i:nth-child(3) { animation-delay: 240ms; }
@keyframes ldr-dot {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40%           { transform: translateY(-3px); opacity: 1; }
}

/* BAR */
.ldr-bar {
  display: block; position: relative;
  width: 100%; min-width: 80px; height: 2px;
  background: color-mix(in srgb, currentColor 14%, transparent);
  overflow: hidden; border-radius: 2px;
}
.ldr-bar i {
  position: absolute; inset: 0 auto 0 0; width: 40%;
  background: currentColor;
  animation: ldr-bar 1.3s cubic-bezier(.4,.0,.2,1) infinite;
}
@keyframes ldr-bar {
  0%   { transform: translateX(-100%); }
  60%  { transform: translateX(180%); }
  100% { transform: translateX(180%); }
}

/* PULSE */
.ldr-pulse {
  display: inline-block; border-radius: 4px;
  background: currentColor; opacity: 0.6;
  animation: ldr-pulse 1.2s ease-in-out infinite;
}
@keyframes ldr-pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.92); }
  50%      { opacity: 0.75; transform: scale(1); }
}

/* TRACE — scanning line */
.ldr-trace {
  display: block; position: relative;
  width: 100%; min-width: 100px; height: 1px;
  background: var(--color-divider);
  overflow: hidden;
}
.ldr-trace i {
  position: absolute; inset: 0 auto 0 0; width: 30%;
  background: linear-gradient(90deg,
    transparent,
    color-mix(in srgb, currentColor 65%, transparent),
    color-mix(in srgb, currentColor 100%, transparent),
    color-mix(in srgb, currentColor 65%, transparent),
    transparent);
  animation: ldr-trace 1.4s linear infinite;
}
@keyframes ldr-trace {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}

@media (prefers-reduced-motion: reduce) {
  .ldr-svg, .ldr-dots i, .ldr-bar i, .ldr-pulse, .ldr-trace i { animation: none; }
}
</style>
