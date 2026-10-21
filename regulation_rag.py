"""Server-side collection and SQLite retrieval for legal-regulation RAG."""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from database import get_connection

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LAW_SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"

def _setting(name, default=""):
    value = os.getenv(name, "").strip().strip("'\"")
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, default)).strip().strip("'\"")
    except Exception:
        return default


def _law_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the law.go.kr JSON response, which varies for one/many hits."""
    result = payload.get("LawSearch", payload)
    items = result.get("law", []) if isinstance(result, dict) else []
    return [items] if isinstance(items, dict) else items


def sync_regulations(region_code: str, region_name: str, query: str | None = None) -> dict[str, Any]:
    """Fetch public legal search results once and persist them for later RAG use.

    This function is deliberately called by an explicit refresh action or a job,
    never by page rendering or the chat request path.
    """
    oc = _setting("LAW_API_OC")
    if not oc:
        raise RuntimeError("LAW_API_OC is missing from .env")
    # 법제처 법령명 검색은 지자체명보다 주제어가 안정적이다. 지역 코드는
    # 저장·검색 범위에 사용하고, 실제 법령 검색은 부동산 규제 주제어로 한다.
    params = {"OC": oc, "target": "law", "type": "JSON", "query": query or "부동산"}
    url = f"{LAW_SEARCH_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("법제처 규제 정보를 가져오지 못했습니다.") from exc

    saved = 0
    with get_connection() as conn:
        for item in _law_items(payload):
            title = str(item.get("법령명한글") or item.get("법령명") or "제목 미상")
            law_id = str(item.get("법령ID") or item.get("법령일련번호") or "")
            effective_date = str(item.get("시행일자") or item.get("공포일자") or "") or None
            description = " · ".join(
                part for part in (f"적용 검토 지역: {region_name}", str(item.get("제개정구분명") or "법령"), str(item.get("법령약칭명") or ""), f"법령 ID: {law_id}" if law_id else "") if part
            )
            source_url = f"https://www.law.go.kr/법령/{law_id}" if law_id else LAW_SEARCH_URL
            conn.execute(
                """INSERT INTO real_estate_regulations
                (region_code,title,restriction_type,description,effective_date,source_url)
                VALUES(?,?,?,?,?,?) ON CONFLICT(region_code,title,source_url) DO UPDATE SET
                restriction_type=excluded.restriction_type, description=excluded.description,
                effective_date=excluded.effective_date, fetched_at=CURRENT_TIMESTAMP""",
                (region_code, title, "법제처 법령", description, effective_date, source_url),
            )
            saved += 1
        conn.commit()
    return {"region_code": region_code, "region_name": region_name, "saved": saved, "fetched_at": date.today().isoformat()}


def retrieve_regulations(region_code: str, question: str = "", limit: int = 4) -> list[dict[str, Any]]:
    """Retrieve stored regional regulations using a transparent SQLite ranking."""
    terms = [term for term in question.replace("?", " ").split() if len(term) >= 2][:5]
    score = " + ".join("CASE WHEN title LIKE ? OR description LIKE ? THEN 1 ELSE 0 END" for _ in terms) or "0"
    params: list[Any] = [region_code]
    for term in terms:
        params.extend([f"%{term}%", f"%{term}%"])
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"""SELECT title,restriction_type,description,effective_date,source_url,fetched_at,{score} AS relevance
                FROM real_estate_regulations WHERE region_code=?
                ORDER BY relevance DESC, fetched_at DESC, id DESC LIMIT ?""",
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def format_regulation_context(region_name: str, regulations: list[dict[str, Any]]) -> str:
    if not regulations:
        return f"{region_name}: 저장된 규제 정보가 없습니다. 최신 동기화가 필요한 상태입니다."
    lines = [f"{region_name} 규제 정보(저장 기준):"]
    for item in regulations:
        lines.append(f"- {item['title']} | {item['restriction_type']} | 시행일: {item['effective_date'] or '미상'} | 수집일: {item['fetched_at']} | 출처: {item['source_url']} | {item['description']}")
    return "\n".join(lines)
