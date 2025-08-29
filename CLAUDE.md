# [项目名称] - Claude Code AI 上下文文件 (claude-master)

## 1. 项目概览
- **愿景：** [描述项目的愿景和目标]
- **当前阶段：** [当前开发阶段和状态]
- **核心架构：** [高层架构描述]
- **开发策略：** [开发方法和策略说明]

## 2. 项目结构

**⚠️ 重要：AI 智能体在执行任何任务前，必须先阅读[项目结构文档](/docs/ai-context/project-structure.md)，了解完整的技术栈、文件树和项目组织方式。**

[项目名称]遵循[描述架构模式]。完整的技术栈和文件树结构，请参见[docs/ai-context/project-structure.md](/docs/ai-context/project-structure.md)。

## 3. 编码规范与 AI 指令

### 通用指令
- 你最重要的工作是管理自己的上下文。在规划变更前，务必先阅读相关文件。
- 更新文档时，保持更新简洁明了，防止内容冗余。
- 编写代码遵循 KISS、YAGNI 和 DRY 原则。
- 有疑问时遵循经过验证的最佳实践。
- 未经用户批准不要提交到 git。
- 不要运行任何服务器，而是告诉用户运行服务器进行测试。
- 优先考虑行业标准库/框架，而不是自定义实现。
- 永远不要模拟任何东西。永远不要使用占位符。永远不要省略代码。
- 相关时应用 SOLID 原则。使用现代框架特性而不是重新发明解决方案。
- 对想法的好坏要坦率诚实。
- 让副作用明确且最小化。
- 设计数据库模式要便于演进（避免破坏性变更）。

### 文件组织与模块化
- 默认创建多个小而专注的文件，而不是大而单一的文件
- 每个文件应该有单一职责和明确目的
- 尽可能保持文件在 350 行以内 - 通过提取工具、常量、类型或逻辑组件到单独模块来拆分大文件
- 分离关注点：工具、常量、类型、组件和业务逻辑到不同文件
- 优先组合而非继承 - 只在真正的 'is-a' 关系中使用继承，在 'has-a' 或行为混合时优先组合

- 遵循现有项目结构和约定 - 将文件放在适当目录。必要时创建新目录并移动文件。
- 使用定义明确的子目录保持组织和可扩展性
- 用清晰的文件夹层次和一致的命名约定构建项目
- 正确导入/导出 - 为可重用性和可维护性而设计

### 类型提示（必需）
- **始终**为函数参数和返回值使用类型提示
- 对复杂类型使用 `from typing import`
- 优先使用 `Optional[T]` 而不是 `Union[T, None]`
- 对数据结构使用 Pydantic 模型

```python
# 良好示例
from typing import Optional, List, Dict, Tuple

async def process_audio(
    audio_data: bytes,
    session_id: str,
    language: Optional[str] = None
) -> Tuple[bytes, Dict[str, Any]]:
    """通过管道处理音频。"""
    pass
```

### 命名约定
- **类**：PascalCase（例如 `VoicePipeline`）
- **函数/方法**：snake_case（例如 `process_audio`）
- **常量**：UPPER_SNAKE_CASE（例如 `MAX_AUDIO_SIZE`）
- **私有方法**：前导下划线（例如 `_validate_input`）
- **Pydantic 模型**：PascalCase 带 `Schema` 后缀（例如 `ChatRequestSchema`、`UserSchema`）

### 文档要求
- 每个模块需要文档字符串
- 每个公共函数需要文档字符串
- 使用 Google 风格的文档字符串
- 在文档字符串中包含类型信息

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本间的语义相似度。

    Args:
        text1: 要比较的第一个文本
        text2: 要比较的第二个文本

    Returns:
        0 到 1 之间的相似度分数

    Raises:
        ValueError: 如果任一文本为空
    """
    pass
```

### 安全优先
- 永远不要信任外部输入 - 在边界处验证一切
- 将秘钥保存在环境变量中，永远不要在代码中
- 记录安全事件（登录尝试、认证失败、速率限制、权限拒绝），但永远不要记录敏感数据（音频、对话内容、令牌、个人信息）
- 在 API 网关级别认证用户 - 永远不要信任客户端令牌
- 使用行级安全（RLS）在用户间强制数据隔离
- 设计认证以在所有客户端类型间一致工作
- 为你的平台使用安全的认证模式
- 在创建会话前在服务器端验证所有认证令牌
- 在存储或处理前清理所有用户输入

### 错误处理
- 使用具体异常而不是泛型异常
- 始终记录带上下文的错误
- 提供有用的错误消息
- 安全地失败 - 错误不应该暴露系统内部

### 可观测系统与日志标准
- 每个请求都需要关联 ID 用于调试
- 为机器而不是人类构建日志 - 使用 JSON 格式，带一致字段（时间戳、级别、关联 ID、事件、上下文）用于自动化分析
- 使跨服务边界的调试成为可能

### 状态管理
- 每个状态片段有一个真相来源
- 让状态变更明确且可追踪
- 为多服务语音处理而设计 - 使用会话 ID 进行状态协调，避免在服务器内存中存储对话数据
- 保持对话历史轻量（文本，不是音频）

### API 设计原则
- 带一致 URL 模式的 RESTful 设计
- 正确使用 HTTP 状态码
- 从第一天就版本化 API（/v1/、/v2/）
- 为列表端点支持分页
- 使用一致的 JSON 响应格式：
  - 成功：`{ "data": {...}, "error": null }`
  - 错误：`{ "data": null, "error": {"message": "...", "code": "..."} }`

## 4. 多智能体工作流与上下文注入

### 子智能体的自动上下文注入
当使用 Task 工具生成子智能体时，核心项目上下文（CLAUDE.md、project-structure.md、docs-overview.md）会通过 subagent-context-injector hook 自动注入到它们的提示中。这确保所有子智能体都能立即访问基本项目文档，无需在每个 Task 提示中手动指定。

## 5. MCP 服务器集成

### Gemini 咨询服务器
**使用场景：**
- 需要深度分析或多种方法的复杂编码问题
- 代码审查和架构讨论
- 跨多个文件调试复杂问题
- 性能优化和重构指导
- 复杂实现的详细解释
- 高度安全相关任务

**自动上下文注入：**
- 套件的 `gemini-context-injector.sh` hook 自动为新会话包含两个关键文件：
  - `/docs/ai-context/project-structure.md` - 完整项目结构和技术栈
  - `/MCP-ASSISTANT-RULES.md` - 项目特定编码标准和指导原则
- 这确保 Gemini 始终全面理解你的技术栈、架构和项目标准

**使用模式：**
```python
# 新咨询会话（项目结构由 hooks 自动附加）
mcp__gemini__consult_gemini(
    specific_question="我应该如何优化这个语音管道？",
    problem_description="需要减少实时音频处理中的延迟",
    code_context="当前管道顺序处理音频...",
    attached_files=[
        "src/core/pipelines/voice_pipeline.py"  # 你的具体文件
    ],
    preferred_approach="optimize"
)

# 在现有会话中跟进
mcp__gemini__consult_gemini(
    specific_question="内存使用怎么办？",
    session_id="session_123",
    additional_context="实现了你的建议，现在看到高内存使用"
)
```

**关键能力：**
- 带上下文保持的持续对话会话
- 多文件分析的文件附加和缓存
- 专门的辅助模式（解决、审查、调试、优化、解释）
- 复杂多步问题的会话管理

**重要：**将 Gemini 的响应作为咨询反馈对待。批判性评估建议，将有价值的洞察整合到你的解决方案中，然后继续实现。

### Context7 文档服务器
**仓库**：[Context7 MCP 服务器](https://github.com/upstash/context7)

**使用场景：**
- 使用外部库/框架（React、FastAPI、Next.js 等）
- 需要超出训练截止日期的当前文档
- 实现与第三方工具的新集成或功能
- 排查库特定问题

**使用模式：**
```python
# 将库名解析为 Context7 ID
mcp__context7__resolve_library_id(libraryName="react")

# 获取焦点文档
mcp__context7__get_library_docs(
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks",
    tokens=8000
)
```

**关键能力：**
- 最新库文档访问
- 主题焦点文档检索
- 支持特定库版本
- 与当前开发实践集成

## 6. 任务完成后协议
完成任何编码任务后，遵循此检查清单：

### 1. 类型安全与质量检查
根据修改内容运行适当命令：
- **Python 项目**：运行 mypy 类型检查
- **TypeScript 项目**：运行 tsc --noEmit
- **其他语言**：运行适当的代码检查/类型检查工具

### 2. 验证
- 确保所有类型检查通过后再认为任务完成
- 如果发现类型错误，在标记任务完成前修复它们

# 重要指令提醒
按要求做；不多不少。
除非绝对必要以实现目标，否则永远不要创建文件。
始终优先编辑现有文件而不是创建新文件。
除非用户明确要求，否则永远不要主动创建文档文件（*.md）或 README 文件。只有在用户明确要求时才创建文档文件。