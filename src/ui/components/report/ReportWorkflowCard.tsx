import { React } from "../../hooks";
import type { ReportProgressProps } from "../../types";
import { Spinner } from "../common/Spinner";
import "../../styles.css";

export const ReportWorkflowCard: React.FC<ReportProgressProps> = (props) => {
    if (props.hidden) return null;

    const status = props.status || "loading";
    const steps = props.steps || [];
    const activeStep = props.active_step || 1;

    // Normalize steps to objects with step and status
    const normalizedSteps = steps.map((s, idx) => {
        if (typeof s === "string") {
            return { step: s, status: idx + 1 < activeStep ? "done" : idx + 1 === activeStep ? "running" : "pending" };
        }
        return s;
    });

    const isInsightsPhase =
        props.step === "generating_insights" ||
        normalizedSteps.some((s: any) => {
            const name = typeof s === "string" ? s : s?.step;
            return typeof name === "string" && name.toLowerCase().includes("insight");
        });

    const isStepDone = (idx: number) => {
        const s = normalizedSteps[idx];
        return s?.status === "done" || (status === "done" && idx < normalizedSteps.length);
    };

    const isStepRunning = (idx: number) => {
        const s = normalizedSteps[idx];
        return s?.status === "running" || (status !== "done" && idx + 1 === activeStep);
    };

    const renderIcon = (idx: number, isDone: boolean, isRunning: boolean) => {
        if (isDone) {
            return (
                <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: 12,
                    background: "#22c55e",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#fff">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                    </svg>
                </div>
            );
        }
        if (isRunning) {
            return (
                <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: 12,
                    background: "#2563eb",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                }}>
                    <Spinner />
                </div>
            );
        }
        return (
            <div style={{
                width: 24,
                height: 24,
                borderRadius: 12,
                background: "#f1f5f9",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#94a3b8",
                fontSize: 12,
                fontWeight: 700
            }}>
                {idx + 1}
            </div>
        );
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
            }}
        >
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, fontSize: 18, fontWeight: 700, color: '#0f172a' }}>
                    <span style={{ fontSize: 24 }}>{isInsightsPhase ? "🔍" : "📊"}</span>
                    {isInsightsPhase ? "Generating Insights" : "Generating Site Report"}
                </div>
                {status === "done" && (
                    <div style={{ marginTop: 4, fontSize: 12, color: "#16a34a", fontWeight: 600 }}>
                        {isInsightsPhase ? "Insights Generated" : "Report Generated"}
                    </div>
                )}
                {status === "error" && (
                    <div style={{ marginTop: 4, fontSize: 12, color: "#ef4444", fontWeight: 600 }}>
                        {isInsightsPhase ? "Insights Generation Failed" : "Report Generation Failed"}
                    </div>
                )}
            </div>

            {/* Steps */}
            {normalizedSteps.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {normalizedSteps.map((stepObj, idx) => {
                        const isDone = isStepDone(idx);
                        const isRunning = isStepRunning(idx);
                        const stepName = typeof stepObj === "string" ? stepObj : stepObj.step;

                        return (
                            <div key={idx} style={{ display: 'flex', gap: 12, alignItems: 'center', opacity: !isDone && !isRunning ? 0.5 : 1 }}>
                                {renderIcon(idx, isDone, isRunning)}
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 14, fontWeight: 600, color: isRunning ? "#2563eb" : isDone ? "#22c55e" : "#64748b" }}>
                                        {stepName}
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

            {/* Message */}
            {props.message && (
                <div style={{ marginTop: 16, padding: 12, background: "#f8fafc", borderRadius: 8, fontSize: 12, color: "#334155" }}>
                    {props.message}
                </div>
            )}

            {/* Error */}
            {props.error_message && (
                <div style={{ marginTop: 16, padding: 12, background: "#fff1f2", borderRadius: 8, border: "1px solid #fecdd3", fontSize: 12, color: "#9f1239" }}>
                    {props.error_message}
                </div>
            )}
        </div>
    );
};
