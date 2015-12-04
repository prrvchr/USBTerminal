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
from Gui import GrblModel


class UsbPoolTaskPanel:

    def __init__(self, obj):
        model = GrblModel.PoolModel()
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
