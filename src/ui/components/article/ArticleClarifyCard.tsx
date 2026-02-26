import { React, useState, useEffect, useStreamContext } from "../../hooks";
import type { ArticleClarifyProps } from "../../types";
import "../../styles.css";

export const ArticleClarifyCard: React.FC<ArticleClarifyProps> = (props) => {
    const streamCtx = useStreamContext?.() as any;

    // 发送消息的辅助函数
    const sendMessage = (text: string) => {
        const win = window as any;
        const globalFns = ["__LANGGRAPH_SEND_MESSAGE__", "__LANGGRAPH_SEND__", "sendMessage", "sendChatMessage"];
        for (const fn of globalFns) {
            if (typeof win[fn] === "function") {
                try {
                    win[fn](text);
                    return;
                } catch { }
            }
        }

        window.dispatchEvent(new CustomEvent("langgraph:send", { detail: { text } }));

        const selectors = ["textarea", 'input[type="text"]'];
        for (const sel of selectors) {
            const input = document.querySelector(sel) as HTMLInputElement | HTMLTextAreaElement | null;
            if (!input) continue;

            const proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
            if (setter) setter.call(input, text);
            else input.value = text;

            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));

            setTimeout(() => {
                const form = input.closest("form");
                const submitBtn =
                    (form?.querySelector('button[type="submit"]') as HTMLButtonElement | null) ||
                    (form?.querySelector('button:not([type="button"])') as HTMLButtonElement | null) ||
                    (document.querySelector('button[type="submit"]') as HTMLButtonElement | null);
                if (submitBtn) {
                    submitBtn.click();
                    return;
                }
                if (form) {
                    const f = form as any;
                    if (typeof f.requestSubmit === "function") f.requestSubmit();
                    else f.submit();
                    return;
                }
                input.dispatchEvent(
                    new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true })
                );
            }, 50);

            return;
        }
    };

    const [topic, setTopic] = useState(props.topic || "");
    const [contentFormat, setContentFormat] = useState(props.content_format || "");
    const [audience, setAudience] = useState(props.target_audience || "");
    const [tone, setTone] = useState(props.tone || "");
    const [appId, setAppId] = useState(props.app_id || "");
    const [appName, setAppName] = useState(props.app_name || "");
    const [modelId, setModelId] = useState(props.model_id || "");
    const [writingRequirements, setWritingRequirements] = useState(props.writing_requirements || "");
    const [submitting, setSubmitting] = useState(false);
    const [errors, setErrors] = useState({} as Record<string, string>);

    // 当后端在多轮中更新已收集字段时，自动带入到表单
    useEffect(() => setTopic(props.topic || ""), [props.topic]);
    useEffect(() => setContentFormat(props.content_format || ""), [props.content_format]);
    useEffect(() => setAudience(props.target_audience || ""), [props.target_audience]);
    useEffect(() => setTone(props.tone || ""), [props.tone]);
    useEffect(() => setAppId(props.app_id || ""), [props.app_id]);
    useEffect(() => setAppName(props.app_name || ""), [props.app_name]);
    useEffect(() => setModelId(props.model_id || ""), [props.model_id]);
    useEffect(() => setWritingRequirements(props.writing_requirements || ""), [props.writing_requirements]);
    useEffect(() => setSubmitting(false), [props.question, JSON.stringify(props.missing || [])]);

    const toneOptions =
        props.tone_options && props.tone_options.length > 0 ? props.tone_options : ["Professional", "Formal", "Friendly"];
    const appOptions = props.app_options && props.app_options.length > 0 ? props.app_options : [];

    const resolveAppName = (id: string) => {
        const hit = appOptions.find((opt) => String(opt.id || "") === String(id || ""));
        return hit?.name || "";
    };

    const resolveModelId = (id: string) => {
        const hit = appOptions.find((opt) => String(opt.id || "") === String(id || ""));
        return hit?.model_id ? String(hit.model_id) : "";
    };

    useEffect(() => {
        if (!appName && appId && appOptions.length > 0) {
            const resolved = resolveAppName(appId);
            if (resolved) setAppName(resolved);
        }
        if (!modelId && appId && appOptions.length > 0) {
            const resolvedModel = resolveModelId(appId);
            if (resolvedModel) setModelId(resolvedModel);
        }
    }, [appId, JSON.stringify(appOptions), appName, modelId]);

    // 校验必填项
    const validateFields = (): boolean => {
        const newErrors: Record<string, string> = {};

        if (!appId.trim()) {
            newErrors.appId = "Please select an app";
        }
        if (!topic.trim()) {
            newErrors.topic = "Topic is required";
        }
        if (!contentFormat.trim()) {
            newErrors.contentFormat = "Content format is required";
        }
        if (!audience.trim()) {
            newErrors.audience = "Target audience is required";
        }
        if (!tone.trim()) {
            newErrors.tone = "Content tone is required";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // 字段变化时清除对应错误
    const clearError = (field: string) => {
        if (errors[field]) {
            setErrors((prev: Record<string, string>) => {
                const next = { ...prev };
                delete next[field];
                return next;
            });
        }
    };

    const handleSubmit = () => {
        if (submitting) return;

        if (!validateFields()) {
            return;
        }

        setSubmitting(true);
        const payload = {
            topic: topic || "",
            content_format: contentFormat || "",
            target_audience: audience || "",
            tone: tone || "",
            app_id: appId || "",
            app_name: appName || resolveAppName(appId) || "",
            model_id: modelId || resolveModelId(appId) || "",
            writing_requirements: writingRequirements || "",
        };
        const payloadJson = JSON.stringify(payload);

        const displayContent =
            `I've updated the article parameters:\n` +
            `\n- **Topic**: ${payload.topic}` +
            `\n- **Format**: ${payload.content_format}` +
            `\n- **Audience**: ${payload.target_audience}` +
            `\n- **Tone**: ${payload.tone}` +
            (payload.writing_requirements ? `\n- **Writing Requirements**: ${payload.writing_requirements}` : "");

        if (streamCtx && typeof streamCtx.submit === "function") {
            const newMessage = {
                role: "assistant",
                type: "ai",
                content: displayContent,
                additional_kwargs: {
                    submitted_payload: payload
                }
            };
            try {
                streamCtx.submit({ messages: [newMessage] });
                return;
            } catch { }
        }

        const fallbackContent = displayContent + `\n\n<!-- ${payloadJson} -->`;
        sendMessage(fallbackContent);
    };

    // 必填项标签样式
    const RequiredLabel = ({ children }: { children: React.ReactNode }) => (
        <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>
            {children} <span style={{ color: "#ef4444" }}>*</span>
        </div>
    );

    // 错误提示组件
    const ErrorMessage = ({ message }: { message?: string }) => {
        if (!message) return null;
        return (
            <div style={{
                fontSize: 11,
                color: "#ef4444",
                marginTop: 4,
                display: "flex",
                alignItems: "center",
                gap: 4
            }}>
                <span style={{ fontSize: 12 }}>⚠</span>
                {message}
            </div>
        );
    };

    // 输入框样式（含错误状态）
    const getInputStyle = (hasError: boolean) => ({
        width: "100%",
        padding: "8px 0",
        border: "none",
        borderBottom: hasError ? "2px solid #ef4444" : "1px solid #cbd5e1",
        background: "transparent",
        fontSize: 13,
        outline: "none",
        transition: "border-color 0.2s"
    });

    // 选择框样式（含错误状态）
    const getSelectStyle = (hasError: boolean) => ({
        width: "100%",
        padding: "8px 0",
        borderRadius: 0,
        border: "none",
        borderBottom: hasError ? "2px solid #ef4444" : "1px solid #cbd5e1",
        fontSize: 13,
        background: "transparent",
        color: "#334155",
        outline: "none",
        transition: "border-color 0.2s"
    });

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
            {/* Simplified Header */}
            <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a" }}>
                    I need a few more details to continue:
                </div>
                <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>
                    Fields marked with <span style={{ color: "#ef4444" }}>*</span> are required
                </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {/* Row 1: App Name & Tone */}
                <div style={{
                    background: errors.appId ? "#fef2f2" : "#f8fafc",
                    padding: 12,
                    borderRadius: 12,
                    border: errors.appId ? "1px solid #fecaca" : "1px solid #f1f5f9",
                    transition: "all 0.2s"
                }}>
                    <RequiredLabel>App Name</RequiredLabel>
                    <select
                        value={appId}
                        onChange={(e: any) => {
                            const nextId = e.target.value;
                            setAppId(nextId);
                            setAppName(resolveAppName(nextId));
                            setModelId(resolveModelId(nextId));
                            clearError("appId");
                        }}
                        style={getSelectStyle(!!errors.appId)}
                    >
                        <option value="">Select App...</option>
                        {appOptions.map((opt, idx) => (
                            <option key={`${opt.id || "app"}-${idx}`} value={String(opt.id || "")}>
                                {opt.name || opt.id}
                            </option>
                        ))}
                    </select>
                    <ErrorMessage message={errors.appId} />
                </div>

                <div style={{
                    background: errors.tone ? "#fef2f2" : "#f8fafc",
                    padding: 12,
                    borderRadius: 12,
                    border: errors.tone ? "1px solid #fecaca" : "1px solid #f1f5f9",
                    transition: "all 0.2s"
                }}>
                    <RequiredLabel>Content Tone</RequiredLabel>
                    <select
                        value={tone}
                        onChange={(e: any) => {
                            setTone(e.target.value);
                            clearError("tone");
                        }}
                        style={getSelectStyle(!!errors.tone)}
                    >
                        <option value="">Select...</option>
                        {toneOptions.map((opt) => (
                            <option key={opt} value={opt}>
                                {opt}
                            </option>
                        ))}
                    </select>
                    <ErrorMessage message={errors.tone} />
                </div>

                {/* Row 2: Content Format & Target Audience */}
                <div style={{
                    background: errors.contentFormat ? "#fef2f2" : "#f8fafc",
                    padding: 12,
                    borderRadius: 12,
                    border: errors.contentFormat ? "1px solid #fecaca" : "1px solid #f1f5f9",
                    transition: "all 0.2s"
                }}>
                    <RequiredLabel>Content Format</RequiredLabel>
                    <input
                        value={contentFormat}
                        onChange={(e: any) => {
                            setContentFormat(e.target.value);
                            clearError("contentFormat");
                        }}
                        placeholder="e.g., News Center"
                        style={getInputStyle(!!errors.contentFormat)}
                    />
                    <ErrorMessage message={errors.contentFormat} />
                </div>

                <div style={{
                    background: errors.audience ? "#fef2f2" : "#f8fafc",
                    padding: 12,
                    borderRadius: 12,
                    border: errors.audience ? "1px solid #fecaca" : "1px solid #f1f5f9",
                    transition: "all 0.2s"
                }}>
                    <RequiredLabel>Target Audience</RequiredLabel>
                    <input
                        value={audience}
                        onChange={(e: any) => {
                            setAudience(e.target.value);
                            clearError("audience");
                        }}
                        placeholder="e.g., Readers"
                        style={getInputStyle(!!errors.audience)}
                    />
                    <ErrorMessage message={errors.audience} />
                </div>

                {/* Row 3: Topic (Full Width) */}
                <div style={{
                    gridColumn: "1 / -1",
                    background: errors.topic ? "#fef2f2" : "#f8fafc",
                    padding: 12,
                    borderRadius: 12,
                    border: errors.topic ? "1px solid #fecaca" : "1px solid #f1f5f9",
                    transition: "all 0.2s"
                }}>
                    <RequiredLabel>Topic</RequiredLabel>
                    <input
                        value={topic}
                        onChange={(e: any) => {
                            setTopic(e.target.value);
                            clearError("topic");
                        }}
                        placeholder="e.g., Company releases 2026 headphones"
                        style={getInputStyle(!!errors.topic)}
                    />
                    <ErrorMessage message={errors.topic} />
                </div>

                {/* Row 4: Writing Requirements (Full Width, Optional) */}
                <div style={{
                    gridColumn: "1 / -1",
                    background: "#f8fafc",
                    padding: 12,
                    borderRadius: 12,
                    border: "1px solid #f1f5f9"
                }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>
                        Writing Requirements <span style={{ color: "#94a3b8", fontWeight: 400 }}>(optional)</span>
                    </div>
                    <textarea
                        value={writingRequirements}
                        onChange={(e: any) => setWritingRequirements(e.target.value)}
                        placeholder="e.g., Include SEO keywords, target 1500 words, use formal tone..."
                        rows={3}
                        style={{
                            width: "100%",
                            padding: "8px",
                            border: "1px solid #e2e8f0",
                            borderRadius: 8,
                            background: "#fff",
                            fontSize: 13,
                            outline: "none",
                            resize: "vertical",
                            fontFamily: "inherit",
                            lineHeight: 1.5
                        }}
                    />
                </div>

                {/* Action Row */}
                <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
                    <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={submitting}
                        style={{
                            borderRadius: 20,
                            border: "none",
                            background: submitting ? "#94a3b8" : "#0f172a",
                            color: "#fff",
                            padding: "8px 20px",
                            fontSize: 13,
                            fontWeight: 600,
                            cursor: submitting ? "not-allowed" : "pointer",
                            boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                            transition: "all 0.2s"
                        }}
                    >
                        {submitting ? "Generating..." : "Generate Article →"}
                    </button>
                </div>
            </div>
        </div>
    );
};
