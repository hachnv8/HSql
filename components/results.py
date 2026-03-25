from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QToolBar, QHeaderView, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal
import csv

class ResultsGrid(QWidget):
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.setup_toolbar()
        self.setup_table()
        
    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #3c3f41;
                border-top: 1px solid #2b2b2b;
                border-bottom: 1px solid #2b2b2b;
                padding: 4px;
            }
            QToolButton {
                color: #a9b7c6;
            }
        """)
        
        refresh_action = QAction("↺ Refresh", self)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        self.toolbar.addAction(refresh_action)
        
        export_action = QAction("↓ Export Data", self)
        export_action.triggered.connect(self.export_data)
        self.toolbar.addAction(export_action)
        
        self.layout.addWidget(self.toolbar)

    def setup_table(self):
        self.table = QTableWidget(0, 0)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(True) # Show row numbers!
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #313335;
                color: #a9b7c6;
                gridline-color: #3c3f41;
                border: none;
                selection-background-color: #2f65ca;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView {
                background-color: #2b2b2b;
                border: none;
            }
            QScrollBar::corner {
                background: #2b2b2b;
                border: none;
            }
            /* Row number header styling */
            QHeaderView::section:vertical {
                background-color: #3c3f41;
                color: #7a7e85;
                border: none;
                border-bottom: 1px solid #2b2b2b;
                border-right: 1px solid #2b2b2b;
                padding: 4px;
            }
            /* Column header styling */
            QHeaderView::section:horizontal {
                background-color: #3c3f41;
                color: #a9b7c6;
                border: none;
                border-right: 1px solid #2b2b2b;
                border-bottom: 1px solid #2b2b2b;
                padding: 4px;
                text-align: left;
            }
            QTableCornerButton::section {
                background-color: #3c3f41;
                border: none;
            }
            /* Scrollbar styling */
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4b5052;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5b6062;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none; background: none; height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #2b2b2b;
                height: 14px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4b5052;
                min-width: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5b6062;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none; background: none; width: 0px;
            }
        """)
        
        self.layout.addWidget(self.table)

    def update_data(self, headers, rows):
        self.table.clear()
        
        if len(rows) == 0:
            self.table.setRowCount(1)
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            for col_idx in range(len(headers)):
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(0, col_idx, empty_item)
        else:
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    if col_data is None:
                        item = QTableWidgetItem("<null>")
                        item.setForeground(Qt.GlobalColor.gray)
                        font = item.font()
                        font.setItalic(True)
                        item.setFont(font)
                    else:
                        item = QTableWidgetItem(str(col_data))
                    self.table.setItem(row_idx, col_idx, item)

    def export_data(self):
        if self.table.rowCount() == 0 or (self.table.rowCount() == 1 and self.table.item(0, 0).text() == ""):
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    
                    # Write headers
                    headers = []
                    for col in range(self.table.columnCount()):
                        headers.append(self.table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write rows
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Export Successful", f"Data exported to {file_path}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Failed", f"Could not export data: {str(e)}")
