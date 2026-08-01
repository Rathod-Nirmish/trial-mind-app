<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <main class="min-h-screen flex items-center justify-center p-8">
    <div class="max-w-lg space-y-4 text-center">
      <h1 class="text-3xl font-semibold">TrialMind</h1>
      <p class="text-neutral-600">
        Multi-agent clinical research assistant — portfolio demo, not a medical
        decision-support tool.
      </p>
      <RouterLink
        to="/ui-kit"
        class="inline-block underline text-sm text-neutral-500 hover:text-neutral-900"
      >
        View UI kit →
      </RouterLink>
    </div>
  </main>
</template>
