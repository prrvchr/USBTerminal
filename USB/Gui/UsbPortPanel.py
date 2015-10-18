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


class UsbPortPanel:

    def __init__(self, pool):
        form = []
        for port in pool.Serials:
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
        self.setObjectName("{}-Monitor".format(port.Name))
        self.setWindowTitle("{} Monitor".format(port.Label))
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Port.xpm"))
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        tableview = PySerialView(port)
        layout.addWidget(tableview)


class PySerialView(QtGui.QTableView):
    
    def __init__(self, port):
        QtGui.QTableView.__init__(self)
        model = PySerialModel(port)
        self.setModel(model)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setStretchLastSection(True)
        #self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        #self.doubleClicked(QtCore.QModelIndex).connect(self.ItemDoubleClicked(QtCore.QModelIndex))

    @QtCore.Slot(QtCore.QModelIndex)
    def ItemDoubleClicked(self, index):
        QMessageBox.information(None, "Hello!", "You Double Clicked: \n{}".format(index.data()))


class PySerialModel(QtCore.QAbstractTableModel):

    def __init__(self, port):
        QtCore.QAbstractTableModel.__init__(self)
        self.port = port
        self._column = 0
        self._header = ["Property", "Value"]
        self._attributes = ["baudrate", "bytesize", "dsrdtr", "inter_byte_timeout", "parity",
                            "port", "rtscts", "stopbits", "timeout", "write_timeout", "xonxoff",
                            "in_waiting", "out_waiting", "rts", "dtr", "name", "cts", "dsr", "ri",
                            "cd", "rs485_mode", "BAUDRATES", "BYTESIZES", "PARITIES", "STOPBITS"]

    def setColumn(self, column):
        self._column = column
        top = self.index(0, column, QtCore.QModelIndex())
        bottom = self.index(self.rowCount() -1, column, QtCore.QModelIndex())
        self.dataChanged.emit(top, bottom)

    def setModel(self, port):
        self.beginResetModel()
        self.port = port
        self.endResetModel()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            if self.port.Async is None or not self.port.Async.is_open:
                if index.column():
                    return "not connected!!!"
                else:
                    return "{}".format(self.port.Label)
            else:
                if index.column():
                    attr = getattr(self.port.Async, self._attributes[index.row()])
                    return "{}".format(attr)
                else:
                    return self._attributes[index.row()]
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
        if self.port.Async is None or not self.port.Async.is_open:
            return 1
        return len(self._attributes)

    @QtCore.Slot(int)
    def onActivated(self, value):
        self.setColumn(value)
