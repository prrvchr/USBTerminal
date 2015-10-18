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
""" Pool Gui and Driver Plugin """
from __future__ import unicode_literals

import FreeCAD
from App import DefaultDriver as UsbPoolDriver
if FreeCAD.GuiUp:
    from Gui import DefaultGui as UsbPoolGui


''' Add/Delete Object Plugin custom property '''
def InitializePlugin(obj):
    for p in obj.PropertiesList:
        if obj.getGroupOfProperty(p) in ["Plugin", "Pool"]:
            if p not in ["Plugin", "DualPort", "EndOfLine"]:
                obj.removeProperty(p)
    if "ReadOnly" not in obj.getEditorMode("DualPort"):
        obj.setEditorMode("DualPort", 1)    
    if obj.DualPort:
        obj.DualPort = False
    if FreeCAD.GuiUp:
        UsbPoolGui._ViewProviderPool(obj.ViewObject)


def getUsbThread(obj):
    return UsbPoolDriver.UsbThread(obj)
