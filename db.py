import sqlite3
from datetime import datetime
import random

class Database:
    def __init__(self, db_path="dating_bot.db"):
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    age INTEGER,
                    gender TEXT,
                    city TEXT,
                    bio TEXT,
                    preferences TEXT,
                    rating INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    from_user INTEGER,
                    to_user INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_user) REFERENCES users (user_id),
                    FOREIGN KEY (to_user) REFERENCES users (user_id),
                    UNIQUE(from_user, to_user)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    user1 INTEGER,
                    user2 INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user1) REFERENCES users (user_id),
                    FOREIGN KEY (user2) REFERENCES users (user_id),
                    UNIQUE(user1, user2)
                )
            """)
            conn.commit()

    def create_user(self, user_id, username, age, gender, city, bio, preferences):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (user_id, username, age, gender, city, bio, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, age, gender, city, bio, preferences))
            conn.commit()

    def get_user(self, user_id):
        with self._get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(user) if user else None

    def get_random_user(self, exclude_user_id, city, preferences):
        """
        preferences can be 'men', 'women', or 'both'
        """
        with self._get_connection() as conn:
            query = "SELECT * FROM users WHERE user_id != ? AND is_active = 1 AND city = ?"
            params = [exclude_user_id, city]
            
            if preferences == "men":
                query += " AND gender = 'male'"
            elif preferences == "women":
                query += " AND gender = 'female'"
            
            # Exclude already liked users
            query += " AND user_id NOT IN (SELECT to_user FROM likes WHERE from_user = ?)"
            params.append(exclude_user_id)
            
            users = conn.execute(query, params).fetchall()
            if not users:
                return None
            return dict(random.choice(users))

    def like_user(self, from_user, to_user):
        with self._get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO likes (from_user, to_user) VALUES (?, ?)", (from_user, to_user))
            conn.commit()
            return self.check_match(from_user, to_user)

    def check_match(self, user1, user2):
        with self._get_connection() as conn:
            # Check if user2 also liked user1
            like = conn.execute("SELECT 1 FROM likes WHERE from_user = ? AND to_user = ?", (user2, user1)).fetchone()
            if like:
                # Create match
                u1, u2 = min(user1, user2), max(user1, user2)
                conn.execute("INSERT OR IGNORE INTO matches (user1, user2) VALUES (?, ?)", (u1, u2))
                conn.commit()
                return True
            return False

    def get_matches(self, user_id):
        with self._get_connection() as conn:
            matches = conn.execute("""
                SELECT * FROM users WHERE user_id IN (
                    SELECT user2 FROM matches WHERE user1 = ?
                    UNION
                    SELECT user1 FROM matches WHERE user2 = ?
                )
            """, (user_id, user_id)).fetchall()
            return [dict(u) for u in matches]

    def ban_user(self, user_id):
        with self._get_connection() as conn:
            conn.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()

    def unban_user(self, user_id):
        with self._get_connection() as conn:
            conn.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
            conn.commit()

# Example usage/migration
if __name__ == "__main__":
    db = Database()
    print("Database initialized and tables created.")
