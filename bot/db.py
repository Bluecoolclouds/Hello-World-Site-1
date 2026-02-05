import sqlite3
from typing import Optional, Dict

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    age INTEGER,
                    gender TEXT,
                    city TEXT,
                    bio TEXT,
                    preferences TEXT,
                    view_count INTEGER DEFAULT 0,
                    last_search_at REAL DEFAULT 0,
                    search_count_hour INTEGER DEFAULT 0,
                    last_hour_reset REAL DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (from_user_id, to_user_id)
                )
            """)

    def save_user(self, user_id: int, data: Dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (user_id, age, gender, city, bio, preferences, view_count, last_search_at, search_count_hour, last_hour_reset)
                VALUES (?, ?, ?, ?, ?, ?, 
                    (SELECT COALESCE(view_count, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(last_search_at, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(search_count_hour, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(last_hour_reset, 0) FROM users WHERE user_id = ?)
                )
            """, (user_id, data['age'], data['gender'], data['city'], data['bio'], data['preferences'], user_id, user_id, user_id, user_id))

    def get_user(self, user_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_random_profile(self, user_id: int, city: str, preferences: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM users 
                WHERE user_id != ? AND city = ? 
                ORDER BY RANDOM() LIMIT 1
            """, (user_id, city))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_like(self, from_id: int, to_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO likes (from_user_id, to_user_id) VALUES (?, ?)", (from_id, to_id))
            cursor = conn.execute("SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?", (to_id, from_id))
            return cursor.fetchone() is not None

    def update_search_stats(self, user_id: int, timestamp: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users SET 
                view_count = view_count + 1,
                last_search_at = ?,
                search_count_hour = CASE 
                    WHEN ? - last_hour_reset > 3600 THEN 1 
                    ELSE search_count_hour + 1 
                END,
                last_hour_reset = CASE 
                    WHEN ? - last_hour_reset > 3600 THEN ? 
                    ELSE last_hour_reset 
                END
                WHERE user_id = ?
            """, (timestamp, timestamp, timestamp, timestamp, user_id))
