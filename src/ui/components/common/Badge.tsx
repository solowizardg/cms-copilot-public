import { React } from "../../hooks";
import type { BadgeProps } from "../../types";

export const Badge: React.FC<BadgeProps> = ({
    children,
    tone = "slate",
}) => {
    const tones: Record<string, { bg: string; fg: string; bd: string }> = {
        slate: { bg: "#f8fafc", fg: "#475569", bd: "#e2e8f0" },
        blue: { bg: "#eff6ff", fg: "#2563eb", bd: "#bfdbfe" },
        green: { bg: "#f0fdf4", fg: "#16a34a", bd: "#bbf7d0" },
        red: { bg: "#fef2f2", fg: "#dc2626", bd: "#fecaca" },
    };
    const t = tones[tone];
    return (
        <span
            style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                borderRadius: 9999,
                padding: "2px 10px",
                fontSize: 11,
                lineHeight: "16px",
                color: t.fg,
                background: t.bg,
                border: `1px solid ${t.bd}`,
                whiteSpace: "nowrap",
            }}
        >
            {children}
        </span>
    );
};
