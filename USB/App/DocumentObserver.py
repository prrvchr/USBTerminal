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
""" Document Observer Object """
from __future__ import unicode_literals

import FreeCAD, FreeCADGui
from PySide import QtCore
from App import Script


class DocumentObserver(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)

    def slotCreatedDocument(self, doc):
        pass

    def slotActivateDocument(self, doc):
        pass

    def slotDeletedDocument(self, doc):
        for obj in doc.Objects:
            self.slotDeletedObject(obj)

    def slotCreatedObject(self, obj):
        pass

    def slotDeletedObject(self, obj):
        if Script.getObjectType(obj) == "App::PySerial":           
            if obj.Proxy.hasParent(obj):
                obj = obj.Proxy.getParent(obj)
        if Script.getObjectType(obj) == "App::UsbPool" and\
           obj.Proxy.Machine.isRunning():
            obj.Proxy.Machine.halt()
            obj.Proxy.Machine.pool.waitForDone()

    def slotChangedObject(self, obj, prop):
        typ = Script.getObjectType(obj)
        if typ == "App::UsbPool":
            if prop in ("Open", "Start", "Pause"):
                self.changedUsbPool.emit(obj)

    def slotUndoDocument(self, doc):
        pass

    def slotRedoDocument(self, doc):
        pass
