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

from PySide import QtCore, QtGui
import FreeCAD, FreeCADGui
from UsbScripts import UsbThread
from UsbScripts import TerminalDock


class Pool:

    def __init__(self, obj):
        """ PySerial port object instance property """
        obj.addProperty("App::PropertyPythonObject", "Serials", "Base", "Array of PySerial port instance", 2)
        obj.Serials = None
        obj.addProperty("App::PropertyBool", "Open", "Base", "Setting open/close the connection", 2, True, True)
        obj.Open = False
        obj.addProperty("App::PropertyPythonObject", "Uploading", "Base", "Event switch of upload", 2)
        obj.Uploading = None
        """ Usb pool property """
        obj.addProperty("App::PropertyBool", "DualPort", "Pool", "Enable/disable dualport connection (fullduplex)")
        obj.DualPort = False
        obj.addProperty("App::PropertyEnumeration", "EndOfLine", "Pool", "End of line char (\\r, \\n, or \\r\\n)")
        obj.EndOfLine = self.getEndOfLine()
        obj.EndOfLine = b"LF"
        obj.addProperty("App::PropertyStringList", "AckList", "Terminal", "Acknowledge string list")
        obj.addProperty("App::PropertyBool", "DualView", "Terminal", "Enable/disable terminal dualview")
        obj.DualView = False
        obj.addProperty("App::PropertyFile", "UploadFile", "Terminal", "Files to upload")
        obj.Proxy = self

    def getEndOfLine(self):
        return [b"CR",b"LF",b"CRLF"]

    def getIndexEndOfLine(self, obj):
        return self.getEndOfLine().index(obj.EndOfLine)

    def getCharEndOfLine(self, obj):
        return ["\r","\n","\r\n"][self.getIndexEndOfLine(obj)]

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "DualPort":
            while len(obj.Group) < int(obj.DualPort) + 1:
                FreeCADGui.runCommand("Usb_Port")
        if prop == "Open":
            if obj.Open:
                thread = UsbThread.UsbThread(obj)
                if thread.start():
                    dock = TerminalDock.TerminalDock(obj, thread)
                    FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
                else:
                    del thread
            else:
                if not obj.Uploading.is_set():
                    obj.Uploading.set()
                mw = FreeCADGui.getMainWindow()
                docks = mw.findChildren(QtGui.QDockWidget, obj.Document.Name+"-"+obj.Name)
                for dock in docks:
                    dock.setParent(None)
                    dock.close()
                obj.Serials = None
                obj.Uploading = None


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
                b'Accel'   : b"U, L",
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
