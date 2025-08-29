# Gausium OpenAPI 端点清单

## API 端点汇总表

| 服务分类 | 接口名称 | HTTP方法 | 端点路径 | 实现状态 |
|---------|---------|----------|----------|----------|
| **认证服务** | 获取OAuth令牌 | POST | `/gas/api/v1alpha1/oauth/token` | ✅ 已实现 |
| **认证服务** | 刷新OAuth令牌 | POST | `/gas/api/v1alpha1/oauth/token` | ❌ 未实现 |
| **机器人信息** | 列出机器人 | GET | `/v1alpha1/robots` | ✅ 已实现 |
| **机器人信息** | 获取机器人状态 | GET | `/v1alpha1/robots/{serial_number}/status` | ✅ 已实现 |
| **机器人任务** | 获取站点信息 | GET | `/openapi/v2alpha1/robots/{robotId}/getSiteInfo` | ❌ 未实现 |
| **机器人指令** | 创建机器人指令 | POST | `/v1alpha1/robots/{serialNumber}/commands` | ❌ 未实现 |
| **机器人地图** | V2列出机器人地图 | GET | `/openapi/v1/map/robotMap/list` | ✅ 已实现 |
| **清洁数据** | 列出任务报告 | GET | `/v1alpha1/robots/{serial_number}/taskReports` | ✅ 已实现 |
| **推送服务** | 事件推送回调 | POST | `/{user_callback_url}` | ❌ 未实现 |
| **云梯控** | 电梯控制接口 | - | `/elevator/*` (待确认) | ❌ 未实现 |

## 详细端点规范

### 1. 认证服务端点

#### 1.1 OAuth令牌管理
```
POST /gas/api/v1alpha1/oauth/token
```
- **用途**: 获取/刷新访问令牌
- **Base URL**: https://openapi.gs-robot.com
- **认证**: 无 (使用client credentials)
- **请求体**: 
  - 获取令牌: `grant_type`, `client_id`, `client_secret`, `open_access_key`
  - 刷新令牌: `grant_type=refresh_token`, `refresh_token`

### 2. 机器人信息服务端点

#### 2.1 机器人列表
```
GET /v1alpha1/robots
```
- **参数**: `page`, `pageSize`, `relation`
- **认证**: Bearer Token

#### 2.2 机器人状态
```
GET /v1alpha1/robots/{serial_number}/status
```
- **路径参数**: `serial_number` (机器人序列号)
- **认证**: Bearer Token

### 3. 机器人任务服务端点

#### 3.1 站点信息
```
GET /openapi/v2alpha1/robots/{robotId}/getSiteInfo
```
- **路径参数**: `robotId` (机器人ID)
- **认证**: Bearer Token
- **响应**: 站点、建筑、楼层、地图层级结构

### 4. 机器人指令服务端点

#### 4.1 指令创建
```
POST /v1alpha1/robots/{serialNumber}/commands
```
- **路径参数**: `serialNumber` (机器人序列号)
- **认证**: Bearer Token
- **支持指令类型**:
  - 任务: `START_TASK`, `PAUSE_TASK`, `RESUME_TASK`, `STOP_TASK`
  - 导航: `CROSS_NAVIGATE`, `PAUSE_NAVIGATE`, `RESUME_NAVIGATE`, `STOP_NAVIGATE`
  - 远控: `REMOTE_CONTROL_START`, `REMOTE_CONTROL_MOVE`, `REMOTE_CONTROL_STOP`

### 5. 机器人地图服务端点

#### 5.1 地图列表
```
GET /openapi/v1/map/robotMap/list
```
- **请求体**: `{"robotSn": "string"}`
- **认证**: Bearer Token
- **响应**: 地图ID、名称、版本信息

### 6. 机器人清洁数据服务端点

#### 6.1 任务报告
```
GET /v1alpha1/robots/{serial_number}/taskReports
```
- **路径参数**: `serial_number`
- **查询参数**: `page`, `pageSize`, `startTimeUtcFloor`, `startTimeUtcUpper`
- **认证**: Bearer Token

### 7. 机器人推送服务端点

#### 7.1 事件推送 (Webhook)
```
POST {user_callback_url}
```
- **方向**: Gausium -> 用户系统
- **内容**: 机器人事件、任务报告、调度任务
- **消息类型**: 1=事件, 2=任务报告, 3=调度任务
- **事件级别**: H0-H7

### 8. 云梯控对接端点

#### 8.1 电梯控制 (待补充)
```
API端点待确认
```
- **用途**: 电梯门禁系统集成
- **认证**: OAuth 2.0
- **状态**: 需要进一步获取技术文档

## API版本分析

### 版本模式识别
- **v1alpha1**: 核心机器人操作 (`/v1alpha1/robots/*`)
- **v2alpha1**: 增强功能 (`/openapi/v2alpha1/robots/*`) 
- **v1**: 地图服务 (`/openapi/v1/map/*`)
- **gas/api/v1alpha1**: 认证服务 (`/gas/api/v1alpha1/oauth/*`)

### 设计问题
1. **版本命名不一致**: 混合使用alpha1和正式版本
2. **路径前缀混乱**: `/v1alpha1/` vs `/openapi/v1/` vs `/openapi/v2alpha1/`
3. **需要统一处理**: 在客户端实现中需要考虑这些差异

## 实现优先级

### 高优先级 (P0) - 立即实现
- [ ] 刷新OAuth令牌
- [ ] 创建机器人指令
- [ ] 获取站点信息

### 中等优先级 (P1) - 本周实现  
- [ ] 事件推送服务处理
- [ ] 错误码统一处理
- [ ] API版本兼容

### 低优先级 (P2) - 下个迭代
- [ ] 云梯控接口集成
- [ ] 高级推送服务功能
- [ ] 性能优化和缓存