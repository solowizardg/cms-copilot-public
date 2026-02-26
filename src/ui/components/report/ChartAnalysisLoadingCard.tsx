import { React } from "../../hooks";
import type { ChartAnalysisLoadingProps } from "../../types";
import "../../styles.css";

export const ChartAnalysisLoadingCard: React.FC<ChartAnalysisLoadingProps> = (props) => {
    // 兜底：只在显式 hidden===false 时显示
    if (props.hidden !== false) return null;

    const title = props.chart_title || props.chart_key || "Chart";

    return (
        <div
            className="lgui-card"
            style={{
                borderRadius: 14,
                border: "1px dashed #fcd34d",
                background: "#fffbeb",
                padding: 12,
                fontSize: 12,
                color: "#92400e",
                boxShadow: "0 1px 2px rgba(15, 23, 42, 0.06)",
                maxWidth: 720,
                marginTop: 8,
            }}
        >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span>⏳</span>
                <div style={{ fontWeight: 600 }}>Processing {title} …</div>
            </div>
        </div>
    );
};
