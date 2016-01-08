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
""" UsbPool panel Plugin object """
from __future__ import unicode_literals

import FreeCADGui
from PySide import QtCore, QtGui
from App import  Script as AppScript
from Gui import UsbPoolModel, Script as GuiScript


class PoolTaskPanel:

    def __init__(self, obj):
        view = PoolPanel()
        model = obj.ViewObject.Proxy.Model
        if model.obj is None: model.obj = obj
        view.setModel(model)
        self.form = [view]

    def accept(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def reject(self):
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
        return False

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok)
        #return int(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)

    def helpRequested(self):
        pass


class PoolPanel(QtGui.QGroupBox):

    def __init__(self):
        QtGui.QGroupBox.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Pool.xpm"))
        layout = QtGui.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        txt = QtGui.QLabel("Not implemented in this plugin!!!")
        layout.addWidget(txt, 0, 0, 1, 1)
        txt1 = QtGui.QLabel("Chose another plugin in Pool properties")
        layout.addWidget(txt1, 1, 0, 1, 1)

    def setModel(self, model):
        if model.obj is not None:
            self.setWindowTitle("Usb {} monitor".format(model.obj.Label))


class TaskWatcher:

    def __init__(self):
        self.title = b"Pool monitor"
        self.icon = b"icons:Usb-Pool.xpm"
        self.model = UsbPoolModel.PoolBaseModel()
        self.view = PoolPanel()
        self.widgets = [self.view]

    def shouldShow(self):
        for obj in FreeCADGui.Selection.getSelection():
            if AppScript.getObjectType(obj) == "App::UsbPool" and\
               GuiScript.getObjectViewType(obj.ViewObject) == "Gui::UsbPool":
                model = obj.ViewObject.Proxy.Model
                if model.obj is None: model.obj = obj
                self.view.setModel(model)
                return True
        self.view.setModel(self.model)
        return False
