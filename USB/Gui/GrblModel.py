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
""" Grbl Model Plugin object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCADGui


class PoolModel(QtCore.QAbstractTableModel):

    title = QtCore.Signal(unicode)
    state = QtCore.Signal(int)

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        self.obj = None
        self.cmd = "$$"
        self._header = ["Cmd", "Value", "Property", "Unit"]
        self.settings = []
        self.newsettings = []
        self.waitsettings = False
        self.changedindex = QtCore.QModelIndex()
        self.modelReset.connect(self.on_modelReset)
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedUsbPool.connect(self.on_state)
        obs.settings.connect(self.on_settings)

    @QtCore.Slot()
    def on_modelReset(self):
        if self.obj is not None:
            self.title.emit(self.obj.Label)

    def setModel(self, obj):
        self.obj = obj
        if obj is None:
            self.beginResetModel()
            self.newsettings = []
            self.updateModel()
            self.endResetModel()
        else:    
            self.on_state(obj)

    @QtCore.Slot(object)
    def on_state(self, obj):
        #Document Observer object filter...
        if obj != self.obj:
            return
        state = self.obj.Pause <<2 | self.obj.Start <<1 | self.obj.Open <<0
        if state == 1 or state == 7:
            self.waitsettings = True
            self.obj.Process.on_write(self.cmd)
        else:
            self.newsettings = []
            self.updateModel()
        self.state.emit(state)
        
    @QtCore.Slot(unicode)
    def on_command(self, cmd):
        self.cmd = cmd
        self.waitsettings = True
        self.obj.Process.on_write(cmd)

    @QtCore.Slot(unicode)
    def on_settings(self, setting):
        if not self.waitsettings:
            return
        elif setting == "endofsettings":
            self.waitsettings = False
            if self.changedindex.isValid():
                self.updateIndex()
            else:
                self.updateModel()
            self.newsettings = []
            return
        r = []
        c = ""
        for i, s in enumerate(setting):
            if s == "=":
                r.append(c)
                c = ""
                break
            c += s
        for j, s in enumerate(setting[i+1:]):
            if s == " ":
                r.append(c)
                c = ""
                break
            c += s
        for k, s in enumerate(setting[i+j+2:]):
            if s == "," or s == ":" :
                r.append(c)
                break
            c += s
        r.append(setting[i+j+k+3:])
        self.newsettings.append(r)

    def updateIndex(self):
        self.layoutAboutToBeChanged.emit()
        self.changePersistentIndex(self.changedindex, self.changedindex)
        self.settings[self.changedindex.row()] = self.newsettings[0]
        self.dataChanged.emit(self.changedindex, self.changedindex)
        self.changedindex = QtCore.QModelIndex()
        self.layoutChanged.emit()

    def updateModel(self):
        old = self.rowCount()
        new = len(self.newsettings)
        if old > new:
            self.beginRemoveRows(QtCore.QModelIndex(), new - 1, old - 1)
            self.removeRows(new - 1, old - new, QtCore.QModelIndex())
            self.settings = list(self.newsettings)
            self.endRemoveRows()
        elif old < new:
            self.beginInsertRows(QtCore.QModelIndex(), old, old + new - 1)
            self.insertRows(old, new - old, QtCore.QModelIndex())
            self.settings = list(self.newsettings)
            self.endInsertRows()
        self.layoutAboutToBeChanged.emit()
        top = self.index(0, 0, QtCore.QModelIndex())
        bottom = self.index(self.rowCount() -1, 1, QtCore.QModelIndex())
        self.changePersistentIndex(top, bottom)
        if old == new: self.settings = list(self.newsettings)
        self.dataChanged.emit(top, bottom)
        self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid() or self.obj is None:
            return None
        if role == QtCore.Qt.DisplayRole:
            return "{}".format(self.settings[index.row()][index.column()])
        if role == QtCore.Qt.BackgroundRole:
            color = QtGui.QColor("#f0f0f0") if index.row() % 2 == 0 else QtCore.Qt.white
            return QtGui.QBrush(color)
        return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        self.waitsettings = True
        self.changedindex = index
        i = self._header.index("Cmd")
        cmd = self.data(self.index(index.row(), i)).strip("[]")
        self.obj.Process.on_write("${}={}".format(cmd, value))
        return True

    def headerData(self, section, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section]
        return None

    def flags(self, index=QtCore.QModelIndex()):
        if index.column() == self._header.index("Value"):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled  
        #return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.settings)
