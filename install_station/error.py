import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import gettext

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext


class ErrorWindow:

    @classmethod
    def on_close(cls, _widget):
        Gtk.main_quit()

    def __init__(self):
        window = Gtk.Window()
        window.set_border_width(8)
        window.connect("destroy", Gtk.main_quit)
        window.set_title(_("Installation Error"))
        # window.set_icon_from_file("/usr/local/lib/install-station/image/logo.png")
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        title = Gtk.Label()
        title.set_use_markup(True)
        title_text = _("Installation has failed!")
        title.set_markup(f'<b><span size="larger">{title_text}</span></b>')
        label = Gtk.Label()
        label.set_use_markup(True)
        url = 'https://github.com/ghostbsd/ghostbsd-src/issues/new/choose'
        anchor = f"<a href='{url}'>{_('GhostBSD issue system')}</a>"
        message = _("Please report the issue to {anchor}, and \nbe sure to provide /tmp/.pc-sysinstall/pc-sysinstall.log.").format(anchor=anchor)
        label.set_markup(message)
        box2.pack_start(title, True, True, 0)
        box2.pack_start(label, True, True, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        table = Gtk.Table(n_rows=1, n_columns=2, homogeneous=True)
        ok = Gtk.Button(label=_("Ok"))
        ok.connect("clicked", self.on_close)
        table.attach(ok, 0, 2, 0, 1)
        box2.pack_start(table, True, True, 0)
        window.show_all()


ErrorWindow()
Gtk.main()
