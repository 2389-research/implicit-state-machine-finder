# ABOUTME: SQLite schema and connection helper for depot.
# ABOUTME: Every module takes a connection made by connect().
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'pending',
    total_cents INTEGER NOT NULL,
    paid_at TEXT,
    shipped_at TEXT,
    refunded_at TEXT,
    cancelled_at TEXT
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    running INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    done INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY,
    expected_parts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS upload_parts (
    upload_id INTEGER NOT NULL,
    n INTEGER NOT NULL,
    body BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'open'
);
"""


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
