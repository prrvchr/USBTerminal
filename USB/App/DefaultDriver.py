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
""" Minimal Default USB Driver Thread object (no dual endpoint, no upload) """
from __future__ import unicode_literals

import io
from PySide.QtCore import QRunnable, QThread, QObject, QMutex, Signal, Slot
from FreeCAD import Console


class SerialThread(QRunnable):

    def __init__(self, port):
        QRunnable.__init__(self)
        pool = port.InList[0]
        self.port = port.Async.port
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        s = io.BufferedReader(port.Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)

    def run(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            p = self.pool.Serials[0].Async.port
            msg = "{} UsbReader thread start on port {}... done\n".format(self.pool.Name, p)
            self.console.emit(0, msg)
            self.run.lock()
            while self.run.value:
                self.run.unlock()
                line = self.sio.readline()
                if len(line):
                    line = line.strip()
                    self.read.emit(line + self.eol)
                self.run.lock()
            self.run.unlock()
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n".format(e)
            self.console.emit(3, msg)
        else:
            msg = "{} UsbReader thread stop on port {}... done\n".format(self.pool.Name, p)
            self.console.emit(0, msg)
        self.finished.emit()
            

    @Slot(int, unicode)
    def on_console(self, level, msg):
        if level == 0:
            Console.PrintLog(msg)
        elif level == 1:
            Console.PrintMessage(msg)
        elif level == 2:
            Console.PrintWarning(msg)
        elif level == 3:
            Console.PrintError(msg)


class Mutex(QMutex):
    
    def __init__(self, value):
        QMutex.__init__(self)
        self.value = value


class UsbThread(QObject):

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.run = Mutex(True)
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        s = io.BufferedWriter(self.pool.Serials[0].Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)
        self.thread = QThread(self)
        self.reader = UsbReader(self.pool, self.run)
        self.reader.moveToThread(self.thread)
        self.reader.console.connect(self.on_console)
        self.thread.started.connect(self.reader.process)
        # Signal the thread to quit, i.e. shut down.
        self.reader.finished.connect(self.thread.quit)
        # Signal for deletion.
        self.reader.finished.connect(self.reader.deleteLater)
        # Cause the thread to be deleted only after it has fully shut down.
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_close)
        self.thread.start()

    @Slot(int, unicode)
    def on_console(self, level, msg):
        if level == 0:
            Console.PrintLog(msg)
        elif level == 1:
            Console.PrintMessage(msg)
        elif level == 2:
            Console.PrintWarning(msg)
        elif level == 3:
            Console.PrintError(msg)

    def close(self):
        self.run.lock()
        self.run.value = False
        self.run.unlock()

    @Slot()
    def on_close(self):
        self.pool.Serials[0].Open = False
        self.pool.Serials[0].purgeTouched()

    def start(self):
        self.pool.Start = False

    def stop(self):
        NotImplemented

    def pause(self):
        self.pool.Pause = False

    def resume(self):
        NotImplemented

    @Slot(unicode)
    def on_write(self, data):
        try:
            self.sio.write(data + self.eol)
            self.sio.flush()
        except Exception as e:
            msg = "Error occurred in UsbWriter process: {}\n".format(e)
            self.on_console(3, msg)


class UsbReader(QObject):

    finished = Signal()
    console = Signal(int, unicode)
    read = Signal(unicode)

    def __init__(self, pool, run):
        QObject.__init__(self)
        self.pool = pool
        self.run = run
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        s = io.BufferedReader(self.pool.Serials[0].Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            p = self.pool.Serials[0].Async.port
            msg = "{} UsbReader thread start on port {}... done\n".format(self.pool.Name, p)
            self.console.emit(0, msg)
            self.run.lock()
            while self.run.value:
                self.run.unlock()
                line = self.sio.readline()
                if len(line):
                    line = line.strip()
                    self.read.emit(line + self.eol)
                self.run.lock()
            self.run.unlock()
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n".format(e)
            self.console.emit(3, msg)
        else:
            msg = "{} UsbReader thread stop on port {}... done\n".format(self.pool.Name, p)
            self.console.emit(0, msg)
        self.finished.emit()
            