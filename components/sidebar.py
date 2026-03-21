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
        
        if node_type == "connection":
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu { background-color: #3c3f41; color: #a9b7c6; border: 1px solid #2b2b2b; }
                QMenu::item { padding: 5px 20px; }
                QMenu::item:selected { background-color: #2f65ca; color: white; }
                QMenu::separator { height: 1px; background: #2b2b2b; margin: 4px 0px; }
            """)
            
            new_menu = menu.addMenu("+ New")
            new_console_action = new_menu.addAction("Query Console")
            menu.addSeparator()
            prop_action = menu.addAction("Properties")
            
            action = menu.exec(self.treeView.viewport().mapToGlobal(position))
            if action == new_console_action:
                main_window = self.window()
                if hasattr(main_window, "open_new_console"):
                    main_window.open_new_console(name, conn_id)
            elif action == prop_action:
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
        from components.db_store import get_connection
        import pymysql
        conn_data = get_connection(conn_id)
        if not conn_data: return
        
        if "MySQL" not in conn_data[2]:
            item.appendRow(QStandardItem(f"Introspection not supported for {conn_data[2]} yet"))
            return
            
        try:
            conn = pymysql.connect(
                host=conn_data[3], port=int(conn_data[4]),
                user=conn_data[5], password=conn_data[6]
            )
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                dbs = cursor.fetchall()
                
            for db in dbs:
                db_name = db[0]
                db_item = QStandardItem(f"🗀 {db_name}")
                db_item.setData("database", Qt.ItemDataRole.UserRole + 1)
                db_item.setData(conn_id, Qt.ItemDataRole.UserRole)
                db_item.setData(db_name, Qt.ItemDataRole.UserRole + 3)
                db_item.setEditable(False)
                
                db_item.appendRow(QStandardItem("Loading..."))
                item.appendRow(db_item)
        except Exception as e:
            item.appendRow(QStandardItem(f"Error: {e}"))

    def load_tables(self, item, conn_id, db_name):
        from components.db_store import get_connection
        import pymysql
        conn_data = get_connection(conn_id)
        if not conn_data: return
        
        try:
            conn = pymysql.connect(
                host=conn_data[3], port=int(conn_data[4]),
                user=conn_data[5], password=conn_data[6], database=db_name
            )
            with conn.cursor() as cursor:
                cursor.execute("SHOW FULL TABLES")
                tables = cursor.fetchall()
                
            base_tables = [t for t in tables if t[1] == "BASE TABLE"]
            tables_folder = QStandardItem(f"📁 tables  {len(base_tables)}")
            tables_folder.setEditable(False)
            
            for tbl in base_tables:
                table_name = tbl[0]
                table_item = QStandardItem(f"⊞ {table_name}")
                table_item.setData("table", Qt.ItemDataRole.UserRole + 1)
                table_item.setData(conn_id, Qt.ItemDataRole.UserRole)
                table_item.setEditable(False)
                tables_folder.appendRow(table_item)
                
            item.appendRow(tables_folder)
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
