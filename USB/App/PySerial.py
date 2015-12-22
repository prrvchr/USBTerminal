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
""" PySerial document object """
from __future__ import unicode_literals

import serial
from serial.tools import list_ports
from FreeCAD import Console
from App import PySerialMachine


class PySerial:

    def __init__(self, obj):
        self.Type = "App::PySerial"
        self.Machine = PySerialMachine.PySerialMachine()
        """ Internal property for management of data update """
        self.Update = []
        """ PySerial Base driving property """
        obj.addProperty("App::PropertyBool",
                        "Open",
                        "Base",
                        "Open/close PySerial port", 2)
        obj.Open = False
        #obj.setEditorMode("Open", 1) made in onChanged() Proxy property
        """ PySerial port property """
        obj.addProperty("App::PropertyEnumeration",
                        "Baudrate",
                        "PySerial",
                        "Set baud rate (default 115200)")
        obj.Baudrate = map(str, serial.Serial().BAUDRATES)
        obj.Baudrate = b"115200"
        obj.addProperty("App::PropertyEnumeration",
                        "ByteSize",
                        "PySerial",
                        "ByteSize")
        obj.ByteSize = map(str, serial.Serial().BYTESIZES)
        obj.ByteSize = b"8"
        obj.addProperty("App::PropertyBool",
                        "DsrDtr",
                        "PySerial",
                        "set initial DTR line state")
        obj.DsrDtr = False
        obj.addProperty("App::PropertyFloat",
                        "InterByteTimeout",
                        "PySerial",
                        "InterByteTimeout")
        obj.InterByteTimeout = -1
        obj.addProperty("App::PropertyEnumeration",
                        "Parity",
                        "PySerial",
                        "set parity (None, Even, Odd, Space, Mark) default N")
        obj.Parity = map(str, serial.Serial().PARITIES)
        obj.Parity = b"N"
        obj.addProperty("App::PropertyString",
                        "Port",
                        "PySerial",
                        "Port, a number or a device name")
        obj.Port = b"loop://"
        obj.addProperty("App::PropertyBool",
                        "RtsCts",
                        "PySerial",
                        "enable RTS/CTS flow control")
        obj.RtsCts = False
        obj.addProperty("App::PropertyEnumeration",
                        "StopBits",
                        "PySerial",
                        "StopBits")
        obj.StopBits = map(str, serial.Serial().STOPBITS)
        obj.StopBits = b"1"
        obj.addProperty("App::PropertyFloat",
                        "Timeout",
                        "PySerial",
                        "Set a read timeout (negative value wait forever)")
        obj.Timeout = 0.05
        obj.addProperty("App::PropertyFloat",
                        "WriteTimeout",
                        "PySerial",
                        "WriteTimeout")
        obj.WriteTimeout = -1
        obj.addProperty("App::PropertyBool",
                        "XonXoff", "PySerial",
                        "enable software flow control")
        obj.XonXoff = False
        """ PySerial list_ports tools """
        obj.addProperty("App::PropertyEnumeration",
                        "Details",
                        "PySerial List_ports Tool",
                        "Discovered ports view mode")
        obj.Details = self.getDetails()
        obj.Details = b"Detail"
        obj.addProperty("App::PropertyEnumeration",
                        "Ports",
                        "PySerial List_ports Tool",
                        "Discovered ports (perhaps need refresh?)")
        obj.Ports = self.getPorts(obj)
        obj.Proxy = self

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        self.Type = "App::PySerial"
        self.Machine = PySerialMachine.PySerialMachine()
        self.Update = []
        return None

    def getDetails(self):
        return [b"Detail", b"Standart", b"VID:PID"]

    def getDetailsIndex(self, obj):
        return self.getDetails().index(obj.Details)

    def getPorts(self, obj):
        return [x[self.getDetailsIndex(obj)] for x in list_ports.comports()]

    def getPortsIndex(self, obj):
        # Get unique index of the port
        try:
            p = list_ports.grep("^{}$".format(obj.Ports))
            i = self.getPorts(obj).index(p.next()[self.getDetailsIndex(obj)])
        except (AssertionError, StopIteration, ValueError):
            return -1
        try:
            p.next()
        except StopIteration:
            return i
        return -1

    def refreshPorts(self, obj):
        index = self.getPortsIndex(obj)
        obj.Ports = self.getPorts(obj)
        if index != -1:
            obj.Ports = index

    def refreshBaudrate(self, obj):
        baudrate = obj.Baudrate
        obj.Baudrate = map(str, serial.Serial().BAUDRATES)
        obj.Baudrate = baudrate

    def execute(self, obj):
        if obj.Proxy.Update:
            if "Port" in obj.Proxy.Update:
                self.refreshPorts(obj)
            if "Baudrate" in obj.Proxy.Update:
                self.refreshBaudrate(obj)
            obj.Proxy.Update = []

    def onChanged(self, obj, prop):
        if prop == "Proxy":
            obj.setEditorMode("Open", 1)
        if prop == "Details":
            obj.Proxy.Update = ["Port"]
            self.refreshPorts(obj)
            obj.Proxy.Update = []
        if prop == "Ports":
            if not obj.Proxy.Update and self.getPortsIndex(obj) != -1:
                if self.getDetailsIndex(obj) == 0:
                    obj.Port = obj.Ports
                else:
                    obj.Port = b"hwgrep://" + obj.Ports
        if prop == "Baudrate":
            self.Machine.serial.baudrate = self.getBaudrate(obj)
        if prop == "ByteSize":
            self.Machine.serial.bytesize = self.getByteSize(obj)
        if prop == "DsrDtr":
            self.Machine.serial.dsrdtr = self.getDsrDtr(obj)
        if prop == "InterByteTimeout":
            self.Machine.serial.inter_byte_timeout = self.getInterByteTimeout(obj)
        if prop == "Parity":
            self.Machine.serial.parity = self.getParity(obj)
        if prop == "Port":
            self.Machine.serial.port = self.getPort(obj)
        if prop == "RtsCts":
            self.Machine.serial.rtscts = self.getRtsCts(obj)
        if prop == "StopBits":
            self.Machine.serial.stopbits = self.getStopBits(obj)
        if prop == "Timeout":
            self.Machine.serial.timeout = self.getTimeout(obj)
        if prop == "WriteTimeout":
            self.Machine.serial.write_timeout = self.getWriteTimeout(obj)
        if prop == "XonXoff":
            self.Machine.serial.xonxoff = self.getXonXoff(obj)
            
    def isInitPort(self, obj):
        return obj.InList and obj.InList[0].Serials[0] == obj

    def getPySerialPool(self, obj):
        pool = None
        if obj.InList:
            pool = obj.InList[0]
        return pool

    def getCharEndOfLine(sef, obj):
        eol = ""
        if obj.InList:
            o = obj.InList[0]
            eol = o.Proxy.getCharEndOfLine(o)
        return eol

    def closeTerminal(self, obj):
        if obj.InList and obj.InList[0].Serials[0] == obj:
            o = obj.InList[0]
            o.Proxy.closeTerminal(o)

    def getSettings(self, obj):
        return {b"baudrate" : self.getBaudrate(obj),
                b"bytesize" : self.getByteSize(obj),
                b"parity" : self.getParity(obj),
                b"stopbits" : self.getStopBits(obj),
                b"xonxoff" : self.getXonXoff(obj),
                b"rtscts" : self.getRtsCts(obj),
                b"dsrdtr" : self.getDsrDtr(obj),
                b"timeout" : self.getTimeout(obj),
                b"write_timeout" : self.getWriteTimeout(obj),
                b"inter_byte_timeout" : self.getInterByteTimeout(obj)}

    def getPort(self, obj):
        return b"{}".format(obj.Port)
    def getBaudrate(self, obj):
        return int(obj.Baudrate)
    def getByteSize(self, obj):
        return int(obj.ByteSize)
    def getParity(self, obj):
        return b"{}".format(obj.Parity)
    def getStopBits(self, obj):
        return float(obj.StopBits)
    def getXonXoff(self, obj):
        return obj.XonXoff
    def getRtsCts(self, obj):
        return obj.RtsCts
    def getDsrDtr(self, obj):
        return obj.DsrDtr
    def getTimeout(self, obj):
        return None if obj.Timeout < 0 else obj.Timeout
    def getWriteTimeout(self, obj):
        return None if obj.WriteTimeout < 0 else obj.WriteTimeout
    def getInterByteTimeout(self, obj):
        return None if obj.InterByteTimeout < 0 else obj.InterByteTimeout


Console.PrintLog("Loading PySerial... done\n")
