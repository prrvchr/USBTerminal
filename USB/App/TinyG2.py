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
""" Usb Pool TinyG2 Plugins document """
from __future__ import unicode_literals

import FreeCAD, os
from  App import UsbPool, TinyG2Machine


class Pool(UsbPool.Pool):

    def __init__(self, obj):
        self.Machine = TinyG2Machine.PoolMachine()
        self.Plugin = "TinyG2"
        self.Update = False
        self.Type = "App::UsbPool"
        for p in obj.PropertiesList:
            if obj.getGroupOfProperty(p) in ("Driver"):
                if p not in ("Buffers", "Device", "Id", "Message", "Timeout", "UploadFile"):
                    obj.removeProperty(p)
        if "ReadOnly" in obj.getEditorMode("DualPort"):
            obj.setEditorMode("DualPort", 0)
        if not obj.DualPort:
            obj.DualPort = True
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
        if "Message" not in obj.PropertiesList:
            obj.addProperty("App::PropertyString",
                            "Message",
                            "Driver",
                            "Usb Device message")
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
        """ Usb Device driver property """
        if "Device" not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration",
                            "Device",
                            "Driver",
                            "Usb Device Plugin driver", 1)
            obj.Device = self.getDevice()
        obj.Device = 1
        obj.Proxy = self

    def __setstate__(self, state):
        self.Machine = TinyG2Machine.PoolMachine()
        self.Plugin = "TinyG2"
        self.Update = False
        self.Type = "App::UsbPool"
        return None

    def setExtra(self, obj, extra):
        obj.Id = extra["id"]
        obj.Message = extra["msg"]


FreeCAD.Console.PrintLog("Loading TinyG2... done\n")
