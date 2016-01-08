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
import FreeCAD
from App import PySerialState


class PoolMachine(QtCore.QStateMachine):

    ctrlStart = QtCore.Signal()
    ctrlStop = QtCore.Signal()
    serialRead = QtCore.Signal(unicode)
    restart = QtCore.Signal(object)

    def __init__(self):
        QtCore.QStateMachine.__init__(self)
        self.pool = QtCore.QThreadPool(self)
        self.obj = None
        self.run = False
        self.close = False
        self.plugin = None

        On = OnState(QtCore.QState.ParallelStates, self)
        On.setObjectName("On")
        Serial0 = PySerialState.SerialState(On)
        Serial1 = PySerialState.SerialState(On)
        Off = OffState(self)
        Off.setObjectName("Off")
        Error = ErrorState(self)
        Error.setObjectName("Error")

        On.setErrorState(Error)
        On.addTransition(On, b"finished()", Off)
        self.setInitialState(On)
        self.Serials = [Serial0, Serial1]
        self.restart.connect(self.onRestart, QtCore.Qt.QueuedConnection)

    @QtCore.Slot(object)
    def onRestart(self, obj):
        mod = b"{}".format(self.plugin)
        app = __import__("App", globals(), locals(), [mod])
        getattr(app, mod).Pool(obj)
        mod = b"{}Gui".format(self.plugin)
        gui = __import__("Gui", globals(), locals(), [mod])
        getattr(gui, mod)._ViewProviderPool(obj.ViewObject)
        obj.Proxy.Machine.start(obj)
        
    def start(self, obj):
        self.obj = obj
        self.obj.touch()
        self.obj.Document.recompute()
        self.setMachine()
        self.run = True
        QtCore.QStateMachine.start(self)
        
    def setMachine(self):
        self.Serials[0].obj = self.obj.Serials[0]
        self.Serials[1].setParent(None)

    def halt(self):
        self.close = False
        self.run = False

    def stop(self):
        self.close = True
        self.run = False
        
    @QtCore.Slot(unicode)
    def serialWrite(self, data):
        self.getCtrlState().serialWrite.emit(data)

    def getCtrlState(self):
        return self.obj.Proxy.getCtrlState(self.obj)

    def getCharEndOfLine(self):
        return self.obj.Proxy.getCharEndOfLine(self.obj)

    def machineErrorMsg(self, e):
        msg = "Error occurred in {} StateMachine: {}\n"
        FreeCAD.Console.PrintError(msg.format(self.obj.Label, e))

    def startThread(self, thread):
        if not self.pool.maxThreadCount() > self.pool.activeThreadCount():
            self.pool.setMaxThreadCount(self.pool.activeThreadCount() +1)
        self.pool.start(thread) 


class OnState(QtCore.QState):

    def onEntry(self, e):
        self.machine().obj.State = b"{}".format(self.objectName())


class OffState(QtCore.QFinalState):

    def onEntry(self, e):
        # Need to try: on close document serialClose is emited...
        # and obj already deleted
        try:
            self.machine().obj.State = b"{}".format(self.objectName())
            self.machine().obj.purgeTouched()
        except ReferenceError:
            pass        
        self.machine().finished.emit()
        


class ErrorState(QtCore.QFinalState):

    def onEntry(self, e):
        self.machine().obj.State = b"{}".format(self.objectName())
        self.machine().machineErrorMsg(self.machine().errorString())


class WaitMachine(QtCore.QRunnable):

    def __init__(self, machine):
        QtCore.QRunnable.__init__(self)
        self.machine = machine

    def run(self):
        """ Wait for StateMachine stop"""
        try:
            while self.machine.running:
                pass
            print "WaitMachine.done"
        except Exception as e:
            self.machine.machineErrorMsg(e)
