# 2인 하루 MVP: 부동산 투자 시뮬레이터

파이썬과 Streamlit으로 만드는 교육용 부동산 투자 시뮬레이터입니다.

## 프로젝트 구조

```text
.
├── app.py              # 팀원 B: Streamlit 화면 및 기능 연결
├── ai_advisor.py       # 팀원 B: AI 상담 및 상담권
├── database.py         # 팀원 A: SQLite 연결 및 공통 데이터 저장
├── market.py           # 팀원 A: 지역, 뉴스 효과, 매수·매도
├── quiz.py             # 팀원 B: 퀴즈 및 코인 보상
├── news_data.json      # 팀원 A: 예시 뉴스 데이터
├── data/
│   └── .gitkeep        # SQLite 파일 저장 위치 (app.db는 생성 후 Git 제외)
├── requirements.txt
└── .gitignore
```

## 역할 분담

- 팀원 A: `market.py`, `database.py`, `news_data.json`
- 팀원 B: `quiz.py`, `ai_advisor.py`, `app.py`

공통 데이터 규칙과 함수 인터페이스는 작업 지시서의 정의를 기준으로 유지합니다.

## 실행 준비

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

실제 결제와 실제 뉴스 수집은 이 MVP 범위에 포함하지 않습니다.
