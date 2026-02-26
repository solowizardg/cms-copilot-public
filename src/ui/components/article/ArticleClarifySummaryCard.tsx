import { React } from "../../hooks";
import type { ArticleClarifySummaryProps } from "../../types";
import { Badge } from "../common/Badge";
import "../../styles.css";

export const ArticleClarifySummaryCard: React.FC<ArticleClarifySummaryProps> = (props) => {
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
            <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                {/* 左侧状态圆环 */}
                <div style={{ paddingTop: 2 }}>
                    <div
                        style={{
                            width: 18,
                            height: 18,
                            borderRadius: "50%",
                            border: "4px solid #bbf7d0",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                        }}
                    >
                        <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#16a34a" }} />
                    </div>
                </div>

                <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b", marginBottom: 2 }}>
                        Confirm the content
                    </div>

                    {/* 链接卡片 */}
                    <div style={{
                        marginTop: 12,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '8px 12px',
                        borderRadius: 8,
                        border: '1px solid #e2e8f0',
                        background: '#fff',
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                    }}
                        onMouseOver={(e: any) => e.currentTarget.style.background = '#f8fafc'}
                        onMouseOut={(e: any) => e.currentTarget.style.background = '#fff'}
                    >
                        <span style={{ fontSize: 16 }}>🌐</span>
                        <span style={{ color: '#2563eb', fontWeight: 500, textDecoration: 'none' }}>
                            {props.topic || "Untitled Article"}
                        </span>
                        <Badge tone="slate">View</Badge>
                    </div>

                    {/* 标签式信息展示 */}
                    <div style={{ marginTop: 12, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 8, fontSize: 12, color: "#475569" }}>
                        <span style={{ fontWeight: 500, color: "#334155" }}>Published Setup:</span>

                        <div style={{ display: "flex", alignItems: "center", gap: 4, background: "#f1f5f9", padding: "2px 8px", borderRadius: 4 }}>
                            <span style={{ color: "#64748b" }}>Application</span>
                            <span style={{ color: "#0f172a", fontWeight: 500 }}>{props.app_name || props.app_id || "Blog"}</span>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: 4, background: "#f1f5f9", padding: "2px 8px", borderRadius: 4 }}>
                            <span style={{ color: "#64748b" }}>Tone</span>
                            <span style={{ color: "#0f172a", fontWeight: 500 }}>{props.tone || "Professional"}</span>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: 4, background: "#f1f5f9", padding: "2px 8px", borderRadius: 4 }}>
                            <span style={{ color: "#64748b" }}>Format</span>
                            <span style={{ color: "#0f172a", fontWeight: 500 }}>{props.content_format || "Article"}</span>
                        </div>
                    </div>

                    {/* Publish 按钮 */}
                    <div style={{ marginTop: 16 }}>
                        <button
                            className="lgui-btn-primary"
                            style={{
                                borderRadius: 6,
                                border: "none",
                                color: "#ffffff",
                                padding: "8px 24px",
                                fontSize: 13,
                                fontWeight: 600,
                                cursor: "pointer",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}
                        >
                            Publish
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
