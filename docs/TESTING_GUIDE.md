# Gausium OpenAPI MCP 测试指南

## 🎯 测试现状

**✅ 代码完成度**: 100% - 所有22个API + 3个工作流已实现  
**✅ 基础测试**: 通过 - 模块导入、端点配置、引擎初始化正常  
**⚠️ 实际调用**: 需要Gausium API凭证

## 📋 测试步骤

### 1. 环境准备

#### 1.1 安装依赖
```bash
# 确保使用正确的Python环境
uv pip install -r requirements.txt
```

#### 1.2 设置API凭证
```bash
# 设置环境变量
export GS_CLIENT_ID="你的客户端ID"
export GS_CLIENT_SECRET="你的客户端密钥"  
export GS_OPEN_ACCESS_KEY="你的访问密钥"
```

或者创建 `.env` 文件：
```bash
cat > .env << EOF
GS_CLIENT_ID=你的客户端ID
GS_CLIENT_SECRET=你的客户端密钥
GS_OPEN_ACCESS_KEY=你的访问密钥
EOF
```

### 2. 基础功能测试

#### 2.1 运行结构测试
```bash
python test_basic.py
```

**预期结果**:
- ✅ 所有模块导入成功
- ✅ 23个端点配置正确
- ✅ 任务引擎初始化成功

#### 2.2 启动MCP服务器
```bash
python main.py
```

**预期结果**:
- 服务器在 `http://0.0.0.0:8000` 启动
- 显示 "Starting Gausium MCP server..." 日志
- 无错误信息

### 3. API功能测试

#### 3.1 认证测试
使用任何API工具（如curl）测试：

```bash
# 测试OAuth令牌获取（内部调用）
curl -X POST http://localhost:8000/api/test-auth
```

#### 3.2 基础API测试
```bash
# 测试机器人列表
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "list_robots",
    "params": {"page": 1, "page_size": 10}
  }'
```

### 4. 产品线专用测试

#### 4.1 M线机器人测试
```bash
# 测试M线状态查询
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_robot_status_v1", 
    "params": {"serial_number": "你的M线机器人序列号"}
  }'

# 测试M线工作流
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "execute_m_line_task_workflow",
    "params": {
      "serial_number": "你的M线机器人序列号",
      "task_selection_criteria": {"cleaning_mode": "__middle_cleaning"}
    }
  }'
```

#### 4.2 S线机器人测试
```bash
# 测试S线状态查询
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_robot_status_v2",
    "params": {"serial_number": "你的S线机器人序列号"}
  }'

# 测试站点信息获取
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_site_info",
    "params": {"robot_id": "你的S线机器人ID"}
  }'

# 测试S线有站点工作流
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "execute_s_line_site_task_workflow",
    "params": {
      "robot_id": "你的S线机器人ID",
      "task_parameters": {
        "cleaning_mode": "__middle_cleaning",
        "target_areas": ["lobby", "corridor"]
      }
    }
  }'
```

### 5. 高级功能测试

#### 5.1 批量操作测试
```bash
# 测试批量状态查询
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "batch_get_robot_statuses_v1",
    "params": {
      "serial_numbers": ["机器人1", "机器人2", "机器人3"]
    }
  }'
```

#### 5.2 地图管理测试
```bash
# 测试地图列表
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "list_robot_maps",
    "params": {"robot_sn": "你的机器人序列号"}
  }'

# 测试地图分区查询
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_map_subareas", 
    "params": {"map_id": "地图ID"}
  }'
```

#### 5.3 指令管理测试
```bash
# 创建指令
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "create_robot_command",
    "params": {
      "serial_number": "机器人序列号",
      "command_type": "START_TASK",
      "command_parameter": {
        "startTaskParameter": {
          "cleaningMode": "__middle_cleaning"
        }
      }
    }
  }'

# 查询指令历史
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "list_robot_commands",
    "params": {"serial_number": "机器人序列号"}
  }'
```

## 🔍 问题排查

### 常见错误及解决方案

#### 1. "Missing required environment variables"
**原因**: 未设置API凭证  
**解决**: 设置正确的环境变量或.env文件

#### 2. "No module named 'mcp'"
**原因**: 依赖未安装  
**解决**: 运行 `uv pip install -r requirements.txt`

#### 3. "API returned error: PERMISSION_DENIED"
**原因**: API凭证无效或权限不足  
**解决**: 检查凭证有效性，确认API权限

#### 4. "Robot serial number not found"
**原因**: 机器人序列号不存在  
**解决**: 先调用 `list_robots` 获取有效的序列号

### 调试技巧

#### 1. 启用详细日志
```python
# 在main.py中修改日志级别
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
```

#### 2. 检查API响应
```bash
# 查看完整的API响应
curl -v -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"method": "list_robots", "params": {}}'
```

#### 3. 验证端点配置
```python
# 运行端点检查
python -c "
from src.gs_openapi.core.endpoints import ALL_ENDPOINTS
for name, endpoint in ALL_ENDPOINTS.items():
    print(f'{name}: {endpoint.method.value} {endpoint.full_path}')
"
```

## 🎯 测试检查清单

### 基础功能 ✅
- [ ] 环境变量设置正确
- [ ] MCP服务器正常启动
- [ ] 认证token获取成功
- [ ] 基础API调用成功

### M线机器人 🟦
- [ ] V1状态查询正常
- [ ] 批量状态查询正常  
- [ ] 指令创建和查询正常
- [ ] M线任务工作流正常
- [ ] 任务报告查询正常

### S线机器人 🟩
- [ ] V2状态查询正常
- [ ] 站点信息获取正常
- [ ] 地图分区查询正常
- [ ] 临时任务下发正常
- [ ] S线工作流正常

### 高级功能 ⭐
- [ ] 批量操作正常
- [ ] 地图管理功能正常
- [ ] 指令历史查询正常
- [ ] 任务报告生成正常
- [ ] 错误处理正常

## 📊 预期测试结果

**成功标准**:
- 所有基础API返回正常响应（非错误状态码）
- M线和S线工作流能够完成多步操作
- 批量操作能够处理多个机器人
- 错误情况下返回有意义的错误信息

**如果所有测试通过，说明Gausium OpenAPI MCP服务器已经可以投入生产使用！** 🚀