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
""" Default USB Driver Thread object (no dual endpoint, no upload) """
from __future__ import unicode_literals

import io
from PySide.QtCore import QThread, QObject, Signal, Slot
from FreeCAD import Console


class UsbDriver(QObject):

    data = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        s = pool.Serials[0]
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
        self.reader = UsbReader(pool)
        self.reader.data.connect(self.data)
        self.thread = QThread()
        self.thread.started.connect(self.reader.process)
        self.reader.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.reader.deleteLater)
        self.thread.finished.connect(self.on_close)              
        self.reader.moveToThread(self.thread)
        self.thread.start()
        
    def open(self):
        self.reader.run = True

    def close(self):
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
        self.pool.Start = False

    def stop(self):
        NotImplemented

    def pause(self):
        self.pool.Pause = False

    def resume(self):
        NotImplemented

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

    def __init__(self, pool):
        QObject.__init__(self)
        self.run = True
        self.pool = pool
        s = pool.Serials[0]
        eol = pool.Proxy.getCharEndOfLine(pool) 
        self.sio = io.TextIOWrapper(io.BufferedRWPair(s, s), newline=eol)

    @Slot()
    def process(self):
        """ Loop and copy PySerial -> Terminal """
        port = self.pool.Serials[0].port
        try:
            while self.run:
                line = self.sio.readline()
                if len(line):
                    self.data.emit(line)
        except Exception as e:
            msg = "Error occurred in UsbReader thread process: {}\n"
            Console.PrintError(msg.format(e))
        else:
            msg = "{} UsbReader thread stop on port {}... done\n"
            Console.PrintLog(msg.format(self.pool.Name, port))
        self.finished.emit()
        