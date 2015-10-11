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
from PySide.QtCore import QThread, QSemaphore, QWaitCondition, QMutex
from PySide.QtCore import QObject, Signal, Slot
from FreeCAD import Console


class Buffers():

    def __init__(self):
        self.free = 0
        self.gain = QSemaphore()
        self.claim = QSemaphore()


class Mutex():
    
    def __init__(self):
        self.paused = QMutex()
        self.buffers = QMutex()
        self.upload = QMutex()
        self.runreader = QMutex()
        self.runuploader = QMutex()


class UsbDriver(QObject):
    
    data = Signal(unicode)
    gcode = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        s = pool.Serials[0]
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
        self.mutex = Mutex()
        self.toggle = QWaitCondition()
        self.buffers = Buffers()

    def open(self):
        thread = QThread()
        self.reader = UsbReader(self.pool, self.buffers, self.mutex)
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
        self.mutex.runreader.lock()
        self.reader.run = True
        self.mutex.runreader.unlock()

    def close(self):
        if self.pool.Pause:
            self.pool.Pause = False 
            self.resume()
        if self.pool.Start:
            self.pool.Start = False
            self.stop()
        else:
            self.mutex.runreader.lock()
            self.reader.run = False
            self.mutex.runreader.unlock()

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
        if self.checkStart():
            return
        if not self.pool.Serials[-1].is_open:
            self.pool.Serials[-1].open()
        self.uploader = UsbUploader(self.pool, self.buffers, self.toggle, self.mutex)
        self.uploader.on_data.connect(self.on_data)
        self.uploader.gcode.connect(self.gcode)
        thread = QThread()
        thread.started.connect(self.uploader.process)
        self.uploader.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self.uploader.deleteLater)        
        thread.finished.connect(self.on_stop)        
        self.uploader.moveToThread(thread)
        self.mutex.upload.lock()
        self.reader.upload = True
        self.mutex.upload.unlock()
        thread.start()
        self.thread.append(thread)

    def checkStart(self):
        if self.pool.Serials is None:
            Console.PrintError("Pool is not connected!\n")
            self.pool.Start = False
            return  True
        return False

    def stop(self):
        self.mutex.runuploader.lock()
        self.uploader.run = False
        self.mutex.runuploader.unlock()

    @Slot()
    def on_stop(self):
        self.mutex.upload.lock()
        self.reader.upload = False
        self.mutex.upload.unlock()
        self.buffers.gain.release(2)
        while self.buffers.gain.available():
            self.buffers.gain.acquire()
        if not self.pool.Open:
            self.mutex.runreader.lock()            
            self.reader.run = False
            self.mutex.runreader.unlock()
            
    def pause(self):
        if self.checkPause():
            return
        self.mutex.paused.lock()
        self.uploader.paused = True
        self.mutex.paused.unlock()

    def checkPause(self):
        if self.pool.Serials is None:
            Console.PrintError("Pool is not connected!\n")
            self.pool.Pause = False
            return True
        if not self.pool.Start and not self.pool.Pause:
            Console.PrintError("File upload is not started!\n")
            self.pool.Pause = False
            return True
        return False
        
    def resume(self):
        if self.checkResume():
            return
        self.mutex.paused.lock()
        self.uploader.paused = False
        self.mutex.paused.unlock()
        self.toggle.wakeAll()
        
    def checkResume(self):
        if self.pool.Serials is None:
            Console.PrintError("Pool is not connected!\n")
            self.pool.Pause = False
            return True
        if not self.pool.Start and self.pool.Pause:
            Console.PrintError("File upload is not started!*****\n")
            self.pool.Pause = False
            return True
        return False

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
    ctrl = Signal(unicode)
    data = Signal(unicode)
    on_data = Signal(unicode)

    def __init__(self, pool, buffers, mutex):
        QObject.__init__(self)
        self.run = True
        self.upload = False
        s = pool.Serials[0]
        eol = pool.Proxy.getCharEndOfLine(pool) 
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s), newline=eol)
        self.pool = pool
        self.buffers = buffers
        self.mutex = mutex

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        port = self.pool.Serials[0].port
        msg = "{} UsbReader thread start on port {}... done\n"
        Console.PrintLog(msg.format(self.pool.Name, port))        
        try:
            self.mutex.runreader.lock()
            while self.run:
                self.mutex.runreader.unlock()
                line = self.sio.readline()
                if len(line):
                    self.mutex.upload.lock()
                    if self.upload:
                        self.mutex.upload.unlock()
                        if line.startswith("qr:"):
                            b = int(line.split(":")[-1])
                            buffers = b - self.pool.Buffers if b > self.pool.Buffers else 0
                            self.mutex.buffers.lock()
                            self.buffers.free = buffers
                            if self.buffers.free > 0:
                                self.mutex.buffers.unlock()
                                self.buffers.claim.release()
                                self.buffers.gain.acquire()
                            else:
                                self.mutex.buffers.unlock()
                                self.on_data.emit("$qr")
                            #continue
                        if line.startswith("pos"):
                            self.ctrl.emit(line)
                        self.mutex.buffers.lock()
                        if self.buffers.free > 0:
                            self.mutex.buffers.unlock()
                            self.buffers.gain.acquire()
                        else:
                            self.mutex.buffers.unlock()
                    else:
                        self.mutex.upload.unlock()
                    self.data.emit(line)
                self.mutex.runreader.lock()    
            self.mutex.runreader.unlock()    
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
    gcode = Signal(unicode)

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
            i = 0
            with open(self.pool.UploadFile) as f:
                for line in f:
                    i += 1
                    self.mutex.buffers.lock()
                    self.buffers.free -= 1
                    if self.buffers.free == 0:
                        self.mutex.buffers.unlock()
                        self.on_data.emit("$qr")
                        self.buffers.gain.release()
                        self.buffers.claim.acquire()
                    else:
                        self.mutex.buffers.unlock()
                    line = line.strip()
                    sio.write(line + eol)
                    sio.flush()
                    self.gcode.emit("{}\t{}".format(i, line))
                    self.mutex.paused.lock()
                    if self.paused:
                        self.toggle.wait(self.mutex.paused)
                    self.mutex.paused.unlock()
                    self.mutex.runuploader.lock()
                    if not self.run:
                        self.mutex.runuploader.unlock()
                        break
                    self.mutex.runuploader.unlock()
        except Exception as e:
            msg = "Error occurred in UsbUploader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbUploader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, port))
        self.mutex.runuploader.lock()
        self.run = False
        self.mutex.runuploader.unlock()
        self.pool.Start = False
        self.finished.emit()
