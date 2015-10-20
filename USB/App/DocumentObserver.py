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

from PySide.QtCore import QObject, Signal
from App import UsbCommand


class DocumentObserver(QObject):

    changedPort = Signal(object, unicode)

    def __init__(self):
        QObject.__init__(self)

    def slotDeletedObject(self, obj):
        pass

    def slotChangedObject(self, obj, prop):
        if UsbCommand.getObjectType(obj) == "App::UsbPort":
            self.changedPort.emit(obj, prop)

    def slotUndoDocument(self, doc):
        pass

    def slotRedoDocument(self, doc):
        pass