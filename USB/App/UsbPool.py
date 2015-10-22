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
import serial 
import imp
import FreeCAD
from App import UsbPort
if FreeCAD.GuiUp:
    import FreeCADGui



class Pool:

    def __init__(self, obj):
        self.Type = "App::UsbPool"
        self.plugin = False
        """ Usb Plugin driver property """
        obj.addProperty("App::PropertyFile",
                        "Plugin",
                        "Plugin",
                        "Application Plugin driver")
        p = path.dirname(__file__) + "/../Plugins/DefaultPlugin.py"
        obj.Plugin = path.abspath(p)
        """ Link to UsbPort document object """
        obj.addProperty("App::PropertyLinkList",
                        "Asyncs",
                        "Base",
                        "Link to UsbPort document object")
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
        """ Usb Pool property """
        obj.addProperty("App::PropertyBool",
                        "DualPort",
                        "Pool",
                        "Enable/disable dual endpoint USB connection (Plugin dependent)")
        obj.DualPort = False
        obj.setEditorMode("DualPort", 1)
        obj.addProperty("App::PropertyEnumeration",
                        "EndOfLine",
                        "Pool",
                        "End of line char (\\r, \\n, or \\r\\n)")
        obj.EndOfLine = self.getEndOfLine()
        obj.EndOfLine = b"LF"
        """ QThread object instance property """
        obj.addProperty("App::PropertyPythonObject",
                        "Process",
                        "Base",
                        "QThread process driver pointer", 2)
        obj.Process = None
        obj.Proxy = self

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        self.Type = "App::UsbPool"
        self.plugin = False
        return None

    def getEndOfLine(self):
        return [b"CR",b"LF",b"CRLF"]

    def getIndexEndOfLine(self, obj):
        return self.getEndOfLine().index(obj.EndOfLine)

    def getCharEndOfLine(self, obj):
        return ["\r","\n","\r\n"][self.getIndexEndOfLine(obj)]

    def getClass(self, obj, source, attr):
        classInstance = None
        moduleName, fileExt = path.splitext(path.split(source)[-1])
        if fileExt.lower() == ".py":
            module = imp.load_source(moduleName, source)
        elif fileExt.lower() == ".pyc":
            module = imp.load_compiled(moduleName, source)
        if hasattr(module, attr):
            classInstance = getattr(module, attr)(obj)
        return classInstance

    def execute(self, obj):
        if len(obj.Asyncs) < int(obj.DualPort) + 1:
            FreeCAD.ActiveDocument.openTransaction(b"New Port")
            o = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Port")
            UsbPort.Port(o)
            # UsbPortGui._ViewProviderPort(o.ViewObject) is made with the Asyncs
            # property change in Gui part of Plugin: updateData()
            obj.Asyncs += [o]
            FreeCAD.ActiveDocument.commitTransaction()
            FreeCAD.ActiveDocument.recompute()
        if self.plugin:
            self.getClass(obj, obj.Plugin, "InitializePlugin")
            if FreeCAD.GuiUp:
                # Need to clear selection for change take effect in property view
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(obj)
            self.plugin = False

    def onChanged(self, obj, prop):
        if prop == "Plugin":
            if obj.Plugin:
                self.plugin = True
        if prop == "Open":
            if obj.Open:
                obj.Asyncs[0].Open = True
                obj.Process = self.getClass(obj, obj.Plugin, "getUsbThread")
            else:
                obj.Process.close()
        if prop == "Start":
            if not obj.Open:
                if obj.Start:
                    obj.Start = False
                return
            if obj.Start:
                obj.Process.start()
            else:
                obj.Process.stop()
        if prop == "Pause":
            if not obj.Open or not obj.Start:
                if obj.Pause:
                    obj.Pause = False
                return
            if obj.Pause:
                obj.Process.pause()
            else:
                obj.Process.resume()


FreeCAD.Console.PrintLog("Loading UsbPool... done\n")
