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

import FreeCAD, serial, os, imp 
from PySide import QtCore
from App import PySerial
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
    from Gui import TerminalDock


class Pool:

    def __init__(self, obj):
        self.Type = "App::UsbPool"
        self.plugin = False
        """ Usb Plugin driver property """
        obj.addProperty("App::PropertyFile",
                        "Plugin",
                        "Plugin",
                        "Application Plugin driver")
        p = os.path.dirname(__file__) + "/../Plugins/DefaultPlugin.py"
        obj.Plugin = os.path.abspath(p)
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

    def getTerminalPort(self, obj):
        return obj.Serials[0]

    def openTerminalPort(self, obj):
        s = self.getTerminalPort(obj)
        return s.Proxy.openPySerial(s)

    def openTerminal(self, obj):
        d = TerminalDock.TerminalDock(obj)
        FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, d)

    def closeTerminal(self, obj):
        objname = "{}-{}".format(obj.Document.Name, obj.Name)
        docks = FreeCADGui.getMainWindow().findChildren(QtGui.QDockWidget, objname)
        for d in docks:
            d.setParent(None)
            d.close()

    def getControlPort(self, obj):
        return obj.Serials[-1]

    def openControlPort(self, obj):
        s = self.getControlPort(obj)
        return s.Proxy.openPySerial(s)

    def getEndOfLine(self):
        return [b"CR",b"LF",b"CRLF"]

    def getIndexEndOfLine(self, obj):
        return self.getEndOfLine().index(obj.EndOfLine)

    def getCharEndOfLine(self, obj):
        return ["\r","\n","\r\n"][self.getIndexEndOfLine(obj)]

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
        if self.plugin:
            self.getClass(obj, obj.Plugin, "InitializePlugin")
            self.plugin = False
            # Need to clear selection for change take effect in property view
            if FreeCAD.GuiUp and FreeCADGui.Selection.isSelected(obj):
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(obj)

    def onChanged(self, obj, prop):
        if prop == "Plugin":
            if obj.Plugin:
                self.plugin = True
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
