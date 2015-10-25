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
""" UsbPort ViewProvider document object """
from __future__ import unicode_literals

import FreeCADGui
from PySide import QtGui
from Gui import UsbPortPanel


class _ViewProviderPort:

    def __init__(self, vobj): #mandatory
        self.Type = "Gui::UsbPort"
        vobj.Proxy = self

    def __getstate__(self): #mandatory
        return None

    def __setstate__(self, state): #mandatory
        return None

    def attach(self, vobj):
        pass

    def getIcon(self):
        return "icons:Usb-Port.xpm"

    def onChanged(self, vobj, prop): #optional
        pass

    def updateData(self, obj, prop): #optional
        # this is executed when a property of the APP OBJECT changes
        if prop == "Async":
            if obj.Async is not None and FreeCADGui.Control.activeDialog():
                obj.Label = obj.Label

    def setEdit(self, vobj, mode):
        # this is executed when the object is double-clicked in the tree
        if FreeCADGui.Control.activeDialog():
            return
        t = UsbPortPanel.UsbPortTaskPanel(vobj.Object.InList[0])
        FreeCADGui.Control.showDialog(t)

    def unsetEdit(self, vobj, mode):
        # this is executed when the user cancels or terminates edit mode
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()
    
    def doubleClicked(self, vobj):
        FreeCADGui.ActiveDocument.setEdit(vobj.Object.Name, 0)
