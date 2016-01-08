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

import FreeCADGui, sys
from Gui import Script, UsbPoolPanel, UsbPoolModel, PySerialGui


class _ViewProviderPool:

    def __init__(self, vobj): #mandatory
        self.Model = UsbPoolModel.PoolModel(vobj.Object)
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
        self.Model = UsbPoolModel.PoolModel(vobj.Object)
        self.Type = "Gui::UsbPool"        
        self.Object = vobj.Object

    def getIcon(self):
        return "icons:Usb-Pool.xpm"

    def getDisplayModes(self, vobj):
        modes = [b"Shaded"]
        return modes

    def getDefaultDisplayMode(self):
        return b"Shaded"

    def setDisplayMode(self, mode):
        return mode

    def onChanged(self, vobj, prop): #optional
        pass          

    def updateData(self, obj, prop): #optional
        # this is executed when a property of the APP OBJECT changes
        if prop == "Serials":
            for o in obj.Serials:
                if Script.getObjectViewType(o.ViewObject) is None:
                    PySerialGui._ViewProviderPort(o.ViewObject)

    def setEdit(self, vobj, mode=0):
        # this is executed when the object is double-clicked in the tree
        if FreeCADGui.Control.activeDialog():
            return
        panel = UsbPoolPanel.PoolTaskPanel(vobj.Object)            
        FreeCADGui.Control.showDialog(panel)

    def unsetEdit(self, vobj, mode=0):
        # this is executed when the user cancels or terminates edit mode
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()

    def doubleClicked(self, vobj):
        FreeCADGui.ActiveDocument.setEdit(vobj.Object.Name, 0)

    def claimChildren(self):
        return  self.Object.Serials
