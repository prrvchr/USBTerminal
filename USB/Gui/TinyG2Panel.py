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
from App import UsbCommand
from Gui import UsbPoolPanel
import copy

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

    @QtCore.Slot(unicode)
    def on_title(self, title):
        self.setWindowTitle(title)

    @QtCore.Slot(int)
    def on_state(self, state):
        if state == 1:
            self.setCurrentIndex(0)
        elif state == 3:
            self.setCurrentIndex(1)


class UsbPoolView(QtGui.QTreeView):
    def __init__(self, model):
        QtGui.QTreeView.__init__(self)
        i = model._header.index("Value")
        self.setItemDelegateForColumn(i, PoolDelegate(self))
        self.setModel(model)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        model.rootindex.connect(self.on_rootindex)

    @QtCore.Slot(QtCore.QModelIndex)
    def on_rootindex(self, index):
        self.setRootIndex(index)


class PoolModel(QtCore.QAbstractItemModel):

    title = QtCore.Signal(unicode)
    state = QtCore.Signal(int)
    rootindex = QtCore.Signal(QtCore.QModelIndex)
    nline = QtCore.Signal(unicode)
    buffers = QtCore.Signal(unicode)
    posx = QtCore.Signal(unicode)
    posy = QtCore.Signal(unicode)
    posz = QtCore.Signal(unicode)
    vel = QtCore.Signal(unicode)
    feed = QtCore.Signal(unicode)
    stat = QtCore.Signal(unicode)

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self.obj = None
        keys = {QtCore.Qt.UserRole + 1: b"command"}
        self.setRoleNames(keys)
        self.command = "r"
        self.oldstate = 0
        self.positions = []
        self.lastposition = [0,0,0]
        self.nodedata = []
        self._header = ["Command", "Value", "Description", "Unit"]
        self.beginResetModel()
        self.root = Node(None, "r")
        self.deeproot = None
        self.initialized = False
        self.lastcmd = {"$$":"g30c"}
        self.initcmd = "$$"
        self.initjson = '{"o":n}\n{"sys":n}\n{"p1":n}\n{"q":n}\n{"m":n}\n{"r":n}'
        self.waitresponse = False
        self.waitextra = False
        self.updateindex = QtCore.QModelIndex()
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.statePool.connect(self.on_state)
        obs.datadic.connect(self.on_datadic)
        obs.data.connect(self.on_data)
        self.endResetModel() 

    def setrootindex(self):
        i = QtCore.QModelIndex()
        f = QtCore.Qt.MatchFlags(QtCore.Qt.MatchRecursive)
        q = self.match(self.index(0,0), QtCore.Qt.DisplayRole, self.command, 1, f)
        if q: i = q[0]
        self.rootindex.emit(i)

    def setModel(self, obj):
        if obj is None:
            self.emptyNode()
            return
        if self.obj is None or self.obj != obj:
            self.obj = obj
            self.title.emit("TinyG2 {} monitor".format(obj.Label))
        self.on_state(obj, self.oldstate)

    @QtCore.Slot(object, int)
    def on_state(self, obj, state):
        #Document Observer object filter...
        if obj != self.obj:
            return
        if state == 1 or state == 7:
            if self.oldstate == 0:
                self.initialized = False
                self.callResponse()
            else:
                self.fullNode()
        else:
            self.emptyNode()
        self.oldstate = state
        self.state.emit(state)

    def callResponse(self):
        self.beginResetModel()
        self.waitresponse = True
        self.root = Node(None, "r")
        self.obj.Process.on_write(self.initjson)

    def emptyNode(self):
        self.beginResetModel()
        self.deeproot = copy.deepcopy(self.root)
        self.root = Node(None, "r")
        self.endResetModel()

    def fullNode(self):
        self.beginResetModel()
        self.root = copy.deepcopy(self.deeproot)
        self.endResetModel()
        self.setrootindex()

    @QtCore.Slot(unicode)
    def on_tabIndex(self, command):
        self.command = command
        self.setrootindex()

    @QtCore.Slot(unicode)
    def on_data(self, data):
        if not self.waitresponse:
            return
        r = []
        c = ""
        search = ["-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        data = data[1:]
        for i, s in enumerate(data):
            if s == "]":
                r.append(c)
                c = ""
                break
            c += s
        for j, s in enumerate(data[i+1:]):
            if s in search and c.endswith(" "):
                r.append(c.strip())
                c = s
                break
            c += s
        for k, s in enumerate(data[i+j+2:]):
            if (s == " " and len(c.strip())) or i+j+k+3 == len(data):
                r.append(c.strip())
                break
            c += s
        r.append(data[i+j+k+3:])
        search1 = ("fbs", "m48e", "ej", "saf", "mfo", "gco", "jv", "gdi", "id", "ct",
                   "gpl", "cofp", "lim", "gpa", "spep", "cv", "tv", "coph", "mfoe", "fv",
                   "comp", "hp", "hv", "spph", "fb", "gun", "js", "ja", "qv", "spdp",
                   "sv", "spdw", "mt", "si", "sl")
        search2 = ("x", "y", "z", "a", "b", "c", "1", "2", "3", "4", "5", "6")
        search3 = ("p1")
        search4 = ("g54", "g55", "g56", "g57", "g58", "g59", "g92", "g28", "g30")
        node = {}
        command = r[0]
        if r[0] in search1:
            node = {"sys":{r[0]:[r[1], r[3]]}}
        elif r[0].startswith(search2):
            n = r.pop(0)
            node = {n[:1]:{n[1:]:[r[0], r[2]]}}
        elif r[0].startswith(search3):
            n = r.pop(0)
            node = {n[:2]:{n[2:]:[r[0], r[2]]}}
        elif r[0].startswith(search4):
            n = r.pop(0)
            node = {n[:3]:{n[3:]:[r[0], r[2]]}}
        if node:
            self.extra(command, node)

    @QtCore.Slot(dict)
    def on_datadic(self, data):
        for key, value in data.items():
            if key == "r":
                if type(value) is dict:
                    if value.has_key("sv"):
                        break
                    if value.has_key("sr"):
                        self.report(value["sr"])
                        break
                self.response(value)
            if key == "qr":
                self.report(value)
                break
            if key == "sr":
                self.report(value)
                break
            if key == "f":
                self.stat.emit("{}".format(value))


    def response(self, response):
        if not self.waitresponse:
            return
        if response.has_key("fv"):
            return
        if response.has_key("r"):
            if self.updateindex.isValid():
                self.waitresponse = False
                self.dataChanged.emit(self.updateindex, self.updateindex)
                self.updateindex = QtCore.QModelIndex()
                self.layoutChanged.emit()
            elif not self.initialized:
                self.initialized = True
                self.endResetModel()
                self.setrootindex()
                self.callExtra()
        else:
            if self.updateindex.isValid():
                self.layoutAboutToBeChanged.emit
                self.changePersistentIndex(self.updateindex, self.updateindex)
            self.root.addChildren("r", response)

    def callExtra(self):
        self.waitextra = True
        self.obj.Process.on_write(self.initcmd)

    def extra(self, command, extra):
        if not self.waitextra:
            return
        if command == self.lastcmd[self.initcmd]:
            self.waitextra = False
        self.root.addChildren("r", extra)

    @QtCore.Slot(dict)
    def report(self, report):
        for key, value in report.items():
            if key == "line":
                self.nline.emit(str(value))
            if key == "qr":
                self.buffers.emit(str(value))
            if key == "posx":
                self.posx.emit(str(value))
                self.lastposition[0] = value
            if key == "posy":
                self.posy.emit(str(value))
                self.lastposition[1] = value
            if key == "posz":
                self.posz.emit(str(value))
                self.lastposition[2] = value
            if key == "vel":
                self.vel.emit(str(value))
            if key == "feed":
                self.feed.emit(str(value))
            #if key == "stat":
            #    self.stat.emit("{}".format(value))
        self.positions.append(list(self.lastposition))
        if not self.obj.ViewObject.Draw:
            return
        if len(self.positions) < self.obj.ViewObject.Buffers:
            return
        self.obj.ViewObject.Positions += list(self.positions)
        self.positions = []

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid() or self.obj is None:
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return "{}".format(getattr(node, self._header[index.column()]))
        elif role == QtCore.Qt.UserRole +1:
            return node
        elif role == QtCore.Qt.BackgroundRole:
            parent = index.parent()
            i = False if not parent.isValid() else not parent.row() % 2
            color = QtGui.QColor("#f0f0f0") if index.row() % 2 == i else QtCore.Qt.white
            return QtGui.QBrush(color)
        return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return False
        if role == QtCore.Qt.EditRole:
            self.waitresponse = True
            self.updateindex = index
            node = index.internalPointer()
            cmd = ""
            if node.parent:
                cmd = '{{"{}":{{"{}":{}}}}}\n{{"r":n}}'.format(node.parent.Property, node.Property, value)
            else:
                cmd = '{{"{}":{}}}\n{{"r":n}}'.format(node.Property, value)
            self.obj.Process.on_write(cmd)
            return True
        return False

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

    def parent(self, index=QtCore.QModelIndex()):
        node = index.internalPointer()
        if node is None:
            return QtCore.QModelIndex()
        parentNode = node.parent
        if parentNode == self.root:
            return QtCore.QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            parentNode = parent.internalPointer()
        else:
            parentNode = self.root
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parentNode = self.root
        else:
            parentNode = parent.internalPointer()
        return parentNode.childCount()


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
        elif prop in ["ej"]:
            menus = ("text", "JSON")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["js"]:
            menus = ("relaxed", "strict")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["gdi"]:
            menus = ("G90", "G91")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["gun"]:
            menus = ("G20", "G21")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["gpl"]:
            menus = ("G17", "G18", "G19")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["gpa"]:
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
        elif prop in ["tv"]:
            menus = ("silent", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["sv"]:
            menus = ("off", "filtered", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["spep"]:
            menus = ("active_low", "active_high")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["spdp"]:
            menus = ("CW_low", "CW_high")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["jv"]:
            menus = ("silent", "footer", "messages", "configs", "linenum", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["am"]:
            menus = ("disabled", "standard", "inhibited", "radius")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["hi"]:
            menus = ("disable homing", "x axis", "y axis", "z axis", "a axis", "b axis", "c axis")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["hd"]:
            menus = ("search-to-negative", "search-to-positive")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["ma"]:
            menus = ("X", "Y", "Z", "A", "B", "C")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["po"]:
            menus = ("normal", "reverse")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["qv"]:
            menus = ("off", "single", "triple")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["pm"]:
            menus = ("disabled", "always on", "in cycle", "when moving")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif prop in ["gco"]:
            menus = ("G54", "G55", "G56", "G57", "G58", "G59")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i+1)
            return combo
        elif prop in ["mi"]:
            menus = ("1", "2", "4", "8", "16", "32")
            combo = QtGui.QComboBox(parent)
            for i in menus:
                combo.addItem(i, i)
            return combo
        elif prop in ["fr", "vm", "sv", "jm", "jh", "csl", "csh", "wsh", "wsl", "frq"]:
            spin = QtGui.QSpinBox(parent)
            spin.setMaximum(50000)
            spin.setMinimum(0)
            return spin
        elif prop in ["si"]:
            spin = QtGui.QSpinBox(parent)
            spin.setMaximum(50000)
            spin.setMinimum(100)
            return spin
        elif prop in ["spdw"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(1)
            spin.setMaximum(10000)
            spin.setMinimum(0)
            return spin
        elif prop in ["lv", "ja", "mt"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(2)
            spin.setMaximum(10000)
            spin.setMinimum(0)
            return spin
        elif prop in ["mfo"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(3)
            spin.setMaximum(2)
            spin.setMinimum(0.05)
            return spin
        elif prop in ["cph", "cpl", "ja", "pl", "wpl", "wph", "pof"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(3)
            spin.setMaximum(1)
            spin.setMinimum(0)
            return spin
        elif prop in ["sa"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(3)
            spin.setMaximum(10000)
            spin.setMinimum(0)
            return spin
        elif prop in ["lb", "zb", "tn", "tm", "x", "y", "z", "a", "b", "c"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(3)
            spin.setMaximum(10000)
            spin.setMinimum(-10000)
            return spin
        elif prop in ["tr", "ct"]: #"jd"
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setDecimals(4)
            spin.setMaximum(10000)
            spin.setMinimum(-10000)
            return spin
        return QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QtGui.QComboBox):
            editor.setCurrentIndex(editor.findData(index.model().data(index)))
        elif isinstance(editor, QtGui.QSpinBox):
            editor.setValue(int(index.model().data(index)))
        elif isinstance(editor, QtGui.QDoubleSpinBox):
            editor.setValue(float(index.model().data(index)))

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtGui.QComboBox):
            model.setData(index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QDoubleSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.EditRole)


class Node(object):

    def __init__(self, parent, item):
        self.Property = item
        self.Value = ""
        self.Description = ""
        self.Unit = ""
        self.children = {}
        self.childrow =[]
        self.parent = parent
        self.Command = item
        if self.parent is not None:
            if self.parent.Command not in ("r", "sys"):
                self.Command = self.parent.Command + item

    def addChildren(self, item, children):
        if item == self.Property:
            node = self
        elif item in self.childrow:
            node = self.children[item]
        else:
            node = Node(self, item) 
            self.childrow.append(item)
            self.children[item] = node
        if type(children) is dict:
            for i, c in children.items():
                node.addChildren(i, c)
        elif type(children) is list:
            properties = ["Description", "Unit"]
            for prop in properties:
                setattr(node, prop, children[properties.index(prop)])
        else:
            node.Value = children

    def child(self, row):
        if self.childrow:
            i = self.childrow[row]
            return self.children[i]

    def childCount(self):
        return len(self.childrow)

    def row(self):
        if self.parent is not None:
            return self.parent.childrow.index(self.Property)

    def log(self, level=-1):
        output = ""
        level += 1
        for i in range(level):
            output += "\t"
        output += "|--- {} --- {}\n".format(self.Property, self.Value)
        for k in self.childrow:
            output += self.children[k].log(level)
        level -= 1
        return output

    def __repr__(self):
        return self.log()
