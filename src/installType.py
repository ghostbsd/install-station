#!/usr/local/bin//python
#
# Copyright (c) 2015 GhostBSD
#
# See COPYING for licence terms.
#
# type.py v 0.5 Thursday, Mar 28 2013 19:31:53 Eric Turgeon
#
# type.py create and delete partition slice for GhostBSD system.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os
import os.path

# Folder use pr the installer.
tmp = "/tmp/.gbinstall/"
installer = "/usr/local/lib/gbinstall/"
if not os.path.exists(tmp):
    os.makedirs(tmp)

logo = "/usr/local/lib/gbinstall/logo.png"
disk_file = '%sdisk' % tmp
boot_file = '%sboot' % tmp
signal = '%ssignal' % tmp

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


class Types():

    def fstype(self, radiobutton, val):
        self.ne = val
        pass_file = open(signal, 'w')
        pass_file.writelines(self.ne)
        pass_file.close
        return

    def get_type(self):
        return self.ne

    def get_model(self):
        return self.vbox1

    def __init__(self):
        self.vbox1 = Gtk.VBox(False, 0)
        self.vbox1.show()
        label = Gtk.Label("Installation Type", name="Header")
        label.set_property("height-request", 40)
        self.vbox1.pack_start(label, False, False, 0)
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        self.vbox1.pack_start(hbox, False, False, 10)
        full_ufs = Gtk.RadioButton.new_with_label_from_widget(None, "UFS Full Disk Configuration")
        vbox.pack_start(full_ufs, False, True, 10)
        full_ufs.connect("toggled", self.fstype, "ufs")
        self.ne = 'zfs'
        pass_file = open(signal, 'w')
        pass_file.writelines(self.ne)
        pass_file.close
        full_ufs.show()
        custom_ufs = Gtk.RadioButton.new_with_label_from_widget(full_ufs, "UFS Custom Disk Configuration")
        vbox.pack_start(custom_ufs, False, True, 10)
        custom_ufs.connect("toggled", self.fstype, "custom")
        custom_ufs.show()
        full_zfs = Gtk.RadioButton.new_with_label_from_widget(custom_ufs, "ZFS Full Disk Configuration(Recommended option for BE)")
        vbox.pack_start(full_zfs, False, True, 10)
        full_zfs.connect("toggled", self.fstype, "zfs")
        full_ufs.show()
        hbox.pack_start(vbox, False, False, 50)
        full_zfs.set_active(True)
