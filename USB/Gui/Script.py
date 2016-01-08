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
""" Resources directory initialization """
from __future__ import unicode_literals

import os
from PySide.QtCore import QDir


# Resources directory relative path
ICONS_PATH = "/Icons"

def initIcons():
    # use "icons" as prefix which we used in the .py file (pixmap: icons:file.svg)
    QDir.addSearchPath("icons", os.path.dirname(__file__) + ICONS_PATH)

def getObjectViewType(vobj):
    if not vobj or vobj.TypeId != "Gui::ViewProviderPythonFeature" and\
       vobj.TypeId != "Gui::ViewProviderDocumentObjectGroupPython":
        return None
    if "Proxy" in vobj.PropertiesList:
        if hasattr(vobj.Proxy, "Type"):
            return vobj.Proxy.Type
    return None
