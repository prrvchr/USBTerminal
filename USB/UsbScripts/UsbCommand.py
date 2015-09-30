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


class CommandDualPort:

    def GetResources(self):
        return {'Pixmap'  : b"icons:Usb-Port.xpm",
                'MenuText': b"USB DualPort",
                'Accel'   : b"U, P",
                'ToolTip' : b"USB DualPort"}

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
        code = '''pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
while len(pool.Group) < int(pool.DualPort) + 1:
    FreeCADGui.runCommand("Usb_Port")'''
        FreeCADGui.doCommand(code)
        

class CommandRefreshPort:

    def GetResources(self):
        return {'Pixmap'  : b"icons:Usb-Port.xpm",
                'MenuText': b"Refresh port",
                'Accel'   : b"U, P",
                'ToolTip' : b"Refresh port"}

    def IsActive(self):
        return not FreeCAD.ActiveDocument is None

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)
        if len(selection) == 0:
            FreeCAD.Console.PrintError("Selection has no elements!\n")
            return
        port = selection[0]
        from UsbScripts import UsbPort
        if not port.isDerivedFrom("App::FeaturePython") or \
           not isinstance(port.Proxy, UsbPort.Port):
            FreeCAD.Console.PrintError("Selection is not a Port!\n")
            return
        code = '''port = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
index = port.Proxy.getPortsIndex(port.Ports)
port.update = False
port.Ports = port.Proxy.getPorts(port.Details)
if index != -1: 
    port.Ports = index
port.update = True'''
        FreeCADGui.doCommand(code)


class CommandTerminal:

    def GetResources(self):
        return {'Pixmap'  : b"icons:Usb-Terminal.xpm",
                'MenuText': b"Connect/Disconnect Terminal",
                'Accel'   : b"U, P",
                'ToolTip' : b"Connect/Disconnect Terminal"}

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
            code = '''from PySide import QtCore
from UsbScripts import UsbThread
from UsbScripts import TerminalDock
pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]
thread = UsbThread.UsbThread(pool)
dock = TerminalDock.TerminalDock(thread, pool)
FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)'''
        else:      
            code = '''from PySide import QtGui
pool = FreeCADGui.Selection.getSelection(FreeCAD.ActiveDocument.Name)[0]            
mw = FreeCADGui.getMainWindow()
dock = mw.findChild(QtGui.QDockWidget, pool.Document.Name+"-"+pool.Name)
dock.setParent(None)
dock.close()            
for i in range(len(pool.Serials)):
    pool.Serials[i].close()
pool.Serials = None'''            
        FreeCADGui.doCommand(code)


if FreeCAD.GuiUp: 
    # register the FreeCAD command
    FreeCADGui.addCommand('Usb_DualPort', CommandDualPort())
    FreeCADGui.addCommand('Usb_RefreshPort', CommandRefreshPort())    
    FreeCADGui.addCommand('Usb_Terminal', CommandTerminal())    

FreeCAD.Console.PrintLog("Loading UsbCommand... done\n")