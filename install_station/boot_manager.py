import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from install_station.partition import bios_or_uefi
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


class BootManager:
    """
    Utility class for managing boot manager selection in GhostBSD installation following the utility class pattern.
    
    This class provides a GTK+ interface for selecting and configuring boot managers
    including rEFInd, FreeBSD boot manager, and native UEFI/BIOS loaders. The class
    automatically determines available options based on the partition scheme (GPT/MBR)
    and firmware type (UEFI/BIOS).
    
    Available boot manager options:
    - rEFInd: Available only for GPT + UEFI configurations
    - FreeBSD boot manager: Available only for MBR partition schemes
    - Native loader: Default option, always available (UEFI or BIOS loader)
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the InstallationData system for configuration persistence.
    """
    # Class variables for state management
    boot = None
    vbox1 = None
    
    # UI elements as class variables
    refind = None
    bsd = None
    none = None
    box3 = None

    @classmethod
    def get_model(cls):
        """
        Return the GTK widget model for the boot manager interface.
        
        Creates and initializes the UI if it doesn't exist yet.
        
        Returns:
            Gtk.Box: The main container widget for the boot manager interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @classmethod
    def boot_manager_selection(cls, _radiobutton, val: str):
        """
        Handle boot manager selection from radio buttons.
        
        Called when a radio button is toggled to update the selected boot manager
        option and store it in both the class variable and InstallationData.
        
        Args:
            _radiobutton: The radio button widget that was toggled (unused)
            val: The boot manager value ('refind', 'bsd', or 'none')
        """
        cls.boot = val
        InstallationData.boot = cls.boot

    @classmethod
    def get_boot_manager_option(cls):
        """
        Get the currently selected boot manager option.
        
        Returns the boot manager value from InstallationData if available,
        otherwise falls back to the class variable.
        
        Returns:
            str: The selected boot manager ('refind', 'bsd', or 'none')
        """
        return InstallationData.boot or cls.boot

    @classmethod
    def initialize(cls):
        """
        Initialize the boot manager user interface following the utility class pattern.
        
        Creates the GTK+ interface for boot manager selection including:
        - Title header ("Boot Option")
        - Radio button group for boot manager options
        - Automatic option availability based on partition scheme and firmware type
        - Default selection of native loader option
        
        The interface adapts based on:
        - Firmware type (UEFI/BIOS) detected from system
        - Partition scheme (GPT/MBR) from installation configuration
        - rEFInd: Only available for GPT + UEFI
        - FreeBSD boot manager: Only available for MBR
        - Native loader: Always available as default
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        
        # Determine firmware type
        if bios_or_uefi() == "UEFI":
            loader = "UEFI"
        else:
            loader = "BIOS"
        
        # Get partition scheme from InstallationData
        scheme = cls._get_partition_scheme()
        
        # Create title header
        title = Gtk.Label(label=get_text('Boot Option'), name="Header")
        title.set_property("height-request", 50)
        cls.vbox1.pack_start(title, False, False, 0)
        
        # Create main horizontal container
        hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=0)
        hbox1.show()
        cls.vbox1.pack_start(hbox1, True, True, 10)
        
        # Create vertical box for radio buttons
        bbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        bbox1.show()
        
        # rEFInd boot manager option
        cls.refind = Gtk.RadioButton(label=get_text("Setup rEFInd boot manager"))
        bbox1.pack_start(cls.refind, False, True, 10)
        cls.refind.connect("toggled", cls.boot_manager_selection, "refind")
        cls.refind.show()
        
        # Enable rEFInd only for GPT + UEFI
        if scheme == 'GPT' and loader == "UEFI":
            cls.refind.set_sensitive(True)
        else:
            cls.refind.set_sensitive(False)
        
        # FreeBSD boot manager option
        cls.bsd = Gtk.RadioButton.new_with_label_from_widget(
            cls.refind,
            get_text("Setup FreeBSD boot manager")
        )
        bbox1.pack_start(cls.bsd, False, True, 10)
        cls.bsd.connect("toggled", cls.boot_manager_selection, "bsd")
        cls.bsd.show()
        
        # Enable FreeBSD boot manager only for MBR
        if scheme == 'MBR':
            cls.bsd.set_sensitive(True)
        else:
            cls.bsd.set_sensitive(False)
        
        # Native loader option (always available)
        cls.none = Gtk.RadioButton.new_with_label_from_widget(
            cls.bsd,
            get_text("FreeBSD {loader} loader only").format(loader=loader)
        )
        bbox1.pack_start(cls.none, False, True, 10)
        cls.none.connect("toggled", cls.boot_manager_selection, "none")
        cls.none.show()
        
        # Add radio button container to main layout
        hbox1.pack_start(bbox1, False, False, 50)
        
        # Set default selection
        cls.none.set_active(True)
        cls.boot = "none"
        InstallationData.boot = cls.boot
        
        # Create additional container for future expansion
        cls.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.box3.set_border_width(0)
        cls.vbox1.pack_start(cls.box3, True, True, 0)

    @classmethod
    def _get_partition_scheme(cls):
        """
        Determine the partition scheme from installation configuration data.
        
        Checks ZFS and UFS configuration data, then falls back to InstallationData.scheme
        or defaults to GPT if no scheme is found.
        
        Returns:
            str: The partition scheme ('GPT' or 'MBR')
        """
        # Check ZFS config data for scheme
        if InstallationData.zfs_config_data:
            scheme_line = next((line for line in InstallationData.zfs_config_data if 'partscheme=' in line), '')
            if scheme_line:
                return scheme_line.split('=')[1].strip()
        
        # Check UFS config data for scheme  
        if InstallationData.ufs_config_data:
            scheme_line = next((line for line in InstallationData.ufs_config_data if 'partscheme=' in line), '')
            if scheme_line:
                return scheme_line.split('=')[1].strip()
        
        # Use scheme from InstallationData or default to GPT
        if InstallationData.scheme:
            # Handle both 'partscheme=GPT' and 'GPT' formats
            if 'partscheme=' in InstallationData.scheme:
                return InstallationData.scheme.split('=')[1].strip()
            else:
                return InstallationData.scheme.strip()
        
        return 'GPT'  # Default fallback
