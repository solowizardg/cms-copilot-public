// UI 类型定义

// ============ Router ============
export type IntentRouterProps = {
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

// ============ RAG ============
export type RAGTabKey = "prep" | "generate";

export type RAGTab = {
    key?: RAGTabKey;
    title?: string;
};

export type RAGStep = {
    key?: string;
    title?: string;
    status?: "pending" | "running" | "done" | "error";
    message?: string;
};

export type RAGWorkflowProps = {
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

// ============ Article ============
export type WorkflowNode = {
    node_code?: string;
    node_name?: string;
    node_status?: string;
    node_message?: string;
};

export type ArticleWorkflowProps = {
    status: "running" | "done" | "error";
    run_id?: string | null;
    thread_id?: string | null;
    current_node?: string | null;
    flow_node_list?: WorkflowNode[];
    error_message?: string | null;
    result_topic?: string;
    result_url?: string;
    setup?: {
        app_name?: string;
        tone?: string;
        format?: string;
    };
};

export type AppOption = {
    id?: string | number;
    name?: string;
    model_id?: string | number;
};

export type ArticleClarifyProps = {
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
    writing_requirements?: string;
};

export type ArticleClarifySummaryProps = {
    status: "done" | "error";
    app_id?: string;
    app_name?: string;
    topic?: string;
    content_format?: string;
    target_audience?: string;
    tone?: string;
};

// ============ Shortcut / MCP ============
export type MCPOption = {
    code?: string;
    name?: string;
    desc?: string;
};

export type MCPWorkflowProps = {
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

export type ShortcutSelectProps = {
    title?: string;
    message?: string;
    options?: { code?: string; name?: string; desc?: string }[];
    recommended?: string | null;
};

export type ShortcutConfirmProps = {
    title?: string;
    message?: string;
    selected?: any;
    params?: any;
};

// ============ SEO Weekly Tasks ============

// 周任务元信息
export type WeeklyTaskMeta = {
    tenant_id?: string;
    site_id?: string;
    week_start?: string;
    timezone?: string;
    run_id?: string;
};

// 周任务项
export type WeeklyTask = {
    task_id?: string;
    task_type?: string;  // CONTENT_PUBLISH
    priority?: number;
    title?: string;
    prompt?: string;  // 不在UI显示，点击发布时发送到聊天框
};

// 周任务数据
export type WeeklyTasksData = {
    schema_version?: string;
    meta?: WeeklyTaskMeta;
    tasks?: WeeklyTask[];
};

// SEO Planner Props
export type SEOPlannerProps = {
    status: "loading" | "done" | "error";
    step?: string;
    user_text?: string;
    steps?: string[];
    active_step?: number;
    weekly_tasks?: WeeklyTasksData | null;
    progress?: string;
    error_message?: string | null;
};

// ============ Report ============
export type SiteReportProps = {
    status: "loading" | "done" | "error";
    step?: string;
    user_text?: string;
    message?: string;
    steps?: string[];
    active_step?: number;
    report?: {
        site_id?: string;
        report_type?: string;
        date_range?: { start?: string; end?: string };
        data_sources?: string[];
        summary?: any;
        charts?: any[];
        insights?: any;
        raw_data?: any;
    } | null;
    error_message?: string | null;
};

export type ReportProgressProps = {
    status: "loading" | "done" | "error";
    step?: string;
    user_text?: string;
    steps?: string[] | { step: string; status: string }[];
    active_step?: number;
    message?: string;
    error_message?: string | null;
    hidden?: boolean;
};

export type ReportChartsProps = {
    status: "loading" | "done" | "error";
    message?: string;
    report?: {
        summary?: any;
        charts?: any;
    } | null;
    summary?: any;
    charts?: any;
};

export type ReportInsightsProps = {
    status: "loading" | "done" | "error";
    message?: string;
    report?: any;
};

export type ChartAnalysisProps = {
    chart_key?: string;
    chart_title?: string;
    chart_type?: string;
    description?: string;
};

export type ChartAnalysisLoadingProps = {
    chart_key?: string;
    chart_title?: string;
    hidden?: boolean;
};

export type ReportConfirmInsightsProps = {
    message?: string;
    hidden?: boolean;
};

// ============ Badge ============
export type BadgeProps = {
    children?: React.ReactNode;
    tone?: "slate" | "blue" | "green" | "red";
};
