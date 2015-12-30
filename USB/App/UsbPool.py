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
""" Usb Pool document object """
from __future__ import unicode_literals

import FreeCAD, os
from App import PySerial, UsbPoolMachine


class Pool:

    def __init__(self, obj):
        self.Type = "App::UsbPool"
        self.Machine = UsbPoolMachine.UsbPoolMachine()
        """ Usb device driver property """
        obj.addProperty("App::PropertyEnumeration",
                        "Device",
                        "Driver",
                        "Usb Device Plugin driver")
        obj.Device = self.getDevice()
        obj.Device = 0
        obj.setEditorMode("Device", 1)
        """ Link to PySerial document object """
        obj.addProperty("App::PropertyLinkList",
                        "Serials",
                        "Base",
                        "Link to PySerial document object")
        """ Usb Base driving property """
        obj.addProperty("App::PropertyEnumeration",
                        "State",
                        "Base",
                        "State of USB Device Machine [On, Off, Error]", 2)
        obj.State = self.getState()
        obj.State = b"Off"
        obj.setEditorMode("State", 1)
        """ Usb PySerial property """
        obj.addProperty("App::PropertyBool",
                        "DualPort",
                        "PySerial",
                        "Enable/disable dual endpoint USB connection (Plugin dependent)")
        obj.DualPort = False
        obj.setEditorMode("DualPort", 1)
        obj.addProperty("App::PropertyEnumeration",
                        "EndOfLine",
                        "PySerial",
                        "End of line char (\\r, \\n, or \\r\\n)")
        obj.EndOfLine = self.getEndOfLine()
        obj.EndOfLine = b"LF"
        obj.Proxy = self

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        self.Type = "App::UsbPool"
        self.Machine = UsbPoolMachine.UsbPoolMachine()
        return None
    
    def getState(self):
        return [b"On", b"Off", b"Error"]

    def getDevice(self):
        return [b"Generic Device", b"TinyG2 Device"]

    def getIndexDevice(self, obj):
        return self.getDevice().index(obj.Device)

    def getEndOfLine(self):
        return [b"CR", b"LF", b"CRLF"]

    def getIndexEndOfLine(self, obj):
        return self.getEndOfLine().index(obj.EndOfLine)

    def getCharEndOfLine(self, obj):
        return ["\r", "\n", "\r\n"][self.getIndexEndOfLine(obj)]

    def getClass(self, obj, source, attr):
        classInstance = None
        moduleName, fileExt = os.path.splitext(os.path.split(source)[-1])
        if fileExt.lower() == ".py":
            module = imp.load_source(moduleName, source)
        elif fileExt.lower() == ".pyc":
            module = imp.load_compiled(moduleName, source)
        if hasattr(module, attr):
            classInstance = getattr(module, attr)(obj)
        return classInstance

    def execute(self, obj):
        if len(obj.Serials) < int(obj.DualPort) + 1:
            o = obj.Document.addObject("App::FeaturePython", "PySerial")
            PySerial.PySerial(o)
            obj.Serials += [o]

    def onChanged(self, obj, prop):
        if prop == "DualPort":
            self.Machine.init = False
        if prop == "Proxy":
            self.Machine.obj = obj


FreeCAD.Console.PrintLog("Loading UsbPool... done\n")
