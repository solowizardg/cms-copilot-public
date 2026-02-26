# 项目问题与建议

在审查代码库后，发现了以下问题和改进领域：

## 1. 硬编码值与配置

### 1.1 MCP 客户端中的硬编码默认站点 ID
**位置**: `src/agent/tools/mcp.py` (第 36 行)
**问题**: 默认 `site_id` 回退到一个硬编码的 UUID (`019b6d33-367c-7244-a6ae-af42b7f32090`)。
**风险**: 如果缺少环境变量 `CMS_SITE_ID`，代理将静默地在硬编码站点 ID 上操作，这可能导致数据泄露或意外修改开发/测试站点。
**建议**: 移除硬编码回退，或者在缺失 ENV 时显式引发错误。

### 1.2 提示词模型名称不匹配
**位置**: `src/agent/nodes/router.py` (第 69, 176 行)
**问题**: UI 面向用户的步骤显式说明 "调用意图分类模型（gpt-4.1-nano）"。
**风险**: 实际使用的模型是通过 `config.py` 中的 `LLM_NANO_MODEL` 配置的。如果配置更改 (例如改为 `gemini-1.5-flash`)，UI 文本将会产生误导。
**建议**: 在 UI 消息的 f-string 中使用 `LLM_NANO_MODEL` 变量。

## 2. 性能与架构

### 2.1 MCP 客户端重复创建
**位置**: `src/agent/tools/mcp.py` -> `call_mcp_tool`
**问题**: 每次工具调用内部都会调用 `_create_mcp_client`。这会每次实例化一个新的 `MultiServerMCPClient`。
**风险**: 根据传输实现的不同，这可能涉及每次工具执行的握手开销 (SSE/HTTP 连接建立)，从而拖慢代理速度。
**建议**: 考虑实现单例模式或上下文管理器，以便在请求生命周期内重用 MCP 客户端实例 (如果是无状态的)。

## 3. 状态管理

### 3.1 状态对象复杂性
**位置**: `src/agent/state.py`
**问题**: `CopilotState` 包含大量 UI 特定的 ID 字段 (例如 `article_ui_id`, `report_ui_id`, `report_progress_ui_id`...)。
**风险**: 随着应用程序的增长，在顶层管理这些离散 ID 会变得混乱且容易出错。
**建议**: 考虑将 UI 状态分组到嵌套字典 (例如 `ui_context: dict`) 或使用更结构化的方法来管理活动 UI 组件 ID。

## 4. 错误处理

### 4.1 路由器兜底逻辑
**位置**: `src/agent/nodes/router.py`
**问题**: 兜底逻辑使用简单的关键词匹配 (`if "文章" in user_text...`)。
**风险**: 虽然作为安全网很有用，但这会在 LLM 失败 (异常) 时覆盖它。但是，如果 LLM 返回 "unknown" (逻辑流)，则适用标准流程。
**建议**: 确保 `llm_nano_nostream.ainvoke` 具有适当的超时处理，以便在模型卡住时快速触发兜底。
