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
""" PySerial Plugin Monitor object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import serial


class PySerialBaseModel(QtCore.QAbstractItemModel):

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self._header = ["Property", "Value"]
        self.properties = []
        self.allproperties = ["BAUDRATES",
                              "BYTESIZES",
                              "PARITIES",
                              "STOPBITS",
                              "baudrate",
                              "break_condition",
                              "bytesize",
                              "cd",
                              "closed",
                              "cts",
                              "dsr",
                              "dsrdtr",
                              "dtr",
                              "fileno",
                              "get_settings",
                              "inter_byte_timeout",
                              "in_waiting",
                              "is_open",
                              "isatty",
                              "out_waiting",
                              "parity",
                              "port",
                              "readable",
                              "ri",
                              "rs485_mode",
                              "rts",
                              "rtscts",
                              "seekable",
                              "stopbits",
                              "timeout",
                              "writable",
                              "write_timeout",
                              "xonxoff"]

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return QtCore.QModelIndex()
        return self.createIndex(row, column, row)

    def parent(self, index=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.properties)

    def flags(self, index=QtCore.QModelIndex()):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        return None

    def headerData(self, section, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section]
        return None


class PySerialModel(PySerialBaseModel):

    def __init__(self, obj):
        PySerialBaseModel.__init__(self)
        self.obj = obj
        state = obj.Proxy.getMachineState(obj)
        state.serialOpen.connect(self.updateModel)
        state.serialClose.connect(self.updateModel)
        state.serialError.connect(self.updateModel)
        self.updateModel()

    @QtCore.Slot()    
    def updateModel(self):
        properties = self.getProperties()
        if self.rowCount() != len(properties):
            self.beginResetModel()
            self.properties = properties
            self.endResetModel()        

    def getProperties(self):
        # Need to try: on close document serialClose is emited... and obj already deleted
        try:
            return [p for p in self.allproperties if hasattr(self.obj.Proxy.Serial, p)]
        except ReferenceError:
            return []

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            prop = self.properties[index.row()]
            if index.column():
                attr = getattr(self.obj.Proxy.Serial, prop)
                if hasattr(attr, "__self__"):
                    try:
                        s = "{}".format(attr())
                    except (serial.SerialException, ValueError) as e:
                        s = "{}".format(e)
                    return s
                else:
                    return "{}".format(attr)
            else:
                return prop
        if role == QtCore.Qt.BackgroundRole:
            color = QtGui.QColor("#f0f0f0") if index.row() % 2 == 0 else QtCore.Qt.white
            return QtGui.QBrush(color)
        return None
