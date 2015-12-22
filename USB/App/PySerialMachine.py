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

import serial, io, json
from FreeCAD import Console
from PySide import QtCore
from App import Plugin
from Gui import PySerialModel


class PySerialMachine(QtCore.QStateMachine):

    initError = QtCore.Signal()
    serialReady = QtCore.Signal(object)
    pluginReady = QtCore.Signal(object)

    def __init__(self):
        QtCore.QStateMachine.__init__(self)
        self.obj = None
        self.sio = None
        self.init = False
        self.signature = ""
        self.serial = serial.serial_for_url(None, do_not_open=True)
        self.model = PySerialModel.PySerialModel(self)
        On = QtCore.QState(self)
        On.setObjectName("On")
        Off = OffState(self)
        Off.setObjectName("Off")
        Error = QtCore.QState(self)
        Error.setObjectName("Error")
        Init = InitState(On)
        Init.setObjectName("Init")
        Open = OpenState(On)
        Open.setObjectName("Open")

        On.setInitialState(Init)
        On.setErrorState(Error)
        Init.addTransition(Init, b"exited()", Open)
        Init.addTransition(self, b"initError()", Error)
        Open.addTransition(self, b"stopped()", Off)
        Error.addTransition(Off)
        self.setInitialState(On)

    def start(self, obj, init=False):
        self.obj = obj
        self.init = init
        QtCore.QStateMachine.start(self)

    def stop(self):
        self.stopped.emit()

    def initDevice(self, device, extra):
        o = self.obj.Proxy.getPySerialPool(self.obj)
        if device != o.Proxy.getIndexDevice(o):
            msg = "Configuration differente!!!\n"
            Console.PrintError(msg)
        Plugin.initPlugin(o, device, extra)
        Plugin.initMachine(o, device)
        o.Device = device

    def resetDevice(self):
        if self.init:
            Plugin.resetPlugin(self.obj.Proxy.getPySerialPool(self.obj))

    def getSettings(self):
        p = self.obj.Proxy.getPort(self.obj)
        s = self.obj.Proxy.getSettings(self.obj)
        return p, s

    def getCharEndOfLine(self):
        return self.obj.Proxy.getCharEndOfLine(self.obj)

    def setSignature(self):
        eol = self.getCharEndOfLine()
        # Need this hack for getting signature
        #self.serial.close()
        #self.serial.open()
        # Now it's shure to have signature
        s = io.BufferedRWPair(self.serial, self.serial)
        self.sio = io.TextIOWrapper(s, newline=eol)
        self.signature = self.sio.readline()

    def openPortMsg(self):
        msg = "{} opening port {}... done\n"
        Console.PrintLog(msg.format(self.obj.Label, self.serial.name))

    def closePortMsg(self):
        msg = "{} closing port {}... done\n"
        Console.PrintLog(msg.format(self.obj.Label, self.serial.name))

    def onInitError(self, e):
        msg = b"Error occurred opening port {}: {}\n"
        Console.PrintError(msg.format(self.serial.name, e))
        self.initError.emit()


class InitState(QtCore.QState):

    def onEntry(self, e):
        if self.machine().serial.is_open:
            self.exited.emit()
            return
        p, s = self.machine().getSettings()
        try:
            self.machine().serial = serial.serial_for_url(p, do_not_open=True, **s)
            self.machine().serial.open()
        except (serial.SerialException, ValueError) as e:
            self.machine().model.setModel()
            self.machine().onInitError(e)
            return
        self.machine().setSignature()
        self.machine().obj.Open = True
        self.machine().model.setModel()
        self.machine().openPortMsg()
        self.exited.emit()


class OpenState(QtCore.QState):

    def onEntry(self, e):
        if self.machine().init:
            self.initDevice()
            self.machine().pluginReady.emit(self.machine())
        else:
            self.machine().serialReady.emit(self.machine())
        
    def initDevice(self):
        device, extra = 0, {}
        try:
            s = json.loads(self.machine().signature)
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
        self.machine().initDevice(device, extra)


class OffState(QtCore.QFinalState):

    def onEntry(self, e):
        doClose = self.machine().serial.is_open
        if doClose:
            self.machine().serial.close()
            self.machine().sio = None
            self.machine().model.setModel()
        try:
            self.machine().obj.Open = False
        except ReferenceError:
            return
        if doClose:
            self.machine().closePortMsg()
            self.machine().resetDevice()
