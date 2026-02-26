import { React } from "../../hooks";
import type { ArticleWorkflowProps, WorkflowNode } from "../../types";
import { TargetIcon, TreeIcon, DocIcon } from "../common/Icons";
import "../../styles.css";

export const ArticleWorkflowCard: React.FC<ArticleWorkflowProps> = (props) => {
    const status = props.status || "running";
    const rawNodes = props.flow_node_list || [];

    // Helper: check if a node is "done" (case-insensitive, multiple status values)
    const isNodeDone = (node: WorkflowNode): boolean => {
        const st = ((node as any).node_status || (node as any).status || "").toLowerCase();
        return st === "done" || st === "success" || st === "completed" || st === "succeeded";
    };

    // Helper: check if a node is "running"
    const isNodeRunning = (node: WorkflowNode): boolean => {
        if (status === "done") return false;
        const st = ((node as any).node_status || (node as any).status || "").toLowerCase();
        return st === "running";
    };

    // Define the 4 expected workflow steps
    const defaultSteps = [
        { node_name: "Determine the topic", node_code: "topic", node_message: "Clearly define the core theme of the content, the target audience, the writing style, and the desired tone." },
        { node_name: "AI builds the content framework", node_code: "framework", node_message: "AI is deeply understanding your topic intent and automatically generating a logically rigorous and detailed structured outline for you." },
        { node_name: "Generate complete content", node_code: "content", node_message: "Within the established framework, AI will enrich the details and examples, ultimately outputting complete content that can be used directly or further optimized." },
        { node_name: "Workflow completed", node_code: "__completed__", node_message: "Workflow has been completed." }
    ];

    // Always show 4 steps - merge backend nodes by index
    const effectiveNodes: WorkflowNode[] = defaultSteps.map((defaultStep, idx) => {
        const backendNode = rawNodes[idx];
        if (backendNode) {
            return {
                node_name: backendNode.node_name || defaultStep.node_name,
                node_code: backendNode.node_code || defaultStep.node_code,
                node_status: backendNode.node_status || "pending",
                node_message: backendNode.node_message || defaultStep.node_message
            };
        }
        return { ...defaultStep, node_status: "pending" };
    });

    const renderIcon = (idx: number, isDone: boolean, isRunning: boolean) => {
        const color = isDone ? "#22c55e" : isRunning ? "#2563eb" : "#cbd5e1";
        if (idx === 0) return <TargetIcon color={color} />;
        if (idx === 1) return <TreeIcon color={color} />;
        return <DocIcon color={color} />;
    };

    const runningIdxFromStatus = effectiveNodes.findIndex((n) => isNodeRunning(n));
    const runningIdxFromCode =
        props.current_node && props.current_node !== "__completed__"
            ? effectiveNodes.findIndex((n) => n.node_code === props.current_node)
            : -1;
    const runningIdx = runningIdxFromStatus !== -1 ? runningIdxFromStatus : runningIdxFromCode;

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
                position: 'relative'
            }}
        >
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, fontSize: 20, fontWeight: 700, color: '#0f172a' }}>
                    <span style={{ fontSize: 26 }}>✨</span> AI is creating great content for you...
                </div>
            </div>

            {/* Workflow Steps */}
            <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 20, marginTop: 10 }}>
                {effectiveNodes.map((node, idx) => {
                    const isDone =
                        status === "done"
                            ? true
                            : isNodeDone(node) || (runningIdx !== -1 && idx < runningIdx);
                    const isRunning =
                        node.node_code === "__completed__"
                            ? false
                            : runningIdx !== -1
                                ? idx === runningIdx
                                : isNodeRunning(node);
                    const isPending = !isDone && !isRunning;

                    const stepIcon = renderIcon(idx, isDone, isRunning);

                    return (
                        <div
                            key={idx}
                            className="workflow-step"
                            style={{
                                display: 'flex',
                                gap: 24,
                                alignItems: 'flex-start',
                                opacity: isPending ? 0.35 : 1
                            }}
                        >
                            {/* Icon Column */}
                            <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', width: 44 }}>
                                <div style={{ zIndex: 1 }}>{stepIcon}</div>
                                {idx < effectiveNodes.length - 1 && (
                                    <div
                                        className="workflow-line"
                                        style={{
                                            position: 'absolute',
                                            top: 32,
                                            bottom: -20,
                                            width: 2,
                                            background: isDone ? "#22c55e" : "#f1f5f9",
                                            zIndex: 0
                                        }}
                                    />
                                )}
                            </div>

                            {/* Content Column */}
                            <div style={{ flex: 1, paddingTop: 4 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    {isDone ? (
                                        <div style={{ color: '#22c55e', transition: 'color 0.3s ease' }}>
                                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                                            </svg>
                                        </div>
                                    ) : (
                                        <div style={{
                                            width: 24,
                                            height: 24,
                                            borderRadius: 12,
                                            background: isRunning ? '#2563eb' : '#f1f5f9',
                                            color: isRunning ? '#fff' : '#94a3b8',
                                            fontSize: 12,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontWeight: 700,
                                            transition: 'background-color 0.3s ease, color 0.3s ease'
                                        }}>
                                            {idx + 1}
                                        </div>
                                    )}

                                    <h4 style={{
                                        margin: 0,
                                        fontSize: 16,
                                        fontWeight: 700,
                                        color: isRunning ? '#2563eb' : isDone ? '#22c55e' : '#1e293b',
                                        transition: 'color 0.3s ease'
                                    }}>
                                        {node.node_name}
                                        {isRunning && (
                                            <span style={{ marginLeft: 8, color: '#3b82f6' }}>
                                                <span className="pulse-dot">.</span>
                                                <span className="pulse-dot">.</span>
                                                <span className="pulse-dot">.</span>
                                            </span>
                                        )}
                                    </h4>
                                </div>

                                <p style={{ margin: '8px 0 0', fontSize: 13, color: '#64748b', lineHeight: 1.6 }}>
                                    {node.node_message}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Bottom Success Section */}
            {status === "done" && (
                <div
                    style={{
                        marginTop: 40,
                        background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)',
                        padding: 20,
                        borderRadius: 12,
                        border: '1px solid #bbf7d0',
                        animation: 'fadeIn 0.4s ease'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 18, fontWeight: 700, color: '#166534', marginBottom: 4 }}>
                                {props.result_topic || "Article Generated"}
                            </div>
                            <div style={{ fontSize: 13, color: '#16a34a' }}>Content generation completed successfully</div>
                        </div>
                        <div style={{
                            background: '#22c55e',
                            color: '#fff',
                            borderRadius: 100,
                            padding: '8px 16px',
                            fontSize: 13,
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6
                        }}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                            </svg>
                            Done
                        </div>
                    </div>

                    {(props.setup?.app_name || props.setup?.tone || props.setup?.format) && (
                        <div style={{ display: "flex", gap: 20, fontSize: 13, color: "#166534", paddingTop: 16, marginTop: 16, borderTop: '1px solid #bbf7d0' }}>
                            {props.setup?.app_name && <span><span style={{ opacity: 0.7 }}>App:</span> <span style={{ fontWeight: 600 }}>{props.setup.app_name}</span></span>}
                            {props.setup?.tone && <span><span style={{ opacity: 0.7 }}>Tone:</span> <span style={{ fontWeight: 600 }}>{props.setup.tone}</span></span>}
                            {props.setup?.format && <span><span style={{ opacity: 0.7 }}>Format:</span> <span style={{ fontWeight: 600 }}>{props.setup.format}</span></span>}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
