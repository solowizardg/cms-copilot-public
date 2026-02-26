import { React } from "../../hooks";
import type { ReportChartsProps } from "../../types";
import "../../styles.css";

export const ReportChartsCard: React.FC<ReportChartsProps> = (props) => {
    const charts = props.charts || props.report?.charts || {};
    const summary = props.summary || props.report?.summary || {};

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
                maxWidth: 720,
            }}
        >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, fontSize: 16, fontWeight: 700, color: '#0f172a' }}>
                    <span style={{ fontSize: 20 }}>📈</span> Charts & Data
                </div>
                <div style={{ fontSize: 11, color: "#94a3b8" }}>report</div>
            </div>

            {/* Summary Stats */}
            {summary && Object.keys(summary).length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12, marginBottom: 20 }}>
                    {summary.total_visits != null && (
                        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, textAlign: "center" }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: "#0f172a" }}>{summary.total_visits.toLocaleString()}</div>
                            <div style={{ fontSize: 11, color: "#64748b" }}>Total Visits</div>
                        </div>
                    )}
                    {summary.total_page_views != null && (
                        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, textAlign: "center" }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: "#0f172a" }}>{summary.total_page_views.toLocaleString()}</div>
                            <div style={{ fontSize: 11, color: "#64748b" }}>Page Views</div>
                        </div>
                    )}
                    {summary.bounce_rate != null && (
                        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, textAlign: "center" }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: "#0f172a" }}>{(summary.bounce_rate * 100).toFixed(1)}%</div>
                            <div style={{ fontSize: 11, color: "#64748b" }}>Bounce Rate</div>
                        </div>
                    )}
                </div>
            )}

            {/* Charts placeholder - actual chart rendering is done externally */}
            {charts && Object.keys(charts).length > 0 ? (
                <div style={{ color: "#64748b", fontSize: 12, padding: 16, background: "#f8fafc", borderRadius: 8, textAlign: "center" }}>
                    {Object.keys(charts).length} chart(s) available. Charts are rendered by the external frontend component.
                </div>
            ) : (
                <div style={{ color: "#94a3b8", fontSize: 12, padding: 16, textAlign: "center", fontStyle: "italic" }}>
                    No charts available yet.
                </div>
            )}
        </div>
    );
};
