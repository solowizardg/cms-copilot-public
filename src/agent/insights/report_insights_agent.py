"""Report 洞察（plan→execute）。

说明：
- 该模块只负责对 EvidencePack 做洞察：先生成分析计划（plan），再用确定性代码执行（execute）
  产出 step_outputs，最后基于 step_outputs 生成 insights/actions。
- 不使用 ReAct 循环，避免死循环与 recursion_limit 问题。
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agent.utils.llm import llm_nostream, llm_nano
from agent.prompts.report import REPORT_INTERPRETER_PROMPT


_PLANNER = None
_SUMMARIZER = None


class HypothesisModel(BaseModel):
    text: str = Field(..., description="Hypothesis to be verified")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence level")
    next_step: str = Field(..., description="How to verify this hypothesis")


class SuccessMetricModel(BaseModel):
    metric: str
    window_days: int = 7
    target: str | None = None


class ActionModel(BaseModel):
    id: str
    title: str
    why: str | None = None
    effort: Literal["low", "medium", "high"] = "medium"
    impact: Literal["low", "medium", "high"] = "medium"
    success_metric: SuccessMetricModel | None = None


class InsightsModel(BaseModel):
    one_liner: str
    evidence: list[str] = Field(default_factory=list)
    hypotheses: list[HypothesisModel] = Field(default_factory=list)


class TraceModel(BaseModel):
    todo_summary: str = Field(..., description="One-line summary of the analysis steps taken")
    used_todos: list[str] = Field(default_factory=list, description="Referenced todo items in order")


class StepOutputModel(BaseModel):
    step: str = Field(..., description="Analysis step title")
    result: str = Field(..., description="Step output with key metrics/conclusions")
    evidence_ref: str | None = Field(
        default=None, description="Evidence source reference (e.g., summary / charts.device_stats)"
    )

class PlanStepModel(BaseModel):
    title: str = Field(..., description="Analysis step title (short phrase)")
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="EvidencePack field paths for this step (e.g., summary / charts.device_stats / data_quality)",
    )
    output_expectation: str = Field(
        ..., description="Expected output type (e.g., percentage, Top3, trend summary, data quality notes)"
    )


class AnalysisPlanModel(BaseModel):
    steps: list[PlanStepModel] = Field(..., description="Analysis steps (1-4 items)")


class InsightsOutputModel(BaseModel):
    insights: InsightsModel
    actions: list[ActionModel] = Field(default_factory=list)
    # trace/step_outputs 由执行器生成，这里仅保留最终洞察与建议动作


def _get_planner():
    """生成分析计划（plan）。"""
    global _PLANNER
    if _PLANNER is None:
        _PLANNER = llm_nostream.with_structured_output(AnalysisPlanModel)
    return _PLANNER


def _get_summarizer():
    """基于 step_outputs 生成洞察/建议（summarize）。"""
    global _SUMMARIZER
    if _SUMMARIZER is None:
        _SUMMARIZER = llm_nostream.with_structured_output(InsightsOutputModel)
    return _SUMMARIZER

def _fmt_int(v: Any) -> str:
    try:
        return f"{int(v):,}"
    except Exception:
        return str(v)


def _fmt_pct(v: float) -> str:
    try:
        return f"{v*100:.1f}%"
    except Exception:
        return str(v)


def _extract_pie_distribution(chart: dict[str, Any]) -> tuple[int, list[tuple[str, int, float]]]:
    """从 pie chart data 提取总数与占比。"""
    data = chart.get("data") or []
    items: list[tuple[str, int]] = []
    total = 0
    for r in data:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or r.get("label") or "")
        val = r.get("value")
        try:
            iv = int(val)
        except Exception:
            continue
        if not name:
            name = "—"
        items.append((name, iv))
        total += iv
    dist: list[tuple[str, int, float]] = []
    if total > 0:
        for name, iv in sorted(items, key=lambda x: x[1], reverse=True)[:5]:
            dist.append((name, iv, iv / total))
    return total, dist


def execute_plan(
    *,
    evidence_pack: dict[str, Any],
    plan: AnalysisPlanModel,
) -> list[dict[str, Any]]:
    """Deterministic execution: generate step_outputs from EvidencePack based on plan."""
    out: list[dict[str, Any]] = []
    summary = (evidence_pack or {}).get("summary") or {}
    charts = (evidence_pack or {}).get("charts") or {}
    dq = (evidence_pack or {}).get("data_quality") or {}

    for step in plan.steps:
        title = step.title
        title_l = title.lower()
        result_lines: list[str] = []
        evidence_ref: str | None = None

        # Core metrics
        if ("core" in title_l) or ("metric" in title_l) or ("summary" in " ".join(step.evidence_refs).lower()):
            tv = summary.get("total_visits")
            tu = summary.get("total_unique_visitors")
            tpv = summary.get("total_page_views")
            pps = summary.get("pages_per_session")
            if tv is not None:
                result_lines.append(f"Total sessions: {_fmt_int(tv)}")
            if tu is not None:
                result_lines.append(f"Active users: {_fmt_int(tu)}")
            if tpv is not None:
                result_lines.append(f"Page views: {_fmt_int(tpv)}")
            if pps is not None:
                result_lines.append(f"Pages per session: {pps}")
            evidence_ref = "summary"

        # Device distribution
        if ("device" in title_l) or ("charts.device" in " ".join(step.evidence_refs).lower()):
            chart = charts.get("device_stats") or {}
            total, dist = _extract_pie_distribution(chart) if isinstance(chart, dict) else (0, [])
            if total and dist:
                parts = [f"{name} {_fmt_int(val)} ({_fmt_pct(p)})" for name, val, p in dist]
                result_lines.append(f"Device total: {_fmt_int(total)}; Top: " + ", ".join(parts))
            evidence_ref = "charts.device_stats"

        # Traffic sources
        if ("source" in title_l) or ("channel" in title_l) or ("traffic" in title_l) or ("charts.traffic" in " ".join(step.evidence_refs).lower()):
            chart = charts.get("traffic_sources") or {}
            total, dist = _extract_pie_distribution(chart) if isinstance(chart, dict) else (0, [])
            if total and dist:
                parts = [f"{name} {_fmt_int(val)} ({_fmt_pct(p)})" for name, val, p in dist]
                result_lines.append(f"Traffic total: {_fmt_int(total)}; Top: " + ", ".join(parts))
            evidence_ref = "charts.traffic_sources"

        # Trend analysis
        if ("trend" in title_l) or ("charts.daily" in " ".join(step.evidence_refs).lower()):
            chart = charts.get("daily_visits") or {}
            data = (chart.get("data") or []) if isinstance(chart, dict) else []
            if isinstance(data, list) and data:
                first = data[0]
                last = data[-1]
                xk = chart.get("x_key") or "date"
                y_keys = chart.get("y_keys") or []
                if isinstance(first, dict) and isinstance(last, dict) and y_keys:
                    y0 = y_keys[0]
                    try:
                        v0 = float(first.get(y0))
                        v1 = float(last.get(y0))
                        delta = v1 - v0
                        result_lines.append(
                            f"{y0} from {first.get(xk)} at {int(v0)} changed to {last.get(xk)} at {int(v1)} (Δ {int(delta):+d})"
                        )
                    except Exception:
                        pass
            evidence_ref = "charts.daily_visits"

        # Data quality
        if ("quality" in title_l) or ("data_quality" in " ".join(step.evidence_refs).lower()):
            notes = dq.get("notes") or []
            warns = dq.get("warnings") or []
            if warns:
                result_lines.append("Warnings: " + "; ".join([str(w) for w in warns[:3]]))
            if notes:
                result_lines.append("Notes: " + "; ".join([str(n) for n in notes[:3]]))
            evidence_ref = "data_quality"

        if not result_lines:
            # No matching rule - provide minimal traceable output
            result_lines.append(f"(No deterministic rule implemented for: {step.output_expectation})")
            evidence_ref = step.evidence_refs[0] if step.evidence_refs else None

        out.append(
            {
                "step": title,
                "result": "\n".join(result_lines),
                "evidence_ref": evidence_ref,
            }
        )

    return out


async def generate_report_insights(
    *,
    evidence_pack: dict[str, Any],
    user_text: str | None = None,
) -> dict[str, Any]:
    """plan→execute: Generate plan, execute to get step_outputs, then summarize into insights/actions."""
    charts_keys = sorted(list(((evidence_pack or {}).get("charts") or {}).keys()))
    planner = _get_planner()
    summarizer = _get_summarizer()

    plan_prompt = (
        "You are a GA report analysis planner.\n"
        "Based on the available fields in EvidencePack, generate 1-4 analysis steps (steps).\n"
        "Each step should specify: title, evidence_refs to reference, and expected output.\n"
        "Do not invent fields that don't exist.\n"
        f"Available charts keys: {charts_keys}\n"
        f"User query (optional): {user_text or ''}\n"
        "EvidencePack (JSON):\n"
        + json.dumps(evidence_pack, ensure_ascii=False)
    )
    plan: AnalysisPlanModel = await planner.ainvoke(
        [HumanMessage(content=plan_prompt)], config={"callbacks": []}
    )

    step_outputs = execute_plan(evidence_pack=evidence_pack, plan=plan)

    summary_prompt = (
        "You are a GA report insights assistant.\n"
        "Based ONLY on the step_outputs provided, generate final insights and recommended actions.\n"
        "Do NOT introduce any facts not present in step_outputs.\n"
        "Output: insights (one_liner/evidence/hypotheses) and actions (1-3 items).\n"
        "All output must be in English.\n"
        "step_outputs (JSON):\n"
        + json.dumps(step_outputs, ensure_ascii=False)
    )
    final: InsightsOutputModel = await summarizer.ainvoke(
        [HumanMessage(content=summary_prompt)], config={"callbacks": []}
    )

    todos = [{"content": s.title, "status": "completed"} for s in plan.steps]
    trace = {
        "todo_summary": "Analysis completed following planned steps.",
        "used_todos": [s.title for s in plan.steps],
    }

    return {
        "plan": plan.model_dump(),
        "insights": final.insights.model_dump(),
        "actions": [a.model_dump() for a in final.actions],
        "trace": trace,
        "step_outputs": step_outputs,
        "todos": todos,
    }


from typing import Callable, Awaitable
from agent.utils.llm import llm_nano, llm_nostream


async def generate_report_insights_streaming(
    *,
    evidence_pack: dict[str, Any],
    user_text: str | None = None,
    on_update: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    """
    Streaming version of generate_report_insights.
    
    Calls on_update callback with partial report data as content is generated:
    - First streams the one_liner text token by token
    - Then generates structured actions/hypotheses
    """
    charts_keys = sorted(list(((evidence_pack or {}).get("charts") or {}).keys()))
    planner = _get_planner()

    # Step 1: Generate plan (structured, non-streaming)
    plan_prompt = (
        "You are a GA report analysis planner.\n"
        "Based on the available fields in EvidencePack, generate 1-4 analysis steps (steps).\n"
        "Each step should specify: title, evidence_refs to reference, and expected output.\n"
        "Do not invent fields that don't exist.\n"
        f"Available charts keys: {charts_keys}\n"
        f"User query (optional): {user_text or ''}\n"
        "EvidencePack (JSON):\n"
        + json.dumps(evidence_pack, ensure_ascii=False)
    )
    plan: AnalysisPlanModel = await planner.ainvoke(
        [HumanMessage(content=plan_prompt)], config={"callbacks": []}
    )

    step_outputs = execute_plan(evidence_pack=evidence_pack, plan=plan)
    
    # Step 2: Stream the one_liner summary
    one_liner_prompt = (
        "You are a GA report insights assistant.\n"
        "Based ONLY on the step_outputs provided, write a single concise sentence summarizing the key insight.\n"
        "This should be the most important finding from the data analysis.\n"
        "Do NOT use any markdown formatting. Just output a plain sentence in English.\n"
        "step_outputs (JSON):\n"
        + json.dumps(step_outputs, ensure_ascii=False)
    )
    
    one_liner_parts: list[str] = []
    try:
        async for chunk in llm_nano.astream(one_liner_prompt, config={"callbacks": []}):
            piece = getattr(chunk, "content", chunk)
            if not isinstance(piece, str) or not piece:
                continue
            one_liner_parts.append(piece)
            # Push partial update with streaming one_liner
            if on_update:
                partial_report = {
                    "insights": {
                        "one_liner": "".join(one_liner_parts),
                        "evidence": [],
                        "hypotheses": [],
                        "_streaming": True,
                    },
                    "actions": [],
                    "todos": [],
                }
                await on_update(partial_report)
    except Exception as e:
        print(f"[ReportInsights] Streaming one_liner failed: {e}")
    
    one_liner = "".join(one_liner_parts).strip()
    
    # Step 3: Generate structured insights and actions
    # Step 3: Generate structured insights and actions
    raws = (evidence_pack or {}).get("raws") or []
    
    # 将 raws 转换为 prompt 要求的 tool/request/response 格式
    datasets_json_str = "[]"
    if raws:
        datasets = []
        for r in raws:
            datasets.append({
                "tool": r.get("tool"),
                "request": r.get("args"),
                "response": r.get("result")
            })
        datasets_json_str = json.dumps(datasets, ensure_ascii=False)

    summary_prompt = (
        f"{REPORT_INTERPRETER_PROMPT}\n"
        "Input Datasets (JSON):\n"
        + datasets_json_str
    )
    
    # summarizer = _get_summarizer()
    # 使用 Gemini Flash Thinking 模型 (Directly instantiated as per requirement)
    llm_gemini = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_FLASH_MODEL", "gemini-3-flash-preview"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        thinking_level=os.getenv("REPORT_INSIGHTS_LEVEL"),
        temperature=0,
    )
    summarizer = llm_gemini.with_structured_output(InsightsOutputModel)

    final: InsightsOutputModel = await summarizer.ainvoke(
        [HumanMessage(content=summary_prompt)], config={"callbacks": []}
    )
    
    # Merge one_liner with structured output
    insights_dict = final.insights.model_dump()
    insights_dict["one_liner"] = one_liner if one_liner else insights_dict.get("one_liner", "")
    
    todos = [{"content": s.title, "status": "completed"} for s in plan.steps]
    trace = {
        "todo_summary": "Analysis completed following planned steps.",
        "used_todos": [s.title for s in plan.steps],
    }
    
    result = {
        "plan": plan.model_dump(),
        "insights": insights_dict,
        "actions": [a.model_dump() for a in final.actions],
        "trace": trace,
        "step_outputs": step_outputs,
        "todos": todos,
    }
    
    # Final update with complete data
    if on_update:
        await on_update(result)
    
    return result
