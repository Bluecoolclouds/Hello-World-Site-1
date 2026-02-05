import csv
import sqlite3
import time
import sys
import os

DB_PATH = "bot.db"

def import_users(csv_path: str, gender: str = "ж"):
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден!")
        return

    conn = sqlite3.connect(DB_PATH)
    
    cursor = conn.execute("SELECT MAX(user_id) FROM users")
    max_id = cursor.fetchone()[0] or 0
    fake_id_start = max(max_id + 1, 9000000000)

    imported = 0
    skipped = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        print(f"Колонки в файле: {reader.fieldnames}")
        
        for row in reader:
            try:
                age = int(row.get('age', '0').strip())
                city = row.get('city', '').strip().lower()
                bio = row.get('bio', 'Не указано').strip()
                media_id = row.get('media_id', '').strip()
                media_type = row.get('media_type', '').strip().lower()
                
                if not city or age < 16 or age > 99:
                    print(f"Пропуск: age={age}, city={city}")
                    skipped += 1
                    continue
                
                if not bio or bio == '-':
                    bio = "Не указано"
                
                if media_type not in ('photo', 'video', 'video_note'):
                    media_type = ''
                
                preferences = "м" if gender == "ж" else "ж"
                
                user_id = fake_id_start + imported
                now = time.time()
                
                conn.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, age, gender, city, bio, preferences, looking_for,
                     photo_id, media_type, view_count, last_search_at, search_count_hour,
                     last_hour_reset, is_banned, last_active, is_archived, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, ?, 0, ?)
                """, (user_id, None, age, gender, city, bio, preferences, '',
                      media_id if media_id else None,
                      media_type if media_type else None,
                      now, now))
                
                imported += 1
                
            except Exception as e:
                print(f"Ошибка в строке: {row} -> {e}")
                skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nГотово!")
    print(f"Импортировано: {imported}")
    print(f"Пропущено: {skipped}")
    if imported > 0:
        print(f"ID диапазон: {fake_id_start} - {fake_id_start + imported - 1}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 bot/import_users.py data.csv")
        print("")
        print("CSV формат (с заголовками):")
        print("age,city,bio,media_id,media_type")
        print("22,москва,Люблю путешествия,AgACAgIAAxk...,photo")
        print("25,астрахань,Привет!,BAACAgIAAxk...,video")
        print("19,казань,-,,")
        print("")
        print("media_id  — file_id из Telegram (фото или видео)")
        print("media_type — photo / video / video_note (пусто = без медиа)")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    gender = sys.argv[2] if len(sys.argv) > 2 else "ж"
    
    print(f"Импорт из: {csv_path}")
    print(f"Пол: {'Девушка' if gender == 'ж' else 'Парень'}")
    print()
    
    import_users(csv_path, gender)
