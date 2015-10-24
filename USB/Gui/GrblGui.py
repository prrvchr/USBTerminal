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
""" Grbl ViewProvider Plugin object """
from __future__ import unicode_literals

import FreeCADGui
from PySide.QtCore import Qt
from PySide.QtGui import QDockWidget
from Gui import UsbPoolGui, GrblPanel
from Gui import TerminalDock
from pivy import coin


class _ViewProviderPool(UsbPoolGui._ViewProviderPool):

    def __init__(self, vobj): #mandatory
        self.Type = "Gui::UsbGrbl"
        for p in vobj.PropertiesList:
            if vobj.getGroupOfProperty(p) != "Base":
                if p not in ["DualView"]:
                    vobj.removeProperty(p)
        if "DualView" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyBool",
                             "DualView",
                             "Terminal",
                             "Enable/disable terminal dualview")
            vobj.DualView = False
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self, vobj):
        UsbPoolGui._ViewProviderPool.attach(self, vobj)
        self.Type = "Gui::UsbGrbl"
        return

    def updateData(self, obj, prop): #optional
        # this is executed when a property of the APP OBJECT changes
        if prop == "Asyncs":
            UsbPoolGui._ViewProviderPool.updateData(self, obj, prop)
        if prop == "Open":
            if obj.Open:
                obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
                if obj.ViewObject.DualView:
                    d = TerminalDock.DualTerminalDock()
                else:
                    d = TerminalDock.TerminalDock()
                obj.Process.reader.read.connect(d.on_write)
                d.read.connect(obj.Process.on_write)
                d.setObjectName("{}-{}".format(obj.Document.Name, obj.Name))
                d.setWindowTitle("{} terminal".format(obj.Label))
                FreeCADGui.getMainWindow().addDockWidget(Qt.RightDockWidgetArea, d)
                obj.Process.on_write("$?{}".format(obj.Proxy.getCharEndOfLine(obj)))
            else:
                objname = "{}-{}".format(obj.Document.Name, obj.Name)
                docks = FreeCADGui.getMainWindow().findChildren(QDockWidget, objname)
                for d in docks:
                    d.setParent(None)
                    d.close()
        if prop == "Start":
            if obj.Start:
                obs = FreeCADGui.getWorkbench("UsbWorkbench").observer
                obj.Process.uploader.line.connect(obs.line)
                obj.Process.uploader.gcode.connect(obs.gcode)
                obj.Process.reader.buffers.connect(obs.buffers)

    def setEdit(self, vobj, mode=0):
        # this is executed when the object is double-clicked in the tree 
        #o = vobj.Object.Proxy.getClass(vobj.Object, vobj.Object.Plugin, "getUsbPoolPanel")
        taskPanel = GrblPanel.UsbPoolTaskPanel(vobj.Object)
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()
        FreeCADGui.Control.showDialog(taskPanel)
