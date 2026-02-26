import { React, useStreamContext, useState } from "../../hooks";
import type { ReportConfirmInsightsProps } from "../../types";
import "../../styles.css";

export const ReportConfirmInsightsCard: React.FC<ReportConfirmInsightsProps> = (props) => {
    const streamCtx = useStreamContext?.() as any;
    const [submitting, setSubmitting] = useState(false);
    const [choice, setChoice] = useState(null as boolean | null);

    const handleChoice = (confirmed: boolean) => {
        if (submitting) return;
        setSubmitting(true);
        setChoice(confirmed);
        // 推荐：用 submit 发起一条新消息继续对话（避免 interrupt/resume 触发的重绘）
        if (streamCtx && typeof streamCtx.submit === "function") {
            try {
                const displayContent = confirmed
                    ? "Confirmed: continue generating deep insights."
                    : "Confirmed: skip deep insights for now.";
                const newMessage = {
                    role: "assistant",
                    type: "ai",
                    content: displayContent,
                    additional_kwargs: {
                        report_insights_confirmed: confirmed,
                        render_markdown: true,
                    },
                };
                streamCtx.submit({ messages: [newMessage] });
                return;
            } catch { }
        }
        // 兜底：老环境可能只有 resume
        if (streamCtx && typeof streamCtx.resume === "function") {
            try {
                streamCtx.resume(confirmed);
                return;
            } catch { }
        }
        console.warn("submit/resume is not supported in this environment");
    };

    if (props.hidden) return null;

    return (
        <div
            className="lgui-card"
            style={{
                borderRadius: 12,
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                padding: 20,
                fontSize: 13,
                boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                maxWidth: 640,
            }}
        >
            {/* Header */}
            <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div
                    style={{
                        width: 34,
                        height: 34,
                        borderRadius: 17,
                        background: "#e0f2fe",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 18,
                        color: "#0284c7",
                    }}
                >
                    💡
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 15, color: "#0f172a", marginBottom: 4 }}>
                        Confirm Insight Generation
                    </div>
                    <div style={{ fontSize: 13, color: "#475569", lineHeight: 1.5 }}>
                        {props.message || "Would you like to run a detailed AI analysis on this report data?"}
                    </div>
                </div>
            </div>

            <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
                <button
                    onClick={() => handleChoice(true)}
                    disabled={submitting}
                    style={{
                        flex: 1,
                        padding: "10px 16px",
                        borderRadius: 8,
                        border: "none",
                        background: "#2563eb",
                        color: "#fff",
                        fontWeight: 700,
                        cursor: "pointer",
                        fontSize: 13,
                        opacity: submitting ? 0.7 : 1,
                    }}
                >
                    {submitting && choice === true ? "Submitted" : "Generate Insights"}
                </button>
                <button
                    onClick={() => handleChoice(false)}
                    disabled={submitting}
                    style={{
                        flex: 1,
                        padding: "10px 16px",
                        borderRadius: 8,
                        border: "1px solid #cbd5e1",
                        background: "#fff",
                        color: "#0f172a",
                        fontWeight: 700,
                        cursor: "pointer",
                        fontSize: 13,
                        opacity: submitting ? 0.7 : 1,
                    }}
                >
                    {submitting && choice === false ? "Submitted" : "Not now"}
                </button>
            </div>

            {choice !== null && (
                <div
                    style={{
                        marginTop: 10,
                        fontSize: 12,
                        color: "#64748b",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                    }}
                >
                    <span>{choice ? "✅" : "ℹ️"}</span>
                    <span>
                        {choice
                            ? "Decision submitted. Insights will be generated."
                            : "Decision submitted. Insights generation skipped."}
                    </span>
                </div>
            )}
        </div>
    );
};
