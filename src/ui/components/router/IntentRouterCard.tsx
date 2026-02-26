import { React } from "../../hooks";
import type { IntentRouterProps } from "../../types";
import "../../styles.css";

export const IntentRouterCard: React.FC<IntentRouterProps> = (props) => {
    if (props.hidden) return null;


    // RAG status override
    const isRAG = !!props.rag_status;
    const isRagRunning = props.rag_status === "running";
    const isRagError = props.rag_status === "error";
    const isRagDone = props.rag_status === "done";

    // Base thinking status
    const isThinking = props.status === "thinking" && !isRAG;
    const isDone = props.status === "done" && !isRAG;
    const isError = props.status === "error" && !isRAG;

    // Derived state for display
    const showRunning = isThinking || isRagRunning;
    const showError = isError || isRagError;
    const showDone = isDone || isRagDone;

    // Decide what text to show
    let mainTitle = props.main_title || "Thinking Completed";
    let subText = "";

    if (isRAG) {
        if (!props.main_title) {
            if (isRagRunning) mainTitle = "Retrieving Knowledge...";
            else if (isRagError) mainTitle = "Retrieval Failed";
            else if (isRagDone) mainTitle = "Knowledge Knowledge Retrieved";
        }

        if (props.rag_message) subText = props.rag_message;
    } else {
        if (isThinking) {
            mainTitle = props.main_title || "Thinking...";
            subText = "Analyzing request details";
        } else if (isError) {
            mainTitle = "Thinking Failed";
            subText = "Failed to identify intent";
        } else if (isDone) {
            mainTitle = props.main_title || "Thinking Completed";
            subText = "Intent identified";
        }
    }

    return (
        <div
            style={{
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                borderRadius: 12,
                border: "1px solid #e2e8f0",
                background: "#fff",
                padding: "12px",
                fontSize: 13,
                boxShadow: "none",
                maxWidth: 700,
            }}
        >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div className="thinking-loader">
                    <div className="thinking-loader">
                        {showRunning ? (
                            <>
                                <div
                                    className="thinking-ring"
                                    style={{
                                        animation: "spin 1s linear infinite",
                                        background: "conic-gradient(from 0deg, #3b82f6, #ec4899, #eab308, #3b82f6)",
                                        padding: 2,
                                    }}
                                ></div>
                                <div className="thinking-star" style={{ color: "#3b82f6" }}>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
                                    </svg>
                                </div>
                            </>
                        ) : showDone ? (
                            <div style={{ color: "#22c55e", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                                </svg>
                            </div>
                        ) : (
                            <div style={{ color: "#ef4444", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
                                </svg>
                            </div>
                        )}
                    </div>
                </div>

                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#1e293b" }}>
                        {mainTitle}
                    </div>
                    {subText ? (
                        <div style={{ fontSize: 12, color: "#64748b", whiteSpace: "pre-wrap" }}>
                            {subText}
                        </div>
                    ) : null}
                </div>

            </div>
        </div>
    );
};
