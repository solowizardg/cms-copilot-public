import { React, useStreamContext } from "../../hooks";
import type { SEOPlannerProps, WeeklyTask } from "../../types";
import { Spinner } from "../common/Spinner";
import "../../styles.css";

export const SEOPlannerCard: React.FC<SEOPlannerProps> = (props) => {
    const streamCtx = useStreamContext?.() as any;
    const status = props.status || "loading";
    const steps = props.steps || [];
    const activeStep = props.active_step || 1;
    const tasks = props.weekly_tasks?.tasks || [];
    const meta = props.weekly_tasks?.meta;

    // 发送消息到聊天框
    const sendMessage = (text: string) => {
        const win = window as any;
        const globalFns = ["__LANGGRAPH_SEND_MESSAGE__", "__LANGGRAPH_SEND__", "sendMessage", "sendChatMessage"];
        for (const fn of globalFns) {
            if (typeof win[fn] === "function") { try { win[fn](text); return; } catch { } }
        }
        window.dispatchEvent(new CustomEvent("langgraph:send", { detail: { text } }));
        const selectors = ['textarea', 'input[type="text"]'];
        for (const sel of selectors) {
            const input = document.querySelector(sel) as HTMLInputElement | HTMLTextAreaElement | null;
            if (!input) continue;
            const proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
            if (setter) setter.call(input, text); else input.value = text;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            setTimeout(() => {
                const form = input.closest("form");
                const submitBtn = form?.querySelector('button[type="submit"]') || form?.querySelector('button:not([type="button"])') || document.querySelector('button[type="submit"]');
                if (submitBtn) { (submitBtn as HTMLButtonElement).click(); return; }
                if (form) { if ((form as any).requestSubmit) (form as any).requestSubmit(); else (form as any).submit(); return; }
                input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
            }, 50);
            return;
        }
    };

    // 处理发布按钮点击
    const handlePublish = (task: WeeklyTask) => {
        if (!task.prompt) return;

        if (streamCtx && typeof streamCtx.submit === "function") {
            const newMessage = {
                role: "user",
                type: "human",
                content: task.prompt,
                additional_kwargs: {
                    render_markdown: true,
                    direct_intent: "article_task",
                    article_topic: task.title, // 顺便把 Title 也带过去，虽然 prompt 里也有
                }
            };
            try {
                streamCtx.submit({ messages: [newMessage] });
                return;
            } catch { }
        }

        sendMessage(task.prompt);
    };

    // 渲染步骤图标
    const renderIcon = (idx: number, isDone: boolean, isRunning: boolean) => {
        const color = isDone ? "#22c55e" : isRunning ? "#2563eb" : "#cbd5e1";
        if (isDone) return (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        );
        if (isRunning) return <Spinner />;
        return <div style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />;
    };

    return (
        <div
            className="lgui-card"
            style={{
                borderRadius: 16,
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                padding: "24px",
                fontSize: 13,
                boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
                maxWidth: 700,
                position: 'relative'
            }}
        >
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, fontSize: 18, fontWeight: 700, color: '#0f172a' }}>
                    <span style={{ fontSize: 24 }}>📝</span> SEO Weekly Content Tasks
                </div>
                {meta?.week_start && (
                    <div style={{ marginTop: 4, fontSize: 12, color: "#64748b" }}>
                        Week: {meta.week_start}
                    </div>
                )}
                {status === "done" && (
                    <div style={{ marginTop: 4, fontSize: 12, color: "#16a34a", fontWeight: 600 }}>
                        {props.progress || `${tasks.length} tasks ready`}
                    </div>
                )}
            </div>

            {/* Loading Steps */}
            {status === "loading" && steps.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
                    {steps.map((step, idx) => {
                        const isDone = idx + 1 < activeStep;
                        const isRunning = idx + 1 === activeStep;
                        return (
                            <div key={idx} style={{ display: 'flex', gap: 12, alignItems: 'center', opacity: idx + 1 > activeStep ? 0.5 : 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24 }}>
                                    {renderIcon(idx, isDone, isRunning)}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 14, fontWeight: 600, color: isRunning ? "#2563eb" : "#1e293b" }}>
                                        {step}
                                        {isRunning && (
                                            <span style={{ marginLeft: 6, color: '#3b82f6' }}>
                                                <span className="pulse-dot">.</span><span className="pulse-dot">.</span><span className="pulse-dot">.</span>
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Task List */}
            {status === "done" && tasks.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {tasks.map((task, idx) => (
                        <div
                            key={task.task_id || idx}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                padding: '12px 16px',
                                borderRadius: 10,
                                border: '1px solid #e2e8f0',
                                background: '#f8fafc',
                            }}
                        >
                            {/* Task Title */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                    fontSize: 14,
                                    fontWeight: 600,
                                    color: '#1e293b',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                }}>
                                    {task.title}
                                </div>
                            </div>

                            {/* Publish Button */}
                            <button
                                onClick={() => handlePublish(task)}
                                style={{
                                    flexShrink: 0,
                                    padding: '8px 16px',
                                    borderRadius: 8,
                                    border: 'none',
                                    background: '#2563eb',
                                    color: '#fff',
                                    fontSize: 13,
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 6,
                                    transition: 'background 0.2s',
                                }}
                                onMouseEnter={(e: any) => (e.currentTarget.style.background = '#1d4ed8')}
                                onMouseLeave={(e: any) => (e.currentTarget.style.background = '#2563eb')}
                            >
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M22 2L11 13"></path>
                                    <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                                </svg>
                                Publish
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Empty State */}
            {status === "done" && tasks.length === 0 && !props.error_message && (
                <div style={{
                    textAlign: 'center',
                    padding: '32px 16px',
                    color: '#64748b',
                    fontSize: 14,
                }}>
                    No tasks available for this week.
                </div>
            )}

            {/* Error State */}
            {props.error_message && (
                <div style={{
                    marginTop: 16,
                    padding: 12,
                    background: "#fff1f2",
                    borderRadius: 8,
                    border: "1px solid #fecdd3",
                    fontSize: 12,
                    color: "#9f1239"
                }}>
                    {props.error_message}
                </div>
            )}
        </div>
    );
};
