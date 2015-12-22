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
""" Plugin StateMachine document object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCAD, FreeCADGui, io, json, importlib
from Gui import TerminalDock


class GenericMachine(QtCore.QStateMachine):

    def __init__(self, obj):
        QtCore.QStateMachine.__init__(self)
        self.obj = obj
        self.machine = None
        On = QtCore.QState(self)
        On.setObjectName("On")
        Off = OffState(self)
        Off.setObjectName("Off")
        Error = QtCore.QState(self)
        Error.setObjectName("Error")
        Open = OpenState(On)
        Open.setObjectName("Open")

        On.setInitialState(Open)
        On.setErrorState(Error)
        Open.addTransition(self, b"stopped()", Off)
        Error.addTransition(Off)
        self.setInitialState(On)

    def stop(self):
        self.stopped.emit()

    def getStates(self):
        states = []
        for s in self.configuration():
            states.append(s.objectName())
        return states

    def getTerminal(self):
        objectName = "{}-{}".format(self.obj.Document.Name, self.obj.Name)
        return FreeCADGui.getMainWindow().findChildren(QtGui.QDockWidget, objectName)

    def openTerminal(self, thread):
        if self.getTerminal():
            return
        d = TerminalDock.TerminalDock(self.obj, thread)
        FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, d)

    def closeTerminal(self):
            for d in self.getTerminal():
                d.setParent(None)
                d.close()

    def getCharEndOfLine(self):
        return self.obj.Proxy.getCharEndOfLine(self.obj)

    def getTerminalThread(self):
        return TerminalThread(self)

    def errorTerminalMsg(self, e):
        msg = "Error occurred in TerminalWriter process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))    

    def startThreadMsg(self):
        msg = "{} UsbReader thread start on port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Name, self.machine.serial.name))
        
    def stopThreadMsg(self):
        msg = "{} UsbReader thread stop on port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Name, self.machine.serial.name))

    def errorThreadMsg(self, e):
        msg = "Error occurred in UsbReader thread process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))


class OpenState(QtCore.QState):

    def onEntry(self, e):
        obj = self.machine().obj
        eol = obj.Proxy.getCharEndOfLine(obj)
        thread = self.machine().getTerminalThread()
        self.machine().openTerminal(thread)
        QtCore.QThreadPool.globalInstance().tryStart(thread)
        thread.on_command("")


class OffState(QtCore.QFinalState):

    def onEntry(self, e):
        self.machine().closeTerminal()


class TerminalThread(QtCore.QObject, QtCore.QRunnable):

    output = QtCore.Signal(unicode)
    
    def __init__(self, machine):
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.machine = machine
        self.eol = machine.getCharEndOfLine()

    def on_command(self, command):
        try:
            self.machine.machine.sio.write(command + self.eol)
            self.machine.machine.sio.flush()
        except Exception as e:
            self.machine.errorTerminalMsg(e)

    def run(self):
        """ Loop and copy PySerial -> Terminal """
        try:
            self.machine.startThreadMsg()
            while self.machine.isRunning():
                line = self.machine.machine.sio.readline()
                if len(line):
                    self.output.emit(line)
        except Exception as e:
            self.machine.errorThreadMsg(e)
        else:
            self.machine.stopThreadMsg()
        finally:
            self.machine.machine.stop()
