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
from App import Script as AppScript
from Gui import UsbPoolPanel, TinyG2Model, Script as GuiScript


class PoolTaskPanel(UsbPoolPanel.PoolTaskPanel):

    def __init__(self, obj):
        view = PoolPanel()
        model = obj.ViewObject.Proxy.Model
        if model.obj is None: model.obj = obj
        view.setModel(model)
        self.form = [view]


class SettingTabBar(QtGui.QTabBar):

    tabIndex = QtCore.Signal(unicode)

    def __init__(self, parent):
        QtGui.QTabBar.__init__(self, parent)
        self.setShape(QtGui.QTabBar.RoundedWest)
        self.setDocumentMode(True)
        self.setTabData(self.addTab("All"), "r")
        self.setTabData(self.addTab("Axis"), "q")
        self.setTabData(self.addTab("Home"), "o")
        self.setTabData(self.addTab("Motor"), "m")
        self.setTabData(self.addTab("Power"), "p1")
        self.setTabData(self.addTab("System"), "sys")
        self.currentChanged.connect(self.onTabIndex)

    @QtCore.Slot(int)
    def onTabIndex(self, index):
        self.tabIndex.emit(self.tabData(index))


class PoolPanel(QtGui.QTabWidget):

    def __init__(self):
        QtGui.QTabWidget.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Pool.xpm"))
        setting = QtGui.QWidget()
        setting.setLayout(QtGui.QHBoxLayout())
        self.tabbar = SettingTabBar(self)
        setting.layout().addWidget(self.tabbar)
        #model.state.connect(tabbar.on_state)
        self.tableview = UsbPoolView(self)
        setting.layout().addWidget(self.tableview)
        self.addTab(setting, "Current settings")
        monitor = QtGui.QWidget()
        monitor.setLayout(QtGui.QGridLayout())
        monitor.layout().addWidget(QtGui.QLabel("Line/N:"), 0, 0, 1, 1)
        line = QtGui.QLabel()
        monitor.layout().addWidget(line, 0, 1, 1, 1)
        monitor.layout().addWidget(QtGui.QLabel("/"), 0, 2, 1, 1)
        nline = QtGui.QLabel()
        monitor.layout().addWidget(nline, 0, 3, 1, 1)
        #model.nline.connect(nline.setText)
        monitor.layout().addWidget(QtGui.QLabel("GCode:"), 1, 0, 1, 1)
        gcode = QtGui.QLabel()
        monitor.layout().addWidget(gcode, 1, 1, 1, 3)
        monitor.layout().addWidget(QtGui.QLabel("Buffers:"), 2, 0, 1, 1)
        buffers = QtGui.QLabel()
        monitor.layout().addWidget(buffers, 2, 1, 1, 3)
        #model.buffers.connect(buffers.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosX:"), 3, 0, 1, 1)
        posx = QtGui.QLabel()
        monitor.layout().addWidget(posx, 3, 1, 1, 3)
        #model.posx.connect(posx.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosY:"), 4, 0, 1, 1)
        posy = QtGui.QLabel()
        monitor.layout().addWidget(posy, 4, 1, 1, 3)
        #model.posy.connect(posy.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosZ:"), 5, 0, 1, 1)
        posz = QtGui.QLabel()
        monitor.layout().addWidget(posz, 5, 1, 1, 3)
        #model.posz.connect(posz.setText)
        monitor.layout().addWidget(QtGui.QLabel("Vel:"), 6, 0, 1, 1)
        vel = QtGui.QLabel()
        monitor.layout().addWidget(vel, 6, 1, 1, 3)
        #model.vel.connect(vel.setText)
        monitor.layout().addWidget(QtGui.QLabel("Feed:"), 7, 0, 1, 1)
        feed = QtGui.QLabel()
        monitor.layout().addWidget(feed, 7, 1, 1, 3)
        #model.feed.connect(feed.setText)
        monitor.layout().addWidget(QtGui.QLabel("Status:"), 8, 0, 1, 1)
        stat = QtGui.QLabel()
        monitor.layout().addWidget(stat, 8, 1, 1, 3)
        #model.stat.connect(stat.setText)
        self.addTab(monitor, "Upload monitor")

    def setModel(self, model):
        self.tabbar.tabIndex.connect(model.setRootIndex)
        model.title.connect(self.onTitle)
        model.title.emit("test")
        self.tableview.setModel(model)

    @QtCore.Slot(unicode)
    def onTitle(self, title):
        self.setWindowTitle(title)


class UsbPoolView(QtGui.QTreeView):
    
    unit = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        model = TinyG2Model.PoolBaseModel()
        i = model._header.index("Value")
        self.setItemDelegateForColumn(i, TinyG2Model.PoolDelegate(self))        
        self.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(self.onUnit)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

    def setModel(self, model):
        model.rootIndex.connect(self.setRootIndex)
        self.unit.connect(model.onUnit)
        QtGui.QTreeView.setModel(self, model)

    @QtCore.Slot(int)
    def onUnit(self, pos):
        self.unit.emit(self.mapToGlobal(pos), self.header().logicalIndexAt(pos))


class TaskWatcher:

    def __init__(self):
        self.title = b"TinyG2 monitor"
        self.icon = b"icons:Usb-Pool.xpm"
        self.model = TinyG2Model.PoolBaseModel()
        self.view = PoolPanel()
        self.widgets = [self.view]

    def shouldShow(self):
        for obj in FreeCADGui.Selection.getSelection():
            if AppScript.getObjectType(obj) == "App::UsbPool" and\
               GuiScript.getObjectViewType(obj.ViewObject) == "Gui::UsbTinyG2":
                self.view.setModel(obj.ViewObject.Proxy.Model)
                return True
        self.view.setModel(self.model)
        return False
