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
""" Minimal Pool default ViewProvider Plugin object """
from __future__ import unicode_literals

import FreeCADGui
from PySide.QtCore import Qt
from PySide.QtGui import QDockWidget
from Gui import UsbPortGui, TerminalDock, UsbPoolPanel


class _ViewProviderPool:

    def __init__(self, vobj): #mandatory
        self.Type = "Gui::UsbPool"
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

    def __getstate__(self): #mandatory
        return None

    def __setstate__(self, state): #mandatory
        return None

    def attach(self, vobj):
        self.Type = "Gui::UsbPool"
        self.Object = vobj.Object
        return

    def getIcon(self):
        return "icons:Usb-Pool.xpm"

    def onChanged(self, vobj, prop): #optional
        pass

    def getObjectViewType(self, vobj):
        if not vobj or vobj.TypeId != "Gui::ViewProviderPythonFeature":
            return None
        if "Proxy" in vobj.PropertiesList:
            if hasattr(vobj.Proxy, "Type"):
                return vobj.Proxy.Type
        return None

    def updateData(self, obj, prop): #optional
        # this is executed when a property of the APP OBJECT changes
        if prop == "Asyncs":
            for o in obj.Asyncs:
                if self.getObjectViewType(o.ViewObject) is None:
                    UsbPortGui._ViewProviderPort(o.ViewObject)
        if prop == "Open":
            if obj.Open:
                if obj.ViewObject.DualView:
                    d = TerminalDock.DualTerminalDock()
                else:
                    d = TerminalDock.TerminalDock()
                obj.Process.reader.read.connect(d.on_write)
                d.read.connect(obj.Process.on_write)
                d.setObjectName("{}-{}".format(obj.Document.Name, obj.Name))
                d.setWindowTitle("{} terminal".format(obj.Label))
                FreeCADGui.getMainWindow().addDockWidget(Qt.RightDockWidgetArea, d)
                eol = obj.Proxy.getCharEndOfLine(obj)
                obj.Process.reader.read.emit("Now, you are connected{}".format(eol))
                obj.Process.on_write("")
            else:
                objname = "{}-{}".format(obj.Document.Name, obj.Name)
                docks = FreeCADGui.getMainWindow().findChildren(QDockWidget, objname)
                for d in docks:
                    d.setParent(None)
                    d.close()

    def setEdit(self, vobj, mode=0):
        # this is executed when the object is double-clicked in the tree 
        #o = vobj.Object.Proxy.getClass(vobj.Object, vobj.Object.Plugin, "getUsbPoolPanel")
        taskPanel = UsbPoolPanel.UsbPoolTaskPanel(vobj.Object)
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()
        FreeCADGui.Control.showDialog(taskPanel)

    def unsetEdit(self, vobj, mode=0):
        # this is executed when the user cancels or terminates edit mode
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()

    def doubleClicked(self, vobj):
        self.setEdit(vobj, 0)
        return True

    def claimChildren(self):
        return  self.Object.Asyncs
