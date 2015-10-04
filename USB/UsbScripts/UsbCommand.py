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

import FreeCAD, FreeCADGui


class CommandRefresh:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Refresh.xpm",
                b'MenuText': b"Refresh port",
                b'Accel'   : b"U, R",
                b'ToolTip' : b"Refresh available port"}

    def IsActive(self):
        return not FreeCAD.ActiveDocument is None

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if len(selection) == 0:
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        obj = selection[0]
        from UsbScripts import UsbPool
        from UsbScripts import UsbPort
        if obj.isDerivedFrom("App::DocumentObjectGroupPython") and \
           isinstance(obj.Proxy, UsbPool.Pool):
            code = '''pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
for port in pool.Group:
    port.Update = ["Port", "Baudrate"]'''
        elif obj.isDerivedFrom("App::FeaturePython") and \
             isinstance(obj.Proxy, UsbPort.Port):
            code = '''port = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
port.Update = ["Port", "Baudrate"]'''
        else:
            FreeCAD.Console.PrintError("Selection is not a Pool or a Port!\n")
            return
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.recompute()


class CommandTerminal:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Terminal.xpm",
                b'MenuText': b"Terminal",
                b'Accel'   : b"U, T",
                b'ToolTip' : b"Connect/disconnect terminal"}

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
        if pool.Serials is None:
            code = '''pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
pool.Open = True'''
        else:
            code = '''pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
pool.Open = False'''
        FreeCADGui.doCommand(code)
        FreeCAD.ActiveDocument.recompute()


class CommandUpload:

    def GetResources(self):
        return {b'Pixmap'  : b"icons:Usb-Upload.xpm",
                b'MenuText': b"File upload",
                b'Accel'   : b"U, U",
                b'ToolTip' : b"Toggle file upload"}

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
        if pool.Serials is None:
            FreeCAD.Console.PrintError("Pool is not connected!\n")
            return
        if pool.Uploading.is_set():
            code = '''pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
pool.Uploading.clear()'''
        else:
            code = '''pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
pool.Uploading.set()'''
        FreeCADGui.doCommand(code)


if FreeCAD.GuiUp:
    # register the FreeCAD command
    FreeCADGui.addCommand('Usb_Refresh', CommandRefresh())
    FreeCADGui.addCommand('Usb_Terminal', CommandTerminal())
    FreeCADGui.addCommand('Usb_Upload', CommandUpload())

FreeCAD.Console.PrintLog("Loading UsbCommand... done\n")
