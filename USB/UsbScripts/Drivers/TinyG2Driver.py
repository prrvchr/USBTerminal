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
""" TinyG2 Driver Thread object (with dual endpoint, file upload) """
from __future__ import unicode_literals

import io
from PySide.QtCore import QThread, QSemaphore, QWaitCondition, QMutex, QObject, Signal, Slot
from FreeCAD import Console


class Buffers():

    def __init__(self):
        self.free = QSemaphore()
        self.gain = QSemaphore()
        self.claim = QSemaphore()

class UsbDriver(QObject):

    data = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        s = pool.Serials[0]
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
        self.mutex = QMutex()
        self.toggle = QWaitCondition()
        self.buffers = Buffers()

    def open(self):
        thread = QThread()
        self.reader = UsbReader(self.pool, self.buffers)
        self.reader.data.connect(self.data)
        self.reader.on_data.connect(self.on_data)
        thread.started.connect(self.reader.process)
        self.reader.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self.reader.deleteLater)
        thread.finished.connect(self.on_close)        
        self.reader.moveToThread(thread)
        thread.start()
        self.thread = [thread]
        self.reader.run = True

    def close(self):
        if self.pool.Pause:
            self.resume()
            self.pool.Pause = False        
        if self.pool.Start:
            self.stop()
            self.pool.Start = False 
        self.reader.run = False

    @Slot()
    def on_close(self):
        for s in self.pool.Serials:
            if s.is_open:
                s.close()
        ports = [s.port for s in self.pool.Serials]
        msg = "{} closing port {}... done\n"
        Console.PrintLog(msg.format(self.pool.Name, ports))                
        self.pool.Serials = None

    def start(self):
        if self.pool.Serials is None:
            Console.PrintError("Pool is not connected!\n")
            self.pool.Start = False
            return            
        if not self.pool.Serials[-1].is_open:
            self.pool.Serials[-1].open()
        self.uploader = UsbUploader(self.pool, self.buffers, self.toggle, self.mutex)
        self.uploader.on_data.connect(self.on_data)
        thread = QThread()
        thread.started.connect(self.uploader.process)
        self.uploader.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self.uploader.deleteLater)        
        thread.finished.connect(self.on_stop)        
        self.uploader.moveToThread(thread)
        self.reader.upload = True
        thread.start()
        self.thread.append(thread)

    def stop(self):
        self.uploader.run = False

    @Slot()
    def on_stop(self):
        self.reader.upload = False
        self.buffers.gain.release()
        while self.buffers.gain.available():
            self.buffers.gain.acquire()
        if self.pool.Serials[-1].is_open:
            self.pool.Serials[-1].close()        

            
    def pause(self):
        if self.pool.Serials is None:
            Console.PrintError("Pool is not connected!\n")
            self.pool.Pause = False
            return
        if not self.pool.Start and self.pool.Pause:
            Console.PrintError("File upload is not started!\n")
            self.pool.Pause = False
            return            
        self.mutex.lock()
        self.uploader.paused = True
        self.mutex.unlock()

    def resume(self):
        if self.pool.Serials is None:
            Console.PrintError("Pool is not connected!\n")
            return
        if not self.pool.Start:
            Console.PrintError("File upload is not started!\n")            
            return            
        self.mutex.lock()
        self.uploader.paused = False
        self.mutex.unlock()
        self.toggle.wakeAll()

    @Slot(unicode)
    def on_data(self, data):
        try:
            self.sio.write(data + self.eol)
            self.sio.flush()
        except Exception as e:
            msg = "Error occurred in UsbWriter process: {}\n"
            Console.PrintError(msg.format(e))

 
class UsbReader(QObject):

    finished = Signal()
    data = Signal(unicode)
    on_data = Signal(unicode)

    def __init__(self, pool, buffers):
        QObject.__init__(self)
        self.run = True
        self.upload = False
        s = pool.Serials[0]
        eol = pool.Proxy.getCharEndOfLine(pool) 
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s), newline=eol)
        self.pool = pool
        self.buffers = buffers

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        port = self.pool.Serials[0].port
        try:
            while self.run:
                line = self.sio.readline()
                if len(line):
                    if self.upload:
                        if line.startswith("qr:"):
                            b = int(line.split(":")[-1])
                            buffers = b - self.pool.Buffers if b > self.pool.Buffers else 0
                            while self.buffers.free.available() < buffers:
                                self.buffers.free.release()
                            while self.buffers.free.available() > buffers:
                                self.buffers.free.acquire()                                    
                            if self.buffers.free.available():
                                self.buffers.claim.release()
                                self.buffers.gain.acquire()
                            else:
                                self.on_data.emit("$qr")
                            continue
                        elif self.buffers.free.available():
                            self.buffers.gain.acquire()
                    self.data.emit(line)
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbReader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, port))
        self.finished.emit()


class UsbUploader(QObject):

    finished = Signal()
    on_data = Signal(unicode)    

    def __init__(self, pool, buffers, toggle, mutex):
        QObject.__init__(self)
        self.run = True
        self.pool = pool
        self.buffers = buffers
        self.toggle = toggle
        self.mutex = mutex
        self.paused = False

    @Slot()
    def process(self):
        """ Loop and copy file -> PySerial """
        try:
            eol = self.pool.Proxy.getCharEndOfLine(self.pool)
            s = self.pool.Serials[-1]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
            port = self.pool.Serials[-1].port
            self.on_data.emit("$qr")
            msg = "{} UsbUploader thread start on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, port))
            self.buffers.claim.acquire()
            with open(self.pool.UploadFile) as f:
                for line in f:
                    if not self.buffers.free.tryAcquire(1):
                        self.on_data.emit("$qr")
                        self.buffers.gain.release()
                        self.buffers.claim.acquire()
                    sio.write(line + eol)
                    sio.flush()
                    self.mutex.lock()
                    if self.paused:
                        self.toggle.wait(self.mutex)
                    self.mutex.unlock()
                    if not self.run:
                        break
        except Exception as e:
            msg = "Error occurred in UsbUploader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbUploader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, port))
        self.finished.emit()
