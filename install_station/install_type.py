"""
Module to create the inner window for select what type of installation.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from install_station.data import InstallationData, get_text

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class InstallTypes:
    """Utility class for filesystem type selection following the utility class pattern.
    
    This class provides a GTK+ interface for installation type selection including:
    - Filesystem type selection between ZFS disk configuration and multi-boot
    - Radio button interface for user selection
    - Integration with InstallationData for persistent configuration
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the Interface controller for navigation flow.
    """
    # Class variables instead of instance variables
    ne: str = 'zfs'
    vbox1: Gtk.Box | None = None
    full_zfs_button: Gtk.RadioButton | None = None
    custom_button: Gtk.RadioButton | None = None

    @classmethod
    def filesystem_type(cls, widget: Gtk.RadioButton, val: str) -> None:
        """Handle filesystem type selection from radio buttons.
        
        Only responds to activation, not deactivation. Updates both
        class variables and InstallationData with the selected filesystem type.
        
        Args:
            widget: RadioButton widget that triggered the action
            val: Filesystem type value ('zfs' or 'custom')
        """
        # Only respond to activation, not deactivation
        if widget.get_active():
            cls.ne = val
            InstallationData.install_type = val
            print(f"Filesystem type selected: {val}")

    @classmethod
    def get_type(cls) -> str:
        """Get the current filesystem type selection.
        
        Returns:
            str: Current filesystem type ('zfs' or 'custom')
        """
        return InstallationData.install_type or cls.ne

    @classmethod
    def get_model(cls) -> Gtk.Box:
        """Return the GTK widget model for the installation type interface.
        
        Returns the main container widget that was created during initialization.
        
        Returns:
            Gtk.Box: The main container widget for the installation type interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @classmethod
    def initialize(cls) -> None:
        """Initialize the installation type selection UI following the utility class pattern.
        
        Creates the main interface including:
        - Radio buttons for ZFS disk configuration and multi-boot setup
        - Descriptive text for each option
        - Centered layout with proper spacing
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=0)
        InstallationData.install_type = cls.ne
        cls.vbox1.pack_start(hbox1, True, False, 0)
        hbox1.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label(label=get_text("How do you want to install GhostBSD?"))
        label.set_alignment(0, 0.5)
        vbox2.pack_start(label, False, False, 10)
        # Create radio button group
        cls.full_zfs_button = Gtk.RadioButton(
            label=get_text(
                "<b>Disks Configuration</b>"
                "\nInstall GhostBSD using Stripe, Mirror, RAIDZ1, RAIDZ2, or RAIDZ3 configurations."
            )
        )
        cls.full_zfs_button.get_child().set_use_markup(True)
        cls.full_zfs_button.get_child().set_line_wrap(True)
        vbox2.pack_start(cls.full_zfs_button, True, True, 10)
        cls.full_zfs_button.connect("toggled", cls.filesystem_type, "zfs")
        cls.full_zfs_button.show()

        cls.custom_button = Gtk.RadioButton.new_with_label_from_widget(
            cls.full_zfs_button,
            get_text(
                "<b>Multi-Boot Configuration</b>\n"
                "Install GhostBSD with ZFS alongside other operating systems."
            )
        )
        cls.custom_button.get_child().set_use_markup(True)
        cls.custom_button.get_child().set_line_wrap(True)
        vbox2.pack_start(cls.custom_button, False, True, 10)
        cls.custom_button.connect("toggled", cls.filesystem_type, "custom")
        cls.custom_button.show()

        hbox1.pack_start(vbox2, True, False, 150)
        vbox2.set_halign(Gtk.Align.CENTER)
        cls.full_zfs_button.set_active(True)
