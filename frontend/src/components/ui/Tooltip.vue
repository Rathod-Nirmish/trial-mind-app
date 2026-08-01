<script setup lang="ts">
import {
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
  TooltipPortal,
  TooltipContent,
  TooltipArrow,
} from "reka-ui";

withDefaults(
  defineProps<{
    content: string;
    side?: "top" | "right" | "bottom" | "left";
    align?: "start" | "center" | "end";
    delay?: number;
  }>(),
  { side: "top", align: "center", delay: 300 },
);
</script>

<template>
  <TooltipProvider :delay-duration="delay">
    <TooltipRoot>
      <TooltipTrigger as-child>
        <slot />
      </TooltipTrigger>
      <TooltipPortal>
        <TooltipContent
          :side="side"
          :align="align"
          :side-offset="6"
          class="z-50 rounded-md bg-neutral-900 text-white text-xs font-body
                 px-2.5 py-1.5 shadow-md max-w-xs
                 data-[state=delayed-open]:animate-tm-rise"
        >
          {{ content }}
          <TooltipArrow class="fill-neutral-900" :width="10" :height="5" />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>
