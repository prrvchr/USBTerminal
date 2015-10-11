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
""" Port document object """
from __future__ import unicode_literals

import FreeCAD, FreeCADGui
import serial
from serial.tools import list_ports


class Port:

    def __init__(self, obj):
        """ Internal property for management of data update """
        obj.addProperty("App::PropertyStringList",
                        "Update",
                        "Base",
                        "Feature list of port to update", 2, True, True)
        """ PySerial discovered port tools """
        obj.addProperty("App::PropertyEnumeration",
                        "Details",
                        "Discovery tool",
                        "Discovered ports view mode")
        obj.Details = self.getDetails()
        obj.Details = b"Detail"
        obj.addProperty("App::PropertyEnumeration",
                        "Ports",
                        "Discovery tool",
                        "Discovered ports (perhaps need refresh?)")
        obj.Ports = self.getPorts(obj)
        """ PySerial port property """
        obj.addProperty("App::PropertyEnumeration",
                        "Baudrate",
                        "PySerial",
                        "Set baud rate (default 115200)")
        obj.Baudrate = map(str, serial.Serial().BAUDRATES)
        obj.Baudrate = b"115200"
        obj.addProperty("App::PropertyEnumeration",
                        "ByteSize",
                        "PySerial",
                        "ByteSize")
        obj.ByteSize = map(str, serial.Serial().BYTESIZES)
        obj.ByteSize = b"8"
        obj.addProperty("App::PropertyBool",
                        "DsrDtr",
                        "PySerial",
                        "set initial DTR line state")
        obj.DsrDtr = False
        obj.addProperty("App::PropertyFloat",
                        "InterByteTimeout",
                        "PySerial",
                        "InterByteTimeout")
        obj.InterByteTimeout = -1
        obj.addProperty("App::PropertyEnumeration",
                        "Parity",
                        "PySerial",
                        "set parity (None, Even, Odd, Space, Mark) default N")
        obj.Parity = map(str, serial.Serial().PARITIES)
        obj.Parity = b"N"
        obj.addProperty("App::PropertyString",
                        "Port",
                        "PySerial",
                        "Port, a number or a device name")
        obj.addProperty("App::PropertyBool",
                        "RtsCts",
                        "PySerial",
                        "enable RTS/CTS flow control")
        obj.RtsCts = False
        obj.addProperty("App::PropertyEnumeration",
                        "StopBits",
                        "PySerial",
                        "StopBits")
        obj.StopBits = map(str, serial.Serial().STOPBITS)
        obj.StopBits = b"1"
        obj.addProperty("App::PropertyFloat",
                        "Timeout",
                        "PySerial",
                        "Set a read timeout (negative value wait forever)")
        obj.Timeout = 0.01
        obj.addProperty("App::PropertyFloat",
                        "WriteTimeout",
                        "PySerial",
                        "WriteTimeout")
        obj.WriteTimeout = -1
        obj.addProperty("App::PropertyBool",
                        "XonXoff", "PySerial",
                        "enable software flow control")
        obj.XonXoff = False
        obj.Proxy = self

    def getDetails(self):
        return [b"Detail", b"Standart", b"VID:PID"]

    def getDetailsIndex(self, obj):
        return self.getDetails().index(obj.Details)

    def getPorts(self, obj):
        return [x[self.getDetailsIndex(obj)] for x in list_ports.comports()]

    def getPortsIndex(self, obj):
        #Get the index of the port:
        try:
            ports = list_ports.grep("^{}$".format(obj.Ports))
            i = self.getPorts(obj).index(ports.next()[self.getDetailsIndex(obj)])
        except (AssertionError, StopIteration, ValueError) as e:
            return -1
        try:
            ports.next()
        except StopIteration as e:
            return i
        return -1

    def refreshPorts(self, obj):
        index = self.getPortsIndex(obj)
        obj.Ports = self.getPorts(obj)
        if index != -1: 
            obj.Ports = index

    def refreshBaudrate(self, obj):
        baudrate = obj.Baudrate
        obj.Baudrate = map(str, serial.Serial().BAUDRATES)
        obj.Baudrate = baudrate

    def execute(self, obj):
        if not obj.Update:
            return
        for name in obj.Update:
            if name == "Port":
                self.refreshPorts(obj)
            if name == "Baudrate":
                self.refreshBaudrate(obj)
        obj.Update = []

    def onChanged(self, obj, prop):
        if prop == "Details":
            obj.Update = ["Port"]
            self.refreshPorts(obj)
            obj.Update = []
        if prop == "Ports":
            if not obj.Update and self.getPortsIndex(obj) != -1:
                if self.getDetailsIndex(obj) == 0:
                    obj.Port = obj.Ports
                else:
                    obj.Port = "hwgrep://" + obj.Ports


class _ViewProviderPort:

    def __init__(self, vobj): #mandatory
        vobj.Proxy = self

    def __getstate__(self): #mandatory
        return None

    def __setstate__(self, state): #mandatory
        return None

    def getIcon(self):
        return "icons:Usb-Port.xpm"

    def onChanged(self, vobj, prop): #optional
        pass

    def updateData(self, vobj, prop): #optional
        # this is executed when a property of the APP OBJECT changes
        pass

    def setEdit(self, vobj, mode): #optional
        # this is executed when the object is double-clicked in the tree
        pass

    def unsetEdit(self, vobj, mode): #optional
        # this is executed when the user cancels or terminates edit mode
        pass


class CommandUsbPort:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Port.xpm",
                b'MenuText': b"New Port",
                b'Accel'   : b"U, P",
                b'ToolTip' : b"New Port"}

    def IsActive(self):
        return not FreeCAD.ActiveDocument is None

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if len(selection) == 0:
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        pool = selection[0]
        from UsbScripts import UsbPool
        if not pool.isDerivedFrom("App::DocumentObjectGroupPython") or \
           not isinstance(pool.Proxy, UsbPool.Pool):
            FreeCAD.Console.PrintError("Selection is not a Pool!\n")
            return
        FreeCAD.ActiveDocument.openTransaction(b"New Port")
        FreeCADGui.addModule(b"UsbScripts.UsbPort")
        code = '''from UsbScripts import UsbPort
obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Port")
UsbPort.Port(obj)
UsbPort._ViewProviderPort(obj.ViewObject)
FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0].addObject(obj)'''
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp: 
    # register the FreeCAD command
    FreeCADGui.addCommand('Usb_Port', CommandUsbPort())

FreeCAD.Console.PrintLog("Loading UsbPort... done\n")
