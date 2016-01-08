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
""" UsbPool Generic Model Plugin object """
from __future__ import unicode_literals

from PySide import QtCore


class PoolBaseModel(QtCore.QAbstractItemModel):

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self.obj = None

    def setModel(self, obj):
        self.obj = obj

    def index(self, row, column, parent=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    def parent(self, index=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        return None


class PoolModel(PoolBaseModel):

    def __init__(self, obj):
        PoolBaseModel.__init__(self)
        self.obj = obj
