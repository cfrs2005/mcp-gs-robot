# 📋 API Documentation

This document provides comprehensive information about the Gausium Robot OpenAPI endpoints used by this MCP server.

## 🔐 Authentication APIs

| API | Description | Chinese Docs | English Docs |
|-----|-------------|--------------|---------------|
| Get OAuth Token | Obtain authentication token | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Openapi%20Oauth%20Service/Get%20OAuth%20Token) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Openapi%20Oauth%20Service/Get%20OAuth%20Token) |
| Refresh OAuth Token | Refresh expired token | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Openapi%20Oauth%20Service/Refresh%20OAuth%20Token) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Openapi%20Oauth%20Service/Refresh%20OAuth%20Token) |

## 🤖 Robot Information APIs

| API | Robot Series | Description | Chinese Docs | English Docs |
|-----|--------------|-------------|--------------|---------------|
| List Robots | All | List accessible robots | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/List%20Robots) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Information%20Service/List%20Robots) |
| Get Robot Status (V1) | M-line (OMNIE, 40, 50, 75) | Get detailed robot status | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/V1%20Get%20Robot%20Status) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Information%20Service/V1%20Get%20Robot%20Status) |
| Batch Get Robot Status (V1) | M-line (OMNIE, 40, 50, 75) | Batch status query | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/V1%20Batch%20Get%20Robot%20Statuses) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Information%20Service/V1%20Batch%20Get%20Robot%20Statuses) |
| Get S Robot Status (V2) | S-line (Phantas, BEETLE) | Get S/SW robot status | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/V2%20Get%20S%20Robot%20Status) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Information%20Service/V2%20Get%20S%20Robot%20Status) |
| Batch Get S Robot Status (V2) | S-line (Phantas, BEETLE) | Batch S/SW status query | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/V2%20Batch%20Get%20S%20Robot%20Status) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Information%20Service/V2%20Batch%20Get%20S%20Robot%20Status) |

## 🎯 Robot Command APIs

| API | Robot Series | Description | Chinese Docs | English Docs |
|-----|--------------|-------------|--------------|---------------|
| Create Robot Command | M-line | Send commands (start/pause/stop) | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Command%20Service/Create%20Robot%20Command) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Command%20Service/Create%20Robot%20Command) |
| Get Robot Command | All | Get command execution result | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Command%20Service/Get%20Robot%20Command) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Command%20Service/Get%20Robot%20Command) |
| List Robot Commands | All | Get command history | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Command%20Service/List%20Robot%20Commands) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Command%20Service/List%20Robot%20Commands) |

## 🗺️ Map Management APIs

| API | Version | Description | Chinese Docs | English Docs |
|-----|---------|-------------|--------------|---------------|
| List Robot Maps | V2 | Get available robot maps | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V2%20List%20Robot%20Map) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Map%20Service/V2%20List%20Robot%20Map) |
| Get Map Subareas | V2 | Get map area divisions | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V2%20Get%20Subareas) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Map%20Service/V2%20Get%20Subareas) |
| Upload Robot Map | V1 | Upload new map | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V1%20Upload%20Robot%20Map) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Map%20Service/V1%20Upload%20Robot%20Map) |
| Get Upload Record | V1 | Check upload status | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V1%20Get%20Robot%20Record) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Map%20Service/V1%20Get%20Robot%20Record) |
| Download Map | V1 | Download map (legacy) | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V1%20Get%20Robot%20Map) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Map%20Service/V1%20Get%20Robot%20Map) |
| Download Map | V2 | Download map (recommended) | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V2%20Get%20Robot%20Map) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Map%20Service/V2%20Get%20Robot%20Map) |

## 🎯 Task Management APIs

### S-line Robot Tasks

| API | Description | Chinese Docs | English Docs |
|-----|-------------|--------------|---------------|
| Submit Temporary Site Task | Create task with site info | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Task%20Service/Submit%20Temporary%20Site%20Task) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Task%20Service/Submit%20Temporary%20Site%20Task) |
| Submit Temporary No Site Task | Create task without site info | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Task%20Service/Submit%20Temporary%20No%20Site%20Task) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Task%20Service/Submit%20Temporary%20No%20Site%20Task) |

### Task Reports

| API | Robot Series | Description | Chinese Docs | English Docs |
|-----|--------------|-------------|--------------|---------------|
| List Task Reports (V1) | M-line | Get M-line task reports | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Cleaning%20Data%20Service/V1%20List%20Robot%20Task%20Reports) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Cleaning%20Data%20Service/V1%20List%20Robot%20Task%20Reports) |
| List Task Reports (V2) | S-line | Get S-line task reports | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Cleaning%20Data%20Service/V2%20List%20Robot%20Task%20Reports) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Cleaning%20Data%20Service/V2%20List%20Robot%20Task%20Reports) |
| Generate Task Report PNG | M-line | Generate map visualization | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Cleaning%20Data%20Service/Generate%20Robot%20Task%20Report%20Png) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Cleaning%20Data%20Service/Generate%20Robot%20Task%20Report%20Png) |

## 🏢 Site Information APIs

| API | Robot Series | Description | Chinese Docs | English Docs |
|-----|--------------|-------------|--------------|---------------|
| Get Site Info | S-line | Get building and floor info | [🇨🇳 zh_CN](https://developer.gs-robot.com/zh_CN/Robot%20Task%20Service/Get%20Site%20Info) | [🇺🇸 en_US](https://developer.gs-robot.com/en_US/Robot%20Task%20Service/Get%20Site%20Info) |

## 🤖 Robot Series Support

### M-line Robots (Traditional Cleaning)
- **OMNIE** (OMNIE series) - Multi-purpose cleaning robot
- **Vacuum 40** (40 series) - Vacuum cleaning robot  
- **Scrubber 50** (50 series) - Floor scrubbing robot
- **Scrubber 75** (75 series) - Heavy-duty floor scrubbing robot

**Supported APIs**: V1 Status, Commands, Task Reports, Map Management

### S-line Robots (Smart Cleaning, including SW)
- **Phantas** (S series) - Phantom intelligent cleaning robot
- **BEETLE** (SW series) - Beetle smart cleaning robot

**Supported APIs**: V2 Status, Site Tasks, Advanced Task Reports, Full Map Management

## 📝 API Usage Notes

### Version Recommendations
- **Map APIs**: Prefer V2 over V1 for new implementations
- **Status APIs**: Use V1 for M-line, V2 for S-line robots
- **Task APIs**: S-line robots support advanced site-based tasks

### Authentication
All APIs require OAuth authentication using the token endpoints. The MCP server handles this automatically using environment variables.

### Rate Limiting
Please refer to the official Gausium developer documentation for current rate limiting policies.

---

## 🔗 Official Documentation

- 🇨🇳 **Chinese**: [https://developer.gs-robot.com/zh_CN/](https://developer.gs-robot.com/zh_CN/)
- 🇺🇸 **English**: [https://developer.gs-robot.com/en_US/](https://developer.gs-robot.com/en_US/)