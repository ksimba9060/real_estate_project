"""부동산·금융 기초 퀴즈와 코인 보상."""
from database import get_connection, ensure_user

QUESTIONS = [{"id":"q1","question":"분산 투자의 주된 목적은 무엇일까요?","choices":["위험을 나누기 위해","항상 수익을 보장하기 위해","세금을 없애기 위해"],"answer":0,"explanation":"자산을 나누면 특정 자산의 변동 위험을 줄이는 데 도움이 됩니다."},{"id":"q2","question":"부동산 투자에서 유동성이란 무엇에 가까울까요?","choices":["현금화하기 쉬운 정도","건물의 높이","대출 금리의 종류"],"answer":0,"explanation":"유동성은 자산을 현금화할 수 있는 정도입니다."},{"id":"q3","question":"금리가 오르면 일반적으로 대출을 활용한 투자 비용은 어떻게 되나요?","choices":["증가할 수 있다","항상 감소한다","전혀 변하지 않는다"],"answer":0,"explanation":"금리 상승은 이자 부담을 키울 수 있습니다."}]
def get_quiz_questions(): return QUESTIONS
def submit_quiz_answer(user_id, question_id, answer, date):
    ensure_user(user_id); q = next((x for x in QUESTIONS if x["id"]==question_id),None)
    if not q: raise ValueError("존재하지 않는 문제입니다.")
    with get_connection() as db:
        if db.execute("SELECT 1 FROM quiz_records WHERE user_id=? AND date=? AND question_id=?",(user_id,str(date),question_id)).fetchone(): return {"correct":False,"rewarded":False,"message":"오늘 이미 제출한 문제입니다."}
        correct = int(q["answer"] == int(answer)); db.execute("INSERT INTO quiz_records(user_id,date,question_id,is_correct,reward_granted) VALUES (?,?,?,?,?)",(user_id,str(date),question_id,correct,correct))
        if correct: db.execute("UPDATE users SET coins=coins+10 WHERE user_id=?",(user_id,))
    return {"correct":bool(correct),"rewarded":bool(correct),"coins":10 if correct else 0,"explanation":q["explanation"]}
def get_coin_balance(user_id):
    ensure_user(user_id)
    with get_connection() as db: return db.execute("SELECT coins FROM users WHERE user_id=?",(user_id,)).fetchone()["coins"]

