import sys
from types import SimpleNamespace
from unittest.mock import patch


def main() -> int:
    sys.path.append("src")
    import asyncio
    from agent.nodes import shortcut as sc

    class FakeTool:
        def __init__(self, name: str, description: str = ""):
            self.name = name
            self.description = description

    async def run_case(decision_value: str):
        fake_tools = [
            FakeTool("site_setting_update", "更新站点设置"),
            FakeTool("site_setting_get", "获取站点设置"),
        ]

        plan_json = (
            '{"steps":['
            '{"title":"更新公司名称","tool":"site_setting_update","args":{"company_name":"你好"}},'
            '{"title":"读取确认","tool":"site_setting_get","args":{}}'
            "]}"
        )

        async def fake_get_mcp_tools(*args, **kwargs):
            return fake_tools

        class FakeLLM:
            async def ainvoke(self, prompt, config=None):
                return SimpleNamespace(content=plan_json)

        async def fake_call_mcp_tool(*args, **kwargs):
            return {"success": True, "message": "ok", "data": {"echo": kwargs}}

        def fake_interrupt(payload):
            return decision_value

        def fake_push_ui_message(name, props, id=None, message=None, merge=True):
            # mimic langgraph UI message shape enough for finalize to read status
            return {"type": "ui", "name": name, "id": id or f"{name}:fake", "props": props, "metadata": {"merge": merge}}

        base_state = {
            "messages": [],
            "ui": [],
            "tenant_id": "t1",
            "site_id": "s1",
            "user_text": "把公司名称设置成你好，并检查",
            "ui_anchor_id": None,
            "ui_id": None,
        }

        with patch.object(sc, "get_mcp_tools", fake_get_mcp_tools), patch.object(
            sc, "call_mcp_tool", fake_call_mcp_tool
        ), patch.object(sc, "interrupt", fake_interrupt), patch.object(
            sc.llm_nostream, "_getter", lambda: FakeLLM()
        ), patch.object(
            sc, "get_stream_writer", lambda: None
        ), patch.object(
            sc, "push_ui_message", fake_push_ui_message
        ):
            out = await sc.shortcut_init(base_state)
            st = {**base_state, **out}
            st.update(await sc.shortcut_plan(st))

            # step 1
            st.update(await sc.shortcut_prepare_step(st))
            st.update(await sc.shortcut_confirm_step(st))
            st.update(await sc.shortcut_execute_step(st))

            # step 2 (may not happen if cancel)
            if not st.get("cancelled") and not st.get("error"):
                st.update(await sc.shortcut_prepare_step(st))
                st.update(await sc.shortcut_confirm_step(st))
                st.update(await sc.shortcut_execute_step(st))

            fin = await sc.shortcut_finalize(st)
            return st, fin

    for name, decision in [("approve", "approve"), ("skip", "skip"), ("cancel", "cancel")]:
        st, fin = asyncio.run(run_case(decision))
        status = (fin.get("ui") or [{}])[0].get("props", {}).get("status")
        print(
            "CASE",
            name,
            "cancelled=",
            st.get("cancelled"),
            "error=",
            st.get("error"),
            "outputs=",
            len(st.get("step_outputs") or []),
            "final_status=",
            status,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

