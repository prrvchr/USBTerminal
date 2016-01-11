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

from PySide import QtCore, QtGui


class TextEditWidget(QtGui.QPlainTextEdit):

    command = QtCore.Signal(unicode)

    def __init__(self):
        QtGui.QPlainTextEdit.__init__(self)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)
        self.history = []

    def getCommand(self):
        line = self.document().lineCount() - 2
        return self.document().findBlockByLineNumber(line).text()

    def setCommand(self, command):
        self.moveCursor(QtGui.QTextCursor.End)
        self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
        self.textCursor().removeSelectedText()
        self.textCursor().insertText(command)
        self.moveCursor(QtGui.QTextCursor.End)

    def runCommand(self):
        command = self.getCommand()
        self.addToHistory(command)
        self.command.emit(command)

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
            history_len = len(self.history)
            self.history_index = min(history_len, self.history_index + 1)
            if self.history_index < history_len:
                return self.history[self.history_index]
        return ""

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Home:
            self.moveCursor(QtGui.QTextCursor.StartOfLine)
            return
        elif e.key() == QtCore.Qt.Key_PageUp:
            return
        elif e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace) and \
             self.textCursor().columnNumber() == 0:
            return
        elif e.key() == QtCore.Qt.Key_Up:
            self.setCommand(self.getPrevHistoryEntry())
            return
        elif e.key() == QtCore.Qt.Key_Down:
            self.setCommand(self.getNextHistoryEntry())
            return
        elif e.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return) and \
             not self.textCursor().atEnd():
            self.moveCursor(QtGui.QTextCursor.End)        
        QtGui.QPlainTextEdit.keyPressEvent(self, e)
        if e.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.runCommand()
 
    def mouseReleaseEvent(self, e):
        QtGui.QPlainTextEdit.mouseReleaseEvent(self, e)
        if self.textCursor().atEnd() or self.textCursor().hasSelection():
            return
        self.moveCursor(QtGui.QTextCursor.End)


class TerminalDock(QtGui.QDockWidget):

    def __init__(self, state):
        QtGui.QDockWidget.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.stop = True
        self.state = state
        obj = state.machine().obj
        self.setWindowTitle("{} terminal on {}".format(obj.Label, state.obj.Label))
        self.setObjectName("{}-{}".format(obj.Document.Name, obj.Name))
        state.serialRead.connect(self.on_output)
        state.machine().finished.connect(self.finished)
        if obj.ViewObject.DualView:
            terminal = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.output = QtGui.QPlainTextEdit()
            terminal.addWidget(self.output)
            textedit = TextEditWidget()
            textedit.command.connect(state.serialWrite)
            terminal.addWidget(textedit)
        else:
            terminal = QtGui.QWidget(self)
            terminal.setLayout(QtGui.QVBoxLayout())
            terminal.layout().setContentsMargins(0, 0, 0, 0)
            self.output = TextEditWidget()
            self.output.command.connect(state.serialWrite)
            terminal.layout().addWidget(self.output)
        self.setWidget(terminal)

    @QtCore.Slot(unicode)
    def on_output(self, data):
        self.output.insertPlainText(data)
        self.output.ensureCursorVisible()

    @QtCore.Slot()    
    def finished(self):
        self.stop = False
        self.close()

    def closeEvent(self, e):
        if self.stop and self.state.machine().isRunning():
            self.state.machine().stop()
