import sqlite3
import time

DB_NAME = "links.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            url TEXT,
            expires_at INTEGER,
            clicks_left INTEGER
        )
    """)
    conn.commit()
    conn.close()

def create_link(code, url, expires_at, clicks):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO links VALUES (?, ?, ?, ?)",
        (code, url, expires_at, clicks)
    )
    conn.commit()
    conn.close()

def get_link(code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT url, expires_at, clicks_left FROM links WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    return row

def update_clicks(code, clicks_left):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE links SET clicks_left=? WHERE code=?", (clicks_left, code))
    conn.commit()
    conn.close()

def delete_link(code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM links WHERE code=?", (code,))
    conn.commit()
    conn.close()