import sqlite3
import time
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


def normalize_city(city: str) -> str:
    """Нормализация названия города: убираем пробелы, приводим к нижнему регистру"""
    if not city:
        return ""
    return city.strip().lower()


def format_online_status(last_active: float) -> str:
    """Форматирование статуса онлайн"""
    if not last_active:
        return "🔘 Статус неизвестен"
    
    now = time.time()
    diff = now - last_active
    
    if diff < 300:  # 5 минут
        return "🟢 Онлайн"
    elif diff < 3600:  # 1 час
        minutes = int(diff / 60)
        return f"🟡 Был(а) {minutes} мин. назад"
    elif diff < 86400:  # 1 день
        hours = int(diff / 3600)
        return f"🟠 Был(а) {hours} ч. назад"
    elif diff < 604800:  # 7 дней
        days = int(diff / 86400)
        return f"🔴 Был(а) {days} дн. назад"
    else:
        return "⚫ Неактивен >недели"


class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
        self._create_tables()
        self._migrate_tables()

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
                    looking_for TEXT,
                    photo_id TEXT,
                    media_type TEXT,
                    view_count INTEGER DEFAULT 0,
                    last_search_at REAL DEFAULT 0,
                    search_count_hour INTEGER DEFAULT 0,
                    last_hour_reset REAL DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    last_active REAL DEFAULT (strftime('%s', 'now')),
                    is_archived INTEGER DEFAULT 0,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
    
    def _migrate_tables(self):
        """Добавляем новые колонки если их нет"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'last_active' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN last_active REAL DEFAULT 0")
                import time
                conn.execute("UPDATE users SET last_active = ?", (time.time(),))
                logger.info("Добавлена колонка last_active")
            
            if 'is_archived' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN is_archived INTEGER DEFAULT 0")
                logger.info("Добавлена колонка is_archived")
            
            if 'photo_id' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN photo_id TEXT")
                logger.info("Добавлена колонка photo_id")
            
            if 'media_type' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN media_type TEXT")
                logger.info("Добавлена колонка media_type")
            
            if 'looking_for' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN looking_for TEXT")
                logger.info("Добавлена колонка looking_for")

            if 'media_ids' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN media_ids TEXT")
                logger.info("Добавлена колонка media_ids")

            if 'is_fake' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN is_fake INTEGER DEFAULT 0")
                logger.info("Добавлена колонка is_fake")

            if 'name' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN name TEXT")
                logger.info("Добавлена колонка name")

            if 'filter_min_age' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN filter_min_age INTEGER")
                logger.info("Добавлена колонка filter_min_age")

            if 'filter_max_age' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN filter_max_age INTEGER")
                logger.info("Добавлена колонка filter_max_age")

            if 'is_girl' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN is_girl INTEGER DEFAULT 0")
                logger.info("Добавлена колонка is_girl")

            if 'services' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN services TEXT")
                logger.info("Добавлена колонка services")

            if 'prices' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN prices TEXT")
                logger.info("Добавлена колонка prices")

            if 'schedule' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN schedule TEXT")
                logger.info("Добавлена колонка schedule")

            if 'is_online' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN is_online INTEGER DEFAULT 0")
                logger.info("Добавлена колонка is_online")

            if 'phone' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                logger.info("Добавлена колонка phone")

            if 'breast' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN breast TEXT")
                logger.info("Добавлена колонка breast")

            if 'height' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN height INTEGER")
                logger.info("Добавлена колонка height")

            if 'weight' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN weight INTEGER")
                logger.info("Добавлена колонка weight")

            if 'clothing_size' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN clothing_size TEXT")
                logger.info("Добавлена колонка clothing_size")

            if 'shoe_size' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN shoe_size TEXT")
                logger.info("Добавлена колонка shoe_size")

            if 'intimate_grooming' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN intimate_grooming TEXT")
                logger.info("Добавлена колонка intimate_grooming")

            if 'min_age_restriction' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN min_age_restriction INTEGER DEFAULT 18")
                logger.info("Добавлена колонка min_age_restriction")

        with sqlite3.connect(self.db_path) as conn:
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocked_users (
                    user_id INTEGER,
                    blocked_user_id INTEGER,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (user_id, blocked_user_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skips (
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (from_user_id, to_user_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    stars_amount INTEGER,
                    telegram_charge_id TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    text TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tracking (
                    user_id INTEGER,
                    tracked_user_id INTEGER,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (user_id, tracked_user_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS girl_whitelist (
                    user_id INTEGER PRIMARY KEY,
                    added_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)

    def add_girl_whitelist(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO girl_whitelist (user_id) VALUES (?)", (user_id,))

    def is_girl_whitelisted(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT 1 FROM girl_whitelist WHERE user_id = ?", (user_id,)).fetchone()
            return row is not None

    def remove_girl_whitelist(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM girl_whitelist WHERE user_id = ?", (user_id,))

    def create_girl_user(self, user_id: int, username: str, name: str, age: int, city: str, bio: str, photo_id: str = None, media_type: str = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users
                (user_id, username, age, gender, city, bio, preferences, looking_for,
                 photo_id, media_type, is_fake, is_girl, view_count, last_search_at, search_count_hour,
                 last_hour_reset, is_banned, last_active, is_archived, created_at, name)
                VALUES (?, ?, ?, 'ж', ?, ?, 'м', '', ?, ?, 0, 1, 0, 0, 0, 0, 0,
                        strftime('%s', 'now'), 0, strftime('%s', 'now'), ?)
            """, (user_id, username, age, city, bio, photo_id, media_type, name))

    def delete_user(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def create_male_user(self, user_id: int, username: str = None):
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if existing:
                return
            conn.execute("""
                INSERT INTO users (user_id, username, age, gender, city, bio, preferences, looking_for, is_fake, last_active, created_at)
                VALUES (?, ?, 25, 'м', 'астрахань', '', 'ж', '', 0, strftime('%s', 'now'), strftime('%s', 'now'))
            """, (user_id, username))

    def update_user_filters(self, user_id: int, min_age: int = None, max_age: int = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE users SET filter_min_age = ?, filter_max_age = ? WHERE user_id = ?",
                (min_age, max_age, user_id)
            )

    def save_user(self, user_id: int, data: Dict):
        city = normalize_city(data['city'])
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (user_id, username, age, gender, city, bio, preferences, looking_for, photo_id, media_type, view_count, last_search_at, search_count_hour, last_hour_reset, is_banned, last_active, is_archived, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    (SELECT COALESCE(view_count, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(last_search_at, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(search_count_hour, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(last_hour_reset, 0) FROM users WHERE user_id = ?),
                    (SELECT COALESCE(is_banned, 0) FROM users WHERE user_id = ?),
                    COALESCE((SELECT last_active FROM users WHERE user_id = ?), strftime('%s', 'now')),
                    COALESCE((SELECT is_archived FROM users WHERE user_id = ?), 0),
                    COALESCE((SELECT created_at FROM users WHERE user_id = ?), strftime('%s', 'now'))
                )
            """, (user_id, data.get('username'), data['age'], data['gender'], city, data['bio'], data['preferences'], data.get('looking_for'), data.get('photo_id'), data.get('media_type'), user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))

    def get_user(self, user_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_field(self, user_id: int, field: str, value):
        allowed = {'age', 'gender', 'city', 'bio', 'preferences', 'looking_for', 'photo_id', 'media_type', 'media_ids', 'filter_min_age', 'filter_max_age', 'services', 'prices', 'schedule', 'is_online', 'name', 'phone', 'breast', 'height', 'weight', 'clothing_size', 'shoe_size', 'intimate_grooming', 'min_age_restriction'}
        if field not in allowed:
            return
        if field == 'city':
            value = normalize_city(value)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _build_search_query(self, user_id: int, city_condition: str, city_value: str, 
                             preferences: str, current_age: int, looking_for: str = None,
                             min_age: int = None, max_age: int = None, match_looking_for: bool = False):
        gender_filter = None
        if preferences == 'м':
            gender_filter = 'м'
        elif preferences == 'ж':
            gender_filter = 'ж'

        week_ago = time.time() - 604800

        query = f"""
            SELECT * FROM users 
            WHERE user_id != ? 
            AND city {city_condition} ? 
            AND (is_banned = 0 OR is_banned IS NULL)
            AND (is_archived = 0 OR is_archived IS NULL)
            AND user_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
            AND user_id NOT IN (
                SELECT blocked_user_id FROM blocked_users WHERE user_id = ?
            )
            AND user_id NOT IN (
                SELECT to_user_id FROM skips WHERE from_user_id = ? AND created_at > ?
            )
        """
        params = [user_id, city_value, user_id, user_id, user_id, week_ago]

        if match_looking_for and looking_for:
            query += " AND looking_for = ?"
            params.append(looking_for)

        if min_age is not None:
            query += " AND age >= ?"
            params.append(min_age)
        if max_age is not None:
            query += " AND age <= ?"
            params.append(max_age)
        if gender_filter:
            query += " AND gender = ?"
            params.append(gender_filter)

        query += " ORDER BY ABS(age - ?) ASC, RANDOM() LIMIT 1"
        params.append(current_age)
        return query, params

    def get_random_profile(self, user_id: int, city: str, preferences: str, min_age: int = None, max_age: int = None) -> Optional[Dict]:
        city = normalize_city(city)
        
        current_user = self.get_user(user_id)
        current_age = current_user['age'] if current_user else 25
        looking_for = current_user.get('looking_for', '') if current_user else ''
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            search_order = [
                ("=", city, True),
                ("=", city, False),
                ("!=", city, True),
                ("!=", city, False),
            ]

            for city_cond, city_val, match_lf in search_order:
                if match_lf and not looking_for:
                    continue
                q, p = self._build_search_query(
                    user_id, city_cond, city_val, preferences, current_age,
                    looking_for, min_age, max_age, match_lf
                )
                row = conn.execute(q, p).fetchone()
                if row:
                    return dict(row)
            
            return None

    def save_gift(self, from_id: int, to_id: int, stars_amount: int, telegram_charge_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO gifts (from_user_id, to_user_id, stars_amount, telegram_charge_id) VALUES (?, ?, ?, ?)",
                (from_id, to_id, stars_amount, telegram_charge_id)
            )

    def get_gifts_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as count FROM gifts").fetchone()['count']
            total_stars = conn.execute("SELECT COALESCE(SUM(stars_amount), 0) as total FROM gifts").fetchone()['total']
            return {'total_gifts': total, 'total_stars': total_stars}

    def add_skip(self, from_id: int, to_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO skips (from_user_id, to_user_id, created_at) VALUES (?, ?, ?)",
                (from_id, to_id, time.time())
            )

    def add_like(self, from_id: int, to_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO likes (from_user_id, to_user_id) VALUES (?, ?)", (from_id, to_id))
            cursor = conn.execute("SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?", (to_id, from_id))
            return cursor.fetchone() is not None

    def remove_like(self, from_id: int, to_id: int):
        """Remove a like (used when user skips someone who liked them)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM likes WHERE from_user_id = ? AND to_user_id = ?", (from_id, to_id))

    def create_match(self, user1_id: int, user2_id: int):
        min_id, max_id = min(user1_id, user2_id), max(user1_id, user2_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO matches (user1_id, user2_id) 
                VALUES (?, ?)
            """, (min_id, max_id))

    def has_match(self, user1_id: int, user2_id: int) -> bool:
        min_id, max_id = min(user1_id, user2_id), max(user1_id, user2_id)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM matches WHERE user1_id = ? AND user2_id = ?",
                (min_id, max_id)
            )
            return cursor.fetchone() is not None

    def delete_match(self, user1_id: int, user2_id: int):
        min_id, max_id = min(user1_id, user2_id), max(user1_id, user2_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM matches WHERE user1_id = ? AND user2_id = ?",
                (min_id, max_id)
            )

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

    def block_user(self, user_id: int, blocked_user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO blocked_users (user_id, blocked_user_id) VALUES (?, ?)",
                (user_id, blocked_user_id)
            )

    def unblock_user(self, user_id: int, blocked_user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM blocked_users WHERE user_id = ? AND blocked_user_id = ?",
                (user_id, blocked_user_id)
            )

    def is_blocked(self, user_id: int, other_user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM blocked_users 
                WHERE (user_id = ? AND blocked_user_id = ?)
                OR (user_id = ? AND blocked_user_id = ?)
            """, (user_id, other_user_id, other_user_id, user_id))
            return cursor.fetchone() is not None

    def get_blocked_users(self, user_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM blocked_users WHERE user_id = ?",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def ban_user(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))

    def unban_user(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))

    def is_banned(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user and user.get('is_banned', 0) == 1

    def get_all_active_users(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE is_banned = 0")
            return [dict(row) for row in cursor.fetchall()]

    def get_global_stats(self) -> Dict:
        now = time.time()
        day_ago = now - 86400
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
            fake_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_fake = 1").fetchone()['count']
            banned_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_banned = 1").fetchone()['count']
            archived_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_archived = 1").fetchone()['count']
            active_today = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE last_active > ?",
                (day_ago,)
            ).fetchone()['count']
            
            total_likes = conn.execute("SELECT COUNT(*) as count FROM likes").fetchone()['count']
            likes_today = conn.execute(
                "SELECT COUNT(*) as count FROM likes WHERE created_at > ?",
                (day_ago,)
            ).fetchone()['count']
            
            total_matches = conn.execute("SELECT COUNT(*) as count FROM matches").fetchone()['count']
            matches_today = conn.execute(
                "SELECT COUNT(*) as count FROM matches WHERE created_at > ?",
                (day_ago,)
            ).fetchone()['count']
            
            return {
                'total_users': total_users,
                'fake_users': fake_users,
                'banned_users': banned_users,
                'archived_users': archived_users,
                'active_today': active_today,
                'total_likes': total_likes,
                'likes_today': likes_today,
                'total_matches': total_matches,
                'matches_today': matches_today
            }
    
    def touch_random_fake_users(self) -> int:
        """Обновить last_active у случайной части fake-профилей"""
        import random
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            fakes = conn.execute(
                "SELECT user_id FROM users WHERE is_fake = 1 AND is_banned = 0 AND is_archived = 0"
            ).fetchall()
            if not fakes:
                return 0
            count = max(1, len(fakes) // 3)
            chosen = random.sample(fakes, min(count, len(fakes)))
            for row in chosen:
                offset = random.randint(-300, 300)
                conn.execute(
                    "UPDATE users SET last_active = ? WHERE user_id = ?",
                    (now + offset, row['user_id'])
                )
            return len(chosen)

    def update_last_active(self, user_id: int):
        """Обновить время последней активности пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?",
                (time.time(), user_id)
            )
    
    def unarchive_user(self, user_id: int):
        """Разархивировать пользователя и обновить активность"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE users SET is_archived = 0, last_active = ? WHERE user_id = ?",
                (time.time(), user_id)
            )
            logger.info(f"Пользователь {user_id} разархивирован")
    
    def archive_inactive_users(self, days: int = 7) -> int:
        """Архивировать неактивных пользователей (старше N дней)"""
        threshold = time.time() - (days * 86400)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE users 
                SET is_archived = 1 
                WHERE (last_active < ? OR last_active IS NULL)
                AND (is_archived = 0 OR is_archived IS NULL)
            """, (threshold,))
            archived_count = cursor.rowcount
            logger.info(f"Архивировано {archived_count} неактивных пользователей")
            return archived_count
    
    def add_tracking(self, user_id: int, tracked_user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO tracking (user_id, tracked_user_id) VALUES (?, ?)",
                (user_id, tracked_user_id)
            )

    def remove_tracking(self, user_id: int, tracked_user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM tracking WHERE user_id = ? AND tracked_user_id = ?",
                (user_id, tracked_user_id)
            )

    def is_tracking(self, user_id: int, tracked_user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM tracking WHERE user_id = ? AND tracked_user_id = ?",
                (user_id, tracked_user_id)
            )
            return cursor.fetchone() is not None

    def get_tracked_users(self, user_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT t.tracked_user_id, t.created_at, u.age, u.city, u.bio, u.name, u.photo_id, u.media_type, u.media_ids, u.is_online, u.last_active
                FROM tracking t
                JOIN users u ON t.tracked_user_id = u.user_id
                WHERE t.user_id = ?
                ORDER BY t.created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_followers(self, user_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT t.user_id as follower_id, t.created_at, u.age, u.city, u.username
                FROM tracking t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.tracked_user_id = ?
                ORDER BY t.created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_followers_count(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM tracking WHERE tracked_user_id = ?", (user_id,)
            ).fetchone()[0]

    def add_comment(self, from_user_id: int, to_user_id: int, text: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO comments (from_user_id, to_user_id, text) VALUES (?, ?, ?)",
                (from_user_id, to_user_id, text)
            )

    def get_comments(self, user_id: int, limit: int = 10) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT c.id, c.from_user_id, c.text, c.created_at, u.username, u.age
                FROM comments c
                LEFT JOIN users u ON c.from_user_id = u.user_id
                WHERE c.to_user_id = ?
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_comments_count(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM comments WHERE to_user_id = ?", (user_id,)
            ).fetchone()[0]

    def get_girl_stats(self, user_id: int) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = self.get_user(user_id)
            views = user['view_count'] if user else 0

            likes_received = conn.execute(
                "SELECT COUNT(*) as count FROM likes WHERE to_user_id = ?", (user_id,)
            ).fetchone()['count']

            followers = self.get_followers_count(user_id)
            comments = self.get_comments_count(user_id)

            matches = conn.execute("""
                SELECT COUNT(*) as count FROM matches
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id)).fetchone()['count']

            chats_active = matches

            return {
                'views': views,
                'likes_received': likes_received,
                'followers': followers,
                'comments': comments,
                'matches': matches,
                'chats_active': chats_active
            }

    def get_archive_stats(self) -> Dict:
        """Получить статистику по архивации"""
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            total = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
            archived = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_archived = 1").fetchone()['count']
            active = conn.execute("SELECT COUNT(*) as count FROM users WHERE (is_archived = 0 OR is_archived IS NULL)").fetchone()['count']
            online_5min = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE last_active > ?",
                (now - 300,)
            ).fetchone()['count']
            online_hour = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE last_active > ?",
                (now - 3600,)
            ).fetchone()['count']
            online_day = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE last_active > ?",
                (now - 86400,)
            ).fetchone()['count']
            
            return {
                'total': total,
                'archived': archived,
                'active': active,
                'online_5min': online_5min,
                'online_hour': online_hour,
                'online_day': online_day
            }
