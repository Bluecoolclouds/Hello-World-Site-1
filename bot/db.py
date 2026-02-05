import sqlite3
from typing import Optional, Dict, List

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    user1_id INTEGER,
                    user2_id INTEGER,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (user1_id, user2_id)
                )
            """)

    def save_user(self, user_id: int, data: Dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (user_id, username, age, gender, city, bio, preferences, view_count, last_search_at, search_count_hour, last_hour_reset)
                VALUES (?, ?, ?, ?, ?, ?, ?,
                    (SELECT COALESCE(view_count, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(last_search_at, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(search_count_hour, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(last_hour_reset, 0) FROM users WHERE user_id = ?)
                )
            """, (user_id, data.get('username'), data['age'], data['gender'], data['city'], data['bio'], data['preferences'], user_id, user_id, user_id, user_id))

    def get_user(self, user_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_random_profile(self, user_id: int, city: str, preferences: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            gender_filter = None
            if preferences == 'м':
                gender_filter = 'м'
            elif preferences == 'ж':
                gender_filter = 'ж'
            
            if gender_filter:
                cursor = conn.execute("""
                    SELECT * FROM users 
                    WHERE user_id != ? 
                    AND city = ? 
                    AND gender = ?
                    AND user_id NOT IN (
                        SELECT to_user_id FROM likes WHERE from_user_id = ?
                    )
                    ORDER BY RANDOM() LIMIT 1
                """, (user_id, city, gender_filter, user_id))
            else:
                cursor = conn.execute("""
                    SELECT * FROM users 
                    WHERE user_id != ? 
                    AND city = ?
                    AND user_id NOT IN (
                        SELECT to_user_id FROM likes WHERE from_user_id = ?
                    )
                    ORDER BY RANDOM() LIMIT 1
                """, (user_id, city, user_id))
            
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_like(self, from_id: int, to_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO likes (from_user_id, to_user_id) VALUES (?, ?)", (from_id, to_id))
            cursor = conn.execute("SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?", (to_id, from_id))
            return cursor.fetchone() is not None

    def create_match(self, user1_id: int, user2_id: int):
        min_id, max_id = min(user1_id, user2_id), max(user1_id, user2_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO matches (user1_id, user2_id) 
                VALUES (?, ?)
            """, (min_id, max_id))

    def get_user_matches(self, user_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END as matched_user_id,
                    created_at
                FROM matches 
                WHERE user1_id = ? OR user2_id = ?
                ORDER BY created_at DESC
            """, (user_id, user_id, user_id))
            return [dict(row) for row in cursor.fetchall()]

    def get_received_likes(self, user_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT l.from_user_id, l.created_at, u.age, u.city
                FROM likes l
                JOIN users u ON l.from_user_id = u.user_id
                WHERE l.to_user_id = ?
                AND l.from_user_id NOT IN (
                    SELECT to_user_id FROM likes WHERE from_user_id = ?
                )
                ORDER BY l.created_at DESC
            """, (user_id, user_id))
            return [dict(row) for row in cursor.fetchall()]

    def increment_view_count(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users SET view_count = view_count + 1
                WHERE user_id = ?
            """, (user_id,))

    def update_search_stats(self, user_id: int, timestamp: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users SET 
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

    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = self.get_user(user_id)
            if not user:
                return None
            
            likes_sent = conn.execute(
                "SELECT COUNT(*) as count FROM likes WHERE from_user_id = ?", 
                (user_id,)
            ).fetchone()['count']
            
            likes_received = conn.execute(
                "SELECT COUNT(*) as count FROM likes WHERE to_user_id = ?", 
                (user_id,)
            ).fetchone()['count']
            
            matches_count = conn.execute("""
                SELECT COUNT(*) as count FROM matches 
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id)).fetchone()['count']
            
            return {
                'view_count': user['view_count'],
                'likes_sent': likes_sent,
                'likes_received': likes_received,
                'matches_count': matches_count,
                'search_count_hour': user['search_count_hour']
            }
