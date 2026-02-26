"""路由节点模块。

意图识别和路由分发。
"""

import time
import uuid
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message

from agent.state import CopilotState
from agent.utils.helpers import (
    find_ai_message_by_id,
    latest_user_message,
    message_text,
)
from agent.utils.llm import llm_nano_nostream


async def start_intent_ui(state: CopilotState) -> dict[str, Any]:
    """先把"正在识别意图"的卡片显示出来。"""
    # 支持 AI 模拟的消息触发（如 SEO Publish）
    user_msg = state["messages"][-1] if state.get("messages") else latest_user_message(state)
    user_text = message_text(user_msg)

    started_at = time.monotonic()

    # 关键：先写入锚点 AIMessage（生成 message_id），前端才能立刻挂载/渲染 UI
    ui_anchor_msg = AIMessage(id=str(uuid.uuid4()), content="")
    ui_props = {
        "status": "thinking",
        "user_text": user_text,
        "steps": [
            "解析用户输入",
            "调用意图分类模型（gpt-4.1-nano）",
            "映射到下游路由（rag / article / shortcut / report / intro）",
        ],
        "active_step": 1,
    }
    if state.get("direct_intent") == "article_task":
        ui_props.update(
            {
                "main_title": "Analyzing article requirements...",
                "rag_message": "Checking parameters...",
                "rag_status": "running",
                "hidden": False,
            }
        )

    ui_msg_start = push_ui_message(
        "intent_router",
        ui_props,
        message=ui_anchor_msg,
    )

    return {
        "messages": [ui_anchor_msg],
        "ui": [ui_msg_start],
        "intent_ui_id": ui_msg_start["id"],
        "intent_anchor_id": ui_anchor_msg.id,
        "intent_started_at": started_at,
    }



def _classify_intent_fallback(user_text: str) -> str:
    """LLM 失败时的基于关键词的兜底分类规则。"""
    user_lower = user_text.lower()
    
    if any(k in user_text for k in ["文章", "写"]):
        return "article_task"
        
    if any(k in user_text for k in ["草稿", "新建"]):
        return "shortcut"
        
    intro_keywords = [
        "你能做什么", "你是谁", "介绍", "帮助", "你好",
        "what can you do", "who are you", "introduce", "hello", "hi", "help"
    ]
    if any(k in user_lower for k in intro_keywords):
        return "introduction"
        
    if "seo" in user_lower or "优化" in user_text:
        return "seo_planning"
        
    report_keywords = ["报告", "统计", "访问量", "流量", "数据"]
    if any(k in user_text for k in report_keywords):
        return "site_report"
        
    return "rag"


async def route_intent(state: CopilotState) -> dict[str, Any]:
    """使用 LLM 对最后一条用户消息做意图分类。"""
    # 支持 AI 模拟的消息触发（如 SEO Publish）
    # 查找触发消息：从后向前遍历，跳过 UI 锚点（空的 AIMessage）
    user_msg = latest_user_message(state)
    user_text = message_text(user_msg)

    # 注入 Direct Intent 作为提示，不再强制跳过 LLM，而是作为上下文参考
    if state.get("direct_intent"):
        user_text += f"\n(System Hint: User explicitly triggered intent '{state.get('direct_intent')}')"

    # UI 绑定到 start_intent_ui 写入的锚点 AIMessage
    ui_anchor_msg = find_ai_message_by_id(state, state.get("intent_anchor_id"))
    intent_ui_id = state.get("intent_ui_id")
    started_at = state.get("intent_started_at")
    if ui_anchor_msg is None or not intent_ui_id:
        # 兜底：如果没有先经过 start_intent_ui，也能正常渲染
        ui_anchor_msg = ui_anchor_msg or AIMessage(id=str(uuid.uuid4()), content="")
        ui_msg_start = push_ui_message(
            "intent_router",
            {
                "status": "thinking",
                "user_text": user_text,
                "steps": [
                    "解析用户输入",
                    "调用意图分类模型（gpt-4.1-nano）",
                    "映射到下游路由（rag / article / shortcut / report / intro）",
                ],
                "active_step": 1,
            },
            message=ui_anchor_msg,
        )
        intent_ui_id = ui_msg_start["id"]
        started_at = started_at or time.monotonic()

    system_prompt = """You are an intent classifier for CMS Copilot.
Classify the user input into ONE of these six categories.

## Categories

1. **article_task**: User wants to CREATE/GENERATE content (articles, blog posts, news, marketing copy).
   - Trigger: Requests to write/generate content, often with parameters like topic, keywords, or outline.
   
2. **shortcut**: User wants to perform a backend CMS operation (change settings, update logo, create drafts).
   - Trigger: Action verbs (change, update, create, set) + CMS objects (logo, title, settings, draft).

3. **seo_planning**: User asks about SEO strategy, weekly plans, or optimization suggestions.
   - Trigger: Requests for SEO analysis, weekly tasks, or optimization advice (NOT writing new content).

4. **site_report**: User asks about analytics, traffic statistics, or data reports.
   - Trigger: Requests for reports, statistics, traffic data, or visitor analytics.

5. **introduction**: User is greeting, asking about capabilities, or requesting self-introduction.
   - Trigger: Greetings (Hi, Hello) or questions about what the AI is or what it can do.

6. **rag**: User asks about usage instructions, configuration, how-to guides, or general knowledge questions.
   - Trigger: Questions about "how to" use the system, documentation, or conceptual questions.

## Few-Shot Examples

Input: "Help me write a blog post about AI trends"
Output: article_task

Input: "Generate an article with parameters: Topic=SEO, Keywords=google rankings"
Output: article_task

Input: "Create a marketing copy for our new product"
Output: article_task

Input: "Change the site title to 'Best Tech News'"
Output: shortcut

Input: "Update the company logo"
Output: shortcut

Input: "Create a new draft post"
Output: shortcut

Input: "What are my SEO tasks for this week?"
Output: seo_planning

Input: "Weekly plan"
Output: seo_planning

Input: "Analyze my site's SEO performance"
Output: seo_planning

Input: "Give me an SEO optimization strategy"
Output: seo_planning

Input: "Show me the traffic report for last month"
Output: site_report

Input: "How many visitors did we have yesterday?"
Output: site_report

Input: "Display the detailed analytics"
Output: site_report

Input: "Hi there"
Output: introduction

Input: "What can you do?"
Output: introduction

Input: "Who are you?"
Output: introduction

Input: "Hello"
Output: introduction

Input: "How do I configure the footer menu?"
Output: rag

Input: "Where can I find the API keys?"
Output: rag

Input: "How to use the text editor?"
Output: rag

## Instructions

- Output ONLY one label: article_task, shortcut, seo_planning, site_report, introduction, or rag.
- If uncertain, prefer 'rag' as the default fallback.
- Simple greetings (Hi, Hello) WITHOUT additional context should be classified as 'introduction'.
"""

    user_prompt = f"""User input: {user_text}
Output:"""

    intent_label = "rag"
    raw_model_output = ""

    try:
        resp = await llm_nano_nostream.bind(temperature=0).ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],config={"callbacks": []})
        raw_model_output = getattr(resp, "content", str(resp)).strip()
        label = raw_model_output.lower()

        if "article_task" in label or label == "article":
            intent_label = "article_task"
        elif "shortcut" in label:
            intent_label = "shortcut"
        elif "seo_planning" in label:
            intent_label = "seo_planning"
        elif "site_report" in label or "report" in label:
            intent_label = "site_report"
        elif "introduction" in label:
            intent_label = "introduction"
        elif "rag" in label:
            intent_label = "rag"
        else:
            # LLM 输出异常时的兜底规则
            intent_label = _classify_intent_fallback(user_text)
    except Exception:
        # LLM 调用失败时回退到简单规则
        intent_label = _classify_intent_fallback(user_text)


    # 将 intent 标签映射到实际的下游路由节点
    if intent_label == "article_task":
        route_to = "article"
    elif intent_label == "shortcut":
        route_to = "shortcut"
    elif intent_label == "seo_planning":
        route_to = "seo"
    elif intent_label == "site_report":
        route_to = "report"
    elif intent_label == "introduction":
        route_to = "introduction"
    else:
        route_to = "rag"

    elapsed_s: float | None = None
    if started_at is not None:
        elapsed_s = max(0.0, time.monotonic() - started_at)

    ui_msg_done = None
    if state.get("direct_intent") != "article_task":
        ui_msg_done = push_ui_message(
            "intent_router",
            {
                "status": "done",
                "user_text": user_text,
                "intent": intent_label,
                "route": route_to,
                "raw": raw_model_output,
                "elapsed_s": elapsed_s,
                "steps": [
                    "解析用户输入",
                    "调用意图分类模型（gpt-4.1-nano）",
                    "映射到下游路由（rag / article / shortcut / report / intro）",
                    f"完成：intent={intent_label} → route={route_to}",
                ],
                "active_step": 4,
            },
            id=intent_ui_id,
            message=ui_anchor_msg,
            merge=True,
        )

    return {
        "intent": intent_label,
        "ui": [ui_msg_done] if ui_msg_done is not None else [],
        "intent_anchor_id": getattr(ui_anchor_msg, "id", None),
        "direct_intent": None,  # 消费完成后清除
    }
