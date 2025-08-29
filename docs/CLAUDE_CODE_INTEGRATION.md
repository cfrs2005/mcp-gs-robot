# 🎯 Claude Code Integration Guide

This guide provides comprehensive instructions for integrating the Gausium OpenAPI MCP Server with Claude Code.

## 🚀 Quick Setup

### Prerequisites

1. **Claude Code installed** - Get it from [https://claude.ai/code](https://claude.ai/code)
2. **Gausium API credentials** - From [Gausium Developer Portal](https://developer.gs-robot.com/)
3. **Python 3.12+** - Required for the MCP server

### Step-by-Step Installation

#### Step 1: Install the MCP Server

```bash
# Option A: Install from PyPI (Recommended)
pip install mcp-gs-robot

# Option B: Install from source
git clone https://github.com/cfrs2005/mcp-gs-robot.git
cd mcp-gs-robot
uv venv && source .venv/bin/activate
uv pip install -e .
```

#### Step 2: Add to Claude Code with Credentials

**🎯 Recommended: Direct installation with environment variables**

```bash
claude mcp add mcp-gs-robot \
  --env GS_CLIENT_ID="your_client_id_here" \
  --env GS_CLIENT_SECRET="your_client_secret_here" \
  --env GS_OPEN_ACCESS_KEY="your_access_key_here"
```

This command will:
- ✅ Install the MCP server
- ✅ Configure environment variables
- ✅ Enable all robot control functions immediately

#### Step 3: Verify Installation

```bash
# Check MCP server list
claude mcp list

# Test the server
claude mcp test mcp-gs-robot
```

## 🔧 Alternative Configuration Methods

### Method 1: Manual JSON Configuration

Edit your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-gs-robot": {
      "command": "mcp-gs-robot",
      "env": {
        "GS_CLIENT_ID": "XVMgb7ow0NVYy211Z4xVLV",
        "GS_CLIENT_SECRET": "pZmSYmV6KeZY3wNMoE7djKzcuw2t2AOOytHzvJEIhMR6jLmzVy",
        "GS_OPEN_ACCESS_KEY": "3d97c0faa9b7740630f21ca0e1001b47"
      }
    }
  }
}
```

### Method 2: Global Environment Variables

Set system-wide environment variables:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export GS_CLIENT_ID="your_client_id"
export GS_CLIENT_SECRET="your_client_secret"
export GS_OPEN_ACCESS_KEY="your_access_key"

# Then simply add the MCP server
claude mcp add mcp-gs-robot
```

### Method 3: Using .env File

Create a `.env` file in your project:

```env
GS_CLIENT_ID=your_client_id
GS_CLIENT_SECRET=your_client_secret
GS_OPEN_ACCESS_KEY=your_access_key
```

Then add the MCP server:
```bash
claude mcp add mcp-gs-robot
```

## 🎮 Usage Examples in Claude Code

Once configured, you can control Gausium robots using natural language:

### 🤖 Basic Robot Operations

```
"List all available robots"
"Get status of robot GS101-0100-V1P-B001"
"Show me the maps for robot GS008-0180-C7P-0000"
```

### 🎯 Task Management

```
"Start cleaning task for robot GS101-0100-V1P-B001"
"Pause current task for robot GS008-0180-C7P-0000"
"Get cleaning reports for robot GS101-0100-V1P-B001 from last week"
```

### 🗺️ Advanced Operations

```
"Create a cleaning task for the lobby area in building 5"
"Get all subareas for map 81ab607b-f5c1-4415-9780-8529386d0aeb"
"Execute automated workflow for robot GS101-0100-V1P-B001"
```

## 🐛 Troubleshooting

### Common Issues

**1. Authentication Failed**
```
Error: Invalid credentials
```
**Solution**: Double-check your API credentials and ensure they're properly set

**2. MCP Server Not Found** 
```
Error: mcp-gs-robot command not found
```
**Solution**: Ensure the package is installed and in your PATH

**3. Robot Not Responding**
```
Error: Robot offline or unreachable
```
**Solution**: Verify robot is online and connected to network

### Debug Mode

Enable debug logging:

```bash
# Run with debug output
PYTHONPATH=src python -m gs_openapi.main --debug
```

### Testing Connection

```bash
# Test MCP server directly
claude mcp test mcp-gs-robot

# Check available tools
claude mcp describe mcp-gs-robot
```

## 🖥️ IDE Integration Examples

### Claude Code
Default stdio transport integration - works out of the box.

### Cursor  
Configure in Cursor's MCP settings with JSON configuration.

### Cherry Studio
Visual MCP configuration interface:

![Cherry Studio Configuration](https://github.com/cfrs2005/mcp-gs-robot/raw/main/docs/images/cherrystudio.png)

**Cherry Studio Setup Steps:**
1. Open Cherry Studio
2. Go to Settings → MCP Servers
3. Add new server with name "mcp-gs-robot"
4. Set command: `mcp-gs-robot`
5. Add environment variables:
   - `GS_CLIENT_ID`: Your client ID
   - `GS_CLIENT_SECRET`: Your client secret  
   - `GS_OPEN_ACCESS_KEY`: Your access key
6. Save and restart Cherry Studio

## 📋 Available MCP Tools

| Tool Name | Purpose | Example Usage |
|-----------|---------|---------------|
| `list_robots` | List available robots | "Show me all robots" |
| `get_robot_status` | Get robot status | "What's the status of robot GS101?" |
| `list_robot_task_reports` | Get task history | "Show cleaning reports" |
| `list_robot_maps` | List robot maps | "What maps does robot have?" |
| `create_robot_command` | Send robot commands | "Start cleaning task" |
| `get_site_info` | Get building info | "Show building layout" |
| `get_map_subareas` | Get area details | "What areas can be cleaned?" |
| `submit_temp_task` | Create temporary tasks | "Clean the lobby now" |

## 🌟 Advanced Features

### Workflow Automation

The MCP server includes powerful workflow automation:

- **M-line Workflows**: Automated task execution for traditional cleaning robots
- **S-line Workflows**: Advanced automation with site/building context
- **Batch Operations**: Handle multiple robots simultaneously

### Integration Examples

```python
# These are handled automatically by Claude Code:
"Execute cleaning workflow for all robots in building 3"
"Generate task report with map visualization"
"Schedule maintenance for robots with low battery"
```

## 🔗 Related Documentation

- 📚 [Main README](../README.md) - Project overview
- 🧪 [Testing Guide](TESTING_GUIDE.md) - How to test the server
- 📖 [API Reference](apis.md) - Complete API documentation
- 🏗️ [Architecture Overview](README.md) - System design

---

<div align="center">

**Ready to control robots with AI? Start with Claude Code! 🤖✨**

*Questions? Check our [Issues](https://github.com/cfrs2005/mcp-gs-robot/issues) or [Email us](mailto:cfrs2005@gmail.com)*

</div>