from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, QTabWidget, QWidget, QCheckBox)
from PyQt6.QtCore import Qt
import json
from components.db_store import get_management_accounts

class ConnectionDialog(QDialog):
    def __init__(self, parent=None, connection_data=None, active_conn_id=None):
        super().__init__(parent)
        self.connection_id = None
        self.active_conn_id = active_conn_id
        self.setWindowTitle("Add Connection" if not connection_data else "Connection Properties")
        self.resize(700, 550)
        
        # Thiết kế Dark Theme Darcula cho Dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #a9b7c6;
            }
            QLabel { color: #a9b7c6; font-size: 13px; }
            QLineEdit, QComboBox {
                background-color: #1e1e1e;
                color: #a9b7c6;
                border: 1px solid #3c3f41;
                padding: 6px;
                border-radius: 3px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #a9b7c6;
                margin-top: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #a9b7c6;
                border: 1px solid #3c3f41;
                selection-background-color: #2f65ca;
                selection-color: white;
                outline: 0;
            }
            QComboBox QAbstractItemView::item {
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #589df6;
            }
            QPushButton {
                background-color: #3c3f41;
                color: #a9b7c6;
                border: 1px solid #555555;
                padding: 6px 18px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5052;
            }
            QPushButton#primary {
                background-color: #365880;
                color: white;
                border: 1px solid #4a88c7;
            }
            QPushButton#primary:hover {
                background-color: #4a88c7;
            }
            QPushButton#test_btn {
                color: #589df6;
                background-color: transparent;
                border: none;
                font-weight: normal;
                padding: 0px;
            }
            QPushButton#test_btn:hover {
                text-decoration: underline;
            }
            QTabWidget::pane { border: none; border-top: 1px solid #3c3f41; }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #a9b7c6;
                padding: 6px 15px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                color: #ffffff;
                border-bottom: 2px solid #589df6;
            }
            QTabBar::tab:hover {
                background-color: #3c3f41;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Top section (Type, Name, Comment)
        top_layout = QGridLayout()
        top_layout.setContentsMargins(0, 0, 0, 10)
        top_layout.setHorizontalSpacing(15)
        top_layout.setVerticalSpacing(10)
        
        top_layout.addWidget(QLabel("Database Type:"), 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["⛁ Oracle", "⛁ MySQL", "⛁ Microsoft SQL Server", "⛁ DB2 iSeries"])
        self.type_combo.currentTextChanged.connect(self.on_db_type_changed)
        top_layout.addWidget(self.type_combo, 0, 1)
        
        # Add Account Sync Dropdown
        top_layout.addWidget(QLabel("Sync Account:"), 1, 0)
        self.sync_combo = QComboBox()
        self.sync_combo.addItem("--- Select From Management ---")
        self.load_management_accounts()
        self.sync_combo.currentIndexChanged.connect(self.on_sync_account_changed)
        top_layout.addWidget(self.sync_combo, 1, 1)

        top_layout.addWidget(QLabel("Name:"), 2, 0)
        self.name_edit = QLineEdit("")
        top_layout.addWidget(self.name_edit, 2, 1)
        
        top_layout.addWidget(QLabel("Comment:"), 3, 0)
        comment_edit = QLineEdit()
        top_layout.addWidget(comment_edit, 3, 1)
        
        main_layout.addLayout(top_layout)
        
        # 2. Tabs section
        tabs = QTabWidget()
        gen_tab = QWidget()
        gen_layout = QGridLayout(gen_tab)
        gen_layout.setContentsMargins(10, 25, 10, 10)
        gen_layout.setHorizontalSpacing(15)
        gen_layout.setVerticalSpacing(20)
        
        # Host & Port
        host_port_layout = QHBoxLayout()
        host_port_layout.setSpacing(10)
        self.host_edit = QLineEdit("")
        self.port_edit = QLineEdit("3306") 
        self.port_edit.setFixedWidth(80)
        
        self.host_edit.textChanged.connect(self.update_url)
        self.port_edit.textChanged.connect(self.update_url)
        
        host_port_layout.addWidget(self.host_edit)
        host_port_layout.addWidget(QLabel("Port:"))
        host_port_layout.addWidget(self.port_edit)
        
        gen_layout.addWidget(QLabel("Host:"), 0, 0)
        gen_layout.addLayout(host_port_layout, 0, 1)
        
        # Authentication
        auth_layout = QHBoxLayout()
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["User & Password", "No Auth"])
        auth_layout.addWidget(self.auth_combo)
        
        # Windows Auth Checkbox (Only for SQL Server)
        self.win_auth_checkbox = QCheckBox("Use Windows Authentication")
        self.win_auth_checkbox.setStyleSheet("color: #589df6; margin-left: 10px;")
        self.win_auth_checkbox.setVisible(False)
        self.win_auth_checkbox.stateChanged.connect(self.on_win_auth_changed)
        auth_layout.addWidget(self.win_auth_checkbox)
        
        gen_layout.addLayout(auth_layout, 1, 1)
        
        # User
        self.user_label = QLabel("User:")
        gen_layout.addWidget(self.user_label, 2, 0)
        self.user_edit = QLineEdit("")
        gen_layout.addWidget(self.user_edit, 2, 1)
        
        # Password & Save
        pass_layout = QHBoxLayout()
        pass_layout.setSpacing(10)
        self.pass_edit = QLineEdit("")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("<hidden>")
        pass_layout.addWidget(self.pass_edit)
        
        pass_layout.addWidget(QLabel("Save:"))
        save_combo = QComboBox()
        save_combo.addItems(["Forever", "Until restart", "Never"])
        pass_layout.addWidget(save_combo)
        
        self.pass_label = QLabel("Password:")
        gen_layout.addWidget(self.pass_label, 3, 0)
        gen_layout.addLayout(pass_layout, 3, 1)
        
        # Store layout for hiding
        self.pass_container = pass_layout
        
        # Database
        gen_layout.addWidget(QLabel("Database:"), 4, 0)
        self.database_edit = QLineEdit("")
        gen_layout.addWidget(self.database_edit, 4, 1)
        
        # URL
        gen_layout.addWidget(QLabel("URL:"), 5, 0)
        url_vbox = QVBoxLayout()
        self.url_edit = QLineEdit("")
        # override hint label
        override_label = QLabel("Overrides settings above")
        override_label.setStyleSheet("color: #7a7e85; font-size: 11px;")
        
        url_vbox.addWidget(self.url_edit)
        url_vbox.addWidget(override_label)
        gen_layout.addLayout(url_vbox, 5, 1)
        
        # Push everything up
        gen_layout.setRowStretch(6, 1)
        
        tabs.addTab(gen_tab, "General")
        tabs.addTab(QWidget(), "Options")
        tabs.addTab(QWidget(), "SSH/SSL")
        tabs.addTab(QWidget(), "Schemas")
        tabs.addTab(QWidget(), "Advanced")
        
        main_layout.addWidget(tabs)
        
        # 3. Bottom section
        bottom_layout = QHBoxLayout()
        
        # Load existing data if provided
        if connection_data:
            self.connection_id = connection_data[0]
            self.name_edit.setText(connection_data[1])
            self.type_combo.setCurrentText(f"⛁ {connection_data[2]}")
            self.host_edit.setText(connection_data[3])
            self.port_edit.setText(str(connection_data[4]))
            self.user_edit.setText(connection_data[5])
            self.pass_edit.setText(connection_data[6])
            self.database_edit.setText(str(connection_data[7] or ""))
            self.is_default_val = connection_data[8] if len(connection_data) > 8 else 0
            
            # Load use_win_auth
            use_win_auth = connection_data[9] if len(connection_data) > 9 else 0
            self.win_auth_checkbox.setChecked(bool(use_win_auth))
            if use_win_auth:
                self.on_win_auth_changed(2) # Force disable fields
        else:
            self.type_combo.setCurrentText("⛁ MySQL")
            self.is_default_val = 0
            
        self.update_url()

        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("test_btn")
        test_btn.clicked.connect(self.test_connection)
        
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary")
        ok_btn.setDefault(True) # Make it blue if supported by OS/style natively, or just ID
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        apply_btn = QPushButton("Apply")
        
        bottom_layout.addWidget(test_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(ok_btn)
        bottom_layout.addWidget(cancel_btn)
        bottom_layout.addWidget(apply_btn)
        
        main_layout.addLayout(bottom_layout)

    def test_connection(self):
        from PyQt6.QtWidgets import QMessageBox
        from components.db_store import save_connection, get_connection
        import os
        
        # To test, we temporarily need these settings in the DB or a way to pass them
        # Simple way: Create a dummy data dict and use a mock-like approach or just direct connect
        db_type = self.type_combo.currentText().replace("⛁ ", "")
        host = self.host_edit.text() or 'localhost'
        port = self.port_edit.text()
        user = self.user_edit.text()
        password = self.pass_edit.text()
        db_name = self.database_edit.text()
        
        # Build a temporary connection check
        try:
            # We use a trick: bypass the stored ID and use the logic from get_db_connection
            # but we'll manually import the drivers here for the TEST button feedback
            if "MySQL" in db_type:
                import pymysql
                conn = pymysql.connect(
                    host=host, port=int(port or 3306),
                    user=user, password=password,
                    database=db_name if db_name else None,
                    connect_timeout=5
                )
            elif "Oracle" in db_type:
                dsn = f"{host}:{port}/{db_name}" if db_name else f"{host}:{port}"
                try:
                    import oracledb
                    conn = oracledb.connect(user=user, password=password, dsn=dsn)
                except ImportError:
                    import cx_Oracle
                    conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
            elif "SQL Server" in db_type:
                import pyodbc
                p = port if port else 1433
                
                if self.win_auth_checkbox.isChecked():
                    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{p};DATABASE={db_name};Trusted_Connection=yes"
                else:
                    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{p};DATABASE={db_name};UID={user};PWD={password}"
                conn = pyodbc.connect(conn_str, timeout=5)
            elif "DB2" in db_type:
                import jaydebeapi
                import os
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                jar_path = os.path.join(project_root, "drivers", "jt400.jar")
                
                if not os.path.exists(jar_path):
                    QMessageBox.critical(self, "Thiếu Driver", f"Không tìm thấy file {jar_path}. Vui lòng copy vào thư mục drivers/.")
                    return
                    
                url = f"jdbc:as400://{host}"
                if port: url += f":{port}"
                driver_class = "com.ibm.as400.access.AS400JDBCDriver"
                conn = jaydebeapi.connect(driver_class, url, [user, password], jar_path)
            else:
                QMessageBox.warning(self, "Not Supported", f"Loại DB '{db_type}' chưa được hỗ trợ test.")
                return

            # Connection success check
            cursor = conn.cursor()
            # Generic version check if possible
            version = "Unknown"
            try:
                if "MySQL" in db_type:
                    cursor.execute("SELECT VERSION()")
                elif "Oracle" in db_type:
                    cursor.execute("SELECT version FROM v$instance")
                elif "SQL Server" in db_type:
                    cursor.execute("SELECT @@VERSION")
                elif "DB2" in db_type:
                    cursor.execute("SELECT CHARACTER_SUBSET FROM QSYS2.SYSCFG") # Simple iSeries check
                
                res = cursor.fetchone()
                if res: version = str(res[0])
            except:
                version = "Connected (Version check failed)"
                
            conn.close()
            QMessageBox.information(self, "Success", f"✅ Kết nối thành công tới {db_type}!\n\nVersion/Info: {version[:100]}")
            
        except ImportError as ie:
            lib = str(ie).split("'")[-2] if "'" in str(ie) else "driver"
            QMessageBox.critical(self, "Thiếu Thư Viện", f"Vui lòng cài đặt thư viện hỗ trợ: pip install {lib}")
        except Exception as e:
            QMessageBox.critical(self, "Kết nối thất bại", f"❌ Lỗi kết nối:\n{str(e)}")

    def on_db_type_changed(self, text):
        db_type = text.replace("⛁ ", "")
        self.win_auth_checkbox.setVisible("SQL Server" in db_type)
        
        # Only change default ports when switching DB type to avoid overwriting host
        if "Oracle" in text:
            self.port_edit.setText("1521")
        elif "MySQL" in text:
            self.port_edit.setText("3306")
        elif "SQL Server" in text:
            self.port_edit.setText("1433")
        elif "DB2" in text:
            self.port_edit.setText("")
            
        self.update_url()

    def on_win_auth_changed(self, state):
        is_windows_auth = (state == 2) # 2 is checked
        self.user_edit.setEnabled(not is_windows_auth)
        self.pass_edit.setEnabled(not is_windows_auth)
        if is_windows_auth:
            self.user_edit.setStyleSheet("background-color: #3c3f41; color: #7a7e85;")
            self.pass_edit.setStyleSheet("background-color: #3c3f41; color: #7a7e85;")
        else:
            self.user_edit.setStyleSheet("")
            self.pass_edit.setStyleSheet("")
        self.update_url()

    def get_connection_data(self):
        return {
            'name': self.name_edit.text() or "Unnamed",
            'db_type': self.type_combo.currentText().replace("⛁ ", ""),
            'host': self.host_edit.text() or "localhost",
            'port': int(self.port_edit.text() or 0),
            'username': self.user_edit.text(),
            'password': self.pass_edit.text(),
            'database_name': self.database_edit.text(),
            'is_synced': self.sync_combo.currentIndex() > 0,
            'is_default': getattr(self, 'is_default_val', 0),
            'use_win_auth': 1 if self.win_auth_checkbox.isChecked() else 0
        }

    def update_url(self):
        db_type = self.type_combo.currentText()
        host = self.host_edit.text()
        port = self.port_edit.text()
        
        if not host:
            host = "localhost"
            
        port_str = f":{port}" if port else ""
        
        if "Oracle" in db_type:
            self.url_edit.setText(f"jdbc:oracle:thin:@{host}{port_str}:XE")
        elif "MySQL" in db_type:
            self.url_edit.setText(f"jdbc:mysql://{host}{port_str}")
        elif "SQL Server" in db_type:
            self.url_edit.setText(f"jdbc:sqlserver://{host}{port_str}")
        elif "DB2" in db_type:
            self.url_edit.setText(f"jdbc:as400://{host}{port_str}")

    def load_management_accounts(self):
        self.mgmt_accounts = get_management_accounts(self.active_conn_id)
        # mgmt_accounts is a list of tuples: (id, name, url, icon, login_details, project_name)
        for acc in self.mgmt_accounts:
            display_name = f"[{acc[5]}] {acc[1]}" # [Project] AccountName
            self.sync_combo.addItem(display_name, acc)

    def on_sync_account_changed(self, index):
        is_synced = index > 0
        
        # Hide/Show User/Pass fields
        self.user_label.setVisible(not is_synced)
        self.user_edit.setVisible(not is_synced)
        self.pass_label.setVisible(not is_synced)
        
        # We need to hide all widgets in pass_layout
        for i in range(self.pass_container.count()):
            widget = self.pass_container.itemAt(i).widget()
            if widget:
                widget.setVisible(not is_synced)
        
        if not is_synced: 
            return
        
        acc = self.sync_combo.itemData(index)
        if not acc: return
        
        # acc: (id, name, url, icon, login_details, project_name)
        self.name_edit.setText(acc[1])
        self.host_edit.setText(acc[2])
        
        # Try to guess DB type from icon or name
        icon = acc[3].lower() if acc[3] else ""
        name = acc[1].lower()
        if "mysql" in name or "mysql" in icon:
            self.type_combo.setCurrentText("⛁ MySQL")
        elif "oracle" in name:
            self.type_combo.setCurrentText("⛁ Oracle")
        elif "sql server" in name or "mssql" in name:
            self.type_combo.setCurrentText("⛁ Microsoft SQL Server")
        elif "db2" in name or "iseries" in name:
            self.type_combo.setCurrentText("⛁ DB2 iSeries")
            
        # Parse login details
        login_json = acc[4]
        if login_json:
            try:
                details = json.loads(login_json)
                if "username" in details: self.user_edit.setText(details["username"])
                if "user" in details: self.user_edit.setText(details["user"])
                if "password" in details: self.pass_edit.setText(details["password"])
                if "pass" in details: self.pass_edit.setText(details["pass"])
                if "port" in details: self.port_edit.setText(str(details["port"]))
                if "database" in details: self.database_edit.setText(details["database"])
                if "db" in details: self.database_edit.setText(details["db"])
            except:
                pass
        
        self.update_url()
