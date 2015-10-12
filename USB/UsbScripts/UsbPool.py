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
""" Pool document object """
from __future__ import unicode_literals

from os import path
from PySide.QtCore import QThread, Qt
from PySide.QtGui import QDockWidget
import FreeCAD, FreeCADGui
import serial, imp


class Pool:

    def __init__(self, obj):
        """ PySerial port object instance property """
        obj.addProperty("App::PropertyPythonObject",
                        "Serials",
                        "Base",
                        "Array of PySerial port instance", 2)
        obj.Serials = None
        obj.addProperty("App::PropertyPythonObject",
                        "Thread",
                        "Base",
                        "QThread pointer", 2)
        obj.Thread = None
        obj.addProperty("App::PropertyBool",
                        "Open",
                        "Base",
                        "Open/close terminal connection", 2)
        obj.Open = False
        obj.addProperty("App::PropertyBool",
                        "Start",
                        "Base",
                        "Start/stop file upload", 2)
        obj.Start = False
        obj.addProperty("App::PropertyBool",
                        "Pause",
                        "Base",
                        "Pause/resume file upload", 2)
        obj.Pause = False
        """ Usb pool property """
        obj.addProperty("App::PropertyInteger",
                        "Buffers",
                        "Pool",
                        "Upload file buffers to keep free")
        obj.Buffers = 5
        obj.addProperty("App::PropertyFile",
                        "Driver",
                        "Pool",
                        "File upload driver")
        obj.Driver = path.dirname(__file__) + "/Drivers/UsbDriver.py"
        obj.addProperty("App::PropertyBool",
                        "DualPort",
                        "Pool",
                        "Enable/disable dual endpoint USB connection")
        obj.DualPort = False
        obj.addProperty("App::PropertyEnumeration",
                        "EndOfLine",
                        "Pool",
                        "End of line char (\\r, \\n, or \\r\\n)")
        obj.EndOfLine = self.getEndOfLine()
        obj.EndOfLine = b"LF"
        obj.addProperty("App::PropertyInteger",
                        "DrawSpeed",
                        "Pool",
                        "Number of position queued before draw")
        obj.DrawSpeed = 5
        obj.addProperty("App::PropertyColor",
                        "DrawColor",
                        "Pool",
                        "Drawing color")
        obj.DrawColor = (1.0, 0.0, 0.0)
        """ Usb terminal property """
        obj.addProperty("App::PropertyBool", "DualView", "Terminal",\
                        "Enable/disable terminal dualview")
        obj.DualView = False
        obj.addProperty("App::PropertyFile", "UploadFile", "Terminal",\
                        "Files to upload")
        obj.UploadFile = path.dirname(__file__) + "/Examples/boomerangv4.ncc"
        obj.Proxy = self

    def getEndOfLine(self):
        return [b"CR",b"LF",b"CRLF"]

    def getIndexEndOfLine(self, obj):
        return self.getEndOfLine().index(obj.EndOfLine)

    def getCharEndOfLine(self, obj):
        return ["\r","\n","\r\n"][self.getIndexEndOfLine(obj)]

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
                b"write_timeout" : None if obj.WriteTimeout < 0 else obj.WriteTimeout,
                b"inter_byte_timeout" : None if obj.InterByteTimeout < 0 else obj.InterByteTimeout}

    def execute(self, obj):
        pass

    def getDriver(self, obj):
        driver = None
        class_name = "UsbDriver"
        mod_name, file_ext = path.splitext(path.split(obj.Driver)[-1])
        if file_ext.lower() == '.py':
            mod = imp.load_source(mod_name, obj.Driver)
        elif file_ext.lower() == '.pyc':
            mod = imp.load_compiled(mod_name, obj.Driver)
        if hasattr(mod, class_name):
            driver = getattr(mod, class_name)(obj)
        return driver
            
    def onChanged(self, obj, prop):
        if prop == "Thread":
            if obj.Thread is None:
                for s in obj.Serials:
                    if s.is_open:
                        s.close()
                ports = [s.port for s in obj.Serials]
                msg = "{} closing port {}... done\n"
                FreeCAD.Console.PrintLog(msg.format(obj.Name, ports))                
            elif obj.Serials is not None:
                code = '''from PySide.QtCore import Qt
from UsbScripts import TerminalDock
pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
dock = TerminalDock.TerminalDock(pool)
FreeCADGui.getMainWindow().addDockWidget(Qt.RightDockWidgetArea, dock)'''
                FreeCADGui.doCommand(code)
        if prop == "DualPort":
            while len(obj.Group) < int(obj.DualPort) + 1:
                FreeCADGui.runCommand("Usb_Port")
        if prop == "Serials":
            if obj.Serials is None:
                objname = "{}-{}".format(obj.Document.Name, obj.Name)
                docks = FreeCADGui.getMainWindow().findChildren(QDockWidget, objname) 
                for d in docks:
                    d.setParent(None)
                    d.close()
            else:
                for i, s in enumerate(obj.Serials):
                    s.apply_settings(self.getSettingsDict(obj.Group[i]))
        if prop == "Open":
            if obj.Open:
                serials = []
                for i in range(int(obj.DualPort) + 1):
                    serials.append(serial.serial_for_url(obj.Group[i].Port, do_not_open=True))
                obj.Serials = serials
                try:
                    for s in obj.Serials:
                        s.open()
                except serial.SerialException as e:
                    msg = "Error occurred opening port: {}\n"
                    FreeCAD.Console.PrintError(msg.format(e))
                    obj.Serials = None
                    obj.Open = False
                    return
                ports = [s.port for s in obj.Serials]
                msg = "{} opening port {}... done\n"
                FreeCAD.Console.PrintLog(msg.format(obj.Name, ports))
                obj.Thread = self.getDriver(obj)
                if obj.Thread is None:
                    return
                obj.Thread.open()
            elif obj.Thread is not None:
                obj.Thread.close()
        if prop == "Start":
            if obj.Thread is None or obj.Serials is None:
                if obj.Start:
                    obj.Start = False
                return
            if obj.Start:
                obj.Thread.start()
            else:
                obj.Thread.stop()
        if prop == "Pause":
            if obj.Thread is None or obj.Serials is None:
                if obj.Pause:
                    obj.Pause = False
                return
            if obj.Pause:
                obj.Thread.pause()
            else:
                obj.Thread.resume()
                

class _ViewProviderPool:

    def __init__(self, vobj): #mandatory
        vobj.Proxy = self

    def __getstate__(self): #mandatory
        return None

    def __setstate__(self, state): #mandatory
        return None

    def getIcon(self):
        return "icons:Usb-Pool.xpm"

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


class CommandUsbPool:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Pool.xpm",
                b'MenuText': b"New Pool",
                b'Accel'   : b"U, N",
                b'ToolTip' : b"New Pool"}

    def IsActive(self):
        return not FreeCAD.ActiveDocument is None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction(b"New Pool")
        FreeCADGui.addModule(b"UsbScripts.UsbPool")
        code = '''from UsbScripts import UsbPool
FreeCADGui.Selection.clearSelection(FreeCAD.ActiveDocument.Name)
obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", "Pool")
UsbPool.Pool(obj)
UsbPool._ViewProviderPool(obj.ViewObject)
FreeCADGui.Selection.addSelection(obj)
FreeCADGui.runCommand("Usb_Port")'''
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp: 
    # register the FreeCAD command
    FreeCADGui.addCommand('Usb_Pool', CommandUsbPool())

FreeCAD.Console.PrintLog("Loading UsbPool... done\n")
