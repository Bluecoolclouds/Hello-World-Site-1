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
                    preferences TEXT
                )
            """)

    def save_user(self, user_id: int, data: Dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (user_id, age, gender, city, bio, preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, data['age'], data['gender'], data['city'], data['bio'], data['preferences']))

    def get_user(self, user_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT age, gender, city, bio, preferences FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "age": row[0],
                    "gender": row[1],
                    "city": row[2],
                    "bio": row[3],
                    "preferences": row[4]
                }
            return None
