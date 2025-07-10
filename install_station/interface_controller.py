from gi.repository import Gtk
import gettext
from install_station.install import InstallProgress, InstallWindow
from install_station.partition import DiskPartition
from install_station.window import Window
from install_station.data import InstallationData

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext


class Button:
    back_button = Gtk.Button(label=_('Back'))
    """This button is used to go back to the previous page."""
    cancel_button = Gtk.Button(label=_('Cancel'))
    """This button is used to quit and clean up."""
    next_button = Gtk.Button(label=_('Next'))
    """This button is used to go to the next page."""
    _box = None

    @classmethod
    def hide_all(cls):
        """
        This method hides all buttons.
        """
        cls.back_button.hide()
        cls.cancel_button.hide()
        cls.next_button.hide()

    @classmethod
    def show_initial(cls):
        """
        This method shows the initial buttons. Cancel and Next.
        """
        cls.cancel_button.show()
        cls.next_button.show()

    @classmethod
    def show_back(cls):
        """
        This method shows the back button.
        """
        cls.back_button.show()

    @classmethod
    def hide_back(cls):
        """
        This method hides the back button.
        """

    @classmethod
    def box(cls):
        """
        This method creates a box container of buttons aligned to the right.

        Returns:
            Box container with buttons aligned to the right for navigation.
        """
        if cls._box is None:
            # Use Box instead of Grid for better right-alignment control
            cls._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=5)
            cls._box.set_halign(Gtk.Align.END)  # Align the entire box to the right
            
            cls.back_button.connect("clicked", Interface.back_page)
            cls._box.pack_start(cls.back_button, False, False, 0)
            
            cls.cancel_button.connect("clicked", Interface.delete)
            cls._box.pack_start(cls.cancel_button, False, False, 0)
            
            cls.next_button.connect("clicked", Interface.next_page)
            cls._box.pack_start(cls.next_button, False, False, 0)
            
            cls._box.show()
        return cls._box


class Interface:
    welcome = None
    installation_type = None
    custom_partition = None
    full_zfs = None
    boot_manager = None
    network_setup = None
    page = Gtk.Notebook()

    @classmethod
    def get_interface(cls):
        interface_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        interface_box.show()
        interface_box.pack_start(cls.page, True, True, 0)
        cls.page.show()
        cls.page.set_show_tabs(False)
        cls.page.set_show_border(False)
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        welcome_box.show()
        cls.welcome.initialize()
        get_types = cls.welcome.get_model()
        welcome_box.pack_start(get_types, True, True, 0)
        Window.set_title(_("Welcome to GhostBSD"))
        label = Gtk.Label(label=_("Welcome to GhostBSD"))
        cls.page.insert_page(welcome_box, label, 0)
        # Set what page to start at type of installation
        cls.page.set_current_page(0)
        cls.nbButton = Gtk.Notebook()
        interface_box.pack_end(cls.nbButton, False, False, 5)
        cls.nbButton.show()
        cls.nbButton.set_show_tabs(False)
        cls.nbButton.set_show_border(False)
        label = Gtk.Label(label=_("Button"))
        cls.nbButton.insert_page(Button.box(), label, 0)
        return interface_box

    @classmethod
    def delete(cls, _widget, _event=None):
        """Close the main window."""
        InstallationData.reset()
        Gtk.main_quit()

    @classmethod
    def next_page(cls, _widget):
        if InstallationData.install_mode == "install":
            cls.next_install_page()
        else:
            cls.next_setup_page()

    @classmethod
    def next_install_page(cls):
        """Go to the next window."""
        page = cls.page.get_current_page()
        if page == 0:
            type_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
            type_box.show()
            get_types = cls.installation_type.get_model()
            type_box.pack_start(get_types, True, True, 0)
            label = Gtk.Label(label=_("Installation Types"))
            cls.page.insert_page(type_box, label, 1)
            cls.page.next_page()
            cls.page.show_all()
            Button.show_initial()
        elif page == 1:
            Button.show_back()
            if InstallationData.filesystem_type == "custom":
                custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
                custom_box.show()
                get_part = cls.custom_partition.get_model()
                custom_box.pack_start(get_part, True, True, 0)
                label = Gtk.Label(label=_("Custom Configuration"))
                cls.page.insert_page(custom_box, label, 2)
                cls.page.next_page()
                cls.page.show_all()
                Button.next_button.set_sensitive(False)
            elif InstallationData.filesystem_type == "zfs":
                zfs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
                zfs_box.show()
                get_zfs = cls.full_zfs.get_model()
                zfs_box.pack_start(get_zfs, True, True, 0)
                label = Gtk.Label(label=_("ZFS Configuration"))
                cls.page.insert_page(zfs_box, label, 2)
                cls.page.next_page()
                cls.page.show_all()
                Button.next_button.set_sensitive(False)
        elif page == 2:
            boot_manager_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
            boot_manager_box.show()
            get_root = cls.boot_manager.get_model()
            boot_manager_box.pack_start(get_root, True, True, 0)
            label = Gtk.Label(label=_("Boot Option"))
            cls.page.insert_page(boot_manager_box, label, 3)
            Button.next_button.set_label(_("Install"))
            cls.page.next_page()
            cls.page.show_all()
            Button.next_button.set_sensitive(True)
        elif page == 3:
            installation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
            installation_box.show()
            install_window = InstallWindow()
            get_install = install_window.get_model()
            installation_box.pack_start(get_install, True, True, 0)
            label = Gtk.Label(label=_("Installation Progress"))
            cls.page.insert_page(installation_box, label, 8)
            cls.page.next_page()
            installation_progressbar = InstallProgress()
            progressbar = installation_progressbar.get_progressbar()
            box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
            box1.show()
            label = Gtk.Label(label=_("Progress Bar"))
            box1.pack_end(progressbar, False, False, 0)
            cls.nbButton.insert_page(box1, label, 4)
            cls.nbButton.next_page()
        current_page_widget = cls.page.get_nth_page(cls.page.get_current_page())
        title_text = cls.page.get_tab_label_text(current_page_widget)
        Window.set_title(title_text)

    @classmethod
    def next_setup_page(cls):
        page = cls.page.get_current_page()
        if page == 0:
            Button.next_button.show()
            Button.next_button.set_sensitive(False)
            Window.set_title(_("Network Setup"))
            net_setup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
            net_setup_box.show()
            model = cls.network_setup.get_model()
            net_setup_box.pack_start(model, True, True, 0)
            label = Gtk.Label(label=_("Network Setup"))
            cls.page.insert_page(net_setup_box, label, 1)
            cls.page.next_page()
            cls.page.show_all()
        if page == 1:
            with open('/usr/home/ghostbsd/.xinitrc', 'w') as xinitrc:
                xinitrc.writelines('gsettings set org.mate.SettingsDaemon.plugins.housekeeping active true &\n')
                xinitrc.writelines('gsettings set org.mate.screensaver lock-enabled false &\n')
                xinitrc.writelines('exec ck-launch-session mate-session\n')
            Gtk.main_quit()

    @classmethod
    def back_page(cls, _widget):
        """Go back to the previous window."""
        current_page = cls.page.get_current_page()
        if current_page == 1:
            Button.hide_back()
        if current_page == 2:
            Button.hide_back()
        elif current_page == 3:
            Button.next_button.set_label(_("Next"))
        cls.page.prev_page()
        new_page = cls.page.get_current_page()
        if current_page == 2 and new_page == 1:
            # Reset partition configuration data when going back
            InstallationData.destroy = {}
            InstallationData.delete = []
            InstallationData.create = []
            InstallationData.new_partition = []
            InstallationData.scheme = ""
            InstallationData.disk = ""
            InstallationData.slice = ""
            InstallationData.zfs_config_data = []
            InstallationData.ufs_config_data = []
            # Clean up temporary directory if it exists
            DiskPartition.create_partition_database()
        Button.next_button.set_sensitive(True)
