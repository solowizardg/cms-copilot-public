# UI Components Documentation

本文档描述了 CMS Copilot 项目中所有 UI 组件的结构和用法。

## 目录结构

```
src/ui/
├── index.tsx          # 入口文件，导出 ComponentMap
├── styles.css         # 全局样式
├── types.ts           # 类型定义
├── hooks.ts           # React hooks
└── components/
    ├── common/        # 通用组件
    ├── router/        # 意图路由
    ├── rag/           # 知识检索
    ├── article/       # 文章生成
    ├── shortcut/      # 快捷操作
    ├── seo/           # SEO 规划
    └── report/        # 站点报告
```

---

## ComponentMap 映射表

| Key | Component | 用途 |
|-----|-----------|------|
| `intent_router` | IntentRouterCard | 显示意图识别状态 |
| `rag_workflow` | RAGWorkflowCard | RAG 检索进度 |
| `article_workflow` | ArticleWorkflowCard | 文章生成工作流 |
| `article_clarify` | ArticleClarifyCard | 文章参数收集表单 |
| `article_clarify_summary` | ArticleClarifySummaryCard | 文章参数确认展示 |
| `mcp_workflow` | MCPWorkflowCard | 后台操作工作流 |
| `shortcut_select` | ShortcutSelectCard | 快捷操作选择 |
| `shortcut_confirm` | ShortcutConfirmCard | 快捷操作确认 |
| `seo_planner` | SEOPlannerCard | SEO 周计划 |
| `site_report` | SiteReportCard | 站点报告概览 |
| `report_progress` | ReportWorkflowCard | 报告生成进度 |
| `report_charts` | ReportChartsCard | 报告图表展示 |
| `report_insights` | ReportInsightsCard | AI 分析洞察 |
| `report_confirm_insights` | ReportConfirmInsightsCard | 确认生成洞察 |
| `chart_analysis` | ChartAnalysisCard | 单图表分析 |
| `chart_analysis_loading` | ChartAnalysisLoadingCard | 图表分析加载中 |

---

## 通用组件 (common/)

### Badge
状态标签组件，支持多种颜色主题。

```tsx
<Badge tone="blue">Running</Badge>
<Badge tone="green">Completed</Badge>
<Badge tone="red">Failed</Badge>
```

**Props:**
- `tone`: `"slate" | "blue" | "green" | "red"`
- `children`: React.ReactNode

### Spinner
加载动画组件。

```tsx
<Spinner />
```

### Icons
SVG 图标集合。

| 组件 | 说明 |
|------|------|
| `TargetIcon` | 目标图标 (用于文章工作流) |
| `TreeIcon` | 树形结构图标 |
| `DocIcon` | 文档图标 |

---

## 域组件

### Router - IntentRouterCard
显示意图识别的思考状态。

**Props:**
```ts
type IntentRouterProps = {
  status: "thinking" | "done" | "error";
  elapsed_s?: number;
  rag_status?: "running" | "done" | "error";
  rag_message?: string;
  hidden?: boolean;
  main_title?: string;
};
```

---

### RAG - RAGWorkflowCard
显示知识库检索进度。

**Props:**
```ts
type RAGWorkflowProps = {
  status: "running" | "done" | "error";
  steps?: { prep?: RAGStep[]; generate?: RAGStep[] };
  error_message?: string;
};
```

---

### Article

#### ArticleWorkflowCard
文章生成工作流，显示 4 个步骤进度。

**Props:**
```ts
type ArticleWorkflowProps = {
  status: "running" | "done" | "error";
  flow_node_list?: WorkflowNode[];
  result_topic?: string;
  setup?: { app_name?: string; tone?: string; format?: string };
};
```

#### ArticleClarifyCard
收集文章生成参数的表单。

**Props:**
```ts
type ArticleClarifyProps = {
  status: "need_info" | "done" | "error";
  topic?: string;
  content_format?: string;
  target_audience?: string;
  tone?: string;
  tone_options?: string[];
  app_options?: AppOption[];
};
```

#### ArticleClarifySummaryCard
显示已收集的文章参数摘要。

---

### Shortcut

#### MCPWorkflowCard
后台操作工作流，显示步骤和确认按钮。

**Props:**
```ts
type MCPWorkflowProps = {
  status: "select" | "confirm" | "running" | "done" | "cancelled" | "error";
  title?: string;
  message?: string;
  options?: MCPOption[];
  steps?: any[];
  active_step?: number;
};
```

#### ShortcutSelectCard
显示可选操作列表。

#### ShortcutConfirmCard
确认执行操作的对话框。

---

### SEO - SEOPlannerCard
SEO 周计划展示，包含任务列表和严重程度标记。

**Props:**
```ts
type SEOPlannerProps = {
  status: "loading" | "done" | "error";
  steps?: string[];
  active_step?: number;
  tasks?: SEOWeeklyPlanData;
};
```

---

### Report

#### SiteReportCard
站点报告概览卡片。

#### ReportWorkflowCard
报告生成进度展示。

#### ReportChartsCard
图表数据展示区域。

#### ReportInsightsCard
AI 生成的洞察和建议，带打字机效果。

#### ReportConfirmInsightsCard
询问用户是否生成深度洞察。

#### ChartAnalysisCard
单个图表的 AI 分析结果。

#### ChartAnalysisLoadingCard
图表分析加载提示。

---

## 后端调用示例

```python
from src.agent.utils.chat_utils import push_ui_message

# 推送 UI 组件
push_ui_message(
    state,
    name="intent_router",  # 对应 ComponentMap 的 key
    props={
        "status": "thinking",
        "main_title": "Analyzing your request..."
    }
)
```

---

## 样式说明

所有组件使用以下设计规范：
- 圆角: 12-16px
- 边框: 1px solid #e2e8f0
- 阴影: 0 1px 3px rgba(0,0,0,0.05)
- 主色调: #2563eb (蓝), #22c55e (绿), #ef4444 (红)
- 字体: Inter, -apple-system, sans-serif
