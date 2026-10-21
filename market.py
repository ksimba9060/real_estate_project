"""Virtual market, daily news effects, and buy/sell operations."""
from __future__ import annotations
import json
from datetime import date as Date
from pathlib import Path
from database import ensure_user, get_connection

PROPERTIES = (
    ("metro_center", "메트로 센터", 850_000_000, "업무·교통 중심의 안정형 지역"),
    ("education_town", "에듀 타운", 620_000_000, "학군 수요가 강한 주거 지역"),
    ("coastal_hub", "코스탈 허브", 470_000_000, "관광·상권 변동성이 있는 해안 지역"),
    ("green_industry", "그린 인더스트리", 540_000_000, "친환경 산업단지 배후 지역"),
    ("newtown_lake", "레이크 뉴타운", 390_000_000, "개발과 공급 이슈가 공존하는 신도시"),
    ("river_side", "리버사이드", 510_000_000, "수변 주거와 생활 인프라가 강점인 지역"),
    ("tech_valley", "테크 밸리", 680_000_000, "IT 기업과 직주근접 수요가 모이는 지역"),
    ("heritage_village", "헤리티지 빌리지", 360_000_000, "구도심 재생과 문화 상권이 진행 중인 지역"),
    ("airport_city", "에어포트 시티", 430_000_000, "공항 접근성과 물류 산업의 영향을 받는 지역"),
    ("forest_hills", "포레스트 힐스", 295_000_000, "녹지와 쾌적성을 중시하는 주거 지역"),
    ("sunset_bay", "선셋 베이", 455_000_000, "해변 산책로와 상업시설이 가까운 생활권"),
    ("central_garden", "센트럴 가든", 575_000_000, "도심 공원과 업무지구를 잇는 주거 지역"),
    ("smart_square", "스마트 스퀘어", 635_000_000, "신산업 기업과 교통망이 모이는 지역"),
    ("blue_river", "블루 리버", 410_000_000, "수변 조망과 신축 주거 수요가 있는 지역"),
    ("morning_village", "모닝 빌리지", 335_000_000, "조용한 생활환경과 학교 수요가 강한 지역"),
    ("urban_forest", "어반 포레스트", 515_000_000, "도심 속 녹지와 문화시설을 누리는 지역"),
    ("innovation_port", "이노베이션 포트", 495_000_000, "물류·산업 개발과 교통 호재가 있는 지역"),
    ("hilltop_station", "힐탑 스테이션", 445_000_000, "역세권과 언덕 조망을 함께 갖춘 지역"),
    ("silver_lake", "실버 레이크", 375_000_000, "호수공원과 여유로운 주거환경이 강점인 지역"),
    ("nova_district", "노바 디스트릭트", 705_000_000, "첨단 업무시설과 고급 주거 수요가 공존하는 지역"),
)
NEWS_PATH = Path(__file__).with_name("news_data.json")

# The simulator keeps its game indicators, but each core market now maps to an
# actual Korean administrative region used by public-data ingestion and RAG.
PROPERTY_REGIONS = {
    # 실제 코드는 공공데이터 수집용으로만 사용하고, 화면에는 가상 지역명만 노출한다.
    "metro_center": ("11680", "메트로 센터"),
    "education_town": ("11470", "에듀 타운"),
    "coastal_hub": ("26350", "코스탈 허브"),
    "green_industry": ("41220", "그린 인더스트리"),
    "newtown_lake": ("36110", "레이크 뉴타운"),
    "sunset_bay": ("V1001", "선셋 베이"),
    "central_garden": ("V1002", "센트럴 가든"),
    "smart_square": ("V1003", "스마트 스퀘어"),
    "blue_river": ("V1004", "블루 리버"),
    "morning_village": ("V1005", "모닝 빌리지"),
    "urban_forest": ("V1006", "어반 포레스트"),
    "innovation_port": ("V1007", "이노베이션 포트"),
    "hilltop_station": ("V1008", "힐탑 스테이션"),
    "silver_lake": ("V1009", "실버 레이크"),
    "nova_district": ("V1010", "노바 디스트릭트"),
}

def _seed(conn):
    conn.executemany("INSERT OR IGNORE INTO properties(property_id,name,current_price,characteristics) VALUES(?,?,?,?)", PROPERTIES)
    for property_id, (region_code, region_name) in PROPERTY_REGIONS.items():
        conn.execute(
            "UPDATE properties SET name=?, region_code=?, region_name=? WHERE property_id=?",
            (region_name, region_code, region_name, property_id),
        )
    conn.executemany("INSERT OR IGNORE INTO news(date,title,type,target_property_id,price_impact_rate,summary) VALUES(:date,:title,:type,:target_property_id,:price_impact_rate,:summary)", json.loads(NEWS_PATH.read_text(encoding="utf-8")))
    conn.commit()

def get_properties():
    with get_connection() as conn:
        _seed(conn)
        return [dict(r) for r in conn.execute("SELECT property_id,name,current_price,characteristics,region_code,region_name FROM properties ORDER BY property_id")]

def get_home(user_id):
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        row = conn.execute("SELECT p.* FROM user_home h JOIN properties p ON p.property_id=h.property_id WHERE h.user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

def set_home(user_id, property_id):
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        if not conn.execute("SELECT 1 FROM properties WHERE property_id=?", (property_id,)).fetchone(): raise ValueError("unknown property_id")
        conn.execute("INSERT OR REPLACE INTO user_home(user_id,property_id) VALUES(?,?)", (user_id, property_id)); conn.commit()

def get_interests(user_id):
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        return [dict(r) for r in conn.execute("SELECT p.* FROM user_interests i JOIN properties p ON p.property_id=i.property_id WHERE i.user_id=? ORDER BY p.name", (user_id,))]

def add_interest(user_id, property_id):
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        conn.execute("INSERT OR IGNORE INTO user_interests(user_id,property_id) VALUES(?,?)", (user_id, property_id)); conn.commit()

def remove_interest(user_id, property_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM user_interests WHERE user_id=? AND property_id=?", (user_id, property_id)); conn.commit()

def get_user_portfolio(user_id):
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        user = conn.execute("SELECT cash,coins FROM users WHERE user_id=?", (user_id,)).fetchone()
        holdings = [dict(r) for r in conn.execute("""SELECT h.property_id,p.name,h.quantity,h.average_purchase_price,p.current_price,h.quantity*p.current_price AS current_value FROM holdings h JOIN properties p USING(property_id) WHERE h.user_id=? AND h.quantity>0 ORDER BY p.name""", (user_id,))]
        conn.commit()
    value = sum(x["current_value"] for x in holdings)
    return {"user_id": user_id, "cash": user["cash"], "coins": user["coins"], "holdings": holdings, "holdings_value": value, "total_assets": user["cash"] + value}

def apply_daily_news(user_id, date):
    try: day = Date.fromisoformat(str(date)).isoformat()
    except ValueError as e: raise ValueError("date must be YYYY-MM-DD") from e
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        items = conn.execute("SELECT news_id,date,title,type,target_property_id,price_impact_rate,summary FROM news WHERE date=? ORDER BY news_id", (day,)).fetchall()
        applied = conn.execute("SELECT 1 FROM daily_news_applications WHERE date=?", (day,)).fetchone() is not None
        if not applied:
            for item in items: conn.execute("UPDATE properties SET current_price=MAX(1,ROUND(current_price*(1+?))) WHERE property_id=?", (item["price_impact_rate"], item["target_property_id"]))
            conn.execute("INSERT INTO daily_news_applications(date) VALUES(?)", (day,))
        conn.commit()
    return {"date": day, "applied": not applied, "news": [dict(i) for i in items]}

def _trade(user_id, property_id, quantity, kind):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0: raise ValueError("quantity must be a positive integer")
    with get_connection() as conn:
        _seed(conn); ensure_user(conn, user_id)
        prop = conn.execute("SELECT current_price FROM properties WHERE property_id=?", (property_id,)).fetchone()
        if not prop: raise ValueError("unknown property_id")
        price, total = prop["current_price"], prop["current_price"] * quantity
        holding = conn.execute("SELECT quantity,average_purchase_price FROM holdings WHERE user_id=? AND property_id=?", (user_id,property_id)).fetchone()
        if kind == "buy":
            cash = conn.execute("SELECT cash FROM users WHERE user_id=?", (user_id,)).fetchone()["cash"]
            if total > cash: raise ValueError("insufficient cash for this purchase")
            old_quantity = holding["quantity"] if holding else 0; old_cost = old_quantity * (holding["average_purchase_price"] if holding else 0)
            conn.execute("UPDATE users SET cash=cash-? WHERE user_id=?", (total,user_id))
            conn.execute("INSERT INTO holdings(user_id,property_id,quantity,average_purchase_price) VALUES(?,?,?,?) ON CONFLICT(user_id,property_id) DO UPDATE SET quantity=excluded.quantity,average_purchase_price=excluded.average_purchase_price", (user_id,property_id,old_quantity+quantity,(old_cost+total)/(old_quantity+quantity)))
        else:
            if not holding or quantity > holding["quantity"]: raise ValueError("insufficient holdings for this sale")
            left = holding["quantity"]-quantity; conn.execute("UPDATE users SET cash=cash+? WHERE user_id=?", (total,user_id))
            if left: conn.execute("UPDATE holdings SET quantity=? WHERE user_id=? AND property_id=?", (left,user_id,property_id))
            else: conn.execute("DELETE FROM holdings WHERE user_id=? AND property_id=?", (user_id,property_id))
        conn.execute("INSERT INTO transactions(user_id,date,property_id,transaction_type,quantity,transaction_price) VALUES(?,?,?,?,?,?)", (user_id,Date.today().isoformat(),property_id,kind,quantity,price)); conn.commit()
    return {"success":True,"type":kind,"property_id":property_id,"quantity":quantity,"price":price,"total":total}

def buy_property(user_id, property_id, quantity): return _trade(user_id, property_id, quantity, "buy")
def sell_property(user_id, property_id, quantity): return _trade(user_id, property_id, quantity, "sell")
