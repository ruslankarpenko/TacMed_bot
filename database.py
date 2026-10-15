import sqlite3
from contextlib import closing

DB_PATH = "bot.db"


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_msgs (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id INTEGER
            )
        """)
        cur.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('registration_open','1')")
        conn.commit()


def add_user(user_id, username, first_name):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users(user_id, username, first_name) VALUES (?,?,?)",
            (user_id, username, first_name),
        )
        conn.commit()


def mark_registered(user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("UPDATE users SET registered=1 WHERE user_id=?", (user_id,))
        conn.commit()


def unmark_registered(user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("UPDATE users SET registered=0 WHERE user_id=?", (user_id,))
        conn.commit()


def is_registered(user_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT registered FROM users WHERE user_id=?", (user_id,)).fetchone()
        return bool(row and row[0])


# === Розсилка ===
def all_users() -> list[int]:
    """Усі, хто запускав бота."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
        return [r[0] for r in rows]


def registered_users() -> list[int]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute("SELECT user_id FROM users WHERE registered=1").fetchall()
        return [r[0] for r in rows]


# === Reply-зв'язка ===
def save_admin_msg(admin_msg_id: int, user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admin_msgs(admin_msg_id, user_id) VALUES (?,?)",
            (admin_msg_id, user_id),
        )
        conn.commit()


def get_user_for_admin_msg(admin_msg_id: int) -> int | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT user_id FROM admin_msgs WHERE admin_msg_id=?", (admin_msg_id,)
        ).fetchone()
        return row[0] if row else None


# === Налаштування ===
def registration_open() -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='registration_open'").fetchone()
        return bool(row and row[0] == "1")


def set_registration_open(open_: bool):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "UPDATE settings SET value=? WHERE key='registration_open'",
            ("1" if open_ else "0",),
        )
        conn.commit()