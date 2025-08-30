# 📝 Changelog

All notable changes to this project will be documented in this file.

## [0.1.9] - 2025-08-30

### 🔧 Critical API Path Fixes
- Fixed V2 S-line robot status API paths to include required `/s/` prefix
- Corrected map API version from V2alpha1 back to V1 (per official documentation)
- Fixed README navigation links to use GitHub absolute URLs for PyPI compatibility
- Updated batch S-line status API path with proper `/s/` prefix

### 📚 Documentation  
- Enhanced navigation links for better PyPI page experience
- Verified all API endpoints against official Gausium documentation

## [0.1.8] - 2025-08-30

### 🔧 API Fixes
- Fixed map API endpoints from V1 to V2alpha1 version for proper compatibility
- Corrected map list API method from GET to POST according to API specification
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
- Added Cherry Studio configuration guide with screenshot
- Fixed PyPI image display using absolute GitHub raw URLs
- Added bilingual support (English/Chinese) with collapsible sections
- Created dedicated Claude Code integration guide
- Updated project structure with emoji visualization
- Added comprehensive feature tables and IDE support matrix

### 🔧 Improvements
- Corrected stdio transport mode documentation (removed incorrect SSE references)
- Added three methods for Claude Code MCP configuration
- Enhanced installation instructions with multiple options

## [0.1.5] - 2025-08-29

### 🐛 Fixed
- Fixed package import path issues for proper MCP server execution
- Corrected executable entry point configuration in pyproject.toml
- Fixed PyPI publishing GitHub Secret naming convention

### 📝 Documentation
- Enhanced README with comprehensive badges and icons
- Added detailed Claude Code integration instructions with environment variables
- Added Cherry Studio configuration guide with screenshot
- Fixed PyPI image display by converting relative paths to absolute GitHub raw URLs
- Added bilingual support (English/Chinese) in documentation
- Created comprehensive Claude Code integration guide

## [0.1.4] - 2025-08-29

### 🚀 Features
- Renamed package to `mcp-gs-robot` for better PyPI distribution
- Configured PyPI publishing with stdio transport mode

### 🔧 Infrastructure  
- Removed .cursor configuration directory from git tracking
- Removed personal configuration files from git tracking
- Properly configured gitignore to exclude personal files

## [0.1.3] - 2025-08-29

### 🚀 Features
- Complete Gausium OpenAPI MCP server implementation
- Added architecture diagrams and updated README with uv instructions

## [0.1.2] - 2025-08-29

### 🎨 Documentation
- Implemented Gausium OpenAPI MCP server structure and tools

## [0.1.1] - 2025-08-29

### 📝 Documentation  
- Updated to correct MCP plugin usage approach
- Updated installation instructions using GitHub installation method

## [0.1.0] - 2025-04-30

### 🎉 Initial Release
- Initial commit: Added Gausium robot MCP plugin basic functionality

---

*Based on actual git commit history*