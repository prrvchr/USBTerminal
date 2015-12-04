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
""" Grbl Plugin Driver Thread object (with file upload) """
from __future__ import unicode_literals

import io, serial, Queue
import serial
from PySide.QtCore import QThread, QObject, QWaitCondition, QSemaphore, QMutex, Signal, Slot
from FreeCAD import Console


class Mutex(QMutex):

    def __init__(self, value):
        QMutex.__init__(self)
        self.value = value


class Control():

    def __init__(self, buffers):
        self.buffers = QSemaphore(buffers)
        self.commands = Queue.Queue()
        self.claim = QSemaphore()
        self.open = Mutex(True)
        self.start = Mutex(False)
        self.pause = Mutex(False)
        self.condition = QWaitCondition()


class UsbThread(QObject):

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.maxbuffers = 127
        self.ctrl = Control(self.maxbuffers)
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        s = io.BufferedWriter(self.pool.Serials[0].Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)
        self.thread = QThread(self)
        self.reader = UsbReader(self.pool, self.ctrl)
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
        if self.pool.Start:
            self.stop()
        self.ctrl.open.lock()
        self.ctrl.open.value = False
        self.ctrl.open.unlock()

    @Slot()
    def on_close(self):
        self.pool.Serials[0].Open = False
        self.pool.Serials[0].purgeTouched()
        if self.pool.Start:
            self.pool.Start = False

    def start(self):
        self.uploadthread = QThread()
        self.uploader = UsbUploader(self.pool, self.ctrl, self.sio)
        self.uploader.moveToThread(self.uploadthread)
        self.uploader.console.connect(self.on_console)
        self.uploadthread.started.connect(self.uploader.process)
        # Signal the thread to quit, i.e. shut down.
        self.uploader.finished.connect(self.uploadthread.quit)
        # Signal for deletion
        self.uploader.finished.connect(self.uploader.deleteLater)
        # Cause the thread to be deleted only after it has fully shut down.
        self.uploadthread.finished.connect(self.uploadthread.deleteLater)
        self.uploadthread.finished.connect(self.on_stop)
        self.ctrl.start.lock()
        self.ctrl.start.value = True
        self.ctrl.start.unlock()
        self.uploadthread.start()

    def stop(self):
        self.ctrl.start.lock()
        self.ctrl.start.value = False
        self.ctrl.start.unlock()
        if self.pool.Pause:
            self.resume()
        while self.ctrl.buffers.available() < self.maxbuffers:
            self.ctrl.buffers.release()

    @Slot()
    def on_stop(self):
        if self.pool.Pause:
            self.pool.Pause = False
        if self.pool.Start:
            self.pool.Start = False

    def pause(self):
        self.ctrl.pause.lock()
        self.ctrl.pause.value = True
        self.ctrl.pause.unlock()

    def resume(self):
        self.ctrl.pause.lock()
        self.ctrl.pause.value = False
        self.ctrl.pause.unlock()
        self.ctrl.condition.wakeAll()

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
    buffers = Signal(unicode)
    settings = Signal(unicode)

    def __init__(self, pool, ctrl):
        QObject.__init__(self)
        self.pool = pool
        self.ctrl = ctrl
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        s = io.BufferedReader(self.pool.Serials[0].Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)
        self.sendsetting = False

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            p = self.pool.Serials[0].Async.port
            msg = "{} UsbReader thread start on port {}... done\n".format(self.pool.Name, p)
            self.console.emit(0, msg)
            self.ctrl.open.lock()
            while self.ctrl.open.value:
                self.ctrl.open.unlock()
                line = self.sio.readline()
                if len(line):
                    line = line.strip()
                    if not self.ctrl.commands.empty():
                        if line.startswith("ok"):
                            self.ctrl.buffers.release(self.ctrl.commands.get())
                            self.ctrl.commands.task_done()
                            self.buffers.emit(str(self.ctrl.buffers.available()))
                            if self.ctrl.buffers.available():
                                self.ctrl.claim.tryAcquire(1, self.pool.Timeout)
                        elif line.startswith("error"):
                            self.pool.Pause = True
                    if line.startswith("$"):
                        self.sendsetting = True
                        self.settings.emit(line)
                    elif line.startswith("ok") and self.sendsetting:
                        self.sendsetting = False
                        self.settings.emit("endofsettings")
                    self.read.emit(line + self.eol)
                self.ctrl.open.lock()
            self.ctrl.open.unlock()
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n".format(e)
            self.console.emit(3, msg)
        else:
            msg = "{} UsbReader thread stop on port {}... done\n".format(self.pool.Name, p)
            self.console.emit(0, msg)
        self.finished.emit()


class UsbUploader(QObject):

    finished = Signal()
    console = Signal(int, unicode)
    line = Signal(unicode)
    gcode = Signal(unicode)

    def __init__(self, pool, ctrl, sio):
        QObject.__init__(self)
        self.pool = pool
        self.ctrl = ctrl
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        self.sio = sio
        self.gcode.connect(self.on_gcode)

    @Slot(unicode)
    def on_gcode(self, data):
        try:
            self.sio.write(data + self.eol)
            self.sio.flush()
        except Exception as e:
            msg = "Error occurred in UsbUploaderWriter process: {}\n".format(e)
            self.console.emit(3, msg)

    @Slot()
    def process(self):
        """ Loop and copy file -> PySerial """
        try:
            s = self.pool.Serials[self.pool.DualPort].Async.port
            msg = "{} UsbUploader thread start on port {}... done\n".format(self.pool.Name, s)
            self.console.emit(0, msg)
            i = 0
            with open(self.pool.UploadFile) as f:
                for line in f:
                    self.ctrl.pause.lock()
                    if self.ctrl.pause.value:
                        self.ctrl.condition.wait(self.ctrl.pause)
                        self.ctrl.pause.unlock()
                    else:
                        self.ctrl.pause.unlock()
                    i += 1
                    l = len(line + self.eol)
                    if not self.ctrl.buffers.tryAcquire(l):
                        self.ctrl.claim.release()
                        self.ctrl.buffers.acquire(l)
                    self.ctrl.commands.put(l)
                    self.line.emit(str(i))
                    self.gcode.emit(line.strip())
                    self.ctrl.start.lock()
                    if not self.ctrl.start.value:
                        self.ctrl.start.unlock()
                        break
                    else:
                        self.ctrl.start.unlock()
            self.ctrl.commands.join()
        except Exception as e:
            msg = "Error occurred in UsbUploader thread process: {}\n".format(e)
            self.console.emit(3, msg)
        else:
            msg = "{} UsbUploader thread stop on port {}... done\n".format(self.pool.Name, s)
            self.console.emit(0, msg)
        self.finished.emit()
