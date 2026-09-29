import { useSettingsStore } from '@/api/settings'
import { t, type MessageKey } from '@/i18n'

export class ApiError extends Error {
  constructor(message: string, public code: string | number, public traceId: string | null = null) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface Health { status: string; version: string; agent_provider: string; tools: number; auth_required?: boolean }
export interface Robot {
  robotSn: string
  /** Online flag returned by list_robots; the list page relies on it alone to split online/offline. */
  online?: boolean
  displayName?: string
  modelTypeCode?: string
  modelFamilyCode?: string
  softwareVersion?: string
  hardwareVersion?: string
  [key: string]: unknown
}
export interface RobotStatus {
  robotSn: string
  onlineStatus?: string
  batteryPercent?: number
  charging?: boolean
  currentMapName?: string
  currentMapId?: string
  workState?: number
  work_state_name?: string
  work_state_desc?: string
  taskName?: string
  observedMsTimestamp?: number
  /** Localization on the current map: grid cells (origin bottom-left, y up), angle in degrees (0 = +x, CCW). */
  position?: {
    angle?: number
    gridPosition?: { x?: number; y?: number }
    mapInfo?: MapInfo
    worldPosition?: { position?: { x?: number; y?: number; z?: number } }
  }
  /** Backend fallback placeholder: false on upstream 230003, with `error` (including trace_id). */
  reachable?: boolean
  error?: { code?: string | number; message?: string; trace_id?: string | null }
  [key: string]: unknown
}
export interface RobotMap { mapId: string; displayName: string; mapVersionId?: string }
export interface MapInfo { gridWidth?: number; gridHeight?: number; resolution?: number; originX?: number; originY?: number }
export interface MapCanvas {
  mapPng?: { downloadUri?: string; exist?: boolean }
  mapInfo?: MapInfo
}
/** Map positions: gridX / gridY arrive as strings from map resources and as numbers from charging positions. */
export interface MapPosition { mapResourceId?: string; mapResourceName?: string; positionName?: string; positionType?: string; gridX?: string | number; gridY?: string | number }
export interface MapResources { maps?: { mapId?: string; positions?: MapPosition[] }[] }
export interface ChargingPositions { mapId?: string; positions?: MapPosition[] }
export interface TaskDefinition { fusionTaskId: string; taskName: string; loopCount?: number }
export interface TaskReport {
  id?: string
  robotSerialNumber?: string
  displayName?: string
  cleaningMode?: string
  startTime?: number
  endTime?: number
  actualCleaningAreaSquareMeter?: number
  durationSeconds?: number
  completionPercentage?: number
}
export interface Page<T> {
  list?: T[]
  robotTaskReports?: T[]
  count?: number
  totalSize?: number
  page?: number
  pagesize?: number
}
/** SSE error events persisted with the session; after_message = messages.length when it happened. */
export interface SessionError { message: string; at: number; after_message: number; code?: string }
export interface AgentSession {
  session_id: string
  title?: string | null
  messages: { role: string; content: unknown; tool_calls?: unknown[] }[]
  errors?: SessionError[]
  created_at: number
  updated_at?: number
  message_count?: number
}
export interface SessionSummary { session_id: string; title: string | null; created_at: number; updated_at: number; message_count: number }
export interface SessionPage { items: SessionSummary[]; total: number; page: number; page_size: number }

export function apiUrl(path: string): string {
  return `${useSettingsStore().apiBase}${path}`
}

export function apiHeaders(): Headers {
  const headers = new Headers()
  const key = useSettingsStore().apiKey
  if (key) headers.set('X-API-Key', key)
  return headers
}

export const AUTH_REQUIRED_EVENT = 'saodi:auth-required'

/** Business / HTTP codes the UI explains in its own language. Server text is shown only for codes not listed here. */
const CODE_MESSAGES: Record<string, MessageKey> = {
  // upstream business codes / HTTP
  110003: 'errors.robotNotBound',
  100026: 'errors.rateLimited',
  230003: 'errors.robotUnreachable',
  401: 'auth.message',
  // SSE `error.code` from the agent (docs/ARCHITECTURE_V3.md §4)
  incomplete_response: 'errors.agentIncomplete',
  max_turns: 'errors.agentMaxTurns',
  provider_auth: 'errors.agentProviderAuth',
  provider_rate_limited: 'errors.agentProviderRateLimited',
  provider_http: 'errors.agentProviderUnavailable',
  provider_connection: 'errors.agentProviderUnavailable',
  provider_error: 'errors.agentProviderUnavailable',
  internal_error: 'errors.internal',
}

/** Localized text for a structured error code; falls back to the server message, then to a generic one. */
export function messageForCode(code: string | number | null | undefined, fallback?: string | null): string {
  const key = code == null ? undefined : CODE_MESSAGES[String(code)]
  return key ? t(key) : fallback || t('errors.requestFailed')
}

export async function parseResponse<T>(response: Response): Promise<T> {
  const body: unknown = await response.json().catch(() => null)
  if (response.status === 401) {
    // Never surface the raw envelope; App.vue listens and guides the user to #/settings.
    window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT))
    throw new ApiError(t('auth.message'), 401)
  }
  if (!response.ok) {
    const envelope = body as { error?: { code?: string | number; message?: string; trace_id?: string | null } } | null
    const code = envelope?.error?.code ?? response.status
    throw new ApiError(messageForCode(code, envelope?.error?.message ?? t('errors.requestFailedStatus', { status: response.status })), code, envelope?.error?.trace_id ?? null)
  }
  return body as T
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  apiHeaders().forEach((value, key) => headers.set(key, value))
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  return parseResponse<T>(await fetch(apiUrl(path), { ...init, headers }))
}

const root = '/api/v1'
const robotPath = (sn: string) => `${root}/robots/${encodeURIComponent(sn)}`
const sessionPath = (id: string) => `${root}/agent/sessions/${encodeURIComponent(id)}`
const post = <T>(path: string, data: unknown = {}) => apiFetch<T>(path, { method: 'POST', body: JSON.stringify(data) })

export const health = () => apiFetch<Health>(`${root}/health`)
export const authCheck = () => apiFetch<{ ok: boolean }>(`${root}/auth/check`)
export const listRobots = (page = 1) => apiFetch<Robot[] | Page<Robot>>(`${root}/robots?page=${page}&page_size=100`)
export const batchRobotStatus = (robot_sn_list: string[]) => post<RobotStatus[] | Page<RobotStatus>>(`${root}/robots/status`, { robot_sn_list })
export const getRobotStatus = (sn: string) => apiFetch<RobotStatus>(`${robotPath(sn)}/status`)
export const listMaps = (sn: string) => apiFetch<RobotMap[] | Page<RobotMap>>(`${robotPath(sn)}/maps`)
export const getMapCanvas = (sn: string, mapId: string) => apiFetch<MapCanvas>(`${robotPath(sn)}/maps/${encodeURIComponent(mapId)}/canvas`)
export const getMapResources = (sn: string, mapId: string) => apiFetch<MapResources>(`${robotPath(sn)}/maps/${encodeURIComponent(mapId)}/resources`)
/** Read-only tools without a dedicated REST route go through the registry's generic endpoint. Only list read-only names here. */
type ReadOnlyTool = 'list_charging_positions'
const callTool = async <T>(name: ReadOnlyTool, args: Record<string, unknown>) => (await post<{ result: T }>(`${root}/tools/${name}`, args)).result
export const listChargingPositions = (sn: string, mapId: string) => callTool<ChargingPositions>('list_charging_positions', { robot_sn: sn, map_id: mapId })
export const getCapabilities = (sn: string) => apiFetch<unknown>(`${robotPath(sn)}/capabilities`)
export const listTaskDefinitions = (sn: string, page = 1) => apiFetch<TaskDefinition[] | Page<TaskDefinition>>(`${robotPath(sn)}/task-definitions?page=${page}&pagesize=100`)
export const startTask = (sn: string, fusionTaskId: string, loopCount?: number) => post<unknown>(`${robotPath(sn)}/tasks/start`, { fusion_task_id: fusionTaskId, ...(loopCount === undefined ? {} : { loop_count: loopCount }) })
export const pauseTask = (sn: string) => post<unknown>(`${robotPath(sn)}/tasks/pause`)
export const resumeTask = (sn: string) => post<unknown>(`${robotPath(sn)}/tasks/resume`)
export const stopTask = (sn: string) => post<unknown>(`${robotPath(sn)}/tasks/stop`)
export const navigateHome = (sn: string, mapId: string, mapResourceId?: string) => post<unknown>(`${robotPath(sn)}/navigation/go-home`, { map_id: mapId, ...(mapResourceId ? { map_resource_id: mapResourceId } : {}) })
export const listReports = (sn: string, page = 1) => apiFetch<TaskReport[] | Page<TaskReport>>(`${robotPath(sn)}/reports?page=${page}&pagesize=20`)
export const createAgentSession = () => post<{ session_id: string }>(`${root}/agent/sessions`)
export const getAgentSession = (id: string) => apiFetch<AgentSession>(sessionPath(id))
export const listAgentSessions = (page = 1, pageSize = 50) => apiFetch<SessionPage>(`${root}/agent/sessions?page=${page}&page_size=${pageSize}`)
export const deleteAgentSession = (id: string) => apiFetch<void>(sessionPath(id), { method: 'DELETE' })
export const confirmAgent = (id: string, confirmId: string, approve: boolean) => post<{ ok: boolean }>(`${sessionPath(id)}/confirm`, { confirm_id: confirmId, approve })

/** Upstream 230003: the platform cannot route to the robot, i.e. it is offline or has not reached the cloud for a while. */
export const ROBOT_UNREACHABLE = 230003

export function isRobotUnreachable(e: unknown): boolean {
  return e instanceof ApiError && Number(e.code) === ROBOT_UNREACHABLE
}

/** Shared localized error text for robot pages; traceId is shown separately in the detail view, never in toasts. */
export function robotErrorMessage(e: unknown): string {
  if (isRobotUnreachable(e)) return t('errors.robotUnreachable')
  return e instanceof Error ? e.message : t('errors.requestFailed')
}

export function pageItems<T>(data: T[] | Page<T>): T[] {
  return Array.isArray(data) ? data : (data.list ?? data.robotTaskReports ?? [])
}
