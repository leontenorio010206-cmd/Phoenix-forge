import re
from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt


class VerilogHighlighter(G.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        keywords = "module endmodule input output inout wire reg logic parameter localparam assign always initial begin end if else case endcase default for while repeat posedge negedge integer generate endgenerate function endfunction task endtask signed unsigned or"
        for pattern, color in ((r"\b(?:" + "|".join(keywords.split()) + r")\b", "#e0a0f7"),
                               (r"\b\d+(?:'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ_]+)?\b", "#ecc079"),
                               (r"\$\w+|`\w+", "#7fc5ea"), (r'"[^"\n]*"', "#91c9a5"),
                               (r"//[^\n]*", "#738ba0")):
            fmt = G.QTextCharFormat()
            fmt.setForeground(G.QColor(color))
            self.rules.append((re.compile(pattern), fmt))
        self.comment_format = G.QTextCharFormat()
        self.comment_format.setForeground(G.QColor("#738ba0"))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)
        self.setCurrentBlockState(0)
        start = 0 if self.previousBlockState() == 1 else text.find("/*")
        while start >= 0:
            end = text.find("*/", start + (0 if self.previousBlockState() == 1 and start == 0 else 2))
            if end < 0:
                self.setCurrentBlockState(1)
                self.setFormat(start, len(text) - start, self.comment_format)
                break
            self.setFormat(start, end + 2 - start, self.comment_format)
            start = text.find("/*", end + 2)


class LineNumbers(W.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return C.QSize(self.editor.number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_numbers(event)


class CodeEditor(W.QPlainTextEdit):
    def __init__(self, name, text, parent=None):
        super().__init__(parent)
        self.name = name
        self.setLineWrapMode(W.QPlainTextEdit.NoWrap)
        font = G.QFont("Consolas", 11)
        font.setStyleHint(G.QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.numbers = LineNumbers(self)
        self.highlighter = VerilogHighlighter(self.document()) if name.lower().endswith((".v", ".sv", ".vh", ".svh")) else None
        self.blockCountChanged.connect(self.update_margin)
        self.updateRequest.connect(self.update_numbers)
        self.cursorPositionChanged.connect(self.highlight_line)
        self.setPlainText(text)
        self.document().setModified(False)
        self.update_margin()
        self.highlight_line()

    def number_width(self):
        return 20 + self.fontMetrics().horizontalAdvance("9") * len(str(max(1, self.blockCount())))

    def update_margin(self, *_):
        self.setViewportMargins(self.number_width(), 0, 0, 0)

    def update_numbers(self, rect, dy):
        if dy:
            self.numbers.scroll(0, dy)
        else:
            self.numbers.update(0, rect.y(), self.numbers.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_margin()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.numbers.setGeometry(C.QRect(rect.left(), rect.top(), self.number_width(), rect.height()))

    def paint_numbers(self, event):
        painter = G.QPainter(self.numbers)
        painter.fillRect(event.rect(), G.QColor("#101a29"))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        while block.isValid() and top <= event.rect().bottom():
            height = round(self.blockBoundingRect(block).height())
            if block.isVisible() and top + height >= event.rect().top():
                painter.setPen(G.QColor("#62768d"))
                painter.drawText(0, top, self.numbers.width() - 8, self.fontMetrics().height(), Qt.AlignRight, str(number + 1))
            top += height
            block = block.next()
            number += 1

    def highlight_line(self):
        selection = W.QTextEdit.ExtraSelection()
        selection.format.setBackground(G.QColor("#16243a"))
        selection.format.setProperty(G.QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def go_to_line(self, line):
        block = self.document().findBlockByNumber(max(0, line - 1))
        if block.isValid():
            self.setTextCursor(G.QTextCursor(block))
            self.centerCursor()
            self.setFocus()

    def search(self, text):
        if self.find(text):
            return True
        cursor = self.textCursor()
        cursor.movePosition(G.QTextCursor.Start)
        self.setTextCursor(cursor)
        return self.find(text)

