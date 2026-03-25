import sqlite3
import os
import platform
import configparser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hsql.db')

# Cấu hình môi trường mặc định
ENVIRONMENT = "local"
DB_HOST = "36.50.135.128" # Default to public IP for sync
DB_PORT = 3306
DB_USER = "account_user"
DB_PASSWORD = "account_password"
DB_NAME = "account_db"

def set_environment(env):
    global ENVIRONMENT, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    ENVIRONMENT = env
    
    if ENVIRONMENT == "production":
        # Production strictly uses 10.201.11.115 for internal storage/sync
        DB_HOST = "10.201.11.115"
        DB_PORT = 3306
        DB_USER = "account_user"
        DB_PASSWORD = "account_password"
        DB_NAME = "account_db"
        print(f"--- DEBUG: Starting production config load ---")
        
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'config.ini'),
            os.path.join(os.getcwd(), 'config.ini'),
            os.path.abspath('config.ini')
        ]
        
        config_file = None
        for p in possible_paths:
            abs_p = os.path.abspath(p)
            if os.path.exists(abs_p):
                config_file = abs_p
                break
                
        if config_file:
            try:
                config = configparser.ConfigParser()
                config.read(config_file, encoding="utf-8")
                if 'database' in config:
                    db_config = config['database']
                    DB_HOST = db_config.get("host", "10.201.11.115")
                    DB_PORT = int(db_config.get("port", "3306"))
                    DB_USER = db_config.get("username", "account_user")
                    DB_PASSWORD = db_config.get("password", "account_password")
                    DB_NAME = db_config.get("database", "account_db")
                    print(f"--- SUCCESS: Loaded production config ---")
            except Exception as e:
                print(f"Error parsing config.ini: {e}")
    else:
        # Local strictly uses 36.50.135.128 and account_db
        DB_HOST = "36.50.135.128"
        DB_PORT = 3306
        DB_USER = "account_user"
        DB_PASSWORD = "account_password"
        DB_NAME = "account_db"
        print(f"--- SUCCESS: Running in Local mode with remote MySQL 36.50.135.128 ---")

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

def get_management_accounts(conn_id=None):
    """
    Fetches the list of accounts from the internal management database
    based on the current environment (Local or Production).
    """
    try:
        # ALWAYS use the internal management MySQL for sync
        conn = get_mysql_connection()
            
        if not conn: 
            return []
        
        try:
            with conn.cursor() as cursor:
                # Check if projects table exists
                cursor.execute("SHOW TABLES LIKE 'projects'")
                has_projects = cursor.fetchone()
                
                if has_projects:
                    query = """
                        SELECT a.id, a.name, a.url, a.platform_icon, a.login_details, p.name as project_name
                        FROM accounts a
                        LEFT JOIN projects p ON a.project_id = p.id
                        ORDER BY p.name, a.name
                    """
                else:
                    query = """
                        SELECT id, name, url, platform_icon, login_details, 'No Project' as project_name
                        FROM accounts
                        ORDER BY name
                    """
                
                cursor.execute(query)
                results = cursor.fetchall()
                return results
        finally:
            conn.close()
    except Exception as e:
        print(f"Error fetching accounts from management database: {e}")
        return []

def init_db():
    # Luôn khởi tạo DB trên MySQL
    import pymysql
    try:
        temp_conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
        with temp_conn.cursor() as temp_cursor:
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        temp_conn.commit()
        temp_conn.close()
    except Exception as e:
        print(f"Error creating/checking database: {e}")
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
                    database_name VARCHAR(255),
                    is_default INT DEFAULT 0,
                    use_win_auth INT DEFAULT 0
                )
            ''')
            # Migration to add is_default if not exists
            try:
                cursor.execute("ALTER TABLE connections ADD COLUMN is_default INT DEFAULT 0")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE connections ADD COLUMN use_win_auth INT DEFAULT 0")
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()

def get_connections():
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name, is_default, use_win_auth FROM connections")
            return cursor.fetchall()
    finally:
        conn.close()

def get_connection(conn_id):
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, db_type, host, port, username, password, database_name, is_default, use_win_auth FROM connections WHERE id = %s", (conn_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def save_to_management_accounts(data):
    """
    Saves a manual connection's details to the centralized accounts table.
    """
    import json
    import pymysql
    
    # Construct login_details JSON
    details = {
        "username": data.get('username', ''),
        "password": data.get('password', ''),
        "port": data.get('port', 3306),
        "database": data.get('database_name', ''),
        "notes": "Auto-saved from HSql"
    }
    login_details_json = json.dumps(details)
    
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            # We use name as the account name, host as URL
            # platform_icon is 'bx bxs-data' for Database type
            query = """
                INSERT INTO accounts (name, url, platform_icon, login_details, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            cursor.execute(query, (
                data['name'], 
                data['host'], 
                'bx bxs-data', 
                login_details_json
            ))
        conn.commit()
    except Exception as e:
        print(f"Error auto-saving to management accounts: {e}")
    finally:
        conn.close()

def save_connection(data):
    # Auto-save to management accounts if NOT synced and NOT an update
    # In this app, data usually comes without 'id' if it's new
    if not data.get('is_synced', False) and 'id' not in data:
        save_to_management_accounts(data)

    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            if 'id' in data:
                query = "UPDATE connections SET name=%s, db_type=%s, host=%s, port=%s, username=%s, password=%s, database_name=%s, is_default=%s, use_win_auth=%s WHERE id=%s"
                cursor.execute(query, (
                    data['name'], data['db_type'], data['host'], data['port'], 
                    data['username'], data['password'], data['database_name'], 
                    data.get('is_default', 0), data.get('use_win_auth', 0), data['id']
                ))
            else:
                query = "INSERT INTO connections (name, db_type, host, port, username, password, database_name, is_default, use_win_auth) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (
                    data['name'], data['db_type'], data['host'], data['port'], 
                    data['username'], data['password'], data['database_name'], 
                    data.get('is_default', 0), data.get('use_win_auth', 0)
                ))
        conn.commit()
    finally:
        conn.close()

def set_default_database(conn_id, db_name):
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            # First, unset all defaults globally
            cursor.execute("UPDATE connections SET is_default = 0, database_name = NULL")
            # Then set this connection and this db as the sole default
            cursor.execute("UPDATE connections SET is_default = 1, database_name = %s WHERE id = %s", (db_name, conn_id))
        conn.commit()
    finally:
        conn.close()

def get_default_database(conn_id):
    conn_data = get_connection(conn_id)
    return conn_data[7] if conn_data else None

def set_connection_as_default(conn_id):
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            # First, unset all globally (including database_names)
            cursor.execute("UPDATE connections SET is_default = 0, database_name = NULL")
            # Then set selected
            cursor.execute("UPDATE connections SET is_default = 1 WHERE id = %s", (conn_id,))
        conn.commit()
    finally:
        conn.close()
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
        use_win_auth = conn_data[10] if len(conn_data) > 10 else 0
        
        if use_win_auth:
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{p};DATABASE={db_name};Trusted_Connection=yes"
        else:
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
