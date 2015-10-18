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

    def __init__(self):
        self.buffers = QSemaphore()
        self.gain = QSemaphore()
        self.claim = QSemaphore()
        self.open = Mutex(False)
        self.start = Mutex(False)
        self.pause = Mutex(False)
        self.condition = QWaitCondition()


class UsbThread(QObject):

    data = Signal(unicode)
    line = Signal(unicode)
    gcode = Signal(unicode)
    pointx = Signal(unicode)
    pointy = Signal(unicode)
    pointz = Signal(unicode)
    freebuffer = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        s = pool.Serials[0].Async
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
        self.ctrl = Control()
        self.points = []
        self.last = [0,0,0]
        self.readThread = QThread()
        self.uploadThread = None
        self.reader = UsbReader(self.pool, self.ctrl)
        self.reader.data.connect(self.data)
        self.reader.position.connect(self.on_position)
        self.reader.control.connect(self.on_data)
        self.reader.freebuffer.connect(self.freebuffer)
        self.readThread.started.connect(self.reader.process)
        self.reader.finished.connect(self.readThread.quit)
        self.readThread.finished.connect(self.readThread.deleteLater)
        self.readThread.finished.connect(self.reader.deleteLater)
        self.readThread.finished.connect(self.on_close)
        self.reader.moveToThread(self.readThread)
        self.uploader = None

    def open(self):
        self.ctrl.open.lock()
        self.ctrl.open.value = True
        self.ctrl.open.unlock()
        self.readThread.start()
        self.on_data("$${}".format(self.eol))

    def close(self):
        if self.pool.Start:
            self.pool.Start = False
            self.stop()
            self.ctrl.claim.release(2)
        self.ctrl.open.lock()
        self.ctrl.open.value = False
        self.ctrl.open.unlock()
        self.ctrl.gain.release(2)

    @Slot()
    def on_close(self):
        self.readThread = None
        while self.ctrl.gain.available():
            self.ctrl.gain.acquire()        
        if self.uploadThread is None:
            self.pool.Thread = None

    def start(self):
        s = self.pool.Serials[self.pool.DualPort]
        if s.Async is None:
            try:
                s.Async = serial.serial_for_url(s.Port)
            except serial.SerialException as e:
                msg = "Error occurred opening port: {}\n"
                Console.PrintError(msg.format(repr(e)))
                self.pool.Start = False
                return
            else:
                msg = "{} opening port {}... done\n"
                Console.PrintLog(msg.format(self.pool.Label, s.Async.port))
        elif not s.Async.is_open:
            s.Async.open()
        self.uploader = UsbUploader(self.pool, self.ctrl)
        if self.pool.DualPort:
            s = self.pool.Serials[1].Async
            self.uploader.sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
            self.uploader.gcode.connect(self.uploader.on_data)
        else:
            self.uploader.gcode.connect(self.on_data)
        self.uploader.control.connect(self.on_data)
        self.uploader.gcode.connect(self.gcode)
        self.uploader.line.connect(self.line)
        self.uploadThread = QThread()
        self.uploadThread.started.connect(self.uploader.process)
        self.uploader.finished.connect(self.uploadThread.quit)
        self.uploadThread.finished.connect(self.uploadThread.deleteLater)
        self.uploadThread.finished.connect(self.uploader.deleteLater)
        self.uploadThread.finished.connect(self.on_stop)
        self.uploader.moveToThread(self.uploadThread)
        self.positions = []
        self.lastposition = [0,0,0]
        if self.pool.ViewObject.Draw:
            self.pool.ViewObject.Positions = []
            self.pool.ViewObject.Proxy.indexPosition = 0
        self.ctrl.start.lock()
        self.ctrl.start.value = True
        self.ctrl.start.unlock()
        self.uploadThread.start()

    def stop(self):
        if self.pool.Pause:
            self.pool.Pause = False
            self.resume()
        self.ctrl.start.lock()
        self.ctrl.start.value = False
        self.ctrl.start.unlock()
        self.ctrl.claim.release(2)

    @Slot()
    def on_stop(self):
        if len(self.positions):
            self.pool.ViewObject.Positions += list(self.positions)
            self.positions = []
        self.uploadThread = None
        while self.ctrl.claim.available():
            self.ctrl.claim.acquire()        
        if self.readThread is None:
            self.pool.Thread = None
        if self.pool.Start:
            self.stoped()

    def stoped(self):
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
    def on_data(self, data):
        try:
            self.sio.write(data + self.eol)
            self.sio.flush()
        except Exception as e:
            msg = "Error occurred in UsbWriter process: {}\n"
            Console.PrintError(msg.format(e))

    @Slot(unicode)
    def on_position(self, line):
        try:
            new = list(self.last)
            for key, value in [l.split(":") for l in line.split(",")]:
                if key == "posx":
                    new[0] = float(value)
                elif key == "posy":
                    new[1] = float(value)
                elif key == "posz":
                    new[2] = float(value)
            self.last = list(new)
            self.pointx.emit(str(new[0]))
            self.pointy.emit(str(new[1]))
            self.pointz.emit(str(new[2]))
            self.positions.append(new)
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
    data = Signal(unicode)
    position = Signal(unicode)
    freebuffer = Signal(unicode)
    control = Signal(unicode)


    def __init__(self, pool, ctrl):
        QObject.__init__(self)
        self.pool = pool
        self.ctrl = ctrl
        s = self.pool.Serials[0].Async
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s), newline=self.eol)

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        port = self.pool.Serials[0].Async.port
        msg = "{} UsbReader thread start on port {}... done\n"
        Console.PrintLog(msg.format(self.pool.Name, port))
        try:
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
                            self.freebuffer.emit(str(b))
                            while self.ctrl.buffers.available() > buffers:
                                self.ctrl.buffers.acquire()
                            while self.ctrl.buffers.available() < buffers:
                                self.ctrl.buffers.release()
                            if self.ctrl.buffers.available() > 0:
                                self.ctrl.claim.release()
                                self.ctrl.gain.acquire()
                            else:
                                self.control.emit("$qr")
                            self.ctrl.open.lock()
                            continue
                        if line.startswith("pos"):
                            self.position.emit(line)
                        if self.ctrl.buffers.available() > 0:
                            self.ctrl.claim.release()
                            self.ctrl.gain.acquire()
                        if self.pool.ViewObject.EchoFilter and line.startswith("tinyg"):
                            self.ctrl.open.lock()
                            continue
                    else:
                        self.ctrl.start.unlock()
                    self.data.emit(line + self.eol)
                self.ctrl.open.lock()
            self.ctrl.open.unlock()
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbReader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, self.pool.Serials[0].Async.port))
        self.finished.emit()


class UsbUploader(QObject):

    finished = Signal()
    line = Signal(unicode)
    gcode = Signal(unicode)
    control = Signal(unicode)

    def __init__(self, pool, ctrl):
        QObject.__init__(self)
        self.pool = pool
        self.ctrl = ctrl
        self.sio = None
        self.port = self.pool.Serials[self.pool.DualPort].Async.port
        self.eol = self.pool.Proxy.getCharEndOfLine(self.pool)

    @Slot(unicode)
    def on_data(self, data):
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
            msg = "{} UsbUploader thread start on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, self.port))
            i = 0
            self.control.emit("$qr")
            self.ctrl.claim.acquire()
            with open(self.pool.UploadFile) as f:
                for line in f:
                    i += 1
                    if not self.ctrl.buffers.tryAcquire():
                        self.control.emit("$qr")
                        self.ctrl.gain.release()
                        self.ctrl.claim.acquire()
                    self.line.emit(str(i))
                    self.gcode.emit(line.strip())
                    self.ctrl.pause.lock()
                    if self.ctrl.pause.value:
                        self.ctrl.condition.wait(self.ctrl.pause)
                        self.ctrl.pause.unlock()
                    else:
                        self.ctrl.pause.unlock()
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
            Console.PrintLog(msg.format(self.pool.Name, self.port))
        if self.pool.DualPort and self.pool.Serials[1].Async.is_open:
            self.pool.Serials[1].Async.close()
            self.pool.Serials[1].Async = None
            msg = "{} closing port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Label, self.port))
        self.finished.emit()
