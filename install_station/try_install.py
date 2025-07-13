import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from install_station.data import InstallationData, get_text, gif_logo

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class TryOrInstall:
    """
    Utility class for the welcome screen and initial mode selection following the utility class pattern.
    
    This class provides a GTK+ interface for the initial GhostBSD welcome screen including:
    - Mode selection between "Install GhostBSD" and "Try GhostBSD" using radio buttons
    - Visual elements with GhostBSD logo and instructional text
    - Integration with InstallationData for persistent configuration
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the Interface controller for navigation flow.
    """
    # Class variables instead of instance variables
    what = None
    install_button = None
    try_button = None
    instruction_label = None
    vbox1 = None

    @classmethod
    def mode_selection(cls, widget, val):
        """
        Handle mode selection from radio buttons.
        
        Only responds to activation, not deactivation. Updates both
        class variables and InstallationData with the selected mode.
        
        Args:
            widget: RadioButton widget that triggered the action
            val: Mode value ('install' or 'try')
        """
        # Only respond to activation, not deactivation
        if widget.get_active():
            cls.what = val
            InstallationData.install_mode = val
            print(f"Mode selected: {val}")

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
        - GhostBSD logo on the left side
        - Radio buttons for Install/Try options on the right side
        - Instructional text explaining the options
        - Grid-based layout with proper spacing and margins
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.what = 'install'  # Default to install mode
        InstallationData.install_mode = cls.what
        
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        
        main_grid = Gtk.Grid()
        cls.vbox1.pack_start(main_grid, True, True, 0)
        
        # Left side - Logo
        logo_image = Gtk.Image()
        logo_image.set_from_file(gif_logo)
        logo_image.show()
        
        # Right side - Radio button options
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        right_box.set_border_width(20)
        right_box.set_halign(Gtk.Align.CENTER)
        right_box.set_valign(Gtk.Align.CENTER)
        right_box.show()
        
        # Instruction label
        cls.instruction_label = Gtk.Label(label=get_text("What would you like to do?"))
        cls.instruction_label.set_alignment(0.0, 0.5)
        right_box.pack_start(cls.instruction_label, False, False, 10)
        
        # Create radio button group
        cls.install_button = Gtk.RadioButton(
            label=get_text(
                "<b>Install GhostBSD</b>\n"
                "Install GhostBSD on your computer."
            )
        )
        cls.install_button.get_child().set_use_markup(True)
        cls.install_button.get_child().set_line_wrap(True)
        right_box.pack_start(cls.install_button, False, False, 10)
        cls.install_button.connect("toggled", cls.mode_selection, "install")
        cls.install_button.show()
        
        cls.try_button = Gtk.RadioButton.new_with_label_from_widget(
            cls.install_button,
            get_text(
                "<b>Try GhostBSD</b>\n"
                "Run GhostBSD without installing to your computer."
            )
        )
        cls.try_button.get_child().set_use_markup(True)
        cls.try_button.get_child().set_line_wrap(True)
        right_box.pack_start(cls.try_button, False, False, 10)
        cls.try_button.connect("toggled", cls.mode_selection, "try")
        cls.try_button.show()
        
        # Layout in grid
        main_grid.set_row_spacing(20)
        main_grid.set_column_spacing(20)
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        main_grid.set_margin_left(10)
        main_grid.set_margin_right(10)
        main_grid.set_margin_top(10)
        main_grid.set_margin_bottom(10)
        
        main_grid.attach(logo_image, 0, 0, 1, 1)
        main_grid.attach(right_box, 1, 0, 1, 1)
        main_grid.show()
        
        # Set default selection
        cls.install_button.set_active(True)

    @classmethod
    def get_model(cls):
        """
        Return the GTK widget model for the welcome screen interface.
        
        Returns the main container widget created during initialization.
        
        Returns:
            Gtk.Box: The main container widget for the welcome screen interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1
