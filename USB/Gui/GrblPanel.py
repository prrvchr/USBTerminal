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
""" Grbl panel Plugin object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCADGui
from App import UsbCommand
from Gui import UsbPoolPanel


class UsbPoolTaskPanel:

    def __init__(self, obj):
        model = PoolModel()
        panel = UsbPoolPanel(model)
        model.setModel(obj)
        self.form = panel

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
        return False

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok)
        #return int(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)

    def helpRequested(self):
        pass


class SettingTabBar(QtGui.QTabBar):

    command = QtCore.Signal(unicode)

    def __init__(self):
        QtGui.QTabBar.__init__(self)
        self.setShape(QtGui.QTabBar.RoundedWest)
        self.setDocumentMode(True)
        self.setTabData(self.addTab("All"), "$$")
        self.currentChanged.connect(self.on_command)

    @QtCore.Slot(int)
    def on_command(self, index):
        self.command.emit(self.tabData(index))
        
    @QtCore.Slot(int)
    def on_state(self, state):
        self.setEnabled(state == 1 or state == 7)


class UsbPoolPanel(QtGui.QTabWidget):

    def __init__(self, model):
        QtGui.QTabWidget.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Pool.xpm"))
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        setting = QtGui.QWidget()
        setting.setLayout(QtGui.QHBoxLayout())
        tabbar = SettingTabBar()
        setting.layout().addWidget(tabbar)
        tabbar.command.connect(model.on_command)
        model.state.connect(tabbar.on_state)
        tableview = UsbPoolView(model)
        setting.layout().addWidget(tableview)
        self.addTab(setting, "Current settings")
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
        self.addTab(monitor, "Upload monitor")
        model.title.connect(self.on_title)
        model.state.connect(self.on_state)

    @QtCore.Slot(unicode)
    def on_title(self, title):
        self.setWindowTitle("Grbl {} monitor".format(title))

    @QtCore.Slot(int)
    def on_state(self, state):
        if state == 1:
            self.setCurrentIndex(0)
        elif state == 3:
            self.setCurrentIndex(1)


class UsbPoolView(QtGui.QTableView):

    def __init__(self, model):
        QtGui.QTableView.__init__(self)
        i = model._header.index("Value")
        self.setItemDelegateForColumn(i, PoolDelegate(self))
        self.setModel(model)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMovable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)


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
        obs.statePool.connect(self.on_state)
        obs.settings.connect(self.on_settings)

    @QtCore.Slot()
    def on_modelReset(self):
        if self.obj is not None:
            self.title.emit(self.obj.Label)

    def setModel(self, obj):
        self.beginResetModel()
        self.obj = obj
        self.on_state(obj, 1)
        self.endResetModel()

    @QtCore.Slot(object, int)
    def on_state(self, obj, state):
        #Clear or not yet initialized
        if obj is None or self.obj is None:
            self.newsettings = []
            self.updateModel()
            return
        #Document Observer object filter...
        elif obj != self.obj:
            return
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


class PoolDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        model = index.model()
        i = model._header.index("Unit")
        unit = model.data(model.index(index.row(), i))
        if not unit:
            return QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)
        if unit in ["usec", "msec"]:
            spin = QtGui.QSpinBox(parent)
            spin.setMaximum(10000)
            spin.setMinimum(0)
            return spin
        elif unit in ["mm/min", "step/mm", "mm/sec^2"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(3)
            spin.setMaximum(10000)
            spin.setMinimum(0)
            return spin
        elif unit in ["mm"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(3)
            spin.setMaximum(10000)
            spin.setMinimum(-10000)
            return spin
        elif unit == "bool":
            combo = QtGui.QComboBox(parent)
            combo.addItem("on", "1")
            combo.addItem("off", "0")
            return combo
        elif "0" or "1" in unit:
            spin = QtGui.QSpinBox(parent)
            spin.setMaximum(255)
            spin.setMinimum(0)
            return spin
        return QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)

        
    def setEditorData(self, editor, index):
        if isinstance(editor, QtGui.QComboBox):
            editor.setCurrentIndex(editor.findData(index.model().data(index)))
        elif isinstance(editor, (QtGui.QDoubleSpinBox, QtGui.QSpinBox)):
            editor.setValue(int(index.model().data(index)))
        
    def setModelData(self, editor, model, index):
        if isinstance(editor, QtGui.QComboBox):
            model.setData(index, editor.itemData(editor.currentIndex()))
        elif isinstance(editor, (QtGui.QDoubleSpinBox, QtGui.QSpinBox)):
            model.setData(index, editor.value())
