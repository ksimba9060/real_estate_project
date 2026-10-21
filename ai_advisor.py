"""AI 상담, 무료 횟수 제한, 상담권 교환."""
import os
from database import get_connection, ensure_user

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_or_create_chat_session(user_id):
    ensure_user(user_id)
    with get_connection() as db:
        row = db.execute("SELECT session_id FROM chat_sessions WHERE user_id=? ORDER BY updated_at DESC, session_id DESC LIMIT 1", (user_id,)).fetchone()
        if row: return row["session_id"]
        cur = db.execute("INSERT INTO chat_sessions(user_id) VALUES(?)", (user_id,)); db.commit()
        return cur.lastrowid

def get_chat_messages(session_id, user_id):
    with get_connection() as db:
        return [dict(row) for row in db.execute("SELECT role,content,created_at FROM chat_messages WHERE session_id=? AND EXISTS (SELECT 1 FROM chat_sessions WHERE session_id=? AND user_id=?) ORDER BY message_id", (session_id, session_id, user_id))]

def save_chat_message(session_id, user_id, role, content):
    with get_connection() as db:
        db.execute("INSERT INTO chat_messages(session_id,role,content) SELECT ?,?,? WHERE EXISTS (SELECT 1 FROM chat_sessions WHERE session_id=? AND user_id=?)", (session_id, role, content, session_id, user_id))
        db.execute("UPDATE chat_sessions SET updated_at=CURRENT_TIMESTAMP WHERE session_id=? AND user_id=?", (session_id, user_id)); db.commit()

def _usage(user_id, date):
    ensure_user(user_id)
    with get_connection() as db:
        db.execute("INSERT OR IGNORE INTO advice_usage(user_id,date) VALUES(?,?)", (user_id,str(date)))
        return db.execute("SELECT * FROM advice_usage WHERE user_id=? AND date=?", (user_id,str(date))).fetchone()

def redeem_advice_credits(user_id):
    ensure_user(user_id)
    with get_connection() as db:
        user = db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,)).fetchone()
        if user["coins"] < 200: return {"success":False,"message":"코인이 200개 이상 필요합니다."}
        today = __import__("datetime").date.today().isoformat()
        db.execute("UPDATE users SET coins=coins-200 WHERE user_id=?", (user_id,)); db.execute("INSERT OR IGNORE INTO advice_usage(user_id,date) VALUES(?,?)", (user_id,today)); db.execute("UPDATE advice_usage SET extra_advice_credits=extra_advice_credits+10 WHERE user_id=? AND date=?", (user_id,today))
    return {"success":True,"credits_added":10}

def ask_ai_advisor(user_id, question, portfolio, news, date, conversation=None):
    # 테스트 기간에는 상담 횟수와 상담권을 차감하지 않는다.
    ensure_user(user_id)
    mode = "테스트 상담"
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            previous = "\n".join(f"{item['role']}: {item['content']}" for item in (conversation or [])[-6:])
            prompt = f"이전 대화:\n{previous or '(첫 질문)'}\n\n사용자 질문: {question}\n포트폴리오: {portfolio}\n오늘 뉴스: {news}"
            response = client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-5-mini"), instructions="교육용 부동산 상담사입니다. 근거, 고려할 점, 불확실성을 구분하고 매수·매도를 단정하거나 수익을 보장하지 마세요.", input=prompt)
            answer = response.output_text
        except Exception:
            return {"success":False,"message":"AI 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요. 상담 횟수는 차감되지 않았습니다."}
    else: answer = "근거: 현재 포트폴리오와 뉴스 흐름을 함께 확인해야 합니다.\n\n고려할 점: 가격 변동뿐 아니라 현금 여유, 보유 기간, 분산 정도를 살펴보세요.\n\n불확실성: 이 화면은 교육용 시뮬레이션이며 실제 수익이나 미래 가격을 보장하지 않습니다."
    return {"success":True,"mode":mode,"answer":answer}

