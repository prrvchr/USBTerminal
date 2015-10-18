# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 Pierre Vacher <prrvchr@gmail.com>                  *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
""" GUI Terminal Dock object """
from __future__ import unicode_literals

from PySide.QtGui import QDockWidget, QSplitter, QPlainTextEdit, QTextOption
from PySide.QtGui import QTextCursor, QWidget, QLabel, QStatusBar, QVBoxLayout
from PySide.QtCore import Qt, Signal, Slot


class InPutTextEdit(QPlainTextEdit):

    data = Signal(unicode)

    def __init__(self, pool):
        QPlainTextEdit.__init__(self)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)
        self.history = []
        self.data.connect(pool.Thread.on_data)

    def getCommand(self):
        doc = self.document()
        line = doc.findBlockByLineNumber(doc.lineCount() - 1).text()
        line = line.strip()
        return line

    def setCommand(self, command):
        if self.getCommand() == command:
            return
        self.moveCursor(QTextCursor.End)
        self.moveCursor(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        self.textCursor().removeSelectedText()
        self.textCursor().insertText(command)
        self.moveCursor(QTextCursor.End)

    def runCommand(self):
        command = self.getCommand()
        self.addToHistory(command)
        self.data.emit(command)

    def getHistory(self):
        return self.history

    def setHisory(self, history):
        self.history = history

    def addToHistory(self, command):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = len(self.history)

    def getPrevHistoryEntry(self):
        if self.history:
            self.history_index = max(0, self.history_index - 1)
            return self.history[self.history_index]
        return ""

    def getNextHistoryEntry(self):
        if self.history:
            hist_len = len(self.history)
            self.history_index = min(hist_len, self.history_index + 1)
            if self.history_index < hist_len:
                return self.history[self.history_index]
        return ""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            if self.textCursor().atEnd():
                self.runCommand()
            else:
                self.moveCursor(QTextCursor.End)
                return
        elif event.key() == Qt.Key_Home:
            self.moveCursor(QTextCursor.StartOfLine)
            return
        elif event.key() == Qt.Key_PageUp:
            return
        elif event.key() in (Qt.Key_Left, Qt.Key_Backspace):
            if self.textCursor().columnNumber() == 0:
                return
        elif event.key() == Qt.Key_Up:
            self.setCommand(self.getPrevHistoryEntry())
            return
        elif event.key() == Qt.Key_Down:
            self.setCommand(self.getNextHistoryEntry())
            return
        super(InPutTextEdit, self).keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        super(InPutTextEdit, self).mouseReleaseEvent(event)
        if self.textCursor().atEnd() or self.textCursor().hasSelection():
            return
        self.moveCursor(QTextCursor.End)

    @Slot(unicode)
    def on_echo(self, data):
        self.insertPlainText(data)
        self.ensureCursorVisible()
        self.data.emit(data.strip())


class OutPutTextEdit(QPlainTextEdit):

    def __init__(self, pool):
        QPlainTextEdit.__init__(self)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)
        pool.Thread.data.connect(self.on_data)

    @Slot(unicode)
    def on_data(self, data):
        self.insertPlainText(data)
        self.ensureCursorVisible()


class TextEditWidget(OutPutTextEdit, InPutTextEdit):

    def __init__(self, pool):
        InPutTextEdit.__init__(self, pool)
        pool.Thread.data.connect(self.on_data)


class TerminalWidget(QWidget):

    def __init__(self, pool):
        QWidget.__init__(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        textEdit = TextEditWidget(pool)
        layout.addWidget(textEdit)
        bar = StatusBar(pool)
        layout.addWidget(bar)        


class DualTerminalWidget(QSplitter):

    def __init__(self, pool):
        QSplitter.__init__(self, Qt.Vertical)
        outputText = OutPutTextEdit(pool)
        self.addWidget(outputText)
        inputText = InPutTextEdit(pool)
        self.addWidget(inputText)
        bar = StatusBar(pool)
        self.addWidget(bar)


class StatusBar(QStatusBar):

    def __init__(self, pool):
        QStatusBar.__init__(self)
        self.addWidget(QLabel("Line:"))
        lineLabel = QLabel()
        self.addWidget(lineLabel)
        pool.Thread.line.connect(lineLabel.setText) 
        self.addWidget(QLabel("GCode:"))
        gcodeLabel = QLabel()
        self.addWidget(gcodeLabel, 1)
        pool.Thread.gcode.connect(gcodeLabel.setText)
        self.addPermanentWidget(QLabel("X:"))
        pointxLabel = QLabel()
        self.addPermanentWidget(pointxLabel)
        pool.Thread.pointx.connect(pointxLabel.setText)
        self.addPermanentWidget(QLabel("Y:"))
        pointyLabel = QLabel()
        self.addPermanentWidget(pointyLabel)
        pool.Thread.pointy.connect(pointyLabel.setText)
        self.addPermanentWidget(QLabel("Z:"))
        pointzLabel = QLabel()
        self.addPermanentWidget(pointzLabel, 1)
        pool.Thread.pointz.connect(pointzLabel.setText)
        self.addPermanentWidget(QLabel("Buffers:"))
        bufferLabel = QLabel()
        self.addPermanentWidget(bufferLabel)
        pool.Thread.freebuffer.connect(bufferLabel.setText)        
 

class TerminalDock(QDockWidget):

    def __init__(self, pool):
        QDockWidget.__init__(self)
        self.setObjectName("{}-{}".format(pool.Document.Name, pool.Name))
        self.setWindowTitle("{} terminal".format(pool.Label))
        if pool.ViewObject.DualView:
            terminal = DualTerminalWidget(pool)
        else:
            terminal = TerminalWidget(pool)
        self.setWidget(terminal)
        eol = pool.Proxy.getCharEndOfLine(pool)
        pool.Thread.data.emit("Now, you are connected{}".format(eol))
