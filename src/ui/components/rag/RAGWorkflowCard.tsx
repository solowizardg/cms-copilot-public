import { React } from "../../hooks";
import type { RAGWorkflowProps, RAGStep } from "../../types";
import "../../styles.css";

const ragTone = (s?: string) => {
    const st = String(s || "").toLowerCase();
    if (st === "running") return "blue";
    if (st === "done") return "green";
    if (st === "error") return "red";
    return "slate";
};

const ragLabel = (s?: string) => {
    const st = String(s || "").toLowerCase();
    if (st === "running") return "Retrieving";
    if (st === "done") return "Completed";
    if (st === "error") return "Failed";
    if (st === "pending") return "Pending";
    return st || "—";
};

export const RAGWorkflowCard: React.FC<RAGWorkflowProps> = (props) => {
    const isRunning = props.status === "running";
    const isDone = props.status === "done";
    const isError = props.status === "error";

    const steps = props.steps || {};
    const prepSteps = (steps.prep || []) as RAGStep[];
    const genSteps = (steps.generate || []) as RAGStep[];
    const allSteps = [...prepSteps, ...genSteps].filter(
        (s) =>
            !["workflow", "analysis_language", "detect_language", "initialize"].includes(s.key || "") &&
            !["workflow", "analysis_language"].includes(s.title || "")
    );

    // Find current running step or last completed
    const currentStep = allSteps.find(s => s.status === "running") || allSteps[allSteps.length - 1];

    return (
        <div
            className="lgui-card"
            style={{
                borderRadius: 12,
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                padding: 16,
                fontSize: 13,
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                maxWidth: 600,
            }}
        >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                {/* Loader / Status Icon */}
                <div className="thinking-loader">
                    <div
                        className="thinking-ring"
                        style={{
                            animation: isRunning ? "spin 1s linear infinite" : "none",
                            background: isRunning
                                ? "conic-gradient(from 0deg, #3b82f6, #ec4899, #eab308, #3b82f6)"
                                : isError ? "#ef4444" : "#22c55e",
                            padding: 2,
                        }}
                    ></div>

                    <div className="thinking-star" style={{ color: isRunning ? "#3b82f6" : isError ? "#ef4444" : "#22c55e" }}>
                        {isDone ? (
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                            </svg>
                        ) : isError ? (
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
                            </svg>
                        ) : (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
                            </svg>
                        )}
                    </div>
                </div>

                {/* Content */}
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#1e293b" }}>
                        {isRunning ? "Retrieving Knowledge..." : isError ? "Retrieval Failed" : "Knowledge Base Retrieval Completed"}
                    </div>

                    {/* Subtext: Current step or summary */}
                    <div style={{ fontSize: 12, color: "#64748b" }}>
                        {isRunning && currentStep
                            ? `Processing: ${currentStep.title || currentStep.key}`
                            : isDone
                                ? "Relevant context retrieved"
                                : "Waiting for tasks..."}
                    </div>
                </div>

                <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>rag</div>
            </div>

            {/* Expanded details */}
            {isRunning || isError ? (
                <div style={{ marginTop: 12, borderTop: "1px solid #f1f5f9", paddingTop: 8 }}>
                    {allSteps.map((s, idx) => {
                        const sRun = s.status === "running";
                        const sDone = s.status === "done";
                        if (!sRun && !sDone && s.status !== "error") return null; // Hide pending
                        return (
                            <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                                <span style={{ color: sRun ? "#2563eb" : sDone ? "#10b981" : "#64748b", fontWeight: sRun ? 600 : 400 }}>
                                    {s.title || s.key}
                                </span>
                                <span style={{ color: "#94a3b8" }}>{s.status}</span>
                            </div>
                        )
                    })}
                </div>
            ) : null}

            {props.error_message ? (
                <div style={{ marginTop: 8, fontSize: 11, color: "#ef4444" }}>
                    {props.error_message}
                </div>
            ) : null}
        </div>
    );
};
