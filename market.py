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
)
NEWS_PATH = Path(__file__).with_name("news_data.json")

def _seed(conn):
    conn.executemany("INSERT OR IGNORE INTO properties(property_id,name,current_price,characteristics) VALUES(?,?,?,?)", PROPERTIES)
    conn.executemany("INSERT OR IGNORE INTO news(date,title,type,target_property_id,price_impact_rate,summary) VALUES(:date,:title,:type,:target_property_id,:price_impact_rate,:summary)", json.loads(NEWS_PATH.read_text(encoding="utf-8")))
    conn.commit()

def get_properties():
    with get_connection() as conn:
        _seed(conn)
        return [dict(r) for r in conn.execute("SELECT property_id,name,current_price,characteristics FROM properties ORDER BY property_id")]

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
