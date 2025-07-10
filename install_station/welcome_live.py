import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import gettext
from install_station.system_calls import language_dictionary
from install_station.interface_controller import Interface
from install_station.data import InstallationData
from install_station.window import Window

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext

lang_dictionary = language_dictionary()

Messages = _("""To run GhostBSD without installing, select "Try GhostBSD."

To install GhostBSD on your computer hard disk drive, click "Install GhostBSD."

Note: Language selection only works when selecting "Try GhostBSD."
      When installing GhostBSD, the installation program is only in English.""")

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class Welcome:
    """
    Utility class for the welcome screen and initial mode selection following the utility class pattern.
    
    This class provides a GTK+ interface for the initial GhostBSD welcome screen including:
    - Language selection from available system languages
    - Mode selection between "Install GhostBSD" and "Try GhostBSD"
    - Visual elements with images and instructional text
    - Integration with InstallationData for persistent configuration
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the Interface controller for navigation flow.
    """
    # Class variables instead of instance variables
    what = None
    language = None
    install_ghostbsd = None
    try_ghostbsd = None
    vbox1 = None

    @classmethod
    def language_selection(cls, tree_selection):
        """
        Handle language selection from the treeview.
        
        Extracts the selected language from the tree view and updates both
        class variables and InstallationData with the language name and code.
        Also updates the UI text to reflect the new language selection.
        
        Args:
            tree_selection: TreeSelection widget containing the user's language choice
        """
        model, tree_iter = tree_selection.get_selected()
        if tree_iter is not None:
            value = model[tree_iter][0]
            language_code = lang_dictionary[value]
            cls.language = language_code
            InstallationData.language = value
            InstallationData.language_code = language_code
            print(f"Language selected: {value} ({language_code})")
            
            # Update gettext to use the new language
            import os
            os.environ['LANGUAGE'] = language_code
            gettext.bindtextdomain('install-station', '/usr/local/share/locale')
            gettext.textdomain('install-station')
            
            # Update the UI text with new translations
            cls.update_ui_text()
        return

    @classmethod
    def update_ui_text(cls):
        """
        Update all UI text elements with new translations after language change.
        """
        # Reload the gettext function to pick up new locale
        _ = gettext.gettext
        
        # Update UI elements if they exist
        if hasattr(cls, 'install_button') and cls.install_button:
            cls.install_button.set_label(_('Install GhostBSD'))
        
        if hasattr(cls, 'try_button') and cls.try_button:
            cls.try_button.set_label(_('Try GhostBSD'))
            
        if hasattr(cls, 'text_label') and cls.text_label:
            cls.text_label.set_text(_("""To run GhostBSD without installing, select "Try GhostBSD."
        

To install GhostBSD on your computer hard disk drive, click "Install GhostBSD."

Note: Language selection only works when selecting "Try GhostBSD."
      When installing GhostBSD, the installation program is only in English."""))
            
        if hasattr(cls, 'language_column_header') and cls.language_column_header:
            cls.language_column_header.set_text(_('Language'))

        Window.set_title(_("Welcome to GhostBSD"))

    @classmethod
    def language_columns(cls, treeview):
        """
        Configure the language selection treeview with appropriate columns.
        
        Creates a single column with a "Language" header for displaying
        available languages in the tree view.
        
        Args:
            treeview: TreeView widget to configure with language column
        """
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        column_header = Gtk.Label(label=_('Language'))
        column_header.set_use_markup(True)
        column_header.show()
        column.set_widget(column_header)
        # Store reference for updating
        cls.language_column_header = column_header
        column.set_sort_column_id(0)
        treeview.append_column(column)

    @classmethod
    def save_selection(cls):
        """
        Save the current language selection.
        
        This method is maintained for compatibility but language selection
        is now automatically saved to InstallationData when chosen.
        """
        # Language is now saved in InstallationData automatically
        pass

    @classmethod
    def install_system(cls, _widget):
        """
        Handle "Install GhostBSD" button click.
        
        Sets the installation mode to 'install' and navigates to the
        installation workflow pages.
        
        Args:
            _widget: Button widget that triggered the action (unused)
        """
        cls.what = 'install'
        InstallationData.install_mode = 'install'
        Interface.next_install_page()

    @classmethod
    def try_system(cls, _widget):
        """
        Handle "Try GhostBSD" button click.
        
        Sets the installation mode to 'try' and navigates to the
        live system setup pages (typically network configuration).
        
        Args:
            _widget: Button widget that triggered the action (unused)
        """
        cls.what = 'try'
        InstallationData.install_mode = 'try'
        Interface.next_setup_page()

    @classmethod
    def get_what(cls):
        """
        Get the current installation mode.
        
        Returns the installation mode from InstallationData if available,
        otherwise falls back to the class variable.
        
        Returns:
            str: Current installation mode ('install' or 'try')
        """
        return InstallationData.install_mode or cls.what

    @classmethod
    def initialize(cls):
        """
        Initialize the welcome screen UI following the utility class pattern.
        
        Creates the main interface including:
        - Language selection tree view on the left side
        - Install and Try buttons with images on the right side
        - Instructional text explaining the options
        - Grid-based layout with proper spacing and margins
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.what = None
        cls.language = None
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        main_grid = Gtk.Grid()
        cls.vbox1.pack_start(main_grid, True, True, 0)
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        store = Gtk.TreeStore(str)
        for line in lang_dictionary:
            store.append(None, [line])
        treeview = Gtk.TreeView()
        treeview.set_model(store)
        treeview.set_rules_hint(True)
        cls.language_columns(treeview)
        tree_selection = treeview.get_selection()
        tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        tree_selection.connect("changed", cls.language_selection)
        sw.add(treeview)
        sw.show()
        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        vbox2.set_border_width(10)
        vbox2.show()
        pix_buf1 = GdkPixbuf.Pixbuf().new_from_file_at_scale(
            filename='/usr/local/lib/install-station/laptop.png',
            width=190,
            height=190,
            preserve_aspect_ratio=True
        )
        image1 = Gtk.Image.new_from_pixbuf(pix_buf1)
        image1.show()
        pix_buf2 = GdkPixbuf.Pixbuf().new_from_file_at_scale(
            filename='/usr/local/lib/install-station/disk.png',
            width=120,
            height=120,
            preserve_aspect_ratio=True)
        image2 = Gtk.Image.new_from_pixbuf(pix_buf2)
        image2.show()
        install_button = Gtk.Button(label=_('Install GhostBSD'), image=image1,
                                    image_position=2)
        install_button.set_always_show_image(True)
        install_button.connect("clicked", cls.install_system)
        try_button = Gtk.Button(label=_('Try GhostBSD'), image=image2,
                                image_position=2)
        try_button.set_always_show_image(True)
        try_button.connect("clicked", cls.try_system)
        text_label = Gtk.Label(label=Messages)
        text_label.set_line_wrap(True)
        
        # Store references for updating
        cls.install_button = install_button
        cls.try_button = try_button
        cls.text_label = text_label
        right_grid = Gtk.Grid()
        right_grid.set_row_spacing(10)
        right_grid.set_column_spacing(2)
        right_grid.set_column_homogeneous(True)
        right_grid.set_row_homogeneous(True)
        right_grid.set_margin_left(10)
        right_grid.set_margin_right(10)
        right_grid.set_margin_top(10)
        right_grid.set_margin_bottom(10)
        right_grid.attach(install_button, 1, 1, 1, 5)
        right_grid.attach(try_button, 2, 1, 1, 5)
        right_grid.attach(text_label, 1, 6, 2, 5)
        main_grid.set_row_spacing(10)
        main_grid.set_column_spacing(4)
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        main_grid.set_margin_left(10)
        main_grid.set_margin_right(10)
        main_grid.set_margin_top(10)
        main_grid.set_margin_bottom(10)
        main_grid.attach(sw, 1, 1, 1, 10)
        main_grid.attach(right_grid, 2, 1, 3, 10)
        main_grid.show()

    @classmethod
    def get_model(cls):
        """
        Return the GTK widget model for the welcome screen interface.
        
        Returns the main container widget that was created during initialization.
        
        Returns:
            Gtk.Box: The main container widget for the welcome screen interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1
