#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from subprocess import Popen
from install_station.data import get_text


lyrics = get_text("""Installation is complete. You need to restart the
computer in order to use the new installation.
You can continue to use this live media, although
any changes you make or documents you save will
not be preserved on reboot.""")


class EndWindow:
    @classmethod
    def on_reboot(cls, _widget):
        Popen('shutdown -r now', shell=True)
        Gtk.main_quit()

    @classmethod
    def on_close(cls, _widget):
        Gtk.main_quit()

    def __init__(self):
        window = Gtk.Window()
        window.set_border_width(8)
        window.connect("destroy", Gtk.main_quit)
        window.set_title(get_text("Installation Completed"))
        window.set_icon_from_file("/usr/local/lib/install-station/image/logo.png")
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        label = Gtk.Label(label=lyrics)
        box2.pack_start(label, True, True, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        table = Gtk.Table(1, 2, True)
        restart = Gtk.Button(label=get_text("Restart"))
        restart.connect("clicked", self.on_reboot)
        continue_button = Gtk.Button(label=get_text("Continue"))
        continue_button.connect("clicked", self.on_close)
        table.attach(continue_button, 0, 1, 0, 1)
        table.attach(restart, 1, 2, 0, 1)
        box2.pack_start(table, True, True, 0)
        window.show_all()
