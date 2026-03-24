import sqlite3
import os
import platform
import configparser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hsql.db')

# Cấu hình môi trường mặc định
ENVIRONMENT = "local"
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "portfolio_db"

def set_environment(env):
    global ENVIRONMENT, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    ENVIRONMENT = env
    
    # Đọc config.ini nếu chạy trên production (Linux)
    if ENVIRONMENT == "production":
        print(f"--- DEBUG: Starting production config load ---")
        print(f"Current Dir (os.getcwd()): {os.getcwd()}")
        print(f"Script Dir (__file__): {os.path.dirname(__file__)}")
        
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'config.ini'),
            os.path.join(os.getcwd(), 'config.ini'),
            os.path.abspath('config.ini')
        ]
        
        config_file = None
        for p in possible_paths:
            abs_p = os.path.abspath(p)
            exists = os.path.exists(abs_p)
            print(f"Checking path: {abs_p} -> Exists: {exists}")
            if exists:
                config_file = abs_p
                break
                
        if config_file:
            try:
                config = configparser.ConfigParser()
                config.read(config_file, encoding="utf-8")
                print(f"Successfully read config file. Sections: {config.sections()}")
                
                if 'database' in config:
                    db_config = config['database']
                    DB_HOST = db_config.get("host", "10.201.11.115")
                    DB_PORT = int(db_config.get("port", "3306"))
                    DB_USER = db_config.get("username", "root")
                    DB_PASSWORD = db_config.get("password", "")
                    DB_NAME = db_config.get("database", "portfolio_db")
                    print(f"--- SUCCESS: Loaded config ---")
                    print(f"Host: {DB_HOST}, User: {DB_USER}, DB: {DB_NAME}")
                else:
                    print("Error: Section [database] NOT FOUND in config.ini")
            except Exception as e:
                print(f"Error parsing config.ini: {e}")
        else:
            print("--- CRITICAL: config.ini NOT FOUND in any expected location ---")
            # Fallback values
            DB_HOST = "10.201.11.115"
            DB_PORT = 3306
            DB_USER = "portfolio_user" # Better defaults just in case
            DB_PASSWORD = "portfolio_password"

def get_mysql_connection():
    import pymysql
    # Sử dụng con trỏ mặc định (tuple) để tương thích với output của sqlite3
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=10
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
            temp_conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
            with temp_conn.cursor() as temp_cursor:
                temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            temp_conn.commit()
            temp_conn.close()
        except Exception as e:
            print(f"Error creating production database: {e}")
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

def set_default_database(conn_id, db_name):
    if ENVIRONMENT == "local":
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE connections SET database_name = ? WHERE id = ?", (db_name, conn_id))
            conn.commit()
    else:
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE connections SET database_name = %s WHERE id = %s", (db_name, conn_id))
            conn.commit()
        finally:
            conn.close()

def get_default_database(conn_id):
    conn_data = get_connection(conn_id)
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys
    import os
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

def init_jvm():
    """
    Initializes the JVM early to prevent Segmentation Faults when using JPype with PyQt6.
    """
    import os
    try:
        import jpype
        if not jpype.isJVMStarted():
            jar_path = get_resource_path(os.path.join("drivers", "jt400.jar"))
            if os.path.exists(jar_path):
                # Start JVM with jar_path included
                jpype.startJVM(jpype.getDefaultJVMPath(), classpath=[jar_path], convertStrings=True)
                print("--- JVM Initialized successfully ---")
            else:
                # Still start JVM even if jar missing (can be added to classpath later or handled)
                jpype.startJVM(jpype.getDefaultJVMPath(), convertStrings=True)
                print("--- JVM Initialized (without it400.jar) ---")
    except Exception as e:
        print(f"--- Warning: Failed to pre-init JVM: {e} ---")

def get_db_connection(conn_id, database_name=None):
    """
    Returns a unified connection object based on the connection type.
    """
    conn_data = get_connection(conn_id)
    if not conn_data:
        return None
        
    db_type = conn_data[2]
    host = conn_data[3]
    port = conn_data[4]
    user = conn_data[5]
    password = conn_data[6]
    db_name = database_name or conn_data[7]
    
    if "MySQL" in db_type:
        import pymysql
        return pymysql.connect(
            host=host, port=int(port or 3306),
            user=user, password=password,
            database=db_name,
            connect_timeout=10
        )
    elif "Oracle" in db_type:
        # Standard Oracle ports: 1521
        dsn = f"{host}:{port}/{db_name}" if db_name else f"{host}:{port}"
        try:
            import oracledb
            return oracledb.connect(user=user, password=password, dsn=dsn)
        except ImportError:
            import cx_Oracle
            return cx_Oracle.connect(user=user, password=password, dsn=dsn)
    elif "SQL Server" in db_type:
        import pyodbc
        # Port for SQL Server is usually 1433
        p = port if port else 1433
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{p};DATABASE={db_name};UID={user};PWD={password}"
        return pyodbc.connect(conn_str)
    elif "DB2" in db_type:
        import jaydebeapi
        import os
        import jpype
        jar_path = get_resource_path(os.path.join("drivers", "jt400.jar"))
        
        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"Missing JDBC Driver: {jar_path}")
            
        url = f"jdbc:as400://{host}"
        # If a port is specified, it's usually added to the URL for JT400 though default is 446
        # URL format: jdbc:as400://systemname[:port][/defaultSchema][;property=value...]
        if port:
            url += f":{port}"
            
        driver_class = "com.ibm.as400.access.AS400JDBCDriver"
        
        # Ensure JVM is started
        if not jpype.isJVMStarted():
            return jaydebeapi.connect(driver_class, url, [user, password], jar_path)
        else:
            # Reusing already started JVM
            return jaydebeapi.connect(driver_class, url, [user, password])
        
    return None
