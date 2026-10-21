"""SQLite storage and shared schema for the simulator."""
from __future__ import annotations
import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "data" / "app.db"
INITIAL_CASH = 1_000_000_000

def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    initialize_database(conn)
    return conn

def initialize_database(conn: sqlite3.Connection | None = None) -> None:
    owns = conn is None
    conn = conn or sqlite3.connect(DATABASE_PATH)
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, cash INTEGER NOT NULL DEFAULT 1000000000 CHECK(cash>=0), coins INTEGER NOT NULL DEFAULT 0 CHECK(coins>=0), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS properties (property_id TEXT PRIMARY KEY, name TEXT NOT NULL, current_price INTEGER NOT NULL CHECK(current_price>0), characteristics TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS holdings (user_id TEXT NOT NULL, property_id TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>=0), average_purchase_price REAL NOT NULL CHECK(average_purchase_price>=0), PRIMARY KEY(user_id,property_id), FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(property_id) REFERENCES properties(property_id));
        CREATE TABLE IF NOT EXISTS news (news_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, title TEXT NOT NULL, type TEXT NOT NULL, target_property_id TEXT NOT NULL, price_impact_rate REAL NOT NULL, summary TEXT NOT NULL, UNIQUE(date,title,target_property_id), FOREIGN KEY(target_property_id) REFERENCES properties(property_id));
        CREATE TABLE IF NOT EXISTS daily_news_applications (date TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS quiz_records (user_id TEXT NOT NULL, date TEXT NOT NULL, question_id TEXT NOT NULL, is_correct INTEGER NOT NULL, reward_granted INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,date,question_id), FOREIGN KEY(user_id) REFERENCES users(user_id));
        CREATE TABLE IF NOT EXISTS advice_usage (user_id TEXT NOT NULL, date TEXT NOT NULL, free_advice_count INTEGER NOT NULL DEFAULT 0, extra_advice_credits INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,date), FOREIGN KEY(user_id) REFERENCES users(user_id));
        CREATE TABLE IF NOT EXISTS user_home (user_id TEXT PRIMARY KEY, property_id TEXT NOT NULL, purchased_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(property_id) REFERENCES properties(property_id));
        CREATE TABLE IF NOT EXISTS user_interests (user_id TEXT NOT NULL, property_id TEXT NOT NULL, added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id,property_id), FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(property_id) REFERENCES properties(property_id));
        CREATE TABLE IF NOT EXISTS chat_sessions (session_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, title TEXT NOT NULL DEFAULT 'AI 부동산 상담', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(user_id));
        CREATE TABLE IF NOT EXISTS chat_messages (message_id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','assistant')), content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS transactions (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, date TEXT NOT NULL, property_id TEXT NOT NULL, transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy','sell')), quantity INTEGER NOT NULL CHECK(quantity>0), transaction_price INTEGER NOT NULL CHECK(transaction_price>0), FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(property_id) REFERENCES properties(property_id));
        """)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    finally:
        if owns: conn.close()

def ensure_user(conn: sqlite3.Connection | str, user_id: str | None = None) -> None:
    """Create a user; supports both ensure_user(conn, id) and ensure_user(id)."""
    owns = user_id is None
    if owns:
        user_id = str(conn)
        conn = get_connection()
    if not user_id or not str(user_id).strip(): raise ValueError("user_id is required")
    conn.execute("INSERT OR IGNORE INTO users (user_id,cash,coins) VALUES (?,?,0)", (str(user_id), INITIAL_CASH))
    if owns:
        conn.commit()
        conn.close()

def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"pbkdf2_sha256$240000${salt.hex()}${digest.hex()}"

def _password_matches(password: str, encoded: str | None) -> bool:
    if not encoded or not encoded.startswith("pbkdf2_sha256$"): return False
    _, rounds, salt_hex, digest_hex = encoded.split("$", 3)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
    return hmac.compare_digest(candidate, digest_hex)

def register_user(user_id: str, password: str) -> tuple[bool, str]:
    user_id, password = user_id.strip(), password.strip()
    if len(user_id) < 3: return False, "아이디는 3자 이상이어야 합니다."
    if len(password) < 4: return False, "비밀번호는 4자 이상이어야 합니다."
    with get_connection() as conn:
        if conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone(): return False, "이미 사용 중인 아이디입니다."
        conn.execute("INSERT INTO users(user_id,password_hash) VALUES(?,?)", (user_id, _password_hash(password))); conn.commit()
    return True, "회원가입이 완료되었습니다."

def authenticate_user(user_id: str, password: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE user_id=?", (user_id.strip(),)).fetchone()
    return bool(row and _password_matches(password, row["password_hash"]))
