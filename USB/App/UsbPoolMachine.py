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
""" UsbPool StateMachine document object """
from __future__ import unicode_literals

from PySide import QtCore
import FreeCAD, FreeCADGui, io, json, importlib


class UsbPoolMachine(QtCore.QStateMachine):

    initError = QtCore.Signal()

    def __init__(self):
        QtCore.QStateMachine.__init__(self)
        self.obj = None
        self.serial = None
        self.sio = None
        On = QtCore.QState(self)
        On.setObjectName("On")
        Off = QtCore.QFinalState(self)
        Off.setObjectName("Off")
        Error = ErrorState(self)
        Error.setObjectName("Error")
        Open = OpenState(On)
        Open.setObjectName("Open")

        On.setInitialState(Open)
        On.setErrorState(Error)
        Open.addTransition(self, b"stopped()", Off)
        Open.addTransition(self, b"initError()", Error)
        Error.addTransition(Off)
        self.setInitialState(On)

    def start(self, obj):
        self.obj = obj
        QtCore.QStateMachine.start(self)

    def stop(self):
        self.obj.Proxy.PluginMachine.stop()
        QtCore.QStateMachine.stop(self)

    @QtCore.Slot(object)
    def onPlugin(self, obj):
        machine = self.obj.Proxy.PluginMachine
        machine.machine = obj
        machine.start()


class OpenState(QtCore.QState):

    def onEntry(self, e):
        obj = self.machine().obj
        for o in obj.Serials:
            if obj.Proxy.isInitPort(obj, o):
                machine = o.Proxy.Machine
                machine.pluginReady.connect(self.machine().onPlugin)
                machine.initError.connect(self.machine().initError)
                #self.machine().stopped.connect(machine.stopped)
                machine.start(o, True)

class ErrorState(QtCore.QState):

    def onEntry(self, e):
        obj = self.machine().obj
        obj.Open  = False