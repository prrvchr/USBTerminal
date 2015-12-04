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
from PySide.QtGui import QTextCursor, QWidget, QVBoxLayout
from PySide.QtCore import Qt, Signal, Slot, QThreadPool, QRunnable, QObject
from FreeCAD import Console
import FreeCADGui
import io


class TextEditWidget(QPlainTextEdit):

    command = Signal(unicode)

    def __init__(self):
        QPlainTextEdit.__init__(self)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)
        self.history = []

    def getCommand(self):
        doc = self.document()
        line = doc.findBlockByLineNumber(doc.lineCount() - 1).text()
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
        QPlainTextEdit.keyPressEvent(self, event)

    def mouseReleaseEvent(self, event):
        QPlainTextEdit.mouseReleaseEvent(self, event)
        if self.textCursor().atEnd() or self.textCursor().hasSelection():
            return
        self.moveCursor(QTextCursor.End)


class TerminalDock(QDockWidget):

    def __init__(self, pool):
        QDockWidget.__init__(self)
        self.port = pool.Proxy.getTerminalPort(pool)
        self.setWindowTitle("{} terminal".format(pool.Label))
        self.setObjectName("{}-{}".format(pool.Document.Name, pool.Name))
        thread = TerminalThread(pool, self.port)
        thread.output.connect(self.on_output)
        if pool.ViewObject.DualView:
            terminal = QSplitter(Qt.Vertical)
            self.output = QPlainTextEdit()
            terminal.addWidget(self.output)
            textedit = TextEditWidget()
            textedit.command.connect(thread.on_command)
            terminal.addWidget(textedit)
            self.setWidget(terminal)
        else:
            terminal = QWidget(self)
            terminal.setLayout(QVBoxLayout())
            terminal.layout().setContentsMargins(0, 0, 0, 0)
            self.output = TextEditWidget()
            self.output.command.connect(thread.on_command)
            terminal.layout().addWidget(self.output)
            self.setWidget(terminal)
        QThreadPool.globalInstance().start(thread)

    @Slot(unicode)
    def on_output(self, data):
        self.output.insertPlainText(data)
        self.output.ensureCursorVisible()

    def closeEvent(self, event):
        self.port.Open = False
        QThreadPool.globalInstance().waitForDone()
        # Signalling PySerialModel of close event
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedPySerial.emit(self.port)


class TerminalThread(QObject, QRunnable):

    output = Signal(unicode)
    
    def __init__(self, pool, port):
        QObject.__init__(self)
        QRunnable.__init__(self)
        self.pool = pool
        self.port = port
        self.serial = port.Proxy.PySerial
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        s = io.BufferedRWPair(self.serial, self.serial)
        self.sio = io.TextIOWrapper(s, newline=self.eol)

    def on_command(self, command):
        try:
            self.sio.write(command + self.eol)
            self.sio.flush()
        except Exception as e:
            msg = "Error occurred in TerminalWriter process: {}\n"
            Console.PrintError(msg.format(e))

    def run(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            msg = "{} UsbReader thread start on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, self.serial.name))
            while self.port.Open:
                line = self.sio.readline()
                if len(line):
                    self.output.emit(line)
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbReader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, self.serial.name))
        finally:
            self.serial.close()
            msg = "{} closing port {}... done\n"
            Console.PrintLog(msg.format(self.port.Label, self.serial.name))
