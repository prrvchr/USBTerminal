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
""" TinyG2 Gui and Driver Plugin """
from __future__ import unicode_literals

import FreeCAD, os
if FreeCAD.GuiUp:
    import FreeCADGui
    from Gui import TinyG2Gui, TinyG2Model, TinyG2Panel, initResources


''' Add/Delete App Object Plugin custom property '''
def initDevice(obj, device, extra):
    for p in obj.PropertiesList:
        if obj.getGroupOfProperty(p) in ("Driver"):
            if p not in ("Buffers", "Device", "Id", "Message", "Timeout", "UploadFile"):
                obj.removeProperty(p)
    if "ReadOnly" in obj.getEditorMode("DualPort"):
        obj.setEditorMode("DualPort", 0)
    if "Buffers" not in obj.PropertiesList:
        obj.addProperty("App::PropertyIntegerConstraint",
                        "Buffers",
                        "Driver",
                        "Upload file buffers to keep free")
        obj.Buffers = (5,0,28,1)
    if "Id" not in obj.PropertiesList:
        obj.addProperty("App::PropertyString",
                        "Id",
                        "Driver",
                        "Usb Device Id")
    obj.Id = extra["id"]
    if "Message" not in obj.PropertiesList:
        obj.addProperty("App::PropertyString",
                        "Message",
                        "Driver",
                        "Usb Device message")
    obj.Message = extra["msg"]
    if "Timeout" not in obj.PropertiesList:
        obj.addProperty("App::PropertyIntegerConstraint",
                        "Timeout",
                        "Driver",
                        "Buffers dump timeout (ms:0->1000)")
        obj.Timeout = (500,0,1000,1)
    if "UploadFile" not in obj.PropertiesList:
        obj.addProperty("App::PropertyFile",
                        "UploadFile",
                        "Driver",
                        "Files to upload")
        p = os.path.dirname(__file__) + "/../Examples/boomerangv4.ncc"
        obj.UploadFile = os.path.abspath(p)
    obj.Device = device
    if FreeCAD.GuiUp:
        TinyG2Gui._ViewProviderPool(obj.ViewObject)
        #obj.Proxy.openTerminal(obj)
    #obj.Document.recompute()

class TaskWatcher:

    def __init__(self):
        self.title = b"TinyG2 monitor"
        self.icon = b"icons:Usb-Pool.xpm"
        self.model = TinyG2Model.PoolModel()
        self.widgets = getPanels(self.model)

    def shouldShow(self):
        s = FreeCADGui.Selection.getSelection()
        if len(s):
            o = s[0]
            if initResources.getObjectType(o) == "App::UsbPool"\
               and o.ViewObject.Proxy.Type == "Gui::UsbTinyG2":
                self.model.setModel(o)
                return True
        self.model.setModel(None)
        return False
