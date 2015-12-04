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
from Gui import TinyG2Model


class UsbPoolTaskPanel:

    def __init__(self, obj):
        model = TinyG2Model.PoolModel()
        panel = UsbPoolPanel(model)
        model.setModel(obj)
        self.form = [panel]

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

    tabindex = QtCore.Signal(unicode)

    def __init__(self):
        QtGui.QTabBar.__init__(self)
        self.setShape(QtGui.QTabBar.RoundedWest)
        self.setDocumentMode(True)
        self.setTabData(self.addTab("All"), "r")
        self.setTabData(self.addTab("System"), "sys")
        self.setTabData(self.addTab("Power"), "p1")
        self.setTabData(self.addTab("Axis X"), "x")
        self.setTabData(self.addTab("Y"), "y")
        self.setTabData(self.addTab("Z"), "z")
        self.setTabData(self.addTab("A"), "a")
        self.setTabData(self.addTab("B"), "b")
        self.setTabData(self.addTab("C"), "c")
        self.setTabData(self.addTab("Motor 1"), "1")
        self.setTabData(self.addTab("2"), "2")
        self.setTabData(self.addTab("3"), "3")
        self.setTabData(self.addTab("4"), "4")
        self.setTabData(self.addTab("5"), "5")
        self.setTabData(self.addTab("6"), "6")
        self.currentChanged.connect(self.on_tabIndex)

    @QtCore.Slot(int)
    def on_tabIndex(self, index):
        self.tabindex.emit(self.tabData(index))

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
        tabbar.tabindex.connect(model.on_tabIndex)
        model.state.connect(tabbar.on_state)
        tableview = UsbPoolView(model)
        setting.layout().addWidget(tableview)
        self.addTab(setting, "Current settings")
        monitor = QtGui.QWidget()
        monitor.setLayout(QtGui.QGridLayout())
        monitor.layout().addWidget(QtGui.QLabel("Line/N:"), 0, 0, 1, 1)
        line = QtGui.QLabel()
        monitor.layout().addWidget(line, 0, 1, 1, 1)
        obs.line.connect(line.setText)
        monitor.layout().addWidget(QtGui.QLabel("/"), 0, 2, 1, 1)
        nline = QtGui.QLabel()
        monitor.layout().addWidget(nline, 0, 3, 1, 1)
        model.nline.connect(nline.setText)
        monitor.layout().addWidget(QtGui.QLabel("GCode:"), 1, 0, 1, 1)
        gcode = QtGui.QLabel()
        monitor.layout().addWidget(gcode, 1, 1, 1, 3)
        obs.gcode.connect(gcode.setText)
        monitor.layout().addWidget(QtGui.QLabel("Buffers:"), 2, 0, 1, 1)
        buffers = QtGui.QLabel()
        monitor.layout().addWidget(buffers, 2, 1, 1, 3)
        model.buffers.connect(buffers.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosX:"), 3, 0, 1, 1)
        posx = QtGui.QLabel()
        monitor.layout().addWidget(posx, 3, 1, 1, 3)
        model.posx.connect(posx.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosY:"), 4, 0, 1, 1)
        posy = QtGui.QLabel()
        monitor.layout().addWidget(posy, 4, 1, 1, 3)
        model.posy.connect(posy.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosZ:"), 5, 0, 1, 1)
        posz = QtGui.QLabel()
        monitor.layout().addWidget(posz, 5, 1, 1, 3)
        model.posz.connect(posz.setText)
        monitor.layout().addWidget(QtGui.QLabel("Vel:"), 6, 0, 1, 1)
        vel = QtGui.QLabel()
        monitor.layout().addWidget(vel, 6, 1, 1, 3)
        model.vel.connect(vel.setText)
        monitor.layout().addWidget(QtGui.QLabel("Feed:"), 7, 0, 1, 1)
        feed = QtGui.QLabel()
        monitor.layout().addWidget(feed, 7, 1, 1, 3)
        model.feed.connect(feed.setText)
        monitor.layout().addWidget(QtGui.QLabel("Status:"), 8, 0, 1, 1)
        stat = QtGui.QLabel()
        monitor.layout().addWidget(stat, 8, 1, 1, 3)
        model.stat.connect(stat.setText)
        self.addTab(monitor, "Upload monitor")
        model.title.connect(self.on_title)
        model.state.connect(self.on_state)

    @QtCore.Slot(unicode)
    def on_title(self, title):
        self.setWindowTitle(title)

    @QtCore.Slot(int)
    def on_state(self, state):
        self.setTabEnabled(0, state == 1 or state == 7)
        self.setTabEnabled(1, state == 3 or state == 7)
        if state == 1:
            self.setCurrentIndex(0)
        elif state == 3:
            self.setCurrentIndex(1)


class UsbPoolView(QtGui.QTreeView):
    
    unit = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, model):
        QtGui.QTreeView.__init__(self)
        i = model._header.index("Value")
        self.setItemDelegateForColumn(i, PoolDelegate(self))
        self.setModel(model)
        self.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(self.on_unit)
        self.unit.connect(model.on_unit)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        model.rootindex.connect(self.on_rootindex)
        model.state.connect(self.on_state)

    @QtCore.Slot(QtCore.QModelIndex)
    def on_rootindex(self, index):
        self.setRootIndex(index)

    @QtCore.Slot(int)
    def on_state(self, state):
        self.setEnabled(state == 1 or state == 7)

    @QtCore.Slot(int)
    def on_unit(self, pos):
        self.unit.emit(self.mapToGlobal(pos), self.header().logicalIndexAt(pos))


class PoolDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        node = index.internalPointer()
        prop = node.Property
        root = None
        if node.parent:
            root = node.parent.Property
        if prop in ["m48e", "saf", "lim", "mfoe", "sl"]:
            menus = ("disable", "enable")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "ej":
            menus = ("text", "JSON")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "js":
            menus = ("relaxed", "strict")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "gdi":
            menus = ("G90", "G91")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "gun":
            menus = ("G20 inches", "G21 mm")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "gpl":
            menus = ("G17", "G18", "G19")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "gpa":
            menus = ("G61", "G61.1", "G64")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["cofp", "comp"]:
            menus = ("low is ON", "high is ON")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["coph", "spph"]:
            menus = ("no", "pause_on_hold")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "tv":
            menus = ("silent", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "sv" and node.Command == "sv":
            menus = ("off", "filtered", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "spep":
            menus = ("active_low", "active_high")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "spdp":
            menus = ("CW_low", "CW_high")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "jv":
            menus = ("silent", "footer", "messages", "configs", "linenum", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "am":
            menus = ("disabled", "standard", "inhibited", "radius")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "hi":
            menus = ("disable homing", "x axis", "y axis", "z axis", "a axis", "b axis", "c axis")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "hd":
            menus = ("search-to-negative", "search-to-positive")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "ma":
            menus = ("X", "Y", "Z", "A", "B", "C")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "po":
            menus = ("normal", "reverse")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "qv":
            menus = ("off", "single", "triple")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "pm":
            menus = ("disabled", "always on", "in cycle", "when moving")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop == "gco":
            menus = ("G54", "G55", "G56", "G57", "G58", "G59")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i+1)
            return combo
        elif prop == "mi":
            menus = ("1", "2", "4", "8", "16", "32")
            combo = QtGui.QComboBox(parent)
            for i in menus:
                combo.addItem(i, i)
            return combo
        elif prop == "sv" and node.Command != "sv":
            spin = QtGui.QSpinBox(parent)
            spin.setRange(0, 50000)
            return spin
        elif prop in ["fr", "vm", "jm", "csl", "csh", "wsh", "wsl", "frq"]:
            spin = QtGui.QSpinBox(parent)
            spin.setRange(0, 50000)
            return spin
        elif prop == "jh":
            spin = QtGui.QSpinBox(parent)
            spin.setRange(0, 1000000)
            return spin
        elif prop == "si":
            spin = QtGui.QSpinBox(parent)
            spin.setRange(100, 50000)
            return spin
        elif prop == "spdw":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 10000)
            spin.setDecimals(1)
            return spin
        elif prop in ["lv", "mt"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 10000)
            spin.setDecimals(2)
            return spin
        elif prop == "ja":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 1000)
            spin.setDecimals(2)
            return spin
        elif prop == "mfo":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0.05, 2)
            spin.setDecimals(3)
            return spin
        elif prop in ["cph", "cpl", "pl", "wpl", "wph", "pof"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 1)
            spin.setDecimals(3)
            return spin
        elif prop == "sa":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 10000)
            spin.setDecimals(3)
            return spin
        elif prop in ["lb", "zb", "tn", "tm", "x", "y", "z", "a", "b", "c"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(-10000, 10000)
            spin.setDecimals(3)
            return spin
        elif prop in ["tr", "ct"]: #"jd"
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(-10000, 10000)
            spin.setDecimals(4)
            return spin
        return QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QtGui.QComboBox):
            editor.setCurrentIndex(editor.findData(index.model().data(index)))
        elif isinstance(editor, QtGui.QSpinBox):
            editor.setValue(int(index.model().data(index)))
        elif isinstance(editor, QtGui.QDoubleSpinBox):
            editor.setValue(float(index.model().data(index)))
        elif isinstance(editor, QtGui.QLineEdit):
            editor.setText(index.model().data(index).strip())

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtGui.QComboBox):
            model.setData(index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QDoubleSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QLineEdit):
            model.setData(index, editor.text(), QtCore.Qt.EditRole)


