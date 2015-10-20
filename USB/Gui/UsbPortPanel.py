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
import FreeCAD, FreeCADGui
from App import UsbCommand
import serial


class UsbPortPanel:

    def __init__(self, pool):
        form = []
        for port in pool.Asyncs:
            form.append(UsbPortTaskPanel(port))
        self.form = form
        
    def accept(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def clicked(self, index):
        pass

    def open(self):
        pass

    def needsFullSpace(self):
        return False

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return True

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok)
        #return int(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)

    def helpRequested(self):
        pass


class UsbPortTaskPanel(QtGui.QGroupBox):

    def __init__(self, port):
        QtGui.QGroupBox.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Port.xpm"))
        self.setWindowTitle("PySerial {} monitor".format(port.Label))
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        model = PySerialModel()
        tableview = PySerialView(model)
        layout.addWidget(tableview)
        model.setModel(port)


class PySerialView(QtGui.QTableView):

    def __init__(self, model):
        QtGui.QTableView.__init__(self)
        self.setModel(model)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)


class PySerialModel(QtCore.QAbstractTableModel):

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedPort.connect(self.setModel)
        self.pyserial = None
        self._column = 0
        self._header = ["Property", "Value"]
        self.offline = ["baudrate", "break_condition", "bytesize", "closed",
                        "dsrdtr", "dtr", "get_settings", "inter_byte_timeout",
                        "is_open", "isatty", "parity", "port", "readable", "rts",
                        "rtscts", "seekable", "stopbits", "timeout", "writable",
                        "write_timeout", "xonxoff", "BAUDRATES", "BAUDRATE_CONSTANTS",
                        "BYTESIZES", "PARITIES", "STOPBITS", "_SAVED_SETTINGS",]
        self.online = ["cd", "cts", "dsr", "fileno", "in_waiting", "out_waiting",
                       "ri", "rs485_mode"]
        self.properties = []

    @QtCore.Slot(object, unicode)
    def setModel(self, port, prop=None):
        if port is None or port.Async is None:
            self.pyserial = None
            properties = []
        else:
            self.pyserial = port.Async
            if self.pyserial.is_open:
                properties = list(self.online + self.offline)
            else:
                properties = list(self.offline)
        oldlen = self.rowCount()
        newlen = len(properties)
        if oldlen > newlen:
            self.beginRemoveRows(QtCore.QModelIndex(), newlen - 1, oldlen - 1)
            self.removeRows(newlen - 1, oldlen - newlen, QtCore.QModelIndex())
            self.properties = properties
            self.endRemoveRows()
        elif oldlen < newlen:
            self.beginInsertRows(QtCore.QModelIndex(), oldlen, oldlen + newlen - 1)
            self.insertRows(oldlen, newlen - oldlen, QtCore.QModelIndex())
            self.properties = properties
            self.endInsertRows()
        self.layoutAboutToBeChanged.emit()
        top = self.index(0, 0, QtCore.QModelIndex())
        bottom = self.index(self.rowCount() -1, 1, QtCore.QModelIndex())
        self.changePersistentIndex(top, bottom)
        self.dataChanged.emit(top, bottom)
        self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            prop = self.properties[index.row()]
            if index.column():
                a = getattr(self.pyserial, prop)
                if hasattr(a, "__self__"):
                    return "{}".format(a())
                else:
                    return "{}".format(a)
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
        if parent.isValid():
            return 0
        return len(self.properties)


class PortWatcher:

    def __init__(self):
        self.model = PySerialModel()
        view = PySerialView(self.model)
        self.widgets = [view]

    def shouldShow(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel):
            obj = sel[0]
            if UsbCommand.getObjectType(obj) == "App::UsbPort":
                self.model.setModel(obj)
                return True
        self.model.setModel(None)
        return False
