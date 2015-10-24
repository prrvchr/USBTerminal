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


class UsbPortTaskPanel:

    def __init__(self, obj):
        form = []
        for o in obj.Asyncs:
            model = PySerialModel()
            panel = UsbPortPanel(model)
            model.setModel(o)
            form.append(panel)
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


class UsbPortPanel(QtGui.QWidget):

    def __init__(self, model):
        QtGui.QWidget.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Port.xpm"))
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        tableview = PySerialView(model)
        layout.addWidget(tableview)
        model.title.connect(self.on_title)

    @QtCore.Slot(unicode)
    def on_title(self, title):
        self.setWindowTitle("PySerial {} monitor".format(title))


class PySerialView(QtGui.QTableView):

    def __init__(self, model):
        QtGui.QTableView.__init__(self)
        self.setModel(model)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)


class PySerialModel(QtCore.QAbstractTableModel):

    title = QtCore.Signal(unicode)

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        self.obj = None
        self._header = ["Property", "Value"]
        self.offline = ["baudrate", "break_condition", "bytesize", "closed",
                        "dsrdtr", "dtr", "get_settings", "inter_byte_timeout",
                        "is_open", "parity", "port", "readable", "rts",
                        "rtscts", "seekable", "stopbits", "timeout", "writable",
                        "write_timeout", "xonxoff"]
        # "fileno" raise error on loop:// port!!!
        self.online = ["baudrate", "break_condition", "bytesize", "cd", "closed",
                       "cts", "dsr", "dsrdtr", "dtr", "get_settings",
                       "inter_byte_timeout", "in_waiting", "is_open", "isatty",
                       "out_waiting", "parity", "port", "readable", "ri",
                       "rs485_mode" "rts", "rtscts", "seekable", "stopbits",
                       "timeout", "writable", "write_timeout", "xonxoff"]
        self.properties = []
        self.newproperties = []
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedPort.connect(self.on_change)
        self.modelReset.connect(self.on_modelReset)

    @QtCore.Slot()
    def on_modelReset(self):
        if self.obj is not None:
            self.title.emit(self.obj.Label)

    def setModel(self, obj):
        if self.obj != obj:
            self.beginResetModel()
            self.obj = obj
            self.endResetModel()
        self.on_change(obj)

    @QtCore.Slot(object)
    def on_change(self, obj):
        if obj is None or self.obj is None:
            self.newproperties = []
            self.updateModel()
            return
        elif obj != self.obj:
            return
        elif self.obj.Async.is_open:
            #Test needed no "out_waiting" on loop:// port!!!
            self.newproperties = [o for o in self.online if hasattr(self.obj.Async, o)]
        else:
            self.newproperties = list(self.offline)
        self.updateModel()

    def updateModel(self):
        old = self.rowCount()
        new = len(self.newproperties)
        if old > new:
            self.beginRemoveRows(QtCore.QModelIndex(), new - 1, old - 1)
            self.removeRows(new - 1, old - new, QtCore.QModelIndex())
            self.properties = self.newproperties
            self.endRemoveRows()
        elif old < new:
            self.beginInsertRows(QtCore.QModelIndex(), old, old + new - 1)
            self.insertRows(old, new - old, QtCore.QModelIndex())
            self.properties = self.newproperties
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
        if not index.isValid() or self.obj.Async is None:
            return None
        if role == QtCore.Qt.DisplayRole:
            prop = self.properties[index.row()]
            if index.column():
                a = getattr(self.obj.Async, prop)
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


class TaskWatcher:

    def __init__(self):
        self.title = b"PySerial monitor"
        self.icon = b"icons:Usb-Port.xpm"
        self.model = PySerialModel()
        self.widgets = [UsbPortPanel(self.model)]
        self.model.title.connect(self.on_title)

    def shouldShow(self):
        s = FreeCADGui.Selection.getSelection()
        if len(s):
            o = s[0]
            if UsbCommand.getObjectType(o) == "App::UsbPort":
                self.model.setModel(o)
                return True
        self.model.on_change(None)
        return False

    @QtCore.Slot(unicode)
    def on_title(self, title):
        self.title = b"PySerial {} monitor".format(title)