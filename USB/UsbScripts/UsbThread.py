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
from PySide.QtCore import QThread, Signal, Slot
from FreeCAD import Console


class UsbReader(QThread):

    data = Signal(unicode)

    def __init__(self, pool):
        QThread.__init__(self)
        self.pool = pool

    def run(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            s = self.pool.Serials[0]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s),\
                  newline=self.pool.Proxy.getCharEndOfLine(self.pool))
            while self.pool.Open:
                data = sio.readline()
                if len(data):
                    self.data.emit(data)
        except Exception as e:
            Console.PrintError("Error occurred in UsbReader thread process: {}\n".format(e))
            return
        self.msleep(5)        
        Console.PrintLog("{} UsbReader thread stop on port {}... done\n".\
                         format(self.pool.Name, s.port))


class UsbWriter(QThread):
    
    def __init__(self, pool):
        QThread.__init__(self)
        self.pool = pool
        self._data = []

    @Slot(unicode)
    def on_data(self, data):
        self._data.append(data + self.pool.Proxy.getCharEndOfLine(self.pool))

    def run(self):
        """ Loop and copy Terminal -> PySerial """
        try:
            s = self.pool.Serials[0]
            sio = io.TextIOWrapper(io.BufferedRWPair(s, s))
            while self.pool.Open:
                while len(self._data):
                    sio.write(self._data.pop(0))
                    sio.flush()
        except Exception as e:
            Console.PrintError("Error occurred in UsbWriter thread process: {}\n".format(e))
            return
        self.msleep(5)
        Console.PrintLog("{} UsbWriter thread stop on port {}... done\n".\
                         format(self.pool.Name, s.port))
