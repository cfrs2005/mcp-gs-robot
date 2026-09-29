# Changelog

All notable changes to this project are documented here.

## [0.2.0] - 2026-09-28

### 🚀 Added
- OpenAPI V3 client covering 36 robot/task endpoint tools plus OAuth token operations, with typed models and reference tables (38 archived endpoint pages).
- Shared 40-tool registry: 36 V3 endpoint tools, legacy robot listing, local work-state lookup, and two workflow tools; MCP, Pi Agent, and REST share the definitions.
- Pi Agent CLI and HTTP chat with Anthropic and OpenAI-compatible providers, streaming SSE and confirmation gates.
- FastAPI REST server, robot routes, API-key option, and Vue/Vite H5 interface.
- Cross-client gs-robot Skill, V3 endpoint index (`docs/apis.md`) linking to the official documentation, automated tests, CI, and container packaging.

### 🔧 Changed
- V3 tools are the MCP default; package now exposes `mcp-gs-robot`, `gs-robot-server`, and `pi-agent`.
- Tool inputs use snake_case; agent dangerous operations require explicit confirmation by default.

### 🐛 Fixed
- OAuth token handling uses the returned `expires_in` lifetime correctly.
- Updated V3 endpoint mapping and documentation to match the official public reference.

### ⚠️ Breaking
- Old 0.1.x MCP tool names and smart-routing tools are no longer registered by default. Set `GS_ENABLE_LEGACY_TOOLS=1` to expose them under `legacy_`-prefixed names; migrate clients to the [V3 tool list](https://github.com/cfrs2005/mcp-gs-robot/blob/main/README.md).

## [0.1.12] - 2025-09-02

### 🎯 Smart Routing Enhancement
- Enhanced smart routing strategy to use serial number prefix detection
- Improved robot series identification performance by eliminating API dependency
- Updated automatic routing detection to handle additional robot series prefixes
- Optimized intelligent routing for better reliability and faster response times

### 🔧 Technical Improvements
- Streamlined robot series detection logic in RobotAPIRouter
- Enhanced prefix-based routing mapping for comprehensive robot coverage
- Improved error handling and fallback strategies for unknown robot types
- Added comprehensive test coverage for prefix-based routing functionality

## [0.1.11] - 2025-08-30

### 🧹 Major Interface Cleanup
- Removed redundant MCP tools to eliminate confusion for AI models
- Consolidated robot status tools: removed get_robot_status, get_robot_status_v1, get_robot_status_v2
- Consolidated batch status tools: removed batch_get_robot_statuses_v1, batch_get_robot_statuses_v2
- Consolidated task reports: removed list_robot_task_reports, list_robot_task_reports_s
- Added batch_get_robot_statuses_smart for intelligent batch status queries

### 🎯 Simplified Tool Set
- Reduced from 21 tools to 16 tools (23% reduction)
- All remaining tools use smart routing (automatic M-line/S-line detection)
- Users only need to use `_smart` versions - no need to know robot series details

## [0.1.10] - 2025-08-30

### 🔧 Map Subareas API Fix
- Fixed map subareas API path from `/map/{map_id}/subareas` to `/map/subareas/get`
- Corrected method from GET to POST according to official documentation
- Updated API version from V2alpha1 to V1 (matches official curl examples)
- Fixed request format to use JSON body with mapId and robotSn parameters

## [0.1.9] - 2025-08-30

### 🔧 Critical API Path Fixes
- Fixed V2 S-line robot status API paths to include required `/s/` prefix
- Corrected map API version from V2alpha1 back to V1 (per official documentation)
- Fixed README navigation links to use GitHub absolute URLs for PyPI compatibility
- Updated API version constant name (OPENAPI_V2ALPHA1 → OPENAPI_V2_ALPHA1)

### 📚 Documentation
- Enhanced navigation links for better PyPI page experience
- Verified all API endpoints against official Gausium documentation

## [0.1.8] - 2025-08-30

### 🔧 API Fixes
- Fixed map API endpoints from V1 to V2alpha1 version for proper compatibility
- Corrected map API method from GET to POST according to API specification
- Fixed API version constant name (OPENAPI_V2ALPHA1 → OPENAPI_V2_ALPHA1)
- Updated robot list API to use relation=bound parameter for better filtering

### 🚀 New Features
- Added intelligent robot routing system for automatic API version selection
- Implemented RobotAPIRouter class to distinguish M-line vs S-line robots
- Added smart routing MCP tools: get_robot_status_smart, get_task_reports_smart, get_robot_capabilities
- Enhanced robot series detection (M-line: 40/50/75/OMNIE, S-line: S/SW)

### 🧹 Cleanup
- Updated .gitignore to exclude documentation templates and development files
- Improved project file organization

## [0.1.7] - 2025-08-30

### 🎨 Visual Improvements
- Completely redesigned architecture diagram with improved layout and clarity
- Fixed background layer alignment and proper component masking
- Moved architecture diagram components 50px to the right for better spacing
- Aligned all layer labels for consistent visual presentation
- Removed all connection lines for cleaner, simplified diagram appearance
- Enhanced layer visibility with proper background colors and opacity

## [0.1.6] - 2025-08-30

### 📝 Documentation
- Enhanced README with comprehensive badges, icons, and professional layout
- Added detailed Claude Code integration with environment variable configuration
- Fixed PyPI image display using absolute GitHub raw URLs
- Added bilingual support (English/Chinese) with collapsible sections
- Created dedicated Claude Code integration guide
- Added comprehensive IDE support matrix

### 🔧 Improvements
- Corrected stdio transport mode documentation (removed incorrect SSE references)
- Added three methods for Claude Code MCP configuration
- Enhanced installation instructions with multiple options

## [0.1.5] - 2025-08-29

### 🐛 Fixed
- Fixed package import path issues for proper MCP server execution
- Corrected executable entry point configuration in pyproject.toml
- Fixed PyPI publishing GitHub Secret naming convention

## [0.1.4] - 2025-08-29

### 🚀 Features
- Renamed package to `mcp-gs-robot` for PyPI distribution
- Configured PyPI publishing with stdio transport mode

## [0.1.3] - 2025-08-29

### 🚀 Features
- Complete Gausium OpenAPI MCP server implementation
- Added architecture diagrams and updated README with uv instructions

## [0.1.2] - 2025-08-29

### 🎨 Documentation
- Implemented Gausium OpenAPI MCP server structure and tools

## [0.1.1] - 2025-08-29

### 📝 Documentation
- Updated installation instructions using GitHub installation method

## [0.1.0] - 2025-04-30

### 🎉 Initial Release
- Initial commit: basic Gausium robot MCP plugin
