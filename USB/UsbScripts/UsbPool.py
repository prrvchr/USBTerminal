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
        """ Array of PySerial port object instance """
        obj.addProperty("App::PropertyPythonObject", "Serials", "Base", "", 2)
        obj.Serials = None
        """ Usb pool property """
        obj.addProperty("App::PropertyBool", "DualPort", "Pool","Enable/disable dualport connection (fullduplex)")
        obj.DualPort = False
        obj.addProperty("App::PropertyEnumeration", "EndOfLine", "Pool","End of line char (\\r, \\n, or \\r\\n)")
        obj.EndOfLine = self.getEndOfLine()
        obj.addProperty("App::PropertyBool", "Open", "Pool", "Open the connection", 2)
        obj.Open = False
        obj.addProperty("App::PropertyBool", "DualView", "Terminal","Enable/disable terminal dualview")
        obj.DualView = False
        obj.EndOfLine = b"LF"
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
                dock = TerminalDock.TerminalDock(thread, obj)
                FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock) 
            else:
                mw = FreeCADGui.getMainWindow()
                dock = mw.findChild(QtGui.QDockWidget, obj.Document.Name+"-"+obj.Name)
                dock.setParent(None)
                dock.close()
                obj.Serials = None                
            

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
                b'Accel'   : b"U, T",
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





