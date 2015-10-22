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
""" TinyG2 Plugin Driver Thread object (with dual endpoint and file upload) """
from __future__ import unicode_literals

import io
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
        self.claim = QSemaphore()
        self.open = Mutex(True)
        self.start = Mutex(False)
        self.pause = Mutex(False)
        self.condition = QWaitCondition()


class UsbThread(QObject):

    pointx = Signal(unicode)
    pointy = Signal(unicode)
    pointz = Signal(unicode)
    vel = Signal(unicode)
    feed = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.maxbuffers = 28
        self.pool = pool
        b = self.maxbuffers - self.pool.Buffers if self.pool.Buffers < self.maxbuffers else 0
        self.ctrl = Control(b)
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        s = io.BufferedWriter(self.pool.Asyncs[0].Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)
        self.thread = QThread(self)
        self.reader = UsbReader(self.pool, self.ctrl)
        self.reader.moveToThread(self.thread)
        self.thread.started.connect(self.reader.process)
        self.reader.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.reader.deleteLater)
        self.thread.finished.connect(self.on_close)
        self.reader.position.connect(self.on_position)
        self.reader.claimbuffer.connect(self.on_write)
        self.thread.start()

    def close(self):
        if self.pool.Start:
            self.stop()
        self.ctrl.open.lock()
        self.ctrl.open.value = False
        self.ctrl.open.unlock()
        if not self.ctrl.claim.available():
            self.ctrl.claim.release()

    @Slot()
    def on_close(self):
        self.pool.Asyncs[0].Open = False
        self.pool.Asyncs[0].purgeTouched()
        if self.pool.Start:
            self.pool.Start = False

    def start(self):
        if self.pool.DualPort:
            s = self.pool.Asyncs[1]
            if not s.Async.is_open:
                s.Open = True
                if not s.Open:
                    self.pool.Start = False
                    return
        self.uploadthread = QThread()
        self.uploader = UsbUploader(self.pool, self.ctrl, self.sio)
        self.uploader.moveToThread(self.uploadthread)
        self.uploadthread.started.connect(self.uploader.process)
        self.uploader.finished.connect(self.uploadthread.quit)
        self.uploadthread.finished.connect(self.uploadthread.deleteLater)
        self.uploadthread.finished.connect(self.uploader.deleteLater)
        self.uploadthread.finished.connect(self.on_stop)
        self.uploader.claimbuffer.connect(self.on_write)
        self.positions = []
        self.last = [0,0,0]
        if self.pool.ViewObject.Draw:
            self.pool.ViewObject.Positions = []
            self.pool.ViewObject.Proxy.indexPosition = 0
        self.ctrl.start.lock()
        self.ctrl.start.value = True
        self.ctrl.start.unlock()
        self.uploadthread.start()

    def stop(self):
        self.ctrl.start.lock()
        self.ctrl.start.value = False
        self.ctrl.start.unlock()
        if not self.ctrl.buffers.available():
            self.ctrl.buffers.release()
        if not self.ctrl.claim.available():
            self.ctrl.claim.release()
        if self.pool.Pause:
            self.resume()

    @Slot()
    def on_stop(self):
        while self.ctrl.claim.available():
            self.ctrl.claim.acquire()
        if len(self.positions):
            self.pool.ViewObject.Positions += list(self.positions)
            self.positions = []
        if self.pool.DualPort:
            self.pool.Asyncs[1].Open = False
            self.pool.Asyncs[1].purgeTouched()
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
            msg = "Error occurred in UsbWriter process: {}\n"
            Console.PrintError(msg.format(e))

    @Slot(unicode)
    def on_position(self, line):
        try:
            pos = list(self.last)
            for key, value in [l.split(":") for l in line.split(",")]:
                if key == "posx":
                    pos[0] = float(value)
                elif key == "posy":
                    pos[1] = float(value)
                elif key == "posz":
                    pos[2] = float(value)
                elif key == "vel":
                    self.vel.emit(str(value))
                elif key == "feed":
                    self.feed.emit(str(value))
            self.last = list(pos)
            self.pointx.emit(str(pos[0]))
            self.pointy.emit(str(pos[1]))
            self.pointz.emit(str(pos[2]))
            self.positions.append(pos)
            if not self.pool.ViewObject.Draw:
                return
            if len(self.positions) < self.pool.ViewObject.Buffers:
                return
            self.pool.ViewObject.Positions += list(self.positions)
            self.positions = []
        except Exception as e:
            msg = "Error occurred in ViewCrtl process: {}\n"
            Console.PrintError(msg.format(e))


class UsbReader(QObject):

    finished = Signal()
    read = Signal(unicode)
    position = Signal(unicode)
    buffers = Signal(unicode)
    claimbuffer = Signal(unicode)
    settings = Signal(unicode)

    def __init__(self, pool, ctrl):
        QObject.__init__(self)
        self.pool = pool
        self.ctrl = ctrl
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        s = io.BufferedReader(self.pool.Asyncs[0].Async)
        self.sio = io.TextIOWrapper(s, newline = self.eol)
        self.sendsetting = False

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            p = self.pool.Asyncs[0].Async.port
            msg = "{} UsbReader thread start on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, p))
            self.ctrl.open.lock()
            while self.ctrl.open.value:
                self.ctrl.open.unlock()
                line = self.sio.readline()
                if len(line):
                    line = line.strip()
                    self.ctrl.start.lock()
                    if self.ctrl.start.value:
                        self.ctrl.start.unlock()
                        if line.startswith("qr:"):
                            b = int(line.split(":")[-1])
                            buffers = b - self.pool.Buffers\
                                if b > self.pool.Buffers else 0
                            self.buffers.emit(str(b))
                            if self.ctrl.buffers.available() > buffers:
                                self.ctrl.buffers.acquire\
                                    (self.ctrl.buffers.available() - buffers)
                            elif self.ctrl.buffers.available() < buffers:
                                self.ctrl.buffers.release\
                                    (buffers - self.ctrl.buffers.available())
                            if self.ctrl.buffers.available():
                                self.ctrl.claim.acquire()
                            else:
                                self.claimbuffer.emit("$qr")
                            if self.pool.ViewObject.EchoFilter:
                                self.ctrl.open.lock()
                                continue
                        elif line.startswith("tinyg") and not self.sendsetting\
                             and self.pool.ViewObject.EchoFilter:
                            self.ctrl.open.lock()
                            continue
                        elif line.startswith("pos"):
                            self.position.emit(line)
                    else:
                        self.ctrl.start.unlock()
                    if line.startswith("["):
                        self.sendsetting = True
                        self.settings.emit(line)
                    elif line.startswith("tinyg") and self.sendsetting:
                        self.sendsetting = False
                        self.settings.emit("eol")
                    self.read.emit(line + self.eol)
                self.ctrl.open.lock()
            self.ctrl.open.unlock()
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbReader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, p))
        self.finished.emit()


class UsbUploader(QObject):

    finished = Signal()
    line = Signal(unicode)
    gcode = Signal(unicode)
    claimbuffer = Signal(unicode)

    def __init__(self, pool, ctrl, sio):
        QObject.__init__(self)
        self.pool = pool
        self.ctrl = ctrl
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        if self.pool.DualPort:
            s = io.BufferedWriter(self.pool.Asyncs[1].Async)
            self.sio = io.TextIOWrapper(s, newline = self.eol)
        else:
            self.sio = sio
        self.gcode.connect(self.on_gcode)

    @Slot(unicode)
    def on_gcode(self, data):
        try:
            self.sio.write(data + self.eol)
            self.sio.flush()
        except Exception as e:
            msg = "Error occurred in UsbUploaderWriter process: {}\n"
            Console.PrintError(msg.format(e))

    @Slot()
    def process(self):
        """ Loop and copy file -> PySerial """
        try:
            s = self.pool.Asyncs[self.pool.DualPort].Async.port
            msg = "{} UsbUploader thread start on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, s))
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
                    if not self.ctrl.buffers.tryAcquire():
                        self.claimbuffer.emit("$qr")
                        self.ctrl.claim.release()
                        self.ctrl.buffers.acquire()
                    self.line.emit(str(i))
                    self.gcode.emit(line.strip())
                    self.ctrl.start.lock()
                    if not self.ctrl.start.value:
                        self.ctrl.start.unlock()
                        break
                    else:
                        self.ctrl.start.unlock()
        except Exception as e:
            msg = "Error occurred in UsbUploader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbUploader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, s))
        self.finished.emit()
