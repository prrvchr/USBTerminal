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
import FreeCADGui


class PySerialModel(QtCore.QAbstractTableModel):

    title = QtCore.Signal(unicode)

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        self.obj = None
        self.PySerial = None
        self._header = ["Property", "Value"]
        # "fileno" raise error on loop:// port!!!
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
        self.properties = []
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedPySerial.connect(self.onChanged)

    @QtCore.Slot(object)
    def onChanged(self, obj):
        #Document Observer object filter...
        if self.obj == obj:
            self.setModel(obj)

    def setModel(self, obj):
        self.updateModel(obj, self.getProperties(obj))

    def getProperties(self, obj):
        #Test needed no "out_waiting" on loop:// port!!!
        return [] if obj is None else [p for p in self.allproperties
                                       if hasattr(obj.Proxy.PySerial, p)]

    def updateModel(self, obj, properties):
        if self.obj != obj or self.rowCount() != len(properties):
            self.beginResetModel()
            self.obj = obj
            self.PySerial = None if obj is None else obj.Proxy.PySerial
            self.properties = properties
            self.endResetModel()

    def updateModel1(self, properties):
        old = self.rowCount()
        new = len(properties)
        if old > new:
            self.beginRemoveRows(QtCore.QModelIndex(), new - 1, old - 1)
            self.removeRows(new - 1, old - new, QtCore.QModelIndex())
            self.properties = properties
            self.endRemoveRows()
        elif old < new:
            self.beginInsertRows(QtCore.QModelIndex(), old, old + new - 1)
            self.insertRows(old, new - old, QtCore.QModelIndex())
            self.properties = properties
            self.endInsertRows()
        self.layoutAboutToBeChanged.emit()
        top = self.index(0, 0, QtCore.QModelIndex())
        bottom = self.index(self.rowCount() - 1, self.columnCount() - 1, QtCore.QModelIndex())
        self.changePersistentIndex(top, bottom)
        if old == new: self.properties = properties
        self.dataChanged.emit(top, bottom)
        self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid() or self.PySerial is None:
            return None
        if role == QtCore.Qt.DisplayRole:
            prop = self.properties[index.row()]
            if index.column():
                attr = getattr(self.PySerial, prop)
                if hasattr(attr, "__self__"):
                    return "{}".format(attr())
                else:
                    return "{}".format(attr)
            else:
                return prop
        if role == QtCore.Qt.BackgroundRole:
            color = QtGui.QColor("#f0f0f0") if index.row() % 2 == 0 else QtCore.Qt.white
            return QtGui.QBrush(color)
        return None

    def headerData(self, section, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section]
        return None

    def flags(self, index=QtCore.QModelIndex()):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid() or self.PySerial is None:
            return 0
        return len(self.properties)
