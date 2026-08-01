<script setup lang="ts">
import { ref } from "vue";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Checkbox,
  Dialog,
  Icon,
  IconButton,
  Input,
  ProgressBar,
  RadioGroup,
  SegmentedControl,
  Skeleton,
  Table,
  Tag,
  Textarea,
  Tooltip,
} from "@/components/ui";
import { toast } from "@/lib/useToast";

const text = ref("");
const bigText = ref("");
const checked = ref(false);
const partial = ref<boolean | "indeterminate">("indeterminate");
const view = ref("verified");
const radio = ref("nct1");
const dialogOpen = ref(false);
</script>

<template>
  <div class="min-h-full">
    <header class="bg-white border-b border-divider px-8 py-5">
      <h1>TrialMind UI kit</h1>
      <p class="text-sm text-neutral-700 mt-1">
        Every primitive — hover, focus, and disabled states are themed. Consumed by every screen.
      </p>
    </header>

    <main class="max-w-6xl mx-auto px-8 py-10 flex flex-col gap-10">
      <!-- Buttons -->
      <section>
        <h5 class="mb-4">Buttons</h5>
        <div class="flex flex-wrap items-end gap-3">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button disabled>Disabled</Button>
          <Button size="sm">Small</Button>
          <Button size="lg">Large</Button>
          <Button>
            <Icon :size="14"><path d="m22 2-7 20-4-9-9-4z" /><path d="M22 2 11 13" /></Icon>
            With icon
          </Button>
        </div>
        <div class="mt-4 flex items-center gap-3">
          <IconButton label="Search">
            <Icon :size="16"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></Icon>
          </IconButton>
          <IconButton variant="solid" label="Send">
            <Icon :size="14"><path d="m22 2-7 20-4-9-9-4z" /><path d="M22 2 11 13" /></Icon>
          </IconButton>
          <IconButton variant="outline" label="Menu">
            <Icon :size="16"><path d="M4 6h16M4 12h16M4 18h16" /></Icon>
          </IconButton>
        </div>
      </section>

      <!-- Tags & Badges -->
      <section>
        <h5 class="mb-4">Tags & badges</h5>
        <div class="flex flex-wrap items-center gap-2">
          <Tag variant="accent" uppercase>VERIFIED</Tag>
          <Tag variant="neutral" uppercase>NCT04368728</Tag>
          <Tag variant="outline" uppercase>CHECK FAILED</Tag>
          <Tag variant="accent" mono>c1</Tag>
          <Tag variant="neutral">Phase 3</Tag>
          <span class="ml-4 inline-flex items-center gap-2">
            <Badge>3</Badge>
            <Badge variant="neutral">12</Badge>
            <Badge variant="dot" />
            <span class="text-xs text-neutral-700">Live</span>
          </span>
        </div>
      </section>

      <!-- Inputs -->
      <section>
        <h5 class="mb-4">Inputs</h5>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs uppercase tracking-wider text-neutral-600">Question</label>
            <Input v-model="text" placeholder="Ask about clinical trials…" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs uppercase tracking-wider text-neutral-600">Disabled</label>
            <Input disabled placeholder="Unavailable" />
          </div>
          <div class="flex flex-col gap-1.5 md:col-span-2">
            <label class="text-xs uppercase tracking-wider text-neutral-600">NCT IDs — one per line</label>
            <Textarea v-model="bigText" mono placeholder="NCT01234567&#10;NCT07654321" :rows="4" />
          </div>
        </div>
      </section>

      <!-- Choices -->
      <section>
        <h5 class="mb-4">Choices</h5>
        <div class="flex flex-wrap gap-8">
          <div class="flex flex-col gap-2">
            <Checkbox v-model="checked" label="Include results & adverse-event sections" />
            <Checkbox v-model="partial" label="Indeterminate example" />
            <Checkbox disabled label="Disabled" />
          </div>
          <RadioGroup
            v-model="radio"
            :options="[
              { value: 'nct1', label: 'NCT04368728' },
              { value: 'nct2', label: 'NCT02015429' },
              { value: 'nct3', label: 'NCT03760146', disabled: true },
            ]"
          />
          <SegmentedControl
            v-model="view"
            :options="[
              { value: 'empty', label: 'Empty' },
              { value: 'streaming', label: 'Streaming' },
              { value: 'verified', label: 'Verified' },
              { value: 'retry', label: 'Retry' },
            ]"
          />
        </div>
      </section>

      <!-- Card + Avatar + Progress + Skeleton -->
      <section>
        <h5 class="mb-4">Surfaces</h5>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <div class="flex items-center gap-3">
              <Avatar name="Ravi Kumar" />
              <div>
                <p class="text-sm font-medium">Ravi Kumar</p>
                <p class="text-xs text-neutral-600">Portfolio demo</p>
              </div>
            </div>
          </Card>
          <Card>
            <p class="text-xs uppercase tracking-wider text-neutral-600 mb-2">Indexing progress</p>
            <ProgressBar :value="64" />
            <p class="text-xs text-neutral-600 mt-2">64% · NCT05605899</p>
          </Card>
          <Card>
            <p class="text-xs uppercase tracking-wider text-neutral-600 mb-2">Loading</p>
            <div class="flex flex-col gap-2">
              <Skeleton height="14px" width="80%" />
              <Skeleton height="14px" width="60%" />
              <Skeleton height="14px" width="70%" />
            </div>
          </Card>
        </div>
      </section>

      <!-- Table -->
      <section>
        <h5 class="mb-4">Table</h5>
        <Table>
          <thead>
            <tr>
              <th style="width: 130px">NCT ID</th>
              <th>Title / condition</th>
              <th style="width: 90px">Phase</th>
              <th style="width: 110px">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr data-interactive>
              <td class="font-mono text-xs text-accent-800 font-semibold">NCT04368728</td>
              <td>
                <p class="text-sm font-medium">Adaptive COVID-19 Treatment Trial</p>
                <p class="text-xs text-neutral-600">SARS-CoV-2 infection</p>
              </td>
              <td><Tag variant="neutral">Phase 3</Tag></td>
              <td><Tag variant="accent" uppercase>Indexed</Tag></td>
            </tr>
            <tr data-interactive>
              <td class="font-mono text-xs text-accent-800 font-semibold">NCT02015429</td>
              <td>
                <p class="text-sm font-medium">Vaccine Safety Study</p>
                <p class="text-xs text-neutral-600">Healthy adults</p>
              </td>
              <td><Tag variant="neutral">Phase 1</Tag></td>
              <td><Tag variant="outline" uppercase>Indexing</Tag></td>
            </tr>
          </tbody>
        </Table>
      </section>

      <!-- Overlays -->
      <section>
        <h5 class="mb-4">Overlays</h5>
        <div class="flex flex-wrap gap-3">
          <Button @click="dialogOpen = true">Open dialog</Button>
          <Tooltip content="Hybrid search over the ClinicalTrials.gov corpus">
            <Button variant="secondary">Hover for tooltip</Button>
          </Tooltip>
          <Button
            variant="secondary"
            @click="toast({ title: 'Answer verified', message: '3 of 3 citations entailed the answer.' })"
          >
            Show toast
          </Button>
          <Button
            variant="secondary"
            @click="toast({ title: 'Retry failed', message: 'Gemini rate-limited after 2 attempts.', variant: 'error' })"
          >
            Show error toast
          </Button>
        </div>
        <Dialog
          v-model:open="dialogOpen"
          title="Add trials to the corpus"
          description="Fetched from ClinicalTrials.gov, then chunked and embedded automatically."
        >
          <div class="flex flex-col gap-3">
            <label class="text-xs uppercase tracking-wider text-neutral-600">
              NCT IDs — one per line
            </label>
            <Textarea mono placeholder="NCT01234567&#10;NCT07654321" :rows="4" />
            <Checkbox v-model="checked" label="Include results & adverse-event sections when available" />
          </div>
          <template #actions>
            <Button variant="ghost" @click="dialogOpen = false">Cancel</Button>
            <Button @click="dialogOpen = false">Add</Button>
          </template>
        </Dialog>
      </section>
    </main>
  </div>
</template>
