import { React } from "../../hooks";
import type { MCPWorkflowProps } from "../../types";
import { Spinner } from "../common/Spinner";
import "../../styles.css";

export const MCPWorkflowCard: React.FC<MCPWorkflowProps> = (props) => {
    const status = props.status || "loading";
    const title = props.title || "Background Operation";
    const steps = props.steps || props.plan_steps || [];
    const activeStep = props.active_step || 1;

    // 发送消息的辅助函数
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

    // 恢复 interrupt 的函数
    const resumeInterrupt = (value: any) => {
        const win = window as any;
        if (typeof win.__LANGGRAPH_RESUME__ === "function") { try { win.__LANGGRAPH_RESUME__(value); return; } catch { } }
        const resumeFns = ["resumeThread", "resume", "sendResume"];
        for (const fn of resumeFns) { if (typeof win[fn] === "function") { try { win[fn](value); return; } catch { } } }
        window.dispatchEvent(new CustomEvent("langgraph:resume", { detail: value }));
        sendMessage(value?.confirmed ? "Confirmed" : "Cancelled");
    };

    const handleConfirm = () => resumeInterrupt({ confirmed: true, action: "approve" });
    const handleCancel = () => resumeInterrupt({ confirmed: false, action: "cancel" });

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
                    <span style={{ fontSize: 24 }}>🛠️</span> {title}
                </div>
                {props.status === "done" && (
                    <div style={{ marginTop: 4, fontSize: 12, color: "#16a34a", fontWeight: 600 }}>Operation Completed</div>
                )}
            </div>

            {/* Steps List */}
            {steps.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 20 }}>
                    {steps.map((step: any, idx: number) => {
                        const isDone = (status === "done" || status === "cancelled") ? true : idx + 1 < activeStep;
                        const isRunning = (status !== "done" && status !== "cancelled") && idx + 1 === activeStep;
                        return (
                            <div key={idx} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', opacity: idx + 1 > activeStep ? 0.5 : 1 }}>
                                <div style={{ marginTop: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24 }}>
                                    {renderIcon(idx, isDone, isRunning)}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 14, fontWeight: 600, color: isRunning ? "#2563eb" : "#1e293b" }}>
                                        {step.title || step.name || `Step ${idx + 1}`}
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

            {/* Current Message / Log */}
            {props.message && props.status !== "done" && (
                <div style={{ marginTop: 12, borderRadius: 8, background: "#f8fafc", padding: 12, border: "1px solid #e2e8f0", fontSize: 12, color: "#334155" }}>
                    {props.message}
                </div>
            )}

            {/* Options Selection */}
            {props.options && props.options.length > 0 && (
                <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
                    {props.options.map((o, idx) => (
                        <button
                            key={idx}
                            onClick={props.status === "select" ? () => sendMessage(String(idx + 1)) : undefined}
                            style={{
                                textAlign: 'left',
                                padding: '10px 14px',
                                borderRadius: 8,
                                border: '1px solid #e2e8f0',
                                background: '#fff',
                                cursor: props.status === "select" ? 'pointer' : 'default',
                                fontSize: 13
                            }}
                        >
                            <b>{idx + 1}. {o.name || o.code}</b> <span style={{ color: '#64748b' }}> - {o.desc}</span>
                        </button>
                    ))}
                </div>
            )}

            {/* Confirmation Actions */}
            {props.status === "confirm" && (
                <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
                    <button
                        onClick={handleConfirm}
                        style={{
                            flex: 1, padding: "10px", borderRadius: 8, border: "none",
                            background: "#2563eb", color: "#fff", fontWeight: 600, cursor: "pointer"
                        }}
                    >
                        Confirmed & Execute
                    </button>
                    <button
                        onClick={handleCancel}
                        style={{
                            flex: 1, padding: "10px", borderRadius: 8, border: "1px solid #e2e8f0",
                            background: "#fff", color: "#64748b", fontWeight: 600, cursor: "pointer"
                        }}
                    >
                        Cancel
                    </button>
                </div>
            )}

            {/* Result Output */}
            {props.result && (
                <div style={{ marginTop: 16, padding: 12, background: "#ecfdf5", borderRadius: 8, border: "1px solid #bbf7d0", fontSize: 12, color: "#065f46", whiteSpace: "pre-wrap" }}>
                    {props.result}
                </div>
            )}

            {/* Error Output */}
            {props.error_message && (
                <div style={{ marginTop: 16, padding: 12, background: "#fff1f2", borderRadius: 8, border: "1px solid #fecdd3", fontSize: 12, color: "#9f1239" }}>
                    {props.error_message}
                </div>
            )}
        </div>
    );
};
