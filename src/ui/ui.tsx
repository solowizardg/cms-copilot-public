/// <reference path="./react-shim.d.ts" />
import * as React from "react";
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";

// react-shim 在部分环境下不包含 hooks 的类型声明，这里用 any 兜底避免 TS 报错
const useState = (React as any).useState as any;
const useEffect = (React as any).useEffect as any;

type IntentRouterProps = {
  status: "thinking" | "done" | "error";
  user_text?: string;
  intent?: string;
  route?: string;
  raw?: string;
  elapsed_s?: number | null;
  steps?: string[];
  active_step?: number;
  rag_status?: "running" | "done" | "error";
  rag_message?: string;
  hidden?: boolean;
  main_title?: string;
};

type RAGTabKey = "prep" | "generate";

type RAGTab = {
  key?: RAGTabKey;
  title?: string;
};

type RAGStep = {
  key?: string;
  title?: string;
  status?: "pending" | "running" | "done" | "error";
  message?: string;
};

type RAGWorkflowProps = {
  status: "running" | "done" | "error";
  session_id?: string | null;
  tabs?: RAGTab[];
  active_tab?: RAGTabKey;
  steps?: {
    prep?: RAGStep[];
    generate?: RAGStep[];
  };
  error_message?: string | null;
};

type WorkflowNode = {
  node_code?: string;
  node_name?: string;
  node_status?: string;
  node_message?: string;
};

type ArticleWorkflowProps = {
  status: "running" | "done" | "error";
  run_id?: string | null;
  thread_id?: string | null;
  current_node?: string | null;
  flow_node_list?: WorkflowNode[];
  error_message?: string | null;
  // Merged result fields
  result_topic?: string;
  result_url?: string;
  setup?: {
    app_name?: string;
    tone?: string;
    format?: string;
  };
};

type AppOption = {
  id?: string | number;
  name?: string;
  model_id?: string | number;
};

type ArticleClarifyProps = {
  status: "need_info" | "done" | "error";
  missing?: string[];
  question?: string;
  topic?: string;
  content_format?: string;
  target_audience?: string;
  tone?: string;
  tone_options?: string[];
  app_id?: string;
  app_name?: string;
  app_options?: AppOption[];
  model_id?: string;
};

type ArticleClarifySummaryProps = {
  status: "done" | "error";
  app_id?: string;
  app_name?: string;
  topic?: string;
  content_format?: string;
  target_audience?: string;
  tone?: string;
};

type MCPOption = {
  code?: string;
  name?: string;
  desc?: string;
};

type SEOTaskEvidence = {
  evidence_path?: string;
  value_summary?: string;
};

type SEOTask = {
  date?: string;
  day_of_week?: string;
  category?: string;
  issue_type?: string;
  title?: string;
  description?: string;
  impact?: number;
  difficulty?: number;
  severity?: string;
  requires_manual_confirmation?: boolean;
  workflow_id?: string;
  params?: Record<string, any>;
  evidence?: SEOTaskEvidence[];
  fix_action?: "article" | "link" | "none";
  fix_prompt?: string;
};

type SEOWeeklyPlanData = {
  site_id?: string;
  week_start?: string;
  week_end?: string;
  tasks?: SEOTask[];
};

type SEOPlannerProps = {
  status: "loading" | "done" | "error";
  step?: string;
  user_text?: string;
  steps?: string[];
  active_step?: number;
  tasks?: SEOWeeklyPlanData | null;
  error_message?: string | null;
};

// 添加全局 JSX 类型声明以解决构建/Lint 错误
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

type MCPWorkflowProps = {
  status: "select" | "confirm" | "running" | "done" | "cancelled" | "error" | "loading";
  title?: string;
  message?: string;
  options?: MCPOption[];
  selected?: MCPOption | null;
  recommended?: string | null;
  result?: string | null;
  company_name?: string | null;
  logo_url?: string | null;
  steps?: any[];
  plan_steps?: any[];
  active_step?: number;
  error_message?: string;
};

const cssText = `
  .lgui-card { 
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }
  .lgui-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
  }
  .lgui-spin { animation: lgui-spin 0.8s linear infinite; }
  @keyframes lgui-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  .lgui-btn-primary {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    transition: all 0.2s;
  }
  .lgui-btn-primary:hover {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
    transform: translateY(-1px);
  }
  .lgui-btn-primary:active { transform: translateY(0); }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  .gemini-loader {
    position: relative;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .gemini-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    padding: 2px;
    background: conic-gradient(from 0deg, #3b82f6, #ec4899, #eab308, #3b82f6);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
    animation: spin 1s linear infinite;
  }
  .gemini-star {
    color: #3b82f6;
    display: flex;
    align-items: center;
    justify-content: center;
  }
`;

const Badge: React.FC<{ children?: React.ReactNode; tone?: "slate" | "blue" | "green" | "red" }> = ({
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

const Spinner: React.FC = () => {
  return (
    <span
      className="lgui-spin"
      style={{
        display: "inline-block",
        width: 14,
        height: 14,
        borderRadius: "50%",
        border: "2px solid #e2e8f0",
        borderTopColor: "#3b82f6",
      }}
    />
  );
};

const IntentRouterCard: React.FC<IntentRouterProps> = (props) => {
  if (props.hidden) return null;

  const elapsedLabel = (() => {
    const s = props.elapsed_s ?? null;
    if (s == null || Number.isNaN(s)) return null;
    const total = Math.round(s);
    const m = Math.floor(total / 60);
    const r = total % 60;
    if (m > 0) return `Thinking ${m}m ${r}s`;
    return `Thinking ${r}s`;
  })();

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
      <style>{cssText}</style>
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

        {elapsedLabel ? (
          <div style={{ fontSize: 12, color: "#94a3b8" }}>
            {elapsedLabel.replace("Thinking ", "")}
          </div>
        ) : null}
      </div>
    </div>
  );
};



const ragTone = (s?: string) => {
  const st = String(s || "").toLowerCase();
  if (st === "running") return "blue";
  if (st === "done") return "green";
  if (st === "error") return "red";
  return "slate";
};

const ragLabel = (s?: string) => {
  const st = String(s || "").toLowerCase();
  if (st === "running") return "Retrieving";
  if (st === "done") return "Completed";
  if (st === "error") return "Failed";
  if (st === "pending") return "Pending";
  return st || "—";
};

const RAGWorkflowCard: React.FC<RAGWorkflowProps> = (props) => {
  const isRunning = props.status === "running";
  const isDone = props.status === "done";
  const isError = props.status === "error";

  const steps = props.steps || {};
  const prepSteps = (steps.prep || []) as RAGStep[];
  const genSteps = (steps.generate || []) as RAGStep[];
  const allSteps = [...prepSteps, ...genSteps].filter(
    (s) =>
      !["workflow", "analysis_language", "detect_language", "initialize"].includes(s.key || "") &&
      !["workflow", "analysis_language"].includes(s.title || "")
  );

  // Find current running step or last completed
  const currentStep = allSteps.find(s => s.status === "running") || allSteps[allSteps.length - 1];

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
      <style>{cssText}</style>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {/* Loader / Status Icon */}
        <div className="thinking-loader">
          <div
            className="thinking-ring"
            style={{
              animation: isRunning ? "spin 1s linear infinite" : "none",
              background: isRunning
                ? "conic-gradient(from 0deg, #3b82f6, #ec4899, #eab308, #3b82f6)"
                : isError ? "#ef4444" : "#22c55e",
              padding: 2,
            }}
          ></div>

          <div className="thinking-star" style={{ color: isRunning ? "#3b82f6" : isError ? "#ef4444" : "#22c55e" }}>
            {isDone ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            ) : isError ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
              </svg>
            )}
          </div>
        </div>

        {/* Content */}
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: "#1e293b" }}>
            {isRunning ? "Retrieving Knowledge..." : isError ? "Retrieval Failed" : "Knowledge Base Retrieval Completed"}
          </div>

          {/* Subtext: Current step or summary */}
          <div style={{ fontSize: 12, color: "#64748b" }}>
            {isRunning && currentStep
              ? `Processing: ${currentStep.title || currentStep.key}`
              : isDone
                ? "Relevant context retrieved"
                : "Waiting for tasks..."}
          </div>
        </div>

        <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>rag</div>
      </div>

      {/* Expanded details (only if running or error, usually) or just always show compactly? 
          User said "update UI in thinking position", "no need for new tab".
          Let's show step progress compactly below if it's running.
      */}
      {isRunning || isError ? (
        <div style={{ marginTop: 12, borderTop: "1px solid #f1f5f9", paddingTop: 8 }}>
          {allSteps.map((s, idx) => {
            const sRun = s.status === "running";
            const sDone = s.status === "done";
            if (!sRun && !sDone && s.status !== "error") return null; // Hide pending
            return (
              <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                <span style={{ color: sRun ? "#2563eb" : sDone ? "#10b981" : "#64748b", fontWeight: sRun ? 600 : 400 }}>
                  {s.title || s.key}
                </span>
                <span style={{ color: "#94a3b8" }}>{s.status}</span>
              </div>
            )
          })}
        </div>
      ) : null}

      {props.error_message ? (
        <div style={{ marginTop: 8, fontSize: 11, color: "#ef4444" }}>
          {props.error_message}
        </div>
      ) : null}
    </div>
  );
};

const TargetIcon = ({ color }: { color: string }) => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="20" cy="20" r="18" stroke={color} strokeWidth="2" />
    <circle cx="20" cy="20" r="12" stroke={color} strokeWidth="2" />
    <circle cx="20" cy="20" r="6" fill={color} />
    <path d="M20 2V6M20 34V38M2 20H6M34 20H38" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const TreeIcon = ({ color }: { color: string }) => (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 3V7M12 7L8 11M12 7L16 11M8 11V15L6 18M8 11V15L10 18M16 11V15L14 18M16 11V15L18 18" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="12" cy="7" r="1" fill={color} />
    <circle cx="8" cy="11" r="1" fill={color} />
    <circle cx="16" cy="11" r="1" fill={color} />
  </svg>
);

const DocIcon = ({ color }: { color: string }) => (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="3" width="14" height="18" rx="2" stroke={color} strokeWidth="2" />
    <path d="M9 7H15M9 11H15M9 15H12" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <circle cx="18" cy="6" r="4" fill="#fff" stroke={color} strokeWidth="2" />
    <path d="M16.5 6L17.5 7L19.5 5" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ArticleWorkflowCard: React.FC<ArticleWorkflowProps> = (props) => {
  const status = props.status || "running";
  const rawNodes = props.flow_node_list || [];

  // Helper: check if a node is "done" (case-insensitive, multiple status values)
  // When overall status is "done", only "__completed__" node turns green, others stay as-is
  const isNodeDone = (node: WorkflowNode, nodeCode?: string): boolean => {
    // When done, only the __completed__ node shows as green
    if (status === "done") {
      return nodeCode === "__completed__";
    }
    const st = ((node as any).node_status || (node as any).status || "").toLowerCase();
    return st === "done" || st === "success" || st === "completed" || st === "succeeded";
  };

  // Helper: check if a node is "running"
  const isNodeRunning = (node: WorkflowNode): boolean => {
    if (status === "done") return false; // Stop animation on completion
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

  // Always show 4 steps - merge backend nodes by index (keep original statuses)
  const effectiveNodes: WorkflowNode[] = defaultSteps.map((defaultStep, idx) => {
    // Use backend node if available
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
      <style>{`
        ${cssText}
        @keyframes pulse-dots {
          0% { opacity: 0.2; }
          50% { opacity: 1; }
          100% { opacity: 0.2; }
        }
        .pulse-dot {
          animation: pulse-dots 1.5s infinite;
          display: inline-block;
          font-weight: bold;
          vertical-align: middle;
        }
        .pulse-dot:nth-child(2) { animation-delay: 0.2s; }
        .pulse-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .workflow-step {
          transition: opacity 0.3s ease, color 0.3s ease;
        }
        .workflow-line {
          transition: background-color 0.3s ease;
        }
      `}</style>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, fontSize: 20, fontWeight: 700, color: '#0f172a' }}>
          <span style={{ fontSize: 26 }}>✨</span> AI is creating great content for you...
        </div>
      </div>

      {/* Workflow Steps */}
      <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 20, marginTop: 10 }}>
        {effectiveNodes.map((node, idx) => {
          const isDone = isNodeDone(node, node.node_code);
          const isRunning = isNodeRunning(node);
          const isPending = !isDone && !isRunning;

          // Icons logic
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

      {/* Bottom Success Section (replaces progress bar) */}
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

const ArticleClarifyCard: React.FC<ArticleClarifyProps> = (props) => {
  const streamCtx = useStreamContext?.() as any;

  // 发送消息的辅助函数（复制 MCPWorkflowCard 的实现，保证在 agent-chat-ui / Studio 都能工作）
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
        input.dispatchEvent(
          new KeyboardEvent("keypress", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true })
        );
        input.dispatchEvent(
          new KeyboardEvent("keyup", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true })
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
  const [submitting, setSubmitting] = useState(false);

  // 当后端在多轮中更新已收集字段时，自动带入到表单
  useEffect(() => setTopic(props.topic || ""), [props.topic]);
  useEffect(() => setContentFormat(props.content_format || ""), [props.content_format]);
  useEffect(() => setAudience(props.target_audience || ""), [props.target_audience]);
  useEffect(() => setTone(props.tone || ""), [props.tone]);
  useEffect(() => setAppId(props.app_id || ""), [props.app_id]);
  useEffect(() => setAppName(props.app_name || ""), [props.app_name]);
  useEffect(() => setModelId(props.model_id || ""), [props.model_id]);
  // 当后端推送了新一轮澄清/进入工作流后，解除按钮禁用
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

  const handleSubmit = () => {
    if (submitting) return;
    setSubmitting(true);
    const payload = {
      topic: topic || "",
      content_format: contentFormat || "",
      target_audience: audience || "",
      tone: tone || "",
      app_id: appId || "",
      app_name: appName || resolveAppName(appId) || "",
      model_id: modelId || resolveModelId(appId) || "",
    };
    const payloadJson = JSON.stringify(payload);

    // 构造语义化文本（给用户看）
    const displayContent =
      `I've updated the article parameters:\n` +
      `\n- **Topic**: ${payload.topic}` +
      `\n- **Format**: ${payload.content_format}` +
      `\n- **Audience**: ${payload.target_audience}` +
      `\n- **Tone**: ${payload.tone}`;

    // Generative UI 推荐：直接通过 useStreamContext().submit() 继续对话
    if (streamCtx && typeof streamCtx.submit === "function") {
      const newMessage = {
        role: "assistant", // Use assistant role to trigger Markdown rendering in frontend
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

    // 兜底：无法 submit 时，仍然使用 hidden JSON 方式（以防万一）
    // 但在支持 submit 的环境下，上面的代码会优先执行
    const fallbackContent = displayContent + `\n\n<!-- ${payloadJson} -->`;
    sendMessage(fallbackContent);
  };

  return (
    <div
      className="lgui-card"
      style={{
        borderRadius: 12,
        // Removed heavy card borders/shadows for "embedded" feel
        border: "none",
        background: "transparent",
        padding: "4px 0",
        fontSize: 13,
        maxWidth: 600,
      }}
    >
      <style>{cssText}</style>

      {/* Simplified Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a" }}>
          I need a few more details to continue:
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {/* Row 1: App Name & Tone */}
        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 12, border: "1px solid #f1f5f9" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>App Name</div>
          <select
            value={appId}
            onChange={(e: any) => {
              const nextId = e.target.value;
              setAppId(nextId);
              setAppName(resolveAppName(nextId));
              setModelId(resolveModelId(nextId));
            }}
            style={{
              width: "100%",
              padding: "8px 0",
              borderRadius: 0,
              border: "none",
              borderBottom: "1px solid #cbd5e1",
              fontSize: 13,
              background: "transparent",
              color: "#334155",
              outline: "none"
            }}
          >
            <option value="">Select App...</option>
            {appOptions.map((opt, idx) => (
              <option key={`${opt.id || "app"}-${idx}`} value={String(opt.id || "")}>
                {opt.name || opt.id}
              </option>
            ))}
          </select>
        </div>

        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 12, border: "1px solid #f1f5f9" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>Content Tone</div>
          <select
            value={tone}
            onChange={(e: any) => setTone(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 0",
              borderRadius: 0,
              border: "none",
              borderBottom: "1px solid #cbd5e1",
              fontSize: 13,
              background: "transparent",
              color: "#334155",
              outline: "none"
            }}
          >
            <option value="">Select...</option>
            {toneOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>

        {/* Row 2: Content Format & Target Audience */}
        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 12, border: "1px solid #f1f5f9" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>Content Format</div>
          <input
            value={contentFormat}
            onChange={(e: any) => setContentFormat(e.target.value)}
            placeholder="e.g., News Center"
            style={{ width: "100%", padding: "8px 0", border: "none", borderBottom: "1px solid #cbd5e1", background: "transparent", fontSize: 13, outline: "none" }}
          />
        </div>

        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 12, border: "1px solid #f1f5f9" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>Target Audience</div>
          <input
            value={audience}
            onChange={(e: any) => setAudience(e.target.value)}
            placeholder="e.g., Readers"
            style={{ width: "100%", padding: "8px 0", border: "none", borderBottom: "1px solid #cbd5e1", background: "transparent", fontSize: 13, outline: "none" }}
          />
        </div>

        {/* Row 3: Topic (Full Width) */}
        <div style={{ gridColumn: "1 / -1", background: "#f8fafc", padding: 12, borderRadius: 12, border: "1px solid #f1f5f9" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>Topic</div>
          <input
            value={topic}
            onChange={(e: any) => setTopic(e.target.value)}
            placeholder="e.g., Company releases 2026 headphones"
            style={{ width: "100%", padding: "8px 0", border: "none", borderBottom: "1px solid #cbd5e1", background: "transparent", fontSize: 13, outline: "none" }}
          />
        </div>

        {/* Action Row */}
        <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            style={{
              borderRadius: 20, // Pill shape
              border: "none",
              background: submitting ? "#94a3b8" : "#0f172a", // Dark button
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

const ArticleClarifySummaryCard: React.FC<ArticleClarifySummaryProps> = (props) => {
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
      <style>{cssText}</style>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        {/* 左侧状态圆环 */}
        <div style={{ paddingTop: 2 }}>
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: "50%",
              border: "4px solid #bbf7d0", // ring-green-200
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

          {/* 链接卡片 (模拟 Top US Photovoltaic Brands...) */}
          <div style={{
            marginTop: 12,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid #e2e8f0', // border-slate-200
            background: '#fff',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
            onMouseOver={(e) => e.currentTarget.style.background = '#f8fafc'}
            onMouseOut={(e) => e.currentTarget.style.background = '#fff'}
          >
            <span style={{ fontSize: 16 }}>🌐</span>
            <span style={{ color: '#2563eb', fontWeight: 500, textDecoration: 'none' }}>
              {props.topic || "Untitled Article"}
            </span>
            <Badge tone="slate">View</Badge>
          </div>

          {/* 标签式信息展示 (Published Setup: Application Blog ...) */}
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

const MCPWorkflowCard: React.FC<MCPWorkflowProps> = (props) => {
  const status = props.status || "loading";
  const title = props.title || "Background Operation";
  const steps = props.steps || props.plan_steps || [];
  const activeStep = props.active_step || 1;

  // 发送消息的辅助函数
  const sendMessage = (text: string) => {
    const win = window as any;
    const globalFns = ["__LANGGRAPH_SEND_MESSAGE__", "__LANGGRAPH_SEND__", "sendMessage", "sendChatMessage"];
    for (const fn of globalFns) {
      if (typeof win[fn] === "function") { try { win[fn](text); return; } catch { } }
    }
    window.dispatchEvent(new CustomEvent("langgraph:send", { detail: { text } }));
    const selectors = ['textarea', 'input[type="text"]'];
    for (const sel of selectors) {
      const input = document.querySelector(sel) as HTMLInputElement | HTMLTextAreaElement | null;
      if (!input) continue;
      const proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
      if (setter) setter.call(input, text); else input.value = text;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      setTimeout(() => {
        const form = input.closest("form");
        const submitBtn = form?.querySelector('button[type="submit"]') || form?.querySelector('button:not([type="button"])') || document.querySelector('button[type="submit"]');
        if (submitBtn) { (submitBtn as HTMLButtonElement).click(); return; }
        if (form) { if (form.requestSubmit) form.requestSubmit(); else form.submit(); return; }
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
      }, 50);
      return;
    }
  };

  // 恢复 interrupt 的函数
  const resumeInterrupt = (value: any) => {
    const win = window as any;
    if (typeof win.__LANGGRAPH_RESUME__ === "function") { try { win.__LANGGRAPH_RESUME__(value); return; } catch { } }
    const resumeFns = ["resumeThread", "resume", "sendResume"];
    for (const fn of resumeFns) { if (typeof win[fn] === "function") { try { win[fn](value); return; } catch { } } }
    window.dispatchEvent(new CustomEvent("langgraph:resume", { detail: value }));
    sendMessage(value?.confirmed ? "Confirmed" : "Cancelled");
  };

  const handleConfirm = () => resumeInterrupt({ confirmed: true, action: "approve" });
  const handleCancel = () => resumeInterrupt({ confirmed: false, action: "cancel" });

  const renderIcon = (idx: number, isDone: boolean, isRunning: boolean) => {
    const color = isDone ? "#22c55e" : isRunning ? "#2563eb" : "#cbd5e1";
    if (isDone) return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
    );
    if (isRunning) return <Spinner />;
    return <div style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />;
  };

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
      <style>{`
        ${cssText}
        @keyframes pulse-dots { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }
        .pulse-dot { animation: pulse-dots 1.5s infinite; display: inline-block; }
        .pulse-dot:nth-child(2) { animation-delay: 0.2s; }
        .pulse-dot:nth-child(3) { animation-delay: 0.4s; }
        .workflow-step { transition: opacity 0.3s ease; }
      `}</style>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, fontSize: 18, fontWeight: 700, color: '#0f172a' }}>
          <span style={{ fontSize: 24 }}>🛠️</span> {title}
        </div>
        {props.status === "done" && (
          <div style={{ marginTop: 4, fontSize: 12, color: "#16a34a", fontWeight: 600 }}>Operation Completed</div>
        )}
      </div>

      {/* Steps List */}
      {steps.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 20 }}>
          {steps.map((step: any, idx: number) => {
            const isDone = (status === "done" || status === "cancelled") ? true : idx + 1 < activeStep;
            const isRunning = (status !== "done" && status !== "cancelled") && idx + 1 === activeStep;
            return (
              <div key={idx} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', opacity: idx + 1 > activeStep ? 0.5 : 1 }}>
                <div style={{ marginTop: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24 }}>
                  {renderIcon(idx, isDone, isRunning)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: isRunning ? "#2563eb" : "#1e293b" }}>
                    {step.title || step.name || `Step ${idx + 1}`}
                    {isRunning && (
                      <span style={{ marginLeft: 6, color: '#3b82f6' }}>
                        <span className="pulse-dot">.</span><span className="pulse-dot">.</span><span className="pulse-dot">.</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Current Message / Log */}
      {props.message && props.status !== "done" && (
        <div style={{ marginTop: 12, borderRadius: 8, background: "#f8fafc", padding: 12, border: "1px solid #e2e8f0", fontSize: 12, color: "#334155" }}>
          {props.message}
        </div>
      )}

      {/* Options Selection (e.g. for Tool Selection if needed, though rarely used in shortcut v2) */}
      {props.options && props.options.length > 0 && (
        <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
          {props.options.map((o, idx) => (
            <button
              key={idx}
              onClick={props.status === "select" ? () => sendMessage(String(idx + 1)) : undefined}
              style={{
                textAlign: 'left',
                padding: '10px 14px',
                borderRadius: 8,
                border: '1px solid #e2e8f0',
                background: '#fff',
                cursor: props.status === "select" ? 'pointer' : 'default',
                fontSize: 13
              }}
            >
              <b>{idx + 1}. {o.name || o.code}</b> <span style={{ color: '#64748b' }}> - {o.desc}</span>
            </button>
          ))}
        </div>
      )}

      {/* Confirmation Actions */}
      {props.status === "confirm" && (
        <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
          <button
            onClick={handleConfirm}
            style={{
              flex: 1, padding: "10px", borderRadius: 8, border: "none",
              background: "#2563eb", color: "#fff", fontWeight: 600, cursor: "pointer"
            }}
          >
            Confirmed & Execute
          </button>
          <button
            onClick={handleCancel}
            style={{
              flex: 1, padding: "10px", borderRadius: 8, border: "1px solid #e2e8f0",
              background: "#fff", color: "#64748b", fontWeight: 600, cursor: "pointer"
            }}
          >
            Cancel
          </button>
        </div>
      )}

      {/* Result Output */}
      {props.result && (
        <div style={{ marginTop: 16, padding: 12, background: "#ecfdf5", borderRadius: 8, border: "1px solid #bbf7d0", fontSize: 12, color: "#065f46", whiteSpace: "pre-wrap" }}>
          {props.result}
        </div>
      )}

      {/* Error Output */}
      {props.error_message && (
        <div style={{ marginTop: 16, padding: 12, background: "#fff1f2", borderRadius: 8, border: "1px solid #fecdd3", fontSize: 12, color: "#9f1239" }}>
          {props.error_message}
        </div>
      )}

    </div>
  );
};

const severityColor = (s?: string) => {
  if (s === "critical") return { bg: "#fef2f2", fg: "#dc2626", bd: "#fecaca" };
  if (s === "warning") return { bg: "#fffbeb", fg: "#d97706", bd: "#fde68a" };
  return { bg: "#f0fdf4", fg: "#16a34a", bd: "#bbf7d0" };
};

const categoryColor = (c?: string) => {
  const colors: Record<string, { bg: string; fg: string }> = {
    Indexing: { bg: "#dbeafe", fg: "#1d4ed8" },
    OnPage: { bg: "#fef3c7", fg: "#b45309" },
    Performance: { bg: "#fce7f3", fg: "#be185d" },
    Content: { bg: "#d1fae5", fg: "#047857" },
    StructuredData: { bg: "#e0e7ff", fg: "#4338ca" },
  };
  return colors[c || ""] || { bg: "#f1f5f9", fg: "#64748b" };
};

const SEOPlannerCard: React.FC<SEOPlannerProps> = (props) => {
  const badgeTone = props.status === "done" ? "green" : props.status === "error" ? "red" : "blue";
  const badgeLabel = props.status === "done" ? "Completed" : props.status === "error" ? "Failed" : "Analyzing";
  const tasks = props.tasks?.tasks || [];
  const steps = props.steps || [];

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
        maxWidth: 640,
      }}
    >
      <style>{cssText}</style>

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>SEO Weekly Plan</div>
          <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <Badge tone={badgeTone as any}>
              {props.status === "loading" ? <Spinner /> : null}
              <span>{badgeLabel}</span>
            </Badge>
            {props.tasks?.week_start && props.tasks?.week_end ? (
              <span style={{ fontSize: 11, color: "#64748b" }}>
                {props.tasks.week_start} ~ {props.tasks.week_end}
              </span>
            ) : null}
          </div>
        </div>
        <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>seo</div>
      </div>

      {/* 进度步骤 */}
      {props.status === "loading" && steps.length > 0 ? (
        <div style={{ marginTop: 12, borderRadius: 12, border: "1px solid #f1f5f9", background: "#f8fafc", padding: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>Analysis Progress</div>
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
                      flex: "0 0 auto",
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
      ) : null}

      {/* 任务列表 */}
      {props.status === "done" && tasks.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>
            Weekly Tasks ({tasks.length})
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            {tasks.map((task, idx) => {
              const sev = severityColor(task.severity);
              const cat = categoryColor(task.category);
              return (
                <div
                  key={idx}
                  style={{
                    borderRadius: 10,
                    border: `1px solid ${sev.bd}`,
                    background: "#ffffff",
                    padding: 12,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: 4,
                            fontSize: 10,
                            fontWeight: 600,
                            background: cat.bg,
                            color: cat.fg,
                          }}
                        >
                          {task.category}
                        </span>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: 4,
                            fontSize: 10,
                            fontWeight: 600,
                            background: sev.bg,
                            color: sev.fg,
                          }}
                        >
                          {task.severity}
                        </span>
                        {task.requires_manual_confirmation ? (
                          <span style={{ fontSize: 10, color: "#dc2626" }}>⚠ Confirm</span>
                        ) : null}
                      </div>
                      <div style={{ marginTop: 6, fontSize: 13, fontWeight: 600, color: "#0f172a" }}>
                        {task.title}
                      </div>
                      <div style={{ marginTop: 4, fontSize: 12, color: "#64748b" }}>
                        {task.description}
                      </div>
                    </div>
                    <div style={{ textAlign: "right", flex: "0 0 auto" }}>
                      <div style={{ fontSize: 11, color: "#64748b" }}>{task.date}</div>
                      <div style={{ fontSize: 10, color: "#94a3b8" }}>{task.day_of_week}</div>
                    </div>
                  </div>
                  <div style={{ marginTop: 8, display: "flex", gap: 12, fontSize: 11, color: "#64748b" }}>
                    <span>Impact: {"★".repeat(task.impact || 0)}{"☆".repeat(5 - (task.impact || 0))}</span>
                    <span>Difficulty: {"★".repeat(task.difficulty || 0)}{"☆".repeat(5 - (task.difficulty || 0))}</span>
                  </div>
                  {task.evidence?.length ? (
                    <details style={{ marginTop: 8 }}>
                      <summary style={{ cursor: "pointer", fontSize: 11, color: "#64748b" }}>
                        View Evidence ({task.evidence.length})
                      </summary>
                      <div style={{ marginTop: 6, fontSize: 11, color: "#475569" }}>
                        {task.evidence.map((ev, evIdx) => (
                          <div key={evIdx} style={{ marginTop: 4 }}>
                            <code style={{ background: "#f1f5f9", padding: "1px 4px", borderRadius: 3, fontSize: 10 }}>
                              {ev.evidence_path}
                            </code>
                            <span style={{ marginLeft: 6 }}>{ev.value_summary}</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  ) : null}

                  {/* 修复按钮 */}
                  <div style={{ marginTop: 10, display: "flex", justifyContent: "flex-end" }}>
                    {task.fix_action === "article" ? (
                      <button
                        style={{
                          padding: "6px 12px",
                          borderRadius: 6,
                          border: "none",
                          background: "#3b82f6",
                          color: "#ffffff",
                          fontSize: 12,
                          fontWeight: 600,
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                        data-action="article"
                        data-prompt={task.fix_prompt || task.title}
                        onClick={() => {
                          // 直接使用 fix_prompt 作为完整的需求描述
                          const chatMessage = task.fix_prompt || `针对"${task.title}"问题，创建相关内容进行优化。`;

                          // 方式1: 触发自定义事件（供外部监听）
                          const event = new CustomEvent("copilot:send", {
                            detail: {
                              message: chatMessage,
                              intent: "article_task",
                              task_info: {
                                issue_type: task.issue_type,
                                category: task.category,
                                title: task.title,
                              }
                            }
                          });
                          window.dispatchEvent(event);

                          // 方式2: 尝试找到 LangGraph Studio 的输入框并提交
                          try {
                            // 查找输入框（LangGraph Studio 使用 textarea）
                            const textarea = document.querySelector('textarea[placeholder*="input"], textarea[name="input"], form textarea') as HTMLTextAreaElement;
                            if (textarea) {
                              // 设置输入框的值
                              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
                              if (nativeInputValueSetter) {
                                nativeInputValueSetter.call(textarea, chatMessage);
                              } else {
                                textarea.value = chatMessage;
                              }
                              // 触发 input 事件让 React 感知变化
                              textarea.dispatchEvent(new Event('input', { bubbles: true }));

                              // 查找并点击提交按钮
                              const form = textarea.closest('form');
                              const submitBtn = form?.querySelector('button[type="submit"]') || document.querySelector('button[aria-label*="Submit"], button[aria-label*="send"]');
                              if (submitBtn) {
                                setTimeout(() => (submitBtn as HTMLButtonElement).click(), 100);
                              }
                            }
                          } catch (e) {
                            console.log('[SEO] 自动填充失败，请手动输入:', chatMessage);
                          }
                        }}
                      >
                        <span>✏️</span>
                        <span>Generate Content</span>
                      </button>
                    ) : (
                      <a
                        href="#"
                        style={{
                          padding: "6px 12px",
                          borderRadius: 6,
                          border: "1px solid #e2e8f0",
                          background: "#f8fafc",
                          color: "#64748b",
                          fontSize: 12,
                          fontWeight: 600,
                          textDecoration: "none",
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                        onClick={(e) => e.preventDefault()}
                      >
                        <span>🔧</span>
                        <span>Fix</span>
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* 错误信息 */}
      {props.status === "error" && props.error_message ? (
        <div
          style={{
            marginTop: 12,
            borderRadius: 12,
            border: "1px solid #fecdd3",
            background: "#fff1f2",
            padding: 12,
            fontSize: 12,
            color: "#9f1239",
          }}
        >
          {props.error_message}
        </div>
      ) : null}
    </div>
  );
};

// ============ 站点报告组件 ============

type SiteReportProps = {
  status: "loading" | "done" | "error";
  step?: string;
  user_text?: string;
  message?: string;
  steps?: string[];
  active_step?: number;
  report?: {
    site_id?: string;
    report_type?: "overview" | "traffic" | "content" | "engagement" | "performance";
    report_type_name?: string;
    summary?: {
      total_visits?: number;
      total_unique_visitors?: number;
      total_page_views?: number;
      avg_session_duration?: number;
      bounce_rate?: number;
      pages_per_session?: number;
    } | null;
    charts?: {
      // 图表由外部前端项目的组件渲染，这里不再定义强约束结构
      daily_visits?: any;
      traffic_sources?: any;
      top_pages?: any;
      device_stats?: any;
      user_engagement?: any;
    };
    data_quality?: {
      notes?: string[];
      warnings?: string[];
      window_days?: number | null;
      property_id?: string | null;
    } | null;
    insights?: {
      one_liner?: string;
      evidence?: string[];
      hypotheses?: { text?: string; confidence?: "high" | "medium" | "low"; next_step?: string }[];
    } | null;
    actions?: {
      id?: string;
      title?: string;
      why?: string;
      effort?: "low" | "medium" | "high";
      impact?: "low" | "medium" | "high";
      success_metric?: { metric?: string; window_days?: number; target?: string };
    }[] | null;
    todos?: {
      id?: string;
      title?: string;
      description?: string;
      success_metric?: { metric?: string; window_days?: number; target?: string };
    }[] | null;
    trace?: {
      todo_summary?: string;
      used_todos?: string[];
    } | null;
    step_outputs?: { step?: string; result?: string; evidence_ref?: string | null }[] | null;
    content?: {
      total_articles?: number;
      published_this_week?: number;
      draft_count?: number;
      scheduled_count?: number;
    } | null;
    performance?: {
      avg_load_time_ms?: number;
      lcp_ms?: number;
      fid_ms?: number;
      cls?: number;
      ttfb_ms?: number;
      uptime_percentage?: number;
      error_rate?: number;
    } | null;
  } | null;
  error_message?: string | null;
};

// 报告类型图标和颜色
const reportTypeStyles: Record<string, { icon: string; color: string; bg: string }> = {
  overview: { icon: "📊", color: "#3b82f6", bg: "linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%)" },
  traffic: { icon: "📈", color: "#10b981", bg: "linear-gradient(135deg, #ecfdf5 0%, #f0fdfa 100%)" },
  content: { icon: "📝", color: "#8b5cf6", bg: "linear-gradient(135deg, #f5f3ff 0%, #faf5ff 100%)" },
  engagement: { icon: "💬", color: "#f59e0b", bg: "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)" },
  performance: { icon: "⚡", color: "#ef4444", bg: "linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%)" },
};


// ========== 图表分析卡片（单独显示每个图表的 LLM 分析结果）==========
type ChartAnalysisProps = {
  chart_key?: string;
  chart_title?: string;
  chart_type?: string;
  description?: string;
};

const ChartAnalysisCard: React.FC<ChartAnalysisProps> = (props) => {
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
      <style>{cssText}</style>
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

// ========== 图表分析加载提示 ==========
type ChartAnalysisLoadingProps = {
  chart_key?: string;
  chart_title?: string;
  hidden?: boolean;
};

const ChartAnalysisLoadingCard: React.FC<ChartAnalysisLoadingProps> = (props) => {
  // 兜底：只在显式 hidden===false 时显示，避免回放/补发时因缺字段而“误显示”
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
      <style>{cssText}</style>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span>⏳</span>
        <div style={{ fontWeight: 600 }}>Processing {title} …</div>
      </div>
    </div>
  );
};

// 站点报告卡片
const SiteReportCard: React.FC<SiteReportProps> = (props) => {
  const badgeTone = props.status === "done" ? "green" : props.status === "error" ? "red" : "blue";
  const badgeLabel = props.status === "done" ? "Completed" : props.status === "error" ? "Failed" : "Generating";
  const steps = props.steps || [];
  const report = props.report;
  const summary = report?.summary;
  const dataQuality = report?.data_quality || null;
  const insights = report?.insights || null;
  const actions = report?.actions || null;
  const todos = report?.todos || null;
  const trace = report?.trace || null;
  const stepOutputs = report?.step_outputs || null;
  const reportType = report?.report_type || "overview";
  const reportTypeName = report?.report_type_name || "Overview";
  const typeStyle = reportTypeStyles[reportType] || reportTypeStyles.overview;

  // [New] 获取所有图表 key
  const chartKeys = report?.charts ? Object.keys(report.charts) : [];

  return (
    <div
      className="lgui-card"
      style={{
        borderRadius: 14,
        border: "1px solid #e2e8f0",
        background: "#ffffff",
        padding: 14,
        fontSize: 13,
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.06)",
        maxWidth: 720,
      }}
    >
      <style>{cssText}</style>

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>
            {typeStyle.icon} {reportTypeName}报告
          </div>
          <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <Badge tone={badgeTone as any}>
              {props.status === "loading" ? <Spinner /> : null}
              <span>{badgeLabel}</span>
            </Badge>
            {report?.site_id ? (
              <span style={{ fontSize: 11, color: "#64748b" }}>Site: {report.site_id}</span>
            ) : null}
            {props.status === "done" && reportType !== "overview" ? (
              <span
                style={{
                  fontSize: 10,
                  padding: "2px 6px",
                  borderRadius: 4,
                  background: typeStyle.color + "15",
                  color: typeStyle.color,
                  fontWeight: 600,
                }}
              >
                {reportTypeName}
              </span>
            ) : null}
          </div>
        </div>
        <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>report</div>
      </div>

      {/* 进度步骤 */}
      {props.status === "loading" && steps.length > 0 ? (
        <div style={{ marginTop: 12, borderRadius: 12, border: "1px solid #f1f5f9", background: "#f8fafc", padding: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>Generation Progress</div>
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
                      flex: "0 0 auto",
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
      ) : null}

      {/* 生成过程提示 */}
      {props.status === "loading" && props.message ? (
        <div
          style={{
            marginTop: 12,
            borderRadius: 12,
            border: "1px solid #bfdbfe",
            background: "#eff6ff",
            padding: 12,
            fontSize: 12,
            color: "#1e3a8a",
            whiteSpace: "pre-wrap",
          }}
        >
          {props.message}
        </div>
      ) : null}

      {/* 概览指标 - 流量相关 */}
      {props.status === "done" && summary && (reportType === "overview" || reportType === "traffic") ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>📈 Traffic Metrics</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 10,
              padding: 12,
              background: typeStyle.bg,
              borderRadius: 12,
              border: "1px solid #e2e8f0",
            }}
          >
            {summary.total_visits != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#1d4ed8" }}>
                  {(summary.total_visits || 0).toLocaleString()}
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Total Visits</div>
              </div>
            ) : null}
            {summary.total_unique_visitors != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#047857" }}>
                  {(summary.total_unique_visitors || 0).toLocaleString()}
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Unique Visitors</div>
              </div>
            ) : null}
            {summary.total_page_views != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#7c3aed" }}>
                  {(summary.total_page_views || 0).toLocaleString()}
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Page Views</div>
              </div>
            ) : null}
            {summary.avg_session_duration != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#334155" }}>
                  {Math.floor((summary.avg_session_duration || 0) / 60)}m{(summary.avg_session_duration || 0) % 60}s
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Avg Duration</div>
              </div>
            ) : null}
            {summary.bounce_rate != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#334155" }}>{summary.bounce_rate || 0}%</div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Bounce Rate</div>
              </div>
            ) : null}
            {summary.pages_per_session != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#334155" }}>{summary.pages_per_session || 0}</div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Pages/Session</div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* 互动指标 - engagement 类型专用 */}
      {props.status === "done" && summary && reportType === "engagement" ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>💬 Engagement Metrics</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 10,
              padding: 12,
              background: typeStyle.bg,
              borderRadius: 12,
              border: "1px solid #e2e8f0",
            }}
          >
            {summary.avg_session_duration != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: typeStyle.color }}>
                  {Math.floor((summary.avg_session_duration || 0) / 60)}m{(summary.avg_session_duration || 0) % 60}s
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Avg Stay</div>
              </div>
            ) : null}
            {summary.bounce_rate != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: typeStyle.color }}>{summary.bounce_rate || 0}%</div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Bounce Rate</div>
              </div>
            ) : null}
            {summary.pages_per_session != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: typeStyle.color }}>{summary.pages_per_session || 0}</div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Pages/Session</div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* 性能指标 - performance 类型专用 */}
      {props.status === "done" && report?.performance && (reportType === "overview" || reportType === "performance") ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>⚡ Performance Metrics</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: reportType === "performance" ? "repeat(4, 1fr)" : "repeat(3, 1fr)",
              gap: 10,
              padding: 12,
              background: reportType === "performance" ? typeStyle.bg : "#f8fafc",
              borderRadius: 12,
              border: "1px solid #e2e8f0",
            }}
          >
            {report.performance.avg_load_time_ms != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: report.performance.avg_load_time_ms > 2000 ? "#ef4444" : "#10b981" }}>
                  {(report.performance.avg_load_time_ms / 1000).toFixed(2)}s
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Load Time</div>
              </div>
            ) : null}
            {report.performance.lcp_ms != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: report.performance.lcp_ms > 2500 ? "#ef4444" : "#10b981" }}>
                  {(report.performance.lcp_ms / 1000).toFixed(2)}s
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>LCP</div>
              </div>
            ) : null}
            {report.performance.fid_ms != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: report.performance.fid_ms > 100 ? "#f59e0b" : "#10b981" }}>
                  {report.performance.fid_ms}ms
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>FID</div>
              </div>
            ) : null}
            {report.performance.cls != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: report.performance.cls > 0.1 ? "#f59e0b" : "#10b981" }}>
                  {report.performance.cls}
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>CLS</div>
              </div>
            ) : null}
            {report.performance.uptime_percentage != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#10b981" }}>
                  {report.performance.uptime_percentage}%
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Uptime</div>
              </div>
            ) : null}
            {report.performance.error_rate != null ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: report.performance.error_rate > 1 ? "#ef4444" : "#10b981" }}>
                  {report.performance.error_rate}%
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Error Rate</div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* [New] 图表分析区域：循环展示图表及分析 */}
      {chartKeys.length > 0 ? (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>📊 Key Trends</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {chartKeys.map((key) => {
              const chart = report?.charts?.[key];
              return chart ? (
                <div key={key}>
                  <ChartAnalysisCard
                    chart_key={key}
                    chart_title={chart.title}
                    chart_type={chart.chart_type}
                    description={chart.description}
                  />
                </div>
              ) : null;
            })}
          </div>
        </div>
      ) : null}
      {/* 数据质量提示（允许在 loading 阶段展示阶段性结果） */}
      {props.status !== "error" && dataQuality && (dataQuality.warnings?.length || dataQuality.notes?.length) ? (
        <div style={{ marginTop: 12 }}>
          <div
            style={{
              borderRadius: 12,
              border: "1px solid #e2e8f0",
              background: "#f8fafc",
              padding: 12,
              fontSize: 12,
              color: "#334155",
            }}
          >
            {dataQuality.warnings?.length ? (
              <div style={{ marginBottom: dataQuality.notes?.length ? 10 : 0 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#9f1239", marginBottom: 6 }}>Warnings</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {dataQuality.warnings.map((w, idx) => (
                    <li key={idx} style={{ marginTop: idx ? 4 : 0 }}>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {dataQuality.notes?.length ? (
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 6 }}>Notes</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {dataQuality.notes.map((n, idx) => (
                    <li key={idx} style={{ marginTop: idx ? 4 : 0 }}>
                      {n}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* 分析轨迹（基于 Todo 步骤） */}
      {props.status !== "error" && trace && (trace.todo_summary || (trace.used_todos && trace.used_todos.length)) ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>🧭 Analysis Trace</div>
          <div
            style={{
              borderRadius: 12,
              border: "1px solid #e2e8f0",
              background: "#ffffff",
              padding: 12,
              fontSize: 12,
              color: "#334155",
            }}
          >
            {trace.todo_summary ? <div style={{ fontWeight: 600 }}>{trace.todo_summary}</div> : null}
            {trace.used_todos?.length ? (
              <ul style={{ margin: "10px 0 0 0", paddingLeft: 18 }}>
                {trace.used_todos.map((t, idx) => (
                  <li key={idx} style={{ marginTop: idx ? 4 : 0 }}>
                    {t}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* 逐步产出（每个 Todo 步骤的具体结果） */}
      {props.status !== "error" && stepOutputs && stepOutputs.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>🧾 Step Outputs</div>
          <div style={{ display: "grid", gap: 8 }}>
            {stepOutputs.map((s, idx) => (
              <div
                key={idx}
                style={{
                  borderRadius: 12,
                  border: "1px solid #e2e8f0",
                  background: "#ffffff",
                  padding: 12,
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>
                  {idx + 1}. {s.step || "—"}
                </div>
                {s.result ? (
                  <div style={{ marginTop: 6, fontSize: 12, color: "#334155", whiteSpace: "pre-wrap" }}>{s.result}</div>
                ) : null}
                {s.evidence_ref ? (
                  <div style={{ marginTop: 6, fontSize: 11, color: "#64748b" }}>Evidence Ref: {s.evidence_ref}</div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* 解读与洞察 */}
      {props.status !== "error" && insights && (insights.one_liner || insights.evidence?.length || insights.hypotheses?.length) ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>🔎 Insights</div>
          <div
            style={{
              borderRadius: 12,
              border: "1px solid #e2e8f0",
              background: "#ffffff",
              padding: 12,
            }}
          >
            {insights.one_liner ? (
              <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a" }}>{insights.one_liner}</div>
            ) : null}
            {insights.evidence?.length ? (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 6 }}>Evidence</div>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "#334155" }}>
                  {insights.evidence.map((e, idx) => (
                    <li key={idx} style={{ marginTop: idx ? 4 : 0 }}>
                      {e}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {insights.hypotheses?.length ? (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 6 }}>Hypotheses (To Verify)</div>
                <div style={{ display: "grid", gap: 8 }}>
                  {insights.hypotheses.map((h, idx) => (
                    <div
                      key={idx}
                      style={{
                        borderRadius: 10,
                        border: "1px solid #f1f5f9",
                        background: "#f8fafc",
                        padding: 10,
                        fontSize: 12,
                        color: "#334155",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                        <div style={{ fontWeight: 600 }}>{h.text || "—"}</div>
                        {h.confidence ? <span style={{ fontSize: 11, color: "#64748b" }}>{h.confidence}</span> : null}
                      </div>
                      {h.next_step ? (
                        <div style={{ marginTop: 4, fontSize: 11, color: "#64748b" }}>Verify: {h.next_step}</div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* 建议动作（仅展示） */}
      {props.status !== "error" && actions && actions.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>✅ Suggested Actions</div>
          <div style={{ display: "grid", gap: 8 }}>
            {actions.map((a, idx) => (
              <div
                key={a.id || idx}
                style={{
                  borderRadius: 12,
                  border: "1px solid #e2e8f0",
                  background: "#ffffff",
                  padding: 12,
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a" }}>{a.title || "—"}</div>
                {a.why ? <div style={{ marginTop: 6, fontSize: 12, color: "#334155" }}>{a.why}</div> : null}
                {(a.impact || a.effort || a.success_metric?.metric) ? (
                  <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {a.impact ? <Badge tone="green">impact: {a.impact}</Badge> : null}
                    {a.effort ? <Badge tone="slate">effort: {a.effort}</Badge> : null}
                    {a.success_metric?.metric ? (
                      <Badge tone="blue">
                        metric: {a.success_metric.metric}
                        {a.success_metric.window_days ? ` (${a.success_metric.window_days}d)` : ""}
                      </Badge>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* 内容统计 */}
      {props.status === "done" && report?.content ? (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 8 }}>📝 Content Stats</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 8,
              padding: 12,
              background: "#f8fafc",
              borderRadius: 10,
              border: "1px solid #e2e8f0",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#334155" }}>{report.content.total_articles || 0}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>Total Articles</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#10b981" }}>+{report.content.published_this_week || 0}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>Published This Week</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#f59e0b" }}>{report.content.draft_count || 0}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>Drafts</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#8b5cf6" }}>{report.content.scheduled_count || 0}</div>
              <div style={{ fontSize: 10, color: "#64748b" }}>Scheduled</div>
            </div>
          </div>
        </div>
      ) : null}

      {/* 错误信息 */}
      {props.status === "error" && props.error_message ? (
        <div
          style={{
            marginTop: 12,
            borderRadius: 12,
            border: "1px solid #fecdd3",
            background: "#fff1f2",
            padding: 12,
            fontSize: 12,
            color: "#9f1239",
          }}
        >
          {props.error_message}
        </div>
      ) : null}
    </div>
  );
};

// ============ Report v2：三张卡（进度 / 图表 / 洞察）===========
type ReportProgressProps = {
  status: "loading" | "done" | "error";
  step?: string;
  user_text?: string;
  steps?: string[] | { step: string, status: string }[];
  active_step?: number;
  message?: string;
  error_message?: string | null;
  hidden?: boolean;
};

// Replaces old ReportProgressCard with new Workflow style
const ReportWorkflowCard: React.FC<ReportProgressProps> = (props) => {
  if (props.hidden) return null;
  const status = props.status || "running";

  // Default steps for Report Generation
  const defaultSteps = [
    { name: "Plan Report Structure", desc: "Analyze request and define report scope and metrics." },
    { name: "Fetch Site Data", desc: "Retrieve performance data from Google Analytics & Search Console." },
    { name: "Analyze Trends & Charts", desc: "Visualize data and identify key performance patterns." },
    { name: "Generate Insights", desc: "Synthesize findings into actionable business insights." },
    { name: "Report Completed", desc: "Report generation finished." }
  ];

  const steps = props.steps && props.steps.length > 0
    ? props.steps.map((s: any) => {
      if (typeof s === 'string') return { name: s, desc: '' };
      return { name: s.step, desc: s.status };
    })
    : defaultSteps;

  // Determine active step index (1-based)
  let activeStep = props.active_step || 1;
  if (status === "done") activeStep = steps.length + 1;

  const isStepDone = (idx: number) => {
    if (status === "done") return idx === 4; // Only last step green on done
    return idx + 1 < activeStep;
  };

  const isStepRunning = (idx: number) => {
    if (status === "done") return false;
    return idx + 1 === activeStep;
  };

  const isStepPending = (idx: number) => !isStepDone(idx) && !isStepRunning(idx);

  const renderIcon = (idx: number, isDone: boolean, isRunning: boolean) => {
    const color = isDone ? "#22c55e" : isRunning ? "#2563eb" : "#cbd5e1";
    // Inline icons for specific report steps
    if (idx === 0) return <TargetIcon color={color} />; // Plan
    // Fetch Data (Search/Database)
    if (idx === 1) return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
    );
    // Analyze (Chart)
    if (idx === 2) return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"></line>
        <line x1="12" y1="20" x2="12" y2="4"></line>
        <line x1="6" y1="20" x2="6" y2="14"></line>
      </svg>
    );
    // Insights (Bulb)
    if (idx === 3) return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 18h6"></path>
        <path d="M10 22h4"></path>
        <path d="M12 2v1"></path>
        <path d="M12 2v1"></path>
        <path d="M4.2 4.2l.7.7"></path>
        <path d="M19.1 4.2l-.7.7"></path>
        <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"></path>
      </svg>
    );
    return <DocIcon color={color} />; // Done
  };

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
      <style>{`
        ${cssText}
        @keyframes pulse-dots {
          0% { opacity: 0.2; }
          50% { opacity: 1; }
          100% { opacity: 0.2; }
        }
        .pulse-dot {
          animation: pulse-dots 1.5s infinite;
          display: inline-block;
        }
        .pulse-dot:nth-child(2) { animation-delay: 0.2s; }
        .pulse-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .workflow-step {
          transition: opacity 0.3s ease;
        }
        .workflow-step-text {
          transition: color 0.3s ease;
        }
        .workflow-step-bg {
          transition: background-color 0.3s ease, color 0.3s ease;
        }
      `}</style>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, fontSize: 20, fontWeight: 700, color: '#0f172a' }}>
          <span style={{ fontSize: 26 }}>📈</span> AI is analyzing site data...
        </div>
      </div>

      {/* Workflow Steps */}
      <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 20, marginTop: 10 }}>
        {steps.slice(0, 5).map((step, idx) => {
          const isDone = isStepDone(idx);
          const isRunning = isStepRunning(idx);
          const isPending = isStepPending(idx);

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
              <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', width: 44 }}>
                <div style={{ zIndex: 1, display: 'flex', height: 24, alignItems: 'center', justifyContent: 'center' }}>
                  {renderIcon(idx, isDone, isRunning)}
                </div>
                {idx < steps.length - 1 && (
                  <div style={{
                    position: 'absolute',
                    top: 32,
                    bottom: -20,
                    width: 2,
                    background: isDone ? "#22c55e" : "#f1f5f9",
                    zIndex: 0,
                    transition: 'background-color 0.3s ease'
                  }} />
                )}
              </div>

              <div style={{ flex: 1, paddingTop: 2 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {isDone ? (
                    <div style={{ color: '#22c55e', transition: 'color 0.3s ease' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                      </svg>
                    </div>
                  ) : (
                    <div className="workflow-step-bg" style={{
                      width: 20,
                      height: 20,
                      borderRadius: 10,
                      background: isRunning ? '#2563eb' : '#f1f5f9',
                      color: isRunning ? '#fff' : '#94a3b8',
                      fontSize: 11,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700
                    }}>
                      {idx + 1}
                    </div>
                  )}

                  <h4 className="workflow-step-text" style={{
                    margin: 0,
                    fontSize: 15,
                    fontWeight: 700,
                    color: isRunning ? '#2563eb' : isDone ? '#22c55e' : '#1e293b'
                  }}>
                    {step.name}
                    {isRunning && (
                      <span style={{ marginLeft: 8, color: '#3b82f6' }}>
                        <span className="pulse-dot">.</span>
                        <span className="pulse-dot">.</span>
                        <span className="pulse-dot">.</span>
                      </span>
                    )}
                  </h4>
                </div>

                <p style={{ margin: '6px 0 0', fontSize: 13, color: '#64748b', lineHeight: 1.5 }}>
                  {step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Success Section */}
      {status === "done" && (
        <div style={{
          marginTop: 40,
          background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)',
          padding: 20,
          borderRadius: 12,
          border: '1px solid #bbf7d0',
          animation: 'fadeIn 0.4s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#166534', marginBottom: 4 }}>
                Insights Generated
              </div>
              <div style={{ fontSize: 13, color: '#16a34a' }}>Analysis completed successfully</div>
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
        </div>
      )}

      {props.status === "error" && props.error_message ? (
        <div style={{ marginTop: 24, borderRadius: 12, border: "1px solid #fecdd3", background: "#fff1f2", padding: 12, fontSize: 13, color: "#9f1239" }}>
          {props.error_message}
        </div>
      ) : null}
    </div>
  );
};

type ReportChartsProps = {
  status: "loading" | "done" | "error";
  message?: string;
  report?: {
    summary?: any;
    charts?: any;
  } | null;
};

const ReportChartsCard: React.FC<ReportChartsProps> = (props) => {
  const report = props.report || null;
  return (
    <div
      className="lgui-card"
      style={{
        borderRadius: 14,
        border: "1px solid #e2e8f0",
        background: "#ffffff",
        padding: 14,
        fontSize: 13,
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.06)",
        maxWidth: 720,
      }}
    >
      <style>{cssText}</style>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>📈 图表</div>
          {props.message ? <div style={{ marginTop: 6, fontSize: 12, color: "#64748b" }}>{props.message}</div> : null}
        </div>
        <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>charts</div>
      </div>
      {/* 本仓库内不渲染具体图表（图表已在 agentchatui 外层项目渲染），这里只做占位避免重复“报告卡”。 */}
      <div style={{ marginTop: 12, fontSize: 12, color: "#64748b" }}>
        {report?.charts ? (() => {
          const charts = report.charts;
          const chartKeys = Object.keys(charts);
          return chartKeys.map((key) => {
            const chart = charts[key];
            if (!chart) return null;
            const title = chart.title || key;
            const chartType = chart.chart_type || "chart";
            const desc = chart.description || "";
            return (
              <div key={key} style={{ marginTop: 12, borderRadius: 10, border: "1px solid #e2e8f0", background: "#f8fafc", padding: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>📊 {title}</div>
                  <Badge tone="slate">{chartType}</Badge>
                </div>
                {desc ? (
                  <div style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 4 }}>💡 智能分析</div>
                    <div style={{ fontSize: 12, color: "#334155", lineHeight: 1.6 }}>{desc}</div>
                  </div>
                ) : (
                  <div style={{ marginTop: 10, fontSize: 11, color: "#94a3b8", fontStyle: "italic" }}>正在生成分析...</div>
                )}
              </div>
            );
          });
        })() : "等待图表数据…"}
      </div>
    </div>
  );
};



type ReportInsightsProps = {
  status: "loading" | "done" | "error";
  message?: string;
  report?: any;
};

// Typewriter effect component for streaming-like display
const TypewriterText: React.FC<{ text: string; speed?: number; className?: string; style?: any }> = ({ text, speed = 20, className, style }) => {
  const [displayed, setDisplayed] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!text) return;
    setDisplayed("");
    setIsComplete(false);
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        setIsComplete(true);
        clearInterval(timer);
      }
    }, speed);
    return () => clearInterval(timer);
  }, [text, speed]);

  return (
    <span className={className} style={style}>
      {displayed}
      {!isComplete && <span className="typing-cursor">|</span>}
    </span>
  );
};

const ReportInsightsCard: React.FC<ReportInsightsProps> = (props) => {
  const report = props.report || {};

  return (
    <div
      className="lgui-card"
      style={{
        borderRadius: 16,
        border: "1px solid #e2e8f0",
        background: "#ffffff",
        padding: "32px",
        fontSize: 14,
        boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
        maxWidth: 800,
        position: 'relative'
      }}
    >
      <style>{`
        ${cssText}
        @keyframes blink-cursor {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        .typing-cursor {
          animation: blink-cursor 0.8s infinite;
          color: #3b82f6;
          font-weight: 300;
        }
      `}</style>

      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        marginBottom: 24,
        paddingBottom: 16,
        borderBottom: "1px solid #f1f5f9"
      }}>
        <div style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: "#eff6ff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 24
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800, color: "#0f172a" }}>
            {report.report_type_name || "Site Data Report"}
          </div>
          <div style={{ fontSize: 13, color: "#64748b", marginTop: 4 }}>
            Generated on {new Date().toLocaleDateString()}
          </div>
        </div>
      </div>

      {/* Helper to render sections with typewriter effect/streaming feel can be implemented here if backend sends token stream. 
          For now, we render the structured data cleanly. 
      */}

      {/* 1. Insights (Key Findings) */}
      {report.insights ? (
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#1e293b", marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24 }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            Key Insights
          </div>
          <div style={{
            background: "#f8fafc",
            borderRadius: 12,
            padding: "20px",
            border: "1px solid #f1f5f9"
          }}>
            {report.insights.one_liner && (
              <div style={{ fontSize: 15, fontWeight: 600, color: "#0f172a", marginBottom: 16, lineHeight: 1.6 }}>
                {report.insights.one_liner}
                {report.insights._streaming && <span className="typing-cursor">|</span>}
              </div>
            )}

            {report.insights.evidence && report.insights.evidence.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "#94a3b8", textTransform: 'uppercase', marginBottom: 8 }}>Evidence</div>
                <ul style={{ margin: 0, paddingLeft: 20, color: "#475569", lineHeight: 1.6 }}>
                  {report.insights.evidence.map((e: string, i: number) => (
                    <li key={i} style={{ marginBottom: 4 }}>{e}</li>
                  ))}
                </ul>
              </div>
            )}

            {report.insights.hypotheses && report.insights.hypotheses.length > 0 && (
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: "#94a3b8", textTransform: 'uppercase', marginBottom: 8 }}>Analysis</div>
                <div style={{ display: 'grid', gap: 10 }}>
                  {report.insights.hypotheses.map((h: any, i: number) => (
                    <div key={i} style={{ background: "#ffffff", padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                      <div style={{ fontWeight: 600, color: "#334155" }}>{h.text}</div>
                      {h.next_step && <div style={{ fontSize: 12, color: "#64748b", marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        Suggestion: {h.next_step}
                      </div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* 2. Actions (ToDo) */}
      {report.actions && report.actions.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#1e293b", marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24 }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            Recommended Actions
          </div>
          <div style={{ display: "grid", gap: 12 }}>
            {report.actions.map((action: any, i: number) => (
              <div key={i} style={{
                display: 'flex',
                gap: 16,
                padding: 16,
                borderRadius: 12,
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                boxShadow: "0 1px 2px rgba(0,0,0,0.03)"
              }}>
                <div style={{
                  width: 24,
                  height: 24,
                  borderRadius: 12,
                  background: "#f0fdf4",
                  color: "#16a34a",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  fontWeight: 700
                }}>
                  {i + 1}
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: 2 }}>{action.title || action.action}</div>
                  {action.description && <div style={{ fontSize: 13, color: "#64748b", lineHeight: 1.5 }}>{action.description}</div>}
                  {action.impact && (
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: 8, padding: "2px 8px", background: "#f1f5f9", borderRadius: 4, fontSize: 11, color: "#475569" }}>
                      <span>⚡ Impact:</span>
                      <span style={{ fontWeight: 600 }}>{action.impact}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Todos (Development) */}
      {report.todos && report.todos.length > 0 && (
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#1e293b", marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24 }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
              </svg>
            </div>
            Development Tasks
          </div>
          <div style={{ background: "#f8fafc", borderRadius: 12, padding: 8 }}>
            {report.todos.map((todo: any, i: number) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "10px", borderBottom: i < report.todos.length - 1 ? "1px solid #e2e8f0" : "none" }}>
                <div style={{ marginTop: 2, color: "#cbd5e1" }}>◻</div>
                <div style={{ fontSize: 13, color: "#475569", lineHeight: 1.5 }}>{typeof todo === 'string' ? todo : (todo.title || todo.task || todo.content || JSON.stringify(todo))}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============ 洞察确认组件 ============
type ReportConfirmInsightsProps = {
  message?: string;
};

const ReportConfirmInsightsCard: React.FC<ReportConfirmInsightsProps> = (props) => {
  const streamCtx = useStreamContext?.() as any;

  const handleChoice = (confirmed: boolean) => {
    if (streamCtx && typeof streamCtx.resume === "function") {
      try {
        streamCtx.resume(confirmed);
        return;
      } catch { }
    }
    // TODO: 兜底逻辑（如果不支持 resume）
    console.warn("resume is not supported in this environment");
  };

  return (
    <div
      className="lgui-card"
      style={{
        borderRadius: 14,
        border: "1px solid #bfdbfe",
        background: "#eff6ff",
        padding: 16,
        fontSize: 13,
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.06)",
        maxWidth: 500,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 20 }}>🔍</span>
        <div style={{ fontWeight: 700, color: "#1e3a8a", fontSize: 14 }}>
          {props.message || "图表已生成，是否继续执行深度洞察分析？"}
        </div>
      </div>
      <div style={{ marginTop: 6, fontSize: 12, color: "#64748b", marginLeft: 34 }}>
        深度分析将利用 AI 对数据进行多维度解读，并提供改进建议与待办事项。
      </div>
      <div style={{ marginTop: 16, display: "flex", gap: 10, marginLeft: 34 }}>
        <button
          onClick={() => handleChoice(true)}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            background: "#1d4ed8",
            color: "white",
            border: "none",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          继续深度分析
        </button>
        <button
          onClick={() => handleChoice(false)}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            background: "white",
            color: "#64748b",
            border: "1px solid #e2e8f0",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          暂时不需要
        </button>
      </div>
    </div>
  );
};

// ============ Shortcut：选择/确认组件（Generative UI）============
type ShortcutSelectProps = {
  title?: string;
  message?: string;
  options?: { code?: string; name?: string; desc?: string }[];
  recommended?: string | null;
};

const ShortcutSelectCard: React.FC<ShortcutSelectProps> = (props) => {
  const streamCtx = useStreamContext?.() as any;
  const options = props.options || [];
  const recommended = props.recommended || null;

  const resume = (value: any) => {
    if (streamCtx && typeof streamCtx.resume === "function") {
      try { streamCtx.resume(value); return; } catch { }
    }
    console.warn("resume is not supported in this environment");
  };

  return (
    <div className="lgui-card" style={{
      borderRadius: 14,
      border: "1px solid #e2e8f0",
      background: "#ffffff",
      padding: 14,
      fontSize: 13,
      boxShadow: "0 1px 2px rgba(15, 23, 42, 0.06)",
      maxWidth: 560,
    }}>
      <style>{cssText}</style>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>{props.title || "请选择操作"}</div>
          {props.message ? <div style={{ marginTop: 6, fontSize: 12, color: "#64748b" }}>{props.message}</div> : null}
        </div>
        <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>shortcut</div>
      </div>

      <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
        {options.map((o, idx) => {
          const code = String(o.code || "");
          const label = o.name || o.code || `操作 ${idx + 1}`;
          const isRec = recommended && code && String(recommended) === code;
          return (
            <button
              key={`${code || label}-${idx}`}
              onClick={() => resume(code)}
              style={{
                textAlign: "left",
                padding: "10px 12px",
                borderRadius: 10,
                border: "1px solid #e2e8f0",
                background: isRec ? "#eff6ff" : "#ffffff",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                <div style={{ fontWeight: 700, color: "#0f172a" }}>
                  {label}{isRec ? <span style={{ marginLeft: 8, fontSize: 11, color: "#2563eb" }}>推荐</span> : null}
                </div>
                <span style={{ fontSize: 11, color: "#94a3b8" }}>{code ? code : ""}</span>
              </div>
              {o.desc ? <div style={{ marginTop: 6, color: "#64748b" }}>{o.desc}</div> : null}
            </button>
          );
        })}

        <button
          onClick={() => resume("__cancel__")}
          style={{
            marginTop: 4,
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid #e2e8f0",
            background: "#f8fafc",
            color: "#64748b",
            cursor: "pointer",
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          取消
        </button>
      </div>
    </div>
  );
};

type ShortcutConfirmProps = {
  title?: string;
  message?: string;
  selected?: any;
  params?: any;
};

const ShortcutConfirmCard: React.FC<ShortcutConfirmProps> = (props) => {
  const streamCtx = useStreamContext?.() as any;
  const resume = (value: any) => {
    if (streamCtx && typeof streamCtx.resume === "function") {
      try { streamCtx.resume(value); return; } catch { }
    }
    console.warn("resume is not supported in this environment");
  };

  return (
    <div className="lgui-card" style={{
      borderRadius: 14,
      border: "1px solid #bfdbfe",
      background: "#eff6ff",
      padding: 16,
      fontSize: 13,
      boxShadow: "0 1px 2px rgba(15, 23, 42, 0.06)",
      maxWidth: 560,
    }}>
      <style>{cssText}</style>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <div style={{ fontWeight: 700, color: "#1e3a8a", fontSize: 13 }}>{props.title || "确认执行"}</div>
        <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>shortcut</div>
      </div>
      {props.message ? <div style={{ marginTop: 8, fontSize: 12, color: "#334155" }}>{props.message}</div> : null}
      <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
        <button
          onClick={() => resume(true)}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            background: "#1d4ed8",
            color: "white",
            border: "none",
            fontWeight: 700,
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          继续执行
        </button>
        <button
          onClick={() => resume(false)}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            background: "white",
            color: "#64748b",
            border: "1px solid #e2e8f0",
            fontWeight: 700,
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          取消
        </button>
      </div>
    </div>
  );
};

// 默认导出组件映射表，key 必须和 push_ui_message 里的 name 一致
const ComponentMap = {
  intent_router: IntentRouterCard,
  rag_workflow: RAGWorkflowCard,
  article_workflow: ArticleWorkflowCard,
  article_clarify: ArticleClarifyCard,
  article_clarify_summary: ArticleClarifySummaryCard,
  mcp_workflow: MCPWorkflowCard,
  seo_planner: SEOPlannerCard,
  site_report: SiteReportCard,
  report_progress: ReportWorkflowCard,
  report_progress_insights: ReportWorkflowCard,
  report_charts: ReportChartsCard,
  chart_analysis: ChartAnalysisCard,
  chart_analysis_loading: ChartAnalysisLoadingCard,
  report_insights: ReportInsightsCard,
  report_confirm_insights: ReportConfirmInsightsCard,
  shortcut_select: ShortcutSelectCard,
  shortcut_confirm: ShortcutConfirmCard,
  // 兼容旧名字：如果后端仍 push "card"，也能渲染为新版卡片
  card: IntentRouterCard as any,
};

export default ComponentMap;
