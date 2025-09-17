import sqlite3
import json
from datetime import datetime
from config import DATABASE_URL

def init_db():
    """Создание базы данных и таблиц"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица ответов на вопросы
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_num INTEGER,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Таблица результатов тестов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        result_type TEXT,
        answers_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных инициализирована")

def save_user(user_id, username=None, first_name=None, last_name=None):
    """Сохранение информации о пользователе"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()

def save_user_answer(user_id, question_num, answer):
    """Сохранение ответа пользователя на вопрос"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Удаляем предыдущий ответ на этот вопрос (если есть)
    cursor.execute('''
    DELETE FROM user_answers 
    WHERE user_id = ? AND question_num = ?
    ''', (user_id, question_num))
    
    # Сохраняем новый ответ
    cursor.execute('''
    INSERT INTO user_answers (user_id, question_num, answer)
    VALUES (?, ?, ?)
    ''', (user_id, question_num, answer))
    
    conn.commit()
    conn.close()

def save_user_result(user_id, result_type, answers_dict):
    """Сохранение результата теста"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    answers_json = json.dumps(answers_dict)
    
    cursor.execute('''
    INSERT INTO test_results (user_id, result_type, answers_json)
    VALUES (?, ?, ?)
    ''', (user_id, result_type, answers_json))
    
    conn.commit()
    conn.close()

def get_user_results(user_id):
    """Получение результатов пользователя"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT result_type, answers_json, created_at
    FROM test_results
    WHERE user_id = ?
    ORDER BY created_at DESC
    ''', (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_statistics():
    """Получение общей статистики"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Общее количество прохождений
    cursor.execute('SELECT COUNT(*) FROM test_results')
    total_tests = cursor.fetchone()[0]
    
    # Статистика по типам
    cursor.execute('''
    SELECT result_type, COUNT(*) as count
    FROM test_results
    GROUP BY result_type
    ORDER BY count DESC
    ''')
    
    type_stats = cursor.fetchall()
    conn.close()
    
    return {
        'total_tests': total_tests,
        'type_distribution': dict(type_stats)
    }

def get_daily_stats():
    """Получение статистики за сегодня"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT COUNT(*) 
    FROM test_results 
    WHERE DATE(created_at) = DATE('now')
    ''')
    
    today_tests = cursor.fetchone()[0]
    conn.close()
    
    return today_tests
