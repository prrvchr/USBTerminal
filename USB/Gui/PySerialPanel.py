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
""" PySerial Plugin Monitor object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCAD, FreeCADGui
from Gui import initResources
import serial


class PySerialTaskPanel:

    def __init__(self, obj):
        form = []
        for o in obj.Serials:
            panel = PySerialPanel()
            panel.setModel(o.Proxy.Machine.model)
            form.append(panel)
        self.form = form

    def accept(self):
        if FreeCADGui.ActiveDocument is not None:
            FreeCADGui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        if FreeCADGui.ActiveDocument is not None:
            FreeCADGui.ActiveDocument.resetEdit()
        return True

    def clicked(self, index):
        pass

    def open(self):
        pass

    def needsFullSpace(self):
        return False

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return True

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok)
        #return int(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)

    def helpRequested(self):
        pass


class PySerialPanel(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-PySerial.xpm"))
        self.setWindowTitle("PySerial version {}".format(serial.VERSION))
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.view = PySerialView()
        self.layout().addWidget(self.view)

    def setModel(self, model):
        self.view.setModel(model)


class PySerialView(QtGui.QTableView):

    def __init__(self):
        QtGui.QTableView.__init__(self)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)


class TaskWatcher:

    def __init__(self):
        self.title = b"PySerial version {}".format(serial.VERSION)
        self.icon = b"icons:Usb-PySerial.xpm"
        self.view = PySerialPanel()
        self.widgets = [self.view]

    def shouldShow(self):
        s = FreeCADGui.Selection.getSelection()
        if len(s):
            o = s[0]
            if initResources.getObjectType(o) == "App::PySerial":
                self.view.setModel(o.Proxy.Machine.model)
                return True
        self.view.setModel(None)
        return False
