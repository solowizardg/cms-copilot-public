"""SEO 工具模块。

提供 SEO 周任务数据获取等功能。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

from agent.config import get_logger

logger = get_logger(__name__)


# ============ 周任务 Pydantic 模型定义 ============


class WeeklyTaskMeta(BaseModel):
    """周任务元信息"""

    model_config = {"extra": "ignore"}

    tenant_id: str
    site_id: str
    week_start: str
    timezone: str = "America/Los_Angeles"
    run_id: str | None = None


class WeeklyTask(BaseModel):
    """周任务项（CONTENT_PUBLISH 类型）"""

    model_config = {"extra": "ignore"}

    task_id: str
    task_type: str = "CONTENT_PUBLISH"
    priority: int = Field(default=50, ge=0, le=100)
    title: str
    prompt: str


class WeeklyTasksData(BaseModel):
    """周任务数据"""

    model_config = {"extra": "ignore"}

    schema_version: str = "seo_weekly_tasks.v1"
    meta: WeeklyTaskMeta
    tasks: list[WeeklyTask] = Field(default_factory=list)


class WeeklyTasksResponse(BaseModel):
    """周任务 API 响应"""

    model_config = {"extra": "ignore"}

    code: int = 0
    message: str = "success"
    data: WeeklyTasksData
    trace_id: str | None = None


# ============ SEO 周任务 API 配置 ============

# 默认 API 地址，可通过环境变量覆盖
SEO_WEEKLY_PLAN_API_URL = "https://ai-content-dev.aihtm.com/ai/api/seo/weekly-plan"


# ============ 周任务 API 调用函数 ============


async def fetch_weekly_tasks(
    site_id: str,
    tenant_id: str | None = None,
    site_url: str | None = None,
    token: str | None = None,
    request_body: dict[str, Any] | None = None,
    api_url: str | None = None,
) -> WeeklyTasksResponse:
    """调用接口获取 SEO 周任务。

    Args:
        site_id: 站点 ID
        tenant_id: 租户 ID
        site_url: 站点 URL
        token: 授权令牌
        request_body: 请求体（包含 meta, pages, keyword_assets, semrush_snapshot 等）
        api_url: API 地址，默认使用 SEO_WEEKLY_PLAN_API_URL

    Returns:
        WeeklyTasksResponse: 周任务响应
    """
    url = api_url or SEO_WEEKLY_PLAN_API_URL
    trace_id = f"seo-{uuid.uuid4().hex[:16]}"

    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "X-Request-Id": trace_id,
        "X-Stream": "False",
    }
    if token:
        headers["Authorization"] = f"bearer {token}"
    if tenant_id:
        headers["X-Tenant-Id"] = tenant_id
    if site_id:
        headers["X-Site-Id"] = site_id
    if site_url:
        headers["X-Site-Url"] = site_url

    logger.info(f"[SEO][fetch_weekly_tasks] 调用接口: {url}")
    logger.info(f"[SEO][fetch_weekly_tasks] headers: X-Site-Id={site_id}, X-Tenant-Id={tenant_id}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=request_body or {},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"[SEO][fetch_weekly_tasks] 响应成功，任务数: {len(data.get('data', {}).get('tasks', []))}")
            return WeeklyTasksResponse.model_validate(data)

    except httpx.HTTPStatusError as e:
        logger.error(f"[SEO][fetch_weekly_tasks] HTTP 错误: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"[SEO][fetch_weekly_tasks] 请求错误: {e}")
        raise
    except Exception as e:
        logger.error(f"[SEO][fetch_weekly_tasks] 未知错误: {e}", exc_info=True)
        raise


# ============ Mock 数据（开发测试用）============


def get_mock_weekly_tasks_response(
    tenant_id: str = "t_demo_001",
    site_id: str = "s_demo_aiweb_001",
    week_start: str | None = None,
) -> WeeklyTasksResponse:
    """获取 Mock 周任务响应（开发测试用）。

    Args:
        tenant_id: 租户 ID
        site_id: 站点 ID
        week_start: 周起始日期，默认使用当前日期

    Returns:
        WeeklyTasksResponse: Mock 周任务响应
    """
    if not week_start:
        week_start = datetime.now().strftime("%Y-%m-%d")

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    return WeeklyTasksResponse(
        code=0,
        message="success",
        data=WeeklyTasksData(
            schema_version="seo_weekly_tasks.v1",
            meta=WeeklyTaskMeta(
                tenant_id=tenant_id,
                site_id=site_id,
                week_start=week_start,
                timezone="America/Los_Angeles",
                run_id=run_id,
            ),
            tasks=[
                WeeklyTask(
                    task_id="wk20260203_01",
                    task_type="CONTENT_PUBLISH",
                    priority=95,
                    title="AI Website Builder vs Wix: Comprehensive Comparison 2026",
                    prompt="""The detailed prompt sent to the Content Writer AI. Must include:
- **Defined SEO Title**: AI Website Builder vs Wix: Comprehensive Comparison 2026
- Content Type: News
- Subject: Detailed comparison of AI Website Builder and Wix, highlighting differences, pros and cons, pricing, features, and user suitability.
- Primary Keywords: ["ai website builder vs wix", "ai website builder", "wix ai website builder"]
- Secondary Keywords: ["website builder", "website builder pricing", "website builder features"]
- Keyword Distribution Requirements: Primary keywords must appear in the H1/Title and first paragraph. Secondary keywords should be naturally integrated into H2 sections covering pricing, features, and user reviews.
- Required Output Fields: SEO Title, Meta Description, Slug, Content Outline, Body Content, FAQ (>=6 questions).""",
                ),
                WeeklyTask(
                    task_id="wk20260203_02",
                    task_type="CONTENT_PUBLISH",
                    priority=90,
                    title="How to Build a Website with AI: Step-by-Step Guide 2026",
                    prompt="""The detailed prompt sent to the Content Writer AI. Must include:
- **Defined SEO Title**: How to Build a Website with AI: Step-by-Step Guide 2026
- Content Type: Blog
- Subject: Educational guide explaining the process of building a website using AI tools, focusing on ease of use, benefits, and best practices.
- Primary Keywords: ["how to build a website with ai", "create website with ai", "build a website with ai"]
- Secondary Keywords: ["ai website builder", "no code website builder", "website templates"]
- Keyword Distribution Requirements: Primary keywords in H1/Title and first paragraph. Secondary keywords in H2 sections related to tools, templates, and AI benefits.
- Required Output Fields: SEO Title, Meta Description, Slug, Content Outline, Body Content, FAQ (>=6 questions).""",
                ),
                WeeklyTask(
                    task_id="wk20260203_03",
                    task_type="CONTENT_PUBLISH",
                    priority=88,
                    title="Introducing New Restaurant and Real Estate Website Templates for 2026",
                    prompt="""The detailed prompt sent to the Content Writer AI. Must include:
- **Defined SEO Title**: Introducing New Restaurant and Real Estate Website Templates for 2026
- Content Type: Product Update
- Subject: Announcement of new high-quality, AI-optimized website templates specifically for restaurant and real estate businesses.
- Primary Keywords: ["restaurant website template", "real estate website template", "website templates"]
- Secondary Keywords: ["ai website builder", "business website templates", "website builder"]
- Keyword Distribution Requirements: Primary keywords in the H1/Title and intro paragraph. Secondary keywords in body sections detailing features and benefits.
- Required Output Fields: SEO Title, Meta Description, Slug, Content Outline, Body Content, FAQ (>=6 questions).""",
                ),
                WeeklyTask(
                    task_id="wk20260203_04",
                    task_type="CONTENT_PUBLISH",
                    priority=85,
                    title="Best AI Website Builders in 2026: Top Features and User Reviews",
                    prompt="""The detailed prompt sent to the Content Writer AI. Must include:
- **Defined SEO Title**: Best AI Website Builders in 2026: Top Features and User Reviews
- Content Type: News
- Subject: Analysis and curation of the best AI website builders including features comparison and user feedback.
- Primary Keywords: ["best ai website builder", "ai website builder reviews", "ai website builder"]
- Secondary Keywords: ["website builder features", "website builder", "ai website builder pricing"]
- Keyword Distribution Requirements: Primary keywords in H1/Title and first paragraph. Secondary keywords in H2 sections covering features and pricing.
- Required Output Fields: SEO Title, Meta Description, Slug, Content Outline, Body Content, FAQ (>=6 questions).""",
                ),
                WeeklyTask(
                    task_id="wk20260203_05",
                    task_type="CONTENT_PUBLISH",
                    priority=80,
                    title="Zapier Integration with XSite AI Website Builder: How It Boosts Your Workflow",
                    prompt="""The detailed prompt sent to the Content Writer AI. Must include:
- **Defined SEO Title**: Zapier Integration with XSite AI Website Builder: How It Boosts Your Workflow
- Content Type: Product Update
- Subject: Announcement and detailed explanation about the new Zapier integration for automating workflows with the AI website builder.
- Primary Keywords: ["zapier website builder", "website builder integrations", "ai website builder"]
- Secondary Keywords: ["integrations", "workflow automation", "productivity"]
- Keyword Distribution Requirements: Primary keywords in H1/Title and first paragraph. Secondary keywords in body sections about features and benefits.
- Required Output Fields: SEO Title, Meta Description, Slug, Content Outline, Body Content, FAQ (>=6 questions).""",
                ),
                WeeklyTask(
                    task_id="wk20260203_06",
                    task_type="CONTENT_PUBLISH",
                    priority=75,
                    title="AI Website Builder for Small Business: Why It's a Game Changer in 2026",
                    prompt="""The detailed prompt sent to the Content Writer AI. Must include:
- **Defined SEO Title**: AI Website Builder for Small Business: Why It's a Game Changer in 2026
- Content Type: Blog
- Subject: Educational article focused on benefits and tailored features of AI website builders for small businesses.
- Primary Keywords: ["ai website builder for small business", "website builder for small business"]
- Secondary Keywords: ["ai website builder", "business website templates", "pricing"]
- Keyword Distribution Requirements: Primary keywords in H1/Title and first paragraph. Secondary keywords in H2 sections about templates and plans.
- Required Output Fields: SEO Title, Meta Description, Slug, Content Outline, Body Content, FAQ (>=6 questions).""",
                ),
            ],
        ),
        trace_id=f"mock-{uuid.uuid4().hex[:16]}",
    )


def get_mock_request_body(
    tenant_id: str = "t_demo_001",
    site_id: str = "s_demo_aiweb_001",
    site_url: str = "https://demo-xsite.ai",
    week_start: str | None = None,
    week_end: str | None = None,
) -> dict:
    """获取 Mock 请求体数据（开发测试用）。

    Args:
        tenant_id: 租户 ID
        site_id: 站点 ID
        site_url: 站点 URL
        week_start: 周起始日期 (YYYY-MM-DD)，默认自动计算下周一
        week_end: 周结束日期 (YYYY-MM-DD)，默认自动计算下周日

    Returns:
        dict: Mock 请求体
    """
    # 计算 week_start 和 week_end
    if not week_start or not week_end:
        from datetime import timedelta
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        ws = today + timedelta(days=days_until_monday)
        we = ws + timedelta(days=6)
        week_start = week_start or ws.strftime("%Y-%m-%d")
        week_end = week_end or we.strftime("%Y-%m-%d")

    return {
        "meta": {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "site_url": site_url,
            "week_start": week_start,
            "week_end": week_end,
            "timezone": "America/Los_Angeles",
            "generated_at": datetime.now().isoformat() + "Z",
            "sources": {
                "pages": "cms_db.pages",
                "keyword_assets": "cms_db.keyword_assets",
                "semrush_snapshot": "cms_db.semrush_snapshots (ingested from Semrush Analytics API)",
            },
            "semrush": {
                "endpoint": "https://api.semrush.com/",
                "type": "phrase_fullsearch",
                "database": "us",
                "export_columns": ["Dt", "Db", "Ph", "Nq", "Cp", "Co", "Nr", "Td", "In", "Kd", "Fk"],
                "ingested_at": "2026-02-03T03:10:00Z",
                "snapshot_id": "snap_s_demo_aiweb_001_2026-02-03_us_v1",
            },
        },
        "pages": [
            {"page_id": "p_home", "url": "https://demo-xsite.ai/", "title": "XSite AI Website Builder", "page_type": "general_page", "status": "published", "updated_at": "2026-01-28T18:12:00Z", "existing_keywords": ["ai website builder", "create website with ai"]},
            {"page_id": "p_pricing", "url": "https://demo-xsite.ai/pricing", "title": "Pricing & Plans", "page_type": "landing_page", "status": "published", "updated_at": "2026-01-30T07:20:00Z", "existing_keywords": ["website builder pricing", "ai website builder pricing"], "primary_keyword": "ai website builder pricing"},
            {"page_id": "p_features", "url": "https://demo-xsite.ai/features", "title": "Features", "page_type": "general_page", "status": "published", "updated_at": "2026-01-26T10:03:00Z", "existing_keywords": ["website builder features"]},
            {"page_id": "p_feature_ai_copy", "url": "https://demo-xsite.ai/features/ai-copywriter", "title": "AI Copywriter for Websites", "page_type": "detail_page", "status": "published", "updated_at": "2026-01-27T09:40:00Z", "existing_keywords": ["ai copywriter for website"]},
            {"page_id": "p_feature_seo", "url": "https://demo-xsite.ai/features/seo-tools", "title": "Built-in SEO Tools", "page_type": "detail_page", "status": "published", "updated_at": "2026-01-22T05:11:00Z", "existing_keywords": ["seo tools for website builder"]},
            {"page_id": "p_templates", "url": "https://demo-xsite.ai/templates", "title": "Website Templates", "page_type": "list_page", "status": "published", "updated_at": "2026-01-25T12:00:00Z", "existing_keywords": ["website templates", "business website templates"]},
            {"page_id": "p_template_restaurant", "url": "https://demo-xsite.ai/templates/restaurant-website", "title": "Restaurant Website Template", "page_type": "detail_page", "status": "published", "updated_at": "2026-01-25T12:10:00Z", "existing_keywords": ["restaurant website template"]},
            {"page_id": "p_template_real_estate", "url": "https://demo-xsite.ai/templates/real-estate-website", "title": "Real Estate Website Template", "page_type": "detail_page", "status": "published", "updated_at": "2026-01-25T12:12:00Z", "existing_keywords": ["real estate website template"]},
            {"page_id": "p_integrations", "url": "https://demo-xsite.ai/integrations", "title": "Integrations", "page_type": "list_page", "status": "published", "updated_at": "2026-01-23T08:00:00Z", "existing_keywords": ["website builder integrations"]},
            {"page_id": "p_integration_zapier", "url": "https://demo-xsite.ai/integrations/zapier", "title": "Zapier Integration", "page_type": "detail_page", "status": "draft", "updated_at": "2026-02-01T10:10:00Z", "existing_keywords": ["zapier website builder"]},
            {"page_id": "p_blog", "url": "https://demo-xsite.ai/blog", "title": "Blog", "page_type": "list_page", "status": "published", "updated_at": "2026-01-21T03:00:00Z", "existing_keywords": ["ai website tips"]},
            {"page_id": "p_blog_vs_wix", "url": "https://demo-xsite.ai/blog/ai-website-builder-vs-wix", "title": "AI Website Builder vs Wix: What's Different?", "page_type": "detail_page", "status": "published", "updated_at": "2026-01-29T02:40:00Z", "existing_keywords": ["wix ai website builder", "ai website builder vs wix"]},
            {"page_id": "p_blog_how_to", "url": "https://demo-xsite.ai/blog/how-to-build-a-website-with-ai", "title": "How to Build a Website with AI (Step-by-Step)", "page_type": "detail_page", "status": "published", "updated_at": "2026-01-24T06:10:00Z", "existing_keywords": ["how to build a website with ai"]},
            {"page_id": "p_use_cases", "url": "https://demo-xsite.ai/use-cases", "title": "Use Cases", "page_type": "category_page", "status": "published", "updated_at": "2026-01-20T01:00:00Z", "existing_keywords": ["website builder for small business"]},
            {"page_id": "p_use_case_small_business", "url": "https://demo-xsite.ai/use-cases/small-business", "title": "AI Website Builder for Small Business", "page_type": "landing_page", "status": "published", "updated_at": "2026-01-20T01:05:00Z", "existing_keywords": ["ai website builder for small business"]},
            {"page_id": "p_support", "url": "https://demo-xsite.ai/support", "title": "Support", "page_type": "general_page", "status": "published", "updated_at": "2026-01-18T04:30:00Z", "existing_keywords": []},
            {"page_id": "p_search", "url": "https://demo-xsite.ai/search", "title": "Search", "page_type": "search_page", "status": "published", "updated_at": "2026-01-18T04:31:00Z", "existing_keywords": []},
            {"page_id": "p_author_jane", "url": "https://demo-xsite.ai/author/jane-doe", "title": "Jane Doe", "page_type": "author_page", "status": "published", "updated_at": "2026-01-18T04:32:00Z", "existing_keywords": []},
        ],
        "keyword_assets": [
            {"keyword_id": "k001", "keyword": "ai website builder", "asset_type": "core", "priority": 5, "language": "en", "country": "US"},
            {"keyword_id": "k002", "keyword": "website builder", "asset_type": "core", "priority": 5, "language": "en", "country": "US"},
            {"keyword_id": "k003", "keyword": "create website with ai", "asset_type": "core", "priority": 5, "language": "en", "country": "US"},
            {"keyword_id": "k004", "keyword": "website templates", "asset_type": "core", "priority": 4, "language": "en", "country": "US"},
            {"keyword_id": "k005", "keyword": "website builder for small business", "asset_type": "core", "priority": 4, "language": "en", "country": "US"},
            {"keyword_id": "k101", "keyword": "best ai website builder", "asset_type": "expanded", "priority": 4, "language": "en", "country": "US"},
            {"keyword_id": "k102", "keyword": "ai website builder free", "asset_type": "expanded", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k103", "keyword": "ai landing page generator", "asset_type": "expanded", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k104", "keyword": "no code website builder", "asset_type": "expanded", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k105", "keyword": "wix ai website builder", "asset_type": "expanded", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k106", "keyword": "squarespace ai website builder", "asset_type": "expanded", "priority": 2, "language": "en", "country": "US"},
            {"keyword_id": "k107", "keyword": "wordpress ai website builder", "asset_type": "expanded", "priority": 2, "language": "en", "country": "US"},
            {"keyword_id": "k201", "keyword": "ai website builder for photographers", "asset_type": "longtail", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k202", "keyword": "ai website builder for real estate agents", "asset_type": "longtail", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k203", "keyword": "ai website builder for restaurants", "asset_type": "longtail", "priority": 3, "language": "en", "country": "US"},
            {"keyword_id": "k204", "keyword": "real estate website template", "asset_type": "longtail", "priority": 2, "language": "en", "country": "US"},
            {"keyword_id": "k205", "keyword": "restaurant website template", "asset_type": "longtail", "priority": 2, "language": "en", "country": "US"},
            {"keyword_id": "k206", "keyword": "how to build a website with ai", "asset_type": "longtail", "priority": 2, "language": "en", "country": "US"},
            {"keyword_id": "k207", "keyword": "ai website builder vs wix", "asset_type": "longtail", "priority": 2, "language": "en", "country": "US"},
        ],
        "semrush_snapshot": [
            {"Dt": "20260215", "Db": "us", "Ph": "website builder", "Nq": 90500, "Cp": 5.42, "Co": 0.71, "Nr": 2680000000, "Td": "0.88,0.90,0.92,0.93,0.91,0.89,0.87,0.86,0.86,0.88,0.90,0.92", "In": 0, "Kd": 82, "Fk": "adt,adb,kng,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder", "Nq": 4400, "Cp": 8.12, "Co": 0.66, "Nr": 532000000, "Td": "0.74,0.76,0.78,0.82,0.85,0.88,0.90,0.92,0.94,0.96,0.98,1.00", "In": 0, "Kd": 58, "Fk": "aio,adt,fsn,rel,kng"},
            {"Dt": "20260215", "Db": "us", "Ph": "best ai website builder", "Nq": 1900, "Cp": 9.54, "Co": 0.62, "Nr": 214000000, "Td": "0.70,0.72,0.73,0.75,0.78,0.80,0.84,0.86,0.90,0.93,0.96,1.00", "In": 0, "Kd": 52, "Fk": "aio,fsn,rel,res,kng"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder free", "Nq": 1300, "Cp": 4.10, "Co": 0.55, "Nr": 188000000, "Td": "0.68,0.70,0.72,0.73,0.74,0.76,0.78,0.80,0.82,0.86,0.92,1.00", "In": 0, "Kd": 46, "Fk": "adt,adb,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "create website with ai", "Nq": 2400, "Cp": 6.35, "Co": 0.58, "Nr": 406000000, "Td": "0.66,0.68,0.70,0.74,0.78,0.82,0.86,0.90,0.92,0.94,0.97,1.00", "In": 1, "Kd": 49, "Fk": "aio,rel,fsn,vid,img"},
            {"Dt": "20260215", "Db": "us", "Ph": "build a website with ai", "Nq": 1600, "Cp": 5.90, "Co": 0.51, "Nr": 392000000, "Td": "0.60,0.62,0.64,0.67,0.70,0.74,0.79,0.83,0.88,0.92,0.96,1.00", "In": 1, "Kd": 45, "Fk": "rel,fsn,vid,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai landing page generator", "Nq": 900, "Cp": 11.20, "Co": 0.63, "Nr": 98000000, "Td": "0.72,0.73,0.74,0.76,0.78,0.80,0.83,0.86,0.90,0.93,0.96,1.00", "In": 0, "Kd": 51, "Fk": "adt,adb,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "no code website builder", "Nq": 2900, "Cp": 7.05, "Co": 0.60, "Nr": 318000000, "Td": "0.85,0.84,0.83,0.82,0.81,0.80,0.80,0.81,0.83,0.86,0.92,1.00", "In": 0, "Kd": 63, "Fk": "kng,rel,res,adt"},
            {"Dt": "20260215", "Db": "us", "Ph": "website templates", "Nq": 14800, "Cp": 2.15, "Co": 0.42, "Nr": 1990000000, "Td": "0.95,0.92,0.90,0.88,0.86,0.84,0.82,0.81,0.82,0.86,0.92,1.00", "In": 1, "Kd": 78, "Fk": "img,car,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "business website templates", "Nq": 3600, "Cp": 2.78, "Co": 0.40, "Nr": 476000000, "Td": "0.92,0.90,0.88,0.86,0.85,0.83,0.81,0.80,0.81,0.84,0.90,1.00", "In": 1, "Kd": 61, "Fk": "img,car,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "restaurant website template", "Nq": 2200, "Cp": 3.10, "Co": 0.44, "Nr": 215000000, "Td": "0.98,0.95,0.90,0.86,0.82,0.78,0.74,0.72,0.74,0.80,0.90,1.00", "In": 1, "Kd": 47, "Fk": "img,car,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "real estate website template", "Nq": 1800, "Cp": 6.45, "Co": 0.53, "Nr": 172000000, "Td": "0.86,0.85,0.84,0.83,0.82,0.82,0.83,0.85,0.88,0.92,0.96,1.00", "In": 0, "Kd": 55, "Fk": "img,car,rel,res,adt"},
            {"Dt": "20260215", "Db": "us", "Ph": "photography website template", "Nq": 2400, "Cp": 2.90, "Co": 0.39, "Nr": 338000000, "Td": "0.90,0.88,0.86,0.84,0.83,0.82,0.81,0.82,0.84,0.88,0.94,1.00", "In": 1, "Kd": 52, "Fk": "img,car,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "website builder for small business", "Nq": 5400, "Cp": 9.80, "Co": 0.65, "Nr": 684000000, "Td": "0.84,0.85,0.86,0.86,0.85,0.84,0.83,0.82,0.83,0.86,0.92,1.00", "In": 0, "Kd": 59, "Fk": "adt,adb,rel,kng"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder for small business", "Nq": 320, "Cp": 10.60, "Co": 0.52, "Nr": 98000000, "Td": "0.70,0.71,0.72,0.74,0.76,0.78,0.81,0.84,0.88,0.92,0.96,1.00", "In": 0, "Kd": 32, "Fk": "aio,rel,res,adt"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder for photographers", "Nq": 140, "Cp": 7.20, "Co": 0.35, "Nr": 56000000, "Td": "0.68,0.69,0.70,0.71,0.73,0.75,0.78,0.82,0.86,0.90,0.95,1.00", "In": 0, "Kd": 22, "Fk": "aio,rel,res,img"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder for real estate agents", "Nq": 170, "Cp": 12.40, "Co": 0.48, "Nr": 72000000, "Td": "0.66,0.67,0.68,0.70,0.73,0.77,0.81,0.85,0.89,0.93,0.97,1.00", "In": 0, "Kd": 27, "Fk": "aio,rel,res,adt"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder for restaurants", "Nq": 110, "Cp": 8.80, "Co": 0.33, "Nr": 48000000, "Td": "0.65,0.66,0.67,0.68,0.70,0.73,0.78,0.82,0.87,0.92,0.96,1.00", "In": 0, "Kd": 21, "Fk": "aio,rel,res,img"},
            {"Dt": "20260215", "Db": "us", "Ph": "wix ai website builder", "Nq": 720, "Cp": 3.20, "Co": 0.44, "Nr": 82000000, "Td": "0.78,0.79,0.80,0.82,0.84,0.86,0.87,0.88,0.90,0.93,0.96,1.00", "In": 2, "Kd": 38, "Fk": "kng,rel,res,adt"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder vs wix", "Nq": 260, "Cp": 4.70, "Co": 0.38, "Nr": 64000000, "Td": "0.72,0.73,0.74,0.76,0.78,0.80,0.82,0.84,0.87,0.91,0.95,1.00", "In": 1, "Kd": 29, "Fk": "rel,res,fsn"},
            {"Dt": "20260215", "Db": "us", "Ph": "squarespace ai website builder", "Nq": 260, "Cp": 2.90, "Co": 0.36, "Nr": 61000000, "Td": "0.80,0.81,0.82,0.83,0.84,0.85,0.86,0.88,0.90,0.93,0.96,1.00", "In": 2, "Kd": 35, "Fk": "kng,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "wordpress ai website builder", "Nq": 210, "Cp": 3.60, "Co": 0.31, "Nr": 76000000, "Td": "0.76,0.77,0.78,0.79,0.80,0.82,0.84,0.86,0.89,0.92,0.96,1.00", "In": 2, "Kd": 33, "Fk": "kng,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "website builder integrations", "Nq": 590, "Cp": 7.85, "Co": 0.50, "Nr": 214000000, "Td": "0.88,0.86,0.84,0.82,0.81,0.80,0.80,0.81,0.83,0.86,0.92,1.00", "In": 1, "Kd": 44, "Fk": "rel,res,kng"},
            {"Dt": "20260215", "Db": "us", "Ph": "zapier website builder", "Nq": 260, "Cp": 9.10, "Co": 0.42, "Nr": 98000000, "Td": "0.86,0.85,0.84,0.83,0.82,0.82,0.83,0.85,0.88,0.92,0.96,1.00", "In": 3, "Kd": 28, "Fk": "rel,res,kng"},
            {"Dt": "20260215", "Db": "us", "Ph": "how to build a website with ai", "Nq": 1000, "Cp": 3.40, "Co": 0.28, "Nr": 398000000, "Td": "0.60,0.62,0.64,0.67,0.70,0.74,0.79,0.83,0.88,0.92,0.96,1.00", "In": 1, "Kd": 41, "Fk": "rel,fsn,vid,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website design", "Nq": 3600, "Cp": 6.90, "Co": 0.49, "Nr": 512000000, "Td": "0.70,0.72,0.74,0.76,0.79,0.82,0.85,0.88,0.91,0.94,0.97,1.00", "In": 1, "Kd": 57, "Fk": "aio,img,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "generate website from prompt", "Nq": 520, "Cp": 5.10, "Co": 0.34, "Nr": 116000000, "Td": "0.62,0.64,0.66,0.69,0.73,0.77,0.82,0.86,0.90,0.93,0.97,1.00", "In": 1, "Kd": 36, "Fk": "aio,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "website builder pricing", "Nq": 2400, "Cp": 6.60, "Co": 0.58, "Nr": 736000000, "Td": "0.84,0.83,0.82,0.81,0.80,0.80,0.81,0.83,0.86,0.90,0.95,1.00", "In": 0, "Kd": 61, "Fk": "adt,adb,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder pricing", "Nq": 210, "Cp": 9.30, "Co": 0.46, "Nr": 91000000, "Td": "0.72,0.73,0.74,0.75,0.77,0.80,0.83,0.86,0.90,0.93,0.96,1.00", "In": 0, "Kd": 34, "Fk": "adt,adb,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "website builder features", "Nq": 1600, "Cp": 5.70, "Co": 0.45, "Nr": 692000000, "Td": "0.86,0.85,0.84,0.83,0.82,0.81,0.81,0.82,0.84,0.88,0.94,1.00", "In": 1, "Kd": 48, "Fk": "rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "seo tools for website builder", "Nq": 260, "Cp": 7.90, "Co": 0.40, "Nr": 124000000, "Td": "0.88,0.86,0.84,0.83,0.82,0.82,0.83,0.85,0.88,0.92,0.96,1.00", "In": 1, "Kd": 33, "Fk": "rel,res,fsn"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai copywriter for website", "Nq": 720, "Cp": 12.80, "Co": 0.57, "Nr": 186000000, "Td": "0.76,0.78,0.80,0.82,0.84,0.86,0.88,0.90,0.92,0.94,0.97,1.00", "In": 0, "Kd": 49, "Fk": "aio,rel,res,adt"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder reviews", "Nq": 590, "Cp": 6.30, "Co": 0.39, "Nr": 152000000, "Td": "0.72,0.74,0.76,0.78,0.80,0.82,0.85,0.88,0.91,0.94,0.97,1.00", "In": 1, "Kd": 43, "Fk": "rel,res,rev"},
            {"Dt": "20260215", "Db": "us", "Ph": "best website builder for small business", "Nq": 8100, "Cp": 12.10, "Co": 0.72, "Nr": 812000000, "Td": "0.82,0.83,0.84,0.85,0.85,0.84,0.83,0.82,0.83,0.86,0.92,1.00", "In": 0, "Kd": 71, "Fk": "adt,adb,rel,res,kng"},
            {"Dt": "20260215", "Db": "us", "Ph": "best website builder", "Nq": 49500, "Cp": 6.85, "Co": 0.75, "Nr": 3210000000, "Td": "0.90,0.88,0.86,0.85,0.84,0.83,0.82,0.82,0.83,0.86,0.92,1.00", "In": 0, "Kd": 88, "Fk": "adt,adb,kng,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder for ecommerce", "Nq": 320, "Cp": 14.60, "Co": 0.61, "Nr": 132000000, "Td": "0.68,0.69,0.70,0.72,0.74,0.77,0.80,0.84,0.88,0.92,0.96,1.00", "In": 0, "Kd": 39, "Fk": "aio,adt,rel,res"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website generator", "Nq": 2900, "Cp": 7.40, "Co": 0.58, "Nr": 488000000, "Td": "0.72,0.73,0.74,0.76,0.79,0.82,0.85,0.88,0.91,0.94,0.97,1.00", "In": 1, "Kd": 54, "Fk": "aio,rel,res,vid"},
            {"Dt": "20260215", "Db": "us", "Ph": "ai website builder for plumbers", "Nq": 90, "Cp": 10.20, "Co": 0.29, "Nr": 41000000, "Td": "0.65,0.66,0.67,0.68,0.70,0.72,0.76,0.81,0.86,0.91,0.96,1.00", "In": 0, "Kd": 18, "Fk": "aio,rel,res"},
        ],
    }
