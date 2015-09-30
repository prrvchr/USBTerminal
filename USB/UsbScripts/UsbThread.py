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
""" Usb Thread object """
from __future__ import unicode_literals

import io
import serial
from threading import Thread
from Queue import Queue
from PySide.QtCore import QObject, Signal, Slot
from FreeCAD import Console


class UsbThread(QObject):

    input = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.name = pool.Name
        self.serials = []
        for i in range(int(pool.DualPort) + 1):
            settings = pool.Group[i].Proxy.getSettingsDict(pool.Group[i])
            port = settings.pop("port", 0)
            self.serials.append(serial.serial_for_url(port, **settings))
        Console.PrintLog("{} opening port {}... done\n".format(pool.Name, [x.port for x in self.serials]))            
        self.eol = pool.Proxy.getCharEndOfLine(pool)
        self.reader = Thread(target=self.run_reader)
        self.writer = Thread(target=self.run_writer)
        self.reader.setDaemon(True)
        self.writer.setDaemon(True)
        self._data = Queue()
        self.reader.start()
        self.writer.start()
        pool.Serials = self.serials
        
    @Slot(unicode)
    def on_output(self, data):
        self._data.put(data + self.eol)

    def run_reader(self):
        """loop and copy serial -> console"""
        try:
            s = self.serials[0]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s), newline=self.eol)
            while s.isOpen():
                data = sio.readline()
                if len(data):
                    self.input.emit(data)
        except Exception as e:
            Console.PrintError("Error occurred in reader Process: {}\n".format(e))
            return
        Console.PrintLog("{} reader thread stop on port {}... done\n".format(self.name, s.port))            
        
    def run_writer(self):
        """loop and copy console -> serial"""
        try:
            s = self.serials[-1]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
            while s.isOpen():
                while not self._data.empty():
                    sio.write(self._data.get())
                    sio.flush()
        except Exception as e:
            Console.PrintError("Error occurred in writer Process: {}\n".format(e))
            return
        Console.PrintLog("{} writer thread stop on port {}... done\n".format(self.name, s.port))            

