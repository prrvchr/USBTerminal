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

import FreeCAD
from App import UsbPoolMachine, PySerial


class Pool:

    def __init__(self, obj):
        self.Type = "App::UsbPool"
        self.Plugin = "UsbPool"
        self.Machine = UsbPoolMachine.PoolMachine()
        for p in obj.PropertiesList:
            if obj.getGroupOfProperty(p) in ("Driver"):
                if p not in ("Device"):            
                    obj.removeProperty(p)        
        if "DualPort" not in obj.PropertiesList:
            obj.addProperty("App::PropertyBool",
                            "DualPort",
                            "Base",
                            "Enable/disable dual endpoint USB connection (Plugin dependent)", 1)
        obj.DualPort = False
        #obj.setEditorMode("DualPort", 1)
        if "EndOfLine" not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration",
                            "EndOfLine",
                            "Base",
                            "End of line char (\\r, \\n, or \\r\\n)")
            obj.EndOfLine = self.getEndOfLine()
            obj.EndOfLine = b"LF"
        """ Link to PySerial document object """
        if "Serials" not in obj.PropertiesList:
            obj.addProperty("App::PropertyLinkList",
                            "Serials",
                            "Base",
                            "Link to PySerial document object")
        """ Usb Base driving property """
        if "State" not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration",
                            "State",
                            "Base",
                            "State of USB Device Machine [On, Off, Error]", 1)
            obj.State = self.getState()
        """ Usb Device driver property """
        if "Device" not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration",
                            "Device",
                            "Driver",
                            "Usb Device Plugin driver")
            obj.Device = [b"Generic Device", b"TinyG2 Device"]
            obj.setEditorMode("Device", 1)
        obj.Device = 0
        obj.Proxy = self

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        self.Type = "App::UsbPool"
        self.Plugin = "UsbPool"
        self.Machine = UsbPoolMachine.PoolMachine()
        self.Update = True
        return None

    def setExtra(self, obj, extra):
        pass     
            
    def resetExtra(self, obj):
        pass

    def getState(self):
        return [b"Off", b"On", b"Error"]

    def getEndOfLine(self):
        return [b"CR", b"LF", b"CRLF"]

    def getIndexEndOfLine(self, obj):
        return self.getEndOfLine().index(obj.EndOfLine)

    def getCharEndOfLine(self, obj):
        return ["\r", "\n", "\r\n"][self.getIndexEndOfLine(obj)]

    def getCtrlChannel(self, obj):
        return obj.Serials[0]

    def getDataChannel(self, obj):
        return obj.Serials[int(obj.DualPort)]

    def getCtrlState(self, obj):
        return obj.Proxy.Machine.Serials[0]

    def getDataState(self, obj):
        return obj.Proxy.Machine.Serials[int(obj.DualPort)]

    def execute(self, obj):
        while len(obj.Serials) < int(obj.DualPort) + 1:
            o = obj.Document.addObject("App::FeaturePython", "PySerial")
            PySerial.PySerial(o)
            obj.Serials += [o]

    def onChanged(self, obj, prop):
        pass


FreeCAD.Console.PrintLog("Loading UsbPool... done\n")
