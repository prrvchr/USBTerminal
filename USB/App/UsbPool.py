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

import FreeCAD, serial, os, importlib
from PySide import QtCore
from App import PySerial, UsbPoolMachine, PluginMachine
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
    from Gui import TerminalDock


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

    def isInitPort(self, obj, port):
        return obj.Serials[0] == port

    def getTerminal(self, obj):
        objectName = "{}-{}".format(obj.Document.Name, obj.Name)
        return FreeCADGui.getMainWindow().findChildren(QtGui.QDockWidget, objectName)

    def openTerminal(self, obj, thread):
        if self.getTerminal(obj):
            return
        d = TerminalDock.TerminalDock(obj, thread)
        FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, d)

    def closeTerminal(self, obj):
        for d in self.getTerminal(obj):
            d.setParent(None)
            d.close()

    def getControlPort(self, obj):
        return obj.Serials[-1]

    def openControlPort(self, obj):
        s = self.getControlPort(obj)
        return s.Proxy.openPySerial(s)

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
        if prop == "Open":
            if obj.Open:
                obj.Proxy.Machine.start(obj)
            else:
                obj.Proxy.Machine.stop()
        if prop == "Device1":
            if obj.Proxy.Machine.isRunning():
                device = obj.Proxy.getIndexDevice(obj)
                if device == 0:
                    obj.Proxy.PluginMachine = PluginMachine.GenericMachine(obj)
                if device == 1:
                    obj.Proxy.PluginMachine = PluginMachine.TinyG2Machine(obj)


FreeCAD.Console.PrintLog("Loading UsbPool... done\n")
