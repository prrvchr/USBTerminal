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
""" USB command object """
from __future__ import unicode_literals

import FreeCAD

if FreeCAD.GuiUp:
    import FreeCADGui


def getObjectType(obj):
    if not obj or (obj.TypeId != "App::DocumentObjectGroupPython"
                   and obj.TypeId != "App::FeaturePython"):
        return None
    if "Proxy" in obj.PropertiesList:
        if hasattr(obj.Proxy, "Type"):
            return obj.Proxy.Type
    return None


class CommandPool:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Pool.xpm",
                b'MenuText': b"New Pool",
                b'Accel'   : b"U, N",
                b'ToolTip' : b"New Pool"}

    def IsActive(self):
        return True

    def Activated(self):
        if FreeCAD.ActiveDocument is None:
            FreeCAD.newDocument()
        FreeCAD.ActiveDocument.openTransaction(b"New Pool")
        #FreeCADGui.addModule(b"App.UsbPool")
        code = '''from App import UsbPool
from Gui import DefaultGui as UsbPoolGui
obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", "Pool")
UsbPool.Pool(obj)
UsbPoolGui._ViewProviderPool(obj.ViewObject)'''
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class CommandRefresh:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Refresh.xpm",
                b'MenuText': b"Refresh port",
                b'Accel'   : b"U, R",
                b'ToolTip' : b"Refresh available port"}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        s = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if not len(s):
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        obj = s[0]
        if getObjectType(obj) == "App::UsbPool":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
for o in obj.Serials:
    o.Update = ["Port", "Baudrate"]'''
        elif getObjectType(obj) == "App::UsbPort":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.Update = ["Port", "Baudrate"]'''
        else:
            FreeCAD.Console.PrintError("Selection is not a Pool or a Port!\n")
            return
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.recompute()


class CommandOpen:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Terminal.xpm",
                b'MenuText': b"Open Terminal",
                b'Accel'   : b"U, T",
                b'ToolTip' : b"Connect/disconnect terminal"}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        s = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if len(s) == 0:
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        obj = s[0]
        if getObjectType(obj) == "App::UsbPool":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.Open = not obj.Open'''
        elif getObjectType(obj) == "App::UsbPort":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.InList[0].Open = not obj.InList[0].Open'''
        else:
            FreeCAD.Console.PrintError("Selection is not a Pool or a Port!\n")
            return
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.recompute()


class CommandStart:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Upload.xpm",
                b'MenuText': b"File upload",
                b'Accel'   : b"U, F",
                b'ToolTip' : b"Start/stop file upload"}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        s = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if not len(s):
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        obj = s[0]
        if getObjectType(obj) == "App::UsbPool":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.Start = not obj.Start'''
        elif getObjectType(obj) == "App::UsbPort":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.InList[0].Start = not obj.InList[0].Start'''
        else:
            FreeCAD.Console.PrintError("Selection is not a Pool or a Port!\n")
            return
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.recompute()


class CommandPause:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Pause.xpm",
                b'MenuText': b"Pause file upload",
                b'Accel'   : b"U, P",
                b'ToolTip' : b"Pause/resume file upload"}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        s = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if len(s) == 0:
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        obj = s[0]
        if getObjectType(obj) == "App::UsbPool":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.Pause = not obj.Pause'''
        elif getObjectType(obj) == "App::UsbPort":
            code = '''obj = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
obj.InList[0].Pause = not obj.InList[0].Pause'''
        else:
            FreeCAD.Console.PrintError("Selection is not a Pool or a Port!\n")
            return
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp:
    # register the FreeCAD command
    FreeCADGui.addCommand('Usb_Pool', CommandPool())
    FreeCADGui.addCommand('Usb_Refresh', CommandRefresh())
    FreeCADGui.addCommand('Usb_Open', CommandOpen())
    FreeCADGui.addCommand('Usb_Start', CommandStart())
    FreeCADGui.addCommand('Usb_Pause', CommandPause())

FreeCAD.Console.PrintLog("Loading UsbCommand... done\n")
