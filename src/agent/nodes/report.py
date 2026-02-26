"""站点 Report 节点模块（ReAct：AI 规划 → 连续调用 GA MCP tools → 图表展示）。

目标：
- 用户提问 → 意图识别进入 report
- AI 基于需求规划要调用哪些 GA MCP tools（可能多次 run_report）
- 执行 tool calling 获取数据
- 聚合为前端 SiteReportCard 期望的 charts 结构并展示
"""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, Awaitable, Callable

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import AIMessage
from langchain_core.tools import ToolException
from langgraph.config import get_stream_writer
from langgraph.graph.ui import UIMessage, push_ui_message

from agent.config import get_logger
from agent.insights.report_insights_agent import (
    generate_report_insights_streaming,
)
from agent.insights.reporting.evidence import build_evidence_pack
from agent.state import CopilotState, ReportState
from agent.prompts.report import REPORT_PLANNING_PROMPT
from agent.tools.ga_mcp import (
    check_ga_tool_error,
    is_token_expired_error,
    list_ga_tool_specs,
    normalize_ga_tool_result,
    with_ga_tools,
)
from agent.utils.helpers import find_ai_message_by_id, latest_user_message, message_text
from agent.utils.llm import llm_nano, llm_nano_nostream, llm_nostream

logger = get_logger(__name__)

DEFAULT_DAYS = int(os.getenv("CMS_GA_DEFAULT_DAYS", "7"))


def _default_run_report_args(property_id: str, days: int = 7) -> dict[str, Any]:
    """生成默认的 run_report 参数（时间趋势）。"""
    return {
        "property_id": property_id,
        "date_ranges": [{"start_date": f"{days}daysAgo", "end_date": "yesterday"}],
        "dimensions": ["date"],
        "metrics": ["activeUsers", "sessions", "screenPageViews"],
        "limit": 10000,
    }


def _extract_property_id(text: str) -> str | None:
    m = re.search(r"(properties/\d+)", text or "", flags=re.IGNORECASE)
    return m.group(1) if m else None


def _get_anchor_msg_by_id(state: ReportState, anchor_id: str | None) -> AIMessage:
    if anchor_id:
        for m in state.get("messages", []):
            if isinstance(m, AIMessage) and getattr(m, "id", None) == anchor_id:
                return m
    return AIMessage(id=str(uuid.uuid4()), content="")


def _get_anchor_msg(state: ReportState) -> AIMessage:
    anchor_id = state.get("report_anchor_id") or state.get("ui_anchor_id")
    return _get_anchor_msg_by_id(state, anchor_id)


def _get_ui_id(state: ReportState) -> str | None:
    return state.get("report_ui_id")

def _get_progress_ui_id(state: ReportState) -> str | None:
    return state.get("report_progress_ui_id")

def _get_charts_ui_id(state: ReportState) -> str | None:
    return state.get("report_charts_ui_id")


def _get_insights_ui_id(state: ReportState) -> str | None:
    return state.get("report_insights_ui_id")

def _make_ui_message(
    name: str,
    ui_id: str | None,
    anchor_msg: AIMessage,
    props: dict[str, Any],
    *,
    merge: bool = True,
) -> UIMessage:
    """通过 push_ui_message 发送 UI stream，并写入 state.ui。"""
    stable_id = ui_id or f"{name}:{getattr(anchor_msg, 'id', '')}"
    return push_ui_message(
        name=name,
        props=props,
        id=stable_id,
        message=anchor_msg,
        merge=merge,
    )


def _build_report_snapshot(
    *,
    site_id: str | None,
    tool_result: dict[str, Any] | None,
    data_quality: dict[str, Any] | None,
    insights: dict[str, Any] | None,
    actions: Any,
    todos: Any,
) -> dict[str, Any]:
    """构造可安全覆盖的 report 快照（避免发送 None 清空字段）。"""
    tool_result = tool_result or {}
    report: dict[str, Any] = {
        "site_id": site_id,
        "report_type": "overview",
        "report_type_name": "Site Data Report",
        "summary": tool_result.get("summary") or {},
        "charts": tool_result.get("charts") or {},
    }
    if data_quality:
        report["data_quality"] = data_quality
    if insights:
        report["insights"] = insights
    if isinstance(actions, list) and actions:
        report["actions"] = actions
    if isinstance(todos, list) and todos:
        report["todos"] = todos
    return report


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """从模型输出中提取 JSON object（兼容 ```json ...``` 包裹）。"""
    t = (text or "").strip()
    if not t:
        return None
    # 直接尝试
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # 尝试截取第一个 { 到最后一个 }
    l = t.find("{")
    r = t.rfind("}")
    if 0 <= l < r:
        try:
            obj = json.loads(t[l : r + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _try_build_summary_from_report(result: dict[str, Any]) -> dict[str, Any] | None:
    """从 GA report rows 推导 summary（用于前端摘要区）。"""
    try:
        metric_headers = result.get("metric_headers") or []
        metric_names = [h.get("name") for h in metric_headers if h.get("name")]
        rows = result.get("rows") or []
        totals: dict[str, float] = {mn: 0.0 for mn in metric_names}
        for r in rows:
            met_vals = r.get("metric_values") or []
            for i, mn in enumerate(metric_names):
                if i < len(met_vals):
                    v = (met_vals[i] or {}).get("value")
                    try:
                        totals[mn] += float(v)
                    except Exception:
                        pass
        total_visits = int(totals.get("sessions", 0))
        total_unique = int(totals.get("activeUsers", 0))
        total_pv = int(totals.get("screenPageViews", 0))
        return {
            "total_visits": total_visits,
            "total_unique_visitors": total_unique,
            "total_page_views": total_pv,
            "avg_session_duration": 0,
            "bounce_rate": 0.0,
            "pages_per_session": round(total_pv / total_visits, 2) if total_visits > 0 else 0,
        }
    except Exception:
        return None


def _filter_args_by_schema(args: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """根据工具的 input_schema 过滤参数，只保留工具实际需要的参数。
    
    这样可以避免传入工具不支持的参数（如 check_report_compatibility 不接受 date_ranges）。
    """
    if not schema or not isinstance(schema, dict):
        return args
    
    # 从 JSON Schema 中提取允许的属性名
    properties = schema.get("properties") or {}
    allowed_keys = set(properties.keys())
    
    # 如果 schema 中有 required 字段，确保这些字段被保留
    required = set(schema.get("required") or [])
    
    # 过滤参数：只保留 schema 中定义的属性
    filtered: dict[str, Any] = {}
    for key, value in args.items():
        if key in allowed_keys:
            filtered[key] = value
    
    # 确保 required 字段存在（即使值为 None）
    for req_key in required:
        if req_key not in filtered and req_key in args:
            filtered[req_key] = args[req_key]
    
    return filtered


def _normalize_ga_tool_args(tool_name: str, args: Any, *, property_id: str) -> dict[str, Any]:
    """把 LLM 生成的参数归一化，并补齐 GA MCP 工具的必填字段。

    关键点：
    - GA MCP run_report 必填：property_id / date_ranges / dimensions / metrics
    - GA MCP run_realtime_report 必填：property_id / dimensions / metrics
    - LLM 可能输出驼峰字段名（dateRanges、orderBys 等），这里做一次兼容转换
    """
    if not isinstance(args, dict):
        args = {}

    # 常见驼峰/变体转 snake_case
    alias_map = {
        "propertyId": "property_id",
        "dateRanges": "date_ranges",
        "dateRange": "date_ranges",
        "dimension": "dimensions",
        "dims": "dimensions",
        "metric": "metrics",
        "orderBys": "order_bys",
        "currencyCode": "currency_code",
        "returnPropertyQuota": "return_property_quota",
    }
    normalized: dict[str, Any] = {}
    for k, v in args.items():
        kk = alias_map.get(k, k)
        normalized[kk] = v

    # 统一 property_id
    normalized.setdefault("property_id", property_id)

    if tool_name == "run_report":
        # 默认 date_ranges
        normalized.setdefault(
            "date_ranges",
            [{"start_date": f"{DEFAULT_DAYS}daysAgo", "end_date": "yesterday"}],
        )
        # 默认 dimensions/metrics（空列表也会补齐，GA API 要求至少其一非空）
        if not normalized.get("dimensions"):
            normalized["dimensions"] = ["date"]
        if not normalized.get("metrics"):
            normalized["metrics"] = ["activeUsers", "sessions", "screenPageViews"]
    elif tool_name == "run_realtime_report":
        if not normalized.get("dimensions"):
            normalized["dimensions"] = ["country"]
        if not normalized.get("metrics"):
            normalized["metrics"] = ["activeUsers"]

    # 确保 list 类型
    # 确保 list 类型，并展平内部可能的 dict（LLM 有时会输出 [{"name": "date"}]）
    def _flatten_list(lst: list) -> list[str]:
        res = []
        for x in lst:
            if isinstance(x, dict):
                # 尝试取 name 或 value，否则转 str
                v = x.get("name") or x.get("value") or str(x)
                res.append(str(v))
            else:
                res.append(str(x))
        return res

    if "dimensions" in normalized:
        if not isinstance(normalized["dimensions"], list):
            normalized["dimensions"] = [normalized["dimensions"]]
        normalized["dimensions"] = _flatten_list(normalized["dimensions"])

    if "metrics" in normalized:
        if not isinstance(normalized["metrics"], list):
            normalized["metrics"] = [normalized["metrics"]]
        normalized["metrics"] = _flatten_list(normalized["metrics"])

    if "date_ranges" in normalized and not isinstance(normalized["date_ranges"], list):
        normalized["date_ranges"] = [normalized["date_ranges"]]

    return normalized


def _humanize_ga_value(dim_name: str, value: str) -> str:
    """把 GA 技术名称转换为人类可读的中文描述。"""
    if not value:
        return value
    
    # sessionDefaultChannelGroup 翻译
    if dim_name == "sessionDefaultChannelGroup":
        mapping = {
            "Organic Search": "Organic Search",
            "Direct": "Direct",
            "Paid Search": "Paid Search",
            "Organic Social": "Social Media",
            "Referral": "Referral",
            "Email": "Email",
            "Paid Social": "Paid Social",
            "Display": "Display",
            "Organic Shopping": "Organic Shopping",
            "Paid Shopping": "Paid Shopping",
            "Organic Video": "Video",
            "(Other)": "Other",
            "(not set)": "Not Set",
        }
        return mapping.get(value, value)
    
    # deviceCategory 翻译
    if dim_name == "deviceCategory":
        mapping = {
            "desktop": "Desktop",
            "mobile": "Mobile",
            "tablet": "Tablet",
        }
        return mapping.get(value.lower(), value)
    
    # 其他维度（如有需要可继续扩展）
    return value


def _build_chart_from_ga_report(result: dict[str, Any]) -> dict[str, Any] | None:
    """通用 GA report -> chart（line/bar/pie），并翻译技术名称为人类可读。"""
    rows = result.get("rows") or []
    dim_headers = result.get("dimension_headers") or []
    metric_headers = result.get("metric_headers") or []

    dim_names = [h.get("name") for h in dim_headers if h.get("name")]
    metric_names = [h.get("name") for h in metric_headers if h.get("name")]
    if not metric_names:
        return None

    data: list[dict[str, Any]] = []
    for r in rows:
        row: dict[str, Any] = {}
        dim_vals = r.get("dimension_values") or []
        met_vals = r.get("metric_values") or []
        for i, dn in enumerate(dim_names):
            if i < len(dim_vals):
                raw_val = (dim_vals[i] or {}).get("value")
                # 翻译维度值为人类可读
                row[dn] = _humanize_ga_value(dn, raw_val)
        for i, mn in enumerate(metric_names):
            if i < len(met_vals):
                v = (met_vals[i] or {}).get("value")
                try:
                    row[mn] = float(v) if "." in str(v) else int(v)
                except Exception:
                    row[mn] = v
        data.append(row)

    # 维度为 date：折线
    x_key = dim_names[0] if dim_names else "x"
    if "date" in (x_key or "").lower():
        return {
            "chart_type": "line",
            "title": "Trend",
            "data": data,
            "x_key": x_key,
            "y_keys": metric_names,
            "y_labels": metric_names,
            "colors": ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"],
        }

    # 单指标分布：仅在“分布类维度”下使用饼图；页面/内容类维度用柱状图更符合预期
    PIE_FRIENDLY_DIMS = {
        "deviceCategory",
        "sessionDefaultChannelGroup",
        "country",
        "city",
        "region",
        "browser",
        "operatingSystem",
        "platform",
        "language",
    }
    if len(metric_names) == 1 and len(data) <= 12 and (x_key in PIE_FRIENDLY_DIMS):
        pie_data = [{"name": r.get(x_key), "value": r.get(metric_names[0], 0)} for r in data]
        return {
            "chart_type": "pie",
            "title": f"{x_key} Distribution",
            "data": pie_data,
            "value_key": "value",
            "label_key": "name",
        }

    # 否则：柱状图
    y_key = metric_names[0]
    return {
        "chart_type": "bar",
        "title": f"{x_key} - {y_key}",
        "data": data,
        "x_key": x_key,
        "y_key": y_key,
        "color": "#6366f1",
        "show_change": False,
    }


def _chart_key_for_report(result: dict[str, Any], chart: dict[str, Any] | None) -> str | None:
    """根据 GA 的维度和图表类型决定塞到前端哪个 chart key。
    
    规则：
    1. 优先映射到前端已有的“标准槽位”（如 daily_visits, traffic_sources 等）。
    2. 其他维度采用 `{chart_type}_{dimension_name}` 格式，确保前端能识别图表类型并渲染。
    """
    if not chart:
        return None
    
    chart_type = chart.get("chart_type", "bar")
    dim_headers = result.get("dimension_headers") or []
    dim_names = [h.get("name") for h in dim_headers if h.get("name")]
    first = (dim_names[0] if dim_names else "unknown").lower()
    
    # 1. 标准槽位映射（保持向后兼容）
    if first == "date":
        return "daily_visits"
    if first == "sessiondefaultchannelgroup":
        return "traffic_sources"
    if first == "devicecategory":
        return "device_stats"
    
    # 2. 语义化槽位映射
    if first in {
        "pagepath", "pagetitle", "landingpage", "pagelocation", 
        "screenname", "hostname", "pagereferrer"
    } or "page" in first or "screen" in first:
        return "top_pages"
        
    if first == "eventname" or "event" in first:
        return "user_engagement"
    
    # 3. 动态槽位：{type}_{dimension} 确保前端 Recharts 能对应上组件
    # 例如：pie_country, bar_city, tech_browser 等
    prefix = ""
    if first in {"country", "city", "region", "continent"}:
        prefix = "geo_"
    elif first in {"browser", "operatingsystem", "platform"}:
        prefix = "tech_"
        
    return f"{chart_type}_{prefix}{first}"


async def _stream_chart_description_with_llm(
    chart: dict[str, Any],
    *,
    on_update: Callable[[str], Awaitable[None]] | None = None,
) -> str | None:
    """使用 LLM 流式生成图表分析，并支持按 chunk 更新 UI。"""
    if not chart or not chart.get("data"):
        return None

    try:
        # 简化数据以减少 token
        # 如果数据量过大，只取前N条或汇总信息
        data_preview = chart["data"]
        if isinstance(data_preview, list) and len(data_preview) > 10:
            data_preview = data_preview[:10]
        
        prompt = f"""You are a professional Data Analyst. Based on the following chart data, write a short English analysis conclusion.
Focus on maximum values, trend changes, or outliers. The language should be natural and professional, like reporting to a client.

Chart Title: {chart.get("title")}
Chart Type: {chart.get("chart_type")}
Data Overview: {json.dumps(data_preview, ensure_ascii=False)}

Analysis Conclusion:"""

        parts: list[str] = []
        try:
            async for chunk in llm_nano.astream(prompt, config={"callbacks": []}):
                piece = getattr(chunk, "content", chunk)
                if not isinstance(piece, str) or not piece:
                    continue
                parts.append(piece)
                if on_update:
                    await on_update("".join(parts))
        except Exception as e:
            # astream 失败时降级到非流式
            logger.warning(f"[Report] Streaming description failed, fallback to nostream: {e}")
            parts = []

        content = "".join(parts).strip()
        if content:
            return content

        resp = await llm_nano_nostream.ainvoke(prompt, config={"callbacks": []})
        return getattr(resp, "content", str(resp)).strip() or None
    except Exception as e:
        logger.warning(f"[Report] Generated description failed: {e}")
        return None


# ============ 主图节点 ============


def _get_progress_insights_ui_id(state: ReportState) -> str:
    """获取洞察阶段进度条 UI ID，确保其在 state 生命周期内唯一且稳定。"""
    if state.get("report_progress_insights_ui_id"):
        return state["report_progress_insights_ui_id"]
    # 默认 fallback（不应发生，因为 start_report_ui 会生成）
    return f"report_progress_insights:{uuid.uuid4()}"


async def start_report_ui(state: CopilotState) -> dict[str, Any]:
    """创建报告 UI 锚点和初始卡片。"""
    user_msg = latest_user_message(state)
    user_text = message_text(user_msg)

    anchor = AIMessage(id=str(uuid.uuid4()), content="")
    # 只创建锚点与 UI id；实际 UI 首次渲染放到 report_init（避免主图/子图各 push 一次导致双卡）
    progress_ui_id = f"report_progress:{anchor.id}"
    charts_ui_id = f"report_charts:{anchor.id}"
    insights_ui_id = f"report_insights:{anchor.id}"
    progress_insights_ui_id = f"report_progress_insights:{anchor.id}"

    # 从 header 获取 property_id
    from agent.utils.website_header import get_extra_headers
    extra_headers = get_extra_headers()
    property_id = extra_headers.get("property_id")

    return {
        "messages": [anchor],
        "report_progress_ui_id": progress_ui_id,
        "report_charts_ui_id": charts_ui_id,
        "report_insights_ui_id": insights_ui_id,
        "report_progress_insights_ui_id": progress_insights_ui_id,
        "report_anchor_id": anchor.id,
        "user_text": user_text,
        "property_id": property_id,
        # Pass intent router card IDs for hiding
        "intent_ui_id": state.get("intent_ui_id"),
        "intent_anchor_id": state.get("intent_anchor_id"),
    }
# ============ 子图节点 ============


async def report_init(state: ReportState) -> dict[str, Any]:
    """初始化：拉取 tools 列表，LLM 判断意图，给 UI & ReAct 规划提供上下文。"""
    anchor_msg = _get_anchor_msg(state)

    # 洞察恢复模式：跳过 init 的工具列表/进度 UI，避免重推造成 UI 重绘
    if state.get("report_resume_mode") == "insights":
        return {}

    user_msg = latest_user_message(state)
    user_text = message_text(user_msg) if user_msg else ""

    # Hide Thinking Card if exists
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)
    writer = get_stream_writer()
    
    if intent_ui_id and intent_anchor_msg and writer:
        hide_msg = push_ui_message(
             "intent_router",
             {"status": "done", "hidden": True},
             id=intent_ui_id,
             message=intent_anchor_msg,
             merge=True
        )
        writer(hide_msg)

    ui_1 = _make_ui_message(
        "report_progress",
        _get_progress_ui_id(state),
        anchor_msg,
        {
            "status": "loading",
            "step": "listing_tools",
            "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
            "active_step": 1,
            "message": "Listing tools from GA MCP...",
        },
    )

    tenant_id = state.get("tenant_id")
    site_id = state.get("site_id")
    
    # 从 GA MCP 获取工具列表（含详细描述和参数 schema）
    try:
        specs = await list_ga_tool_specs(site_id=site_id, tenant_id=tenant_id)
    except Exception as e:
        logger.warning("[Report] Failed to fetch MCP tools: %s", e)
        specs = []
    
    options = [
        {"code": s.name, "name": s.name, "desc": s.description, "schema": s.input_schema}
        for s in specs
    ]

    # ============ 检测 MCP 工具是否为空 ============
    if not specs:
        ui_empty = _make_ui_message(
            "report_progress",
            _get_progress_ui_id(state),
            anchor_msg,
            {
                "status": "error",
                "step": "no_tools",
                "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
                "active_step": 1,
                "message": "Failed to get GA MCP tool list, please check if MCP service is running.",
                "error_message": "MCP tool list is empty",
            },
        )
        return {
            "ui": [ui_1, ui_empty],
            "user_text": user_text,
            "options": [],
            "tool_specs": [],
            "is_capability_inquiry": False,
            "tool_error": "MCP tool list is empty, cannot execute report query.",
        }

    # 优先使用 state 中的 property_id（从 header 获取）
    property_id = state.get("property_id")

    # ============ LLM 意图分类：判断是能力询问还是数据请求 ============
    is_capability_inquiry = False
    try:
        from agent.utils.llm import llm_nano_nostream
        
        intent_prompt = f"""You are an Intent Classifier. Determine which category the user's question belongs to:

1. capability_inquiry: User asks what the system can do, what reports are supported, what functions are available, what data can be queried, etc.
2. data_request: User requests specific data or reports (e.g., traffic trends, visit statistics, device distribution, etc.)

User Question: {user_text}

Output only one label: capability_inquiry or data_request"""
        
        resp = await llm_nano_nostream.ainvoke(intent_prompt, config={"callbacks": []})
        intent_label = getattr(resp, "content", str(resp)).strip().lower()
        is_capability_inquiry = "capability_inquiry" in intent_label
    except Exception as e:
        logger.warning("[Report] Intent classification failed: %s", e)
        is_capability_inquiry = False

    if is_capability_inquiry:
        ui_2 = _make_ui_message(
            "report_progress",
            _get_progress_ui_id(state),
            anchor_msg,
            {
                "status": "loading",
                "step": "capability_response",
                "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
                "active_step": 1,
                "message": "Capability inquiry detected, organizing available report types...",
            },
        )
    else:
        ui_2 = _make_ui_message(
            "report_progress",
            _get_progress_ui_id(state),
            anchor_msg,
            {
                "status": "loading",
                "step": "planning",
                "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
                "active_step": 1,
                "message": f"Got {len(specs)} GA MCP tools, AI is planning the call...",
            },
        )

    return {
        "ui": [ui_1, ui_2],
        "user_text": user_text,
        "tool_specs": specs,
        "is_capability_inquiry": is_capability_inquiry,
        "property_id": property_id,  # 保存到 state，供后续节点使用
    }


async def report_execute_tool(state: ReportState) -> dict[str, Any]:
    """Planning + Execution：先基于 MCP 工具列表规划，再批量执行。"""
    anchor_msg = _get_anchor_msg(state)

    tenant_id = state.get("tenant_id")
    site_id = state.get("site_id")
    user_text = state.get("user_text") or ""
    tool_specs = state.get("tool_specs") or []

    # 优先使用 state 中的 property_id（从 header 获取），否则从用户文本提取，最后使用默认值
    property_id = state.get("property_id") 

    ui_fetch = _make_ui_message(
        "report_progress",
        _get_progress_ui_id(state),
        anchor_msg,
        {
            "status": "loading",
            "step": "fetching_data",
            "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
            "active_step": 2,
            "message": "AI is planning data fetching scheme based on MCP tool list...",
        },
    )

    # 收集每个图表的 chart_analysis UI，用于：1) 流式推送 2) 返回 ui 做持久化/回放
    chart_ui_updates: list[UIMessage] = []

    # 构建工具详情（给 LLM 参考）
    tool_details = []
    for spec in tool_specs: # 不要限制数量，除非真的装不下
        # 既然我们重构了，input_schema 里会有极其详细的定义
        # 直接转成 JSON 字符串贴进去
        schema_str = json.dumps(spec.input_schema, indent=2, ensure_ascii=False)
        
        tool_details.append(f"### Tool: {spec.name}\n")
        tool_details.append(f"Description: {spec.description}\n")
        tool_details.append(f"Args Definition (Schema):\n```json\n{schema_str}\n```\n")
    tool_info = "\n".join(tool_details)

    # Planning + Execution 模式：先让 AI 规划出需要哪些数据
    planning_prompt = REPORT_PLANNING_PROMPT.format(
        user_text=user_text,
        tool_info=tool_info,
        property_id=property_id
    )

    # 构建工具名到 schema 的映射
    tool_schema_map: dict[str, dict[str, Any]] = {
        spec.name: spec.input_schema for spec in tool_specs
    }
    
    async def _run(tools_by_name: dict[str, Any]):
        """Planning + Execution 模式：先规划方案，再批量执行，避免 ReAct 重复同样参数。"""
        plan_items: list[dict[str, Any]] | None = None
        plan_descs: list[str] = []

        # Step 1: LLM 规划（内部 JSON）
        try:
            # 使用 LangChain + Gemini
            llm_gemini = ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_FLASH_MODEL"),
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                thinking_level=os.getenv("REPORT_THINKING_LEVEL"),
            )
            plan_resp = await llm_gemini.ainvoke(planning_prompt,config={"callbacks": []})
            plan_content = plan_resp.content
            
            # Handle case where content is a list of blocks (e.g. [{'type': 'text', 'text': '...'}])
            if isinstance(plan_content, list):
                plan_text = "".join([
                    item.get("text", "") for item in plan_content 
                    if isinstance(item, dict) and item.get("type") == "text"
                ])
            else:
                plan_text = str(plan_content)

            plan_json = json.loads(plan_text)
            maybe_items = plan_json.get("plan") if isinstance(plan_json, dict) else None
            if isinstance(maybe_items, list) and maybe_items:
                plan_items = maybe_items
        except Exception as e:
            logger.error(f"Gemini Planning Failed: {e}")
            plan_items = None
        
        if not plan_items:
            # Plan generation failed (empty or None), notify user to retry
            ui_fail_msg = _make_ui_message(
                "report_progress",
                _get_progress_ui_id(state),
                _get_anchor_msg(state),
                {
                    "status": "error",
                    "step": "ai_planning_failed",
                    "steps": ["AI Planning"],
                    "active_step": 0,
                    "message": "AI failed to plan the report. Please try rephrasing your question.",
                    "error_message": "PLANNING_FAILED",
                },
            )
            return {
                "ui": [ui_fail_msg],
                "tool_result": None,
                "tool_error": "AI Planning Failed",
            }
        # 步骤 2：去重（基于 dimensions，避免重复调用）
        seen_dims: set[str] = set()
        unique_plan: list[dict[str, Any]] = []
        for item in plan_items:
            dims = item.get("args", {}).get("dimensions") or []
            # 标准化：统一小写，排序
            dims_normalized = [str(d).lower().strip() for d in dims]
            dims_key = ",".join(sorted(dims_normalized)) if dims_normalized else "__no_dims__"
            if dims_key not in seen_dims and len(unique_plan) < 6:
                seen_dims.add(dims_key)
                unique_plan.append(item)

        # 步骤 3：依次执行 plan 中的工具调用
        charts: dict[str, Any] = {}
        summary: dict[str, Any] | None = None
        raws: list[Any] = []
        tool_error_message: str | None = None  # GA MCP 错误文案（token 过期或一般错误）
        tool_error_is_auth: bool = False  # True=需重新 OAuth，False=一般错误

        writer = get_stream_writer()

        for idx, item in enumerate(unique_plan):
            if tool_error_message is not None:
                break
            tool_name = item.get("tool")
            args = item.get("args") or {}
            desc = item.get("desc") or tool_name
            if desc:
                plan_descs.append(str(desc))

            # “处理中…”提示：在 MCP 调用开始时显示，但隐藏时机保持在“开始输出分析内容/分析结束”等位置
            loading_ui_id = f"chart_analysis_loading:{getattr(anchor_msg, 'id', '')}:mcp:{idx}"
            loading_title = str(desc or tool_name or "Data Query")
            loading_shown = False

            if tool_name in {"run_report", "run_realtime_report"}:
                args = _normalize_ga_tool_args(str(tool_name), args, property_id=property_id)
            
            # 根据工具的 schema 过滤参数，移除工具不支持的参数
            tool_schema = tool_schema_map.get(tool_name)
            if tool_schema:
                args_before_filter = args.copy()
                args = _filter_args_by_schema(args, tool_schema)
                if args != args_before_filter:
                    removed_keys = set(args_before_filter.keys()) - set(args.keys())
                    if removed_keys:
                        logger.debug("[MCP Debug] ⚠️ 已过滤工具 %s 不支持的参数: %s", tool_name, removed_keys)

            tool_obj = tools_by_name.get(tool_name)
            if tool_obj is None:
                norm = {"error": f"unknown tool: {tool_name}"}
            else:
                try:
                    # MCP 开始调用前：先显示“处理中…”提示（用 desc 作为标题）
                    loading_ui_msg = _make_ui_message(
                        name="chart_analysis_loading",
                        ui_id=loading_ui_id,
                        anchor_msg=anchor_msg,
                        props={
                            "chart_key": str(tool_name or ""),
                            "chart_title": loading_title,
                            "hidden": False,
                        },
                    )
                    if writer:
                        writer({"ui": [loading_ui_msg]})
                        loading_shown = True

                    # 打印调用参数
                    logger.debug("[MCP Debug] 调用工具: %s", tool_name)
                    logger.debug("[MCP Debug] 调用参数: %s", json.dumps(args, indent=2, ensure_ascii=False))
                    
                    out = await tool_obj.ainvoke(args)

                    # 统一判断 GA MCP 错误返回（token 过期 / 一般错误）
                    is_err, err_msg, is_auth_err = check_ga_tool_error(out)
                    if is_err:
                        tool_error_message = err_msg
                        tool_error_is_auth = is_auth_err
                        logger.warning(
                            "[Report] GA MCP tool error (auth=%s): %s",
                            is_auth_err,
                            tool_error_message,
                        )
                        break

                    # 打印原始 MCP 返回结果
                    logger.debug("[MCP Debug] 原始返回结果 (type: %s):", type(out))
                    if isinstance(out, dict):
                        logger.debug("%s", json.dumps(out, indent=2, ensure_ascii=False))
                    elif isinstance(out, str):
                        logger.debug("%s", out)
                    else:
                        logger.debug("%s", out)
                    
                    norm = normalize_ga_tool_result(out)
                    
                    # 打印规范化后的结果
                    logger.debug("[MCP Debug] 规范化后的结果: %s", json.dumps(norm, indent=2, ensure_ascii=False))
                    
                    # 检查关键字段
                    if isinstance(norm, dict):
                        rows_count = len(norm.get("rows") or [])
                        dim_headers = norm.get("dimension_headers") or []
                        metric_headers = norm.get("metric_headers") or []
                        logger.debug("[MCP Debug] 数据统计: rows=%s, dimensions=%s, metrics=%s", rows_count, len(dim_headers), len(metric_headers))
                        if rows_count == 0:
                            logger.debug("[MCP Debug] ⚠️ 警告: 返回的数据行数为 0，可能没有匹配的数据")
                    
                except ToolException as e:
                    # 特定处理 LangChain Tool 执行异常（如 Validation Error / input_value=None）
                    # 这通常意味着 MCP 连接问题、授权过期导致返回空、或参数严重错误
                    err_msg = str(e)
                    logger.warning("[MCP Error] ToolException caught: %s", err_msg)
                    if "input_value=None" in err_msg or "validation error" in err_msg:
                        # Suspect Auth failure or server no response
                        tool_error_message = "Please check your Google Analytics authorization status. The service returned an empty response, which usually indicates an expired token."
                        tool_error_is_auth = True # Assume auth issue, guide to check
                    else:
                        tool_error_message = f"Tool execution error: {err_msg}"
                    
                    # 记录详细日志但不崩溃
                    norm = {"error": tool_error_message}
                    break # 发生严重工具错误，通常中断后续执行比较安全

                except Exception as e:
                    logger.exception("[MCP Debug] ❌ 调用工具时发生异常: %s", e)
                    error_msg = str(e)
                    norm = {"error": error_msg}
                    
                    # 检查是否为 token 过期错误
                    if is_token_expired_error(error_msg):
                        tool_error_message = error_msg
                        tool_error_is_auth = True
                        logger.warning(
                            "[Report] 检测到 TOKEN_REFRESH_FAILED (from exception): %s",
                            error_msg,
                        )
                        break
                    else:
                        # 其他异常，也设置为工具错误
                        tool_error_message = error_msg
                        tool_error_is_auth = False
                        logger.warning(
                            "[Report] 工具调用异常: %s",
                            error_msg,
                        )
                        break

            raws.append({"desc": desc, "tool": tool_name, "args": args, "result": norm})
            if summary is None:
                summary = _try_build_summary_from_report(norm)
            if isinstance(norm, dict) and ("rows" in norm or "dimension_headers" in norm):
                chart = _build_chart_from_ga_report(norm)
                key = _chart_key_for_report(norm, chart)
                if key and chart:
                    # 如果 key 已存在，跳过（避免覆盖）
                    if key not in charts:
                        chart_title = chart.get("title", key)
                        chart_type = chart.get("chart_type", "chart")
                        charts[key] = chart

                        # 1) 先推一个空分析卡，随后流式更新同一张卡
                        analysis_ui_id = f"chart_analysis:{getattr(anchor_msg, 'id', '')}:{key}"
                        analysis_props = {
                            "chart_key": key,
                            "chart_title": chart_title,
                            "chart_type": chart_type,
                            "description": "",
                        }
                        analysis_ui_msg = _make_ui_message(
                            name="chart_analysis",
                            ui_id=analysis_ui_id,
                            anchor_msg=anchor_msg,
                            props=analysis_props,
                        )
                        if writer:
                            writer({"ui": [analysis_ui_msg]})

                        last_analysis_ui: UIMessage | None = None
                        loading_hidden = False

                        async def _update_analysis(text: str) -> None:
                            nonlocal last_analysis_ui, loading_hidden
                            # 隐藏位置保持不变：开始输出分析内容时隐藏“处理中…”
                            if loading_shown and not loading_hidden:
                                loading_hidden = True
                                loading_hide_msg = _make_ui_message(
                                    name="chart_analysis_loading",
                                    ui_id=loading_ui_id,
                                    anchor_msg=anchor_msg,
                                    props={
                                        "chart_key": str(tool_name or ""),
                                        "chart_title": loading_title,
                                        "hidden": True,
                                    },
                                )
                                if writer:
                                    writer({"ui": [loading_hide_msg]})
                            ui_msg = _make_ui_message(
                                name="chart_analysis",
                                ui_id=analysis_ui_id,
                                anchor_msg=anchor_msg,
                                props={
                                    "chart_key": key,
                                    "chart_title": chart_title,
                                    "chart_type": chart_type,
                                    "description": text,
                                },
                            )
                            last_analysis_ui = ui_msg
                            if writer:
                                writer({"ui": [ui_msg]})

                        # 2) 流式生成分析文本，并在流结束后落盘到 chart
                        desc_text = await _stream_chart_description_with_llm(chart, on_update=_update_analysis)
                        if desc_text:
                            chart["description"] = desc_text
                            if last_analysis_ui is None:
                                last_analysis_ui = _make_ui_message(
                                    name="chart_analysis",
                                    ui_id=analysis_ui_id,
                                    anchor_msg=anchor_msg,
                                    props={
                                        "chart_key": key,
                                        "chart_title": chart_title,
                                        "chart_type": chart_type,
                                        "description": desc_text,
                                    },
                                )
                        if last_analysis_ui is not None:
                            chart_ui_updates.append(last_analysis_ui)
                        # 注意：loading 卡已前置到 MCP 调用阶段，这里不再显示

                        # 3) 紧跟着输出单图表卡，实现“分析 → 图表”成对结构
                        chart_ui_id = f"report_charts:{getattr(anchor_msg, 'id', '')}:{key}"
                        report_snapshot = {
                            "site_id": state.get("site_id"),
                            "report_type": "overview",
                            "report_type_name": "网站数据报告",
                            "summary": summary or {},
                            "charts": {key: chart},
                        }
                        chart_ui_msg = _make_ui_message(
                            "report_charts",
                            chart_ui_id,
                            anchor_msg,
                            {
                                "status": "done",
                                "step": "completed",
                                "message": "图表已生成。",
                                "report": report_snapshot,
                            },
                        )
                        chart_ui_updates.append(chart_ui_msg)
                        if writer:
                            writer({"ui": [chart_ui_msg]})

                        # 兜底：如果流式没有任何 chunk（未触发 _update_analysis），在本图表结束时隐藏“处理中…”
                        if loading_shown and not loading_hidden:
                            loading_hidden = True
                            loading_hide_msg = _make_ui_message(
                                name="chart_analysis_loading",
                                ui_id=loading_ui_id,
                                anchor_msg=anchor_msg,
                                props={
                                    "chart_key": str(tool_name or ""),
                                    "chart_title": loading_title,
                                    "hidden": True,
                                },
                            )
                            if writer:
                                writer({"ui": [loading_hide_msg]})
                    else:
                        # 重复 key：不会进入分析流程，避免“处理中…”卡悬挂
                        if loading_shown:
                            loading_hide_msg = _make_ui_message(
                                name="chart_analysis_loading",
                                ui_id=loading_ui_id,
                                anchor_msg=anchor_msg,
                                props={
                                    "chart_key": str(tool_name or ""),
                                    "chart_title": loading_title,
                                    "hidden": True,
                                },
                            )
                            if writer:
                                writer({"ui": [loading_hide_msg]})
                else:
                    # tool 返回非图表数据：隐藏“处理中…”卡，避免悬挂
                    if loading_shown:
                        loading_hide_msg = _make_ui_message(
                            name="chart_analysis_loading",
                            ui_id=loading_ui_id,
                            anchor_msg=anchor_msg,
                            props={
                                "chart_key": str(tool_name or ""),
                                "chart_title": loading_title,
                                "hidden": True,
                            },
                        )
                        if writer:
                            writer({"ui": [loading_hide_msg]})
            else:
                # norm 不是 dict：隐藏“处理中…”卡，避免悬挂
                if loading_shown:
                    loading_hide_msg = _make_ui_message(
                        name="chart_analysis_loading",
                        ui_id=loading_ui_id,
                        anchor_msg=anchor_msg,
                        props={
                            "chart_key": str(tool_name or ""),
                            "chart_title": loading_title,
                            "hidden": True,
                        },
                    )
                    if writer:
                        writer({"ui": [loading_hide_msg]})

        return (
            f"已完成 {len(unique_plan)} 次数据获取（{', '.join(str(p.get('desc','')) for p in unique_plan)}）",
            charts,
            summary or {},
            raws,
            plan_descs,
            tool_error_message,
            tool_error_is_auth,
        )

    try:
        final_text, charts, summary, raws, plan_descs, tool_error_msg, tool_error_auth = await with_ga_tools(
            site_id=site_id, tenant_id=tenant_id, fn=_run
        )
        
        # ============ GA MCP 返回错误：按类型展示（重新 OAuth / 一般错误）============
        if tool_error_msg:
            display_message = (
                "Google Account authorization has expired. Please re-authenticate via OAuth and try again."
                if tool_error_auth and not tool_error_msg.strip()
                else tool_error_msg
            )
            ui_err = _make_ui_message(
                "report_progress",
                _get_progress_ui_id(state),
                anchor_msg,
                {
                    "status": "error",
                    "step": "auth_expired" if tool_error_auth else "tool_error",
                    "steps": ["AI Planning", "Fetching Data", "Displaying Charts"],
                    "active_step": 2,
                    "message": display_message,
                    "error_message": "TOKEN_REFRESH_FAILED" if tool_error_auth else tool_error_msg,
                },
            )
            return {
                "ui": [ui_fetch, ui_err],
                "tool_result": None,
                "tool_error": display_message,
            }
        
        # ============ 检测工具返回的数据是否为空（charts 为空即认为无有效数据）============
        has_valid_data = bool(charts)
        
        if not has_valid_data:
            ui_no_data = _make_ui_message(
                "report_progress",
                _get_progress_ui_id(state),
                anchor_msg,
                {
                    "status": "error",
                    "step": "no_data",
                    "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
                    "active_step": 2,
                    "message": "Failed to get valid data, possibly due to mismatched query conditions or no records in the data source.",
                    "error_message": "GA data query result is empty",
                },
            )
            return {
                "ui": [ui_fetch, ui_no_data],
                "tool_result": {"final": final_text, "charts": {}, "summary": {}, "raws": raws},
                "tool_error": "GA 数据查询结果为空，请尝试调整查询条件或检查数据源。",
            }
        
        ui_plan = _make_ui_message(
            "report_progress",
            _get_progress_ui_id(state),
            anchor_msg,
            {
                "status": "loading",
                "step": "plan_ready",
                "steps": ["AI 规划调用", "获取数据", "展示图表"],
                "active_step": 2,
                "message": "This run will fetch the following data:\n- " + "\n- ".join([d for d in plan_descs if d]),
            },
        )
        progress_done = _make_ui_message(
            "report_progress",
            _get_progress_ui_id(state),
            anchor_msg,
            {
                "status": "done",
                "step": "completed",
                "steps": ["AI Planning", "Data Fetching", "Rendering Charts"],
                "active_step": 3,
                "message": "Charts generated.",
            },
        )
        progress_hide = _make_ui_message(
            "report_progress",
            _get_progress_ui_id(state),
            anchor_msg,
            {
                "hidden": True,
            },
        )
        writer = get_stream_writer()
        if writer:
            writer({"ui": [progress_done]})
            writer({"ui": [progress_hide]})
        return {
            "ui": [ui_fetch, ui_plan, progress_done, progress_hide, *chart_ui_updates],
            "tool_result": {"final": final_text, "charts": charts, "summary": summary, "raws": raws},
            "tool_error": None,
        }
    except Exception as e:
        # 保留 tool_error（例如 MCP 调用异常），但不把“规划失败”当致命错误
        return {"ui": [ui_fetch], "tool_result": None, "tool_error": str(e)}


async def report_build_evidence(state: ReportState) -> dict[str, Any]:
    """纯代码生成 EvidencePack 与数据质量提示。"""
    evidence = build_evidence_pack(
        tool_result=state.get("tool_result") if isinstance(state.get("tool_result"), dict) else None,
        user_text=state.get("user_text"),
        default_window_days=DEFAULT_DAYS,
    )
    return {
        "evidence_pack": evidence.to_dict(),
        "data_quality": evidence.to_dict().get("data_quality"),
    }


async def report_ask_insights(state: ReportState) -> dict[str, Any]:
    """询问用户是否继续生成洞察（不使用 interrupt；改为自定义 UI + submit 继续）。"""
    # 1) 如果已经有选择结果（来自下一轮 submit 触发的恢复），则跳过
    if state.get("insights_confirmed") is not None:
        return {"report_insights_pending": False}

    anchor_msg = _get_anchor_msg(state)
    ui_id = state.get("report_confirm_insights_ui_id") or f"report_confirm_insights:{getattr(anchor_msg, 'id', '')}"

    ui_confirm = _make_ui_message(
        name="report_confirm_insights",
        ui_id=ui_id,
        anchor_msg=anchor_msg,
        props={
            "message": "Would you like to run a detailed AI analysis on this report data?",
            "hidden": False,
        },
        merge=True,
    )

    writer = get_stream_writer()
    if writer:
        writer(ui_confirm)

    # 2) 标记 pending：等待前端 submit 一条新消息带回 confirmed
    return {
        "ui": [ui_confirm],
        "report_insights_pending": True,
        "report_confirm_insights_ui_id": ui_id,
    }


async def report_generate_insights_start(state: ReportState) -> dict[str, Any]:
    """生成并立即返回 Loading UI 状态。"""
    anchor_msg = _get_anchor_msg(state)

    # Hide confirm card if exists (submit flow)
    confirm_ui_id = state.get("report_confirm_insights_ui_id")
    writer = get_stream_writer()
    if confirm_ui_id and writer:
        writer(
            _make_ui_message(
                name="report_confirm_insights",
                ui_id=confirm_ui_id,
                anchor_msg=anchor_msg,
                props={"hidden": True},
                merge=True,
            )
        )

    # 注意：当前洞察确认已从 interrupt/resume 改为 submit。
    # 在 submit 模式下，不需要补发 charts（补发会导致整表重绘）。
    # 仅保留在非 submit 恢复场景下的 rehydrate 兜底逻辑。
    rehydrate_ui: list[UIMessage] = []
    if state.get("report_resume_mode") != "insights":
        tool_result = state.get("tool_result") if isinstance(state.get("tool_result"), dict) else None
        charts = (tool_result or {}).get("charts") or {}
        if isinstance(charts, dict) and charts:
            summary = (tool_result or {}).get("summary") or {}
            for key, chart in charts.items():
                if not isinstance(chart, dict):
                    continue
                chart_title = chart.get("title", key)
                chart_type = chart.get("chart_type", "chart")
                desc = chart.get("description") or ""

                # 0) 洞察阶段不应出现“正在处理…”：补发隐藏更新清理残留（不补发显示）
                loading_hide = _make_ui_message(
                    name="chart_analysis_loading",
                    ui_id=f"chart_analysis_loading:{getattr(anchor_msg, 'id', '')}:{key}",
                    anchor_msg=anchor_msg,
                    props={
                        "chart_key": key,
                        "chart_title": chart_title,
                        "hidden": True,
                    },
                )
                rehydrate_ui.append(loading_hide)

                # 1) 先补发分析卡
                ui_id = f"chart_analysis:{getattr(anchor_msg, 'id', '')}:{key}"
                ui_msg = _make_ui_message(
                    name="chart_analysis",
                    ui_id=ui_id,
                    anchor_msg=anchor_msg,
                    props={
                        "chart_key": key,
                        "chart_title": chart_title,
                        "chart_type": chart_type,
                        "description": desc,
                    },
                )
                rehydrate_ui.append(ui_msg)

                # 2) 再补发对应图表卡（与正常输出保持“分析 → 图表”的顺序）
                chart_ui_id = f"report_charts:{getattr(anchor_msg, 'id', '')}:{key}"
                report_snapshot = {
                    "site_id": state.get("site_id"),
                    "report_type": "overview",
                    "report_type_name": "网站数据报告",
                    "summary": summary,
                    "charts": {key: chart},
                }
                chart_ui_msg = _make_ui_message(
                    "report_charts",
                    chart_ui_id,
                    anchor_msg,
                    {
                        "status": "done",
                        "step": "completed",
                        "message": "Charts generated.",
                        "report": report_snapshot,
                    },
                )
                rehydrate_ui.append(chart_ui_msg)

    if writer and rehydrate_ui:
        writer({"ui": rehydrate_ui})

    progress_insights_ui = _make_ui_message(
        "report_progress_insights",
        _get_progress_insights_ui_id(state),
        anchor_msg,
        {
            "status": "loading",
            "step": "generating_insights",
            "steps": ["Generate Insights", "Completed"],
            "active_step": 1,
            "message": "Generating insights report...",
        }
    )
    if writer:
        writer(progress_insights_ui)
    return {
        "ui": [*rehydrate_ui, progress_insights_ui],
        "report_resume_mode": None,
        "report_insights_pending": False,
    }


async def report_generate_insights_run(state: ReportState) -> dict[str, Any]:
    """调用洞察 agent：生成 insights/actions，并通过流式输出推送 UI 更新。"""
    
    def _map_todos_for_ui(todos: Any) -> list[dict[str, Any]] | None:
        if not isinstance(todos, list) or not todos:
            return None
        mapped: list[dict[str, Any]] = []
        for i, t in enumerate(todos):
            if not isinstance(t, dict):
                continue
            content = str(t.get("content") or "").strip()
            status = str(t.get("status") or "").strip()
            if not content:
                continue
            mapped.append(
                {
                    "id": f"todo-{i+1}",
                    "title": content,
                    "description": f"Status: {status}" if status else None,
                }
            )
        return mapped or None

    anchor_msg = _get_anchor_msg(state)
    insights_ui_id = _get_insights_ui_id(state)
    writer = get_stream_writer()
    
    async def on_streaming_update(partial_report: dict[str, Any]) -> None:
        """Push incremental UI updates as tokens stream in."""
        if not writer:
            return
        
        # Build partial insights report for UI
        streaming_report: dict[str, Any] = {
            "site_id": state.get("site_id"),
            "report_type": "overview",
            "report_type_name": "Site Data Report",
        }
        if partial_report.get("insights"):
            streaming_report["insights"] = partial_report["insights"]
        if partial_report.get("actions"):
            streaming_report["actions"] = partial_report["actions"]
        if partial_report.get("todos"):
            streaming_report["todos"] = _map_todos_for_ui(partial_report["todos"])
        
        # Determine if still streaming
        is_streaming = partial_report.get("insights", {}).get("_streaming", False)
        
        ui_msg = _make_ui_message(
            "report_insights",
            insights_ui_id,
            anchor_msg,
            {
                "status": "loading" if is_streaming else "done",
                "step": "streaming" if is_streaming else "completed",
                "message": "Generating insights..." if is_streaming else "Insights generated.",
                "report": streaming_report,
            },
        )
        writer(ui_msg)

    evidence_pack = state.get("evidence_pack") or {}
    try:
        out = await generate_report_insights_streaming(
            evidence_pack=evidence_pack, 
            user_text=state.get("user_text"),
            on_update=on_streaming_update,
        )
        ui_todos = _map_todos_for_ui(out.get("todos"))

        return {
            "insights": out.get("insights"),
            "actions": out.get("actions"),
            "todos": ui_todos,
            "trace": out.get("trace"),
            "step_outputs": out.get("step_outputs"),
        }
    except Exception as e:
        # 洞察失败不影响报表基础数据展示
        return {
            "insights": None,
            "actions": None,
            "todos": None,
            "error": f"generate_insights_failed: {e}",
        }


async def report_finalize(state: ReportState) -> dict[str, Any]:
    """最终渲染：置为 done，并输出完整 report_data。"""
    ui_id = _get_progress_ui_id(state)
    anchor_msg = _get_anchor_msg(state)

    tool_error = state.get("tool_error")
    if tool_error:
        return {"error": tool_error}

    insights_report: dict[str, Any] = {
        "site_id": state.get("site_id"),
        "report_type": "overview",
        "report_type_name": "Site Data Report",
    }
    if state.get("data_quality"):
        insights_report["data_quality"] = state.get("data_quality")
    if state.get("insights"):
        insights_report["insights"] = state.get("insights")
    if state.get("actions"):
        insights_report["actions"] = state.get("actions")
    if state.get("todos"):
        insights_report["todos"] = state.get("todos")
    if state.get("trace"):
        insights_report["trace"] = state.get("trace")
    if state.get("step_outputs"):
        insights_report["step_outputs"] = state.get("step_outputs")
    
    ui_updates = state.get("ui") or []

    # 兜底：如果存在确认卡，finalize 时隐藏（用户选择“不需要”也要收起）
    confirm_ui_id = state.get("report_confirm_insights_ui_id")
    if confirm_ui_id:
        ui_updates.append(
            _make_ui_message(
                name="report_confirm_insights",
                ui_id=confirm_ui_id,
                anchor_msg=anchor_msg,
                props={"hidden": True},
                merge=True,
            )
        )

    # 兜底：洞察结束时强制隐藏所有 chart_analysis_loading（防止历史 state 残留导致误显示）
    tool_result = state.get("tool_result") if isinstance(state.get("tool_result"), dict) else None
    charts = (tool_result or {}).get("charts") or {}
    if isinstance(charts, dict) and charts:
        for key, chart in charts.items():
            if not isinstance(chart, dict):
                continue
            chart_title = chart.get("title", key)
            ui_updates.append(
                _make_ui_message(
                    name="chart_analysis_loading",
                    ui_id=f"chart_analysis_loading:{getattr(anchor_msg, 'id', '')}:{key}",
                    anchor_msg=anchor_msg,
                    props={
                        "chart_key": key,
                        "chart_title": chart_title,
                        "hidden": True,
                    },
                )
            )
    
    insights_done = _make_ui_message(
        "report_insights",
        _get_insights_ui_id(state),
        anchor_msg,
        {
            "status": "done",
            "step": "completed",
            "message": "Insights generated.",
            "report": insights_report,
        },
        merge=True,
    )
    ui_updates.append(insights_done)

    progress_insights_ui = _make_ui_message(
        "report_progress_insights",
        _get_progress_insights_ui_id(state),
        anchor_msg,
        {
            "status": "done",
            "step": "completed",
            "message": "Insights analysis completed.",
        }
    )
    ui_updates.append(progress_insights_ui)

    return {
        "ui": ui_updates,
        "report_resume_mode": None,
        "report_insights_pending": False,
    }


async def report_capability_response(state: ReportState) -> dict[str, Any]:
    """能力询问响应：基于工具列表生成用户友好的功能说明。"""
    ui_id = _get_progress_ui_id(state)
    anchor_msg = _get_anchor_msg(state)
    
    tool_specs = state.get("tool_specs") or []
    user_text = state.get("user_text") or ""
    
    # 构建工具摘要供 LLM 参考
    tool_summaries = []
    for spec in tool_specs:
        tool_summaries.append(f"- {spec.name}: {spec.description}")
    tools_info = "\n".join(tool_summaries) if tool_summaries else "暂无可用工具"
    
    # 使用 LLM 生成用户友好的回复
    try:
        response_prompt = f"""You are a Google Analytics Data Report Assistant. The user wants to know what reports and data query capabilities you can provide.

Based on the available tool list below, reply to the user in friendly, concise English. Do not list technical details (like parameter schema), but describe what data can be queried in business language.

Available Tools:
{tools_info}

User Question: {user_text}

Please reply in markdown format, including:
1. A short welcome message
2. Categorized list of main capabilities (e.g., Traffic Analysis, User Behavior, Real-time Monitoring, etc.)
3. Provide 2-3 example questions to guide the user

Reply:"""
        
        resp = await llm_nostream.ainvoke(response_prompt, config={"callbacks": []})
        raw_content = getattr(resp, "content", str(resp)).strip()
        
        # 去除可能存在的 markdown 代码块标记
        capability_response = re.sub(r"^```(markdown)?\s*", "", raw_content, flags=re.IGNORECASE|re.MULTILINE).strip()
        capability_response = re.sub(r"\s*```$", "", capability_response, flags=re.MULTILINE).strip()
        
    except Exception as e:
        logger.warning(f"[Report] Capability response generation failed: {e}")
        capability_response = f"I can help you query the following Google Analytics data:\n\n{tools_info}\n\nYou can ask me questions like \"traffic trends for the last 7 days\" or \"device distribution\"."
    
    # 创建一个完成的 AI 消息
    response_msg = AIMessage(content=capability_response)
    
    # 更新 UI 为完成状态
    ui_done = _make_ui_message(
        "report_progress",
        ui_id,
        anchor_msg,
        {
            "status": "done",
            "step": "completed",
            "steps": ["Completed"],
            "active_step": 3,
            "message": "Question answered.",
        },
    )
    
    return {
        "messages": [response_msg],
        "ui": [ui_done],
    }
