// 与 docs/openapi-v3/robot-work-state-reference.md 的状态表保持一致。
export const workStates: Record<number, string> = {
  0: '未指定', 100: '空闲', 110: '未初始化', 140: '路径录制中',
  150: '区域录制中', 160: '地图保存中', 170: '导航中',
  180: '手动充电', 190: '自动充电', 200: '工作站补水／排水',
  210: '手动任务', 220: '自动任务暂停', 230: '自动任务执行中',
  240: '导航暂停', 250: '地图扫描中', 260: '电梯暂停',
  270: '远程唤醒', 300: '等待工作站', 310: '预约工作站',
  320: '等待电梯', 330: '电梯内', 340: '前往电梯',
  350: '已到呼叫点', 360: '即将进入低功耗', 370: '进入低功耗',
  380: '低功耗模式', 390: '退出低功耗', 400: '手动过渡',
  410: '机器人休眠', 420: '主停止', 430: '前往闸机',
  431: '等待闸机', 432: '通过闸机', 440: '紧急停车',
}

export function workStateName(status: { work_state_name?: string; workState?: number }): string {
  return status.work_state_name || (status.workState === undefined ? '未知' : workStates[status.workState] ?? `状态 ${status.workState}`)
}
