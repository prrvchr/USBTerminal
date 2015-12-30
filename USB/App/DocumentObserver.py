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
from Gui import initResources


class DocumentObserver(QtCore.QObject):

    changedUsbPool = QtCore.Signal(object)
    line = QtCore.Signal(unicode)
    gcode = QtCore.Signal(unicode)
    data = QtCore.Signal(unicode)
    datadic = QtCore.Signal(dict)
    buffers = QtCore.Signal(unicode)
    settings = QtCore.Signal(unicode)

    def __init__(self):
        QtCore.QObject.__init__(self)

    def slotCreatedDocument(self, doc):
        pass

    def slotActivateDocument(self, doc):
        pass

    def slotDeletedDocument(self, doc):
        if FreeCAD.GuiUp:
            for o in doc.Objects:
                self.slotDeletedObject(o)

    def slotCreatedObject(self, obj):
        pass

    def slotDeletedObject(self, obj):
        if FreeCAD.GuiUp:
            if initResources.getObjectType(obj) == "App::UsbPool" and \
               obj.Proxy.Machine.isRunning():
                obj.Proxy.Machine.stop()
                QtCore.QThreadPool.globalInstance().waitForDone()

    def slotChangedObject(self, obj, prop):
        typ = initResources.getObjectType(obj)
        if typ == "App::UsbPool":
            if prop in ("Open", "Start", "Pause"):
                self.changedUsbPool.emit(obj)

    def slotUndoDocument(self, doc):
        pass

    def slotRedoDocument(self, doc):
        pass
