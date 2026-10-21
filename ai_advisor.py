"""AI 상담, 무료 횟수 제한, 상담권 교환."""
import os
from database import get_connection, ensure_user
from market import get_home
from regulation_rag import format_regulation_context, retrieve_regulations

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
    home = get_home(user_id)
    regulations = retrieve_regulations(home["region_code"], question) if home and home.get("region_code") else []
    regulation_context = format_regulation_context(home["region_name"], regulations) if home else "등록된 내 집 지역이 없습니다."
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            previous = "\n".join(f"{item['role']}: {item['content']}" for item in (conversation or [])[-6:])
            prompt = f"이전 대화:\n{previous or '(첫 질문)'}\n\n사용자 질문: {question}\n포트폴리오: {portfolio}\n오늘 뉴스: {news}\n\n[SQLite RAG - 규제 정보]\n{regulation_context}"
            response = client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-5-mini"), instructions="교육용 부동산 상담사입니다. 근거, 고려할 점, 불확실성을 구분하고 매수·매도를 단정하거나 수익을 보장하지 마세요. 제공된 SQLite RAG 근거만 규제 사실로 사용하세요. 답변에 '근거', '고려할 점', '불확실성', '출처·기준일'을 각각 표시하고, 출처 URL과 수집일 또는 시행일을 포함하세요.", input=prompt)
            answer = response.output_text
        except Exception:
            return {"success":False,"message":"AI 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요. 상담 횟수는 차감되지 않았습니다."}
    else: answer = f"교육용 상담입니다. OpenAI API 키를 설정하면 아래 RAG 근거를 바탕으로 상세 답변을 생성합니다.\n\n{regulation_context}"
    return {"success":True,"mode":mode,"answer":answer,"regulations":regulations}

