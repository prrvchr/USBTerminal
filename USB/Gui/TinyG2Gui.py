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
""" TinyG2 ViewProvider Plugin object """
from __future__ import unicode_literals

import FreeCADGui
from Gui import UsbPoolGui, TinyG2Panel, TinyG2Model
from pivy import coin


class _ViewProviderPool(UsbPoolGui._ViewProviderPool):

    def __init__(self, vobj): #mandatory
        self.Model = TinyG2Model.PoolModel(vobj.Object)
        self.Type = "Gui::UsbTinyG2"
        for p in vobj.PropertiesList:
            if vobj.getGroupOfProperty(p) in ["Drawing", "Terminal"]:
                if p not in ["Buffers", "Color", "Draw", "Positions", "DualView", "EchoFilter"]:
                    vobj.removeProperty(p)
        if "Buffers" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyInteger",
                             "Buffers",
                             "Drawing",
                             "Number of position queued before display")
            vobj.Buffers = 5
        if "Color" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyColor",
                             "Color",
                             "Drawing",
                             "Drawing color")
            vobj.Color = (1.0, 0.0, 0.0)
        if "Draw" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyBool",
                             "Draw",
                             "Drawing",
                             "Draw positions received during upload")
            vobj.Draw = True
        if "Positions" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyPythonObject",
                             "Positions",
                             "Drawing",
                             "List of positions acquired during upload")
            vobj.Positions = []
        if "DualView" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyBool",
                             "DualView",
                             "Terminal",
                             "Enable/disable terminal dualview")
            vobj.DualView = False
        if "EchoFilter" not in vobj.PropertiesList:
            vobj.addProperty("App::PropertyBool",
                             "EchoFilter",
                             "Terminal",
                             "Filter terminal echo during upload")
            vobj.EchoFilter = True
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self, vobj):
        self.Model = TinyG2Model.PoolModel(vobj.Object)
        self.Type = "Gui::UsbTinyG2"
        self.Object = vobj.Object

    def onChanged(self, vobj, prop):
        if prop == "Positions":
            if not vobj.Draw:
                return
            if vobj.Proxy.indexPosition:
                po = list(vobj.Positions[vobj.Proxy.indexPosition-1:])
            else:
                po = list(vobj.Positions[vobj.Proxy.indexPosition:])
            vobj.Proxy.indexPosition = len(vobj.Positions)
            co = coin.SoCoordinate3()
            co.point.setValues(0, len(po), po)
            ma = coin.SoBaseColor()
            ma.rgb = vobj.Color[0:3]
            li = coin.SoLineSet()
            li.numVertices.setValue(len(po))
            no = coin.SoSeparator()
            no.addChild(co)
            no.addChild(ma)
            no.addChild(li)
            vobj.RootNode.addChild(no)

    def setEdit(self, vobj, mode=0):
        # this is executed when the object is double-clicked in the tree
        if FreeCADGui.Control.activeDialog():
            return
        panel = TinyG2Panel.PoolTaskPanel(vobj.Object)
        FreeCADGui.Control.showDialog(panel)
