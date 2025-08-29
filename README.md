# 🤖 Gausium OpenAPI MCP Server

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/mcp-gs-robot.svg)](https://pypi.org/project/mcp-gs-robot/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://github.com/modelcontextprotocol)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Ready-orange.svg)](https://claude.ai/code)

**🔧 A powerful MCP server bridging AI models with Gausium robots**

*Control and monitor Gausium cleaning robots through Claude, Cursor, and other AI assistants*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🛠️ Installation](#️-installation) • [🎯 Examples](#-examples)

</div>

---

## 🌟 What is this?

This MCP (Model Control Protocol) server enables seamless interaction between AI models and Gausium cleaning robots through a standardized interface. Perfect for building intelligent automation workflows with Claude Code, Cursor, and other MCP-compatible AI tools.

**🔗 Repository:** [https://github.com/cfrs2005/mcp-gs-robot](https://github.com/cfrs2005/mcp-gs-robot)

### 🎯 Key Benefits

- 🤖 **AI-First Design**: Built specifically for AI assistant integration
- 🔄 **Real-time Control**: Monitor and command robots instantly
- 📊 **Rich Data Access**: Get detailed status, maps, and task reports
- 🛡️ **Secure**: OAuth-based authentication with environment variables
- 🌐 **Universal**: Works with Claude, Cursor, and any MCP client

## 🏗️ Architecture

The server follows a layered architecture that separates concerns and promotes maintainability:

![Architecture Diagram](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/architecture.svg)

### 🔄 MCP Protocol Flow

The diagram below shows how AI models interact with Gausium robots through the MCP protocol:

![MCP Protocol Flow](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/mcp-flow.svg)

## ✨ Features

### 🛠️ Core MCP Tools

| Tool | Description | Status |
|------|-------------|--------|
| 🤖 `list_robots` | List all accessible robots | ✅ Ready |
| 📊 `get_robot_status` | Get detailed robot status and position | ✅ Ready |
| 📋 `list_robot_task_reports` | Retrieve cleaning task reports with filtering | ✅ Ready |
| 🗺️ `list_robot_maps` | Get available maps for robot navigation | ✅ Ready |
| 🎯 `create_robot_command` | Send commands to robots (start/pause/stop) | ✅ Ready |
| 🏢 `get_site_info` | Get building and floor information | ✅ Ready |
| 📍 `get_map_subareas` | Get detailed area information for tasks | ✅ Ready |
| 🚀 `submit_temp_task` | Submit temporary cleaning tasks | ✅ Ready |

### 🔧 Advanced Workflows

- 🎛️ **Automated Task Execution**: Complete workflows from status → task selection → execution
- 📈 **Batch Operations**: Handle multiple robots simultaneously
- 🗺️ **Map Management**: Upload, download, and manage robot maps
- 📊 **Report Generation**: Generate PNG maps from task reports
- 🏗️ **Site-based Tasks**: Advanced task creation with building/floor context

### 🤝 Supported Robot Lines

- **M-line Robots** (40, 50, 75 series): Traditional cleaning robots
- **S-line Robots**: Advanced robots with site information support
- **SW-line Robots**: Next-generation smart cleaning systems

## 📁 Project Structure

The project follows a structured layout optimized for MCP development:

```
🗂️ mcp-gs-robot/
├── 📦 src/gs_openapi/           # Main package
│   ├── 🔌 api/                  # Direct API integrations
│   │   ├── 🤖 robots.py         # Robot management APIs
│   │   └── 🗺️ maps.py           # Map management APIs
│   ├── 🔐 auth/                 # Authentication layer
│   │   └── 🎫 token_manager.py  # OAuth token lifecycle
│   ├── ⚙️ config.py             # Configuration management
│   ├── 🔧 core/                 # Core functionality
│   │   ├── 📡 client.py         # HTTP client wrapper
│   │   └── 🛣️ endpoints.py      # API endpoint definitions
│   ├── 🔌 mcp/                  # MCP server implementation
│   │   └── 🌉 gausium_mcp.py    # Main MCP bridge
│   └── 🔄 workflows/            # Automated workflows
│       └── 🎯 task_engine.py    # Task automation engine
├── 📚 docs/                     # Documentation
│   ├── 🖼️ images/               # Visual documentation
│   ├── 📖 apis.md              # API documentation
│   └── 🧪 TESTING_GUIDE.md     # Testing instructions
├── 🚀 main.py                  # Application entry point
└── 📋 pyproject.toml           # Package configuration
```

### 🔍 Key Components

| Component | Purpose | Icon |
|-----------|---------|------|
| **config.py** | Base URLs, API paths, environment variables | ⚙️ |
| **token_manager.py** | OAuth token acquisition and refresh | 🔐 |
| **api/robots.py** | Robot status, commands, task reports | 🤖 |
| **api/maps.py** | Map listing, upload, download | 🗺️ |
| **gausium_mcp.py** | MCP server integration layer | 🌉 |
| **task_engine.py** | Automated workflow orchestration | 🎯 |
| **main.py** | Server initialization and tool registration | 🚀 |

## 🚀 Quick Start

### 📦 Installation

#### Option 1: Install from PyPI (Recommended)

```bash
pip install mcp-gs-robot
```

#### Option 2: Install from Source

```bash
# Clone repository
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot

# Setup with uv (recommended)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

### 🔧 Configuration

**Set up your Gausium API credentials:**

```bash
# Required environment variables
export GS_CLIENT_ID="your_client_id"
export GS_CLIENT_SECRET="your_client_secret" 
export GS_OPEN_ACCESS_KEY="your_access_key"
```

> 🔑 **Get credentials from [Gausium Developer Portal](https://developer.gs-robot.com/)**

### 🏃‍♂️ Running the Server

```bash
# Start MCP server (stdio mode)
python -m gs_openapi.main
# or if installed via pip:
mcp-gs-robot
```

✅ Server starts using `stdio` transport (perfect for Claude Code)

### 🔌 Claude Code Integration

**Method 1: Automatic installation with environment setup**

```bash
# Add MCP server with environment variables
claude mcp add mcp-gs-robot \
  --env GS_CLIENT_ID="your_client_id" \
  --env GS_CLIENT_SECRET="your_client_secret" \
  --env GS_OPEN_ACCESS_KEY="your_access_key"
```

**Method 2: Manual configuration**

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-gs-robot": {
      "command": "mcp-gs-robot",
      "env": {
        "GS_CLIENT_ID": "your_client_id",
        "GS_CLIENT_SECRET": "your_client_secret", 
        "GS_OPEN_ACCESS_KEY": "your_access_key"
      }
    }
  }
}
```

**Method 3: Using environment file**

If you prefer to use a `.env` file:

```bash
# Set global environment variables
export GS_CLIENT_ID="your_client_id"
export GS_CLIENT_SECRET="your_client_secret"
export GS_OPEN_ACCESS_KEY="your_access_key"

# Simple MCP installation
claude mcp add mcp-gs-robot
```

> 💡 **Note**: This MCP server uses `stdio` transport (not SSE), which is perfect for Claude Code integration

## 🎯 Examples

### 📱 Claude Code Usage

```python
# In Claude Code, you can now use natural language:

"List all my robots"
# → Calls mcp__mcp-gs-robot__list_robots

"Get status of robot GS101-0100-V1P-B001" 
# → Calls mcp__mcp-gs-robot__get_robot_status

"Start cleaning task for robot in building 5"
# → Orchestrates site info → map selection → task creation
```

### 🖥️ IDE Integration

**Cursor Configuration:**

![Cursor Usage Screenshot](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cursor_usage_screenshot.png)

**Cherry Studio Configuration:**

![Cherry Studio Configuration](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cherrystudio.png)

### 🐛 Debugging

Monitor server logs for troubleshooting:

![MCP Debug Screenshot](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/mcp_debug_screenshot.png)

## 📖 Documentation

| Document | Purpose |
|----------|----------|
| 🎯 [Claude Code Integration](docs/CLAUDE_CODE_INTEGRATION.md) | Complete Claude Code setup guide |
| 📋 [API Reference](docs/apis.md) | Complete API documentation |
| 🧪 [Testing Guide](docs/TESTING_GUIDE.md) | How to test the MCP server |
| 🔧 [Configuration](docs/README.md) | Detailed setup instructions |

## 🤝 Contributing

We welcome contributions! Please:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ✅ Add tests for your changes
4. 📝 Update documentation
5. 🔄 Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📝 [Issues](https://github.com/cfrs2005/mcp-gs-robot/issues)
- 📧 [Email](mailto:cfrs2005@gmail.com)
- 📚 [Gausium Developer Docs](https://developer.gs-robot.com/)

---

<div align="center">

**Made with ❤️ for the Claude Code community**

*Enabling AI-powered robot automation, one task at a time* 🤖✨

</div>

## 🌐 Language Support | 语言支持

<details>
<summary>🇨🇳 中文说明 (Chinese Documentation)</summary>

# 🤖 高斯OpenAPI MCP服务器

这是一个MCP（模型控制协议）服务器，作为高斯OpenAPI的桥梁，允许AI模型或其他客户端通过标准化接口与高斯机器人交互。

## 🌟 主要功能

- 🤖 **机器人管理**：列出、监控和控制高斯清洁机器人
- 📊 **实时状态**：获取详细的机器人状态和位置信息
- 🗺️ **地图管理**：上传、下载和管理机器人地图
- 📋 **任务报告**：检索清洁任务报告和历史数据
- 🎯 **任务创建**：提交临时清洁任务
- 🔧 **自动化工作流**：完整的任务执行流程

## 🚀 快速开始

### 安装

```bash
pip install mcp-gs-robot
```

### 配置环境变量

```bash
export GS_CLIENT_ID="你的客户端ID"
export GS_CLIENT_SECRET="你的客户端密钥"
export GS_OPEN_ACCESS_KEY="你的访问密钥"
```

### 运行服务器

```bash
mcp-gs-robot
```

### Claude Code集成

**推荐方法：带环境变量的自动安装**

```bash
claude mcp add mcp-gs-robot \
  --env GS_CLIENT_ID="你的客户端ID" \
  --env GS_CLIENT_SECRET="你的客户端密钥" \
  --env GS_OPEN_ACCESS_KEY="你的访问密钥"
```

**手动配置方法：**

在 `claude_desktop_config.json` 中添加：

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

**IDE集成支持：**
- 🎯 Claude Code：原生支持，stdio传输
- 🖥️ Cursor：JSON配置
- 🍒 Cherry Studio：可视化配置界面

现在你可以在这些AI助手中使用自然语言控制机器人：

- "列出所有机器人"
- "获取机器人状态"  
- "开始清洁任务"

### 支持的机器人系列

- **M系列机器人** (40, 50, 75系列)：传统清洁机器人
- **S系列机器人**：支持站点信息的高级机器人
- **SW系列机器人**：下一代智能清洁系统

### 获取帮助

- 📝 [问题反馈](https://github.com/cfrs2005/mcp-gs-robot/issues)
- 📚 [高斯开发者文档](https://developer.gs-robot.com/)

</details>
