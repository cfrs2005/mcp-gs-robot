import { computed, reactive } from 'vue'
import { ApiError, batchRobotStatus, listRobots, pageItems, robotErrorMessage, type Robot, type RobotStatus } from './client'

// The fleet, in one place. Two cached layers:
// - loadFleet(): list_robots only (model / name lookup by SN).
// - loadFleetStatus(): list_robots + live batch status for robots the list marks online.
// fleetState() is the only definition of online / offline / unreachable; the home overview and the
// robot list both count through fleetSummary(), so they always agree.
const TTL_MS = 60_000

export type FleetRobot = Robot & Partial<RobotStatus> & { online: boolean }
export type FleetState = 'online' | 'offline' | 'unreachable'

const state = reactive({
  robots: [] as Robot[], loaded: false, failed: false,
  cards: [] as FleetRobot[], statusLoaded: false, statusFailed: false,
})
let listInflight: Promise<Robot[]> | null = null
let statusInflight: Promise<FleetRobot[]> | null = null
let listAt = 0
let statusAt = 0

export function useFleet() {
  return state
}

export function loadFleet(force = false): Promise<Robot[]> {
  if (!force && state.loaded && Date.now() - listAt < TTL_MS) return Promise.resolve(state.robots)
  listInflight ??= listRobots()
    .then(data => {
      state.robots = pageItems(data)
      state.loaded = true
      state.failed = false
      listAt = Date.now()
      return state.robots
    })
    .catch(e => { state.failed = true; throw e })
    .finally(() => { listInflight = null })
  return listInflight
}

/** Fleet entry for a SN, if the cached list has it. */
export function fleetRobot(sn: string | undefined): Robot | undefined {
  return sn ? state.robots.find(r => r.robotSn === sn || r.serialNumber === sn) : undefined
}

/**
 * online: list says online and a live snapshot confirms it.
 * unreachable: list says online, but the status query failed (upstream 230003) or the snapshot says OFFLINE.
 * offline: list says offline (never queried: upstream rejects a whole batch that contains an offline SN).
 */
export function fleetState(robot: FleetRobot): FleetState {
  if (!robot.online) return 'offline'
  return robot.reachable === false || robot.onlineStatus === 'OFFLINE' ? 'unreachable' : 'online'
}

// Live status only for robots the list marks online, in chunks of 100. A failed chunk marks just its
// robots unreachable (with the error), with no global toast.
async function liveStatuses(sns: string[]): Promise<Map<string, Partial<RobotStatus>>> {
  const chunks = Array.from({ length: Math.ceil(sns.length / 100) }, (_, i) => sns.slice(i * 100, i * 100 + 100))
  const settled = await Promise.allSettled(chunks.map(chunk => batchRobotStatus(chunk)))
  const bySn = new Map<string, Partial<RobotStatus>>()
  settled.forEach((result, i) => {
    if (result.status === 'fulfilled') pageItems(result.value).forEach(item => bySn.set(item.robotSn, item))
    else chunks[i].forEach(sn => bySn.set(sn, { reachable: false, error: { code: result.reason instanceof ApiError ? result.reason.code : undefined, message: robotErrorMessage(result.reason) } }))
  })
  return bySn
}

const ORDER: Record<FleetState, number> = { online: 0, unreachable: 1, offline: 2 }

export function loadFleetStatus(force = false): Promise<FleetRobot[]> {
  if (!force && state.statusLoaded && Date.now() - statusAt < TTL_MS) return Promise.resolve(state.cards)
  statusInflight ??= (async () => {
    const listed: FleetRobot[] = (await loadFleet(force)).map(item => ({ ...item, online: item.online === true }))
    // Show the list at once; live fields fill in when the status batch returns.
    if (!state.statusLoaded) state.cards = [...listed].sort((a, b) => Number(b.online) - Number(a.online))
    const bySn = await liveStatuses(listed.filter(item => item.online).map(item => item.robotSn))
    state.cards = listed.map(item => ({ ...item, ...bySn.get(item.robotSn) })).sort((a, b) => ORDER[fleetState(a)] - ORDER[fleetState(b)])
    state.statusLoaded = true
    state.statusFailed = false
    statusAt = Date.now()
    return state.cards
  })()
    .catch(e => { state.statusFailed = true; throw e })
    .finally(() => { statusInflight = null })
  return statusInflight
}

/** Counts over the status-checked fleet; null until loadFleetStatus() has finished once. */
const summary = computed(() => {
  if (!state.statusLoaded) return null
  const counts = { total: state.cards.length, online: 0, offline: 0, unreachable: 0 }
  for (const robot of state.cards) counts[fleetState(robot)]++
  return counts
})
export function fleetSummary() {
  return summary
}
