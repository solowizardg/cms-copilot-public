import { React } from "../../hooks";
import type { ChartAnalysisProps } from "../../types";
import "../../styles.css";

export const ChartAnalysisCard: React.FC<ChartAnalysisProps> = (props) => {
    const title = props.chart_title || props.chart_key || "Chart Analysis";
    const chartType = props.chart_type || "chart";
    const desc = props.description || "";

    return (
        <div
            className="lgui-card"
            style={{
                borderRadius: 16,
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                padding: "20px",
                fontSize: 13,
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
                maxWidth: 720,
                marginTop: 12,
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 20 }}>📊</span>
                    <div style={{ fontSize: 15, fontWeight: 700, color: "#0f172a" }}>{title}</div>
                </div>
                <div style={{
                    fontSize: 11,
                    padding: "4px 10px",
                    borderRadius: 20,
                    background: "#f1f5f9",
                    color: "#64748b",
                    fontWeight: 600,
                    textTransform: "uppercase"
                }}>
                    {chartType}
                </div>
            </div>

            {desc ? (
                <div style={{ background: "#f8fafc", padding: 16, borderRadius: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#3b82f6", marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span>💡</span> AI Analysis
                    </div>
                    <div style={{ fontSize: 13, color: "#334155", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{desc}</div>
                </div>
            ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: "#94a3b8", fontSize: 13, fontStyle: "italic", padding: 8 }}>
                    <span className="pulse-dot">.</span>
                    <span className="pulse-dot">.</span>
                    <span className="pulse-dot">.</span>
                    Generating analysis...
                </div>
            )}
        </div>
    );
};
