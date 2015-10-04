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
from threading import Thread, Event
from PySide.QtCore import QObject, Signal, Slot
from FreeCAD import Console


class UsbThread(QObject):

    input = Signal(unicode)
    echo = Signal(unicode)

    def __init__(self, pool):
        QObject.__init__(self)
        self.pool = pool
        self.reader = Thread(target=self.run_reader)
        self.writer = Thread(target=self.run_writer)
        self.uploader = Thread(target=self.run_uploader)
        self.reader.setDaemon(True)
        self.writer.setDaemon(True)
        self.uploader.setDaemon(True)
        self._upload = False
        self._data = []

    def start(self):
        serials = []
        try:
            for i in range(int(self.pool.DualPort) + 1):
                settings = self.pool.Group[i].Proxy.getSettingsDict(self.pool.Group[i])
                port = settings.pop("port", 0)
                serials.append(serial.serial_for_url(port, **settings))
        except serial.SerialException as e:
            Console.PrintError("Error occurred opening port: {}\n".format(e))
            return False
        Console.PrintLog("{} opening port {}... done\n".format(self.pool.Name, [x.port for x in serials]))
        self.pool.Serials = serials
        self.pool.Uploading = Event()
        self.reader.start()
        self.writer.start()
        self.uploader.start()
        return True

    @Slot(unicode)
    def on_output(self, data):
        self._data.append(data + self.pool.Proxy.getCharEndOfLine(self.pool))

    def ackData(self, data):
        if len(self.pool.AckList) == 0:
            return True
        for ack in self.pool.AckList:
            if ack in data:
                return True
        return False

    def run_reader(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            s = self.pool.Serials[0]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s), newline=self.pool.Proxy.getCharEndOfLine(self.pool))
            while self.pool.Open:
                data = sio.readline()
                if len(data):
                    self.input.emit(data)
                    if self._upload and self.ackData(data):
                        self.pool.Uploading.set()
        except Exception as e:
            Console.PrintError("Error occurred in reader Process: {}\n".format(e))
            return
        s.close()
        Console.PrintLog("{} reader thread stop on port {}... done\n".format(self.pool.Name, s.port))

    def run_writer(self):
        """ Loop and copy Terminal -> PySerial """
        try:
            s = self.pool.Serials[-1]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
            while self.pool.Open:
                while len(self._data):
                    sio.write(self._data.pop(0))
                    sio.flush()
        except Exception as e:
            Console.PrintError("Error occurred in writer Process: {}\n".format(e))
            return
        s.close()
        Console.PrintLog("{} writer thread stop on port {}... done\n".format(self.pool.Name, s.port))

    def run_uploader(self):
        """ Loop and copy file -> Terminal """
        try:
            while self.pool.Open:
                self.pool.Uploading.clear()
                self.pool.Uploading.wait()
                if not self.pool.Open:
                    break
                if self.pool.UploadFile:
                    self._upload = True
                    with open(self.pool.UploadFile) as f:
                        for line in f:
                            self.echo.emit(line)
                            self.pool.Uploading.clear()
                            self.pool.Uploading.wait()
                            if not self.pool.Open:
                                break
                    self._upload = False
        except Exception as e:
            Console.PrintError("Error occurred in uploader Process: {}\n".format(e))
            return
        Console.PrintLog("{} uploader thread stop... done\n".format(self.pool.Name))
