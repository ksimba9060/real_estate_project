"""Public-data collection and SQLite retrieval for price RAG."""
from __future__ import annotations

import os
import random
import xml.etree.ElementTree as ET
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

APT_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"


def sync_prices(region_code: str, region_name: str, year_month: str | None = None) -> dict[str, Any]:
    """Fetch one month of MOLIT apartment trades and persist them."""
    service_key = os.getenv("PUBLIC_DATA_API_KEY", "").strip().strip("'\"")
    if not service_key:
        raise RuntimeError("PUBLIC_DATA_API_KEY가 .env에 없습니다.")
    ym = year_month or date.today().strftime("%Y%m")
    params = {"serviceKey": service_key, "LAWD_CD": region_code, "DEAL_YMD": ym, "pageNo": 1, "numOfRows": 1000}
    try:
        with urlopen(f"{APT_TRADE_URL}?{urlencode(params)}", timeout=20) as response:
            root = ET.fromstring(response.read())
    except Exception as exc:
        raise RuntimeError("국토부 실거래가 API를 호출하지 못했습니다.") from exc
    result_code = root.findtext("./header/resultCode")
    if result_code not in (None, "00"):
        raise RuntimeError(f"국토부 API 오류({result_code}): {root.findtext('./header/resultMsg') or '알 수 없는 오류'}")
    saved = 0
    with get_connection() as conn:
        for item in root.findall("./body/items/item"):
            def text(*names):
                for name in names:
                    value = item.findtext(name)
                    if value and value.strip(): return value.strip()
                return ""
            price = int(text("거래금액").replace(",", "").replace(" ", "")) * 10000
            area = float(text("전용면적")) if text("전용면적") else None
            floor = int(text("층")) if text("층") else None
            deal_date = "-".join((text("년"), text("월").zfill(2), text("일").zfill(2)))
            name = text("아파트") or "아파트"
            conn.execute("""INSERT INTO real_estate_prices
                (region_code,region_name,property_name,deal_date,deal_price,area,floor,source)
                VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(region_code,property_name,deal_date,deal_price,area,floor,source)
                DO UPDATE SET fetched_at=CURRENT_TIMESTAMP, region_name=excluded.region_name""",
                (region_code, region_name, name, deal_date, price, area, floor, "국토교통부 실거래가"))
            saved += 1
        conn.commit()
    return {"region_code": region_code, "region_name": region_name, "year_month": ym, "saved": saved, "fetched_at": date.today().isoformat()}


def retrieve_prices(region_code: str, question: str = "", limit: int = 8) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""SELECT region_name,property_name,deal_date,deal_price,area,floor,source,fetched_at
            FROM real_estate_prices WHERE region_code=? ORDER BY deal_date DESC, id DESC LIMIT ?""", (region_code, limit)).fetchall()
    return [dict(row) for row in rows]


def price_history(region_code: str, years: int) -> list[dict[str, Any]]:
    """Return a virtual monthly price series informed by public-data trends.

    Stored MOLIT transactions are used as an anchor when available. If none
    have been collected yet, a deterministic educational series is generated
    so the simulator never depends on a live API response to render a chart.
    """
    with get_connection() as conn:
        rows = conn.execute("""SELECT substr(deal_date,1,7) AS month,
            ROUND(AVG(deal_price)) AS average_price, COUNT(*) AS transaction_count
            FROM real_estate_prices
            WHERE region_code=? AND deal_date >= date('now', ?)
            GROUP BY substr(deal_date,1,7) ORDER BY month""", (region_code, f"-{years} years")).fetchall()
    baselines = {"11680": 980_000_000, "11470": 720_000_000, "26350": 610_000_000, "41220": 430_000_000, "36110": 390_000_000}
    rng = random.Random(f"real-estate-demo:{region_code}:{years}")
    total = years * 12
    observed_anchor = sum(int(row["average_price"] or 0) for row in rows) / len(rows) if rows else 0
    baseline = observed_anchor or baselines.get(region_code, 500_000_000)
    # 공개 실거래 추세를 참고한 교육용 상승률과 변동폭(실제 예측값 아님).
    monthly_growth = {"11680": .020, "11470": .015, "26350": .011, "41220": .013, "36110": .010}.get(region_code, .012)
    result = []
    for offset in range(total - 1, -1, -1):
        month_index = total - offset
        month_value = baseline * ((1 + monthly_growth) ** month_index)
        cycle = 1 + 0.16 * ((month_index % 12) / 11 - 0.5)
        shock = 1 + (0.10 if month_index % 19 == 0 else 0) - (0.08 if month_index % 23 == 0 else 0)
        noise = 1 + rng.uniform(-0.065, 0.065)
        month = __import__("datetime").date.today().replace(day=1)
        year = month.year + (month.month - 1 - offset) // 12
        month_num = (month.month - 1 - offset) % 12 + 1
        result.append({"month": f"{year:04d}-{month_num:02d}", "average_price": round(month_value * cycle * shock * noise), "transaction_count": rng.randint(8, 34), "is_virtual": 1})
    return result


def format_price_context(region_name: str, prices: list[dict[str, Any]]) -> str:
    if not prices: return f"{region_name}: 저장된 실거래가가 없습니다. 최신 동기화가 필요합니다."
    lines = [f"{region_name} 최근 실거래가(저장 기준):"]
    for p in prices:
        lines.append(f"- {p['deal_date']} | {p['property_name']} | {p['deal_price']:,}원 | 전용 {p['area'] or '미상'}㎡ | {p['floor'] or '미상'}층 | 수집일 {p['fetched_at']} | 출처: {p['source']}")
    return "\n".join(lines)
