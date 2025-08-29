# Gausium OpenAPI MCP 服务器 - API能力审核文档

## 📋 实现的MCP工具总览

### 1. `list_robots` - 机器人列表查询
**功能描述**: 获取当前API密钥可访问的机器人列表

**参数**:
- `page` (可选): 页码，默认1
- `pageSize` (可选): 每页数量，默认10  
- `relation` (可选): 关系过滤器，如"contract"

**返回数据**:
```json
{
  "robots": [
    {
      "serialNumber": "机器人序列号",
      "name": "机器人名称", 
      "displayName": "显示名称",
      "modelFamilyCode": "型号系列代码",
      "modelTypeCode": "型号类型代码",
      "online": true/false,
      "softwareVersion": "软件版本"
    }
  ],
  "page": 当前页码,
  "pageSize": 每页数量,
  "total": "总数量"
}
```

**典型使用场景**: 
- 查看当前管理的机器人清单
- 获取机器人基本信息用于后续操作

---

### 2. `get_robot_status` - 机器人状态查询
**功能描述**: 获取指定机器人的详细运行状态

**参数**:
- `serial_number` (必需): 机器人序列号

**返回数据**: 机器人详细状态信息（具体格式需要实际调用确认）

**典型使用场景**:
- 监控机器人当前工作状态
- 诊断机器人运行问题
- 获取机器人位置和任务信息

---

### 3. `get_site_info` - 站点信息查询
**功能描述**: 获取机器人所在站点的建筑、楼层、地图信息

**参数**:
- `robot_id` (必需): 机器人ID

**返回数据**: 站点层级结构
```json
{
  "id": "站点ID",
  "name": "机器人名称",
  "buildings": [
    {
      "name": "建筑名称",
      "floorNum": 楼层总数,
      "floors": [
        {
          "floorInfo": "楼层详情",
          "maps": "地图信息"
        }
      ]
    }
  ]
}
```

**典型使用场景**:
- 了解机器人工作环境结构
- 为任务规划提供地图信息
- 导航和路径规划

---

### 4. `create_robot_command` - 机器人指令创建
**功能描述**: 向指定机器人发送控制指令

**参数**:
- `serial_number` (必需): 机器人序列号
- `command_type` (必需): 指令类型
- `command_parameter` (可选): 指令参数

**支持的指令类型**:

#### 任务控制指令:
- `START_TASK`: 开始清洁任务
- `PAUSE_TASK`: 暂停当前任务
- `RESUME_TASK`: 恢复暂停的任务
- `STOP_TASK`: 停止当前任务

#### 导航控制指令:
- `CROSS_NAVIGATE`: 跨区域导航
- `PAUSE_NAVIGATE`: 暂停导航
- `RESUME_NAVIGATE`: 恢复导航
- `STOP_NAVIGATE`: 停止导航

#### 远程控制指令:
- `REMOTE_CONTROL_START`: 开始远程控制
- `REMOTE_CONTROL_MOVE`: 远程移动控制
- `REMOTE_CONTROL_STOP`: 停止远程控制

**参数示例** (START_TASK):
```json
{
  "startTaskParameter": {
    "cleaningMode": "__middle_cleaning",
    "task": {
      "loop": false,
      "loopCount": 1,
      "map": "9-2",
      "name": "execute_task_a_a_path0"
    }
  }
}
```

**典型使用场景**:
- 远程启动/停止清洁任务
- 控制机器人导航移动
- 紧急情况下停止机器人操作

---

### 5. `list_robot_maps` - 机器人地图列表
**功能描述**: 获取指定机器人关联的地图信息

**参数**:
- `robot_sn` (必需): 机器人序列号

**返回数据**:
```json
[
  {
    "mapId": "地图唯一标识",
    "mapName": "地图名称",
    "mapVersion": "地图版本"
  }
]
```

**典型使用场景**:
- 查看机器人可用的地图
- 为任务指令选择合适的地图
- 地图管理和维护

---

### 6. `list_robot_task_reports` - 任务报告查询
**功能描述**: 获取机器人的清洁任务执行报告

**参数**:
- `serial_number` (必需): 机器人序列号
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认100
- `start_time_utc_floor` (可选): 开始时间过滤器 (ISO 8601格式)
- `start_time_utc_upper` (可选): 结束时间过滤器 (ISO 8601格式)

**返回数据**: 分页的任务报告列表
```json
{
  "robotTaskReports": [
    {
      "任务报告详细信息": "具体格式需要实际调用确认"
    }
  ],
  "page": 当前页码,
  "pageSize": 每页数量,
  "total": 总数量
}
```

**典型使用场景**:
- 查看机器人清洁任务历史
- 分析清洁效果和性能
- 生成清洁报告和统计

---

## 🔍 需要审核的关键问题

### 1. API功能边界确认
- **当前实现的6个工具是否覆盖了核心使用场景？**
- **是否有遗漏的重要机器人控制功能？**

### 2. 参数设计合理性
- **各工具的参数设计是否符合实际使用需求？**
- **是否有不必要的复杂参数？**

### 3. 返回数据有效性
- **返回的数据结构是否满足AI模型的理解和使用？**
- **是否需要对某些复杂返回数据进行简化处理？**

### 4. 实际业务价值
- **这些API能解决什么具体的机器人管理问题？**
- **哪些是高频使用的核心功能？**

### 5. 功能组合可能性
- **这些工具之间如何配合完成复杂的机器人管理任务？**
- **典型的工作流程是什么？**

## 🎯 待确认的使用场景

### 场景1: 日常机器人监控
1. `list_robots` - 获取机器人列表
2. `get_robot_status` - 检查每个机器人状态
3. `list_robot_task_reports` - 查看最近任务执行情况

### 场景2: 执行清洁任务
1. `list_robots` - 选择可用机器人
2. `get_site_info` - 获取站点地图信息
3. `list_robot_maps` - 确认可用地图
4. `create_robot_command` - 发送START_TASK指令

### 场景3: 问题诊断和处理
1. `get_robot_status` - 检查机器人当前状态
2. `list_robot_task_reports` - 查看历史任务执行情况
3. `create_robot_command` - 发送STOP_TASK或其他控制指令

**请审核以上API能力总结，指出需要修正或补充的地方。**