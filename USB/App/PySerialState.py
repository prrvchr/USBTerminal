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

import FreeCAD, serial, io, json
from PySide import QtCore


class SerialState(QtCore.QState):

    serialOpen = QtCore.Signal()
    serialClose = QtCore.Signal()
    serialError = QtCore.Signal()
    serialRead = QtCore.Signal(unicode)
    serialWrite = QtCore.Signal(unicode)

    def __init__(self, parent=None):
        QtCore.QState.__init__(self, parent)
        self.setObjectName("Serial")
        self.obj = None
        self.sio = None

        Init = InitState(self)
        Init.setObjectName(b"Init")
        Open = OpenState(self)
        Open.setObjectName(b"Open")
        Close = CloseState(self)
        Close.setObjectName(b"Close")
        Error = ErrorState(self)
        Error.setObjectName(b"Error")

        Init.addTransition(self, b"serialOpen()", Open)
        Init.addTransition(self, b"serialClose()", Close)
        Init.addTransition(self, b"serialError()", Error)
        Open.addTransition(SerialWriter(self.serialWrite[unicode]))
        Open.addTransition(self, b"serialClose()", Close)        
        Open.addTransition(self, b"serialError()", Error)
        self.setInitialState(Init)

    def isDataChannel(self):
        return self.obj.Proxy.isDataChannel(self.obj)

    def isUrl(self):
        return self.obj.Proxy.isUrl(self.obj)

    def isCtrlChannel(self):
        return self.obj.Proxy.isCtrlChannel(self.obj)

    def getParent(self):
        return self.obj.Proxy.getParent(self.obj)

    def trySerialOpen(self):
        if not self.obj.Proxy.Serial.is_open:
            port, settings = self.obj.Proxy.getSettings(self.obj)
            try:
                self.obj.Proxy.Serial = serial.serial_for_url(port, **settings)
            except (serial.SerialException, ValueError) as e:
                self.serialErrorMsg(e)
                return False
            else:
                self.doSerialOpen()
        return True

    def doSerialOpen(self):
        eol = self.machine().getCharEndOfLine()
        s = io.BufferedRWPair(self.obj.Proxy.Serial, self.obj.Proxy.Serial)
        self.sio = io.TextIOWrapper(s, newline=eol)
        self.serialOpenMsg()

    def isOpen(self):
        return self.obj.Proxy.Serial.is_open

    def doSerialClose(self):
        if self.isOpen():
            self.serialCloseMsg()
            self.obj.Proxy.Serial.close()
        self.sio = None

    def doThreadClose(self):
        self.stopThreadMsg()
        self.doSerialClose()
        self.resetExtra()

    def getSignature(self):
        # Need this hack for getting signature
        if not self.isUrl():
            self.obj.Proxy.Serial.close()
            self.obj.Proxy.Serial.open()
        # Now it's shure to have signature
        return self.sio.readline()

    def getPlugin(self):
        plugin, extra = b"UsbPool", {}
        try:
            s = json.loads(self.getSignature())
        except ValueError:
            pass
            #device = __import__("App").UsbPool
        else:
            if s.has_key("r"):
                r = s["r"]
                if (r.has_key("fv") and r["fv"] >= 0.98 and
                    r.has_key("hp") and r["hp"] >= 3 and
                    r.has_key("hv") and r["hv"] >= 0 and
                    r.has_key("fb") and r["fb"] >= 83.09 and
                    r.has_key("msg") and r.has_key("id")):
                    plugin = b"TinyG2"
                    #device = __import__("App").TinyG2
                    extra = {"msg": r["msg"], "id": r["id"]}
        return plugin, extra

    def newPlugin(self):
        if self.isCtrlChannel():
            plugin, extra = self.getPlugin()
            o = self.getParent()
            if plugin != o.Proxy.Plugin:
                self.machine().plugin = plugin
                self.newDeviceMsg(plugin)
                return True
            o.Proxy.setExtra(o, extra)
        return False

    def resetExtra(self):
        if self.isCtrlChannel():
            o = self.getParent()
            o.Proxy.resetExtra(o)

    def serialOpenMsg(self):
        msg = "{} opening port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Label, self.obj.Proxy.Serial.name))

    def serialCloseMsg(self):
        msg = "{} closing port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Label, self.obj.Proxy.Serial.name))

    def serialErrorMsg(self, e):
        msg = b"Error occurred opening port {}: {}\n"
        FreeCAD.Console.PrintError(msg.format(self.obj.Proxy.Serial.name, e))
        
    def newDeviceMsg(self, device):
        msg = "{} StateMachine has detected a new {}: restart required!!!\n"
        FreeCAD.Console.PrintWarning(msg.format(self.machine().obj.Label, device))

    def readerErrorMsg(self, e):
        msg = "Error occurred in SerialReader process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))

    def writerErrorMsg(self, e):
        msg = "Error occurred in SerialWriter process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))

    def startThreadMsg(self):
        msg = "{} UsbReader thread start on port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Name, self.obj.Proxy.Serial.name))
        
    def stopThreadMsg(self):
        msg = "{} UsbReader thread stop on port {}... done\n"
        FreeCAD.Console.PrintLog(msg.format(self.obj.Name, self.obj.Proxy.Serial.name))

    def errorThreadMsg(self, e):
        msg = "Error occurred in UsbReader thread process: {}\n"
        FreeCAD.Console.PrintError(msg.format(e))


class InitState(QtCore.QState):

    def onEntry(self, e):
        self.parentState().obj.State = b"{}".format(self.objectName())
        if self.parentState().trySerialOpen():
            if self.parentState().newPlugin():
                self.parentState().doSerialClose()
                self.machine().startThread(RestartMachine(self.machine()))
                self.machine().run = False                
                self.parentState().serialClose.emit()
            else:
                self.parentState().serialOpen.emit()
        else:
            self.parentState().serialError.emit()


class OpenState(QtCore.QState):

    def onEntry(self, e):
        self.parentState().obj.State = b"{}".format(self.objectName())        
        self.machine().startThread(SerialReader(self.parentState()))


class CloseState(QtCore.QFinalState):
    
    def onEntry(self, e):
        # Need to try: on close document serialClose is emited... 
        # and obj already deleted
        try:
            self.parentState().obj.State = b"{}".format(self.objectName())
            self.parentState().obj.purgeTouched()
        except ReferenceError:
            pass

class ErrorState(QtCore.QFinalState):
    
    def onEntry(self, e):
        self.parentState().obj.State = b"{}".format(self.objectName())
        self.machine().run = False


class SerialWriter(QtCore.QSignalTransition):

    def onTransition(self, e):
        try:
            state = self.sourceState().parentState()
            state.sio.write(e.arguments()[0] + self.machine().getCharEndOfLine())
            state.sio.flush()
        except Exception as e:
            state.writerErrorMsg(e)
            state.serialError.emit()


class SerialReader(QtCore.QRunnable):

    def __init__(self, state):
        QtCore.QRunnable.__init__(self)
        self.state = state

    def run(self):
        """ Loop and read PySerial """
        try:
            isCtrl = self.state.isCtrlChannel()
            if isCtrl:
                self.state.machine().ctrlStart.emit()
            self.state.startThreadMsg()
            while self.state.machine().run:
                line = self.state.sio.readline()
                if len(line):
                    self.state.serialRead.emit(line)
                    if isCtrl:
                        self.state.machine().serialRead.emit(line)
            self.state.doThreadClose()
            if isCtrl:
                self.state.machine().ctrlStop.emit()
            self.state.serialClose.emit()
        except Exception as e:
            self.state.errorThreadMsg(e)
            self.state.serialError.emit()


class RestartMachine(QtCore.QRunnable):

    def __init__(self, machine):
        QtCore.QRunnable.__init__(self)
        self.machine = machine

    def run(self):
        """ Wait for restart StateMachine """
        try:
            while self.machine.isRunning():
                pass
            self.machine.restart.emit(self.machine.obj)
        except Exception as e:
            self.machine.machineErrorMsg(e)