# 🤖 高仙机器人 OpenAPI MCP服务器

<div align="center">

[![Python 版本](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI 版本](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![许可证](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP 兼容](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://github.com/modelcontextprotocol)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Ready-orange.svg)](https://claude.ai/code)

**🔧 连接AI模型与高仙机器人的强大MCP服务器**

*通过Claude、Cursor等AI助手控制和监控高仙清洁机器人*

[🚀 快速开始](#-快速开始) • [📖 文档](#-文档) • [🛠️ 安装](#️-安装) • [🎯 示例](#-示例)

</div>

---

## 🌟 这是什么？

这是一个MCP（模型控制协议）服务器，通过标准化接口实现AI模型与高仙清洁机器人的无缝交互。非常适合构建智能自动化工作流，支持Claude Code、Cursor和其他MCP兼容的AI工具。

**🔗 代码仓库：** [https://github.com/cfrs2005/mcp-gs-robot](https://github.com/cfrs2005/mcp-gs-robot)

### 🎯 核心优势

- 🤖 **AI优先设计**：专为AI助手集成而构建
- 🔄 **实时控制**：即时监控和命令机器人
- 📊 **丰富数据**：获取详细状态、地图和任务报告
- 🛡️ **安全可靠**：基于OAuth的环境变量身份验证
- 🌐 **通用兼容**：支持Claude、Cursor和任何MCP客户端

## 🏗️ 架构设计

服务器采用分层架构，关注点分离，提升可维护性：

![架构图](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture.svg)

### 🔄 MCP协议流程

下图展示AI模型如何通过MCP协议与高仙机器人交互：

![MCP协议流程](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/mcp-flow.svg)

### 🤝 支持的机器人系列

#### M系列机器人（传统清洁机器人）
- **OMNIE** (OMNIE系列) - 多功能清洁机器人
- **Vacuum 40** (40系列) - 吸尘清洁机器人
- **Scrubber 50** (50系列) - 洗地清洁机器人
- **Scrubber 75** (75系列) - 重型洗地清洁机器人

#### S系列机器人（高级智能机器人，包含SW系列）
- **Phantas** (S系列) - 幻影智能清洁机器人
- **BEETLE** (SW系列) - 甲壳虫智能清洁机器人

## ✨ 功能特性

### 🛠️ 核心MCP工具

| 工具 | 描述 | 状态 |
|------|------|------|
| 🤖 `list_robots` | 列出所有可访问的机器人 | ✅ 就绪 |
| 📊 `get_robot_status` | 获取详细的机器人状态和位置 | ✅ 就绪 |
| 📋 `list_robot_task_reports` | 检索带过滤的清洁任务报告 | ✅ 就绪 |
| 🗺️ `list_robot_maps` | 获取机器人导航可用地图 | ✅ 就绪 |
| 🎯 `create_robot_command` | 发送机器人命令（开始/暂停/停止） | ✅ 就绪 |
| 🏢 `get_site_info` | 获取建筑和楼层信息 | ✅ 就绪 |
| 📍 `get_map_subareas` | 获取任务详细区域信息 | ✅ 就绪 |
| 🚀 `submit_temp_task` | 提交临时清洁任务 | ✅ 就绪 |

### 🔧 高级工作流

- 🎛️ **自动化任务执行**：状态查询 → 任务选择 → 执行的完整工作流
- 📈 **批量操作**：同时处理多个机器人
- 🗺️ **地图管理**：上传、下载和管理机器人地图
- 📊 **报告生成**：从任务报告生成PNG地图
- 🏗️ **基于站点的任务**：包含建筑/楼层上下文的高级任务创建

### 🤝 支持的机器人系列

#### M系列机器人（传统清洁机器人）
- **OMNIE** (OMNIE) - 全能清洁机器人
- **Vacuum 40** (40系列) - 吸尘清洁机器人
- **Scrubber 50** (50系列) - 洗地清洁机器人  
- **Scrubber 75** (75系列) - 大型洗地清洁机器人

#### S系列机器人（高级智能机器人，包含SW系列）
- **Phantas** (S系列) - 幻影智能清洁机器人
- **BEETLE** (SW系列) - 甲壳虫智能清洁机器人

## 📁 项目结构

项目采用针对MCP开发优化的结构化布局：

```
🗂️ mcp-gs-robot/
├── 📦 src/gs_openapi/           # 主包
│   ├── 🔌 api/                  # 直接API集成
│   │   ├── 🤖 robots.py         # 机器人管理API
│   │   └── 🗺️ maps.py           # 地图管理API
│   ├── 🔐 auth/                 # 认证层
│   │   └── 🎫 token_manager.py  # OAuth令牌生命周期
│   ├── ⚙️ config.py             # 配置管理
│   ├── 🔧 core/                 # 核心功能
│   │   ├── 📡 client.py         # HTTP客户端包装器
│   │   └── 🛣️ endpoints.py      # API端点定义
│   ├── 🔌 mcp/                  # MCP服务器实现
│   │   └── 🌉 gausium_mcp.py    # 主MCP桥接
│   └── 🔄 workflows/            # 自动化工作流
│       └── 🎯 task_engine.py    # 任务自动化引擎
├── 📚 docs/                     # 文档
│   ├── 🖼️ images/               # 可视化文档
│   ├── 📖 apis.md              # API文档
│   └── 🧪 TESTING_GUIDE.md     # 测试说明
├── 🚀 main.py                  # 应用程序入口点
└── 📋 pyproject.toml           # 包配置
```

## 🚀 快速开始

### 📦 安装

#### 选项1：从PyPI安装（推荐）

```bash
pip install mcp-gs-robot
```

#### 选项2：从源码安装

```bash
# 克隆仓库
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot

# 使用uv设置（推荐）
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

### 🔧 配置

**设置你的高仙API凭证：**

```bash
# 必需的环境变量
export GS_CLIENT_ID="你的客户端ID"
export GS_CLIENT_SECRET="你的客户端密钥"
export GS_OPEN_ACCESS_KEY="你的访问密钥"
```

> 🔑 **从 [高仙开发者门户](https://developer.gs-robot.com/) 获取凭证**

### 🏃‍♂️ 运行服务器

```bash
# 启动MCP服务器（stdio模式）
python -m gs_openapi.main
# 或通过pip安装后：
mcp-gs-robot
```

✅ 服务器使用 `stdio` 传输启动（完美适配Claude Code）

### 🔌 Claude Code集成

**方法1：带环境变量的自动安装**

```bash
# 添加带环境变量的MCP服务器
claude mcp add mcp-gs-robot \
  --env GS_CLIENT_ID="你的客户端ID" \
  --env GS_CLIENT_SECRET="你的客户端密钥" \
  --env GS_OPEN_ACCESS_KEY="你的访问密钥"
```

**方法2：手动配置**

在你的 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "mcp-gs-robot": {
      "command": "mcp-gs-robot",
      "env": {
        "GS_CLIENT_ID": "你的客户端ID",
        "GS_CLIENT_SECRET": "你的客户端密钥",
        "GS_OPEN_ACCESS_KEY": "你的访问密钥"
      }
    }
  }
}
```

**方法3：使用环境文件**

如果你偏好使用 `.env` 文件：

```bash
# 设置全局环境变量
export GS_CLIENT_ID="你的客户端ID"
export GS_CLIENT_SECRET="你的客户端密钥"
export GS_OPEN_ACCESS_KEY="你的访问密钥"

# 简单MCP安装
claude mcp add mcp-gs-robot
```

> 💡 **注意**：此MCP服务器使用 `stdio` 传输（非SSE），完美适配Claude Code集成

## 🎯 使用示例

### 📱 Claude Code使用

```python
# 在Claude Code中，你现在可以使用自然语言：

"列出所有我的机器人"
# → 调用 mcp__mcp-gs-robot__list_robots

"获取机器人 GS101-0100-V1P-B001 的状态"
# → 调用 mcp__mcp-gs-robot__get_robot_status

"为5号楼的机器人开始清洁任务"
# → 编排 站点信息 → 地图选择 → 任务创建
```

### 🖥️ IDE集成

**Cursor配置：**

![Cursor使用截图](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cursor_usage_screenshot.png)

**Cherry Studio配置：**

![Cherry Studio配置](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cherrystudio.png)

### 🐛 调试

监控服务器日志以进行故障排除：

![MCP调试截图](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/mcp_debug_screenshot.png)

## 📖 文档

| 文档 | 用途 |
|------|------|
| 🎯 [Claude Code集成](docs/CLAUDE_CODE_INTEGRATION.md) | 完整的Claude Code设置指南 |
| 📋 [API参考](docs/apis.md) | 完整的API文档 |
| 🧪 [测试指南](docs/TESTING_GUIDE.md) | 如何测试MCP服务器 |
| 🔧 [配置说明](docs/README.md) | 详细的设置说明 |

## 🤝 贡献

我们欢迎贡献！请：

1. 🍴 Fork仓库
2. 🌿 创建功能分支
3. ✅ 为你的更改添加测试
4. 📝 更新文档
5. 🔄 提交拉取请求

## 📄 许可证

MIT许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🆘 支持

- 📝 [问题反馈](https://github.com/cfrs2005/mcp-gs-robot/issues)
- 📧 [邮箱](mailto:cfrs2005@gmail.com)
- 📚 [高仙开发者文档](https://developer.gs-robot.com/)

---

<div align="center">

**为Claude Code社区用 ❤️ 制作**

*启用AI驱动的机器人自动化，一次一个任务* 🤖✨

</div>