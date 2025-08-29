# Gausium 任务执行工作流分析

## 🔄 M线 vs S线任务执行的根本差异

### M线任务执行流程

#### 特点：使用机器人内置任务列表
```
1. 获取机器人状态 
   └── GET /v1alpha1/robots/{serial_number}/status
   
2. 从状态信息中提取可执行任务列表
   └── 机器人状态包含预定义的地图任务清单
   
3. 选择任务并下发指令
   └── POST /v1alpha1/robots/{serial_number}/commands
   └── 指令类型: START_TASK
   └── 任务参数来自机器人状态中的任务列表
```

#### 工作流程代码逻辑：
```python
# M线任务执行
async def execute_m_line_task(serial_number: str, task_selection_criteria: str):
    # 1. 获取机器人当前状态
    status = await client.call_endpoint('get_robot_status_v1', 
                                       path_params={'serial_number': serial_number})
    
    # 2. 从状态中解析可执行任务列表
    available_tasks = status.get('available_tasks', [])  # 具体格式需确认
    
    # 3. 根据条件选择任务
    selected_task = select_task_from_list(available_tasks, task_selection_criteria)
    
    # 4. 通过Create Robot Command下发任务
    return await client.call_endpoint('create_command',
        path_params={'serial_number': serial_number},
        json_data={
            "serialNumber": serial_number,
            "remoteTaskCommandType": "START_TASK", 
            "commandParameter": {
                "startTaskParameter": selected_task
            }
        })
```

---

### S线任务执行流程

#### 特点：基于外部地图和区域信息构建任务

#### S线有站点任务流程：
```
1. 获取站点信息
   └── GET /openapi/v2alpha1/robots/{robotId}/getSiteInfo
   
2. 从站点信息中获取地图列表
   └── 站点信息包含buildings -> floors -> maps层级结构
   
3. 获取地图分区信息  
   └── GET /openapi/v1/map/{map_id}/subareas
   
4. 构建任务参数并下发有站点临时任务
   └── POST /tasks/temporary/site (需要确认具体endpoint)
```

#### S线无站点任务流程：
```
1. 直接获取机器人地图列表
   └── GET /openapi/v1/map/robotMap/list
   
2. 获取目标地图的分区信息
   └── GET /openapi/v1/map/{map_id}/subareas  
   
3. 构建任务参数并下发无站点临时任务
   └── POST /tasks/temporary/no-site (需要确认具体endpoint)
```

#### 工作流程代码逻辑：
```python
# S线有站点任务执行
async def execute_s_line_site_task(robot_id: str, task_params: dict):
    # 1. 获取站点信息
    site_info = await client.call_endpoint('get_site_info',
                                          path_params={'robot_id': robot_id})
    
    # 2. 解析可用地图
    available_maps = extract_maps_from_site(site_info)
    
    # 3. 获取目标地图分区
    target_map_id = select_map(available_maps, task_params.get('map_criteria'))
    subareas = await client.call_endpoint('get_map_subareas',
                                         path_params={'map_id': target_map_id})
    
    # 4. 构建并下发有站点临时任务
    task_data = build_site_task_data(target_map_id, subareas, task_params)
    return await client.call_endpoint('submit_temp_site_task', json_data=task_data)

# S线无站点任务执行  
async def execute_s_line_no_site_task(robot_sn: str, task_params: dict):
    # 1. 获取机器人地图列表
    maps = await client.call_endpoint('list_maps', json_data={'robotSn': robot_sn})
    
    # 2. 获取目标地图分区  
    target_map_id = select_map(maps, task_params.get('map_criteria'))
    subareas = await client.call_endpoint('get_map_subareas',
                                         path_params={'map_id': target_map_id})
    
    # 3. 构建并下发无站点临时任务
    task_data = build_no_site_task_data(target_map_id, subareas, task_params)
    return await client.call_endpoint('submit_temp_no_site_task', json_data=task_data)
```

---

## 🎯 关键差异总结

| 维度 | M线 | S线 |
|------|-----|-----|
| **任务来源** | 机器人内置任务列表 | 外部构建临时任务 |
| **地图信息** | 从机器人状态获取 | 从站点信息或地图服务获取 |
| **任务下发** | Create Robot Command | 临时任务API |
| **站点概念** | 无站点概念 | 区分有站点/无站点 |
| **任务类型** | 预定义任务 | 动态构建任务 |
| **复杂度** | 简单(2步) | 复杂(3-4步) |

## 🚨 当前实现Gap更新

### 严重缺失的工作流支持

#### 1. M线任务执行 - **部分支持** 
- ✅ 有 `get_robot_status` 
- ✅ 有 `create_robot_command`
- ❌ 缺少任务列表解析逻辑
- ❌ 缺少任务选择辅助方法

#### 2. S线任务执行 - **基本无支持**
- ✅ 有 `get_site_info`
- ✅ 有 `list_robot_maps` 
- ❌ 缺少 `get_map_subareas` **（关键缺失）**
- ❌ 缺少 `submit_temp_site_task` **（关键缺失）**
- ❌ 缺少 `submit_temp_no_site_task` **（关键缺失）**
- ❌ 缺少任务数据构建逻辑

## 📋 更新后的优先级

### 立即实现 (P0) - 任务执行核心功能
1. **获取地图分区API** (`get_map_subareas`)
2. **S线临时任务下发APIs**
   - `submit_temp_site_task`  
   - `submit_temp_no_site_task`
3. **任务构建辅助方法**

### 高优先级 (P1) - 完整工作流支持  
4. **M线任务选择逻辑**
5. **S线地图选择逻辑**
6. **任务参数构建方法**

## 🎭 Linus更新评价

**【品味评分】**: 🔴 **之前理解完全错误**

**【根本问题】**:
- 🔴 **工作流理解错误**: M线和S线是完全不同的任务执行模式，不是简单API差异
- 🔴 **缺少核心逻辑**: 任务构建、地图选择、参数生成完全缺失
- 🔴 **实用性为零**: 当前实现无法支持任何产线的完整任务执行

**【真正的解决方案】**:
不是简单添加API调用，而是要实现完整的任务执行工作流引擎。

这才是真正的工程挑战！