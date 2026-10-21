"""Streamlit 진입점."""
import streamlit as st
from datetime import date
from database import ensure_user, register_user, authenticate_user
from market import (get_properties, get_user_portfolio, apply_daily_news, buy_property, sell_property,
                    get_home, set_home, get_interests, add_interest, remove_interest)
from quiz import get_quiz_questions, submit_quiz_answer, get_coin_balance
from ai_advisor import ask_ai_advisor, get_or_create_chat_session, get_chat_messages, save_chat_message
from regulation_rag import sync_regulations

st.set_page_config(page_title="하우스렌즈", page_icon="•", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;700;800&display=swap');
:root { --ink:#18324b; --muted:#718399; --blue:#3b82f6; --sky:#eaf4ff; --mint:#e9fbf4; --line:#e4edf5; }
html, body, [class*="css"] { font-family: 'Inter','Noto Sans KR',sans-serif; }
.stApp { background: #fff5e1; color: var(--ink); }
[data-testid="stHeader"] { background: rgba(255,245,225,.94); }
[data-testid="stSidebar"] { background: #fffaf0; border-right:1px solid #e2d7c2; }
.hero { background: #fff5e1; border:1px solid #d9ccb4; border-radius:0; padding:18px 24px; margin:0 0 28px; }
.hero h1 { margin:0; font-size:32px; letter-spacing:-1.3px; color:var(--ink); }
.hero p { margin:8px 0 0; color:var(--muted); font-size:15px; }
.section-title { font-size:19px; font-weight:800; color:var(--ink); margin:16px 0 10px; }
.property-card, .news-card { background:#fffaf0; border:1px solid #d9ccb4; border-radius:2px; padding:18px; min-height:145px; box-shadow:none; }
.property-card h4, .news-card h4 { margin:0 0 8px; color:var(--ink); font-size:17px; }
.property-card p, .news-card p { color:var(--muted); font-size:13px; line-height:1.6; margin:4px 0; }
.price { font-size:21px; font-weight:800; color:#2563eb; }
.badge-good { color:#0f9f6e; background:#e8faf2; border-radius:999px; padding:4px 9px; font-size:12px; font-weight:700; }
.badge-bad { color:#e45c68; background:#fff0f1; border-radius:999px; padding:4px 9px; font-size:12px; font-weight:700; }
.icon-chip { display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:9px; background:#eaf4ff; color:#3b82f6; font-weight:800; margin-right:7px; }
.wire-card-title { font-size:18px; font-weight:700; color:#18324b; margin-bottom:6px; }
.wire-card-sub { color:#766c5b; font-size:13px; }
.wire-empty { min-height:70px; display:flex; align-items:center; color:#a09582; font-size:14px; }
.login-panel { background:#fff5e1; border:0; padding:20px; max-width:560px; margin:55px auto; box-shadow:none; }
div.stButton > button { border-radius:2px; font-weight:700; border:1px solid #b9ad98; background:#fffaf0; }
div.stButton > button[kind="primary"] { background:#18324b; border-color:#18324b; color:#fffaf0; }
[data-testid="stMetric"] { background:#fffaf0; border:1px solid #d9ccb4; border-radius:2px; padding:16px; }
[data-baseweb="tab-list"] { gap:28px; border-bottom:1px solid #d9ccb4; }
[data-baseweb="tab"] { background:transparent; color:#766c5b; }
[aria-selected="true"] { color:#18324b !important; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>하우스 렌즈</h1></div>', unsafe_allow_html=True)
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if not st.session_state.logged_in_user:
    st.markdown('<div class="login-panel">', unsafe_allow_html=True)
    st.markdown("## 로그인")
    st.caption("나의 집과 관심 매물, 상담 기록을 불러옵니다.")
    login_tab, signup_tab = st.tabs(["로그인", "처음 시작하기"])
    with login_tab:
        login_id = st.text_input("아이디", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인", type="primary"):
            if authenticate_user(login_id, login_pw):
                st.session_state.logged_in_user = login_id.strip(); st.rerun()
            else: st.error("아이디 또는 비밀번호를 확인해 주세요.")
    with signup_tab:
        st.markdown("### 나만의 투자 공간 만들기")
        st.caption("아이디와 비밀번호를 설정하면 보유 자산과 상담 기록이 저장됩니다.")
        signup_id = st.text_input("새 아이디", key="signup_id")
        signup_pw = st.text_input("새 비밀번호", type="password", key="signup_pw")
        signup_pw2 = st.text_input("비밀번호 확인", type="password", key="signup_pw2")
        if st.button("회원가입"):
            if signup_pw != signup_pw2: st.error("비밀번호가 일치하지 않습니다.")
            else:
                ok, message = register_user(signup_id, signup_pw)
                if ok:
                    st.success("회원가입이 완료되었습니다. 로그인 탭에서 시작해 주세요.")
                else:
                    st.error(message)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
user_id = st.session_state.logged_in_user
ensure_user(user_id); today = date.today()
st.sidebar.success(f"로그인: {user_id}")
if st.sidebar.button("로그아웃"):
    st.session_state.logged_in_user = None; st.rerun()
news_result = apply_daily_news(user_id, today)
today_news = news_result["news"]
portfolio = get_user_portfolio(user_id)
properties = get_properties()
home = get_home(user_id)
interests = get_interests(user_id)
if not home:
    st.markdown("## 나의 첫 집을 선택하세요")
    st.write("서비스를 시작하려면 먼저 내가 살고 있는 집을 한 채 등록해야 합니다.")
    home_choice = st.selectbox("내 집 지역", properties, format_func=lambda p: f"{p['name']} · {p['current_price']:,}원")
    st.info(f"{home_choice['characteristics']} · 구매 후 현금 {portfolio['cash'] - home_choice['current_price']:,}원")
    if st.button("이 지역을 내 집으로 구매하기", type="primary", use_container_width=True):
        try:
            buy_property(user_id, home_choice["property_id"], 1)
            set_home(user_id, home_choice["property_id"])
            st.success("내 집이 등록되었습니다. 이제 지역 뉴스와 관심 지역을 설정할 수 있습니다.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    st.stop()
relevant_ids = {home["property_id"], *(item["property_id"] for item in interests)}
today_news = [item for item in today_news if item["target_property_id"] in relevant_ids]
st.sidebar.metric("보유 코인", f"{get_coin_balance(user_id)}개")

st.markdown(f"### 내 집 · {home['name']}")
st.caption(home["characteristics"])
available = [p for p in properties if p["property_id"] not in {home["property_id"], *(x["property_id"] for x in interests)}]
home_col, interest_col = st.columns(2, gap="large")
with home_col:
    st.markdown('<div class="section-title">보유 부동산</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f'<div class="wire-card-title">{home["name"]}</div><div class="wire-card-sub">내 집 · 현재가 {home["current_price"]:,}원</div>', unsafe_allow_html=True)
        st.caption(home["characteristics"])
with interest_col:
    st.markdown('<div class="section-title">관심 매물</div>', unsafe_allow_html=True)
    with st.container(border=True):
        if interests:
            for item in interests:
                row = st.columns([5, 1])
                row[0].markdown(f'<div class="wire-card-title">{item["name"]}</div><div class="wire-card-sub">{item["current_price"]:,}원</div>', unsafe_allow_html=True)
                if row[1].button("−", key=f"remove_{item['property_id']}"):
                    remove_interest(user_id, item["property_id"]); st.rerun()
        else:
            st.markdown('<div class="wire-empty">관심 매물을 추가해보세요</div>', unsafe_allow_html=True)
        if available:
            interest_choice = st.selectbox("관심 매물 추가", available, format_func=lambda p: p["name"], label_visibility="collapsed", key="interest_choice")
            if st.button("+", key="add_interest", help="관심 매물 추가"):
                add_interest(user_id, interest_choice["property_id"]); st.rerun()

def news_label(item):
    return "호재" if item["price_impact_rate"] >= 0 else "규제·악재"

def show_news_popup():
    @st.dialog("오늘의 부동산 뉴스")
    def news_dialog():
        st.caption(f"{today.isoformat()} 기준 · 뉴스 효과가 시장 가격에 반영되었습니다.")
        if not today_news:
            st.info("오늘 등록된 뉴스가 없습니다. 시장을 천천히 살펴보세요.")
            return
        for item in today_news:
            positive = item["price_impact_rate"] >= 0
            st.markdown(f"### {news_label(item)}")
            st.subheader(item["title"])
            st.write(item["summary"])
            st.caption(f"예상 가격 영향: {'+' if positive else ''}{item['price_impact_rate']:.1%}")
        st.divider()
        st.markdown("#### 이 뉴스, AI에게 바로 물어보세요")
        popup_question = st.text_area(
            "상담 질문",
            value="오늘 뉴스가 제 포트폴리오에 어떤 영향을 줄 수 있나요?",
            key="popup_ai_question",
        )
        if st.button("AI 상담 시작", type="primary", use_container_width=True):
            result = ask_ai_advisor(user_id, popup_question, portfolio, today_news, today)
            if result["success"]:
                st.success(result["answer"])
            else:
                st.error(result["message"])
        if st.button("뉴스 확인 완료", use_container_width=True):
            st.session_state.news_popup_closed = True
            st.rerun()

def show_news_panel():
    """Streamlit 초기 렌더링에서도 확실히 보이는 뉴스 팝업 패널."""
    with st.container(border=True):
        st.markdown("## 오늘의 뉴스")
        st.caption(f"{today.isoformat()} · 오늘 시장에 반영된 주요 소식")
        if not today_news:
            st.info("오늘 등록된 뉴스가 없습니다.")
        else:
            news_cols = st.columns(min(3, len(today_news)))
            for col, item in zip(news_cols, today_news):
                positive = item["price_impact_rate"] >= 0
                badge = "호재" if positive else "규제·악재"
                with col:
                    st.markdown(f'<div class="news-card"><span class="{"badge-good" if positive else "badge-bad"}">{badge}</span><h4>{item["title"]}</h4><p>{item["summary"]}</p><p><b>{"+" if positive else ""}{item["price_impact_rate"]:.1%}</b> 예상 영향</p></div>', unsafe_allow_html=True)
        st.markdown("#### 이 뉴스에 대해 바로 AI에게 질문하기")
        first_question = st.text_input(
            "질문",
            value="오늘 뉴스가 제 포트폴리오에 어떤 영향을 줄 수 있나요?",
            key="first_news_question",
        )
        if st.button("뉴스 기반 AI 상담", type="primary", key="first_news_advice"):
            result = ask_ai_advisor(user_id, first_question, portfolio, today_news, today)
            if result["success"]:
                st.info(result["answer"])
            else:
                st.error(result["message"])

show_news_panel()

def show_ai_welcome_popup():
    @st.dialog("AI 부동산 상담")
    def ai_popup():
        st.markdown("### 무엇이든 물어보세요")
        st.write("현재 포트폴리오와 오늘의 시장 뉴스를 바탕으로 AI가 상담해드립니다.")
        popup_question = st.text_area(
            "상담 질문",
            placeholder="예: 지금 내 포트폴리오에서 가장 먼저 공부할 점은 무엇인가요?",
            key="welcome_ai_question",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("AI에게 질문하기", type="primary", use_container_width=True) and popup_question.strip():
                result = ask_ai_advisor(user_id, popup_question.strip(), portfolio, today_news, today, [])
                if result["success"]:
                    st.session_state.advisor_session_id = get_or_create_chat_session(user_id)
                    st.session_state.advisor_messages = [
                        {"role": "user", "content": popup_question.strip()},
                        {"role": "assistant", "content": result["answer"]},
                    ]
                    save_chat_message(st.session_state.advisor_session_id, user_id, "user", popup_question.strip())
                    save_chat_message(st.session_state.advisor_session_id, user_id, "assistant", result["answer"])
                    st.markdown("#### AI 답변")
                    st.markdown(result["answer"])
                else:
                    st.error(result["message"])
        with c2:
            if st.button("메인 화면으로 이동", use_container_width=True):
                st.session_state.ai_popup_closed = True
                st.rerun()

if "news_popup_closed" not in st.session_state:
    st.session_state.news_popup_closed = False
if not st.session_state.news_popup_closed:
    show_news_popup()

if st.button("오늘의 뉴스 다시 보기", type="secondary"):
    show_news_popup()

tabs = st.tabs(["홈", "지역 시장", "거래", "퀴즈", "AI 상담"])
with tabs[0]:
    st.markdown('<div class="section-title">오늘의 자산 현황</div>', unsafe_allow_html=True)
    c1,c2,c3=st.columns(3); c1.metric("현금", f"{portfolio['cash']:,}원"); c2.metric("보유 자산", f"{portfolio['holdings_value']:,}원"); c3.metric("보유 코인", f"{portfolio['coins']}개")
    st.markdown('<div class="section-title">보유 부동산</div>', unsafe_allow_html=True)
    if portfolio["holdings"]:
        cols = st.columns(min(3, len(portfolio["holdings"])))
        for col, item in zip(cols, portfolio["holdings"]):
            with col:
                st.markdown(f'<div class="property-card"><h4><span class="icon-chip">H</span>{item["name"]}</h4><p>{item["quantity"]}채 보유 · 평균 매입가 {item["average_purchase_price"]:,.0f}원</p><div class="price">{item["current_value"]:,}원</div><p>현재가 기준 평가액</p></div>', unsafe_allow_html=True)
    else:
        st.info("아직 보유한 부동산이 없습니다. 지역 시장에서 매물을 살펴보세요.")
with tabs[1]:
    st.markdown('<div class="section-title">지역 시장</div>', unsafe_allow_html=True)
    st.caption("지역 카드를 비교하고 관심 지역을 찾아보세요.")
    for start in range(0, len(properties), 3):
        cols = st.columns(3)
        for col, item in zip(cols, properties[start:start+3]):
            with col:
                home_badge = " · 내 집" if item["property_id"] == home["property_id"] else ""
                st.markdown(f'<div class="property-card"><h4><span class="icon-chip">R</span>{item["name"]}{home_badge}</h4><div class="price">{item["current_price"]:,}원</div><p>{item["characteristics"]}</p></div>', unsafe_allow_html=True)
with tabs[2]:
    props=get_properties(); selected=st.selectbox("지역", props, format_func=lambda p:f"{p['name']} — {p['current_price']:,}원"); qty=st.number_input("수량", min_value=1, value=1, step=1)
    c1,c2=st.columns(2)
    with c1:
        if st.button("매수", use_container_width=True):
            try: buy_property(user_id,selected["property_id"],qty); st.success("매수했습니다."); st.rerun()
            except ValueError as e: st.error(str(e))
    with c2:
        if st.button("매도", use_container_width=True):
            try: sell_property(user_id,selected["property_id"],qty); st.success("매도했습니다."); st.rerun()
            except ValueError as e: st.error(str(e))
with tabs[3]:
    st.subheader("오늘의 퀴즈")
    for q in get_quiz_questions():
        answer=st.radio(q["question"],q["choices"],key=q["id"])
        if st.button("제출",key=f"submit_{q['id']}"):
            result=submit_quiz_answer(user_id,q["id"],q["choices"].index(answer),today); st.info(("정답입니다! +10코인" if result["correct"] else "오답입니다.")+" "+result.get("message",result["explanation"]))
with tabs[4]:
    st.subheader("AI 투자 상담")
    if home.get("region_code"):
        st.caption(f"규제 RAG 기준 지역: {home['region_name']} · 화면을 열 때는 API를 호출하지 않습니다.")
        if st.button("법제처 규제 정보 새로고침", key="refresh_regulations"):
            try:
                result = sync_regulations(home["region_code"], home["region_name"])
                st.success(f"{result['saved']}건을 SQLite에 저장했습니다. 이후 상담부터 검색 근거로 사용합니다.")
            except RuntimeError as exc:
                st.error(str(exc))
    st.caption("테스트 모드: 상담 횟수 제한 없이 OpenAI LLM과 대화할 수 있습니다. 현재 포트폴리오와 오늘의 뉴스도 함께 참고합니다.")
    if st.session_state.get("advisor_user") != user_id:
        st.session_state.advisor_session_id = get_or_create_chat_session(user_id)
        st.session_state.advisor_messages = get_chat_messages(st.session_state.advisor_session_id, user_id)
        st.session_state.advisor_user = user_id
    for message in st.session_state.advisor_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("예: 현금 비중을 어떻게 공부하면 좋을까요?")
    if question:
        st.session_state.advisor_messages.append({"role":"user", "content":question})
        save_chat_message(st.session_state.advisor_session_id, user_id, "user", question)
        with st.chat_message("user"):
            st.markdown(question)
        result = ask_ai_advisor(user_id, question, portfolio, today_news, today, st.session_state.advisor_messages[:-1])
        if result["success"]:
            st.session_state.advisor_messages.append({"role":"assistant", "content":result["answer"]})
            save_chat_message(st.session_state.advisor_session_id, user_id, "assistant", result["answer"])
            with st.chat_message("assistant"):
                st.markdown(result["answer"])
        else:
            st.error(result["message"])
    if st.session_state.advisor_messages and st.button("대화 초기화"):
        st.session_state.advisor_session_id = get_or_create_chat_session(user_id)
        st.session_state.advisor_messages = []
        st.rerun()

