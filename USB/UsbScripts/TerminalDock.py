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

from PySide.QtGui import QDockWidget, QSplitter, QPlainTextEdit, QTextOption, QTextCursor
from PySide.QtCore import Qt, Signal, Slot


class InPutTextEdit(QPlainTextEdit):

    data = Signal(unicode)

    def __init__(self):
        QPlainTextEdit.__init__(self)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)
        self.history = []

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

    def __init__(self):
        QPlainTextEdit.__init__(self)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)

    @Slot(unicode)
    def on_data(self, data):
        self.insertPlainText(data)
        self.ensureCursorVisible()


class TerminalWidget(OutPutTextEdit, InPutTextEdit):

    def __init__(self, driver):
        InPutTextEdit.__init__(self)
        driver.data.connect(self.on_data)
        self.data.connect(driver.on_data)


class DualTerminalWidget(QSplitter):
    
    def __init__(self, driver):
        QSplitter.__init__(self, Qt.Vertical)
        outputText = OutPutTextEdit()
        self.addWidget(outputText)
        inputText = InPutTextEdit()
        self.addWidget(inputText)
        driver.data.connect(outputText.on_data)
        inputText.data.connect(driver.on_data)


class TerminalDock(QDockWidget):

    def __init__(self, pool, driver):
        QDockWidget.__init__(self)
        self.setObjectName("{}-{}".format(pool.Document.Name, pool.Name))
        self.setWindowTitle("{} terminal".format(pool.Label))
        self.driver = driver
        if pool.DualView:
            terminal = DualTerminalWidget(driver)
        else:
            terminal = TerminalWidget(driver)
        self.setWidget(terminal)
        eol = pool.Proxy.getCharEndOfLine(pool)
        driver.data.emit("Now, you are connected{}".format(eol))
