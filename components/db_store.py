import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hsql.db')

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                db_type TEXT,
                host TEXT,
                port INTEGER,
                username TEXT,
                password TEXT,
                database_name TEXT
            )
        ''')
        conn.commit()

def get_connections():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name FROM connections")
        return cursor.fetchall()

def get_connection(conn_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name FROM connections WHERE id = ?", (conn_id,))
        return cursor.fetchone()

def update_connection(conn_id, data):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE connections 
            SET name=?, db_type=?, host=?, port=?, username=?, password=?, database_name=?
            WHERE id=?
        ''', (data['name'], data['db_type'], data['host'], data['port'], data['username'], data['password'], data['database_name'], conn_id))
        conn.commit()

def save_connection(data):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO connections (name, db_type, host, port, username, password, database_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['db_type'], data['host'], data['port'], data['username'], data['password'], data['database_name']))
        conn.commit()
