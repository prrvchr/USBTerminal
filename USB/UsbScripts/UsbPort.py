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
        """ PySerial discovered port tools """
        obj.addProperty("App::PropertyEnumeration", "Details", "Discovered ports", "Ports detail")
        obj.Details = self.getDetails()
        obj.Details = b"Detail"
        obj.addProperty("App::PropertyEnumeration", "Ports", "Discovered ports", "Ports discovered")
        obj.Ports = self.getPorts(obj.Details)
        obj.addProperty("App::PropertyBool", "update", "Discovered ports", "Need update PySerial port", 2, True, True)
        obj.update = True
        """ PySerial port property """
        obj.addProperty("App::PropertyEnumeration", "Baudrate", "Port", "Set baud rate, default 115200")
        obj.Baudrate = map(str, serial.Serial().BAUDRATES)
        obj.Baudrate = b"115200"
        obj.addProperty("App::PropertyEnumeration", "ByteSize", "Port", "ByteSize")
        obj.ByteSize = map(str, serial.Serial().BYTESIZES)
        obj.ByteSize = b"8"
        obj.addProperty("App::PropertyBool", "DsrDtr", "Port", "set initial DTR line state")
        obj.DsrDtr = False
        obj.addProperty("App::PropertyFloat", "InterCharTimeout", "Port", "InterCharTimeout")
        obj.InterCharTimeout = -1
        obj.addProperty("App::PropertyEnumeration", "Parity", "Port", "set parity (None, Even, Odd, Space, Mark) default N")
        obj.Parity = map(str, serial.Serial().PARITIES)
        obj.Parity = b"N"
        obj.addProperty("App::PropertyString", "Port", "Port", "Port, a number or a device name")
        obj.addProperty("App::PropertyBool", "RtsCts", "Port", "enable RTS/CTS flow control")
        obj.RtsCts = False
        obj.addProperty("App::PropertyEnumeration", "StopBits", "Port", "StopBits")
        obj.StopBits = map(str, serial.Serial().STOPBITS)
        obj.StopBits = b"1"
        obj.addProperty("App::PropertyFloat", "Timeout", "Port", "Timeout")
        obj.Timeout = 0.05
        obj.addProperty("App::PropertyFloat", "WriteTimeout", "Port", "WriteTimeout")
        obj.WriteTimeout = 0.05
        obj.addProperty("App::PropertyBool", "XonXoff", "Port", "enable software flow control")
        obj.XonXoff = False
        obj.Proxy = self

    def getDetails(self):
        return [b"Detail", b"Standart", b"VID:PID"]
    def getDetailsIndex(self, detail):
        return self.getDetails().index(detail)
    
    def getPorts(self, detail):
        return [x[self.getDetails().index(detail)] for x in list_ports.comports()]
    def getPortsIndex(self, port):
        #Get the index of the port:
        ports = list_ports.grep("(^{}$)".format(port))
        try:
            i = list_ports.comports().index(ports.next())
        except (StopIteration, ValueError) as e:
            return -1
        try:
            ports.next()
        except StopIteration as e:
            return i
        return -1

    def getSettingsDict(self, obj):
        return {b"port" : b"{}".format(obj.Port),
                b"baudrate" : int(obj.Baudrate),
                b"bytesize" : int(obj.ByteSize),
                b"parity" : b"{}".format(obj.Parity),
                b"stopbits" : float(obj.StopBits),
                b"xonxoff" : obj.XonXoff,
                b"rtscts" : obj.RtsCts,
                b"dsrdtr" : obj.DsrDtr,
                b"timeout" : None if obj.Timeout < 0 else obj.Timeout,
                b"writeTimeout" : None if obj.WriteTimeout < 0 else obj.WriteTimeout,
                b"interCharTimeout" : None if obj.InterCharTimeout < 0 else obj.InterCharTimeout}

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "Details":
            FreeCADGui.runCommand("Usb_RefreshPort")
        if prop == "Ports":
            if obj.update and self.getPortsIndex(obj.Ports) != -1:
                if self.getDetailsIndex(obj.Details) == 0:
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
        return {'Pixmap'  : b"icons:Usb-Port.xpm",
                'MenuText': b"New Port",
                'Accel'   : b"U, P",
                'ToolTip' : b"New Port"}

    def IsActive(self):
        return not FreeCAD.ActiveDocument is None

    def Activated(self):
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





