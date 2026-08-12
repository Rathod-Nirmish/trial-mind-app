<script setup lang="ts">
import { ref } from 'vue';
import {
  Blueprint, Btn, Card, Tag, Field, TextInput, TextArea,
  Radio, Checkbox, Seg, Icon, PageHeader, RowCard, Loader,
} from '../components/industry';

const text = ref('');
const long = ref('The retriever combines BM25 and vector search via reciprocal rank fusion.');
const seg = ref<'hybrid' | 'bm25' | 'vector'>('hybrid');
const scope = ref<'all' | 'mine' | 'shared'>('all');
const radio = ref('phase-3');
const checks = ref({ phase1: false, phase2: true, phase3: true, phase4: false });

const tableRows = [
  { nct: 'NCT01234567', title: 'Semaglutide in T2D', phase: 'III', status: 'Completed', chunks: 412, score: '0.914' },
  { nct: 'NCT02233445', title: 'Adherence in adolescent obesity', phase: 'II', status: 'Recruiting', chunks: 128, score: '0.842' },
  { nct: 'NCT03344556', title: 'GLP-1 pharmacokinetics', phase: 'I', status: 'Completed', chunks: 96, score: '0.798' },
];
</script>

<template>
  <div class="showcase">
    <div class="showcase-inner tm-enter">
      <PageHeader
        style="--i: 0"
        kicker="DESIGN SYSTEM · INDUSTRY"
        title="UI Kit"
      >
        <template #subtitle>
          Blueprint wireframe · steel accent · Barlow Condensed / Barlow · Lucide 1.5
        </template>
        <template #actions>
          <Btn variant="ghost">
            <Icon name="external-link" />
            Docs
          </Btn>
          <Btn variant="secondary" kbd="⌘K">
            <Icon name="command" />
            Palette
          </Btn>
          <Btn variant="primary">
            <Icon name="arrow-right" />
            Get started
          </Btn>
        </template>
      </PageHeader>

      <section class="section" style="--i: 1">
        <h6>Buttons</h6>
        <div class="row">
          <Btn variant="primary">Primary</Btn>
          <Btn variant="secondary">Secondary</Btn>
          <Btn variant="ghost">Ghost</Btn>
          <Btn variant="primary" kbd="⇧⏎">Send</Btn>
          <Btn variant="secondary" kbd="⌘K">Palette</Btn>
          <Btn variant="icon"><Icon name="settings" /></Btn>
          <Btn variant="icon"><Icon name="search" /></Btn>
          <Btn variant="icon"><Icon name="download" /></Btn>
        </div>
      </section>

      <section class="section" style="--i: 2">
        <h6>Tags</h6>
        <div class="row">
          <Tag variant="accent">Accent</Tag>
          <Tag variant="accent-2">Accent-2</Tag>
          <Tag variant="neutral">Neutral</Tag>
          <Tag variant="outline">Outline</Tag>
          <Tag variant="warn">Warn</Tag>
          <Tag variant="ghost">Ghost</Tag>
          <Tag variant="outline"><span class="num">c3</span></Tag>
          <Tag variant="outline"><span class="num">0.914</span></Tag>
        </div>
      </section>

      <section class="section" style="--i: 3">
        <h6>Cards · Blueprint</h6>
        <div class="grid-3">
          <Blueprint v-for="i in 3" :key="i">
            <Card
              :kicker="`EXP-004${i}`"
              title="Efficacy of GLP-1 receptor agonists"
            >
              Across 3 phase-3 trials, semaglutide showed a mean HbA1c reduction of
              1.4% versus placebo at 26 weeks.
              <template #meta>
                <Tag variant="outline"><span class="num">7 cites</span></Tag>
                <Tag variant="outline"><span class="num">3 trials</span></Tag>
                <Tag variant="accent">verified</Tag>
              </template>
            </Card>
          </Blueprint>
        </div>
      </section>

      <section class="section" style="--i: 4">
        <h6>Forms</h6>
        <Blueprint no-hover>
          <div class="form-grid">
            <Field label="Question">
              <TextArea v-model="long" autosize />
            </Field>
            <Field label="Search">
              <TextInput v-model="text" placeholder="NCT ID, condition, sponsor…" />
            </Field>
            <Field label="Ranker">
              <Seg
                v-model="seg"
                :options="[
                  { value: 'hybrid', label: 'Hybrid' },
                  { value: 'bm25', label: 'BM25' },
                  { value: 'vector', label: 'Vector' },
                ]"
              />
            </Field>
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
            <Field label="Phase (checkbox)">
              <div class="stack">
                <Checkbox v-model="checks.phase1" label="Phase I" />
                <Checkbox v-model="checks.phase2" label="Phase II" />
                <Checkbox v-model="checks.phase3" label="Phase III" />
                <Checkbox v-model="checks.phase4" label="Phase IV" />
              </div>
            </Field>
            <Field label="Preferred phase (radio)">
              <div class="stack">
                <Radio v-model="radio" name="ph" value="phase-1" label="Phase I" />
                <Radio v-model="radio" name="ph" value="phase-2" label="Phase II" />
                <Radio v-model="radio" name="ph" value="phase-3" label="Phase III" />
                <Radio v-model="radio" name="ph" value="phase-4" label="Phase IV" />
              </div>
            </Field>
          </div>
        </Blueprint>
      </section>

      <section class="section" style="--i: 5">
        <h6>Row list · success state (Runs / Agent history)</h6>
        <p class="section-note">
          Prefer this over tables when each row has 5+ dimensions, a long title,
          or benefits from progressive disclosure (▾ expand). Scans faster,
          hides column-header repetition, and stacks gracefully on narrow viewports.
        </p>
        <div class="rowlist">
          <RowCard interactive>
            <template #kicker>RUN 0148</template>
            <template #status>
              <Tag variant="accent"><Icon name="check" :size="11" />&nbsp;Verified</Tag>
            </template>
            <template #timestamp>Today 14:02 <Icon name="chevron-up" :size="14" /></template>
            What were the eligibility criteria in NCT04368728, and how do they compare with NCT02015429?
            <template #meta>
              <span class="meta-item"><Icon name="quote" :size="12" /><span class="num">3/3</span> citations entailed</span>
              <span class="meta-item"><Icon name="refresh-cw" :size="12" /><span class="num">0</span> retries</span>
              <span class="meta-item"><Icon name="clock" :size="12" /><span class="num">3.1s</span></span>
              <span class="meta-item mono" style="color: var(--color-neutral-500)">NCT04368728 · NCT02015429</span>
            </template>
            <template #expanded>
              <div class="agent-grid">
                <div class="agent-step">
                  <div class="agent-step-head">
                    <span class="agent-step-name">RETRIEVER</span>
                    <span class="num agent-step-time">0.42s</span>
                  </div>
                  <div class="agent-step-body">
                    Hybrid search · <span class="num">8</span> chunks · top score <span class="num">0.91</span>
                  </div>
                </div>
                <div class="agent-step">
                  <div class="agent-step-head">
                    <span class="agent-step-name">ANALYZER</span>
                    <span class="num agent-step-time">1.8s</span>
                  </div>
                  <div class="agent-step-body">
                    Drafted <span class="num">214</span> words · <span class="num">3</span> inline citations
                  </div>
                </div>
                <div class="agent-step">
                  <div class="agent-step-head">
                    <span class="agent-step-name">CITATION-CHECKER</span>
                    <span class="num agent-step-time">0.9s</span>
                  </div>
                  <div class="agent-step-body">
                    <span class="num">3/3</span> citations entailed · <span class="num">0</span> issues
                  </div>
                </div>
              </div>
              <div class="agent-actions">
                <Btn variant="primary"><Icon name="arrow-right" :size="14" /> Open in Workbench</Btn>
                <Btn variant="secondary"><Icon name="refresh-cw" :size="14" /> Re-run question</Btn>
                <Btn variant="ghost"><Icon name="external-link" :size="14" /> View answer</Btn>
              </div>
            </template>
          </RowCard>

          <RowCard interactive>
            <template #kicker>RUN 0147</template>
            <template #status><Tag variant="neutral">Verified after retry</Tag></template>
            <template #timestamp>Today 13:41 <Icon name="chevron-down" :size="14" /></template>
            Which trials reported grade 3 or higher adverse events, and at what rates?
            <template #meta>
              <span class="meta-item"><Icon name="quote" :size="12" /><span class="num">4/4</span> entailed after retry</span>
              <span class="meta-item"><Icon name="refresh-cw" :size="12" /><span class="num">1</span> retry</span>
              <span class="meta-item"><Icon name="clock" :size="12" /><span class="num">7.4s</span></span>
              <span class="meta-item"><span class="num">4</span> trials</span>
            </template>
          </RowCard>

          <RowCard interactive>
            <template #kicker>RUN 0146</template>
            <template #status>
              <Tag variant="accent"><Icon name="check" :size="11" />&nbsp;Verified</Tag>
            </template>
            <template #timestamp>Today 11:18 <Icon name="chevron-down" :size="14" /></template>
            Which trials in the corpus were placebo-controlled, and what were their primary endpoints?
            <template #meta>
              <span class="meta-item"><Icon name="quote" :size="12" /><span class="num">5/5</span> citations entailed</span>
              <span class="meta-item"><Icon name="refresh-cw" :size="12" /><span class="num">0</span> retries</span>
              <span class="meta-item"><Icon name="clock" :size="12" /><span class="num">4.2s</span></span>
              <span class="meta-item"><span class="num">5</span> trials</span>
            </template>
          </RowCard>

          <RowCard interactive>
            <template #kicker>RUN 0145</template>
            <template #status><Tag variant="warn">Answer withheld</Tag></template>
            <template #timestamp>Yesterday 17:55 <Icon name="chevron-down" :size="14" /></template>
            What was the median progression-free survival in the CAR-T lymphoma trial?
            <template #meta>
              <span class="meta-item"><Icon name="alert-triangle" :size="12" /> Insufficient corpus evidence</span>
              <span class="meta-item"><Icon name="refresh-cw" :size="12" /><span class="num">2</span> retries</span>
              <span class="meta-item"><Icon name="clock" :size="12" /><span class="num">6.8s</span></span>
            </template>
          </RowCard>
        </div>
      </section>

      <section class="section" style="--i: 6">
        <h6>Table · when to prefer</h6>
        <p class="section-note">
          Use tables when every row has the same 3–5 dimensions, values are dense
          and comparable column-wise (numbers, IDs), and the user wants to scan
          top-to-bottom by a single column (sort, filter, spot outliers).
        </p>
        <Blueprint no-hover>
          <table class="table">
            <thead>
              <tr>
                <th>NCT ID</th>
                <th>Title</th>
                <th>Phase</th>
                <th>Status</th>
                <th style="text-align: right">Chunks</th>
                <th style="text-align: right">Score</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in tableRows" :key="row.nct">
                <td class="num">{{ row.nct }}</td>
                <td>{{ row.title }}</td>
                <td><Tag variant="ghost">{{ row.phase }}</Tag></td>
                <td>{{ row.status }}</td>
                <td class="num" style="text-align: right">{{ row.chunks }}</td>
                <td class="num" style="text-align: right">{{ row.score }}</td>
              </tr>
            </tbody>
          </table>
        </Blueprint>
      </section>

      <section class="section" style="--i: 6">
        <h6>Row list · failure state treatment</h6>
        <p class="section-note">
          Same 3-card layout, but a failed step gets a <strong>left accent bar in
          warn color</strong>, a warn-tinted head, and a one-line "why" so the
          failure point is instantly readable without leaving the horizontal
          layout. Successful steps stay quiet — visual weight goes to what
          went wrong.
        </p>

        <RowCard interactive>
          <template #kicker>RUN 0145</template>
          <template #status><Tag variant="warn">Answer withheld</Tag></template>
          <template #timestamp>Yesterday 17:55 <Icon name="chevron-up" :size="14" /></template>
          What was the median progression-free survival in the CAR-T lymphoma trial?
          <template #meta>
            <span class="meta-item"><Icon name="clock" :size="12" /><span class="num">6.8s</span> total</span>
            <span class="meta-item"><Icon name="refresh-cw" :size="12" /><span class="num">2</span> retries</span>
            <span class="meta-item warn-meta">
              <Icon name="alert-triangle" :size="12" /> Failed at citation-checker
            </span>
          </template>
          <template #expanded>
            <div class="agent-grid">
              <div class="agent-step">
                <div class="agent-step-head">
                  <span class="agent-step-name">RETRIEVER</span>
                  <span class="num agent-step-time">0.6s</span>
                </div>
                <div class="agent-step-body">
                  Hybrid search · <span class="num">2</span> chunks · top score <span class="num">0.42</span>
                </div>
              </div>
              <div class="agent-step is-warn">
                <div class="agent-step-head">
                  <span class="agent-step-name">
                    <Icon name="alert-triangle" :size="11" />
                    ANALYZER
                  </span>
                  <span class="num agent-step-time">3.2s</span>
                </div>
                <div class="agent-step-body">
                  Low grounding · fallback prompt engaged
                </div>
                <div class="agent-step-why">
                  Only 2 chunks scored above threshold; escalated to checker.
                </div>
              </div>
              <div class="agent-step is-fail">
                <div class="agent-step-head">
                  <span class="agent-step-name">
                    <Icon name="x" :size="11" />
                    CITATION-CHECKER
                  </span>
                  <span class="num agent-step-time">3.0s</span>
                </div>
                <div class="agent-step-body">
                  <span class="num">0/2</span> citations entailed
                </div>
                <div class="agent-step-why">
                  Insufficient corpus evidence — answer withheld to prevent hallucination.
                </div>
              </div>
            </div>
            <div class="agent-actions">
              <Btn variant="primary"><Icon name="refresh-cw" :size="14" /> Retry with expanded corpus</Btn>
              <Btn variant="secondary"><Icon name="arrow-right" :size="14" /> Open in Workbench</Btn>
              <Btn variant="ghost"><Icon name="file-text" :size="14" /> View raw trace</Btn>
            </div>
          </template>
        </RowCard>

        <RowCard interactive>
          <template #kicker>RUN 0147</template>
          <template #status><Tag variant="neutral"><Icon name="refresh-cw" :size="11" />&nbsp;Verified after retry</Tag></template>
          <template #timestamp>Today 13:41 <Icon name="chevron-up" :size="14" /></template>
          Which trials reported grade 3 or higher adverse events, and at what rates?
          <template #meta>
            <span class="meta-item"><Icon name="quote" :size="12" /><span class="num">4/4</span> entailed after retry</span>
            <span class="meta-item"><Icon name="clock" :size="12" /><span class="num">7.4s</span></span>
            <span class="meta-item"><span class="num">4</span> trials</span>
          </template>
          <template #expanded>
            <div class="agent-grid">
              <div class="agent-step">
                <div class="agent-step-head">
                  <span class="agent-step-name">RETRIEVER</span>
                  <span class="num agent-step-time">0.5s · 2.1s</span>
                </div>
                <div class="agent-step-body">
                  Hybrid × 2 (broadened on retry) · <span class="num">12</span> chunks
                </div>
              </div>
              <div class="agent-step">
                <div class="agent-step-head">
                  <span class="agent-step-name">ANALYZER</span>
                  <span class="num agent-step-time">2.2s</span>
                </div>
                <div class="agent-step-body">
                  Drafted <span class="num">186</span> words · <span class="num">4</span> inline citations
                </div>
              </div>
              <div class="agent-step is-retry">
                <div class="agent-step-head">
                  <span class="agent-step-name">
                    <Icon name="refresh-cw" :size="11" />
                    CITATION-CHECKER · 2 iters
                  </span>
                  <span class="num agent-step-time">2.6s</span>
                </div>
                <div class="agent-step-body">
                  <span class="num">4/4</span> entailed after retry · <span class="num">1</span> refined
                </div>
                <div class="agent-step-why">
                  First pass flagged 1 unsupported claim; retrieval broadened and re-checked.
                </div>
              </div>
            </div>
            <div class="agent-actions">
              <Btn variant="primary"><Icon name="arrow-right" :size="14" /> Open in Workbench</Btn>
              <Btn variant="secondary"><Icon name="refresh-cw" :size="14" /> Re-run</Btn>
            </div>
          </template>
        </RowCard>
      </section>

      <section class="section" style="--i: 7">
        <h6>Loaders</h6>
        <p class="section-note">
          Five variants, one primitive. Pick by context — see comments in
          <span class="mono">Loader.vue</span>.
        </p>
        <div class="loader-grid">
          <Blueprint no-hover>
            <div class="loader-cell">
              <Loader variant="spinner" :size="20" label="Spinner · &lt;2s ops" />
            </div>
          </Blueprint>
          <Blueprint no-hover>
            <div class="loader-cell">
              <Loader variant="dots" :size="14" label="Dots · streaming" />
            </div>
          </Blueprint>
          <Blueprint no-hover>
            <div class="loader-cell">
              <Loader variant="pulse" :size="14" label="Pulse · unobtrusive" />
            </div>
          </Blueprint>
          <Blueprint no-hover>
            <div class="loader-cell full">
              <Loader variant="bar" />
              <div class="loader-caption">Bar · full-region</div>
            </div>
          </Blueprint>
          <Blueprint no-hover>
            <div class="loader-cell full">
              <Loader variant="trace" />
              <div class="loader-caption">Trace · agent scan line</div>
            </div>
          </Blueprint>
          <Blueprint no-hover>
            <div class="loader-cell">
              <Loader variant="spinner" :size="16" tone="neutral" label="Neutral tone" />
            </div>
          </Blueprint>
        </div>

        <p class="section-note" style="margin-top: 12px">
          In-context usage examples:
        </p>
        <div class="loader-usage">
          <Btn variant="primary"><Loader variant="spinner" :size="14" tone="neutral" /> Ingesting…</Btn>
          <Tag variant="neutral"><Loader variant="dots" :size="10" tone="neutral" /> Analyzer thinking</Tag>
          <span class="mock-input">
            NCT04368728 <Loader variant="dots" :size="8" tone="neutral" />
          </span>
        </div>
      </section>

      <section class="section" style="--i: 8">
        <h6>Metric plate</h6>
        <div class="grid-2">
          <Blueprint elevation="sm" no-hover>
            <div class="metric">
              <div class="metric-kicker">LATEST · AUG 2</div>
              <div class="metric-value num">0.0<span class="metric-unit">%</span></div>
              <div class="metric-sub">hallucinated citations</div>
              <div class="metric-delta">
                <Icon name="trending-down" :size="14" />
                <span class="num">100%</span> vs no-checker
              </div>
              <div class="metric-meta num">
                entail 0.94 · retrieve 0.87 · runs 10/10 · 4.2s avg
              </div>
            </div>
          </Blueprint>
          <Blueprint elevation="sm" no-hover>
            <div class="metric">
              <div class="metric-kicker">CORPUS</div>
              <div class="metric-value num">1,284</div>
              <div class="metric-sub">trials ingested · 47,912 chunks</div>
              <div class="metric-meta num">
                phase I 214 · II 388 · III 512 · IV 170
              </div>
            </div>
          </Blueprint>
        </div>
      </section>

      <section class="section" style="--i: 9">
        <h6>Chat rail layouts · citations + trace together</h6>
        <p class="section-note">
          Four ways to show both concerns without a tab toggle. Each shows the
          same live-run state (5 trace steps done, 4 citations returned).
          Pick the one that feels right — I'll wire it into the chat page.
        </p>

        <div class="opt-grid">
          <!-- OPTION A: two rails side by side (split rail) -->
          <div class="opt">
            <div class="opt-label"><span class="opt-tag">A</span> Split rail — 2 columns inside the rail</div>
            <div class="opt-frame opt-a">
              <div class="mock-conv">
                <div class="mock-line mock-line-user">You · eligibility criteria for BNT162b2</div>
                <div class="mock-line">TrialMind · BNT162b2 <span class="mock-pill">c1</span> enrolled adults 16+ …</div>
              </div>
              <div class="opt-a-rail">
                <div class="opt-a-col">
                  <div class="opt-col-head">CITATIONS · 4</div>
                  <div class="mock-cite"><span class="mock-cid">c1</span> NCT04368728 · 0.91</div>
                  <div class="mock-cite"><span class="mock-cid">c2</span> NCT04368728 · 0.87</div>
                  <div class="mock-cite"><span class="mock-cid">c3</span> NCT02015429 · 0.84</div>
                  <div class="mock-cite"><span class="mock-cid">c4</span> NCT04280705 · 0.79</div>
                </div>
                <div class="opt-a-col">
                  <div class="opt-col-head">TRACE · 5</div>
                  <div class="mock-tl"><span class="mock-dot on" /> Retriever · 0.4s</div>
                  <div class="mock-tl"><span class="mock-dot on" /> Analyzer · 1.8s</div>
                  <div class="mock-tl"><span class="mock-dot on" /> Checker · 0.9s</div>
                </div>
              </div>
            </div>
            <div class="opt-notes">
              + Both fully visible always<br>
              − Narrower columns; long citation text wraps a lot
            </div>
          </div>

          <!-- OPTION B: inline trace above conv, citations rail -->
          <div class="opt">
            <div class="opt-label"><span class="opt-tag">B</span> Trace as a ribbon above the answer</div>
            <div class="opt-frame opt-b">
              <div class="opt-b-main">
                <div class="mock-ribbon">
                  <span class="rib-step done"><span class="rib-dot" /> Retriever <em>0.4s</em></span>
                  <span class="rib-arrow">→</span>
                  <span class="rib-step done"><span class="rib-dot" /> Analyzer <em>1.8s</em></span>
                  <span class="rib-arrow">→</span>
                  <span class="rib-step done"><span class="rib-dot" /> Checker <em>0.9s</em></span>
                  <span class="rib-total">3.1s total · <a href="#">details</a></span>
                </div>
                <div class="mock-conv">
                  <div class="mock-line mock-line-user">You · eligibility criteria for BNT162b2</div>
                  <div class="mock-line">TrialMind · BNT162b2 <span class="mock-pill">c1</span> enrolled adults 16+ …</div>
                </div>
              </div>
              <div class="opt-b-rail">
                <div class="opt-col-head">CITATIONS · 4</div>
                <div class="mock-cite"><span class="mock-cid">c1</span> NCT04368728 · Results · 0.91</div>
                <div class="mock-cite"><span class="mock-cid">c2</span> NCT04368728 · Methods · 0.87</div>
                <div class="mock-cite"><span class="mock-cid">c3</span> NCT02015429 · Results · 0.84</div>
              </div>
            </div>
            <div class="opt-notes">
              + Citations get the full rail; trace stays glanceable<br>
              − Ribbon eats top of conversation area
            </div>
          </div>

          <!-- OPTION C: floating trace overlay, citations rail -->
          <div class="opt">
            <div class="opt-label"><span class="opt-tag">C</span> Floating trace mini-map (bottom-left)</div>
            <div class="opt-frame opt-c">
              <div class="opt-c-main">
                <div class="mock-conv">
                  <div class="mock-line mock-line-user">You · eligibility criteria for BNT162b2</div>
                  <div class="mock-line">TrialMind · BNT162b2 <span class="mock-pill">c1</span> enrolled adults 16+ …</div>
                </div>
                <div class="mock-composer">Ask about clinical trials…</div>
                <div class="mock-float">
                  <div class="float-head"><span class="rib-dot" /> Agent · 3.1s <em>▸</em></div>
                  <div class="float-line">Retriever · Analyzer · Checker</div>
                </div>
              </div>
              <div class="opt-c-rail">
                <div class="opt-col-head">CITATIONS · 4</div>
                <div class="mock-cite"><span class="mock-cid">c1</span> NCT04368728 · 0.91</div>
                <div class="mock-cite"><span class="mock-cid">c2</span> NCT04368728 · 0.87</div>
                <div class="mock-cite"><span class="mock-cid">c3</span> NCT02015429 · 0.84</div>
                <div class="mock-cite"><span class="mock-cid">c4</span> NCT04280705 · 0.79</div>
              </div>
            </div>
            <div class="opt-notes">
              + Zero rail cost; trace expands on click<br>
              − Floating chrome can feel busy over the composer
            </div>
          </div>

          <!-- OPTION E: 3-column workbench layout — matches material/TrialMind Workbench.dc.html -->
          <div class="opt opt-wide">
            <div class="opt-label">
              <span class="opt-tag">E</span> Three-column workbench — trace left · answer center · sources right
            </div>
            <div class="opt-frame opt-e">
              <!-- LEFT: Agent trace -->
              <div class="opt-e-trace">
                <div class="e-block-head">
                  <span>AGENT TRACE</span>
                  <span class="e-run-id mono">RUN 0148</span>
                </div>

                <div class="e-trace-step">
                  <span class="e-step-icon"><Icon name="search" :size="14" /></span>
                  <div class="e-step-body">
                    <div class="e-step-head">
                      <span class="e-step-name">RETRIEVER</span>
                      <Icon name="check" :size="12" class="e-step-check" />
                      <span class="e-step-time mono">0.42s</span>
                    </div>
                    <div class="e-step-note">Hybrid search · 8 chunks · top 0.91</div>
                  </div>
                </div>

                <div class="e-trace-step">
                  <span class="e-step-icon"><Icon name="pen-tool" :size="14" /></span>
                  <div class="e-step-body">
                    <div class="e-step-head">
                      <span class="e-step-name">ANALYZER</span>
                      <Icon name="check" :size="12" class="e-step-check" />
                      <span class="e-step-time mono">1.8s</span>
                    </div>
                    <div class="e-step-note">Drafted 214 words · 3 inline citations</div>
                  </div>
                </div>

                <div class="e-trace-step">
                  <span class="e-step-icon"><Icon name="shield-check" :size="14" /></span>
                  <div class="e-step-body">
                    <div class="e-step-head">
                      <span class="e-step-name">CITATION-CHECKER</span>
                      <Icon name="check" :size="12" class="e-step-check" />
                      <span class="e-step-time mono">0.9s</span>
                    </div>
                    <div class="e-step-note">3/3 citations entailed · 0 issues</div>
                  </div>
                </div>

                <div class="e-meta-box">
                  <div class="e-meta-row"><span>Iterations</span><span class="mono">0 / 2</span></div>
                  <div class="e-meta-row"><span>Model</span><span class="mono">gemini-2.5-pro</span></div>
                  <div class="e-meta-row"><span>Total latency</span><span class="mono">3.1s</span></div>
                </div>

                <div class="e-verified-chip">
                  <Icon name="check" :size="11" />
                  ANSWER VERIFIED
                </div>
              </div>

              <!-- CENTER: Conversation -->
              <div class="opt-e-conv">
                <!-- User turn: avatar right, bubble right-aligned -->
                <div class="e-turn e-turn-user">
                  <div class="e-user-bubble">
                    What were the eligibility criteria in NCT04368728, and how do they compare with NCT02015429?
                  </div>
                  <div class="e-avatar e-avatar-user">
                    <Icon name="user" :size="14" />
                  </div>
                </div>

                <!-- Assistant turn: avatar left, card with peel corner -->
                <div class="e-turn e-turn-assist">
                  <div class="e-avatar e-avatar-assist">
                    <Icon name="sparkles" :size="14" />
                  </div>
                  <div class="e-assistant-card">
                    <div class="e-assistant-head">
                      <span class="e-assist-name">TRIALMIND</span>
                      <span class="mock-verified">
                        <Icon name="check" :size="10" />
                        VERIFIED
                      </span>
                      <span class="e-assist-time mono">14:02:36</span>
                    </div>
                    <div class="e-assistant-body">
                      NCT04368728 enrolled adults <strong>≥18 years</strong> with confirmed SARS-CoV-2 infection<span class="e-cite-pill">c1</span>. NCT02015429 admitted <strong>18–55</strong> and required BMI 18–30 kg/m²<span class="e-cite-pill">c2</span>.
                    </div>
                    <div class="e-assistant-actions">
                      <button class="e-mini-btn"><Icon name="copy" :size="12" /> Copy</button>
                      <button class="e-mini-btn"><Icon name="download" :size="12" /> Export</button>
                      <button class="e-mini-btn"><Icon name="refresh-cw" :size="12" /> Re-run</button>
                    </div>
                  </div>
                </div>

                <!-- Composer -->
                <div class="e-composer">
                  <Icon name="search" :size="16" class="e-composer-icon" />
                  <span class="e-composer-text">Ask across the corpus — adverse events, outcomes, eligibility…</span>
                  <button class="e-composer-btn">
                    <Icon name="send" :size="12" />
                    Ask
                  </button>
                </div>
              </div>

              <!-- RIGHT: Sources -->
              <div class="opt-e-sources">
                <div class="e-block-head">
                  <span>SOURCES</span>
                  <span class="e-sources-count mono">3&nbsp;CITED / 8&nbsp;RETRIEVED</span>
                </div>

                <div class="e-source-card cited">
                  <div class="e-source-head">
                    <span class="e-source-cid">c1</span>
                    <span class="e-source-nct mono">NCT04368728</span>
                    <span class="e-source-tag cited">CITED</span>
                    <span class="e-source-score mono">0.91</span>
                  </div>
                  <div class="e-source-body">
                    "Inclusion: adults aged 18 years or older with laboratory-confirmed SARS-CoV-2… Exclusion: receipt of any investigational vaccine, immunosuppressive therapy within 180 days…"
                  </div>
                  <div class="e-source-foot">
                    <span class="e-source-section">ELIGIBILITY</span>
                    <span class="e-source-bar"><i style="width:91%" /></span>
                  </div>
                </div>

                <div class="e-source-card cited">
                  <div class="e-source-head">
                    <span class="e-source-cid">c2</span>
                    <span class="e-source-nct mono">NCT02015429</span>
                    <span class="e-source-tag cited">CITED</span>
                    <span class="e-source-score mono">0.84</span>
                  </div>
                  <div class="e-source-body">
                    "Healthy adults 18–55 years of age, body-mass index 18–30 kg/m², willing to comply with all study visits…"
                  </div>
                  <div class="e-source-foot">
                    <span class="e-source-section">ELIGIBILITY</span>
                    <span class="e-source-bar"><i style="width:84%" /></span>
                  </div>
                </div>

                <div class="e-source-card cited">
                  <div class="e-source-head">
                    <span class="e-source-cid">c3</span>
                    <span class="e-source-nct mono">NCT04368728</span>
                    <span class="e-source-tag cited">CITED</span>
                    <span class="e-source-score mono">0.78</span>
                  </div>
                  <div class="e-source-body">
                    "…the protocol was amended to prioritize enrollment of adults over 65 and those with comorbidities at elevated risk of severe disease."
                  </div>
                  <div class="e-source-foot">
                    <span class="e-source-section">DESCRIPTION</span>
                    <span class="e-source-bar"><i style="width:78%" /></span>
                  </div>
                </div>

                <button class="e-source-uncited">
                  <Icon name="chevron-down" :size="12" />
                  Show 5 uncited chunks
                </button>
              </div>
            </div>
            <div class="opt-notes">
              + Everything visible at once · trace + answer + sources all first-class<br>
              + Sources distinguish CITED vs RETRIEVED-BUT-UNCITED (transparency win)<br>
              − Densest layout · needs ≥1280px viewport to breathe
            </div>
          </div>

          <!-- OPTION D: inline trace under each turn -->
          <div class="opt">
            <div class="opt-label"><span class="opt-tag">D</span> Trace bound to its turn (inline under answer)</div>
            <div class="opt-frame opt-d">
              <div class="opt-d-main">
                <div class="mock-conv">
                  <div class="mock-line mock-line-user">You · eligibility criteria for BNT162b2</div>
                  <div class="mock-line">
                    TrialMind · BNT162b2 <span class="mock-pill">c1</span> enrolled adults 16+ …
                  </div>
                  <div class="mock-turn-trace">
                    <div class="ttr-head">
                      <span class="rib-dot" /> Agent trace · 3.1s
                      <span class="ttr-badge">3 steps</span>
                      <em>▸</em>
                    </div>
                    <div class="ttr-inline">Retriever 0.4s → Analyzer 1.8s → Checker 0.9s</div>
                  </div>
                </div>
              </div>
              <div class="opt-d-rail">
                <div class="opt-col-head">CITATIONS · 4</div>
                <div class="mock-cite"><span class="mock-cid">c1</span> NCT04368728 · 0.91</div>
                <div class="mock-cite"><span class="mock-cid">c2</span> NCT04368728 · 0.87</div>
                <div class="mock-cite"><span class="mock-cid">c3</span> NCT02015429 · 0.84</div>
              </div>
            </div>
            <div class="opt-notes">
              + Trace stays with its own turn (great for multi-turn sessions)<br>
              − Repeats per turn; can feel noisy after many questions
            </div>
          </div>
        </div>
      </section>

      <section class="section" style="--i: 10">
        <h6>Skeleton (blueprint hairline shimmer)</h6>
        <div class="grid-3">
          <div class="skel" style="height: 96px" />
          <div class="skel" style="height: 96px" />
          <div class="skel" style="height: 96px" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.showcase {
  min-height: 100%;
  padding: var(--space-6) var(--space-8) var(--space-8);
}
.showcase-inner {
  max-width: 1280px; margin: 0 auto;
  display: flex; flex-direction: column; gap: var(--space-8);
}
.section { display: flex; flex-direction: column; gap: var(--space-3); }
.section > h6 { color: var(--color-accent-700); margin: 0; }
.section-note {
  margin: 0 0 var(--space-2);
  font-size: 12.5px; line-height: 1.55;
  color: var(--color-neutral-600); max-width: 780px;
}
.rowlist { display: flex; flex-direction: column; gap: 10px; }

/* Expanded agent breakdown (variant A — 3 cards) */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.agent-step {
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  padding: 11px 14px;
  display: flex; flex-direction: column; gap: 4px;
}
.agent-step-head {
  display: flex; align-items: center; justify-content: space-between;
}
.agent-step-name {
  font-family: var(--font-body); font-weight: 600;
  font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-accent-800);
}
.agent-step-time { font-size: 12px; color: var(--color-neutral-600); }
.agent-step-body { font-size: 12.5px; color: var(--color-neutral-700); }
.agent-step-why {
  margin-top: 4px; padding-top: 6px;
  border-top: 1px dashed var(--color-divider);
  font-size: 11.5px; line-height: 1.45; color: var(--color-neutral-600);
}
.agent-step-name { display: inline-flex; align-items: center; gap: 5px; }
.agent-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* Failure / retry variants — accent bar + tinted head */
.agent-step {
  border-left: 3px solid transparent;
  padding-left: calc(14px - 3px + 1px);
}
.agent-step.is-warn {
  background: #fdf7e5;
  border-color: #d4a017;
  border-left-color: #d4a017;
}
.agent-step.is-warn .agent-step-name { color: #7a5a00; }
.agent-step.is-warn .agent-step-why { border-top-color: color-mix(in srgb, #d4a017 30%, transparent); color: #7a5a00; }

.agent-step.is-fail {
  background: #fbeceb;
  border-color: #c26b60;
  border-left-color: #c26b60;
}
.agent-step.is-fail .agent-step-name { color: #8b3025; }
.agent-step.is-fail .agent-step-why { border-top-color: color-mix(in srgb, #c26b60 30%, transparent); color: #8b3025; }

.agent-step.is-retry {
  border-left-color: var(--color-accent);
}
.agent-step.is-retry .agent-step-name { color: var(--color-accent-800); }

.warn-meta {
  color: #7a5a00 !important;
  background: #fdf6e0;
  padding: 2px 8px; border-radius: 6px;
  border: 1px solid #d4a017;
}
.warn-meta :deep(svg) { color: #b8860b !important; }

/* Loaders */
.loader-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
}
.loader-cell {
  padding: 22px 18px; display: flex; align-items: center; gap: 10px;
  min-height: 72px;
}
.loader-cell.full { flex-direction: column; align-items: stretch; }
.loader-caption {
  font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--color-neutral-600); margin-top: 8px;
}
.loader-usage { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.mock-input {
  display: inline-flex; align-items: center; gap: 8px;
  background: #fff; border: 1px solid var(--color-divider);
  border-radius: 10px; padding: 8px 12px; font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--color-neutral-700);
}

/* ═════════════════════════ Chat rail layout options ═════════════════════════ */
.opt-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;
}
@media (max-width: 900px) { .opt-grid { grid-template-columns: 1fr; } }

.opt { display: flex; flex-direction: column; gap: 8px; }
.opt-label {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--font-body); font-weight: 600;
  font-size: 12.5px; color: var(--color-text);
}
.opt-tag {
  display: inline-grid; place-items: center;
  width: 22px; height: 22px;
  background: var(--color-accent); color: #fff;
  border-radius: 6px; font-weight: 700; font-size: 11px;
  letter-spacing: 0;
}
.opt-notes {
  font-size: 11.5px; line-height: 1.55; color: var(--color-neutral-600);
  padding: 2px 4px;
}

.opt-frame {
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  padding: 10px;
  min-height: 280px;
  display: flex; gap: 10px;
  position: relative; overflow: hidden;
}

/* shared mock pieces */
.mock-conv {
  background: #fff; border: 1px solid var(--color-divider); border-radius: 8px;
  padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;
  flex: 1; min-height: 100px;
  font-size: 11.5px; color: var(--color-neutral-800); line-height: 1.5;
}
.mock-line-user { color: var(--color-neutral-600); font-size: 10.5px; letter-spacing: 0.06em; text-transform: uppercase; }
.mock-line {
  padding: 6px 8px; background: var(--color-neutral-100); border-radius: 6px;
}
.mock-pill {
  display: inline-block; padding: 0 5px; margin: 0 2px;
  font-family: ui-monospace, monospace; font-size: 9.5px; font-weight: 700;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 3px;
}
.mock-composer {
  margin-top: auto;
  padding: 8px 10px; background: #fff; border: 1px solid var(--color-divider);
  border-radius: 8px; color: var(--color-neutral-500); font-size: 11px;
}
.opt-col-head {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-neutral-600);
  padding: 4px 4px 8px;
}
.mock-cite {
  padding: 6px 8px; font-size: 11px; color: var(--color-neutral-700);
  background: #fff; border: 1px solid var(--color-divider); border-left: 3px solid var(--color-divider);
  border-radius: 6px; margin-bottom: 6px;
  display: flex; align-items: center; gap: 6px;
}
.mock-cid {
  display: inline-grid; place-items: center;
  min-width: 20px; padding: 1px 4px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 3px; font-family: ui-monospace, monospace; font-size: 9.5px; font-weight: 700;
}
.mock-tl {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 6px; font-size: 10.5px; color: var(--color-neutral-700);
}
.mock-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--color-neutral-400);
}
.mock-dot.on { background: var(--color-accent); }

/* OPTION A — split rail */
.opt-a .mock-conv { flex: 1.2; }
.opt-a-rail {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
  flex: 1.4; min-width: 0;
}
.opt-a-col {
  background: #fff; border: 1px solid var(--color-divider); border-radius: 8px;
  padding: 8px; display: flex; flex-direction: column; min-width: 0;
}
.opt-a-col .mock-cite,
.opt-a-col .mock-tl { font-size: 10px; padding: 5px 6px; }
.opt-a-col .mock-cite { border-left-color: var(--color-accent-300); }

/* OPTION B — trace ribbon on top */
.opt-b-main { display: flex; flex-direction: column; gap: 10px; flex: 2; min-width: 0; }
.opt-b-rail {
  flex: 1.2; min-width: 0;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 8px;
  padding: 8px;
}
.mock-ribbon {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px 10px;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 8px;
  font-size: 10.5px;
}
.rib-step {
  display: inline-flex; align-items: center; gap: 5px;
  color: var(--color-neutral-700);
}
.rib-step.done { color: var(--color-accent-800); }
.rib-step em { font-style: normal; color: var(--color-neutral-500); font-size: 10px; }
.rib-arrow { color: var(--color-neutral-400); font-size: 12px; }
.rib-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--color-accent); box-shadow: 0 0 0 2px var(--color-accent-100);
}
.rib-total {
  margin-left: auto; font-family: ui-monospace, monospace;
  font-size: 10px; color: var(--color-neutral-500);
}
.rib-total a { color: var(--color-accent-700); }

/* OPTION C — floating mini-map */
.opt-c-main { flex: 2; min-width: 0; display: flex; flex-direction: column; gap: 10px; position: relative; }
.opt-c-rail {
  flex: 1.2; min-width: 0;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 8px;
  padding: 8px;
}
.mock-float {
  position: absolute; left: 10px; bottom: 10px;
  background: #fff; border: 1px solid var(--color-accent);
  border-radius: 10px; padding: 8px 10px;
  box-shadow: 0 6px 18px color-mix(in srgb, var(--color-accent) 20%, transparent);
  min-width: 200px;
  animation: float-in 300ms ease-out both;
}
@keyframes float-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.float-head {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 600; color: var(--color-accent-800);
}
.float-head em { margin-left: auto; font-style: normal; color: var(--color-neutral-500); }
.float-line { font-size: 10.5px; color: var(--color-neutral-600); margin-top: 4px; }

/* OPTION D — per-turn trace */
.opt-d-main { flex: 2; min-width: 0; }
.opt-d-rail {
  flex: 1.2; min-width: 0;
  background: #fff; border: 1px solid var(--color-divider); border-radius: 8px;
  padding: 8px;
}
.mock-turn-trace {
  margin-left: 12px;
  padding: 8px 10px;
  background: var(--color-accent-100);
  border-left: 2px solid var(--color-accent);
  border-radius: 0 8px 8px 0;
  font-size: 10.5px; color: var(--color-accent-800);
}
.ttr-head { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.ttr-head em { margin-left: auto; font-style: normal; color: var(--color-neutral-500); }
.ttr-badge {
  padding: 1px 6px; background: #fff; border: 1px solid var(--color-accent-300);
  border-radius: 99px; font-size: 9.5px; font-weight: 600;
}
.ttr-inline { margin-top: 4px; color: var(--color-neutral-700); }

/* ═══════════ OPTION E — 3-column workbench (matches material/) ═══════════ */
.opt-wide { grid-column: 1 / -1; }

.opt-e {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 280px;
  gap: 14px;
  min-height: 520px;
  padding: 14px;
  background: var(--color-bg);
}

/* All three columns use identical framing */
.opt-e-trace,
.opt-e-sources {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  padding: 14px;
  display: flex; flex-direction: column; gap: 10px;
  min-width: 0;
  box-shadow: var(--shadow-sm);
}
.opt-e-conv {
  background: var(--color-neutral-100);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex; flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.e-block-head {
  display: flex; align-items: center; justify-content: space-between;
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--color-neutral-600);
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-divider);
  margin-bottom: 2px;
}
.e-run-id,
.e-sources-count {
  color: var(--color-neutral-500);
  font-size: 9.5px; letter-spacing: 0.08em;
  text-transform: none;
}

/* ── LEFT: trace steps ─────────────────────────────────────────────── */
.e-trace-step {
  display: grid; grid-template-columns: 28px 1fr; gap: 10px;
  padding: 10px 2px;
  border-bottom: 1px solid var(--color-divider);
}
.e-trace-step:last-of-type { border-bottom: 0; }

.e-step-icon {
  width: 28px; height: 28px; border-radius: 8px;
  background: var(--color-accent-100);
  color: var(--color-accent-700);
  display: inline-grid; place-items: center;
}
.e-step-body { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.e-step-head {
  display: flex; align-items: center; gap: 6px;
}
.e-step-name {
  font-family: var(--font-body); font-weight: 600;
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--color-accent-800);
}
.e-step-check { color: var(--color-accent-700); flex: none; }
.e-step-time {
  margin-left: auto;
  font-size: 11px; color: var(--color-neutral-600);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.e-step-note {
  font-size: 11.5px; line-height: 1.5; color: var(--color-neutral-700);
}

.e-meta-box {
  margin-top: 8px; padding: 12px 14px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  display: flex; flex-direction: column; gap: 8px;
}
.e-meta-row {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: 11px; color: var(--color-neutral-600);
}
.e-meta-row .mono {
  color: var(--color-neutral-800);
  font-size: 11.5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.e-verified-chip {
  align-self: flex-start;
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 700;
  font-size: 10px; letter-spacing: 0.14em;
  margin-top: 6px;
}

/* ── CENTER: conversation ──────────────────────────────────────────── */
.e-turn {
  display: flex; gap: 10px;
  align-items: flex-start;
}
.e-turn-user { align-self: flex-end; max-width: 72%; }
.e-turn-assist { align-self: flex-start; max-width: 88%; }

.e-avatar {
  width: 34px; height: 34px; flex: none;
  border-radius: 10px;
  display: inline-grid; place-items: center;
}
.e-avatar-user {
  background: var(--color-neutral-200);
  color: var(--color-neutral-700);
}
.e-avatar-assist {
  background: var(--color-accent);
  color: #fff;
}

/* Peel-corner bubbles — the signature Workbench treatment */
.e-user-bubble {
  background: var(--color-accent); color: #fff;
  padding: 12px 16px;
  border-radius: 14px 14px 3px 14px;
  box-shadow: var(--shadow-sm);
  font-size: 13px; line-height: 1.55;
}
.e-assistant-card {
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 3px 14px 14px 14px;
  padding: 16px 20px;
  display: flex; flex-direction: column; gap: 10px;
  box-shadow: var(--shadow-md);
  min-width: 0;
}
.e-assistant-head {
  display: flex; align-items: center; gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-divider);
}
.e-assist-name {
  font-family: var(--font-heading); font-weight: 600;
  font-size: 13px; letter-spacing: 0.06em;
  color: var(--color-accent-800);
}
.mock-verified {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 9px;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  font-family: var(--font-body); font-weight: 500;
  font-size: 10px; letter-spacing: 0.06em;
}
.e-assist-time {
  margin-left: auto;
  font-size: 11px; color: var(--color-neutral-500);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.e-assistant-body {
  font-size: 13px; line-height: 1.65;
  color: var(--color-text);
  text-wrap: pretty;
}

/* Inline citation pill — small, monospace, rounded, ties to the source */
.e-cite-pill {
  display: inline-block;
  padding: 1px 7px; margin: 0 2px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; font-weight: 600;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
  vertical-align: 1px;
  cursor: pointer;
  transition: background 120ms, color 120ms;
}
.e-cite-pill:hover { background: var(--color-accent); color: #fff; }

.e-assistant-actions {
  display: flex; gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--color-divider);
}
.e-mini-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 8px;
  background: transparent; border: 1px solid var(--color-divider);
  color: var(--color-neutral-700);
  font-family: var(--font-body); font-weight: 500;
  font-size: 12px; cursor: pointer;
  transition: background 120ms, border-color 120ms, color 120ms;
}
.e-mini-btn:hover {
  background: var(--color-neutral-100);
  border-color: color-mix(in srgb, var(--color-text) 25%, transparent);
  color: var(--color-text);
}

/* Composer pill */
.e-composer {
  margin-top: auto;
  display: flex; align-items: center; gap: 10px;
  padding: 6px 6px 6px 16px;
  background: #fff;
  border: 1px solid var(--color-divider);
  border-radius: 12px;
}
.e-composer-icon { color: var(--color-neutral-500); flex: none; }
.e-composer-text {
  flex: 1; color: var(--color-neutral-500); font-size: 13px;
}
.e-composer-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px;
  background: var(--color-accent); color: #fff;
  border: 0; border-radius: 9px;
  font-family: var(--font-body); font-weight: 500;
  font-size: 12.5px; cursor: pointer;
}
.e-composer-btn:hover { background: var(--color-accent-600); }

/* ── RIGHT: sources ────────────────────────────────────────────────── */
.e-source-card {
  padding: 12px 14px;
  border: 1px solid var(--color-divider);
  border-radius: 10px;
  display: flex; flex-direction: column; gap: 8px;
  background: #fff;
  transition: border-color 120ms;
}
.e-source-card:hover { border-color: color-mix(in srgb, var(--color-accent) 40%, var(--color-divider)); }
.e-source-card.cited { border-color: color-mix(in srgb, var(--color-accent) 35%, var(--color-divider)); }

.e-source-head {
  display: flex; align-items: center; gap: 7px;
}
.e-source-cid {
  display: inline-grid; place-items: center;
  min-width: 22px; padding: 1px 7px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; font-weight: 600;
  background: var(--color-accent-100); color: var(--color-accent-800);
  border-radius: 99px;
}
.e-source-nct {
  font-size: 10.5px; color: var(--color-accent-700); font-weight: 600;
}
.e-source-tag {
  padding: 1px 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 9.5px; font-weight: 600;
  letter-spacing: 0.04em;
  background: #fff; color: var(--color-accent-700);
  border: 1px solid var(--color-accent-300);
  border-radius: 99px;
}
.e-source-tag.cited { background: var(--color-accent-100); color: var(--color-accent-800); border-color: transparent; }
.e-source-score {
  margin-left: auto;
  font-size: 11px; color: var(--color-neutral-600);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.e-source-body {
  font-size: 12px; line-height: 1.55;
  color: var(--color-neutral-800);
  margin: 0;
  display: -webkit-box; -webkit-line-clamp: 4; line-clamp: 4; -webkit-box-orient: vertical;
  overflow: hidden;
}
.e-source-foot {
  display: flex; align-items: center; gap: 10px;
  padding-top: 4px;
  border-top: 1px dashed var(--color-divider);
}
.e-source-section {
  font-family: var(--font-body); font-weight: 600;
  font-size: 9px; letter-spacing: 0.14em;
  color: var(--color-neutral-600);
  text-transform: uppercase;
}
.e-source-bar {
  flex: 1; height: 4px; background: var(--color-neutral-200);
  border-radius: 99px; overflow: hidden;
}
.e-source-bar i {
  display: block; height: 100%;
  background: var(--color-accent);
  border-radius: 99px;
}

.e-source-uncited {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 14px;
  background: transparent;
  border: 1px dashed var(--color-neutral-400);
  border-radius: 10px;
  color: var(--color-neutral-700);
  font-family: var(--font-body); font-weight: 500;
  font-size: 12px; cursor: pointer;
  transition: color 120ms, border-color 120ms, background 120ms;
}
.e-source-uncited:hover {
  color: var(--color-accent-700);
  border-color: var(--color-accent);
  background: var(--color-accent-100);
}
.row { display: flex; flex-wrap: wrap; gap: var(--space-3); align-items: center; }
.stack { display: flex; flex-direction: column; gap: var(--space-2); }
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-4); }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.form-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4) var(--space-6); padding: var(--space-4);
}
.form-grid > :first-child { grid-column: 1 / -1; }

.metric { padding: var(--space-4); display: flex; flex-direction: column; gap: 6px; }
.metric-kicker {
  font-family: var(--font-heading); font-weight: var(--font-heading-weight);
  font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--color-accent-700);
}
.metric-value {
  font-family: var(--font-heading); font-weight: 700;
  font-size: 72px; line-height: 1; color: var(--color-text);
}
.metric-unit { font-size: 32px; margin-left: 4px; color: var(--color-accent-700); }
.metric-sub {
  font-size: 13px; color: color-mix(in srgb, var(--color-text) 60%, transparent);
  margin-top: 4px;
}
.metric-delta {
  display: inline-flex; align-items: center; gap: 4px; margin-top: var(--space-2);
  color: var(--color-accent-700); font-size: 12px;
}
.metric-meta {
  margin-top: var(--space-3);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-divider);
  font-size: 11px; color: color-mix(in srgb, var(--color-text) 55%, transparent);
  letter-spacing: 0.04em;
}
</style>
