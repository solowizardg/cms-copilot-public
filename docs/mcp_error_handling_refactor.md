# MCP 错误处理增强与架构重构说明

## 概览
本次改动旨在提升系统对 MCP (Model Context Protocol) 工具调用的健壮性，统一错误处理机制，并消除代码中的逻辑重复。改动涵盖了从底层的工具封装到上层的业务节点（Report 和 Shortcut）。

## 核心改动

### 1. 业务逻辑增强 (Nodes)

#### **Report 节点 (`src/agent/nodes/report.py`)**
- **精准错误捕获**：引入 `check_ga_tool_error` 统一判断 GA 工具返回的异常情况。
- **授权过期处理**：识别 `TOKEN_REFRESH_FAILED` 错误码，自动引导用户重新进行 OAuth 授权，修复了之前可能出现的“默默失败”问题。
- **UI 反馈优化**：在 `report_progress` UI 消息中增加了对 `auth_expired` 和 `tool_error` 状态的支持，提供更友好的错误文案。

#### **Shortcut 节点 (`src/agent/nodes/shortcut.py`)**
- **结果解析统一**：使用 `is_mcp_error_result` 替代硬编码判断，支持解析 MCP 常见的列表包装格式 (`list[{"text": "..."}]`)。
- **健壮性提升**：增强了对 JSON 解析失败的容错处理，确保工具返回非标准 JSON 时系统不会崩溃。

### 2. 工具层重构 (Tools)

#### **新增 `src/agent/tools/mcp_utils.py` (公共库)**
为了遵循 DRY 原则，我们将所有 MCP 相关的通用逻辑提取到了该模块中：
- **`get_mcp_structured_content`**：统一提取结构化返回内容。
- **`extract_mcp_error_message`**：多层级寻找最合适的错误提示文案。
- **`patch_mcp_streamable_http_bom`**：**关键修复**。自动剥离部分服务端返回中携带的 UTF-8 BOM 头，防止 LangChain 解析 JSON 失败。
- **`normalize_mcp_json_result`**：规范化工具输出为标准可序列化的 JSON 对象。

#### **模块适配 (`ga_mcp.py` & `site_mcp.py`)**
- 这两个模块已切换至 `mcp_utils.py`，大幅精简了重复代码（每处节省约 80+ 行）。
- **针对性 Patch**：在 `site_mcp.py` 中保留了 BOM Patch，以解决部分服务端返回数据带 BOM 头导致解析崩溃的问题。根据评估，GA MCP 服务端不存在此类问题，因此在 `ga_mcp.py` 中去除了该 Patch 以保持逻辑精简。

## 重构带来的优势
1. **更强的容错性**：系统现在能处理更多边缘情况（如 BOM 头、非标准 JSON 返回、特定业务错误码）。
2. **更佳的用户引导**：明确区分“授权过期”与“一般错误”，减少用户困惑。
3. **更易于维护**：解析逻辑收束于一处，未来的协议变动只需修改 `mcp_utils.py` 即可全局生效。

## 涉及文件
- **节点层**：`src/agent/nodes/report.py`, `src/agent/nodes/shortcut.py`
- **工具层**：`src/agent/tools/mcp_utils.py` (New), `src/agent/tools/ga_mcp.py`, `src/agent/tools/site_mcp.py`
