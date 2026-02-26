"""状态定义模块。

定义主图和子图的状态类型。
"""

from typing import Any, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer
from typing_extensions import Annotated, TypedDict


class CopilotState(TypedDict):
    """主图状态。"""

    # 消息列表
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # UI 消息列表（Generative UI）
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    # 网站相关信息
    tenant_id: str | None
    site_id: str | None
    site_url: str | None
    oauth_token: str | None
    # 意图识别结果
    intent: str | None
    intent_ui_id: str | None
    intent_anchor_id: str | None
    intent_started_at: float | None
    # RAG 工作流 UI（rag_workflow）
    rag_ui_id: str | None
    rag_anchor_id: str | None
    rag_started_at: float | None
    rag_session_id: str | None

    # SEO 规划工作流
    seo_ui_id: str | None
    seo_anchor_id: str | None
    # 站点报告工作流
    report_ui_id: str | None
    report_anchor_id: str | None
    property_id: str | None  # GA Property ID（由 report_ui 从 auth/header 写入，传入 report 子图）
    report_progress_ui_id: str | None
    report_charts_ui_id: str | None
    report_insights_ui_id: str | None
    report_progress_insights_ui_id: str | None
    # Report 洞察确认（不使用 interrupt，改为前端 submit 继续）
    report_insights_pending: bool | None  # 是否在等待用户确认继续洞察
    report_resume_mode: str | None  # 恢复模式（如 "insights"）
    report_confirm_insights_ui_id: str | None  # 确认卡 UI id（用于隐藏/merge）
    insights_confirmed: bool | None  # 是否确认执行洞察分析（由 submit 写回，供 report 子图读取）
    # Report 子图数据（提升到主图，保证恢复对话时可读取）
    tool_result: Any | None  # 工具原始结果（已尽量规整）
    evidence_pack: dict[str, Any] | None  # 证据包（如仍使用）
    # Shortcut 工作流（mcp_workflow）- 用于 interrupt 时 values 快照兜底
    shortcut_ui_id: str | None
    shortcut_anchor_id: str | None
    tools: list[dict[str, Any]] | None  # Shortcut 工具缓存（供下次复用）
    tools_fetched_at: float | None  # 工具缓存时间戳（秒）
    # entry 节点设置的跳转目标
    resume_target: str | None
    # 直接指定意图（跳过意图识别）
    direct_intent: str | None
    # 文章工作流
    article_ui_id: str | None
    article_anchor_id: str | None    
    # ============ 文章澄清流程（article_clarify）===========
    article_clarify_pending: bool | None
    article_topic: str | None
    article_content_format: str | None
    article_target_audience: str | None
    article_tone: str | None
    article_app_id: str | None
    article_app_name: str | None
    article_model_id: str | None
    article_missing: list[str] | None
    article_clarify_question: str | None
    article_clarify_ui_id: str | None
    article_clarify_anchor_id: str | None
    article_clarify_summary_ui_id: str | None
    article_clarify_summary_anchor_id: str | None
    article_writing_requirements: str | None  # 写作要求（可选）
    # MCP Token 相关（用于 article 子图）
    mcp_token: str | None  # MCP 访问令牌
    mcp_token_expires_at: float | None  # Token 过期时间戳（秒）


class ShortcutState(TypedDict):
    """Shortcut 子图状态。

    与父图共享 messages/ui 字段，子图会自动继承父图的 checkpointer。
    """

    # 与父图共享的字段
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    tenant_id: str | None
    site_id: str | None
    # Intent Router card (for hiding after workflow starts)
    intent_ui_id: str | None
    intent_anchor_id: str | None
    # 子图专属字段（Plan → Execute）
    user_text: str | None  # 用户输入（用于生成计划）
    tools: list[dict[str, Any]] | None  # 可用工具列表（轻量描述：code/name/desc/schema 可选）
    tools_fetched_at: float | None  # 工具列表拉取时间戳（秒）
    is_capability_inquiry: bool | None  # 是否为能力询问（用户询问"能做什么"）
    needs_params: bool | None  # 是否需要用户补充参数
    plan_steps: list[dict[str, Any]] | None  # 执行计划 steps（title/tool/args/is_risky）
    current_step_idx: int | None  # 当前 step 下标
    current_step: dict[str, Any] | None  # 当前 step 内容
    step_outputs: list[dict[str, Any]] | None  # 每步执行结果/错误/是否跳过/耗时
    pending_decision: dict[str, Any] | None  # interrupt 恢复的临时决策（approve/skip/cancel）
    cancelled: bool | None  # 是否被用户取消
    error: str | None  # 运行错误（fatal）
    # MCP Token 相关
    mcp_token: str | None  # MCP 访问令牌
    mcp_token_expires_at: float | None  # Token 过期时间戳（秒）
    # UI 相关（复用 mcp_workflow）
    shortcut_anchor_id: str | None  # UI 锚点 message id（由主图 shortcut_ui 写入）
    shortcut_ui_id: str | None  # UI 卡片 id（由主图 shortcut_ui 写入）


class ReportState(TypedDict):
    """Report 子图状态。

    用于生成站点统计报告的工作流状态。
    """

    # 与父图共享的字段
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    tenant_id: str | None
    site_id: str | None
    # 从父图传递的 UI 相关字段
    report_ui_id: str | None  # 父图传递的 UI ID
    report_anchor_id: str | None  # 父图传递的锚点 ID
    report_progress_ui_id: str | None
    report_charts_ui_id: str | None
    report_insights_ui_id: str | None
    report_progress_insights_ui_id: str | None  # 洞察生成阶段的专有进度条 ID
    # Report 洞察确认（不使用 interrupt，改为前端 submit 继续）
    report_insights_pending: bool | None
    report_resume_mode: str | None
    report_confirm_insights_ui_id: str | None
    # Intent Router card (for hiding after report starts)
    intent_ui_id: str | None
    intent_anchor_id: str | None
    # 子图专属字段
    property_id: str | None  # GA Property ID（从 header 获取）
    user_text: str | None  # 用户输入
    is_capability_inquiry: bool | None  # 是否为能力询问（如"能做什么"）
    current_step: str | None  # 当前步骤
    report_type: str | None  # 报告类型：overview/traffic/content/engagement/performance
    report_type_name: str | None  # 报告类型中文名
    period: dict[str, Any] | None  # 报告周期
    # 各维度数据
    # （旧字段已移除：traffic_data, traffic_sources, top_pages, content_stats, device_stats, user_engagement, performance, summary, report_data）
    # ============ 洞察层（Report v2）===========
    evidence_pack: dict[str, Any] | None  # 证据包（纯代码生成，可证明事实）
    data_quality: dict[str, Any] | None  # 数据质量提示（阈值/缺失口径/样本不足等）
    insights: dict[str, Any] | None  # 解读（one-liner/evidence/hypotheses）
    actions: list[dict[str, Any]] | None  # 建议动作（仅展示，不触发）
    todos: list[dict[str, Any]] | None  # 可执行 Todo（写入 state，仅展示）
    trace: dict[str, Any] | None  # 洞察轨迹（引用 todo 步骤）
    step_outputs: list[dict[str, Any]] | None  # 洞察逐步产出（对应 todo 步骤）
    # ============ MCP 动态工具调用（Report 新流程）===========
    options: list[dict[str, Any]] | None  # 可选工具列表（UI 展示）
    tool_specs: list[Any] | None  # MCP 工具详细规格（GAToolSpec 列表）
    tool_result: Any | None  # 工具原始结果（已尽量规整）
    tool_error: str | None  # 工具执行错误
    insights_confirmed: bool | None  # 是否确认执行洞察分析
    error: str | None  # 错误信息
    # UI 相关（子图内部使用）
    ui_anchor_id: str | None  # UI 锚点 message id
    ui_id: str | None  # UI 卡片 id
