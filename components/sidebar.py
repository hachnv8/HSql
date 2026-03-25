from PyQt6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QTreeView, QDockWidget, QToolButton, QMenu
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class DatabaseExplorer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Database Explorer", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        # Giấu nút Close/Undock của Dock để UI trông liền mạch phẳng lỳ
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.setup_toolbar()
        self.setup_treeview()
        self.setWidget(self.container)
        
    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #3c3f41;
                border-bottom: 1px solid #2b2b2b;
                padding: 4px;
                spacing: 2px;
            }
            QToolButton {
                color: #a9b7c6;
                background-color: transparent;
                border: none;
                padding: 4px 8px;
                font-family: Consolas, monospace;
            }
            QToolButton:hover {
                background-color: #4b5052;
                border-radius: 3px;
            }
        """)
        
        # Bỏ hệ thống Emoji mặc định của Windows vì nó trêm màu sắc loè loẹt
        # Thay bằng Text ký tự hình khối trung tính
        # Lược bỏ DDL và nút View theo yêu cầu
        actions = [
            ("+", "Add"),
            ("⛭", "Properties"),
            ("↺", "Refresh"),
            ("×", "Disconnect"),
        ]
        
        for text, tooltip in actions:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            if text == "+":
                # Catch the click event to open new dialog
                btn.clicked.connect(self.open_connection_dialog)
            self.toolbar.addWidget(btn)
                
        self.layout.addWidget(self.toolbar)

    def open_connection_dialog(self):
        from components.connections import ConnectionDialog
        from components.db_store import save_connection
        dlg = ConnectionDialog(self)
        if dlg.exec():
            data = dlg.get_connection_data()
            save_connection(data)
            self.reload_treeview()

    def on_tree_double_click(self, index):
        item = self.model.itemFromIndex(index)
        if not item: return
        node_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if node_type == "database":
            db_name = item.data(Qt.ItemDataRole.UserRole + 3)
            conn_id = item.data(Qt.ItemDataRole.UserRole)
            main_window = self.window()
            if hasattr(main_window, "set_active_database"):
                main_window.set_active_database(conn_id, db_name)
        elif node_type == "connection":
            conn_id = item.data(Qt.ItemDataRole.UserRole)
            main_window = self.window()
            if hasattr(main_window, "set_active_database"):
                # No specific DB selected, just the connection
                main_window.set_active_database(conn_id, None)

    def on_context_menu(self, position):
        index = self.treeView.indexAt(position)
        if not index.isValid():
            return
            
        item = self.model.itemFromIndex(index)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
            
        conn_id = item.data(Qt.ItemDataRole.UserRole)
        node_type = item.data(Qt.ItemDataRole.UserRole + 1)
        raw_text = item.text()
        name = raw_text.split(" ")[1] if " " in raw_text else "Connection"
        
        if node_type == "connection" or node_type == "database":
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu { background-color: #3c3f41; color: #a9b7c6; border: 1px solid #2b2b2b; }
                QMenu::item { padding: 5px 20px; }
                QMenu::item:selected { background-color: #2f65ca; color: white; }
                QMenu::separator { height: 1px; background: #2b2b2b; margin: 4px 0px; }
            """)
            
            select_context_action = menu.addAction("Select Context")
            menu.addSeparator()
            
            new_menu = menu.addMenu("+ New")
            new_console_action = new_menu.addAction("Query Console")
            
            set_default_action = None
            if node_type == "database":
                menu.addSeparator()
                set_default_action = menu.addAction("Choose as default db")
            
            if node_type == "connection":
                menu.addSeparator()
                prop_action = menu.addAction("Properties")
            else:
                prop_action = None
            
            action = menu.exec(self.treeView.viewport().mapToGlobal(position))
            
            main_window = self.window()
            if action == select_context_action:
                if node_type == "database":
                    db_name = item.data(Qt.ItemDataRole.UserRole + 3)
                    if hasattr(main_window, "set_active_database"):
                        main_window.set_active_database(conn_id, db_name)
                else:
                    # For connection node, select only the connection
                    if hasattr(main_window, "set_active_database"):
                        main_window.set_active_database(conn_id, None)
            elif action == new_console_action:
                if hasattr(main_window, "open_new_console"):
                    if node_type == "database":
                        db_name = item.data(Qt.ItemDataRole.UserRole + 3)
                        # Get connection name from parent
                        conn_name = item.parent().text().split(" ")[1] if item.parent() else "Conn"
                        main_window.open_new_console(conn_name, conn_id, db_name)
                    else:
                        main_window.open_new_console(name, conn_id)
            elif set_default_action and action == set_default_action:
                from components.db_store import set_default_database
                db_name = item.data(Qt.ItemDataRole.UserRole + 3)
                set_default_database(conn_id, db_name)
                # Refresh Tree to show highlight
                self.reload_treeview()
                # Safe status bar access
                main_win = self.window()
                sbar = main_win.statusBar() if callable(getattr(main_win, 'statusBar', None)) else getattr(main_win, 'statusBar', None)
                if sbar:
                    sbar.showMessage(f"Set {db_name} as default for {name}", 5000)
            elif prop_action and action == prop_action:
                self.open_properties(conn_id)

    def open_properties(self, conn_id):
        from components.db_store import get_connection, update_connection
        from components.connections import ConnectionDialog
        
        conn_data = get_connection(conn_id)
        if not conn_data: return
        
        dlg = ConnectionDialog(self, conn_data)
        if dlg.exec():
            data = dlg.get_connection_data()
            update_connection(conn_id, data)
            self.reload_treeview()

    def on_item_expanded(self, index):
        item = self.model.itemFromIndex(index)
        if not item: return
        
        if item.rowCount() == 1 and item.child(0).text() == "Loading...":
            node_type = item.data(Qt.ItemDataRole.UserRole + 1)
            item.removeRow(0)
            
            if node_type == "connection":
                conn_id = item.data(Qt.ItemDataRole.UserRole)
                self.load_databases(item, conn_id)
            elif node_type == "database":
                conn_id = item.data(Qt.ItemDataRole.UserRole)
                db_name = item.data(Qt.ItemDataRole.UserRole + 3)
                self.load_tables(item, conn_id, db_name)

    def load_databases(self, item, conn_id):
        from components.db_store import get_connection, get_db_connection
        conn_data = get_connection(conn_id)
        if not conn_data: return
        
        db_type = conn_data[2]
        
        try:
            conn = get_db_connection(conn_id)
            if not conn:
                item.appendRow(QStandardItem("Error: Unable to connect"))
                return
                
            cursor = conn.cursor()
            try:
                if "MySQL" in db_type:
                    cursor.execute("SHOW DATABASES")
                elif "Oracle" in db_type:
                    cursor.execute("SELECT username FROM all_users ORDER BY username")
                elif "SQL Server" in db_type:
                    cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
                elif "DB2" in db_type:
                    cursor.execute("SELECT SCHEMA_NAME FROM QSYS2.SYSSCHEMAS ORDER BY SCHEMA_NAME")
                
                dbs = cursor.fetchall()
            finally:
                cursor.close()
                
            default_db = conn_data[7] if len(conn_data) > 7 else None
            
            for db in dbs:
                db_name = db[0]
                is_default = (db_name == default_db)
                display_name = f"🗀 {db_name}"
                if is_default:
                   display_name = f"🗀 {db_name} (default)"
                
                db_item = QStandardItem(display_name)
                db_item.setData("database", Qt.ItemDataRole.UserRole + 1)
                db_item.setData(conn_id, Qt.ItemDataRole.UserRole)
                db_item.setData(db_name, Qt.ItemDataRole.UserRole + 3)
                db_item.setEditable(False)
                
                if is_default:
                    from PyQt6.QtGui import QColor, QFont
                    db_item.setForeground(QColor("#629755")) # IntelliJ Green
                    font = db_item.font()
                    font.setBold(True)
                    db_item.setFont(font)
                
                db_item.appendRow(QStandardItem("Loading..."))
                item.appendRow(db_item)
                
            # After loading databases, re-apply highlight if needed
            main_window = self.window()
            if hasattr(main_window, "tabs"):
                console = main_window.tabs.currentWidget()
                if hasattr(console, "current_conn_id") and console.current_conn_id == conn_id:
                    self.highlight_active_context(console.current_conn_id, getattr(console, "current_db_name", None))
        except Exception as e:
            item.appendRow(QStandardItem(f"Error: {e}"))

    def load_tables(self, item, conn_id, db_name):
        from components.db_store import get_connection, get_db_connection
        conn_data = get_connection(conn_id)
        if not conn_data: return
        db_type = conn_data[2]
        
        try:
            conn = get_db_connection(conn_id, db_name)
            if not conn:
                item.appendRow(QStandardItem("Error: Unable to connect"))
                return
                
            cursor = conn.cursor()
            try:
                if "MySQL" in db_type:
                    cursor.execute("SHOW FULL TABLES")
                    rows = cursor.fetchall()
                    # Filter for BASE TABLE
                    tables = [r[0] for r in rows if r[1] == "BASE TABLE"]
                elif "Oracle" in db_type:
                    cursor.execute("SELECT table_name FROM all_tables WHERE owner = :1 ORDER BY table_name", (db_name,))
                    tables = [r[0] for r in cursor.fetchall()]
                elif "SQL Server" in db_type:
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = ? AND table_type = 'BASE TABLE'", (db_name,))
                    tables = [r[0] for r in cursor.fetchall()]
                elif "DB2" in db_type:
                    cursor.execute("SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = ? ORDER BY TABLE_NAME", (db_name,))
                    tables = [r[0] for r in cursor.fetchall()]
                else:
                    tables = []
            finally:
                cursor.close()
                
            if tables:
                tables_folder = QStandardItem(f"📁 tables  {len(tables)}")
                tables_folder.setEditable(False)
                
                for table_name in tables:
                    table_item = QStandardItem(f"⊞ {table_name}")
                    table_item.setData("table", Qt.ItemDataRole.UserRole + 1)
                    table_item.setData(conn_id, Qt.ItemDataRole.UserRole)
                    table_item.setEditable(False)
                    tables_folder.appendRow(table_item)
                    
                item.appendRow(tables_folder)
            else:
                item.appendRow(QStandardItem("No tables found"))
            
            conn.close()
        except Exception as e:
            item.appendRow(QStandardItem(f"Error: {e}"))

    def setup_treeview(self):
        self.treeView = QTreeView()
        self.treeView.setHeaderHidden(True)
        self.treeView.setStyleSheet("""
            QTreeView {
                background-color: #2b2d30;
                color: #bcbec4;
                border: none;
                font-family: 'JetBrains Mono', Consolas, monospace;
            }
            QTreeView::item {
                padding: 4px;
            }
            QTreeView::item:hover {
                background-color: #43454a;
            }
            QTreeView::item:selected {
                background-color: #2f65ca;
                color: white;
            }
        """)
        
        self.model = QStandardItemModel()
        self.rootNode = self.model.invisibleRootItem()
        self.treeView.setModel(self.model)
        
        self.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.on_context_menu)
        self.treeView.expanded.connect(self.on_item_expanded)
        self.treeView.doubleClicked.connect(self.on_tree_double_click)
        
        self.layout.addWidget(self.treeView)
        self.reload_treeview()

    def reload_treeview(self):
        from components.db_store import get_connections
        self.rootNode.removeRows(0, self.rootNode.rowCount())
        connections = get_connections()
        
        if not connections:
            emptyNode = QStandardItem("> Chưa có Database nào (Bấm + để thêm)")
            emptyNode.setEnabled(False)
            self.rootNode.appendRow(emptyNode)
        else:
            for conn in connections:
                # 0:id, 1:name, 2:db_type, 3:host, 4:port, 5:user, 6:pass, 7:database_name
                conn_id = conn[0]
                name = conn[1]
                host = conn[3]
                
                connectionNode = QStandardItem(f"⛁ {name} @{host}")
                connectionNode.setEditable(False)
                connectionNode.setData(conn_id, Qt.ItemDataRole.UserRole)
                connectionNode.setData("connection", Qt.ItemDataRole.UserRole + 1)
                
                dummyNode = QStandardItem("Loading...")
                dummyNode.setEditable(False)
                connectionNode.appendRow(dummyNode)
                
                self.rootNode.appendRow(connectionNode)
        
        self.treeView.expandAll()

    def highlight_active_context(self, conn_id, db_name=None):
        from PyQt6.QtGui import QColor, QFont
        
        # Reset all styles first
        def reset_items(parent_item):
            for row in range(parent_item.rowCount()):
                child = parent_item.child(row)
                child.setForeground(QColor("#bcbec4"))
                font = child.font()
                font.setBold(False)
                child.setFont(font)
                if child.rowCount() > 0:
                    reset_items(child)
        
        reset_items(self.rootNode)
        
        # Find and highlight target
        for row in range(self.rootNode.rowCount()):
            conn_item = self.rootNode.child(row)
            if conn_item.data(Qt.ItemDataRole.UserRole) == conn_id:
                # If db_name is None, highlight the connection itself
                if db_name is None:
                    conn_item.setForeground(QColor("#629755")) # Green
                    font = conn_item.font()
                    font.setBold(True)
                    conn_item.setFont(font)
                else:
                    # Highlight the specific database under this connection
                    for sub_row in range(conn_item.rowCount()):
                        db_item = conn_item.child(sub_row)
                        if db_item.data(Qt.ItemDataRole.UserRole + 1) == "database" and \
                           db_item.data(Qt.ItemDataRole.UserRole + 3) == db_name:
                            db_item.setForeground(QColor("#629755"))
                            font = db_item.font()
                            font.setBold(True)
                            db_item.setFont(font)
                            break
                break
