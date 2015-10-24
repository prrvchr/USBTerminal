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
""" Grbl Gui and Driver Plugin """
from __future__ import unicode_literals

import FreeCAD
from os import path
from App import UsbCommand, GrblDriver
if FreeCAD.GuiUp:
    import FreeCADGui
    from Gui import GrblGui, GrblPanel, UsbPortPanel


''' Add/Delete App Object Plugin custom property '''
def InitializePlugin(obj):
    for p in obj.PropertiesList:
        if obj.getGroupOfProperty(p) in ["Plugin", "Pool"]:
            if p not in ["Buffers", "UploadFile", "Plugin", "DualPort", "EndOfLine"]:
                obj.removeProperty(p)
    if "ReadOnly" not in obj.getEditorMode("DualPort"):
        obj.setEditorMode("DualPort", 1)
    if obj.DualPort:
        obj.DualPort = False
    if "Buffers" not in obj.PropertiesList:
        obj.addProperty("App::PropertyInteger",
                        "Buffers",
                        "Pool",
                        "Upload file buffers to keep free")
        obj.Buffers = 5
    if "UploadFile" not in obj.PropertiesList:
        obj.addProperty("App::PropertyFile",
                        "UploadFile",
                        "Pool",
                        "Files to upload")
        p = path.dirname(__file__) + "/../Examples/boomerangv4.ncc"
        obj.UploadFile = path.abspath(p)
    if FreeCAD.GuiUp:
        GrblGui._ViewProviderPool(obj.ViewObject)

def getUsbThread(obj):
    return GrblDriver.UsbThread(obj)


class TaskWatcher:

    def __init__(self):
        self.title = b"Grbl monitor"
        self.icon = b"icons:Usb-Pool.xpm"
        self.model = GrblPanel.PoolModel()
        self.widgets = [GrblPanel.UsbPoolPanel(self.model)]

    def shouldShow(self):
        s = FreeCADGui.Selection.getSelection()
        if len(s):
            o = s[0]
            if UsbCommand.getObjectType(o) == "App::UsbPool"\
               and o.ViewObject.Proxy.Type == "Gui::UsbGrbl":
                self.model.setModel(o)
                return True
        self.model.on_change(None)
        return False
