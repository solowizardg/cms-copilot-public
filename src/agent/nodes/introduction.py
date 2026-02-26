"""自我介绍节点模块。

当用户询问"你能做什么"等问题时，返回 CMS Copilot 的能力介绍。
"""

from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message

from agent.state import CopilotState
from agent.utils.helpers import find_ai_message_by_id


INTRODUCTION_TEXT = """Hello! I'm **Webhub Copilot**, your intelligent content management assistant.

Here's what I can help you with:

### Content Creation (Article)
- Generate high-quality articles based on your topic, keywords, target audience, and other parameters
- Support multiple content formats: blog posts, press releases, marketing copy, etc.
- Optimize titles, meta descriptions, and content structure according to SEO requirements

### SEO Planning
- Create weekly SEO plans and task schedules
- Analyze keyword strategies and provide optimization suggestions
- Deliver website SEO improvement recommendations

### Site Reports
- View website traffic statistics and visitor data
- Generate data analysis reports
- Monitor website performance metrics

### Quick Actions (Shortcut)
- Modify site configurations (e.g., company name, logo, etc.)
- Execute backend operations quickly
- Batch process common tasks

### Help & Documentation (RAG)
- Answer questions about the CMS system
- Provide configuration and operation guides
- Query help documentation

---

**Try these commands:**
- `Write an article about AI`
- `Give me this week's SEO task plan`
- `Show the site traffic report`
- `Change the company name to xxx`

What can I help you with today?"""


async def handle_introduction(state: CopilotState) -> dict[str, Any]:
    """处理自我介绍请求，返回能力介绍消息。"""

    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)

    ui_updates: list[dict[str, Any]] = []
    if intent_ui_id and intent_anchor_msg is not None:
        ui_updates.append(
            push_ui_message(
                "intent_router",
                {"status": "done", "hidden": True},
                id=intent_ui_id,
                message=intent_anchor_msg,
                merge=True,
            )
        )

    payload: dict[str, Any] = {
        "messages": [AIMessage(content=INTRODUCTION_TEXT)],
        "intent_ui_id": None,
        "intent_anchor_id": None,
    }
    if ui_updates:
        payload["ui"] = ui_updates
    return payload
