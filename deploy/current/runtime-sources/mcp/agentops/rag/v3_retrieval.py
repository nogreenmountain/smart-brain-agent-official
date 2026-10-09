"""Pure planning helpers for the disabled-by-default RAG v3 shadow path."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable


_EXACT_RE = re.compile(r"\b[A-Z]{1,8}[-_/]\d{2,}[-_/A-Z0-9]*\b", re.I)
_DATE_RE = re.compile(r"(20\d{2})\s*年\s*(1[0-2]|0?[1-9])\s*月")


@dataclass(frozen=True)
class QueryPlan:
    original_query: str
    project_names: list[str]
    persons: list[str]
    file_types: list[str]
    date_range: tuple[str, str] | None
    cross_document: bool
    multi_hop: bool
    subqueries: list[str]


def plan_query(query: str, *, max_subqueries: int = 3) -> QueryPlan:
    max_subqueries = max(1, min(max_subqueries, 5))
    project_names = list(dict.fromkeys(re.findall(r"项目[A-Za-z0-9\u4e00-\u9fff]{1,20}?(?=的|中|里|在|[，,。\s]|$)", query)))
    raw_persons = re.findall(r"[\u4e00-\u9fff]{2,3}(?=在项目|负责|参与)", query)
    persons = list(dict.fromkeys(value[-2:] if len(value) > 2 else value for value in raw_persons))
    lowered = query.lower()
    file_types = []
    for token, normalized in (("pdf", "pdf"), ("word", "docx"), ("docx", "docx"), ("ppt", "pptx"), ("excel", "xlsx"), ("xlsx", "xlsx")):
        if token in lowered and normalized not in file_types:
            file_types.append(normalized)
    dates = [f"{year}-{int(month):02d}" for year, month in _DATE_RE.findall(query)]
    if dates:
        range_match = re.search(r"(20\d{2})\s*年\s*(1[0-2]|0?[1-9])\s*月\s*(?:到|至|-)\s*(1[0-2]|0?[1-9])\s*月", query)
        if range_match:
            year, start_month, end_month = range_match.groups()
            dates = [f"{year}-{int(start_month):02d}", f"{year}-{int(end_month):02d}"]
    date_range = (dates[0], dates[-1]) if dates else None
    cross_document = any(word in query for word in ("比较", "综合", "跨文档", "两份", "多个资料")) or len(file_types) > 1
    multi_hop = any(word in query for word in ("因此", "导致", "关系", "演变", "先后"))
    pieces = [piece.strip(" ，,。") for piece in re.split(r"(?:并且|以及|和|与)", query) if piece.strip()]
    return QueryPlan(query, project_names, persons, file_types, date_range, cross_document, multi_hop, pieces[:max_subqueries])


def choose_channel_weights(query: str) -> dict[str, float | str]:
    exact = bool(_EXACT_RE.search(query)) or any(word in query for word in ("编号", "版本号", "合同号"))
    date_query = bool(_DATE_RE.search(query)) or any(word in query for word in ("日期", "最近", "最新"))
    if exact:
        return {"dense": 0.25, "sparse": 0.25, "lexical": 0.50, "time": 0.0, "reason": "exact_identifier"}
    if date_query:
        return {"dense": 0.35, "sparse": 0.20, "lexical": 0.25, "time": 0.20, "reason": "time_sensitive"}
    return {"dense": 0.55, "sparse": 0.25, "lexical": 0.20, "time": 0.0, "reason": "semantic"}


def prefilter_acl(candidates: Iterable[dict[str, Any]], *, allowed_project_ids: set[str]) -> list[dict[str, Any]]:
    """Apply ACL before any fusion or reranking; callers must pass trusted IDs."""
    return [candidate for candidate in candidates if str(candidate.get("project_id")) in allowed_project_ids]


def should_rerank(query: str, *, candidate_count: int, cross_document: bool) -> bool:
    if _EXACT_RE.search(query) and candidate_count <= 8 and not cross_document:
        return False
    return cross_document or candidate_count >= 12 or any(word in query for word in ("综合", "比较", "冲突", "为什么"))
