import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os
from install_station.system_calls import (
    language_dictionary,
    localize_system
)
from install_station.data import InstallationData, tmp, gif_logo, get_text
from install_station.window import Window

# Ensure temp directory exists
if not os.path.exists(tmp):
    os.makedirs(tmp)

lang_dictionary = language_dictionary()

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
    """
    Utility class for the language selection screen following the utility class pattern.
    
    This class provides a GTK+ interface for language selection including:
    - Language selection from available system languages
    - Visual elements with welcome message and logo
    - Integration with InstallationData for persistent configuration
    - Environment variable setting for immediate translation updates
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the Interface controller for navigation flow.
    """
    # Class variables instead of instance variables
    vbox1 = None
    language = None
    treeview = None
    welcome_text = None
    language_column_header = None

    @classmethod
    def language_selection(cls, tree_selection):
        """
        Handle language selection from the treeview.
        
        Extracts the selected language from the tree view and updates both
        class variables and InstallationData with the language name and code.
        Also sets environment variables globally so all modules pick up the language.
        
        Args:
            tree_selection: TreeSelection widget containing the user's language choice
        """
        model, treeiter = tree_selection.get_selected()
        if treeiter is not None:
            value = model[treeiter][0]
            language_code = lang_dictionary[value]
            cls.language = language_code
            InstallationData.language = value
            InstallationData.language_code = language_code
            print(f"Language selected: {value} ({language_code})")
            
            # Set environment variables globally so all modules pick up the language
            import os
            os.environ['LANGUAGE'] = language_code
            os.environ['LC_ALL'] = f'{language_code}.UTF-8'
            os.environ['LANG'] = f'{language_code}.UTF-8'
            
            # Update the UI text with new translations
            cls.update_ui_text()

    @classmethod
    def update_ui_text(cls):
        """
        Update all UI text elements with new translations after language change.
        """
        from install_station.interface_controller import Button
        
        # Update navigation buttons
        Button.update_button_labels()
        
        # Update the welcome text
        if hasattr(cls, 'welcome_text') and cls.welcome_text:
            cls.welcome_text.set_text(
                get_text(
                    "Please select your language:"
                )
            )

        # Update the language column header
        if hasattr(cls, 'language_column_header') and cls.language_column_header:
            cls.language_column_header.set_text(get_text('Language'))

        Window.set_title(get_text("Welcome to GhostBSD"))

    @classmethod
    def setup_language_columns(cls, treeview):
        """
        Configure the language selection treeview with appropriate columns.
        
        Creates a single column with a "Language" header for displaying
        available languages in the tree view.
        
        Args:
            treeview: TreeView widget to configure with language column
        """
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        column_header = Gtk.Label(label=get_text('Language'))
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
    def save_language(cls):
        """
        Apply the language configuration to the system.
        
        This method applies the selected language to the system for 
        permanent configuration during installation.
        """
        language_code = InstallationData.language_code or cls.language
        if language_code:
            localize_system(language_code)

    @classmethod
    def initialize(cls):
        """
        Initialize the language selection UI following the utility class pattern.
        
        Creates the main interface including:
        - Language selection tree view on the left side
        - Welcome message and logo on the right side
        - Grid-based layout with proper spacing and margins
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.language = None
        
        # Main container
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        
        main_grid = Gtk.Grid()
        cls.vbox1.pack_start(main_grid, True, True, 0)
        
        # Left side - Language selection
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        store = Gtk.TreeStore(str)
        for line in lang_dictionary:
            store.append(None, [line])
            
        cls.treeview = Gtk.TreeView()
        cls.treeview.set_model(store)
        cls.treeview.set_rules_hint(True)
        cls.treeview.set_headers_visible(False)
        cls.setup_language_columns(cls.treeview)
        tree_selection = cls.treeview.get_selection()
        tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        tree_selection.connect("changed", cls.language_selection)
        sw.add(cls.treeview)
        sw.show()
        
        # Right side - Welcome content
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        right_box.set_border_width(20)
        right_box.show()
        
        # Welcome text
        cls.welcome_text = Gtk.Label(
            label=get_text(
                "Please select your language:"
            )
        )
        cls.welcome_text.set_use_markup(True)
        cls.welcome_text.set_line_wrap(True)
        cls.welcome_text.set_justify(Gtk.Justification.CENTER)
        cls.welcome_text.show()
        
        # Logo
        image = Gtk.Image()
        image.set_from_file(gif_logo)
        image.show()
        
        right_box.pack_start(cls.welcome_text, False, False, 10)
        right_box.pack_start(sw, True, True, 10)
        
        # Layout in grid
        main_grid.set_row_spacing(10)
        main_grid.set_column_spacing(20)
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        main_grid.set_margin_left(10)
        main_grid.set_margin_right(10)
        main_grid.set_margin_top(10)
        main_grid.set_margin_bottom(10)
        
        main_grid.attach(image, 0, 0, 1, 1)
        main_grid.attach(right_box, 1, 0, 1, 1)
        main_grid.show()

    @classmethod
    def get_model(cls):
        """
        Return the GTK widget model for the language selection interface.
        
        Returns the main container widget that was created during initialization.
        
        Returns:
            Gtk.Box: The main container widget for the language selection interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @classmethod
    def get_language(cls):
        """
        Get the selected language code.
        
        Returns:
            str: The selected language code
        """
        return InstallationData.language_code or cls.language

    @classmethod
    def get_language_info(cls):
        """
        Get the current language configuration information.
        
        Returns:
            dict: Dictionary containing language name and code information
        """
        return {
            'language': InstallationData.language or '',
            'language_code': InstallationData.language_code or cls.language or ''
        }
