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
""" Gui workbench initialization """
from __future__ import unicode_literals


class UsbWorkbench(Workbench):
    "USB workbench object"
    Icon = b"""
        /* XPM */
        static const char * const usbwb_xpm[]={
        "16 16 3 1",
        ".      c None",
        "#      c #FFFFFF",
        "$      c #000000",
        "................",
        ".......$$#......",
        "......$$$$#.#...",
        "....#..$$#.$$#..",
        "...$$#.$$#$$$$#.",
        "..$$$$#$$#.$$#..",
        "...$$#.$$#.$$#..",
        "...$$#.$$#.$$#..",
        "...$$#.$$#$$#...",
        "...$$#.$$$##....",
        "....$$#$$#......",
        "......$$$#......",
        ".......$$##.....",
        ".....$$$$$$#....",
        ".....$$$$$$#....",
        "................"};
        """
    MenuText = "USB"
    ToolTip = "Python USB workbench"

    def Initialize(self):
        from Gui import initResources, UsbPortPanel, UsbPoolPanel
        from App import DocumentObserver, UsbPool, UsbCommand
        initResources.initIcons()
        commands = [b"Usb_Pool", b"Usb_Refresh", b"Usb_Open", b"Usb_Start", b"Usb_Pause"]
        # Add commands to menu and toolbar
        self.appendToolbar("Commands for Usb", commands)
        self.appendMenu([b"USB"], commands)
        self.observer = DocumentObserver.DocumentObserver()
        App.addDocumentObserver(self.observer)
        Log('Loading USB workbench... done\n')

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Activated(self):
        from Gui import initResources
        initResources.initTaskWatcher()
        Log("USB workbench activated\n")

    def Deactivated(self):
        Gui.Control.clearTaskWatcher()
        Log("USB workbench deactivated\n")

Gui.addWorkbench(UsbWorkbench())
