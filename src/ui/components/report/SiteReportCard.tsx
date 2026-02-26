import { React } from "../../hooks";
import type { SiteReportProps } from "../../types";
import { Badge } from "../common/Badge";
import { Spinner } from "../common/Spinner";
import "../../styles.css";

export const SiteReportCard: React.FC<SiteReportProps> = (props) => {
    const badgeTone = props.status === "done" ? "green" : props.status === "error" ? "red" : "blue";
    const badgeLabel = props.status === "done" ? "Completed" : props.status === "error" ? "Failed" : "Generating";
    const steps = props.steps || [];
    const report = props.report;
    const summary = report?.summary;

    return (
        <div
            className="lgui-card"
            style={{
                borderRadius: 14,
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                padding: 16,
                fontSize: 13,
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                maxWidth: 720,
            }}
        >
            {/* Header */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
                <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "#0f172a" }}>
                        📊 Site Report
                    </div>
                    <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <Badge tone={badgeTone as any}>
                            {props.status === "loading" ? <Spinner /> : null}
                            <span>{badgeLabel}</span>
                        </Badge>
                    </div>
                </div>
                <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>report</div>
            </div>

            {/* Steps Progress */}
            {props.status === "loading" && steps.length > 0 && (
                <div style={{ marginTop: 12, borderRadius: 12, border: "1px solid #f1f5f9", background: "#f8fafc", padding: 12 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>Progress</div>
                    <div style={{ display: "grid", gap: 6 }}>
                        {steps.map((step, idx) => {
                            const isActive = (props.active_step || 1) === idx + 1;
                            const isDone = (props.active_step || 1) > idx + 1;
                            return (
                                <div key={idx} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                                    <span
                                        style={{
                                            width: 18,
                                            height: 18,
                                            borderRadius: 9,
                                            display: "inline-flex",
                                            alignItems: "center",
                                            justifyContent: "center",
                                            fontSize: 10,
                                            fontWeight: 700,
                                            background: isDone ? "#86efac" : isActive ? "#bfdbfe" : "#e2e8f0",
                                            color: isDone ? "#052e16" : isActive ? "#1d4ed8" : "#64748b",
                                        }}
                                    >
                                        {isDone ? "✓" : isActive ? <Spinner /> : idx + 1}
                                    </span>
                                    <span style={{ fontSize: 12, color: isActive ? "#0f172a" : "#64748b", fontWeight: isActive ? 600 : 400 }}>
                                        {step}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Summary Stats */}
            {props.status === "done" && summary && (
                <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: 12 }}>
                    {summary.total_visits != null && (
                        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, textAlign: "center" }}>
                            <div style={{ fontSize: 18, fontWeight: 700, color: "#0f172a" }}>{summary.total_visits.toLocaleString()}</div>
                            <div style={{ fontSize: 10, color: "#64748b" }}>Visits</div>
                        </div>
                    )}
                    {summary.total_page_views != null && (
                        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, textAlign: "center" }}>
                            <div style={{ fontSize: 18, fontWeight: 700, color: "#0f172a" }}>{summary.total_page_views.toLocaleString()}</div>
                            <div style={{ fontSize: 10, color: "#64748b" }}>Page Views</div>
                        </div>
                    )}
                    {summary.bounce_rate != null && (
                        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, textAlign: "center" }}>
                            <div style={{ fontSize: 18, fontWeight: 700, color: "#0f172a" }}>{(summary.bounce_rate * 100).toFixed(1)}%</div>
                            <div style={{ fontSize: 10, color: "#64748b" }}>Bounce Rate</div>
                        </div>
                    )}
                </div>
            )}

            {/* Message */}
            {props.message && (
                <div style={{ marginTop: 12, fontSize: 12, color: "#64748b" }}>
                    {props.message}
                </div>
            )}

            {/* Error */}
            {props.error_message && (
                <div style={{ marginTop: 12, padding: 12, background: "#fff1f2", borderRadius: 8, border: "1px solid #fecdd3", fontSize: 12, color: "#9f1239" }}>
                    {props.error_message}
                </div>
            )}
        </div>
    );
};
