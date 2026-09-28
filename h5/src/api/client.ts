import { useSettingsStore } from '@/stores/settings'

export class ApiError extends Error {
  constructor(message: string, public code: string | number, public traceId: string | null = null) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface Health { status: string; version: string; agent_provider: string; tools: number }
export interface Robot { robotSn: string; [key: string]: unknown }
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
  [key: string]: unknown
}
export interface RobotMap { mapId: string; displayName: string; mapVersionId?: string }
export interface MapCanvas {
  mapPng?: { downloadUri?: string; exist?: boolean }
  mapInfo?: { gridWidth?: number; gridHeight?: number; resolution?: number; originX?: number; originY?: number }
}
export interface TaskDefinition { fusionTaskId: string; taskName: string; loopCount?: number }
export interface TaskReport {
  id?: string
  displayName?: string
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
export interface AgentSession {
  session_id: string
  messages: { role: string; content: unknown; tool_calls?: unknown[] }[]
  created_at: number
}

export function apiUrl(path: string): string {
  return `${useSettingsStore().apiBase}${path}`
}

export function apiHeaders(): Headers {
  const headers = new Headers()
  const key = useSettingsStore().apiKey
  if (key) headers.set('X-API-Key', key)
  return headers
}

export async function parseResponse<T>(response: Response): Promise<T> {
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const envelope = body as { error?: { code?: string | number; message?: string; trace_id?: string | null } } | null
    throw new ApiError(envelope?.error?.message ?? `请求失败 (${response.status})`, envelope?.error?.code ?? response.status, envelope?.error?.trace_id ?? null)
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
export const listRobots = (page = 1) => apiFetch<Robot[] | Page<Robot>>(`${root}/robots?page=${page}&page_size=100`)
export const batchRobotStatus = (robot_sn_list: string[]) => post<RobotStatus[] | Page<RobotStatus>>(`${root}/robots/status`, { robot_sn_list })
export const getRobotStatus = (sn: string) => apiFetch<RobotStatus>(`${robotPath(sn)}/status`)
export const listMaps = (sn: string) => apiFetch<RobotMap[] | Page<RobotMap>>(`${robotPath(sn)}/maps`)
export const getMapCanvas = (sn: string, mapId: string) => apiFetch<MapCanvas>(`${robotPath(sn)}/maps/${encodeURIComponent(mapId)}/canvas`)
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
export const deleteAgentSession = (id: string) => apiFetch<void>(sessionPath(id), { method: 'DELETE' })
export const confirmAgent = (id: string, confirmId: string, approve: boolean) => post<{ ok: boolean }>(`${sessionPath(id)}/confirm`, { confirm_id: confirmId, approve })

export function pageItems<T>(data: T[] | Page<T>): T[] {
  return Array.isArray(data) ? data : (data.list ?? data.robotTaskReports ?? [])
}
