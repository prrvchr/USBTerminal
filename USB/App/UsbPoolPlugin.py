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
""" Usb Pool Plugins document """
from __future__ import unicode_literals

import FreeCAD, os
if FreeCAD.GuiUp:
    from Gui import UsbPoolGui, TinyG2Gui


''' Add/Delete App Object Plugin custom property '''
def initPlugin(obj, device, extra):
    if device == 0:
        initGenericPlugin(obj)
    elif device == 1:
        initTinyG2Plugin(obj, extra)

def initGenericPlugin(obj):
    for p in obj.PropertiesList:
        if obj.getGroupOfProperty(p) in ("Driver"):
            if p not in ("Device"):
                obj.removeProperty(p)
    if "ReadOnly" not in obj.getEditorMode("DualPort"):
        obj.setEditorMode("DualPort", 1)
    if obj.DualPort:
        obj.DualPort = False
    if FreeCAD.GuiUp:
        UsbPoolGui._ViewProviderPool(obj.ViewObject)

def initTinyG2Plugin(obj, extra):
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
    if FreeCAD.GuiUp:
        TinyG2Gui._ViewProviderPool(obj.ViewObject)



def resetPlugin(obj):
    i = obj.Proxy.getIndexDevice(obj)
    if i == 0:
        pass
    elif i == 1:
        obj.Id = ""
        obj.Message = ""
