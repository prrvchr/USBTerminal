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
""" UsbPort document object """
from __future__ import unicode_literals

import serial
from serial.tools import list_ports
import FreeCAD


class Port:

    def __init__(self, obj):
        self.Type = "App::UsbPort"
        """ PySerial port object instance property """
        obj.addProperty("App::PropertyPythonObject",
                        "Async",
                        "Base",
                        "PySerial Serial port instance", 2)
        obj.Async = None
        """ Internal property for management of data update """
        obj.addProperty("App::PropertyStringList",
                        "Update",
                        "Base",
                        "List of PySerial property to update", 2, True, True)
        """ PySerial discovered port tools """
        obj.addProperty("App::PropertyEnumeration",
                        "Details",
                        "Discovery tool",
                        "Discovered ports view mode")
        obj.Details = self.getDetails()
        obj.Details = b"Detail"
        obj.addProperty("App::PropertyEnumeration",
                        "Ports",
                        "Discovery tool",
                        "Discovered ports (perhaps need refresh?)")
        obj.Ports = self.getPorts(obj)
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
        obj.Timeout = 0.01
        obj.addProperty("App::PropertyFloat",
                        "WriteTimeout",
                        "PySerial",
                        "WriteTimeout")
        obj.WriteTimeout = -1
        obj.addProperty("App::PropertyBool",
                        "XonXoff", "PySerial",
                        "enable software flow control")
        obj.XonXoff = False
        obj.Proxy = self

    def getDetails(self):
        return [b"Detail", b"Standart", b"VID:PID"]

    def getDetailsIndex(self, obj):
        return self.getDetails().index(obj.Details)

    def getPorts(self, obj):
        return [x[self.getDetailsIndex(obj)] for x in list_ports.comports()]

    def getPortsIndex(self, obj):
        #Get the index of the port:
        try:
            ports = list_ports.grep("^{}$".format(obj.Ports))
            i = self.getPorts(obj).index(ports.next()[self.getDetailsIndex(obj)])
        except (AssertionError, StopIteration, ValueError) as e:
            return -1
        try:
            ports.next()
        except StopIteration as e:
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

    def getSettingsDict(self, obj):
        return {b"port" : b"{}".format(obj.Port),
                b"baudrate" : int(obj.Baudrate),
                b"bytesize" : int(obj.ByteSize),
                b"parity" : b"{}".format(obj.Parity),
                b"stopbits" : float(obj.StopBits),
                b"xonxoff" : obj.XonXoff,
                b"rtscts" : obj.RtsCts,
                b"dsrdtr" : obj.DsrDtr,
                b"timeout" : None if obj.Timeout < 0 else obj.Timeout,
                b"write_timeout" : None if obj.WriteTimeout < 0 else obj.WriteTimeout,
                b"inter_byte_timeout" : None if obj.InterByteTimeout < 0 else obj.InterByteTimeout}

    def execute(self, obj):
        if obj.Update:
            if "Port" in obj.Update:
                self.refreshPorts(obj)
            if "Baudrate" in obj.Update:
                self.refreshBaudrate(obj)
            obj.Update = []

    def onChanged(self, obj, prop):
        if prop == "Async":
            if obj.Async is not None:
                obj.Async.apply_settings(self.getSettingsDict(obj))
        if prop == "Details":
            obj.Update = ["Port"]
            self.refreshPorts(obj)
            obj.Update = []
        if prop == "Ports":
            if not obj.Update and self.getPortsIndex(obj) != -1:
                if self.getDetailsIndex(obj) == 0:
                    obj.Port = obj.Ports
                else:
                    obj.Port = "hwgrep://" + obj.Ports
        if prop == "Baudrate":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.baudrate = obj.Baudrate
        if prop == "ByteSize":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.bytesize = obj.ByteSize
        if prop == "DsrDtr":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.dsrdtr = obj.DsrDtr
        if prop == "InterByteTimeout":
            if obj.Async is not None and obj.Async.is_open:
                timeout = None if obj.InterByteTimeout < 0 else obj.InterByteTimeout
                obj.Async.inter_byte_timeout = timeout
        if prop == "Parity":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.parity = obj.Parity
        if prop == "Port":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.port = obj.Port
        if prop == "RtsCts":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.rtscts = obj.RtsCts
        if prop == "StopBits":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.stopbits = float(obj.StopBits)
        if prop == "Timeout":
            if obj.Async is not None and obj.Async.is_open:
                timeout = None if obj.Timeout < 0 else obj.Timeout
                obj.Async.timeout = timeout
        if prop == "WriteTimeout":
            if obj.Async is not None and obj.Async.is_open:
                timeout = None if obj.WriteTimeout < 0 else obj.WriteTimeout
                obj.Async.write_timeout = timeout
        if prop == "XonXoff":
            if obj.Async is not None and obj.Async.is_open:
                obj.Async.xonxoff = obj.XonXoff


FreeCAD.Console.PrintLog("Loading UsbPort... done\n")
