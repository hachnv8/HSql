import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QStatusBar, QToolBar, 
                             QWidget, QTabWidget, QLabel, QToolButton, QHBoxLayout, QMenu)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction

from components.sidebar import DatabaseExplorer
from components.console import SqlConsole
from components.results import ResultsGrid
from components.db_store import init_db, set_environment

class HSqlMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Init SQLite connection settings DB
        init_db()
        self.setWindowTitle("HSql - Darcula Theme")
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1f22; color: #bcbec4; }
            QSplitter::handle { background-color: #2b2d30; width: 2px; }
            
            QDockWidget { border: 1px solid #2b2d30; }
            QDockWidget::title {
                background-color: #2b2d30; color: #bcbec4; padding: 6px;
                text-align: left; border-bottom: 1px solid #1e1f22;
            }
            QStatusBar { background-color: #2b2d30; color: #bcbec4; border-top: 1px solid #1e1f22; }
        """)

        self.createLeftToolbar()

        self.explorer = DatabaseExplorer(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; border-top: 2px solid #2b2d30; }
            QTabBar::tab {
                background-color: #1e1f22; color: #868a91; padding: 8px 20px; border-right: 1px solid #2b2d30;
            }
            QTabBar::tab:selected {
                color: #bcbec4; background-color: #2b2d30; border-top: 2px solid #375fad;
            }
        """)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Context menu for Tab Bar
        self.tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        
        self.console = SqlConsole(self)
        
        # Apply default DB if exists
        from components.db_store import get_connections
        connections = get_connections()
        default_tab_name = "console"
        for conn in connections:
            if conn[7]: # database_name is at index 7
                conn_id = conn[0]
                db_name = conn[7]
                conn_name = conn[1]
                self.console.set_database_context(conn_id, db_name)
                default_tab_name = f"{db_name} ({conn_name})"
                break
                
        self.tabs.addTab(self.console, default_tab_name)
        
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.tabs)
        
        self.results = ResultsGrid(self)
        self.splitter.addWidget(self.results)
        self.splitter.setSizes([600, 200])
        self.setCentralWidget(self.splitter)

        self.setup_statusbar()
        self.setup_shortcuts()

    def setup_statusbar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        path_label = QLabel(" Database Consoles > account_db > console")
        path_label.setStyleSheet("color: #a9b7c6; font-size: 11px;")
        
        sb_right = QLabel("1:1  UTF-8  4 spaces")
        self.statusBar.addWidget(path_label)
        self.statusBar.addPermanentWidget(sb_right)

    def setup_shortcuts(self):
        # Alt+Insert mapping to Sidebar's Add Connection
        QShortcut(QKeySequence("Alt+Insert"), self).activated.connect(self.explorer.open_connection_dialog)
        
        # Ctrl+F4 to Close Current Tab
        QShortcut(QKeySequence("Ctrl+F4"), self).activated.connect(lambda: self.close_tab(self.tabs.currentIndex()))

    def set_active_database(self, conn_id, db_name):
        current_console = self.tabs.currentWidget()
        if hasattr(current_console, "set_database_context"):
            current_console.set_database_context(conn_id, db_name)
            self.statusBar.showMessage(f"Selected Database Context: {db_name}", 5000)

    def display_results(self, headers, rows):
        self.results.update_data(headers, rows)

    def open_new_console(self, name, conn_id=None, db_name=None):
        if conn_id and not db_name:
            from components.db_store import get_connection
            conn_data = get_connection(conn_id)
            if conn_data and conn_data[7]:
                db_name = conn_data[7]
                
        new_console = SqlConsole(self)
        new_console.current_conn_id = conn_id
        
        tab_name = f"console ({name})"
        if db_name:
            tab_name = f"{db_name} ({name})"
            new_console.set_database_context(conn_id, db_name)
            
        idx = self.tabs.addTab(new_console, tab_name)
        self.tabs.setCurrentIndex(idx)
        self.statusBar.showMessage(f"Opened new console for {db_name or name}", 5000)

    def createLeftToolbar(self):
        toolbar = QToolBar("Main Left Toolbar")
        toolbar.setOrientation(Qt.Orientation.Vertical)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2b2d30;
                border-right: 1px solid #1e1f22;
                spacing: 12px;
                padding-top: 8px;
            }
            QToolButton { color: #bcbec4; border: none; padding: 8px; font-size: 14px; }
            QToolButton:hover { background-color: #43454a; }
        """)
        
        for text in ["≡", "…"]:
            btn = QToolButton()
            btn.setText(text)
            toolbar.addWidget(btn)

        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Expanding)
        toolbar.addWidget(spacer)
        
        btn_settings = QToolButton()
        btn_settings.setText("⛭")
        toolbar.addWidget(btn_settings)
        
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
        
    def close_tab(self, index):
        if index != -1:
            widget = self.tabs.widget(index)
            self.tabs.removeTab(index)
            if widget:
                widget.deleteLater()

    def show_tab_context_menu(self, position):
        index = self.tabs.tabBar().tabAt(position)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2b2d30; color: #bcbec4; border: 1px solid #1e1f22; }
            QMenu::item { padding: 6px 30px; }
            QMenu::item:selected { background-color: #2f65ca; color: white; }
        """)
        
        close_action = QAction("Close", self)
        close_action.setShortcut("Ctrl+F4")
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)
        
        close_others_action = QAction("Close Other Tabs", self)
        close_others_action.triggered.connect(lambda: self.close_other_tabs(index))
        menu.addAction(close_others_action)
        
        close_all_action = QAction("Close All Tabs", self)
        close_all_action.triggered.connect(self.close_all_tabs)
        menu.addAction(close_all_action)
        
        close_right_action = QAction("Close Tabs to the Right", self)
        close_right_action.triggered.connect(lambda: self.close_tabs_to_right(index))
        menu.addAction(close_right_action)
        
        if index == -1:
            close_action.setEnabled(False)
            close_others_action.setEnabled(False)
            close_right_action.setEnabled(False)
            
        menu.exec(self.tabs.tabBar().mapToGlobal(position))

    def close_other_tabs(self, index):
        for i in range(self.tabs.count() - 1, -1, -1):
            if i != index:
                self.close_tab(i)

    def close_all_tabs(self):
        for i in range(self.tabs.count() - 1, -1, -1):
            self.close_tab(i)

    def close_tabs_to_right(self, index):
        for i in range(self.tabs.count() - 1, index, -1):
            self.close_tab(i)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Font hệ thống gọn gàng
    font = QFont("JetBrains Mono", 10)
    app.setFont(font)
    
    from PyQt6.QtWidgets import QMessageBox
    
    # Hiển thị popup chọn môi trường
    msgBox = QMessageBox()
    msgBox.setWindowTitle("Choose Environment")
    msgBox.setText("Select the database environment for HSql:")
    
    btn_local = msgBox.addButton("Local (Windows/SQLite)", QMessageBox.ButtonRole.AcceptRole)
    btn_prod = msgBox.addButton("Production (Linux/MySQL)", QMessageBox.ButtonRole.AcceptRole)
    
    # Giao diện Dark theme cơ bản cho msgBox
    msgBox.setStyleSheet("""
        QMessageBox { background-color: #2b2b2b; color: #a9b7c6; }
        QLabel { color: #a9b7c6; }
        QPushButton {
            background-color: #3c3f41; color: #a9b7c6;
            border: 1px solid #555555; padding: 6px 18px; border-radius: 4px;
        }
        QPushButton:hover { background-color: #4b5052; }
    """)
    
    msgBox.exec()
    
    if msgBox.clickedButton() == btn_prod:
        set_environment("production")
    else:
        set_environment("local")
    
    window = HSqlMainWindow()
    window.showMaximized()
    sys.exit(app.exec())
