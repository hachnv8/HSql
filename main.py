import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QStatusBar, QToolBar, 
                             QWidget, QTabWidget, QLabel, QToolButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from components.sidebar import DatabaseExplorer
from components.console import SqlConsole
from components.results import ResultsGrid
from components.db_store import init_db

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
        
        self.console = SqlConsole(self)
        self.tabs.addTab(self.console, "console")
        
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

    def set_active_database(self, conn_id, db_name):
        current_console = self.tabs.currentWidget()
        if hasattr(current_console, "set_database_context"):
            current_console.set_database_context(conn_id, db_name)
            self.statusBar.showMessage(f"Selected Database Context: {db_name}", 5000)

    def display_results(self, headers, rows):
        self.results.update_data(headers, rows)

    def open_new_console(self, name, conn_id=None):
        new_console = SqlConsole(self)
        new_console.current_conn_id = conn_id
        idx = self.tabs.addTab(new_console, f"console ({name})")
        self.tabs.setCurrentIndex(idx)
        self.statusBar.showMessage(f"Connected context switched to ({name})", 5000)

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Font hệ thống gọn gàng
    font = QFont("JetBrains Mono", 10)
    app.setFont(font)
    
    window = HSqlMainWindow()
    window.showMaximized()
    sys.exit(app.exec())
