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
""" PySerial StateMachine document object """
from __future__ import unicode_literals

import FreeCAD, FreeCADGui, serial, io, json, time
from PySide import QtCore, QtGui
from App import UsbPoolPlugin
from Gui import PySerialModel, TerminalDock


class SerialState(QtCore.QState):
    
    close = QtCore.Signal()
    error = QtCore.Signal()
    read = QtCore.Signal(unicode)
    write = QtCore.Signal(unicode)

    def __init__(self):
        QtCore.QState.__init__(self)
        self.setObjectName("Serial")
        self.obj = None
        self.init = False
        self.sio = None
        self.serial = serial.serial_for_url(None, do_not_open=True)
        self.model = PySerialModel.PySerialModel(self)
        
        Open = OpenState(self)
        Open.setObjectName("Open")
        Close = CloseState(self)
        Close.setObjectName("Close")
        Error = ErrorState(self)
        Error.setObjectName("Error")
        Open.addTransition(SerialWriter(self.write[unicode]))
        Open.addTransition(self, b"close()", Close)
        Open.addTransition(self, b"error()", Error)
        self.setInitialState(Open)

    def setState(self, state):
        self.obj.State = b"{}".format(state)

    def openState(self):
        if not self.serial.is_open:
            port, settings = self.getSettings()
            try:
                self.serial = serial.serial_for_url(port, **settings)
            except (serial.SerialException, ValueError) as e:
                self.errorSerial(e)
                self.error.emit()
                return
            else:
                self.openSerial()
        QtCore.QThreadPool.globalInstance().start(SerialReader(self))
        if self.init:
            self.openTerminal()
            self.write.emit("$")

    def closeState(self):
        if self.serial.is_open:
            self.closeSerial()
        if self.init:
            self.closeTerminal()        

    def openSerial(self):
        self.setSio()
        if self.init: self.initPlugin()
        self.model.setModel()
        self.openSerialMsg()

    def closeSerial(self):
        self.serial.close()
        self.sio = None
        self.model.setModel()
        self.closeSerialMsg()
        if self.init: self.resetPlugin()

    def errorSerial(self, e):
        self.model.setModel()
        self.errorSerialMsg(e)

    def isUrl(self):
        return self.obj.Proxy.isUrl(self.obj)

    def getSettings(self):
        port = self.obj.Proxy.getPort(self.obj)
        settings = self.obj.Proxy.getSettings(self.obj)
        return port, settings

    def getCharEndOfLine(self):
        return self.obj.Proxy.getCharEndOfLine(self.obj)

    def setSio(self):
        eol = self.getCharEndOfLine()
        s = io.BufferedRWPair(self.serial, self.serial)
        self.sio = io.TextIOWrapper(s, newline=eol)

    def getSignature(self):
        # Need this hack for getting signature
        if not self.isUrl():
            self.serial.close()
            self.serial.open()
        # Now it's shure to have signature
        return self.sio.readline()

    def getDevice(self):
        device, extra = 0, {}
        try:
            s = json.loads(self.getSignature())
        except ValueError:
            pass
        else:
            if s.has_key("r"):
                r = s["r"]
                if (r.has_key("fv") and r["fv"] >= 0.98 and
                    r.has_key("hp") and r["hp"] >= 3 and
                    r.has_key("hv") and r["hv"] >= 0 and
                    r.has_key("fb") and r["fb"] >= 83.09 and
                    r.has_key("msg") and r.has_key("id")):
                    device, extra = 1, {"msg": r["msg"], "id": r["id"]}
        return device, extra

    def initPlugin(self):
        device, extra = self.getDevice()
        o = self.obj.Proxy.getParent(self.obj)
        if device != o.Proxy.getIndexDevice(o):
            self.deviceChangeMsg()
        UsbPoolPlugin.initPlugin(o, device, extra)
        o.Device = device

    def getTerminal(self):
        name = "{}-{}".format(self.machine().obj.Document.Name, self.machine().obj.Name)
        return FreeCADGui.getMainWindow().findChildren(QtGui.QDockWidget, name)

    def openTerminal(self):
        if self.getTerminal():
            return
        dock = TerminalDock.TerminalDock(self)
        FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def closeTerminal(self):
        for d in self.getTerminal():
            d.setParent(None)
            d.close()
            
    def resetPlugin(self):
        UsbPoolPlugin.resetPlugin(self.obj.Proxy.getParent(self.obj))

    def openSerialMsg(self):
        msg = "{} opening port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Label, self.serial.name))

    def closeSerialMsg(self):
        msg = "{} closing port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Label, self.serial.name))

    def errorSerialMsg(self, e):
        msg = b"Error occurred opening port {}: {}\n"
        FreeCAD.Console.PrintError(msg.format(self.serial.name, e))
        
    def deviceChangeMsg(self):
        msg = "Configuration differente!!!\n"
        FreeCAD.Console.PrintError(msg)

    def readerErrorMsg(self, e):
        msg = "Error occurred in SerialReader process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))

    def writerErrorMsg(self, e):
        msg = "Error occurred in SerialWriter process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))

    def startThreadMsg(self):
        msg = "{} UsbReader thread start on port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Name, self.serial.name))
        
    def stopThreadMsg(self):
        msg = "{} UsbReader thread stop on port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Name, self.serial.name))

    def errorThreadMsg(self, e):
        msg = "Error occurred in UsbReader thread process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))


class OpenState(QtCore.QState):

    def onEntry(self, e):
        self.parentState().setState(self.objectName())
        self.parentState().openState()


class CloseState(QtCore.QFinalState):
    
    def onEntry(self, e):
        self.parentState().setState(self.objectName())
        self.parentState().closeState()


class ErrorState(QtCore.QFinalState):
    
    def onEntry(self, e):
        self.parentState().setState(self.objectName())
        self.machine().run = False


class SerialWriter(QtCore.QSignalTransition):

    def onTransition(self, e):
        try:
            state = self.sourceState().parentState()
            state.sio.write(e.arguments()[0] + self.machine().getCharEndOfLine())
            state.sio.flush()
        except Exception as e:
            state.writerErrorMsg(e)


class SerialReader(QtCore.QRunnable):

    def __init__(self, state):
        QtCore.QRunnable.__init__(self)
        self.state = state
        state.machine().run = True

    def run(self):
        """ Loop and read PySerial """
        self.state.startThreadMsg()
        try:
            while self.state.machine().run:
                line = self.state.sio.readline()
                if len(line):
                    self.state.read.emit(line)
        except Exception as e:
            self.state.errorThreadMsg(e)
        else:
            self.state.stopThreadMsg()
        self.state.close.emit()
