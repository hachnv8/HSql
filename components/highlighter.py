from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import QRegularExpression

class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        # Islands Dark Theme Colors from .icls
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#cf8e6d"))
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6aab73"))
        
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#2aacb8"))
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#7a7e85"))
        
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#56a8f5"))

        # SQL Keywords
        keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "INTO", "UPDATE", "DELETE", 
            "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "GROUP BY", "ORDER BY", 
            "HAVING", "LIMIT", "OFFSET", "CREATE", "ALTER", "DROP", "TABLE", 
            "DATABASE", "INDEX", "VIEW", "AS", "AND", "OR", "NOT", "IS", "NULL", 
            "PRIMARY KEY", "FOREIGN KEY", "REFERENCES", "SET", "VALUES", "EXISTS",
            "ASC", "DESC", "IN", "LIKE", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE", "END"
        ]

        for word in keywords:
            parts = word.split()
            if len(parts) == 1:
                pattern = QRegularExpression(rf"\b{word}\b", QRegularExpression.PatternOption.CaseInsensitiveOption)
                self.highlightingRules.append((pattern, keyword_format))
            else:
                # Handle multi-word keywords like GROUP BY
                pattern_str = r"\b" + r"\s+".join(parts) + r"\b"
                pattern = QRegularExpression(pattern_str, QRegularExpression.PatternOption.CaseInsensitiveOption)
                self.highlightingRules.append((pattern, keyword_format))

        # Functions (e.g. COUNT, SUM, MAX, MIN, AVG)
        functions = ["COUNT", "SUM", "MAX", "MIN", "AVG", "COALESCE", "IFNULL", "CAST", "CONVERT"]
        for word in functions:
            pattern = QRegularExpression(rf"\b{word}\b(?=\s*\()", QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.highlightingRules.append((pattern, function_format))

        # Numbers
        self.highlightingRules.append((QRegularExpression(r"\b\d+\b"), number_format))
        self.highlightingRules.append((QRegularExpression(r"\b\d+\.\d+\b"), number_format))

        # Strings (Single quotes and double quotes)
        self.highlightingRules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        self.highlightingRules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlightingRules.append((QRegularExpression(r"`[^`]*`"), string_format))

        # Single-line comment
        self.highlightingRules.append((QRegularExpression(r"--[^\n]*"), comment_format))
        self.highlightingRules.append((QRegularExpression(r"#[^\n]*"), comment_format))

        # Multi-line comment
        self.multiLineCommentFormat = comment_format
        self.commentStartExpression = QRegularExpression(r"/\*")
        self.commentEndExpression = QRegularExpression(r"\*/")

    def highlightBlock(self, text):
        # Thiết lập màu mặc định cho toàn bộ text (nếu không có rule nào match)
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#bcbec4"))
        self.setFormat(0, len(text), default_format)

        for pattern, format in self.highlightingRules:
            matchIterator = pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = text.find("/*")

        while startIndex >= 0:
            match = self.commentEndExpression.match(text, startIndex)
            endIndex = match.capturedStart()
            commentLength = 0
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + match.capturedLength()
            
            self.setFormat(startIndex, commentLength, self.multiLineCommentFormat)
            startIndex = text.find("/*", startIndex + commentLength)
