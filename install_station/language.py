from gi.repository import Gtk, Gdk
import os
from install_station.system_calls import (
    language_dictionary,
    localize_system
)
from install_station.data import InstallationData, tmp, logo
import gettext

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext

# Ensure temp directory exists
if not os.path.exists(tmp):
    os.makedirs(tmp)

lang_dictionary = language_dictionary()
# Text to be replace be multiple language file.
welltext = _("Select the language you want to use with GhostBSD.")

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class Language:
    _instance = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Language, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize only once."""
        if not self._initialized:
            self._language = None
            self._vbox1 = None
            self._initialize_ui()
            self._initialized = True

    # On selection it overwrite the default language file.
    def _language_selection(self, tree_selection):
        model, treeiter = tree_selection.get_selected()
        if treeiter is not None:
            value = model[treeiter][0]
            self._language = lang_dictionary[value]
            InstallationData.language = value
            InstallationData.language_code = lang_dictionary[value]
        return

    def _setup_language_columns(self, treeView):
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        column_header = Gtk.Label(label=_('Language'))
        column_header.set_use_markup(True)
        column_header.show()
        column.set_widget(column_header)
        column.set_sort_column_id(0)
        treeView.append_column(column)
        return

    # Initial definition.
    def _initialize_ui(self):
        # Add a Default vertical box
        self._vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        self._vbox1.show()
        # Add a second vertical box
        grid = Gtk.Grid()
        title = Gtk.Label(label=_('Welcome To GhostBSD!'), name="Header")
        title.set_property("height-request", 50)
        self._vbox1.pack_start(title, False, False, 0)
        self._vbox1.pack_start(grid, True, True, 0)
        grid.set_row_spacing(10)
        grid.set_column_spacing(3)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        # Adding a Scrolling Window
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # Adding a treestore and store language in it.
        store = Gtk.TreeStore(str)
        for line in lang_dictionary:
            store.append(None, [line])
        treeview = Gtk.TreeView()
        treeview.set_model(store)
        treeview.set_rules_hint(True)
        self._setup_language_columns(treeview)
        tree_selection = treeview.get_selection()
        tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        tree_selection.connect("changed", self._language_selection)
        sw.add(treeview)
        sw.show()
        grid.attach(sw, 1, 2, 1, 9)
        # add text in a label.
        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        vbox2.set_border_width(10)
        vbox2.show()
        wellcome_text = Gtk.Label(label=welltext)
        wellcome_text.set_use_markup(True)
        table = Gtk.Table()
        table.attach(wellcome_text, 0, 1, 3, 4)
        vbox2.pack_start(table, False, False, 5)
        image = Gtk.Image()
        image.set_from_file(logo)
        image.show()
        # grid.attach(self.wellcome, 1, 1, 3, 1)
        vbox2.pack_start(image, True, True, 5)
        grid.attach(vbox2, 2, 2, 2, 9)
        grid.show()

    @classmethod
    def get_model(cls):
        return cls()._vbox1

    @classmethod
    def get_language(cls):
        """Get the selected language."""
        return InstallationData.language_code or cls()._language

    def save_selection(self):
        # Language is now saved in InstallationData automatically
        pass

    @classmethod
    def save_language(cls):
        language_code = InstallationData.language_code or cls()._language
        if language_code:
            localize_system(language_code)