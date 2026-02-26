import { React, useState, useEffect } from "../../hooks";
import type { ReportInsightsProps } from "../../types";
import "../../styles.css";

// Typewriter effect component
const TypewriterText = ({ text, speed = 20, className, style }: { text: string; speed?: number; className?: string; style?: any }) => {
    const [displayedText, setDisplayedText] = useState("");
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        if (currentIndex < text.length) {
            const timer = setTimeout(() => {
                setDisplayedText((prev: string) => prev + text[currentIndex]);
                setCurrentIndex((prev: number) => prev + 1);
            }, speed);
            return () => clearTimeout(timer);
        }
    }, [currentIndex, text, speed]);

    useEffect(() => {
        setDisplayedText("");
        setCurrentIndex(0);
    }, [text]);

    return <span className={className} style={style}>{displayedText}</span>;
};

export const ReportInsightsCard: React.FC<ReportInsightsProps> = (props) => {
    const report = props.report || {};
    const insights = report.insights || {};
    const actions = report.actions || [];
    const todos = report.todos || [];

    const oneLiner = insights.one_liner || "";
    const hypotheses = insights.hypotheses || [];

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
                    <span style={{ fontSize: 20 }}>💡</span> Key Insights
                </div>
                <div style={{ fontSize: 11, color: "#94a3b8" }}>insights</div>
            </div>

            {/* One-liner */}
            {oneLiner && (
                <div style={{ background: "linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%)", padding: 16, borderRadius: 12, marginBottom: 20 }}>
                    <div style={{ fontSize: 15, fontWeight: 600, color: "#1e40af", lineHeight: 1.5 }}>
                        <TypewriterText text={oneLiner} speed={15} />
                    </div>
                </div>
            )}

            {/* Hypotheses */}
            {hypotheses.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>Analysis</div>
                    <div style={{ display: "grid", gap: 8 }}>
                        {hypotheses.map((h: any, idx: number) => (
                            <div key={idx} style={{ padding: 12, background: "#f8fafc", borderRadius: 8, border: "1px solid #f1f5f9" }}>
                                <div style={{ fontSize: 13, color: "#334155" }}>{h.text}</div>
                                {h.confidence && (
                                    <div style={{ marginTop: 6, fontSize: 11, color: "#94a3b8" }}>
                                        Confidence: <span style={{ fontWeight: 600, color: h.confidence === "high" ? "#16a34a" : h.confidence === "medium" ? "#d97706" : "#64748b" }}>{h.confidence}</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Actions */}
            {actions.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>Recommended Actions</div>
                    <div style={{ display: "grid", gap: 8 }}>
                        {actions.map((a: any, idx: number) => (
                            <div key={idx} style={{ padding: 12, background: "#fefce8", borderRadius: 8, border: "1px solid #fef08a" }}>
                                <div style={{ fontSize: 13, fontWeight: 600, color: "#854d0e" }}>{a.title}</div>
                                {a.why && <div style={{ marginTop: 4, fontSize: 12, color: "#a16207" }}>{a.why}</div>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Todos */}
            {todos.length > 0 && (
                <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>To-Do Items</div>
                    <div style={{ display: "grid", gap: 8 }}>
                        {todos.map((t: any, idx: number) => (
                            <div key={idx} style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: "#334155" }}>{t.title}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Empty state */}
            {!oneLiner && hypotheses.length === 0 && actions.length === 0 && todos.length === 0 && (
                <div style={{ textAlign: "center", padding: 20, color: "#94a3b8", fontSize: 13, fontStyle: "italic" }}>
                    No insights available yet. Analysis is still in progress...
                </div>
            )}
        </div>
    );
};
