#!/usr/bin/env python
#
#####################################################################
# Copyright (c) 2009-2012, GhostBSD. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistribution's of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistribution's in binary form must reproduce the above
#    copyright notice,this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#
# 3. Neither then name of GhostBSD Project nor the names of its
#    contributors maybe used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES(INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#####################################################################
# language.py show the language for the installer.


from gi.repository import Gtk, Gdk
import os
import os.path
import sys
from create_cfg import gbsd_cfg

# Folder use for the installer.
tmp = "/tmp/.gbinstall/"
pcinstallcfg = f'{tmp}pcinstall.cfg'
installer = "/usr/local/lib/gbinstall/"
logo = f"{installer}logo.png"
if not os.path.exists(tmp):
    os.makedirs(tmp)

sys.path.append(installer)
cssProvider = Gtk.CssProvider()
# if os.path.exists(rcconfgbsd):
#     print(True)
cssProvider.load_from_path('/usr/local/lib/gbinstall/ghostbsd-style.css')
# elif os.path.exists(rcconfdbsd):
#     cssProvider.load_from_path('/usr/local/lib/gbi/desktopbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(screen, cssProvider,
                                     Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class Summary:

    def __init__(self, button3):
        gbsd_cfg()
        cfg_file = open(pcinstallcfg, 'r')
        cfg_text = cfg_file.read()
        cfg_file.close()
        button3.set_sensitive(True)
        # Add a Default vertical box
        self.vbox1 = Gtk.VBox(False, 0)
        self.vbox1.show()
        # Add a second vertical box
        label = Gtk.Label("Installation Summary", name="Header")
        label.set_property("height-request", 40)
        self.vbox1.pack_start(label, False, False, 0)
        grid = Gtk.Grid()
        self.vbox1.pack_start(grid, True, True, 0)
        grid.set_row_spacing(10)
        grid.set_column_spacing(3)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        # Adding a Scrolling Window
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        scrolledwindow.show()
        grid.attach(scrolledwindow, 0, 1, 3, 1)

        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text(cfg_text)
        scrolledwindow.add(self.textview)

        # self.wellcometext = Gtk.Label(welltext)
        # self.wellcometext.set_use_markup(True)
        # table = Gtk.Table()
        # table.attach(self.wellcome, 0, 1, 1, 2)
        # wall = Gtk.Label()
        # table.attach(wall, 0, 1, 2, 3)
        # table.attach(self.wellcometext, 0, 1, 3, 4)
        # vhbox.pack_start(table, False, False, 5)
        # image = Gtk.Image()
        # image.set_from_file(logo)
        # image.show()
        # grid.attach(self.wellcome, 1, 1, 3, 1)
        # vhbox.pack_start(image, True, True, 5)
        # grid.attach(vhbox, 2, 2, 2, 9)
        grid.show()
        return

    def get_model(self):
        return self.vbox1
