"""부동산·금융 기초 퀴즈와 코인 보상."""
import hashlib
from database import get_connection, ensure_user

QUESTION_BANK = [
    {"id":"q1","question":"분산 투자의 주된 목적은 무엇일까요?","choices":["위험을 나누기 위해","항상 수익을 보장하기 위해","세금을 없애기 위해"],"answer":0,"explanation":"자산을 나누면 특정 자산의 변동 위험을 줄이는 데 도움이 됩니다."},
    {"id":"q2","question":"부동산 투자에서 유동성이란 무엇에 가까울까요?","choices":["건물의 높이","현금화하기 쉬운 정도","대출 금리의 종류"],"answer":1,"explanation":"유동성은 자산을 현금화할 수 있는 정도입니다."},
    {"id":"q3","question":"금리가 오르면 일반적으로 대출을 활용한 투자 비용은 어떻게 되나요?","choices":["항상 감소한다","전혀 변하지 않는다","증가할 수 있다"],"answer":2,"explanation":"금리 상승은 이자 부담을 키울 수 있습니다."},
    {"id":"q4","question":"전세가율은 무엇을 비교한 비율일까요?","choices":["전세가와 매매가","세금과 소득","대출금과 이자"],"answer":0,"explanation":"전세가율은 매매가격 대비 전세가격의 비율입니다."},
    {"id":"q5","question":"취득세는 언제 주로 발생하는 세금일까요?","choices":["부동산을 취득할 때","매물을 검색할 때","뉴스를 읽을 때"],"answer":0,"explanation":"부동산을 취득하면 취득세 납부 의무가 생깁니다."},
    {"id":"q6","question":"공실률이 높아지면 임대 투자에는 어떤 영향이 있을까요?","choices":["임대수입이 줄 수 있다","항상 수익이 오른다","세금이 자동 면제된다"],"answer":0,"explanation":"공실이 늘면 임대료 수입이 감소할 수 있습니다."},
    {"id":"q7","question":"LTV는 무엇과 관련된 지표일까요?","choices":["대출 가능 금액","인구 증가율","관리비"],"answer":0,"explanation":"LTV는 담보가치 대비 대출금액 비율입니다."},
    {"id":"q8","question":"거래량이 급감했다는 것은 무엇을 의미할 수 있을까요?","choices":["시장 참여가 줄었을 가능성","가격이 반드시 오른다는 뜻","세금이 없다는 뜻"],"answer":0,"explanation":"거래량 감소는 관망세나 유동성 위축을 의미할 수 있습니다."},
    {"id":"q9","question":"임대수익률을 계산할 때 주로 필요한 것은 무엇일까요?","choices":["임대수입과 투자금액","뉴스 제목과 날씨","층수와 색상만"],"answer":0,"explanation":"임대수익률은 임대수입을 투자금액과 비교해 계산합니다."},
]

def get_quiz_questions(user_id=None):
    if not user_id: return QUESTION_BANK[:3]
    start = int(hashlib.sha256(str(user_id).encode()).hexdigest(), 16) % len(QUESTION_BANK)
    selected = []
    answer_positions = set()
    for offset in range(len(QUESTION_BANK)):
        question = QUESTION_BANK[(start + offset) % len(QUESTION_BANK)]
        if question["answer"] not in answer_positions or len(selected) >= 2:
            selected.append(question)
            answer_positions.add(question["answer"])
        if len(selected) == 3: break
    return selected

def has_answered_quiz(user_id, question_id, date):
    ensure_user(user_id)
    with get_connection() as db:
        return db.execute("SELECT 1 FROM quiz_records WHERE user_id=? AND date=? AND question_id=?", (user_id, str(date), question_id)).fetchone() is not None

def submit_quiz_answer(user_id, question_id, answer, date):
    ensure_user(user_id); q = next((x for x in QUESTION_BANK if x["id"] == question_id), None)
    if not q: raise ValueError("존재하지 않는 문제입니다.")
    with get_connection() as db:
        if db.execute("SELECT 1 FROM quiz_records WHERE user_id=? AND date=? AND question_id=?", (user_id, str(date), question_id)).fetchone():
            return {"correct":False,"rewarded":False,"already_answered":True,"message":"오늘 이미 푼 문제입니다."}
        correct = int(q["answer"] == int(answer))
        db.execute("INSERT INTO quiz_records(user_id,date,question_id,is_correct,reward_granted) VALUES (?,?,?,?,?)", (user_id, str(date), question_id, correct, correct))
        if correct: db.execute("UPDATE users SET coins=coins+10 WHERE user_id=?", (user_id,))
    return {"correct":bool(correct),"rewarded":bool(correct),"coins":10 if correct else 0,"explanation":q["explanation"]}

def get_coin_balance(user_id):
    ensure_user(user_id)
    with get_connection() as db: return db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,)).fetchone()["coins"]
