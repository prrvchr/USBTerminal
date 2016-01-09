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
""" PySerial ViewProvider document object """
from __future__ import unicode_literals

import FreeCADGui
from PySide import QtCore, QtGui
from Gui import PySerialPanel, PySerialModel, TerminalDock


class _ViewProviderPort:

    def __init__(self, vobj): #mandatory
        self.Model = PySerialModel.PySerialModel(vobj.Object)
        self.Type = "Gui::PySerial"
        self.Object = vobj.Object
        vobj.Proxy = self

    def __getstate__(self): #mandatory
        return None

    def __setstate__(self, state): #mandatory
        return None

    def attach(self, vobj):
        print "PySerialGui.attach()"
        self.Model = PySerialModel.PySerialModel(vobj.Object)
        self.Type = "Gui::PySerial"
        self.Object = vobj.Object

    def getIcon(self):
        return "icons:Usb-PySerial.xpm"

    def getDisplayModes(self, vobj):
        modes = [b"Shaded"]
        return modes

    def getDefaultDisplayMode(self):
        return b"Shaded"

    def setDisplayMode(self, mode):
        return mode

    def onChanged(self, vobj, prop): #optional
        pass

    def updateData(self, obj, prop): #optional
        # this is executed when a property of the APP OBJECT changes
        if prop == "State" and obj.State == b"Open" and\
           obj.Proxy.hasParent(obj) and\
           obj.Proxy.getParent(obj).Proxy.Machine.isRunning() and\
           obj.Proxy.isCtrlChannel(obj):
            self.openTerminal(obj)

    def openTerminal(self, obj):
        o = obj.Proxy.getParent(obj)
        name = "{}-{}".format(o.Document.Name, o.Name)
        if FreeCADGui.getMainWindow().findChildren(QtGui.QDockWidget, name):
            return
        state = o.Proxy.getCtrlState(o)
        dock = TerminalDock.TerminalDock(state)
        FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def setEdit(self, vobj, mode=0):
        # this is executed when the object is double-clicked in the tree
        if FreeCADGui.Control.activeDialog():
            return
        panel = PySerialPanel.PySerialTaskPanel(vobj.Object)
        FreeCADGui.Control.showDialog(panel)

    def unsetEdit(self, vobj, mode=0):
        # this is executed when the user cancels or terminates edit mode
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()

    def doubleClicked(self, vobj):
        FreeCADGui.ActiveDocument.setEdit(vobj.Object.Name, 0)
