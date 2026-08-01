<script setup lang="ts">
/**
 * Toast — imperative API via useToast() (../lib/useToast).
 * This file exports the viewport that must be mounted once (in App.vue).
 */
import { computed } from "vue";
import {
  ToastProvider,
  ToastRoot,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastViewport,
} from "reka-ui";
import Icon from "./Icon.vue";
import { toasts, dismiss } from "@/lib/useToast";

const items = computed(() => toasts.value);
</script>

<template>
  <ToastProvider :swipe-direction="'right'">
    <ToastRoot
      v-for="t in items"
      :key="t.id"
      :open="true"
      :duration="t.duration ?? 4000"
      class="flex items-start gap-3 bg-white border border-divider rounded-lg shadow-md
             p-3 pr-8 w-[340px]
             data-[state=open]:animate-tm-rise
             data-[swipe=move]:translate-x-[var(--reka-toast-swipe-move-x)]
             data-[swipe=cancel]:translate-x-0 data-[swipe=cancel]:transition-transform
             data-[swipe=end]:translate-x-[var(--reka-toast-swipe-end-x)] data-[swipe=end]:transition-transform"
      :class="t.variant === 'error' && 'border-accent-700'"
      @update:open="(v) => !v && dismiss(t.id)"
    >
      <span class="w-6 h-6 grid place-items-center rounded-full flex-none mt-0.5"
            :class="t.variant === 'error' ? 'bg-accent-100 text-accent-800' : 'bg-accent-100 text-accent-800'">
        <Icon v-if="t.variant === 'error'" :size="14" :stroke-width="2">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
          <path d="M12 9v4M12 17h.01" />
        </Icon>
        <Icon v-else :size="14" :stroke-width="2.5">
          <path d="M20 6 9 17l-5-5" />
        </Icon>
      </span>
      <div class="flex-1 min-w-0">
        <ToastTitle v-if="t.title" class="font-heading font-semibold text-sm text-text">
          {{ t.title }}
        </ToastTitle>
        <ToastDescription class="text-xs text-neutral-700 mt-0.5 leading-snug">
          {{ t.message }}
        </ToastDescription>
      </div>
      <ToastClose
        aria-label="Dismiss"
        class="absolute top-2 right-2 w-6 h-6 grid place-items-center rounded-full
               text-neutral-500 hover:bg-neutral-200"
      >
        <Icon :size="12">
          <path d="M18 6 6 18M6 6l12 12" />
        </Icon>
      </ToastClose>
    </ToastRoot>
    <ToastViewport
      class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 outline-none"
    />
  </ToastProvider>
</template>
