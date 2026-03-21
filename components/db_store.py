import sqlite3
import os
import platform
import configparser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hsql.db')

# Cấu hình môi trường mặc định
ENVIRONMENT = "local"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "portfolio_db"

def set_environment(env):
    global ENVIRONMENT, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
    ENVIRONMENT = env
    
    # Đọc config.ini nếu chạy trên production (Linux)
    if ENVIRONMENT == "production":
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file, encoding="utf-8")
            if 'database' in config:
                db_config = config['database']
                
                DB_HOST = db_config.get("host", "10.201.11.115")
                DB_USER = db_config.get("username", "root")
                DB_PASSWORD = db_config.get("password", "")
                DB_NAME = db_config.get("database", "portfolio_db")


def get_mysql_connection():
    import pymysql
    # Sử dụng con trỏ mặc định (tuple) để tương thích với output của sqlite3
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def init_db():
    if ENVIRONMENT == "local":
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
    else:
        # Nếu chưa có DB, tạo mới cho Production
        import pymysql
        try:
            temp_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
            with temp_conn.cursor() as temp_cursor:
                temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            temp_conn.commit()
            temp_conn.close()
        except:
            pass

        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS connections (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255),
                        db_type VARCHAR(50),
                        host VARCHAR(255),
                        port INT,
                        username VARCHAR(255),
                        password VARCHAR(255),
                        database_name VARCHAR(255)
                    )
                ''')
            conn.commit()
        finally:
            conn.close()

def get_connections():
    if ENVIRONMENT == "local":
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name FROM connections")
            return cursor.fetchall()
    else:
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name FROM connections")
                return cursor.fetchall()
        finally:
            conn.close()

def get_connection(conn_id):
    if ENVIRONMENT == "local":
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name FROM connections WHERE id = ?", (conn_id,))
            return cursor.fetchone()
    else:
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name FROM connections WHERE id = %s", (conn_id,))
                return cursor.fetchone()
        finally:
            conn.close()

def update_connection(conn_id, data):
    if ENVIRONMENT == "local":
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE connections 
                SET name=?, db_type=?, host=?, port=?, username=?, password=?, database_name=?
                WHERE id=?
            ''', (data['name'], data['db_type'], data['host'], data['port'], data['username'], data['password'], data['database_name'], conn_id))
            conn.commit()
    else:
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE connections 
                    SET name=%s, db_type=%s, host=%s, port=%s, username=%s, password=%s, database_name=%s
                    WHERE id=%s
                ''', (data['name'], data['db_type'], data['host'], data['port'], data['username'], data['password'], data['database_name'], conn_id))
            conn.commit()
        finally:
            conn.close()

def save_connection(data):
    if ENVIRONMENT == "local":
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO connections (name, db_type, host, port, username, password, database_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data['name'], data['db_type'], data['host'], data['port'], data['username'], data['password'], data['database_name']))
            conn.commit()
    else:
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO connections (name, db_type, host, port, username, password, database_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (data['name'], data['db_type'], data['host'], data['port'], data['username'], data['password'], data['database_name']))
            conn.commit()
        finally:
            conn.close()
