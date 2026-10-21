"""SQLite storage and shared schema for the simulator."""
from __future__ import annotations
import sqlite3
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
        CREATE TABLE IF NOT EXISTS transactions (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, date TEXT NOT NULL, property_id TEXT NOT NULL, transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy','sell')), quantity INTEGER NOT NULL CHECK(quantity>0), transaction_price INTEGER NOT NULL CHECK(transaction_price>0), FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(property_id) REFERENCES properties(property_id));
        """)
        conn.commit()
    finally:
        if owns: conn.close()

def ensure_user(conn: sqlite3.Connection, user_id: str) -> None:
    if not user_id or not str(user_id).strip(): raise ValueError("user_id is required")
    conn.execute("INSERT OR IGNORE INTO users (user_id,cash,coins) VALUES (?,?,0)", (str(user_id), INITIAL_CASH))
