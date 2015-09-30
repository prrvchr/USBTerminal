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

import FreeCAD, FreeCADGui


class Pool:

    def __init__(self, obj):
        obj.addProperty("App::PropertyBool", "DualPort", "Pool","DualPort")
        obj.DualPort = False
        obj.addProperty("App::PropertyBool", "DualView", "Pool","DualView")
        obj.DualView = False
        obj.addProperty("App::PropertyEnumeration", "EndOfLine", "Pool","End of line")
        obj.EndOfLine = self.getEndOfLine()
        obj.EndOfLine = b"LF"
        obj.addProperty("App::PropertyPythonObject", "Serials", "Pool","PySerial object", 2)
        obj.Serials = None
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
            FreeCADGui.runCommand("Usb_DualPort")


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
        return {'Pixmap'  : b"icons:Usb-Pool.xpm",
                'MenuText': b"New Pool",
                'Accel'   : b"U, T",
                'ToolTip' : b"New Pool"}

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
FreeCADGui.runCommand("Usb_DualPort")'''
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp: 
    # register the FreeCAD command
    FreeCADGui.addCommand('Usb_Pool', CommandUsbPool())

FreeCAD.Console.PrintLog("Loading UsbPool... done\n")





