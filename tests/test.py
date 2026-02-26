"""
关键词 -> 页面 映射程序 (V0)
- 关键词聚类 (基于 Embedding + HDBSCAN)
- 将每个聚类分配给最佳页面 (仅基于 title+url+type)
- 输出可解释的 JSON 原因报告

依赖库:
  pip install scikit-learn numpy requests
"""

from __future__ import annotations

import json
import math
import uuid
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import urlparse

import requests
import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity


# ----------------------------
# 工具函数
# ----------------------------

# ----------------------------
# 工具与评分逻辑
# ----------------------------

@dataclass
class ValueScoreWeights:
    # 正向：越大越优先
    w_volume: float = 0.35        # Nq
    w_cpc: float = 0.20           # Cp
    w_trend: float = 0.15         # Td (综合 avg/last_vs_avg/slope)
    w_intent: float = 0.10        # In (可调)
    w_serp_features: float = 0.05 # Fk (可调，若你不想用就设 0)

    # 负向：越大越不优先（越难）
    w_competition: float = 0.10   # Co
    w_results: float = 0.03       # Nr
    w_kd: float = 0.02            # Kd

    # intent 偏好（你可以按产品策略改）
    intent_bonus: Dict[str, float] = None

    def __post_init__(self):
        if self.intent_bonus is None:
            # V0：偏商业/交易，其次信息（因为新站也需要内容增长），导航最低
            self.intent_bonus = {
                "transactional": 1.00,
                "commercial": 0.85,
                "informational": 0.55,
                "navigational": 0.20,
                "unknown": 0.40,
            }

def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        if isinstance(v, str) and v.strip() == "":
            return default
        return float(v)
    except Exception:
        return default

def _log1p(v: float) -> float:
    return math.log1p(max(v, 0.0))

def _minmax(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return (x - lo) / (hi - lo)

def parse_fk(fk: Any) -> List[int]:
    """
    phrase_fullsearch 的 Fk 通常是 '5,9,13,21,36' 这种字符串
    """
    if fk is None:
        return []
    if isinstance(fk, list):
        return [int(i) for i in fk if str(i).strip().isdigit()]
    s = str(fk).strip()
    if not s:
        return []
    out = []
    for part in s.split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out

def parse_trend(td: Any) -> List[float]:
    """
    改进版趋势解析：支持处理逗号分隔的字符串
    """
    if td is None:
        return []
    if isinstance(td, list):
        return [_safe_float(v) for v in td]
    if isinstance(td, str):
        parts = [p.strip() for p in td.split(",") if p.strip() != ""]
        return [_safe_float(p) for p in parts]
    return []

def trend_features(td: Any) -> Dict[str, float]:
    """
    Td 是 12 个点，范围通常 0~1。我们提取：
    - avg：平均热度
    - last_vs_avg：最后一个月 / 平均
    - slope：线性趋势斜率（粗略）
    """
    vals = parse_trend(td)

    if len(vals) == 0:
        return {"avg": 0.0, "last_vs_avg": 0.0, "slope": 0.0}

    arr = np.array(vals, dtype=float)
    avg = float(arr.mean())
    last = float(arr[-1])
    last_vs_avg = float(last / avg) if avg > 1e-9 else 0.0

    # slope (simple linear regression on index)
    x = np.arange(len(arr), dtype=float)
    x_mean = float(x.mean())
    y_mean = float(arr.mean())
    denom = float(((x - x_mean) ** 2).sum())
    slope = float(((x - x_mean) * (arr - y_mean)).sum() / denom) if denom > 1e-9 else 0.0

    return {"avg": avg, "last_vs_avg": last_vs_avg, "slope": slope}

def intent_label(intent: Any) -> str:
    m = {
        0: "commercial",
        1: "informational",
        2: "navigational",
        3: "transactional",
    }
    # Handle '1,0' strings by taking the first one
    if isinstance(intent, str):
        intent = intent.split(",")[0].strip()
    
    i = int(_safe_float(intent, -1))
    return m.get(i, "unknown")

def keyword_value_score_full(
    kw: Dict[str, Any],
    stats: Dict[str, Tuple[float, float]],
    w: Optional[ValueScoreWeights] = None,
) -> Tuple[float, Dict[str, Any]]:
    if w is None:
        w = ValueScoreWeights()
        
    # 取数
    Nq = _safe_float(kw.get("Nq"))
    Cp = _safe_float(kw.get("Cp"))
    Co = _safe_float(kw.get("Co"))
    Nr = _safe_float(kw.get("Nr"))
    Kd = _safe_float(kw.get("Kd"))
    In = kw.get("In")

    fk_list = parse_fk(kw.get("Fk"))
    fk_cnt = float(len(fk_list))

    tf = trend_features(kw.get("Td"))

    # 归一化（建议对长尾分布的字段先 log1p）
    logNq = _log1p(Nq)
    logCp = _log1p(Cp)
    logNr = _log1p(Nr)

    n_volume = _minmax(logNq, *stats.get("logNq", (0.0, 1.0)))
    n_cpc    = _minmax(logCp, *stats.get("logCp", (0.0, 1.0)))
    n_comp   = _minmax(Co,   *stats.get("Co",    (0.0, 1.0)))
    n_results= _minmax(logNr,*stats.get("logNr", (0.0, 1.0)))
    n_kd     = _minmax(Kd,   *stats.get("Kd",    (0.0, 100.0)))
    n_fk     = _minmax(fk_cnt, *stats.get("fk_cnt", (0.0, 10.0)))

    # trend 合成：avg + last/avg + slope（都做轻量归一化）
    trend_raw = 0.5 * tf["avg"] + 0.35 * min(tf["last_vs_avg"], 2.0) / 2.0 + 0.15 * (tf["slope"] + 1) / 2.0
    n_trend = _minmax(trend_raw, *stats.get("trend", (0.0, 1.0)))

    # intent bonus
    il = intent_label(In)
    n_intent = w.intent_bonus.get(il, 0.4)

    # 线性加权（可解释）
    pos = (
        w.w_volume * n_volume +
        w.w_cpc * n_cpc +
        w.w_trend * n_trend +
        w.w_intent * n_intent +
        w.w_serp_features * n_fk
    )
    neg = (
        w.w_competition * n_comp +
        w.w_results * n_results +
        w.w_kd * n_kd
    )

    score = max(0.0, pos - neg)

    breakdown = {
        "raw": {
            "Nq": Nq, "Cp": Cp, "Co": Co, "Nr": Nr, "Kd": Kd,
            "In": In, "intent_label": il,
            "Fk": fk_list, "fk_cnt": fk_cnt,
            "Td": kw.get("Td") if isinstance(kw.get("Td"), str) else str(kw.get("Td")),
            "trend_features": tf,
        },
        "norm": {
            "volume": round(n_volume, 3),
            "cpc": round(n_cpc, 3),
            "trend": round(n_trend, 3),
            "intent": round(n_intent, 3),
            "serp_features": round(n_fk, 3),
            "competition": round(n_comp, 3),
            "results": round(n_results, 3),
            "kd": round(n_kd, 3),
        },
        "pos": round(pos, 3),
        "neg": round(neg, 3),
        "score": round(score, 3),
    }
    return score, breakdown

def build_stats_for_fullsearch(rows: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    logNq = []
    logCp = []
    Co = []
    logNr = []
    Kd = []
    fk_cnt = []
    trend = []

    for r in rows:
        logNq.append(_log1p(_safe_float(r.get("Nq"))))
        logCp.append(_log1p(_safe_float(r.get("Cp"))))
        Co.append(_safe_float(r.get("Co")))
        logNr.append(_log1p(_safe_float(r.get("Nr"))))
        Kd.append(_safe_float(r.get("Kd")))
        fk_cnt.append(float(len(parse_fk(r.get("Fk")))))

        tf = trend_features(r.get("Td"))
        trend_raw = 0.5 * tf["avg"] + 0.35 * min(tf["last_vs_avg"], 2.0) / 2.0 + 0.15 * (tf["slope"] + 1) / 2.0
        trend.append(trend_raw)

    def mm(arr: List[float], default=(0.0, 1.0)) -> Tuple[float, float]:
        if not arr:
            return default
        lo = float(np.min(arr))
        hi = float(np.max(arr))
        if math.isfinite(lo) and math.isfinite(hi) and hi > lo:
            return (lo, hi)
        return default

    return {
        "logNq": mm(logNq, (0.0, 10.0)),
        "logCp": mm(logCp, (0.0, 5.0)),
        "Co":    mm(Co,    (0.0, 1.0)),
        "logNr": mm(logNr, (0.0, 15.0)),
        "Kd":    mm(Kd,    (0.0, 100.0)),
        "fk_cnt":mm(fk_cnt,(0.0, 10.0)),
        "trend": mm(trend, (0.0, 1.0)),
    }

def normalize_keyword(k: str) -> str:
    k = (k or "").strip()
    k = re.sub(r"\s+", " ", k)
    return k

def url_tokens(url: str) -> str:
    try:
        p = urlparse(url)
        path = p.path or url
    except Exception:
        path = url or ""
    path = path.lower()
    path = re.sub(r"[/\-_\.]+", " ", path)
    return re.sub(r"\s+", " ", path).strip()

def predict_page_intent(page_type: str, url: str, title: str) -> str:
    t = (page_type or "").lower()
    u = (url or "").lower()
    ttl = (title or "").lower()

    info_markers = ["blog", "news", "guide", "how", "tutorial", "docs", "help", "faq", "kb"]
    trans_markers = ["pricing", "price", "buy", "order", "signup", "register", "checkout", "quote", "demo"] # 交易类特征词
    nav_markers = ["about", "contact", "home", "homepage", "privacy", "terms"] # 导航类特征词

    if any(m in u or m in ttl for m in trans_markers):
        return "transactional"
    if any(m in u or m in ttl for m in info_markers):
        return "informational"
    if any(m in u or m in ttl for m in nav_markers):
        return "navigational"

    if t in ["post", "article", "blog", "guide", "faq", "doc"]:
        return "informational"
    if t in ["product", "pricing", "landing", "signup", "checkout"]:
        return "transactional"
    if t in ["home", "about", "contact"]:
        return "navigational"
    return "commercial"

def intent_match_score(keyword_intent: str, page_intent: str) -> float:
    if keyword_intent == page_intent:
        return 1.0
    close = {
        ("commercial", "transactional"),
        ("transactional", "commercial"),
        ("informational", "commercial"),
        ("commercial", "informational"),
    }
    if (keyword_intent, page_intent) in close:
        return 0.7
    return 0.2



# ----------------------------
# Vectorization & Clustering
# ----------------------------

def build_vectorizer() -> Any:
    """
    已弃用: 不再使用 TF-IDF.
    """
    return None

def call_embedding_api(texts: List[str]) -> np.ndarray:
    """
    调用 Azure OpenAI embedding API.
    """
    if not texts:
        return np.array([])
    
    url = "https://dev-ko.services.ai.azure.com/models/embeddings?api-version=2024-05-01-preview"
    headers = {
        "Authorization": "Bearer <YOUR_AZURE_OPENAI_KEY>",
        "Content-Type": "application/json"
    }
    
    # 简单分批处理以避免超出 payload 限制（虽然用户提供的示例很小）
    # 这里为了保险起见，每批处理 16 个
    batch_size = 16
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {
            "model": "embed-v-4-0",
            "input": batch
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # data 内容: {"data": [{"embedding": [...], "index": 0}, ...], ...}
            # 确保按 index 排序（通常 API 会保证顺序，但 index 字段存在就利用一下）
            batch_results = sorted(data.get("data", []), key=lambda x: x["index"])
            if not batch_results:
                 # 空响应或错误部分的后备处理？
                 # 填充零向量有风险，最好直接抛出异常
                 raise ValueError(f"批次 {i} 未返回数据")
            
            for item in batch_results:
                all_embeddings.append(item["embedding"])
                
        except Exception as e:
            print(f"调用 Embedding API 出错: {e}")
            # 后备方案：简单的零向量或重新抛出
            # 如果这里失败，整个脚本将失败。如果没有已知维度，很难填充零。目前仅在测试脚本中重新抛出。
            raise e

    return np.array(all_embeddings)

def vectorize_texts(vectorizer: Any, texts: List[str]):
    """
    忽略 'vectorizer' 参数。直接调用 API。
    返回稠密 numpy 数组。
    """
    return call_embedding_api(texts)

def cluster_keywords(keyword_texts: List[str], kw_matrix, min_cluster_size: int = 2) -> np.ndarray:
    """
    HDBSCAN 聚类
    """
    # 可视化或预处理：确保使用单位向量，以便在欧氏距离下表现出类似余弦相似度的行为
    kw_matrix = normalize(kw_matrix, norm='l2', axis=1)
    
    # HDBSCAN
    # 在归一化向量上 metric='euclidean' 近似于余弦相似度
    model = HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean', cluster_selection_method='eom')
    labels = model.fit_predict(kw_matrix)
    return labels


# ----------------------------
# 主程序: 映射逻辑
# ----------------------------

def map_keywords_to_pages(
    keywords: List[Dict[str, Any]],
    pages: List[Dict[str, Any]],
    max_secondary_per_page: int = 8,
    min_cluster_size: int = 2,
) -> Dict[str, Any]:
    """
    Return:
      {
        "clusters": [...],
        "assignments": [...],
        "page_keyword_map": {...}
      }
    """

    # 0) 构建统计数据以进行评分归一化
    score_stats = build_stats_for_fullsearch(keywords)
    
    # 评分辅助函数
    def get_score_tuple(k_row):
        return keyword_value_score_full(k_row, score_stats)

    # 1) 清洗与去重关键词
    dedup = {}
    for r in keywords:
        ph = normalize_keyword(r.get("Ph") or r.get("keyword") or "")
        if not ph:
            continue
        
        r2 = dict(r)
        r2["Ph"] = ph
        
        score_new, _ = get_score_tuple(r2)
        
        if ph not in dedup:
            dedup[ph] = r2
        else:
            score_old, _ = get_score_tuple(dedup[ph])
            if score_new > score_old:
                dedup[ph] = r2
                
    kw_rows = list(dedup.values())

    # 2) 准备关键词文本用于向量化
    kw_texts = [r["Ph"] for r in kw_rows]

    # 3) 定义向量化部分 (虚拟) 并执行向量化
    # 优化点: 一次性向量化所有唯一文本 (关键词 + 页面文本) 以节省 API 调用次数
    
    # 首先预测页面画像以获取匹配文本
    page_profiles = []
    for p in pages:
        page_id = p.get("page_id") or p.get("id")
        title = p.get("title", "") or ""
        url = p.get("url", "") or ""
        ptype = p.get("type", "") or ""
        intent = predict_page_intent(ptype, url, title)
        tokens = url_tokens(url)
        text_for_match = f"{title} {tokens} {ptype}".strip()
        page_profiles.append({
            "page_id": page_id,
            "title": title,
            "url": url,
            "type": ptype,
            "pred_intent": intent,
            "match_text": text_for_match,
        })

    page_texts = [pp["match_text"] for pp in page_profiles]
    
    # 向量化所有唯一文本
    all_texts = kw_texts + page_texts
    # 调用 API (内部已分批)
    all_embeddings = vectorize_texts(None, all_texts)
    
    kw_matrix = all_embeddings[:len(kw_texts)]
    page_mat2 = all_embeddings[len(kw_texts):]
    
    # 匹配矩阵形状 (n_samples, n_features)
    # kw_mat2 在此处是 kw_matrix 的别名，因为是我们一起向量化的
    kw_mat2 = kw_matrix 


    # 4) 关键词聚类 (仅使用 kw_matrix)
    labels = cluster_keywords(kw_texts, kw_matrix, min_cluster_size=min_cluster_size)

    # 5) 构建聚类
    clusters: Dict[int, List[int]] = {}
    for idx, lab in enumerate(labels):
        clusters.setdefault(int(lab), []).append(idx)



    # 辅助函数: 词法匹配
    def lexical_hits(kw: str, page_title: str, page_url: str) -> Tuple[List[str], List[str]]:
        kw_low = kw.lower()
        title_low = (page_title or "").lower()
        url_low = (page_url or "").lower()
        # 简单处理：提取 kw 的 token（按空格切分）
        tokens = [t for t in re.split(r"\s+", kw_low) if t]
        title_hit = [t for t in tokens if t in title_low][:5]
        url_hit = [t for t in tokens if t in url_low][:5]
        return title_hit, url_hit

    # 6) 将每个聚类分配给一个页面
    cluster_outputs = []
    mappings = []

    # 页面 -> 关键词 映射结果
    page_keyword_map: Dict[str, Dict[str, Any]] = {
        str(pp["page_id"]): {
            "page_id": pp["page_id"],
            "url": pp["url"],
            "title": pp["title"],
            "type": pp["type"],
            "primary_keyword": None,
            "secondary_keywords": [],
            "clusters": []
        } for pp in page_profiles
    }

    # 确保每个主关键词只被分配一次
    used_primary_keywords = set()

    # 按“最高价值”降序对聚类排序 (以便让高价值聚类优先挑选最佳页面)
    def cluster_value(lab: int) -> float:
        idxs = clusters[lab]
        if not idxs:
            return 0.0
        return max(get_score_tuple(kw_rows[i])[0] for i in idxs)

    sorted_cluster_labels = sorted(clusters.keys(), key=cluster_value, reverse=True)

    for lab in sorted_cluster_labels:
        idxs = clusters[lab]
        if lab == -1:
            # -1 是噪声点：每个关键词自己成“孤簇”
            # 你可以选择：把每个噪声点当一个 cluster
            pass

        # 聚类关键词
        cluster_kw_rows = [kw_rows[i] for i in idxs]
        # 意图分布
        intents = [intent_label(r.get("In")) for r in cluster_kw_rows]
        intent_dist = {}
        for it in intents:
            intent_dist[it] = intent_dist.get(it, 0) + 1
        cluster_intent = max(intent_dist.items(), key=lambda x: x[1])[0] if intent_dist else "commercial"

        # 在聚类内按价值分选择主关键词 (且未被使用过)
        sorted_kws = sorted(cluster_kw_rows, key=lambda k: get_score_tuple(k)[0], reverse=True)
        primary_kw_row = None
        for r in sorted_kws:
            if r["Ph"] not in used_primary_keywords:
                primary_kw_row = r
                break
        if primary_kw_row is None:
            primary_kw_row = sorted_kws[0] if sorted_kws else None

        if primary_kw_row is None:
            continue

        primary_kw = primary_kw_row["Ph"]
        p_score_val, p_score_breakdown = get_score_tuple(primary_kw_row)

        # 聚类代表向量: 聚类内所有关键词向量的均值
        cluster_vec = kw_mat2[idxs].mean(axis=0)

        # 计算与页面的语义相似度
        sims = cosine_similarity(cluster_vec.reshape(1, -1), page_mat2).reshape(-1)  # [num_pages]

        # 结合 semantic + intent + lexical 选择最佳页面
        best_j = None
        best_score = -1.0
        best_reason = None

        for j, pp in enumerate(page_profiles):
            page_int = pp["pred_intent"]
            im = intent_match_score(cluster_intent, page_int)

            title_hit, url_hit = lexical_hits(primary_kw, pp["title"], pp["url"])
            lex = 0.0
            if title_hit:
                lex += 0.12
            if url_hit:
                lex += 0.08

            # 价值信号: 使用主关键词的价值分略微加权 (对所有页面相同)
            v = p_score_val

            score = 0.65 * float(sims[j]) + 0.25 * im + 0.10 * lex

            if score > best_score:
                best_score = score
                best_j = j
                best_reason = {
                    "semantic_similarity": round(float(sims[j]), 4),
                    "intent": {
                        "cluster_intent": cluster_intent,
                        "page_intent": page_int,
                        "match_score": round(im, 2),
                    },
                    "lexical": {
                        "title_hits": title_hit,
                        "url_hits": url_hit,
                    },
                    "value_signals": p_score_breakdown,
                    "anti_cannibalization": {
                        "rule": "each_primary_keyword_unique",
                        "explain": "同一关键词只允许绑定一个主承接页，避免站内关键词内耗",
                    },
                }

        if best_j is None:
            continue

        target_page = page_profiles[best_j]
        target_page_id = str(target_page["page_id"])

        # 确定该页面的主/辅关键词
        used_primary_keywords.add(primary_kw)

        # 辅关键词: 按价值分取前 N 个 (排除主词)
        secondary = []
        for r in sorted_kws:
            if r["Ph"] == primary_kw:
                continue
            s_val, s_bd = get_score_tuple(r)
            secondary.append({
                "kw": r["Ph"],
                "Nq": _safe_float(r.get("Nq", 0)),
                "In": intent_label(r.get("In")),
                "value_score": round(s_val, 3),
                # "breakdown": s_bd # optional complexity
            })
            if len(secondary) >= max_secondary_per_page:
                break

        # cluster label (简单：取前3高价值词拼起来)
        top3 = [r["Ph"] for r in sorted_kws[:3]]
        cluster_label = " / ".join(top3) if top3 else primary_kw

        # 使用 UUIDv5 生成稳定 ID
        cluster_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, cluster_label))

        cluster_out = {
            "cluster_id": cluster_id,
            "cluster_label": cluster_label,
            "cluster_intent": cluster_intent,
            "intent_distribution": intent_dist,
            "primary_keyword": {
                "kw": primary_kw,
                "Nq": _safe_float(primary_kw_row.get("Nq", 0)),
                "In": intent_label(primary_kw_row.get("In")),
                "Cp": _safe_float(primary_kw_row.get("Cp", 0)),
                "Co": _safe_float(primary_kw_row.get("Co", 0)),
                "Nr": _safe_float(primary_kw_row.get("Nr", 0)),
                "trend_score": p_score_breakdown["norm"]["trend"], # use normalized trend score
                "value_score": round(p_score_val, 3),
                "breakdown": p_score_breakdown # rich details
            },
            "keywords": [],
        }
        
        for r in sorted_kws:
            r_val, r_bd = get_score_tuple(r)
            cluster_out["keywords"].append({
                "kw": r["Ph"],
                "Nq": _safe_float(r.get("Nq", 0)),
                "In": intent_label(r.get("In")),
                "value_score": round(r_val, 3)
            })
            
        cluster_outputs.append(cluster_out)

        # -------------------------------------------------------
        # 页面分配逻辑 (反蚕食 & 合并)
        # -------------------------------------------------------
        page_entry = page_keyword_map.get(target_page_id)
        assignment_role = "secondary_support" # 默认角色
        
        if page_entry:
            # 策略：如果页面当前没有 Primary，或者新 Cluster 的 Primary 价值更高，则抢占 Primary 位置
            # 否则，新 Cluster 作为 Secondary Topic (补充内容)
            
            current_primary = page_entry["primary_keyword"]
            
            if current_primary is None:
                # 抢占 Primary
                page_entry["primary_keyword"] = cluster_out["primary_keyword"]
                assignment_role = "primary_owner"
            else:
                existing_vs = current_primary.get("value_score", 0)
                new_vs = cluster_out["primary_keyword"].get("value_score", 0)
                
                if new_vs > existing_vs:
                    # 新 Cluster 价值更高 -> 抢占 Primary
                    # 原 Primary 降级为 Secondary
                    page_entry["secondary_keywords"].append({
                        "kw": current_primary["kw"],
                        "Nq": current_primary["Nq"],
                        "In": current_primary["In"],
                        "value_score": current_primary["value_score"],
                    })
                    page_entry["primary_keyword"] = cluster_out["primary_keyword"]
                    assignment_role = "primary_owner"
                else:
                    # 新 Cluster 价值不够 -> 作为 Secondary
                    # 其 Primary Keyword 也加入 Secondary 列表
                    page_entry["secondary_keywords"].append({
                        "kw": cluster_out["primary_keyword"]["kw"],
                        "Nq": cluster_out["primary_keyword"]["Nq"],
                        "In": cluster_out["primary_keyword"]["In"],
                        "value_score": cluster_out["primary_keyword"]["value_score"],
                    })
                    assignment_role = "secondary_support" # 明确标记为副手

            # 将该 Cluster 的所有词 (这里逻辑上是 cluster 的 secondary，但因为 cluster 被视为 page 的 secondary，所以它们都是 page 的 secondary)
            page_entry["secondary_keywords"].extend(secondary)
            
            # 记录 Cluster ID
            page_entry["clusters"].append(cluster_out["cluster_id"])
            
            # 去重 Page Secondary Keywords
            seen = set()
            uniq = []
            # 优先保留高价值的
            all_seconds = sorted(page_entry["secondary_keywords"], key=lambda x: x.get("value_score", 0), reverse=True)
            for s in all_seconds:
                k = s["kw"]
                if k in seen:
                    continue
                # 也不要和当前的 Primary 重复
                if page_entry["primary_keyword"] and k == page_entry["primary_keyword"]["kw"]:
                    continue
                seen.add(k)
                uniq.append(s)
            page_entry["secondary_keywords"] = uniq[:max_secondary_per_page]

        assign_out = {
            "cluster_id": cluster_out["cluster_id"],
            "target_page": {
                "page_id": target_page["page_id"],
                "url": target_page["url"],
                "title": target_page["title"],
                "type": target_page["type"],
            },
            "confidence": round(best_score, 3),
            "assignment_role": assignment_role, # 增加角色字段，解释冲突处理结果
            "reasons": best_reason,
            "cluster_primary_keyword": cluster_out["primary_keyword"], 
            "secondary_keywords": secondary,
        }
        mappings.append(assign_out)

    result = {
        "clusters": cluster_outputs,
        "mappings": mappings,
        "page_keyword_map": list(page_keyword_map.values()),
        "meta": {
            "num_keywords_input": len(keywords),
            "num_keywords_dedup": len(kw_rows),
            "num_pages": len(pages),
            "hdbscan_min_cluster_size": min_cluster_size,
            "notes": [
                "V1 uses Azure OpenAI Embeddings + HDBSCAN + Semantic Search.",
                "HDBSCAN clustering on L2-normalized embeddings with Euclidean distance.",
            ],
        },
    }
    return result


# ----------------------------
# 示例运行入口
# ----------------------------
if __name__ == "__main__":
    # 示例 Semrush 数据（Keyword;Search Volume;CPC;Competition;Number of Results;Trends;SERP Features;Intent）
    # 扩充数据以覆盖更多页面 (Audit, Local, Case Studies, Glossary, etc.)
    raw_csv_data = [
        # --- Existing (Cheap/AI/Amazon) ---
        "actor lee seo jin;880;0;0;20900000;0.24,0.16,1.00;5,9,13;1",
        "affordable seo packages;880;8.09;0.01;51100000;0.5,0.5,0.5;6,7,20,36;1",
        "affordable seo services for small businesses;880;9.81;0.03;28200000;0.9,0.9,0.9;5,6,36;1",
        "ai seo tool;2900;6.63;0.3;162000000;1.0,1.0,1.0;6,7,52;1,0",
        "amazon seo optimization;880;8.09;0.1;23700000;0.4,0.4,0.4;6,9,36;1",
        "artificial intelligence seo;500;5.57;0.4;0;0.8,0.8,0.9;6,7,52;1",
        "cheap seo;22000;11.21;0.04;73100000;0.5,0.5,0.5;6,7,36;1",
        "cheap seo services;880;8.7;0.04;22800000;0.6,0.6,0.6;3,6,36;3", # Transactional
        
        # --- Technical / Audit ---
        "technical seo audit;1900;15.0;0.45;5000000;0.3,0.3,0.5;1,2,3;0",
        "seo audit checklist;1600;8.5;0.35;3000000;0.4,0.4,0.4;1,5;1", # Info
        "website audit services;720;25.0;0.6;800000;0.2,0.2,0.2;1;3", # Trans
        "how to do an seo audit;480;0;0.1;9000000;0.1,0.1,0.1;5;1", # Info

        # --- Local SEO ---
        "local seo services;9900;12.5;0.5;60000000;0.5,0.5,0.6;1,2;0", 
        "local seo near me;5400;10.0;0.4;100000000;0.6,0.6,0.6;1,2,36;2",
        "google my business optimization;2400;5.0;0.2;1500000;0.4,0.4,0.4;1;1",
        
        # --- Case Studies / Results ---
        "seo case studies;1000;3.0;0.2;4000000;0.3,0.3,0.3;1,2;1",
        "seo success stories;500;2.0;0.1;1000000;0.2,0.2,0.2;1;1",
        "client results seo;300;0;0;500000;0.1,0.1,0.1;1;0",
        
        # --- Glossary / Terms ---
        "what is canonical tag;3600;0;0.1;5000000;0.2,0.2,0.2;5;1",
        "seo glossary;1900;1.0;0.05;2000000;0.1,0.1,0.1;5;1",
        "meta description definition;2900;0;0;10000000;0.1,0.1,0.1;5;1",
        
        # --- Tools ---
        "keyword rank checker;12000;4.0;0.6;80000000;0.5,0.5,0.5;1;3",
        "free serp checker;5400;0;0.3;20000000;0.4,0.4,0.4;1;3",
        
        # --- General ---
        "best seo company;8100;35.0;0.8;100000000;0.5,0.5,0.5;1,2;3",
        "seo firm reviews;1000;5.0;0.4;5000000;0.3,0.3,0.3;1;0",
    ]

    keywords = []
    for line in raw_csv_data:
        parts = line.split(";")
        if len(parts) >= 8:
            keywords.append({
                "Ph": parts[0],
                "Nq": parts[1],
                "Cp": parts[2],
                "Co": parts[3],
                "Nr": parts[4],
                "Td": parts[5],
                "Fk": parts[6],
                "In": parts[7]
            })

    # 示例输入：pages（你说你有 title/url/type）
    pages = [
        {"page_id": "p_home", "title": "Acme SEO Agency", "url": "https://example.com/", "type": "home"},
        {"page_id": "p_pricing", "title": "Pricing - SEO Services", "url": "https://example.com/pricing", "type": "pricing"},
        {"page_id": "p_tools", "title": "AI SEO Tools & Software", "url": "https://example.com/tools/ai-seo", "type": "product"},
        {"page_id": "p_blog_cheap", "title": "Cheap vs Affordable SEO: What's the Difference?", "url": "https://example.com/blog/cheap-seo-services", "type": "post"},
        
        # New simulated pages
        {"page_id": "p_service_amazon", "title": "Amazon SEO Services & Optimization", "url": "https://example.com/services/amazon-seo", "type": "landing"},
        {"page_id": "p_service_audit", "title": "Technical SEO Audit Services", "url": "https://example.com/services/technical-audit", "type": "landing"},
        {"page_id": "p_service_local", "title": "Local SEO Services for Small Business", "url": "https://example.com/services/local-seo", "type": "landing"},
        {"page_id": "p_blog_ai_future", "title": "The Future of AI in SEO 2025", "url": "https://example.com/blog/ai-in-seo", "type": "post"},
        {"page_id": "p_blog_audit_guide", "title": "How to Perform an SEO Audit (Step-by-Step)", "url": "https://example.com/blog/seo-audit-guide", "type": "post"},
        {"page_id": "p_about", "title": "About Us - Acme Agency", "url": "https://example.com/about", "type": "about"},
        {"page_id": "p_contact", "title": "Contact Our SEO Experts", "url": "https://example.com/contact", "type": "contact"},
        {"page_id": "p_case_studies", "title": "Client Success Stories & Case Studies", "url": "https://example.com/case-studies", "type": "landing"},
        {"page_id": "p_glossary", "title": "SEO Glossary: Terms & Definitions", "url": "https://example.com/resources/glossary", "type": "resource"},
        {"page_id": "p_tool_rank", "title": "Free Keyword Rank Checker Tool", "url": "https://example.com/tools/rank-checker", "type": "product"},
    ]

    out = map_keywords_to_pages(
        keywords=keywords,
        pages=pages,
        max_secondary_per_page=6,
        min_cluster_size=2,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
