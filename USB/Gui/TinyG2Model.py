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
import json
import copy


class Node(object):

    def __init__(self, parent, key):
        self.key = key
        self.child = []
        self.parent = parent
        if parent is not None:
            parent.child.append(self)

    def row(self):
        if self.parent is None:
            return None
        else:
            return self.parent.child.index(self)

    def log(self, level=0):
        output = ""
        for i in range(level):
            output += "    "
        output += "|--- {}\n".format(self.key)
        for k in self.child:
            output += k.log(level +1)
        return output

    def __repr__(self):
        return self.log()

def makeTree(parent, child):
    for value in child:
        if type(value) is not list:
            node = Node(parent, value)
        else:
            makeTree(node, value)

def makeData(data, tree, header):
    data[tree.key] = [None] * len(header)
    data[tree.key][0] = tree.key
    for child in tree.child:
        makeData(data, child, header)

def makeCmd(cmd, dic, path):
    if type(dic) is dict:
        for k, value in dic.iteritems():
            p = list(path)
            p.insert(0,k)
            makeCmd(cmd, value, p)
    else:
        cmd[dic] = path


class PoolBaseModel(QtCore.QAbstractItemModel):

    title = QtCore.Signal(unicode)
    rootIndex = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        unit = 0
        self.obj = None
        self._header = ("Command", "Value", "Description",
                        ("Unit (inches)", "Unit (mm)"))
        self.setRoleNames({QtCore.Qt.UserRole + 1: b"command"})
        self.initcmd = ['{"unit":n}','{"o":n}','{"sys":n}','{"p1":n}',
                        '{"q":n}','{"m":n}','{"r":n}', '$$']

        self.dickey = {"r":{"unit":"unit",
                            "g54":{"x":"g54x","y":"g54y","z":"g54z","a":"g54a","b":"g54b","c":"g54c"},
                            "g55":{"x":"g55x","y":"g55y","z":"g55z","a":"g55a","b":"g55b","c":"g55c"},
                            "g56":{"x":"g56x","y":"g56y","z":"g56z","a":"g56a","b":"g56b","c":"g56c"},
                            "g57":{"x":"g57x","y":"g57y","z":"g57z","a":"g57a","b":"g57b","c":"g57c"},
                            "g58":{"x":"g58x","y":"g58y","z":"g58z","a":"g58a","b":"g58b","c":"g58c"},
                            "g59":{"x":"g59x","y":"g59y","z":"g59z","a":"g59a","b":"g59b","c":"g59c"},
                            "g92":{"x":"g92x","y":"g92y","z":"g92z","a":"g92a","b":"g92b","c":"g92c"},
                            "g28":{"x":"g28x","y":"g28y","z":"g28z","a":"g28a","b":"g28b","c":"g28c"},
                            "g30":{"x":"g30x","y":"g30y","z":"g30z","a":"g30a","b":"g30b","c":"g30c"},
                            "sys":{"fb":"fb","fbs":"fbs","fv":"fv","cv":"cv","hp":"hp",
                                   "hv":"hv","id":"id","ja":"ja","ct":"ct","sl":"sl",
                                   "lim":"lim","saf":"saf","mt":"mt","m48e":"m48e","mfoe":"mfoe",
                                   "mfo":"mfo","spep":"spep","spdp":"spdp","spph":"spph","spdw":"spdw",
                                   "cofp":"cofp","comp":"comp","coph":"coph","tv":"tv","ej":"ej",
                                   "jv":"jv","js":"js","qv":"qv","sv":"sv","si":"si",
                                   "gpl":"gpl","gun":"gun","gco":"gco","gpa":"gpa","gdi":"gdi"},
                            "p1":{"frq":"p1frq","csl":"p1csl","csh":"p1csh","cpl":"p1cpl","cph":"p1cph",
                                  "wsl":"p1wsl","wsh":"p1wsh","wpl":"p1wpl","wph":"p1wph","pof":"p1pof"},
                            "x":{"am":"xam","vm":"xvm","fr":"xfr","tn":"xtn","tm":"xtm",
                                 "jm":"xjm","jh":"xjh","jd":"xjd","hi":"xhi","hd":"xhd",
                                 "sv":"xsv","lv":"xlv","lb":"xlb","zb":"xzb"},
                            "y":{"am":"yam","vm":"yvm","fr":"yfr","tn":"ytn","tm":"ytm",
                                 "jm":"yjm","jh":"yjh","jd":"yjd","hi":"yhi","hd":"yhd",
                                 "sv":"ysv","lv":"ylv","lb":"ylb","zb":"yzb"},
                            "z":{"am":"zam","vm":"zvm","fr":"zfr","tn":"ztn","tm":"ztm",
                                 "jm":"zjm","jh":"zjh","jd":"zjd","hi":"zhi","hd":"zhd",
                                 "sv":"zsv","lv":"zlv","lb":"zlb","zb":"zzb"},
                            "a":{"am":"aam","vm":"avm","fr":"afr","tn":"atn","tm":"atm",
                                 "jm":"ajm","jh":"ajh","jd":"ajd","ra":"ara","hi":"ahi",
                                 "hd":"ahd","sv":"asv","lv":"alv","lb":"alb","zb":"azb"},
                            "b":{"am":"bam","vm":"bvm","fr":"bfr","tn":"btn","tm":"btm",
                                 "jm":"bjm","jh":"bjh","jd":"bjd","ra":"bra","hi":"bhi",
                                 "hd":"bhd","sv":"bsv","lv":"blv","lb":"blb","zb":"bzb"},
                            "c":{"am":"cam","vm":"cvm","fr":"cfr","tn":"ctn","tm":"ctm",
                                 "jm":"cjm","jh":"cjh","jd":"cjd","ra":"cra","hi":"chi",
                                 "hd":"chd","sv":"csv","lv":"clv","lb":"clb","zb":"czb"},
                            "1":{"ma":"1ma","sa":"1sa","tr":"1tr","mi":"1mi","po":"1po",
                                 "pm":"1pm","pl":"1pl"},
                            "2":{"ma":"2ma","sa":"2sa","tr":"2tr","mi":"2mi","po":"2po",
                                 "pm":"2pm","pl":"2pl"},
                            "3":{"ma":"3ma","sa":"3sa","tr":"3tr","mi":"3mi","po":"3po",
                                 "pm":"3pm","pl":"3pl"},
                            "4":{"ma":"4ma","sa":"4sa","tr":"4tr","mi":"4mi","po":"4po",
                                 "pm":"4pm","pl":"4pl"},
                            "5":{"ma":"5ma","sa":"5sa","tr":"5tr","mi":"5mi","po":"5po",
                                 "pm":"5pm","pl":"5pl"},
                            "6":{"ma":"6ma","sa":"6sa","tr":"6tr","mi":"6mi","po":"6po",
                                 "pm":"6pm","pl":"6pl"}}}

        treekey = ["o",["g54",["g54x","g54y","g54z","g54a","g54b","g54c"],
                        "g55",["g55x","g55y","g55z","g55a","g55b","g55c"],
                        "g56",["g56x","g56y","g56z","g56a","g56b","g56c"],
                        "g57",["g57x","g57y","g57z","g57a","g57b","g57c"],
                        "g58",["g58x","g58y","g58z","g58a","g58b","g58c"],
                        "g59",["g59x","g59y","g59z","g59a","g59b","g59c"],
                        "g92",["g92x","g92y","g92z","g92a","g92b","g92c"],
                        "g28",["g28x","g28y","g28z","g28a","g28b","g28c"],
                        "g30",["g30x","g30y","g30z","g30a","g30b","g30c"]],
                   "sys",["fb","fbs","fv","cv","hp","hv","id","ja","ct","sl",
                          "lim","saf","mt","m48e","mfoe","mfo","spep","spdp",
                          "spph","spdw","cofp","comp","coph","tv","ej","jv",
                          "js","qv","sv","si","gpl","gun","gco","gpa","gdi"],
                   "p1",["p1frq","p1csl","p1csh","p1cpl","p1cph",
                         "p1wsl","p1wsh","p1wpl","p1wph","p1pof"],
                   "q",["x",["xam","xvm","xfr","xtn","xtm","xjm","xjh","xjd",
                             "xhi","xhd","xsv","xlv","xlb","xzb"],
                        "y",["yam","yvm","yfr","ytn","ytm","yjm","yjh","yjd",
                             "yhi","yhd","ysv","ylv","ylb","yzb"],
                        "z",["zam","zvm","zfr","ztn","ztm","zjm","zjh","zjd",
                             "zhi","zhd","zsv","zlv","zlb","zzb"],
                        "a",["aam","avm","afr","atn","atm","ajm","ajh","ajd",
                             "ara","ahi","ahd","asv","alv","alb","azb"],
                        "b",["bam","bvm","bfr","btn","btm","bjm","bjh","bjd",
                             "bra","bhi","bhd","bsv","blv","blb","bzb"],
                        "c",["cam","cvm","cfr","ctn","ctm","cjm","cjh","cjd",
                             "cra","chi","chd","csv","clv","clb","czb"]],
                   "m",["1",["1ma","1sa","1tr","1mi","1po","1pm","1pl"],
                        "2",["2ma","2sa","2tr","2mi","2po","2pm","2pl"],
                        "3",["3ma","3sa","3tr","3mi","3po","3pm","3pl"],
                        "4",["4ma","4sa","4tr","4mi","4po","4pm","4pl"],
                        "5",["5ma","5sa","5tr","5mi","5po","5pm","5pl"],
                        "6",["6ma","6sa","6tr","6mi","6po","6pm","6pl"]],
                   "unit"]
        self.treeKey = Node(None, "r")
        makeTree(self.treeKey, treekey)
        self.dataKey = {}
        makeData(self.dataKey, self.treeKey, self._header)
        self.dataKey["unit"][self._header.index("Value")] = unit
        self.cmdKey = {}
        makeCmd(self.cmdKey, self.dickey["r"], ["r"])

    def parent(self, index=QtCore.QModelIndex()):
        node = index.internalPointer()
        if node.parent is None:
            return QtCore.QModelIndex()
        parentnode = node.parent
        if parentnode == self.treeKey:
            return QtCore.QModelIndex()
        return self.createIndex(parentnode.row(), 0, parentnode)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            parentnode = parent.internalPointer()
        else:
            parentnode = self.treeKey
        child = parentnode.child[row]
        if child:
            return self.createIndex(row, column, child)
        else:
            return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parentnode = self.treeKey
        else:
            parentnode = parent.internalPointer()
        return len(parentnode.child)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.dataKey[node.key][index.column()]
        elif role == QtCore.Qt.UserRole +1:
            return node
        elif role == QtCore.Qt.BackgroundRole:
            parent = index.parent()
            i = False if not parent.isValid() else not parent.row() % 2
            color = QtGui.QColor("#f0f0f0") if index.row() % 2 == i else QtCore.Qt.white
            return QtGui.QBrush(color)
        return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        return False

    def headerData(self, section, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == len(self._header) -1:
                return self._header[-1][self.getUnit()]
            else:
                return self._header[section]
        return None

    def flags(self, index=QtCore.QModelIndex()):
        return QtCore.Qt.ItemIsEnabled
        #return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def getUnit(self):
        return self.dataKey["unit"][self._header.index("Value")]

    @QtCore.Slot(QtCore.QPoint, int)
    def onUnit(self, pos, index):
        pass
    @QtCore.Slot()
    def onInches(self):
        pass
    @QtCore.Slot()
    def onMetric(self):
        pass
    @QtCore.Slot(unicode)
    def setRootIndex(self, key):
        pass


class PoolModel(PoolBaseModel):

    def __init__(self, obj):
        PoolBaseModel.__init__(self)
        self.obj = obj
        obj.Proxy.Machine.ctrlStart.connect(self.onCtrlStart)
        obj.Proxy.Machine.serialRead.connect(self.onSerialRead)

    @QtCore.Slot()    
    def onCtrlStart(self):
        self.title.emit("Initialisation in progress...")
        eol = self.obj.Proxy.getCharEndOfLine(self.obj)
        self.obj.Proxy.Machine.serialWrite(eol.join(self.initcmd))      
        
    @QtCore.Slot(unicode)    
    def onSerialRead(self, data):
        try:
            d = json.loads(data)
        except ValueError:
            self.onDataTxt(data)
        else:
            if d.has_key("r"):
                self.getDataDic(self.dickey["r"], d["r"])

    def onDataTxt(self, txt):
        if not txt or "]" not in txt:
            return
        i = txt.index("]")
        key = txt[1:i]
        if not self.dataKey.has_key(key):
            return
        value = txt[i+1:]
        values = value.split("  ")
        if len(values)>1:
            description = values[0].strip()
            unit = values[-1].strip()
        else:
            i = min(value.index("0"), value.index("1"))
            description = value[:i].strip()
            unit = value[i:].strip()
        self.setDataKey(key, description, "Description")
        self.setDataKey(key, unit, ("Unit (inches)", "Unit (mm)"))

    def getDataDic(self, dickey, data):
        if type(data) is dict:
            for k, value in data.iteritems():
                if type(dickey) is dict and dickey.has_key(k):
                    self.getDataDic(dickey[k], value)
        else:
            self.setDataKey(dickey, data, "Value")

    def setDataKey(self, key, value, header):
        if not self.dataKey.has_key(key):
            return
        self.dataKey[key][self._header.index(header)] = value

    @QtCore.Slot()
    def onInches(self):
        if self.getUnit() == 0:
            return
        if self.obj.Proxy.Machine.isRunning():
            self.obj.Proxy.Machine.serialWrite('G20')
            self.onCtrlStart()

    @QtCore.Slot()
    def onMetric(self):
        if self.getUnit() == 1:
            return
        if self.obj.Proxy.Machine.isRunning():
            self.obj.Proxy.Machine.serialWrite('G21')
            self.onCtrlStart()

    @QtCore.Slot(QtCore.QPoint, int)
    def onUnit(self, pos, index):
        if index != len(self._header) -1:
            return
        menu = QtGui.QMenu(self)
        inches = menu.addAction("Unit (inches)")
        inches.triggered.connect(self.onInches)
        metric = menu.addAction("Unit (mm)")
        metric.triggered.connect(self.onMetric)
        menu.exec_(pos)

    @QtCore.Slot(unicode)
    def setRootIndex(self, key):
        index = QtCore.QModelIndex()
        flag = QtCore.Qt.MatchFlags(QtCore.Qt.MatchRecursive)
        query = self.match(self.index(0,0), QtCore.Qt.DisplayRole, key, 1, flag)
        if query: index = query[0]
        self.rootIndex.emit(index)

    def flags(self, index=QtCore.QModelIndex()):
        if index.column() == self._header.index("Value") and\
           self.obj.Proxy.Machine.isRunning():
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled
        #return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return False
        if role == QtCore.Qt.EditRole:
            node = index.internalPointer()
            return self.doCommand(node.key, value)
        return False

    def doCommand(self, key, value):
        if not self.cmdKey.has_key(key):
            return False
        for path in self.cmdKey[key]:
            v = {path:value}
            value = v
        if not value.has_key("r"):
            return False        
        self.obj.Proxy.Machine.serialWrite(json.dumps(value["r"]))
        return True

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
