"""Streamlit 진입점."""
import streamlit as st
from datetime import date
from database import ensure_user, register_user, authenticate_user
from market import (get_properties, get_user_portfolio, apply_daily_news, buy_property, sell_property,
                    get_home, set_home, get_interests, add_interest, remove_interest)
from quiz import get_quiz_questions, submit_quiz_answer, get_coin_balance
from ai_advisor import ask_ai_advisor, get_or_create_chat_session, get_chat_messages, save_chat_message
from regulation_rag import sync_regulations
from public_data import price_history
from ai_advisor import redeem_advice_credits

st.set_page_config(page_title="하우스렌즈", page_icon="•", layout="wide")
st.markdown("""
<style>
:root { --ink:#111111; --muted:#111111; --blue:#111111; --blue-soft:#fff2b8; --line:#e5e7eb; --card:#ffffff; --bg:#f7f8fa; --green:#111111; }
html, body, [class*="css"], button, input, textarea, select { font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",Arial,sans-serif; }
.stApp, .stApp p, .stApp span, .stApp label, .stApp div, .stApp li { color:var(--ink); }
.stApp { background:var(--bg); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(246,248,252,.9); }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
.main .block-container { max-width:1180px; margin:28px auto; padding:34px 42px 48px; background:#fff; border:1px solid #bfc5cf; border-radius:6px; box-shadow:0 8px 24px rgba(30,55,90,.06); }
.hero { display:flex; align-items:center; justify-content:space-between; background:#fff3c4; color:#111; border:1px solid #f0d96b; border-radius:22px; padding:30px 36px; margin:0 0 24px; box-shadow:0 12px 28px rgba(120,100,20,.10); }
.hero h1 { margin:0; font-size:30px; letter-spacing:-1.2px; color:#111 !important; }
.hero p { margin:7px 0 0; color:#111 !important; font-size:14px; }
.section-title { font-size:20px; font-weight:800; color:var(--ink); margin:24px 0 12px; letter-spacing:-.5px; }
.property-card, .news-card { background:var(--card); border:1px solid #dfe4ec; border-radius:12px; padding:20px; min-height:150px; box-shadow:none; }
.property-card h4, .news-card h4 { margin:0 0 9px; color:var(--ink); font-size:17px; }
.property-card p, .news-card p { color:var(--muted); font-size:13px; line-height:1.65; margin:4px 0; }
.price { font-size:22px; font-weight:800; color:#111 !important; letter-spacing:-.5px; }
.badge-good, .badge-bad { color:#111; background:#fff0a8; border:1px solid #e2c84e; border-radius:999px; padding:5px 10px; font-size:12px; font-weight:700; }
.icon-chip { display:inline-flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:10px; background:#fff0a8; color:#ff7a00 !important; font-weight:800; margin-right:8px; }
.ui-icon { display:inline-flex; width:30px; height:30px; align-items:center; justify-content:center; border-radius:10px; margin-right:8px; color:#ff7a00 !important; font-weight:800; background:#fff0a8; border:1px solid #e2c84e; vertical-align:middle; }
.ui-icon.yellow, .ui-icon.mint, .ui-icon.pink, .ui-icon.lavender { background:#fff0a8; }
.brand-mark { font-size:38px; font-weight:800; color:#111 !important; letter-spacing:-1.5px; margin:4px 0 76px; }
.wire-card-title { font-size:18px; font-weight:700; color:var(--ink); margin-bottom:6px; }
.wire-card-sub { color:var(--muted); font-size:13px; }
.wire-empty { min-height:70px; display:flex; align-items:center; color:#9aa6b8; font-size:14px; }
.separate-card { background:#fffdf4; border:1px solid #e8d98c; border-radius:8px; padding:18px; margin-bottom:14px; }
.login-panel { background:transparent; border:0; border-radius:0; padding:36px 48px; max-width:560px; margin:0 auto; box-shadow:none; text-align:left; }
.main .block-container:has(.login-panel) { min-height:calc(100vh - 56px); display:flex; flex-direction:column; justify-content:center; }
.main .block-container:has(.login-panel) .brand-mark { position:absolute; top:28px; left:42px; margin:0; font-size:28px; }
div[data-baseweb="input"] input { min-height:34px !important; padding-top:6px !important; padding-bottom:6px !important; font-size:14px !important; }
div.stButton > button { border-radius:11px; min-height:42px; font-weight:700; border:1px solid #dce3ef; background:#fff; color:var(--ink); }
div.stButton > button[kind="primary"] { background:var(--blue); border-color:var(--blue); color:#fff; }
div.stButton > button[kind="primary"] { background:#fff0a8; border-color:#f0d96b; color:#111 !important; }
[data-testid="stMetric"] { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:18px; box-shadow:0 6px 18px rgba(30,55,90,.04); }
[data-testid="stMetricValue"] { color:var(--ink); font-weight:800; }
[data-testid="stMetricLabel"] { color:var(--muted) !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color:var(--ink); }
h1, h2, h3, h4, h5, h6 { color:var(--ink) !important; }
.stCaption, [data-testid="stCaptionContainer"] { color:var(--muted) !important; }
[data-testid="stAlert"] p { color:inherit !important; }
[data-baseweb="tab-list"] { color:var(--ink); }
[data-baseweb="tab-list"] { gap:8px; background:#fff; padding:7px; border:1px solid var(--line); border-radius:14px; }
[data-baseweb="tab"] { border-radius:10px; color:var(--muted) !important; padding:8px 18px; }
[aria-selected="true"] { color:#111 !important; background:#fff2b8; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:#bfc5cf; border-radius:4px; background:#fff; }
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { border-radius:4px; border:1px solid #d8b83d; }
div[data-baseweb="input"] input, div[data-baseweb="select"] *, textarea { color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important; }
div[data-baseweb="select"] > div { background:#fff8d6 !important; color:#111 !important; border-color:#e2c84e !important; }
div[data-baseweb="select"] svg { fill:#ff7a00 !important; color:#ff7a00 !important; }
div[data-baseweb="select"] [role="option"] { background:#fff8d6 !important; color:#111 !important; }
div[data-baseweb="popover"], div[data-baseweb="menu"], div[role="listbox"] { background:#fff8d6 !important; border:1px solid #e2c84e !important; }
div[data-baseweb="popover"] *, div[data-baseweb="menu"] *, div[role="listbox"] * { background:#fff8d6 !important; color:#111 !important; -webkit-text-fill-color:#111 !important; }
div[data-baseweb="popover"] [aria-selected="true"], div[role="option"][aria-selected="true"] { background:#ffe98a !important; color:#111 !important; }
div[data-baseweb="input"] > div { background:#fff; }
button[kind="secondary"], button[kind="tertiary"] { color:#111 !important; }
button, input, textarea, select, [role="option"], [role="button"] { color:#111 !important; }
.stSelectbox label, .stTextInput label, .stNumberInput label { color:#111 !important; }
.stAlert, .stAlert p { color:#111 !important; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="brand-mark"><span class="ui-icon yellow">⌂</span>홈테크</div>', unsafe_allow_html=True)
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
                st.session_state.logged_in_user = login_id.strip(); st.session_state.news_popup_closed = False; st.rerun()
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
    st.markdown("## 시작 자산")
    asset_col, guide_col = st.columns([1, 1.4], gap="large")
    with asset_col:
        st.metric("초기 보유자산", f"{portfolio['total_assets']:,}원")
        st.caption("현금 10억원으로 시작합니다.")
    with guide_col:
        st.info("첫 집을 선택하면 해당 지역이 내 집으로 등록되고, 이후 실거래가·뉴스·규제 정보를 한 화면에서 확인할 수 있습니다.")
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
coin_balance = get_coin_balance(user_id)
st.sidebar.metric("보유 코인", f"{coin_balance}개")
st.sidebar.caption("상담권 교환: 200코인 → AI 상담 10회")
if st.sidebar.button("상담권 교환", disabled=coin_balance < 200):
    redeemed = redeem_advice_credits(user_id)
    st.sidebar.success(redeemed["message"] if not redeemed["success"] else "상담권 10회가 추가되었습니다.")

available = [p for p in properties if p["property_id"] not in {home["property_id"], *(x["property_id"] for x in interests)}]

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
        st.markdown('<h2><span class="ui-icon pink">!</span>오늘의 뉴스</h2>', unsafe_allow_html=True)
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

# 뉴스는 로그인 직후 모달 팝업으로만 표시합니다.

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

if st.session_state.get("news_popup_user") != user_id:
    st.session_state.news_popup_user = user_id
    st.session_state.news_popup_closed = False
if "news_popup_closed" not in st.session_state:
    st.session_state.news_popup_closed = False
if not st.session_state.news_popup_closed:
    show_news_popup()

if st.button("오늘의 뉴스 다시 보기", type="secondary"):
    show_news_popup()

tabs = st.tabs(["홈", "지역 시장", "거래", "퀴즈", "AI 상담"])
with tabs[0]:
    st.markdown('<div class="section-title">오늘의 자산 현황</div>', unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4); c1.metric("총 보유자산", f"{portfolio['total_assets']:,}원"); c2.metric("현금", f"{portfolio['cash']:,}원"); c3.metric("부동산 평가액", f"{portfolio['holdings_value']:,}원"); c4.metric("보유 코인", f"{portfolio['coins']}개")
    st.caption("신규 가입 시 초기 보유자산은 현금 10억원입니다.")
    st.markdown('<div class="section-title">보유 부동산</div>', unsafe_allow_html=True)
    if portfolio["holdings"]:
        cols = st.columns(min(3, len(portfolio["holdings"])))
        for col, item in zip(cols, portfolio["holdings"]):
            with col:
                st.markdown(f'<div class="property-card"><h4><span class="icon-chip">H</span>{item["name"]}</h4><p>{item["quantity"]}채 보유 · 평균 매입가 {item["average_purchase_price"]:,.0f}원</p><div class="price">{item["current_value"]:,}원</div><p>현재가 기준 평가액</p></div>', unsafe_allow_html=True)
    else:
        st.info("아직 보유한 부동산이 없습니다. 지역 시장에서 매물을 살펴보세요.")
    st.markdown('<div class="section-title"><span class="ui-icon yellow">★</span>관심 매물</div>', unsafe_allow_html=True)
    if interests:
        interest_cols = st.columns(min(3, len(interests)))
        for col, item in zip(interest_cols, interests):
            with col:
                st.markdown(f'<div class="property-card"><h4><span class="icon-chip">★</span>{item["name"]}</h4><div class="price">{item["current_price"]:,}원</div><p>관심 매물 · 가상 시장 가격</p></div>', unsafe_allow_html=True)
                if st.button("관심 해제", key=f"remove_home_{item['property_id']}", use_container_width=True):
                    remove_interest(user_id, item["property_id"]); st.rerun()
    else:
        st.info("아직 관심 매물이 없습니다.")
    if available:
        add_select_col, add_button_col = st.columns([8, 1], gap="small", vertical_alignment="bottom")
        with add_select_col:
            interest_choice = st.selectbox("관심 매물 추가", available, format_func=lambda p: p["name"], label_visibility="collapsed", key="home_interest_choice")
        with add_button_col:
            if st.button("＋", key="home_add_interest", type="primary", help="관심 매물 추가", use_container_width=True):
                add_interest(user_id, interest_choice["property_id"]); st.rerun()
with tabs[1]:
    st.markdown('<div class="section-title">지역 시장</div>', unsafe_allow_html=True)
    st.caption("가상 지역별 매물과 시장 정보를 검색해보세요.")
    region_names = sorted({item["region_name"] for item in properties if item.get("region_name")})
    search_col, region_col = st.columns([1.4, 1], gap="medium")
    with search_col:
        st.markdown('<span class="ui-icon yellow">⌕</span><b>매물 검색</b>', unsafe_allow_html=True)
        property_query = st.text_input("매물 검색", placeholder="예: 공원, 역세권, 신산업", key="property_query")
    with region_col:
        selected_region = st.selectbox("지역 필터", ["전체 지역"] + region_names, key="selected_region")
    filtered_properties = [item for item in properties if
        (selected_region == "전체 지역" or item.get("region_name") == selected_region) and
        (not property_query.strip() or property_query.strip().lower() in f"{item['name']} {item['characteristics']}".lower())]
    st.caption(f"검색 결과 {len(filtered_properties)}개")
    for start in range(0, len(filtered_properties), 3):
        cols = st.columns(3)
        for col, item in zip(cols, filtered_properties[start:start+3]):
            with col:
                home_badge = " · 내 집" if item["property_id"] == home["property_id"] else ""
                st.markdown(f'<div class="property-card"><h4><span class="icon-chip">R</span>{item["name"]}{home_badge}</h4><div class="price">{item["current_price"]:,}원</div><p>{item["characteristics"]}</p></div>', unsafe_allow_html=True)
    if not filtered_properties:
        st.info("검색 조건에 맞는 매물이 없습니다.")
    st.divider()
    st.subheader("지역별 실거래가 추이")
    chart_properties = [p for p in properties if p.get("region_code")]
    chart_property = st.selectbox("차트를 볼 지역", chart_properties, format_func=lambda p: p["name"], key="chart_property")
    chart_years = st.radio("조회 기간", [1, 3, 5, 10], format_func=lambda n: f"{n}년", horizontal=True, key="chart_years")
    history = price_history(chart_property["region_code"], chart_years)
    if history:
        import pandas as pd
        chart_df = pd.DataFrame(history).set_index("month").rename(columns={"average_price":"평균 거래가", "transaction_count":"거래 건수"})
        st.line_chart(chart_df["평균 거래가"])
        virtual = bool(history[0].get("is_virtual"))
        label = "국토부 공개 실거래가 추세를 참고한 교육용 가상 데이터" if virtual else "수집된 공개데이터를 참고한 교육용 시뮬레이션"
        st.caption(f"{chart_property['name']} · 월별 평균 거래가 · {label}")
    st.subheader("이 지역의 오늘 뉴스")
    region_news = [n for n in news_result["news"] if n["target_property_id"] == chart_property["property_id"]]
    if region_news:
        for item in region_news:
            st.markdown(f"**{news_label(item)} · {item['title']}**  \n{item['summary']}")
    else:
        st.info("오늘 등록된 지역 뉴스가 없습니다.")
with tabs[2]:
    st.markdown('<h3><span class="ui-icon mint">↔</span>거래하기</h3>', unsafe_allow_html=True)
    props=get_properties(); selected=st.selectbox("지역", props, format_func=lambda p:f"{p['name']} — {p['current_price']:,}원")
    qty_col, action_col = st.columns([1, 1], gap="medium")
    with qty_col:
        st.markdown('<span class="ui-icon yellow" style="width:24px;height:24px">#</span><b>수량</b>', unsafe_allow_html=True)
        qty=st.number_input("수량", min_value=1, value=1, step=1, label_visibility="collapsed")
    with action_col:
        if st.button("매수  →", use_container_width=True):
            try: buy_property(user_id,selected["property_id"],qty); st.success("매수했습니다."); st.rerun()
            except ValueError as e: st.error(str(e))
        if st.button("매도  →", use_container_width=True):
            try: sell_property(user_id,selected["property_id"],qty); st.success("매도했습니다."); st.rerun()
            except ValueError as e: st.error(str(e))
with tabs[3]:
    st.subheader("오늘의 퀴즈")
    for q in get_quiz_questions():
        answer=st.radio(q["question"],q["choices"],key=q["id"])
        if st.button("제출",key=f"submit_{q['id']}"):
            result=submit_quiz_answer(user_id,q["id"],q["choices"].index(answer),today); st.info(("정답입니다! +10코인" if result["correct"] else "오답입니다.")+" "+result.get("message",result["explanation"]))
with tabs[4]:
    st.markdown('<h3><span class="ui-icon lavender">✦</span>AI 투자 상담</h3>', unsafe_allow_html=True)
    if home.get("region_code"):
        st.caption(f"실거래가 차트: 국토부 공개 추세를 참고한 교육용 가상 데이터 · {home['region_name']}")
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
    st.markdown('<span class="ui-icon lavender">?</span><b>AI에게 질문하기</b>', unsafe_allow_html=True)
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

