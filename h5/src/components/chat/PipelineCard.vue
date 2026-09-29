<script setup lang="ts">
import { computed } from 'vue'
import { Button } from 'vant'
import ToolCallCard from '@/components/ToolCallCard.vue'
import type { ToolItem } from '@/components/ToolGroup.vue'
import type { Confirmation } from './timeline'
import { t, type MessageKey } from '@/i18n'

// A dangerous tool as a pipeline: confirm → sent (the tool's own result) → delivery (a later
// get_command_status / wait_for_command for the same requestId, if the agent made one).
// cmdStatus 6 means the command reached the robot, not that the job finished; the labels say so.
const props = defineProps<{ confirm: Confirmation; tool?: ToolItem; followUps: ToolItem[] }>()
const emit = defineEmits<{ respond: [approve: boolean] }>()
type State = 'idle' | 'wait' | 'run' | 'ok' | 'fail' | 'skip' | 'no'
type Out = { requestId?: unknown; cmdStatus?: unknown; cmdResultCode?: unknown; cmdResultMessage?: unknown; timed_out?: unknown }

const out = (tool?: ToolItem) => (tool?.output && typeof tool.output === 'object' ? tool.output : {}) as Out
const requestId = computed(() => { const id = out(props.tool).requestId; return typeof id === 'string' && id ? id : undefined })
const delivery = computed(() => {
  if (!requestId.value) return undefined
  const matches = props.followUps.filter(f => (f.input as { request_id?: unknown })?.request_id === requestId.value && f.output !== undefined)
  return matches[matches.length - 1]
})
const steps = computed<{ key: string; label: MessageKey; state: State; detail?: string }[]>(() => {
  const answered = props.confirm.answered
  const confirmState: State = props.confirm.expired ? 'no' : answered === undefined ? 'wait' : answered ? 'ok' : 'no'
  let sent: State = 'idle', sentDetail: string | undefined
  if (answered === false || props.confirm.expired) sent = 'skip'
  else if (answered && props.tool) {
    sent = props.tool.output === undefined ? 'run' : props.tool.isError ? 'fail' : 'ok'
    sentDetail = sent === 'ok' && requestId.value ? t('pipeline.requestId', { id: requestId.value }) : undefined
  }
  let deliver: State = sent === 'skip' ? 'skip' : 'idle', deliverDetail: string | undefined
  const d = delivery.value
  if (sent === 'fail') deliver = 'skip'
  else if (d) {
    const o = out(d)
    if (d.isError) { deliver = 'fail' }
    else if (o.cmdStatus === 6) { deliver = 'ok'; deliverDetail = t('pipeline.deliveredHint') }
    else if (o.timed_out) { deliver = 'fail'; deliverDetail = t('pipeline.timedOut') }
    else if ([0, 1, 2].includes(o.cmdStatus as number)) deliver = 'run'
    else { deliver = 'fail'; deliverDetail = typeof o.cmdResultMessage === 'string' && o.cmdResultMessage ? o.cmdResultMessage : undefined }
  } else if (sent === 'ok') deliverDetail = t('pipeline.notChecked')
  return [
    { key: 'confirm', label: 'pipeline.stepConfirm', state: confirmState },
    { key: 'sent', label: 'pipeline.stepSent', state: sent, detail: sentDetail },
    { key: 'delivery', label: 'pipeline.stepDelivery', state: deliver, detail: deliverDetail },
  ]
})
const overall = computed<{ tone: 'wait' | 'ok' | 'fail' | 'run' | 'off'; label: MessageKey }>(() => {
  const [c, s, d] = steps.value.map(step => step.state)
  if (c === 'wait') return { tone: 'wait', label: 'pipeline.awaiting' }
  if (c === 'no') return { tone: 'off', label: props.confirm.expired ? 'pipeline.unanswered' : 'pipeline.rejected' }
  if (s === 'fail' || d === 'fail') return { tone: 'fail', label: 'pipeline.failed' }
  if (d === 'ok') return { tone: 'ok', label: 'pipeline.delivered' }
  if (s === 'ok') return { tone: 'ok', label: 'pipeline.accepted' }
  return { tone: 'run', label: 'pipeline.running' }
})
// Title and the corner tag come from the same `overall` state (live and replay alike).
const title = computed(() => t('pipeline.title', { state: t(overall.value.label), name: props.confirm.name }))
</script>

<template>
  <section class="pipeline" :class="overall.tone">
    <header class="head">
      <span class="badge" aria-hidden="true">
        <svg v-if="overall.tone === 'ok'" viewBox="0 0 24 24"><path d="M6 12.5l4 4 8-9" /></svg>
        <svg v-else-if="overall.tone === 'fail'" viewBox="0 0 24 24"><path d="M8 8l8 8M16 8l-8 8" /></svg>
        <svg v-else viewBox="0 0 24 24"><path d="M12 7v5l3 2" /><circle cx="12" cy="12" r="8" /></svg>
      </span>
      <div class="titles">
        <strong>{{ title }}</strong>
        <p class="summary">{{ confirm.summary }}</p>
      </div>
      <span class="state">{{ t(overall.label) }}</span>
    </header>
    <ol class="steps">
      <li v-for="(step, i) in steps" :key="step.key" :class="step.state">
        <span class="node" aria-hidden="true">{{ step.state === 'ok' ? '✓' : step.state === 'fail' ? '!' : step.state === 'no' ? '×' : i + 1 }}</span>
        <div class="step-text"><b>{{ t(step.label) }}</b><small>{{ t(`pipeline.state.${step.state}` as MessageKey) }}<template v-if="step.detail"> · {{ step.detail }}</template></small></div>
      </li>
    </ol>
    <ToolCallCard :name="confirm.name" :input="confirm.input" />
    <div v-if="confirm.answered === undefined && !confirm.expired" class="actions">
      <Button size="small" type="primary" :loading="confirm.pending" @click="emit('respond', true)">{{ t('chat.approve') }}</Button>
      <Button size="small" :disabled="confirm.pending" @click="emit('respond', false)">{{ t('chat.reject') }}</Button>
    </div>
  </section>
</template>

<style scoped>
.pipeline { padding: 14px; border-radius: var(--sd-r-lg); background: var(--sd-surface); box-shadow: var(--sd-shadow-1), inset 0 0 0 1px var(--sd-warning-line); font-size: var(--sd-fs-sm); }
.pipeline.ok, .pipeline.run, .pipeline.off { box-shadow: var(--sd-shadow-1); }
.pipeline.fail { box-shadow: var(--sd-shadow-1), inset 0 0 0 1px var(--sd-danger-soft); }
.head { display: flex; align-items: flex-start; gap: 10px; }
.badge { flex: none; display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; background: var(--sd-warning-soft); }
.badge svg { width: 20px; height: 20px; fill: none; stroke: var(--sd-warning); stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }
.ok .badge { background: var(--sd-success); }
.ok .badge svg { stroke: var(--sd-on-primary); }
.run .badge { background: var(--sd-primary-soft); }
.run .badge svg { stroke: var(--sd-primary); }
.fail .badge { background: var(--sd-danger-soft); }
.fail .badge svg { stroke: var(--sd-danger); }
.off .badge { background: var(--sd-surface-2); }
.off .badge svg { stroke: var(--sd-muted); }
.titles { flex: 1; min-width: 0; }
.titles strong { display: block; font-size: var(--sd-fs-md); color: var(--sd-ink); overflow-wrap: anywhere; }
.summary { margin: 3px 0 0; color: var(--sd-muted); font-size: var(--sd-fs-xs); overflow-wrap: anywhere; }
.state { flex: none; padding: 3px 10px; border-radius: var(--sd-r-pill); font-size: var(--sd-fs-xs); font-weight: 650; color: var(--sd-warning); background: var(--sd-warning-soft); }
.ok .state { color: var(--sd-success); background: var(--sd-success-soft); }
.run .state { color: var(--sd-primary); background: var(--sd-primary-soft); }
.fail .state { color: var(--sd-danger); background: var(--sd-danger-soft); }
.off .state { color: var(--sd-muted); background: var(--sd-surface-2); }
.steps { list-style: none; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; margin: 12px 0; padding: 10px; border-radius: var(--sd-r-md); background: var(--sd-surface-2); }
.steps li { display: flex; align-items: flex-start; gap: 7px; min-width: 0; }
.node { flex: none; display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--sd-line); color: var(--sd-muted); font-size: var(--sd-fs-2xs); font-weight: 700; }
.steps .ok .node { background: var(--sd-success); color: var(--sd-on-primary); }
.steps .wait .node, .steps .run .node { background: var(--sd-primary); color: var(--sd-on-primary); }
.steps .fail .node { background: var(--sd-danger); color: var(--sd-on-primary); }
.step-text { display: flex; flex-direction: column; min-width: 0; }
.step-text b { font-size: var(--sd-fs-xs); color: var(--sd-ink); }
.step-text small { font-size: var(--sd-fs-2xs); color: var(--sd-muted); overflow-wrap: anywhere; }
.skip .step-text b, .idle .step-text b, .no .step-text b { color: var(--sd-muted); }
.actions { display: flex; gap: 10px; margin-top: 12px; }
.pipeline :deep(.dot) { display: none; }
</style>
