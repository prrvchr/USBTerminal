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
""" TinyG2 Model Plugin object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCADGui
import copy


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
        self.unit = 0
        self.waitunit = False
        self.command = "r"
        self.backstate = 0
        self.positions = []
        self.lastposition = [0,0,0]
        self._header = ("Command", "Value", "Description", ("Unit (inches)", "Unit (mm)"))
        self.initialized = False
        self.lastcmd = {"$$":"g30c"}
        self.initcmd = "$$"
        self.waitcmd = False
        self.initjson = '{"unit":n}\n{"o":n}\n{"sys":n}\n{"p1":n}\n{"q":n}\n{"m":n}\n{"r":n}'
        self.waitjson = False
        self.updateindex = QtCore.QModelIndex()
        self.deeproot = None
        self.beginResetModel()
        self.root = Node(None, "r")
        self.endResetModel()
        obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
        obs.changedUsbPool.connect(self.on_state)
        obs.datadic.connect(self.on_datadic)
        obs.data.connect(self.on_data)

    @QtCore.Slot()
    def on_inches(self):
        if self.unit == 0:
            return
        self.waitjson = True
        self.waitunit = True
        self.obj.Process.on_write('G20\n{"unit":n}')

    @QtCore.Slot()
    def on_mm(self):
        if self.unit == 1:
            return
        self.waitjson = True
        self.waitunit = True
        self.obj.Process.on_write('G21\n{"unit":n}')

    @QtCore.Slot(QtCore.QPoint, int)
    def on_unit(self, pos, index):
        if index != len(self._header) -1:
            return
        menu = QtGui.QMenu()
        inches = menu.addAction("Unit (inches)")
        inches.triggered.connect(self.on_inches)
        mm = menu.addAction("Unit (mm)")
        mm.triggered.connect(self.on_mm)
        menu.exec_(pos)

    @QtCore.Slot(unicode)
    def on_tabIndex(self, command):
        self.command = command
        self.setrootindex()

    def setrootindex(self):
        i = QtCore.QModelIndex()
        f = QtCore.Qt.MatchFlags(QtCore.Qt.MatchRecursive)
        q = self.match(self.index(0,0), QtCore.Qt.DisplayRole, self.command, 1, f)
        if q: i = q[0]
        self.rootindex.emit(i)

    def setModel(self, obj):
        if obj is None:
            self.rootToCache()
        elif self.obj != obj:
            self.obj = obj
            self.title.emit("TinyG2 {} monitor".format(obj.Label))
            self.initModel()
        else:
            self.rootFromCache()

    @QtCore.Slot(object)
    def on_state(self, obj):
        #Document Observer object filter...
        if obj != self.obj:
            return
        self.initModel()

    def initModel(self):
        state = self.obj.Pause <<2 | self.obj.Start <<1 | self.obj.Open <<0
        if state == 1 or state == 7:
            if self.backstate == 0:
                self.initRoot()
            else:
                self.rootFromCache()
        else:
            self.rootToCache()
        self.state.emit(state)
        self.backstate = state

    def initRoot(self):
        self.initialized = False
        self.waitjson = True
        self.beginResetModel()
        self.root = Node(None, "r")
        self.obj.Process.on_write(self.initjson)

    def endInitRoot(self):
        self.initialized = True
        self.endResetModel()
        self.setrootindex()
        self.initNode()

    def initNode(self):
        self.waitcmd = True
        self.obj.Process.on_write(self.initcmd)

    def endInitNode(self, command, extra):
        if not self.waitcmd:
            return
        if command == self.lastcmd[self.initcmd]:
            self.waitcmd = False
        f = QtCore.Qt.MatchFlags(QtCore.Qt.MatchRecursive)
        q = self.match(self.index(0,0), QtCore.Qt.DisplayRole, command, 1, f)
        if not q:
            return
        i = q[0]
        self.layoutAboutToBeChanged.emit
        self.changePersistentIndex(i, i)        
        self.root.addChildren("r", extra)
        self.dataChanged.emit(i, i)
        self.layoutChanged.emit()        

    def updateRoot(self, data):
        if not self.waitjson:
            return
        if data.has_key("fv"):
            return
        if data.has_key("unit"):
            self.unit = data["unit"]
            if self.waitunit:
                self.waitjson = False
                self.waitunit = False
                self.initModel()
            return
        if data.has_key("r"):
            if self.updateindex.isValid():
                self.endUpdateNode()
            elif not self.initialized:
                self.endInitRoot()
        else:
            if self.updateindex.isValid():
                self.updateNode()
            self.root.addChildren("r", data)

    def updateNode(self):
        self.layoutAboutToBeChanged.emit
        self.changePersistentIndex(self.updateindex, self.updateindex)

    def endUpdateNode(self):
        self.waitjson = False
        self.dataChanged.emit(self.updateindex, self.updateindex)
        self.updateindex = QtCore.QModelIndex()
        self.layoutChanged.emit()

    def rootToCache(self):
        self.beginResetModel()
        self.deeproot = copy.deepcopy(self.root)
        self.root = Node(None, "r")
        self.reset()
        self.endResetModel()

    def rootFromCache(self):
        self.beginResetModel()
        self.root = copy.deepcopy(self.deeproot)
        self.reset()
        self.endResetModel()
        self.setrootindex()

    @QtCore.Slot(unicode)
    def on_data(self, data):
        if not self.waitcmd:
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
        node = {}        
        command = r[0]
        search1 = ("fbs", "m48e", "ej", "saf", "mfo", "gco", "jv", "gdi", "id", "ct",
                   "gpl", "cofp", "lim", "gpa", "spep", "cv", "tv", "coph", "mfoe", "fv",
                   "comp", "hp", "hv", "spph", "fb", "gun", "js", "ja", "qv", "spdp",
                   "sv", "spdw", "mt", "si", "sl")
        search2 = ("x", "y", "z", "a", "b", "c", "1", "2", "3", "4", "5", "6")
        search3 = ("p1")
        search4 = ("g54", "g55", "g56", "g57", "g58", "g59", "g92", "g28", "g30")
        if command in search1:
            node = {"sys":{r[0]:[r[1], r[3]]}}
        elif command.startswith(search2):
            n = r.pop(0)
            node = {n[:1]:{n[1:]:[r[0], r[2]]}}
        elif command.startswith(search3):
            n = r.pop(0)
            node = {n[:2]:{n[2:]:[r[0], r[2]]}}
        elif command.startswith(search4):
            n = r.pop(0)
            node = {n[:3]:{n[3:]:[r[0], r[2]]}}
        if node:
            self.endInitNode(command, node)

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
                self.updateRoot(value)
            if key == "qr":
                self.report(value)
                break
            if key == "sr":
                self.report(value)
                break
            if key == "f":
                self.stat.emit("{}".format(value))

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
            if index.column() == len(self._header) -1:
                return "{}".format(getattr(node, "Unit"))
            else:
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
            self.waitjson = True
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
            if section == len(self._header) -1:
                return self._header[-1][self.unit]
            else:
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
