# Gausium OpenAPI 完整接口规范

## 1. 认证服务 (Authentication Service)

### 获取 OAuth Token
- **URL**: `https://openapi.gs-robot.com/gas/api/v1alpha1/oauth/token`
- **方法**: POST
- **请求体**:
  ```json
  {
    "grant_type": "urn:gaussian:params:oauth:grant-type:open-access-token",
    "client_id": "{{client_id}}",
    "client_secret": "{{client_secret}}",
    "open_access_key": "{{open_access_key}}"
  }
  ```
- **响应**:
  ```json
  {
    "token_type": "bearer",
    "access_token": "{{token}}",
    "expires_in": 1726111975164,
    "refresh_token": "{{refresh_token}}"
  }
  ```

### 刷新 OAuth Token  
- **URL**: `https://openapi.gs-robot.com/gas/api/v1alpha1/oauth/token`
- **方法**: POST
- **请求体**:
  ```json
  {
    "grant_type": "refresh_token",
    "refresh_token": "{{refresh_token}}"
  }
  ```

## 2. 机器人信息服务 (Robot Information Service)

### 列出机器人
- **URL**: `https://openapi.gs-robot.com/v1alpha1/robots`
- **方法**: GET
- **查询参数**:
  - `page` (可选): 页码
  - `pageSize` (可选): 每页数量，默认10
  - `relation` (可选): 过滤参数，如"contract"
- **认证**: Bearer Token
- **响应**:
  ```json
  {
    "robots": [
      {
        "serialNumber": "string",
        "name": "string", 
        "displayName": "string",
        "modelFamilyCode": "string",
        "modelTypeCode": "string",
        "online": boolean,
        "softwareVersion": "string"
      }
    ],
    "page": number,
    "pageSize": number,
    "total": "string"
  }
  ```

### 获取机器人状态
- **URL**: `https://openapi.gs-robot.com/v1alpha1/robots/{serial_number}/status`
- **方法**: GET
- **认证**: Bearer Token

## 3. 机器人任务服务 (Robot Task Service)

### 获取站点信息
- **URL**: `https://openapi.gs-robot.com/openapi/v2alpha1/robots/{robotId}/getSiteInfo`
- **方法**: GET
- **认证**: Bearer Token
- **响应**: 包含站点详情、建筑物和楼层信息

## 4. 机器人指令服务 (Robot Command Service)

### 创建机器人指令
- **URL**: `https://openapi.gs-robot.com/v1alpha1/robots/{serialNumber}/commands`
- **方法**: POST
- **认证**: Bearer Token
- **指令类型**:
  - 任务指令: START_TASK, PAUSE_TASK, RESUME_TASK, STOP_TASK
  - 导航指令: CROSS_NAVIGATE, PAUSE_NAVIGATE, RESUME_NAVIGATE, STOP_NAVIGATE
  - 远程控制: REMOTE_CONTROL_START, REMOTE_CONTROL_MOVE, REMOTE_CONTROL_STOP
- **请求体示例** (启动任务):
  ```json
  {
    "serialNumber": "TEST00-0000-000-S003",
    "remoteTaskCommandType": "START_TASK",
    "commandParameter": {
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
  }
  ```

## 5. 机器人地图服务 (Robot Map Service)

### 列出机器人地图 (V2)
- **URL**: `https://openapi.gs-robot.com/openapi/v1/map/robotMap/list`
- **方法**: GET
- **请求体**:
  ```json
  {
    "robotSn": "string"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 0,
    "msg": "SUCCESS", 
    "data": [
      {
        "mapId": "string",
        "mapName": "string",
        "mapVersion": "string"
      }
    ]
  }
  ```

## 6. 机器人清洁数据服务 (Robot Cleaning Data Service)

### 列出机器人任务报告
- **URL**: `https://openapi.gs-robot.com/v1alpha1/robots/{serial_number}/taskReports`
- **方法**: GET
- **查询参数**:
  - `page`: 页码
  - `pageSize`: 每页数量
  - `startTimeUtcFloor`: 开始时间过滤器 (ISO 8601)
  - `startTimeUtcUpper`: 结束时间过滤器 (ISO 8601)

## 7. 机器人推送服务 (Robot Push Service)

### 事件推送 (Webhook)
- **URL**: `https://{{host}}/callback` (用户提供的回调URL)
- **方法**: POST
- **内容类型**: application/json
- **请求载荷**:
  ```json
  {
    "appId": "authentication_string",
    "payload": {
      "serialNumber": "string",
      "modelTypeCode": "string",
      "content": {
        "incidentCode": "string",
        "incidentName": "string", 
        "incidentLevel": "H0-H7",
        "incidentStatus": 1,
        "startTime": "UTC_timestamp",
        "endTime": "UTC_timestamp"
      }
    },
    "messageTypeId": 1,
    "productId": "robot_serial",
    "messageId": "unique_id",
    "traceId": "trace_id",
    "messageTimestamp": "timestamp_ms"
  }
  ```

## 8. 云梯控对接接口协议 (Elevator Control System)

### OAuth 2.0 获取访问令牌
- 使用标准 OAuth 2.0 流程获取访问令牌
- 具体实现需要参考云梯控系统文档

## API 通用规范

### 错误码
- `0`: SUCCESS
- `3`: INVALID_ARGUMENT  
- `7`: PERMISSION_DENIED
- `8`: RESOURCE_EXHAUSTED (限流)
- `13`: INTERNAL (内部系统错误)

### 认证
- 大部分API需要Bearer Token认证
- Token通过OAuth服务获取
- 推荐实现Token自动刷新机制