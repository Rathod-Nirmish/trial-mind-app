<script setup lang="ts">
import {
  DialogRoot,
  DialogPortal,
  DialogOverlay,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "reka-ui";
import Icon from "./Icon.vue";

withDefaults(
  defineProps<{
    open?: boolean;
    title?: string;
    description?: string;
    width?: string;
  }>(),
  { open: false, width: "480px" },
);

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
}>();
</script>

<template>
  <DialogRoot :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogPortal>
      <DialogOverlay
        class="fixed inset-0 bg-neutral-900/40 z-50
               data-[state=open]:animate-tm-rise"
      />
      <DialogContent
        class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50
               bg-bg border border-divider rounded-lg shadow-lg
               w-[min(var(--dw),92vw)] max-h-[85vh] flex flex-col
               data-[state=open]:animate-tm-rise
               focus:outline-none"
        :style="{ '--dw': width }"
      >
        <div v-if="title || description" class="px-6 pt-5 pb-2">
          <DialogTitle v-if="title" as="h5" class="m-0">{{ title }}</DialogTitle>
          <DialogDescription
            v-if="description"
            class="mt-1 text-xs text-neutral-700"
          >
            {{ description }}
          </DialogDescription>
        </div>

        <div class="px-6 py-4 flex-1 overflow-y-auto">
          <slot />
        </div>

        <div v-if="$slots.actions" class="px-6 pb-5 pt-2 flex gap-2 justify-end border-t border-divider">
          <slot name="actions" />
        </div>

        <DialogClose
          class="absolute top-3 right-3 w-7 h-7 grid place-items-center rounded-full
                 bg-neutral-200 text-neutral-700 hover:bg-neutral-300
                 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          aria-label="Close"
        >
          <Icon :size="14">
            <path d="M18 6 6 18M6 6l12 12" />
          </Icon>
        </DialogClose>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
