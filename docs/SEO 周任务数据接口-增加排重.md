# SEO 周任务数据接口

> 本文档基于你现有的 `/api/seo/weekly-plan-input` 接口说明补充新需求：**冷却期（cooldown）**、**会话线程排重（thread exclude）**、以及服务端计算后的 **eligible_keywords** 输出。 SEO周任务数据接口

------

## API 概览

### Endpoint（推荐）

```
POST /api/seo/weekly-plan-input
Content-Type: application/json
```

### 目标

一次性返回 **AI 周任务生成**所需的输入数据集，并由**站点侧（PHP）统一执行排重/冷却期**，输出本次生成可用的候选关键词：

- 站点页面清单（pages）
- 关键词资产库（keyword_assets）
- Semrush 周快照（semrush_snapshot：你入库的 export_columns 全字段）
- 冷却期规则（cooldown）及排重统计信息
- `eligible_keywords`：本周可用关键词（已排除“跨周已发布” + “同 thread 已使用”）

------

## 请求参数（POST JSON）

### Request Body

| 字段                      | 类型           | 必填 | 示例                                                   | 说明                                                         |
| ------------------------- | -------------- | ---- | ------------------------------------------------------ | ------------------------------------------------------------ |
| `week_start`              | string(date)   | 是   | `2026-02-02`                                           | ISO 周周一（你现有逻辑）                                     |
| `include`                 | string / array | 否   | `["pages","assets","semrush","eligible"]`              | 默认全包含；可裁剪减少数据量                                 |
| `page_types`              | string / array | 否   | `["general_page","landing_page"]`                      | 只取部分页面类型（可选）                                     |
| `language`                | string         | 否   | `en-US`                                                | 站点主语言/本周生成语言（可选）                              |
| `country`                 | string         | 否   | `US`                                                   | 国家库（可选；用于 Semrush database/资产库过滤）             |
| `thread_id`               | string         | 否   | `thread_abc123`                                        | 驾驶舱同会话标识（用于观测/定位问题；不参与业务规则也可）    |
| `thread_exclude_keywords` | array<string>  | 否   | `["ai website builder","restaurant website template"]` | **驾驶舱从同 thread 历史抽取**：本会话已生成周任务使用过的主关键词（用于本次排重） |
| `cooldown_weeks`          | integer        | 否   | `8`                                                    | 冷却期周数，默认推荐 `8`（站点侧可固定不允许外部改）         |
| `cooldown_scope`          | string         | 否   | `primary_keyword`                                      | 一期建议固定 `primary_keyword`（主关键词冷却）               |

### 示例请求

```json
{
  "week_start": "2026-02-02",
  "include": ["pages", "assets", "semrush", "eligible"],
  "page_types": ["general_page", "landing_page", "detail_page", "list_page"],
  "language": "en-US",
  "country": "US",
  "thread_id": "thread_abc123",
  "thread_exclude_keywords": [
    "ai website builder",
    "restaurant website template"
  ],
  "cooldown_weeks": 8,
  "cooldown_scope": "primary_keyword"
}
```

------

## 响应结构（JSON）

### 顶层结构

```
{
  "meta": { ... },
  "cooldown": { ... },
  "eligibility": { ... },
  "dedup_stats": { ... },

  "pages": [ ... ],
  "keyword_assets": [ ... ],
  "semrush_snapshot": [ ... ],

  "eligible_keywords": [ ... ],
  "excluded_keywords": [ ... ]
}
```

------

## meta

在原有 `meta` 上建议新增两项：冷却/排重信息可追踪、semrush_snapshot 标识更明确。

```
{
  "meta": {
    "tenant_id": "t_123",
    "site_id": "s_456",
    "week_start": "2026-02-02",
    "week_end": "2026-02-09",
    "generated_at": "2026-02-04T10:12:00Z",
    "timezone": "America/Los_Angeles",
    "sources": {
      "pages": "cms_db",
      "keyword_assets": "cms_db",
      "semrush_snapshot": "cms_db (ingested from semrush)",
      "published_keyword_usage": "cms_db (content seo metadata)"
    },
    "semrush": {
      "database": "us",
      "export_columns": "Ph,Nq,Cp,Co,Nr,Td,Kd,In,Fk"
    },
    "filters": {
      "language": "en-US",
      "country": "US",
      "page_types": ["general_page","landing_page","detail_page","list_page"]
    }
  }
}
```

------

## cooldown（新增）

> 冷却期由站点侧统一执行。

```
{
  "cooldown": {
    "weeks": 8,
    "scope": "primary_keyword",
    "based_on": "first_published_at",
    "window": {
      "start_inclusive": "2025-12-07",
      "end_exclusive": "2026-02-02"
    }
  }
}
```

- `based_on`：建议一期固定 `first_published_at`（首次发布），避免“编辑一次就刷新冷却期导致永远不可复用”。

------

## eligibility（新增）

当 `eligible_keywords` 为空时，给驾驶舱明确原因，别让 UI 只能显示空白。

```
{
  "eligibility": {
    "status": "OK",
    "reason_code": null,
    "message": null
  }
}
```

可能的 `status / reason_code`：

- `OK`
- `EMPTY / NO_ELIGIBLE_KEYWORDS_AFTER_DEDUP`：冷却期 + thread 排重后没有候选
- `EMPTY / NO_KEYWORD_ASSETS`：资产库为空
- `EMPTY / NO_SEMRUSH_SNAPSHOT`：本周没有 semrush 数据（如果你要求必须有快照）

------

## dedup_stats（新增）

用于观测与调参（不影响一期生成逻辑，但非常利于排查为什么“本周为空”）。

```
{
  "dedup_stats": {
    "assets_total": 120,
    "assets_after_language_country_filter": 95,
    "excluded_by_cooldown": 30,
    "excluded_by_thread": 10,
    "eligible_total": 55
  }
}
```

------

## pages

- `page_id`
- `url`
- `title`
- `page_type`
- `status: published|draft`
- `updated_at`

------

## keyword_assets

- `keyword_id`
- `keyword`
- `asset_type: core|expanded|longtail`
- `priority: 1–5`
- `language/country`
- `tags`（可选）

------

## eligible_keywords（新增核心输出）

这是你新增需求的关键：站点侧返回**本次生成可用**的关键词（已过滤）。

> 建议至少包含：资产库字段 +（如果有）Semrush字段，用于后续“生成服务挑选/排序”。

```json
{
  "eligible_keywords": [
    {
      "keyword_id": "k_001",
      "keyword": "ai website builder",
      "asset_type": "core",
      "priority": 5,
      "language": "en",
      "country": "US",

      "semrush": {
        "Nq": 4400,
        "Cp": 8.12,
        "Co": 0.72,
        "Nr": 532000000,
        "Td": "62,64,66,65,63,60,58,59,61,63,64,65",
        "Kd": 58,
        "In": 0,
        "Fk": "knowledge_panel,local_pack,people_also_ask"
      }
    }
  ]
}
```

### 站点侧生成 eligible_keywords 的规则

候选集合来源：`keyword_assets`（按 language/country 过滤）
 然后按以下顺序排除：

1. **冷却期排除**：最近 `cooldown_weeks` 窗口内，已发布内容使用过的 `primary_keyword_norm`
2. **thread 排除**：`thread_exclude_keywords` 中出现的 `keyword_norm`

------

##  excluded_keywords

用于解释为什么没选上（对你后续调试非常重要）。

```json
{
  "excluded_keywords": [
    {
      "keyword": "ai website builder",
      "reason": "COOLDOWN",
      "last_used_week_start": "2026-01-13",
      "last_published_at": "2026-01-15T02:10:00Z"
    },
    {
      "keyword": "restaurant website template",
      "reason": "THREAD_EXCLUDE"
    }
  ]
}
```

------

## 端到端响应示例

```json
{
  "meta": {
    "tenant_id": "t_123",
    "site_id": "s_456",
    "week_start": "2026-02-02",
    "week_end": "2026-02-09",
    "generated_at": "2026-02-04T10:12:00Z",
    "timezone": "America/Los_Angeles",
    "sources": {
      "pages": "cms_db",
      "keyword_assets": "cms_db",
      "semrush_snapshot": "cms_db (ingested from semrush)",
      "published_keyword_usage": "cms_db (content seo metadata)"
    },
    "semrush": { "database": "us", "export_columns": "Ph,Nq,Cp,Co,Nr,Td,Kd,In,Fk" },
    "filters": { "language": "en-US", "country": "US", "page_types": ["general_page","landing_page"] }
  },
  "cooldown": {
    "weeks": 8,
    "scope": "primary_keyword",
    "based_on": "first_published_at",
    "window": { "start_inclusive": "2025-12-07", "end_exclusive": "2026-02-02" }
  },
  "eligibility": { "status": "OK", "reason_code": null, "message": null },
  "dedup_stats": {
    "assets_total": 20,
    "assets_after_language_country_filter": 20,
    "excluded_by_cooldown": 6,
    "excluded_by_thread": 2,
    "eligible_total": 12
  },

  "pages": [ { "page_id": "p_001", "url": "https://example.com/pricing", "title": "Pricing", "page_type": "landing_page", "status": "published", "updated_at": "2026-02-01T08:00:00Z" } ],
  "keyword_assets": [ { "keyword_id": "k_001", "keyword": "ai website builder", "asset_type": "core", "priority": 5, "language": "en", "country": "US", "tags": ["product","commercial"] } ],
  "semrush_snapshot": [ { "keyword": "ai website builder", "Nq": 4400, "Cp": 8.12, "Co": 0.72, "Nr": 532000000, "Td": "62,64,66,65,63,60,58,59,61,63,64,65", "Kd": 58, "In": 0, "Fk": "knowledge_panel,local_pack,people_also_ask" } ],

  "eligible_keywords": [
    {
      "keyword_id": "k_101",
      "keyword": "best ai website builder",
      "asset_type": "expanded",
      "priority": 4,
      "language": "en",
      "country": "US",
      "semrush": { "Nq": 1900, "Cp": 9.54, "Co": 0.62, "Nr": 214000000, "Kd": 52, "In": 0, "Td": "0.70,0.72,0.73,0.75,0.78,0.80,0.84,0.86,0.90,0.93,0.96,1.00", "Fk": "aio,fsn,rel,res,kng" }
    }
  ],
  "excluded_keywords": [
    { "keyword": "ai website builder", "reason": "THREAD_EXCLUDE" }
  ]
}
```

------

## 字段说明与来源

### 冷却期数据来源

你需要在“真实发布内容”侧可查询到主关键词，最低成本做法：

- 内容实体（page/post）上有 `seo_primary_keyword`（或等价字段）
- 发布时将其写入（可从编辑器 SEO 设置、或从你 AI 发布流程写入）

冷却期判断查询口径：

- `status = published`
- 时间窗口：`first_published_at ∈ [week_start - cooldown_weeks*7d, week_start)`

产出集合：`recent_published_primary_keywords_norm`



## 排重规则（冷却期 + thread_exclude_keywords）

### 目标

站点侧（PHP）作为**唯一业务规则源**，在返回 `eligible_keywords` 前对关键词做两类排重：

1. **冷却期排重（Cooldown）**：最近 N 周内已经“发布过并绑定主关键词”的关键词，本周不可再作为候选主关键词返回
2. **会话排重（Thread Exclude）**：同一驾驶舱 thread 内已经用于生成周任务的关键词，本次请求不可再返回（避免用户同会话多次触发出现重复）

> 一期建议排重范围只覆盖 **主关键词（primary keyword）**，不做语义去重/同义词归并（后续二期再加）。

------

## 归一化规则（keyword_norm）

所有排重判断必须基于 `keyword_norm`（避免大小写/空格差异绕过去重）。

**建议实现：**

- `trim()` 去首尾空格
- 全部转小写
- 将连续空格折叠为单空格
- 去掉结尾常见标点（可选：`.` `,` `!` `?` `:` `;`）

伪代码：

```
function keyword_norm(string $k): string {
  $k = trim(mb_strtolower($k));
  $k = preg_replace('/\s+/u', ' ', $k);
  $k = preg_replace('/[.,!?;:]+$/u', '', $k);
  return $k;
}
```

------

## 冷却期（Cooldown）规则

### 参数

- `cooldown_weeks`：默认建议 `8`（也可站点侧配置化）
- `cooldown_scope`：一期固定 `primary_keyword`
- `based_on`：建议固定 `first_published_at`（首次发布时间），避免“编辑一次就刷新冷却期导致永远不可复用”

### 判定口径（什么叫“已发布”）

将“已发布”定义为：**对外可访问的内容实体**，满足：

- `status = published`
- `first_published_at` 存在
- 内容有 `seo_primary_keyword`（或等价字段）可回查

### 时间窗口

给定请求 `week_start`：

- `window_start = week_start - cooldown_weeks * 7 days`
- `window_end = week_start`（不含 week_start 当天）

命中条件：

- `first_published_at ∈ [window_start, window_end)`
- `keyword_norm(seo_primary_keyword)` 与候选关键词相等

### 冷却集合生成

站点侧从内容库生成集合：

- `cooldown_set = { keyword_norm(primary_keyword) }`

------

## 会话排重（thread_exclude_keywords）规则

### 参数

- `thread_exclude_keywords[]`：驾驶舱同一 thread 内已生成周任务使用过的“主关键词列表”
- 站点侧将其归一化：
  - `thread_set = { keyword_norm(k) for k in thread_exclude_keywords }`

> 注意：thread_exclude_keywords 不需要也不应该由站点侧持久化；它只是本次请求的“额外过滤条件”。

------

## 排重顺序与优先级

### 推荐执行顺序（清晰且可解释）

1. **构建候选集**：从 `keyword_assets`（按 language/country 过滤后）得到 `candidate_keywords`
2. **构建排重集合**：
   - `cooldown_set`（跨周已发布）
   - `thread_set`（同会话已用）
3. **过滤候选集**：
   - 若 `keyword_norm(k) ∈ cooldown_set` → 排除
   - 若 `keyword_norm(k) ∈ thread_set` → 排除
4. 产出：
   - `eligible_keywords`：未被排除的关键词（可附带 semrush 指标）
   - `excluded_keywords`：被排除关键词及原因（建议支持多原因）

### 原因优先级（用于展示/统计）

如果同一个关键词同时命中两类排重，建议记录为 **多原因**：

- `reasons: ["COOLDOWN", "THREAD_EXCLUDE"]`

如果你必须只返回一个原因，建议优先返回 `THREAD_EXCLUDE`（因为更“即时”、用户更容易理解），但**内部统计仍建议保留两个命中计数**。

------

## 输出字段与 reason_code（建议）

### `excluded_keywords[]`

建议结构：

```
{
  "keyword": "ai website builder",
  "keyword_norm": "ai website builder",
  "reasons": ["COOLDOWN", "THREAD_EXCLUDE"],
  "cooldown": {
    "last_published_at": "2026-01-15T02:10:00Z",
    "last_used_week_start": "2026-01-13"
  }
}
```

### `dedup_stats`

建议统计口径：

- `excluded_by_cooldown`：命中 cooldown 的数量（按 keyword_norm 去重计数）
- `excluded_by_thread`：命中 thread 的数量
- `excluded_by_both`：同时命中两者数量（可选）
- `eligible_total`：最终可用数量

### `eligibility`

当 `eligible_keywords=[]` 时：

- `status = "EMPTY"`
- `reason_code = "NO_ELIGIBLE_KEYWORDS_AFTER_DEDUP"`
- `message`：给用户/前端可读说明（建议包含 cooldown_weeks 和 thread_exclude_count）