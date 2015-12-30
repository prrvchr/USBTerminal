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

from PySide import QtCore, QtGui
import FreeCAD, FreeCADGui, io, json, importlib


class UsbPoolMachine(QtCore.QStateMachine):

    def __init__(self):
        QtCore.QStateMachine.__init__(self)
        self.obj = None
        self.init = False
        self.run = False
        
        On = OnState(self)
        On.setChildMode(QtCore.QState.ParallelStates)
        On.setObjectName("On")
        Off = OffState(self)
        Off.setObjectName("Off")
        Error = ErrorState(self)
        Error.setObjectName("Error")

        On.setErrorState(Error)
        On.addTransition(On, b"finished()", Off)
        self.setInitialState(On)
        
    def start(self):
        if not self.init:
            self.initStates()
        QtCore.QStateMachine.start(self)
            
    def initStates(self):
        self.initState(self.obj.Serials[0])
        if self.obj.DualPort:
            self.initState(self.obj.Serials[1])
            QtCore.QThreadPool.globalInstance().setMaxThreadCount(2)
        elif len(self.obj.Serials) > 1:
            self.resetState(self.obj.Serials[1])
        self.init = True
        
    def initState(self, obj):
        state = obj.Proxy.States
        state.init = obj.Proxy.isInit(obj)
        state.setParent(self.initialState())

    def resetState(self, obj):
        obj.Proxy.States.setParent(None)

    def stop(self):
        self.run = False

    def getCharEndOfLine(self):
        return self.obj.Proxy.getCharEndOfLine(self.obj)


class OnState(QtCore.QState):

    def onEntry(self, e):
        self.machine().obj.State = b"{}".format(self.objectName())


class OffState(QtCore.QFinalState):

    def onEntry(self, e):
        self.machine().obj.State = b"{}".format(self.objectName())


class ErrorState(QtCore.QFinalState):

    def onEntry(self, e):
        self.machine().obj.State = b"{}".format(self.objectName())
 