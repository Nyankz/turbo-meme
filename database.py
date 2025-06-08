import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    media TEXT,
    name TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS battles (
    id TEXT PRIMARY KEY,
    user1_id INTEGER,
    user2_id INTEGER,
    start_time TEXT,
    end_time TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    user_id INTEGER,
    battle_id TEXT,
    voted_for TEXT
)
""")

conn.commit()

def add_user(user_id, username, media, name):
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                   (user_id, username, media, name, "waiting"))
    conn.commit()

def get_waiting_user():
    cursor.execute("SELECT * FROM users WHERE status='waiting'")
    return cursor.fetchone()

def start_battle(battle_id, u1, u2):
    now = datetime.now()
    end = now + timedelta(minutes=30)
    cursor.execute("INSERT INTO battles VALUES (?, ?, ?, ?, ?)",
                   (battle_id, u1, u2, now.isoformat(), end.isoformat()))
    cursor.execute("UPDATE users SET status='battling' WHERE id IN (?, ?)", (u1, u2))
    conn.commit()
    return now, end

def add_vote(user_id, battle_id, voted_for):
    cursor.execute("INSERT INTO votes VALUES (?, ?, ?)", (user_id, battle_id, voted_for))
    conn.commit()

def has_voted(user_id, battle_id):
    cursor.execute("SELECT * FROM votes WHERE user_id=? AND battle_id=?", (user_id, battle_id))
    return cursor.fetchone() is not None

def get_battle_votes(battle_id):
    cursor.execute("SELECT voted_for, COUNT(*) FROM votes WHERE battle_id=? GROUP BY voted_for", (battle_id,))
    return dict(cursor.fetchall())

def get_battle(battle_id):
    cursor.execute("SELECT * FROM battles WHERE id=?", (battle_id,))
    return cursor.fetchone()