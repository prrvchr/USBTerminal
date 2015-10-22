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
""" TinyG2 panel Plugin object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCADGui


class UsbPoolPanel:

    def __init__(self, obj):
        model = SettingsModel()
        model.setModel(obj)
        taskpanel = UsbPoolTaskPanel(model)
        taskpanel.setWindowIcon(QtGui.QIcon("icons:Usb-Pool.xpm"))
        taskpanel.setWindowTitle("TinyG2 {} monitor".format(obj.Label))
        self.form = taskpanel
    
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
        return True

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


class UsbPoolTaskPanel(QtGui.QTabWidget):

    def __init__(self, model):
        QtGui.QTabWidget.__init__(self)
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        tableview = UsbPoolView(model)
        self.addTab(tableview, "Current settings")
        monitor = QtGui.QWidget()
        monitor.setLayout(QtGui.QGridLayout())
        monitor.layout().addWidget(QtGui.QLabel("Line:"), 0, 0, 1, 1)
        line = QtGui.QLabel()
        monitor.layout().addWidget(line, 0, 1, 1, 3)
        obs.line.connect(line.setText)
        monitor.layout().addWidget(QtGui.QLabel("GCode:"), 1, 0, 1, 1)
        gcode = QtGui.QLabel()
        monitor.layout().addWidget(gcode, 1, 1, 1, 3)
        obs.gcode.connect(gcode.setText)
        monitor.layout().addWidget(QtGui.QLabel("Buffers:"), 2, 0, 1, 1)
        buffers = QtGui.QLabel()
        monitor.layout().addWidget(buffers, 2, 1, 1, 3)
        obs.buffers.connect(buffers.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosX:"), 3, 0, 1, 1)
        posx = QtGui.QLabel()
        monitor.layout().addWidget(posx, 3, 1, 1, 3)
        obs.pointx.connect(posx.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosY:"), 4, 0, 1, 1)
        posy = QtGui.QLabel()
        monitor.layout().addWidget(posy, 4, 1, 1, 3)
        obs.pointy.connect(posy.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosZ:"), 5, 0, 1, 1)
        posz = QtGui.QLabel()
        monitor.layout().addWidget(posz, 5, 1, 1, 3)
        obs.pointz.connect(posz.setText)
        monitor.layout().addWidget(QtGui.QLabel("Vel:"), 6, 0, 1, 1)
        vel = QtGui.QLabel()
        monitor.layout().addWidget(vel, 6, 1, 1, 3)
        obs.vel.connect(vel.setText)
        monitor.layout().addWidget(QtGui.QLabel("Feed:"), 7, 0, 1, 1)
        feed = QtGui.QLabel()
        monitor.layout().addWidget(feed, 7, 1, 1, 3)
        obs.feed.connect(feed.setText)
        self.addTab(monitor, "Upload monitor")


class UsbPoolView(QtGui.QTableView):

    def __init__(self, model):
        QtGui.QTableView.__init__(self)
        self.setModel(model)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)


class SettingsModel(QtCore.QAbstractTableModel):


    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        self.obj = None
        self._header = ["Cmd", "Property", "Value"]
        self.settings = []
        self.newsettings = []
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedPool.connect(self.on_model)
        obs.settings.connect(self.on_setting)

    def setModel(self, obj):
        self.obj = obj
        self.on_model(obj, "Open")

    @QtCore.Slot(object, unicode)
    def on_model(self, obj, prop=None):
        if obj is None or self.obj is None:
            self.newsettings = []
            self.updateModel()
            return
        elif obj != self.obj:
            return
        if prop not in ["Open", "Start", "Pause"]:
            return
        if (obj.Open and not obj.Start) or (obj.Open and obj.Pause):
            self.newsettings = []
            self.obj.Process.on_write("$$")
        else:
            self.newsettings = []
            self.updateModel()

    @QtCore.Slot(unicode)
    def on_setting(self, setting):
        if setting == "eol":
            self.updateModel()
            self.newsettings = []
            return
        row = []
        cel = ""
        for i, char in enumerate(setting):
            if char == " " and cel.endswith("]"):
                row.append(cel)
                cel = ""
                continue
            if char in [" ", "0", "1"] and len(cel.strip()) and cel.endswith(" "):
                row.append(cel.strip())
                cel = char
                continue
            cel += char
        row.append(cel.strip())
        self.newsettings.append(row)

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
        self.dataChanged.emit(top, bottom)
        self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid() or self.obj is None:
            return None
        if role == QtCore.Qt.DisplayRole:
            row = self.settings[index.row()]
            return "{}".format(row[index.column()])
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
        return len(self.settings)


class PoolWatcher:

    def __init__(self):
        self.title = b"TinyG2 monitor"
        self.icon = b"icons:Usb-Pool.xpm"
        self.model = SettingsModel()
        self.widgets = [UsbPoolTaskPanel(self.model)]

    def shouldShow(self):
        s = FreeCADGui.Selection.getSelection()
        if len(s):
            o = s[0]
            if UsbCommand.getObjectType(o) == "App::UsbPool":
                if o.Open:
                    self.model.setModel(o)
                    return True
        self.model.on_model(None)
        return False

