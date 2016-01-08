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

import FreeCAD, serial
from serial.tools import list_ports
from App import PySerialState


class PySerial:

    def __init__(self, obj):
        self.Serial = serial.serial_for_url(None, do_not_open=True)
        self.Type = "App::PySerial"
        """ Internal property for management of data update """
        self.Update = ["Init"]
        """ PySerial Base driving property """
        obj.addProperty("App::PropertyEnumeration",
                        "State",
                        "Base",
                        "State of PySerial Machine [Open, Close, Error]", 1)
        obj.State = self.getState()
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
        obj.Parity = serial.PARITY_NAMES.values()
        obj.Parity = serial.PARITY_NAMES[serial.PARITY_NONE]
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
        self.Serial = serial.serial_for_url(None, do_not_open=True)
        self.Type = "App::PySerial"
        self.Update = ["Init"]
        return None

    def getState(self):
        return [b"Close", b"Init", b"Open", b"Start", b"Run", b"Error"]

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
        if self.Update:
            if "Port" in self.Update:
                self.refreshPorts(obj)
            if "Baudrate" in self.Update:
                self.refreshBaudrate(obj)
            self.Update = []

    def onChanged(self, obj, prop):
        if prop == "Label":
            if "Init" in self.Update:
                p, s = self.getSettings(obj)
                self.Serial = serial.serial_for_url(p, do_not_open=True, **s)
                self.Update = []
        if prop == "Details":
            self.Update = ["Port"]
            self.refreshPorts(obj)
            self.Update = []
        if prop == "Ports":
            if not self.Update and self.getPortsIndex(obj) != -1:
                if self.getDetailsIndex(obj) == 0:
                    obj.Port = obj.Ports
                else:
                    obj.Port = b"hwgrep://" + obj.Ports
        msg = "Error occurred in {} {{}}'s property value assignment: {{}}\n"
        msg = msg.format(obj.Label)
        if prop == "Baudrate":
            try:
                self.Serial.baudrate = self.getBaudrate(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "ByteSize":
            try:
                self.Serial.bytesize = self.getByteSize(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "DsrDtr":
            try:
                self.Serial.dsrdtr = self.getDsrDtr(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "InterByteTimeout":
            try:
                self.Serial.inter_byte_timeout = self.getInterByteTimeout(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "Parity":
            try:
                self.Serial.parity = self.getParity(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))
        if prop == "Port":
            try:
                self.Serial.port = self.getPort(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))
        if prop == "RtsCts":
            try:
                self.Serial.rtscts = self.getRtsCts(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "StopBits":
            try:
                self.Serial.stopbits = self.getStopBits(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "Timeout":
            try:
                self.Serial.timeout = self.getTimeout(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "WriteTimeout":
            try:
                self.Serial.write_timeout = self.getWriteTimeout(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))            
        if prop == "XonXoff":
            try:
                self.Serial.xonxoff = self.getXonXoff(obj)
            except (serial.SerialException, ValueError) as e:
                FreeCAD.Console.PrintError(msg.format(prop, e))

    def hasParent(self, obj):
        return len(obj.InList) > 0

    def getParent(self, obj):
        return obj.InList[0]

    def getMachineState(self, obj):
        if self.hasParent(obj):
            o = self.getParent(obj)
            index = o.Serials.index(obj)
            return o.Proxy.Machine.Serials[o.Serials.index(obj)]
        return None

    def isDataChannel(self, obj):
        if self.hasParent(obj):
            o = self.getParent(obj)
            return o.Proxy.getDataChannel(o) == obj
        return False

    def isCtrlChannel(self, obj):
        if self.hasParent(obj):
            o = self.getParent(obj)
            return o.Proxy.getCtrlChannel(o) == obj
        return False

    def getCharEndOfLine(self, obj):
        if self.hasParent(obj):
            o = self.getParent(obj)
            return o.Proxy.getCharEndOfLine(o)
        return "\n"

    def getSettings(self, obj):
        return (self.getPort(obj),
                {b"baudrate" : self.getBaudrate(obj),
                 b"bytesize" : self.getByteSize(obj),
                 b"parity" : self.getParity(obj),
                 b"stopbits" : self.getStopBits(obj),
                 b"xonxoff" : self.getXonXoff(obj),
                 b"rtscts" : self.getRtsCts(obj),
                 b"dsrdtr" : self.getDsrDtr(obj),
                 b"timeout" : self.getTimeout(obj),
                 b"write_timeout" : self.getWriteTimeout(obj),
                 b"inter_byte_timeout" : self.getInterByteTimeout(obj)})

    def isUrl(self, obj):
        return "://" in obj.Port

    def getPort(self, obj):
        return b"{}".format(obj.Port)
    def getBaudrate(self, obj):
        return int(obj.Baudrate)
    def getByteSize(self, obj):
        return int(obj.ByteSize)
    def getParity(self, obj):
        parity = serial.PARITY_NAMES
        return b"{}".format(parity.keys()[parity.values().index(obj.Parity)])
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


FreeCAD.Console.PrintLog("Loading PySerial... done\n")
