/// <reference path="./react-shim.d.ts" />

// 导入样式
import "./styles.css";

// 导入 Router 组件
import { IntentRouterCard } from "./components/router";

// 导入 RAG 组件
import { RAGWorkflowCard } from "./components/rag";

// 导入 Article 组件
import { ArticleWorkflowCard, ArticleClarifyCard, ArticleClarifySummaryCard } from "./components/article";

// 导入 Shortcut 组件
import { MCPWorkflowCard } from "./components/shortcut";

// 导入 SEO 组件
import { SEOPlannerCard } from "./components/seo";

// 导入 Report 组件
import {
    SiteReportCard,
    ReportWorkflowCard,
    ReportChartsCard,
    ReportInsightsCard,
    ReportConfirmInsightsCard,
    ChartAnalysisCard,
    ChartAnalysisLoadingCard,
} from "./components/report";

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
    // 兼容旧名字：如果后端仍 push "card"，也能渲染为新版卡片
    card: IntentRouterCard as any,
};

export default ComponentMap;

// （可选）给后端 typedUi 做类型约束
export type { ComponentMap };
