import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import threading
from subprocess import Popen, PIPE, STDOUT
from time import sleep
from install_station.partition import delete_partition, destroy_partition, add_partition
from install_station.create_cfg import Configuration
from install_station.window import Window
from install_station.data import InstallationData, installation_config, pc_sysinstall
import sys
import gettext

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


def update_progress(progressbar, text):
    """
    This method
    """
    new_val = progressbar.get_fraction() + 0.000003
    progressbar.set_fraction(new_val)
    progressbar.set_text(text[0:80])


def read_output(command, progressbar):
    GLib.idle_add(update_progress, progressbar, _("Creating ghostbsd_installation.cfg"))
    Configuration.create_cfg()
    sleep(1)
    if InstallationData.delete:
        GLib.idle_add(update_progress, progressbar, _("Deleting partition"))
        delete_partition()
        sleep(1)
    # destroy disk partition and create scheme
    if InstallationData.destroy:
        GLib.idle_add(update_progress, progressbar, _("Creating disk partition"))
        destroy_partition()
        sleep(1)
    # create partition
    if InstallationData.create:
        GLib.idle_add(update_progress, progressbar, _("Creating new partitions"))
        add_partition()
        sleep(1)
    progressbar_text = None
    process = Popen(
        command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True, universal_newlines=True
    )
    while True:
        line = process.stdout.readline()
        if not line:
            break
        progressbar_text = line.rstrip()
        GLib.idle_add(update_progress, progressbar, progressbar_text)
        # Those for next 4 line is for debugging only.
        # filer = open(f"{tmp}/tmp", "a")
        # filer.writelines(progressbar_text)
        # filer.close
        print(progressbar_text)
    if progressbar_text.rstrip() == "Installation finished!":
        Popen(f'python {install-station_dir}/end.py', shell=True, close_fds=True)
    else:
        Popen(f'python {install-station_dir}/error.py', shell=True, close_fds=True)
    Window.hide()


class InstallWindow:

    def __init__(self):
        self.vBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        self.vBox.show()
        label = Gtk.Label(label=_("Installation in progress"), name="Header")
        label.set_property("height-request", 50)
        self.vBox.pack_start(label, False, False, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=0, name="install")
        hbox.show()
        self.vBox.pack_end(hbox, True, True, 0)
        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        vbox2.show()
        label2 = Gtk.Label(name="sideText")

        label2.set_markup(_(
            "Thank you for choosing GhostBSD!\n\n"
            "We believe every computer operating system should "
            "be simple, elegant, secure and protect your privacy"
            " while being easy to use. GhostBSD is simplifying "
            "FreeBSD for those who lack the technical expertise "
            "required to use it and lower the entry-level of "
            "using BSD. \n\nWe hope you'll enjoy our BSD "
            "operating system."
        ))
        label2.set_justify(Gtk.Justification.LEFT)
        label2.set_line_wrap(True)
        # label2.set_max_width_chars(10)
        label2.set_alignment(0.0, 0.2)
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=0, name="TransBox")
        hbox2.show()
        hbox.pack_start(hbox2, True, True, 0)
        hbox2.pack_start(label2, True, True, 30)
        image = Gtk.Image()
        image.set_from_file(f"{install-station_dir}/image/G_logo.gif")
        # image.set_size_request(width=256, height=256)
        image.show()
        hbox.pack_end(image, True, True, 20)

    def get_model(self):
        return self.vBox


class InstallProgress:

    def __init__(self):
        self.pbar = Gtk.ProgressBar()
        self.pbar.set_show_text(True)
        command = f'sudo {pc_sysinstall} -c {installation_config}'
        thread = threading.Thread(
            target=read_output,
            args=(
                command,
                self.pbar
            ),
            daemon=True
        )
        thread.start()
        self.pbar.show()

    def get_progressbar(self):
        return self.pbar
