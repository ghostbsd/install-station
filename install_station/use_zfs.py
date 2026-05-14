from gi.repository import Gtk, Gdk
from install_station.common import password_strength
from install_station.data import InstallationData, zfs_datasets, be_name, logo, get_text
from install_station.partition import bios_or_uefi
from install_station.system_calls import (
    get_ram_size_mb,
    zfs_disk_query,
    zfs_disk_size_query,
)
from install_station.interface_controller import Button


cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class ZFS:
    """
    Utility class for ZFS configuration and disk management following the utility class pattern.
    
    This class provides a GTK+ interface for configuring ZFS installations including:
    - Disk selection and validation
    - Pool type configuration (stripe, mirror, RAIDZ1/2/3)
    - Partition scheme selection (GPT/MBR)
    - Disk encryption setup with password verification
    - ZFS pool name configuration
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the InstallationData system for configuration persistence.
    """
    # Class variables instead of instance variables
    zfs_disk_list = []
    pool_type = 'stripe'
    scheme = 'GPT'
    disk_encrypt = False
    mirror = 'stripe'
    vbox1 = None

    # UI elements as class variables
    pool = None
    swap_entry = None
    password = None
    repassword = None
    mirrorTips = None
    strenght_label = None
    img = None
    check_cell = None
    store = None

    @classmethod
    def save_selection(cls):
        """
        Save the current ZFS configuration to InstallationData.
        
        Validates required fields and generates ZFS configuration data including:
        - Pool name and type (stripe, mirror, RAIDZ1/2/3)
        - Disk partitioning scheme and encryption settings
        - Boot environment and dataset configuration
        
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields are populated
        if not cls.zfs_disk_list:
            raise ValueError("No disks selected for ZFS configuration")

        if cls.disk_encrypt and not cls.password.get_text().strip():
            raise ValueError("Password cannot be empty when disk encryption is enabled")

        size = int(cls.zfs_disk_list[0].partition('-')[2].rstrip()) - 512
        swap_size = cls.swap_entry.get_value_as_int()
        zfs_num = size - swap_size
        dgeli = '.eli' if cls.disk_encrypt else ''

        # Store configuration data in InstallationData instead of writing to file
        InstallationData.zfs_config_data = []

        InstallationData.zfs_config_data.append(f"zpoolName={cls.pool.get_text()}\n")
        InstallationData.zfs_config_data.append(f"beName={be_name}\n")
        InstallationData.zfs_config_data.append('ashift=12\n\n')
        disk = cls.zfs_disk_list[0].partition('-')[0].rstrip()
        InstallationData.zfs_config_data.append(f'disk0={disk}\n')
        InstallationData.zfs_config_data.append('partition=ALL\n')
        InstallationData.zfs_config_data.append(f'partscheme={cls.scheme}\n')
        InstallationData.zfs_config_data.append('commitDiskPart\n\n')
        if len(cls.zfs_disk_list) <= 1:
            pool_disk = '\n'
        else:
            zfs_disk = cls.zfs_disk_list
            mirror_dsk = ''
            for i in range(1, len(zfs_disk)):
                mirror_dsk += ' ' + zfs_disk[i].partition('-')[0].rstrip()
            pool_disk = f' ({cls.pool_type}:{mirror_dsk})\n'
        if bios_or_uefi() == "UEFI":
            zfs_num = zfs_num - 100
        else:
            zfs_num = zfs_num - 1
        # adding zero to use remaining space
        zfs_part = f'disk0-part=ZFS{dgeli} {zfs_num} {zfs_datasets}{pool_disk}'
        InstallationData.zfs_config_data.append(zfs_part)
        # encpass must be on the line immediately after the .eli partition
        if cls.disk_encrypt:
            InstallationData.zfs_config_data.append(f'encpass={cls.password.get_text()}\n')
        else:
            InstallationData.zfs_config_data.append('#encpass=None\n')
        if swap_size != 0:
            if cls.disk_encrypt:
                InstallationData.zfs_config_data.append('disk0-part=SWAP.eli 0 none\n')
            else:
                InstallationData.zfs_config_data.append('disk0-part=SWAP 0 none\n')
        InstallationData.zfs_config_data.append('commitDiskLabel\n')

    @classmethod
    def _is_ready(cls):
        """
        Check if all conditions are met to proceed to the next page.

        Returns:
            bool: True if disk count, swap entry, and encryption requirements are all satisfied.
        """
        count = len(cls.zfs_disk_list)
        if cls.mirror == "stripe":
            disks_ok = count >= 1
        elif cls.mirror == "mirror":
            disks_ok = count >= 2
        elif cls.mirror == "raidz1":
            disks_ok = count == 3
        elif cls.mirror == "raidz2":
            disks_ok = count == 4
        elif cls.mirror == "raidz3":
            disks_ok = count == 5
        else:
            disks_ok = False
        if cls.disk_encrypt:
            encrypt_ok = (cls.password.get_text() == cls.repassword.get_text()
                          and len(cls.password.get_text()) > 0)
        else:
            encrypt_ok = True
        return disks_ok and encrypt_ok

    @classmethod
    def scheme_selection(cls, combobox):
        """
        Handle partition scheme selection from combo box.

        Args:
            combobox: ComboBox widget containing scheme options (GPT/MBR)
        """
        model = combobox.get_model()
        index = combobox.get_active()
        data = model[index][0]
        cls.scheme = data.partition(':')[0]

    @classmethod
    def mirror_selection(cls, combobox):
        """
        Handle pool type selection and update UI accordingly.

        Sets the pool type (stripe, mirror, RAIDZ1/2/3) and updates the tip text
        and next button sensitivity based on the number of selected disks.

        Args:
            combobox: ComboBox widget containing pool type options
        """
        model = combobox.get_model()
        index = combobox.get_active()
        data = model[index][0]
        cls.mirror = data
        smallest_msg = get_text("(select the smallest disk first)")
        if cls.mirror == "stripe":
            cls.pool_type = 'stripe'
            cls.mirrorTips.set_text(
                get_text("Select 1 or more drives, no redundancy") + " " + smallest_msg)
        elif cls.mirror == "mirror":
            cls.pool_type = 'mirror'
            cls.mirrorTips.set_text(
                get_text("Select 2 or more drives for mirroring") + " " + smallest_msg)
        elif cls.mirror == "raidz1":
            cls.pool_type = 'raidz1'
            cls.mirrorTips.set_text(
                get_text("Select 3 drives for RAIDZ1") + " " + smallest_msg)
        elif cls.mirror == "raidz2":
            cls.pool_type = 'raidz2'
            cls.mirrorTips.set_text(
                get_text("Select 4 drives for RAIDZ2") + " " + smallest_msg)
        elif cls.mirror == "raidz3":
            cls.pool_type = 'raidz3'
            cls.mirrorTips.set_text(
                get_text("Select 5 drives for RAIDZ3") + " " + smallest_msg)
        Button.next_button.set_sensitive(cls._is_ready())

    @classmethod
    def on_check_encrypt(cls, widget):
        """
        Handle disk encryption checkbox toggle.

        Enables or disables password fields and updates next button sensitivity
        based on encryption state and current disk selection.

        Args:
            widget: CheckButton widget for disk encryption enable/disable
        """
        if widget.get_active():
            cls.password.set_sensitive(True)
            cls.repassword.set_sensitive(True)
            cls.disk_encrypt = True
            Button.next_button.set_sensitive(False)
        else:
            cls.password.set_sensitive(False)
            cls.repassword.set_sensitive(False)
            cls.disk_encrypt = False
            Button.next_button.set_sensitive(cls._is_ready())

    @classmethod
    def on_password_changed(cls, _widget):
        """
        Handle password entry changes and update strength display.

        Wraps the common password_strength function to extract the text
        from the Entry widget and pass it with the strength label.

        Args:
            _widget: Entry widget that triggered the change (unused)
        """
        password_strength(cls.password.get_text(), cls.strenght_label)
        Button.next_button.set_sensitive(cls._is_ready())

    @classmethod
    def initialize(cls):
        """
        Initialize the ZFS configuration UI following the utility class pattern.
        
        Creates the main interface including:
        - Disk selection tree view with checkboxes
        - Pool type selection (stripe, mirror, RAIDZ1/2/3)
        - Pool name configuration
        - Partition scheme selection (GPT/MBR)
        - Disk encryption options with password fields
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()

        # Disk list in a scrolled window
        sw = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        cls.store = Gtk.TreeStore(str, str, str, 'gboolean')
        for disk in zfs_disk_query():
            dsk = disk.partition(':')[0].rstrip()
            dsk_name = disk.partition(':')[2].rstrip()
            dsk_size = zfs_disk_size_query(dsk).rstrip()
            cls.store.append(None, [dsk, dsk_size, dsk_name, False])
        treeview = Gtk.TreeView()
        treeview.set_model(cls.store)
        treeview.set_rules_hint(True)
        cls.check_cell = Gtk.CellRendererToggle()
        cls.check_cell.set_property('activatable', True)
        cls.check_cell.connect('toggled', cls.col1_toggled_cb, cls.store)
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        column_header = Gtk.Label(label=get_text('Disk'))
        column_header.set_use_markup(True)
        column_header.show()
        column.set_widget(column_header)
        column.set_sort_column_id(0)
        cell2 = Gtk.CellRendererText()
        column2 = Gtk.TreeViewColumn(None, cell2, text=0)
        column_header2 = Gtk.Label(label=get_text('Size(MB)'))
        column_header2.set_use_markup(True)
        column_header2.show()
        column2.set_widget(column_header2)
        cell3 = Gtk.CellRendererText()
        column3 = Gtk.TreeViewColumn(None, cell3, text=0)
        column_header3 = Gtk.Label(label=get_text('Name'))
        column_header3.set_use_markup(True)
        column_header3.show()
        column3.set_widget(column_header3)
        column1 = Gtk.TreeViewColumn(get_text("Check"), cls.check_cell)
        column1.add_attribute(cls.check_cell, "active", 3)
        column.set_attributes(cell, text=0)
        column2.set_attributes(cell2, text=1)
        column3.set_attributes(cell3, text=2)
        treeview.append_column(column1)
        treeview.append_column(column)
        treeview.append_column(column2)
        treeview.append_column(column3)
        tree_selection = treeview.get_selection()
        tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        sw.add(treeview)
        sw.show()

        cls.mirrorTips = Gtk.Label(label=get_text('Please select one drive'))
        cls.mirrorTips.set_justify(Gtk.Justification.LEFT)
        cls.mirrorTips.set_alignment(0.01, 0.5)

        # Pool Layout
        cls.mirror = 'stripe'
        mirror_label = Gtk.Label(label=get_text('Pool Layout'))
        mirror_label.set_use_markup(True)
        mirror_box = Gtk.ComboBoxText()
        mirror_box.append_text("stripe")
        mirror_box.append_text("mirror")
        mirror_box.append_text("raidz1")
        mirror_box.append_text("raidz2")
        mirror_box.append_text("raidz3")
        mirror_box.set_active(0)
        mirror_box.connect('changed', cls.mirror_selection)

        # Pool Name (always editable)
        pool_label = Gtk.Label(label=get_text('Pool Name'))
        pool_label.set_use_markup(True)
        cls.pool = Gtk.Entry()
        cls.pool.set_text('zroot')

        # Swap Size
        swap_label = Gtk.Label(label=get_text('Swap Size(MB)'))
        swap_label.set_use_markup(True)
        ram_mb = get_ram_size_mb()
        adj = Gtk.Adjustment(ram_mb, 0, ram_mb, 1, 100, 0)
        cls.swap_entry = Gtk.SpinButton(adjustment=adj, numeric=True)
        cls.swap_entry.set_editable(True)

        # Creating MBR or GPT drive
        cls.scheme = 'GPT'
        shemebox = Gtk.ComboBoxText()
        shemebox.append_text("GPT")
        shemebox.append_text("MBR")
        shemebox.connect('changed', cls.scheme_selection)
        shemebox.set_active(0)
        if bios_or_uefi() == "UEFI":
            shemebox.set_sensitive(False)
        else:
            shemebox.set_sensitive(True)

        # GELI Disk encryption
        cls.disk_encrypt = False
        encrypt_check = Gtk.CheckButton(label=get_text("Encrypt Disk (GELI)"))
        encrypt_check.connect("toggled", cls.on_check_encrypt)
        encrypt_check.set_sensitive(True)

        # Password
        cls.passwd_label = Gtk.Label(label=get_text("Password"))
        cls.password = Gtk.Entry()
        cls.password.set_sensitive(False)
        cls.password.set_visibility(False)
        cls.password.connect("changed", cls.on_password_changed)
        cls.strenght_label = Gtk.Label()
        cls.strenght_label.set_alignment(0.1, 0.5)
        cls.strenght_label.set_size_request(-1, 20)

        # Verify password
        cls.vpasswd_label = Gtk.Label(label=get_text("Confirm"))
        cls.repassword = Gtk.Entry()
        cls.repassword.set_sensitive(False)
        cls.repassword.set_visibility(False)
        cls.repassword.connect("changed", cls.password_verification)

        # Password match image
        cls.img = Gtk.Image()
        cls.img.set_size_request(20, 20)

        # Two-column layout: left settings, right disk list
        hbox_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)

        # Left panel: settings grid
        left_grid = Gtk.Grid()
        left_grid.set_row_spacing(4)
        left_grid.set_column_spacing(6)
        left_grid.set_hexpand(False)

        mirror_label.set_alignment(0, 0.5)
        pool_label.set_alignment(0, 0.5)
        swap_label.set_alignment(0, 0.5)
        cls.passwd_label.set_alignment(0, 0.5)
        cls.vpasswd_label.set_alignment(0, 0.5)

        # Row 0-1: Pool Layout
        left_grid.attach(mirror_label, 0, 0, 2, 1)
        left_grid.attach(mirror_box, 0, 1, 2, 1)
        # Row 2-3: Pool Name
        left_grid.attach(pool_label, 0, 2, 2, 1)
        left_grid.attach(cls.pool, 0, 3, 2, 1)
        # Row 4-5: Swap Size
        left_grid.attach(swap_label, 0, 4, 2, 1)
        left_grid.attach(cls.swap_entry, 0, 5, 2, 1)
        # Row 6: Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        left_grid.attach(sep, 0, 6, 2, 1)
        # Row 7: Encrypt Disk checkbox
        left_grid.attach(encrypt_check, 0, 7, 2, 1)
        # Row 8: Password label + strength indicator
        left_grid.attach(cls.passwd_label, 0, 8, 1, 1)
        left_grid.attach(cls.strenght_label, 1, 8, 1, 1)
        # Row 9: Password input
        left_grid.attach(cls.password, 0, 9, 2, 1)
        # Row 10: Confirm label + match icon
        left_grid.attach(cls.vpasswd_label, 0, 10, 1, 1)
        left_grid.attach(cls.img, 1, 10, 1, 1)
        # Row 11: Confirm input
        left_grid.attach(cls.repassword, 0, 11, 2, 1)

        hbox_main.pack_start(left_grid, False, False, 10)

        # Right panel: tips + disk list
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.mirrorTips.set_alignment(0, 0.5)
        right_panel.pack_start(cls.mirrorTips, False, False, 0)
        right_panel.pack_start(sw, True, True, 0)

        hbox_main.pack_start(right_panel, True, True, 10)

        cls.vbox1.pack_start(hbox_main, True, True, 10)
        return

    @classmethod
    def get_model(cls):
        """
        Return the GTK widget model for the ZFS configuration interface.
        
        Creates and initializes the UI if it doesn't exist yet.
        
        Returns:
            Gtk.Box: The main container widget for the ZFS configuration interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @classmethod
    def check_if_small_disk(cls, size):
        """
        Check if any selected disk is larger than the specified size.
        
        Used to enforce the requirement that the smallest disk must be selected first
        for ZFS pool configurations.
        
        Args:
            size: Size in MB to compare against selected disks
            
        Returns:
            bool: True if any selected disk is larger than the specified size
        """
        if len(cls.zfs_disk_list) != 0:
            for line in cls.zfs_disk_list:
                if int(line.partition('-')[2]) > int(size):
                    return True
                else:
                    return False
        else:
            return False

    @classmethod
    def col1_toggled_cb(cls, _cell, path, model):
        """
        Handle disk selection checkbox toggle events.
        
        Manages the disk selection list and updates next button sensitivity
        based on pool type requirements. Enforces the rule that the smallest
        disk must be selected first.
        
        Args:
            _cell: CellRendererToggle that was clicked (unused)
            path: TreePath of the toggled row
            model: TreeStore model containing disk data
            
        Returns:
            bool: Always returns True to indicate the event was handled
        """
        model[path][3] = not model[path][3]
        if model[path][3] is False:
            cls.zfs_disk_list.remove(model[path][0] + "-" + model[path][1])
        else:
            if cls.check_if_small_disk(model[path][1]) is False:
                cls.zfs_disk_list.extend([model[path][0] + "-" + model[path][1]])
            else:
                cls.check_cell.set_sensitive(False)
                cls.small_disk_warning()
                return True

        # Update swap SpinButton upper limit based on first selected disk
        if cls.zfs_disk_list:
            disk_size = int(cls.zfs_disk_list[0].partition('-')[2].rstrip()) - 512
            cls.swap_entry.get_adjustment().set_upper(disk_size)
        else:
            cls.swap_entry.get_adjustment().set_upper(get_ram_size_mb())
        Button.next_button.set_sensitive(cls._is_ready())

        print(cls.zfs_disk_list)
        return True

    @classmethod
    def small_disk_warning(cls):
        """
        Display a warning dialog when disks are selected out of size order.
        
        Shows a dialog informing the user that the smallest disk must be
        selected first and offers to reset all selections.
        """
        window = Gtk.Window()
        window.set_title(get_text("Warning"))
        window.set_border_width(0)
        # window.set_size_request(480, 200)
        window.set_icon_from_file(logo)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        warning_text = get_text("Smallest disk need to be SELECTED first!\n")
        warning_text += get_text("All the disk selected will reset.")
        label = Gtk.Label(label=warning_text)
        # Add button
        box2.pack_start(label, True, True, 0)
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        bbox.set_border_width(5)
        button = Gtk.Button(stock=Gtk.STOCK_OK)
        button.connect("clicked", cls.resset_selection, window)
        bbox.add(button)
        box2.pack_end(bbox, True, True, 5)
        window.show_all()

    @classmethod
    def resset_selection(cls, _widget, window):
        """
        Reset all disk selections and close the warning dialog.
        
        Clears the disk selection list and unchecks all checkboxes in the tree view.
        
        Args:
            _widget: Button widget that triggered the reset (unused)
            window: Warning dialog window to close
        """
        cls.zfs_disk_list = []
        rows = len(cls.store)
        for row in range(0, rows):
            cls.store[row][3] = False
            row += 1
        cls.check_cell.set_sensitive(True)
        window.hide()

    @classmethod
    def password_verification(cls, _widget):
        """
        Verify that password and confirmation password fields match.
        
        Updates the verification image and next button sensitivity based on
        password match status and current disk selection requirements.
        
        Args:
            _widget: Entry widget that triggered the verification (unused)
        """
        if cls.password.get_text() == cls.repassword.get_text():
            cls.img.set_from_icon_name("gtk-yes", Gtk.IconSize.MENU)
            Button.next_button.set_sensitive(cls._is_ready())
        else:
            cls.img.set_from_icon_name("gtk-no", Gtk.IconSize.MENU)
            Button.next_button.set_sensitive(False)
