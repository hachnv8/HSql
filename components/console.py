from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QToolBar, QToolButton, QComboBox, QMessageBox, QCompleter)
from PyQt6.QtCore import Qt, QSize, QStringListModel
from PyQt6.QtGui import QFont, QIcon, QShortcut, QTextCursor, QKeySequence

class SqlTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer = None

    def setCompleter(self, c):
        if self.completer:
            self.completer.activated.disconnect()
        self.completer = c
        c.setWidget(self)
        c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        if self.completer.widget() is not self: return
        tc = self.textCursor()
        prefix_len = len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, prefix_len)
        tc.insertText(completion)
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, e):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(e)

    def insertFromMimeData(self, source):
        # Force plain text paste to ignore external formatting (fonts, colors, etc.)
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)

    def keyPressEvent(self, e):
        if not self.completer:
            super().keyPressEvent(e)
            return

        if self.completer.popup().isVisible():
            if e.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                e.ignore()
                return

        isShortcut = ((e.modifiers() & Qt.KeyboardModifier.ControlModifier) and e.key() == Qt.Key.Key_Space)
        if not self.completer or not isShortcut:
            super().keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        if not self.completer or (ctrlOrShift and not e.text()):
            return

        hasModifier = (e.modifiers() != Qt.KeyboardModifier.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        # Custom logic for '.' trigger
        if e.text() == ".":
            # For MySQL/Postgres: 'db_name.'
            # We need the word exactly before the cursor (excluding the dot we just typed)
            tc = self.textCursor()
            tc.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
            full_text = self.toPlainText()
            pos = tc.position()
            
            # Find the start of the word before the dot
            start = pos
            while start > 0 and (full_text[start-1].isalnum() or full_text[start-1] in '_'):
                start -= 1
            word_before_dot = full_text[start:pos]
            
            # Check if it's a known schema (case-insensitive)
            schemas_lower = [s.lower() for s in getattr(self, 'sql_schemas', [])]
            if word_before_dot.lower() in schemas_lower:
                idx = schemas_lower.index(word_before_dot.lower())
                actual_schema = self.sql_schemas[idx]
                
                parent_console = self.parent()
                while parent_console and not hasattr(parent_console, 'fetch_schema_tables'):
                    parent_console = parent_console.parent()
                if parent_console:
                    parent_console.fetch_schema_tables(actual_schema)
                    # For a dot, we want to clear prefix and show new tables immediately
                    self.completer.setCompletionPrefix("")
                    cr = self.cursorRect()
                    cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
                    self.completer.complete(cr)
                    self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))
                    return

        if not isShortcut and (hasModifier or not e.text() or len(completionPrefix) < 1):
            self.completer.popup().hide()
            return

        # Context-aware model update
        tc_check = self.textCursor()
        tc_check.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(completionPrefix))
        tc_check.movePosition(QTextCursor.MoveOperation.PreviousWord, QTextCursor.MoveMode.KeepAnchor)
        prev_word = tc_check.selectedText().strip().upper()
        
        # Context-aware model update
        is_table_context = prev_word in ["FROM", "JOIN", "INTO", "UPDATE", "TABLE", "DESC", "DESCRIBE"]
        
        # If we are typing after a dot (db.table), we are still in a "table-like" context
        # Check if the prefix has a dot at the end or in it
        if "." in completionPrefix:
            is_table_context = True

        if getattr(self, '_last_context_was_table', None) != is_table_context:
            self._last_context_was_table = is_table_context
            keywords = getattr(self, 'sql_keywords', [])
            tables = getattr(self, 'sql_tables', [])
            schemas = getattr(self, 'sql_schemas', [])
            
            if is_table_context:
                # Include both tables and schemas (databases) in table context
                model_items = sorted(list(set(tables + schemas)))
            else:
                model_items = sorted(list(set(keywords + tables + schemas)))
            
            self.completer.setModel(QStringListModel(model_items))

        if completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                    + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)
        self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

class SqlConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.current_file = None
        self.current_conn_id = None
        self.current_db_name = None
        self.active_conn = None # Persistent connection for transactions
        
        self.setup_inline_toolbar()
        
        self.editor = SqlTextEdit()
        font = QFont("JetBrains Mono", 14)
        self.editor.setFont(font)
        self.editor.setPlaceholderText("-- Write your SQL here...\nSELECT * FROM account_db;")
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #191a1c;
                color: #bcbec4;
                border: none;
                padding: 10px;
                selection-background-color: #214283;
                font-family: 'JetBrains Mono', Consolas, monospace;
            }
        """)
        
        # Attach Syntax Highlighter
        from components.highlighter import SqlHighlighter
        self.highlighter = SqlHighlighter(self.editor.document())
        
        self.completer = QCompleter()
        self.completer.popup().setStyleSheet("""
            QListView { background-color: #2b2d30; color: #bcbec4; border: 1px solid #43454a; font-family: 'JetBrains Mono', Consolas, monospace; font-size: 14px; }
            QListView::item { padding: 4px; }
            QListView::item:selected { background-color: #2f65ca; color: white; }
        """)
        self.editor.setCompleter(self.completer)
        self.update_autocomplete()
        
        self.layout.addWidget(self.editor)
        self.setup_shortcuts()

    def setup_inline_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { background-color: #2b2d30; border-bottom: 1px solid #1e1f22; padding: 4px; spacing: 4px; }
            QToolButton { color: #bcbec4; background-color: transparent; border: none; padding: 4px 8px; }
            QToolButton:hover { background-color: #43454a; border-radius: 3px; }
            QComboBox { background-color: transparent; color: #bcbec4; border: none; padding: 2px 10px; }
        """)
        
        # Plain text arrow thay vì Emoji
        play_btn = QToolButton()
        play_btn.setText("►")
        play_btn.setStyleSheet("color: #629755; font-size: 16px; font-weight: bold;")
        self.toolbar.addWidget(play_btn)
        
        # The original code had a loop for these, but the diff implies specific buttons.
        # I'll keep the original loop structure for now, as the diff was fragmented here.
        # Loop for extra buttons - removed per user request
        # for text in ["◷", "P", "⛭"]:
        #     btn = QToolButton()
        #     btn.setText(text)
        #     self.toolbar.addWidget(btn)
            
        # self.toolbar.addSeparator()
        
        # tx_combo = QComboBox()
        # tx_combo.addItems(["Tx: Auto"])
        # self.toolbar.addWidget(tx_combo)
        
        btn_commit = QToolButton()
        btn_commit.setText("✓")
        btn_commit.setToolTip("Commit Transaction")
        btn_commit.setStyleSheet("color: #629755; font-size: 16px; font-weight: bold;")
        btn_commit.clicked.connect(self.commit_query)
        self.toolbar.addWidget(btn_commit)
        
        btn_rollback = QToolButton()
        btn_rollback.setText("↺")
        btn_rollback.setToolTip("Rollback Transaction")
        btn_rollback.setStyleSheet("color: #cc6600; font-size: 16px; font-weight: bold;")
        btn_rollback.clicked.connect(self.rollback_query)
        self.toolbar.addWidget(btn_rollback)
        
        self.toolbar.addSeparator()
        
        self.schema_combo = QComboBox()
        self.schema_combo.addItems(["<schema>"])
        self.toolbar.addWidget(self.schema_combo)
        
        # Add Stretch to push the close button to the right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setStyleSheet("color: #bcbec4; font-size: 14px; font-weight: bold;")
        close_btn.setToolTip("Close Console")
        close_btn.clicked.connect(self.close_self)
        self.toolbar.addWidget(close_btn)
        
        self.layout.addWidget(self.toolbar)

    def close_self(self):
        if self.active_conn:
            try:
                self.active_conn.close()
            except Exception:
                pass
            self.active_conn = None
            
        main_window = self.window()
        if hasattr(main_window, 'tabs'):
            idx = main_window.tabs.indexOf(self)
            if idx != -1:
                # Use the close_tab method in main_window if it exists
                if hasattr(main_window, 'close_tab'):
                    main_window.close_tab(idx)
                else:
                    main_window.tabs.removeTab(idx)
                    self.deleteLater()

    def setup_shortcuts(self):
        # Ctrl+Enter to Execute
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.execute_query)
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self.execute_query)
        
        # Ctrl+/ to Toggle Comment
        QShortcut(QKeySequence("Ctrl+/"), self).activated.connect(self.toggle_comment)
        
        # Ctrl+Y to Delete Line (Override default Redo)
        shortcut_del = QShortcut(QKeySequence("Ctrl+Y"), self.editor)
        shortcut_del.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut_del.activated.connect(self.delete_line)
        
        # Ctrl+W to Extend Selection
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.extend_selection)
        
        # Ctrl+S to Save and Ctrl+O to Open
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_file)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.open_file)
        
        # Ctrl+Shift+F to Format Code
        QShortcut(QKeySequence("Ctrl+Shift+F"), self).activated.connect(self.format_sql)
        
    def set_database_context(self, conn_id, db_name):
        self.current_conn_id = conn_id
        self.current_db_name = db_name
        self.schema_combo.clear()
        if db_name:
            self.schema_combo.addItem(db_name)
        else:
            self.schema_combo.addItem("<Connection Only>")
        
        # Trigger autocomplete update (Tables in current db or list of dbs)
        self.update_autocomplete()

    def update_autocomplete(self):
        keywords = ["SELECT", "FROM", "WHERE", "INSERT", "INTO", "UPDATE", "DELETE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET", "CREATE", "ALTER", "DROP", "TABLE", "DATABASE", "INDEX", "VIEW", "AS", "AND", "OR", "NOT", "IS", "NULL", "PRIMARY KEY", "FOREIGN KEY", "REFERENCES", "SET", "VALUES", "ALTER TABLE", "ADD COLUMN", "CHANGE COLUMN"]
        self.editor.sql_keywords = keywords
        self.editor.sql_tables = []
        self.editor.sql_schemas = []
        self.completer_data = list(keywords)
        
        if self.current_conn_id:
            try:
                from components.db_store import get_db_connection, get_connection
                conn_data = get_connection(self.current_conn_id)
                db_type = conn_data[2]
                
                conn = self.active_conn if self.active_conn else get_db_connection(self.current_conn_id, self.current_db_name)
                
                if conn:
                    cursor = conn.cursor()
                    try:
                        if self.current_db_name:
                            if "MySQL" in db_type:
                                # Ensure we are using the correct database context
                                cursor.execute(f"USE `{self.current_db_name}`")
                                cursor.execute("SHOW TABLES")
                            elif "Oracle" in db_type:
                                cursor.execute("SELECT table_name FROM all_tables WHERE owner = :1", (self.current_db_name,))
                            elif "SQL Server" in db_type:
                                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = ?", (self.current_db_name,))
                            elif "DB2" in db_type:
                                cursor.execute("SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = ?", (self.current_db_name,))
                            
                            tables = [str(r[0]).strip() for r in cursor.fetchall()]
                            self.editor.sql_tables = tables
                            self.completer_data += tables
                        else:
                            # Connection level - load schemas
                            if "MySQL" in db_type:
                                cursor.execute("SHOW DATABASES")
                            elif "Oracle" in db_type:
                                cursor.execute("SELECT username FROM all_users")
                            elif "SQL Server" in db_type:
                                cursor.execute("SELECT name FROM sys.databases")
                            elif "DB2" in db_type:
                                cursor.execute("SELECT SCHEMA_NAME FROM QSYS2.SYSSCHEMAS")
                            
                            schemas = [str(r[0]).strip() for r in cursor.fetchall()]
                            # Exclude internal schemas for better UX
                            internal = ['information_schema', 'mysql', 'performance_schema', 'sys']
                            schemas = [s for s in schemas if s.lower() not in internal]
                            self.editor.sql_schemas = schemas
                            self.completer_data += schemas
                            
                    finally:
                        cursor.close()
                    if not self.active_conn:
                        conn.close()
            except Exception:
                pass
        
        self.editor._last_context_was_table = None # Force re-calculation on next key
        self.refresh_completer_model()

    def fetch_schema_tables(self, schema_name):
        """Fetches tables for a specific schema dynamically (triggered by '.')"""
        if not self.current_conn_id: return
        
        try:
            from components.db_store import get_db_connection, get_connection
            conn_data = get_connection(self.current_conn_id)
            db_type = conn_data[2]
            
            conn = self.active_conn if self.active_conn else get_db_connection(self.current_conn_id, schema_name)
            if conn:
                cur = conn.cursor()
                try:
                    if "DB2" in db_type:
                        cur.execute("SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = ?", (schema_name,))
                    elif "MySQL" in db_type:
                        # Use backticks for schema name to handle reserved words/spaces
                        cur.execute(f"SHOW TABLES FROM `{schema_name}`")
                    elif "SQL Server" in db_type:
                        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = ?", (schema_name,))
                    else:
                        # Generic attempt
                        cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}'")
                    
                    new_tables = [str(r[0]) for r in cur.fetchall()]
                    
                    # Add new tables to the existing list (merging)
                    # Use a set to avoid duplicates
                    all_tables = list(set(self.editor.sql_tables + new_tables))
                    self.editor.sql_tables = all_tables
                    
                    self.refresh_completer_model(new_tables)
                    
                finally:
                    cur.close()
                if not self.active_conn:
                    conn.close()
        except Exception:
            pass

    def refresh_completer_model(self, custom_list=None):
        if custom_list is not None:
            word_list = sorted(list(set(custom_list)))
        else:
            keywords = getattr(self.editor, 'sql_keywords', [])
            tables = getattr(self.editor, 'sql_tables', [])
            schemas = getattr(self.editor, 'sql_schemas', [])
            word_list = list(set(keywords + tables + schemas))
            
        model = QStringListModel(word_list)
        self.completer.setModel(model)

    def execute_query(self):
        from PyQt6.QtWidgets import QMessageBox, QMenu
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if selected_text.strip():
            self._do_run_sql(selected_text)
            return
            
        text = self.editor.toPlainText()
        if not text.strip(): return
        
        # Split into statements keeping track of bounds
        cursor_pos = cursor.position()
        statements = []
        last_pos = 0
        for i, char in enumerate(text):
            if char == ';':
                statements.append((last_pos, i + 1, text[last_pos:i].strip()))
                last_pos = i + 1
        if last_pos < len(text) and text[last_pos:].strip():
            statements.append((last_pos, len(text), text[last_pos:].strip()))
            
        valid_stmts = [s for s in statements if s[2]]
        
        current_stmt = ""
        for start, end, stmt in valid_stmts:
            if start <= cursor_pos <= end:
                current_stmt = stmt
                break
                
        if not current_stmt and valid_stmts:
            for start, end, stmt in reversed(valid_stmts):
                if cursor_pos >= start:
                    current_stmt = stmt
                    break
            if not current_stmt:
                current_stmt = valid_stmts[0][2]

        full_text = text.strip()
        
        # If only one statement exists
        if len(valid_stmts) <= 1:
            self._do_run_sql(full_text)
            return
            
        # Menu popup for multiple statements
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2b2d30; color: #bcbec4; border: 1px solid #1e1f22; }
            QMenu::item { padding: 8px 30px; font-family: 'JetBrains Mono', Consolas, monospace; }
            QMenu::item:selected { background-color: #2f65ca; color: white; }
            QMenu::separator { height: 1px; background: #1e1f22; }
        """)
        
        # Header label (non-clickable) style
        header_action = menu.addAction("          Statements")
        header_action.setEnabled(False)
        menu.addSeparator()
        
        disp_stmt = current_stmt[:50] + "..." if len(current_stmt) > 50 else current_stmt
        disp_stmt_action = menu.addAction(disp_stmt)
        # Use single backslash for newline replacement
        all_stmts_action = menu.addAction(full_text.replace('\n', ' ')[:50] + "...")
        
        # Calculate cursor pos
        cursor_rect = self.editor.cursorRect(cursor)
        global_pos = self.editor.viewport().mapToGlobal(cursor_rect.bottomLeft())
        global_pos.setY(global_pos.y() + 10)
        
        menu.setActiveAction(disp_stmt_action)
        
        selected_action = menu.exec(global_pos)
        if selected_action == disp_stmt_action:
            self._do_run_sql(current_stmt)
        elif selected_action == all_stmts_action:
            self._do_run_sql(full_text)

    def _do_run_sql(self, sql):
        from PyQt6.QtWidgets import QMessageBox
        if not getattr(self, "current_conn_id", None):
            QMessageBox.warning(self, "Execute", "Chưa có kết nối nào được gán cho Console này!")
            return
            
        from components.db_store import get_connection
        import pymysql
        conn_data = get_connection(self.current_conn_id)
        if not conn_data: return
        
        db_name = self.schema_combo.currentText()
        if db_name in ["<schema>", "<Connection Only>"]: db_name = None
        
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        if not statements: return
        
        try:
            from components.db_store import get_db_connection
            # Reuse or create active connection
            if not self.active_conn:
                self.active_conn = get_db_connection(self.current_conn_id, db_name)
                # Ensure autocommit is off for manual transaction control
                if hasattr(self.active_conn, 'autocommit'):
                    try:
                        self.active_conn.autocommit(False)
                    except TypeError:
                        self.active_conn.autocommit = False
            
            if not self.active_conn:
                QMessageBox.critical(self, "Lỗi", "Không thể tạo kết nối tới Database!")
                return
                
            affected = 0
            last_headers = None
            last_rows = None
            
            with self.active_conn.cursor() as cur:
                for stmt in statements:
                    cur.execute(stmt)
                    if cur.description:
                        last_headers = [desc[0] for desc in cur.description]
                        # Tối đa 200 dòng cho 1 lần hiển thị result
                        last_rows = cur.fetchmany(200)
                    else:
                        affected += cur.rowcount
            
            if last_headers is not None:
                main_window = self.window()
                if hasattr(main_window, "display_results"):
                    main_window.display_results(last_headers, last_rows)
            else:
                # Do NOT commit automatically!
                # conn.commit() 
                QMessageBox.information(self, "Thành công", f"Đã chạy lệnh (Chưa commit)!\nBị ảnh hưởng: {affected} dòng.")
        except Exception as e:
            # If connection lost, clear active_conn
            self.active_conn = None
            QMessageBox.critical(self, "Lỗi Query", f"{e}")

    def commit_query(self):
        if not self.active_conn:
            QMessageBox.information(self, "Commit", "Không có transaction nào đang chờ.")
            return
        try:
            self.active_conn.commit()
            QMessageBox.information(self, "Commit", "Đã Commit thành công!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Commit", f"{e}")

    def rollback_query(self):
        if not self.active_conn:
            QMessageBox.information(self, "Rollback", "Không có transaction nào đang chờ.")
            return
        try:
            self.active_conn.rollback()
            QMessageBox.information(self, "Rollback", "Đã Rollback thành công!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Rollback", f"{e}")

    def save_file(self):
        from PyQt6.QtWidgets import QFileDialog
        import os
        if not getattr(self, "current_file", None):
            file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file SQL", "", "SQL Files (*.sql);;All Files (*)")
            if not file_path: return
            self.current_file = file_path
            
            main_window = self.window()
            if hasattr(main_window, 'tabs'):
                idx = main_window.tabs.indexOf(self)
                if idx != -1:
                    main_window.tabs.setTabText(idx, os.path.basename(file_path))
                    
        try:
            import json
            context = {
                "conn_id": self.current_conn_id,
                "db_name": self.schema_combo.currentText()
            }
            context_header = f"-- @hsql_context: {json.dumps(context)}\n"
            
            content = self.editor.toPlainText()
            # If already has context header, replace it
            if content.startswith("-- @hsql_context:"):
                first_newline = content.find("\n")
                if first_newline != -1:
                    content = content[first_newline+1:]
            
            final_content = context_header + content
            
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(final_content)
            main_window = self.window()
            if hasattr(main_window, "statusBar"):
                bar = main_window.statusBar() if callable(main_window.statusBar) else main_window.statusBar
                bar.showMessage(f"Đã lưu: {self.current_file}", 3000)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi lưu file: {e}")

    def open_file(self):
        from PyQt6.QtWidgets import QFileDialog
        import os
        file_path, _ = QFileDialog.getOpenFileName(self, "Mở file SQL", "", "SQL Files (*.sql);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                main_window = self.window()
                file_name = os.path.basename(file_path)
                
                new_console = SqlConsole(main_window)
                new_console.current_conn_id = getattr(self, "current_conn_id", None)
                
                db_name = self.schema_combo.currentText()
                if db_name and db_name != "<schema>":
                    new_console.set_database_context(new_console.current_conn_id, db_name)
                    
                new_console.editor.setPlainText(content)
                new_console.current_file = file_path
                
                # Check for @hsql_context
                import json
                if content.startswith("-- @hsql_context:"):
                    try:
                        first_line = content.split("\n")[0]
                        json_str = first_line.replace("-- @hsql_context:", "").strip()
                        ctx = json.loads(json_str)
                        conn_id = ctx.get("conn_id")
                        db_name = ctx.get("db_name")
                        if conn_id:
                            # Verify connection still exists
                            from components.db_store import get_connection
                            if get_connection(conn_id):
                                new_console.set_database_context(conn_id, db_name)
                    except Exception as e:
                        print(f"Error parsing context: {e}")

                if hasattr(main_window, 'tabs'):
                    idx = main_window.tabs.addTab(new_console, file_name)
                    main_window.tabs.setCurrentIndex(idx)
                
                if hasattr(main_window, "statusBar"):
                    bar = main_window.statusBar() if callable(main_window.statusBar) else main_window.statusBar
                    bar.showMessage(f"Đã mở: {file_path}", 3000)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi mở file: {e}")

    def format_sql(self):
        try:
            import sqlparse
            text = self.editor.toPlainText()
            if not text.strip(): return
            
            formatted = sqlparse.format(text, reindent=True, keyword_case='upper')
            
            if formatted == text:
                return

            cursor = self.editor.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(formatted)
            cursor.endEditBlock()
            
            # Restore cursor position (approximate)
            # cursor.setPosition(min(pos, len(formatted))) 
            # Note: insertText leaves cursor at the end, so we might want to reset it
            self.editor.setTextCursor(cursor)
        except Exception as e:
            print(f"Format error: {e}")

    def toggle_comment(self):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        text = cursor.selectedText()
        if text.startswith("-- "):
            cursor.insertText(text[3:])
        else:
            cursor.insertText("-- " + text)

    def delete_line(self):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

    def extend_selection(self):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        elif len(cursor.selectedText()) == len(cursor.block().text()):
            cursor.select(QTextCursor.SelectionType.Document)
        else:
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        self.editor.setTextCursor(cursor)
