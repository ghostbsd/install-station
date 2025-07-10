from gi.repository import Gtk, Gdk
import gettext
from install_station.common import password_strength
from install_station.data import InstallationData, zfs_datasets, be_name, logo
from install_station.partition import bios_or_uefi
from install_station.system_calls import (
    zfs_disk_query,
    zfs_disk_size_query,
)
from install_station.interface_controller import Button

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
    zpool = False
    disk_encrypt = False
    mirror = 'single disk'
    vbox1 = None
    
    # UI elements as class variables
    pool = None
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
            
        if cls.zpool and not cls.pool.get_text().strip():
            raise ValueError("Pool name cannot be empty when zpool is enabled")
            
        if cls.disk_encrypt and not cls.password.get_text().strip():
            raise ValueError("Password cannot be empty when disk encryption is enabled")
            
        size = int(cls.zfs_disk_list[0].partition('-')[2].rstrip()) - 512
        swap = 0
        zfs_num = size - swap
        if cls.disk_encrypt is True:
            dgeli = '.eli'
        else:
            dgeli = ''

        # Store configuration data in InstallationData instead of writing to file
        InstallationData.zfs_config_data = []
        
        if cls.zpool is True:
            InstallationData.zfs_config_data.append(f"zpoolName={cls.pool.get_text()}\n")
        else:
            InstallationData.zfs_config_data.append("#zpoolName=None\n")
        InstallationData.zfs_config_data.append(f"beName={be_name}\n")
        InstallationData.zfs_config_data.append('ashift=12\n\n')
        disk = cls.zfs_disk_list[0].partition('-')[0].rstrip()
        InstallationData.zfs_config_data.append(f'disk0={disk}\n')
        InstallationData.zfs_config_data.append('partition=ALL\n')
        InstallationData.zfs_config_data.append(f'partscheme={cls.scheme}\n')
        InstallationData.zfs_config_data.append('commitDiskPart\n\n')
        if cls.pool_type == 'none':
            pool_disk = '\n'
        else:
            zfs_disk = cls.zfs_disk_list
            disk_len = len(zfs_disk) - 1
            num = 1
            mirror_dsk = ''
            while disk_len != 0:
                mirror_dsk += ' ' + zfs_disk[num].partition('-')[0].rstrip()
                print(mirror_dsk)
                num += 1
                disk_len -= 1
            pool_disk = f' ({cls.pool_type}:{mirror_dsk})\n'
        if bios_or_uefi() == "UEFI":
            zfs_num = zfs_num - 100
        else:
            zfs_num = zfs_num - 1
        # adding zero to use remaining space
        zfs_part = f'disk0-part=ZFS{dgeli} {zfs_num} {zfs_datasets}{pool_disk}'
        InstallationData.zfs_config_data.append(zfs_part)
        if swap != 0:
            InstallationData.zfs_config_data.append('disk0-part=swap 0 none\n')
        if cls.disk_encrypt is True:
            InstallationData.zfs_config_data.append(f'encpass={cls.password.get_text()}\n')
        else:
            InstallationData.zfs_config_data.append('#encpass=None\n')
        InstallationData.zfs_config_data.append('commitDiskLabel\n')

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
        data = model[index][0]  # Get the internal value (English)
        cls.mirror = data
        if cls.mirror == "1+ disks Stripe":
            cls.pool_type = 'stripe'
            cls.mirrorTips.set_text(
                _("Please select 1 or more drive for stripe (select the smallest disk first)"))
            if len(cls.zfs_disk_list) >= 1:
                Button.next_button.set_sensitive(True)
            else:
                Button.next_button.set_sensitive(False)
        elif cls.mirror == "2+ disks Mirror":
            cls.pool_type = 'mirror'
            mir_msg1 = _("Please select 2 drive for mirroring (select the smallest disk first)")
            cls.mirrorTips.set_text(mir_msg1)
            if len(cls.zfs_disk_list) >= 2:
                Button.next_button.set_sensitive(True)
            else:
                Button.next_button.set_sensitive(False)
        elif cls.mirror == "3 disks RAIDZ1":
            cls.pool_type = 'raidz1'
            cls.mirrorTips.set_text(_("Please select 3 drive for RAIDZ1 (select the smallest disk first)"))
            if len(cls.zfs_disk_list) == 3:
                Button.next_button.set_sensitive(True)
            else:
                Button.next_button.set_sensitive(False)
        elif cls.mirror == "4 disks RAIDZ2":
            cls.pool_type = 'raidz2'
            cls.mirrorTips.set_text(_("Please select 4 drive for RAIDZ2 (select the smallest disk first)"))
            if len(cls.zfs_disk_list) == 4:
                Button.next_button.set_sensitive(True)
            else:
                Button.next_button.set_sensitive(False)
        elif cls.mirror == "5 disks RAIDZ3":
            cls.pool_type = 'raidz3'
            cls.mirrorTips.set_text(_("Please select 5 drive for RAIDZ3 (select the smallest disk first)"))
            if len(cls.zfs_disk_list) == 5:
                Button.next_button.set_sensitive(True)
            else:
                Button.next_button.set_sensitive(False)

    @classmethod
    def on_check_poll(cls, widget):
        """
        Handle custom pool name checkbox toggle.
        
        Enables or disables the pool name entry field based on checkbox state.
        
        Args:
            widget: CheckButton widget for pool name enable/disable
        """
        if widget.get_active():
            cls.pool.set_sensitive(True)
            cls.zpool = True
        else:
            cls.pool.set_sensitive(False)
            cls.zpool = False

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
            if cls.mirror == "1+ disks Stripe":
                if len(cls.zfs_disk_list) >= 1:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "2+ disks Mirror":
                if len(cls.zfs_disk_list) >= 2:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "3 disks RAIDZ1":
                if len(cls.zfs_disk_list) == 3:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "4 disks RAIDZ2":
                if len(cls.zfs_disk_list) == 4:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "5 disks RAIDZ3":
                if len(cls.zfs_disk_list) == 5:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)

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
        # Chose disk
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
        column_header = Gtk.Label(label=_('Disk'))
        column_header.set_use_markup(True)
        column_header.show()
        column.set_widget(column_header)
        column.set_sort_column_id(0)
        cell2 = Gtk.CellRendererText()
        column2 = Gtk.TreeViewColumn(None, cell2, text=0)
        column_header2 = Gtk.Label(label=_('Size(MB)'))
        column_header2.set_use_markup(True)
        column_header2.show()
        column2.set_widget(column_header2)
        cell3 = Gtk.CellRendererText()
        column3 = Gtk.TreeViewColumn(None, cell3, text=0)
        column_header3 = Gtk.Label(label=_('Name'))
        column_header3.set_use_markup(True)
        column_header3.show()
        column3.set_widget(column_header3)
        column1 = Gtk.TreeViewColumn(_("Check"), cls.check_cell)
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
        cls.mirrorTips = Gtk.Label(label=_('Please select one drive'))
        cls.mirrorTips.set_justify(Gtk.Justification.LEFT)
        cls.mirrorTips.set_alignment(0.01, 0.5)
        # Mirror, raidz and stripe
        cls.mirror = 'none'
        mirror_label = Gtk.Label(label=_('<b>Pool Type</b>'))
        mirror_label.set_use_markup(True)
        mirror_box = Gtk.ComboBox()
        mirror_store = Gtk.ListStore(str, str)  # value, display_text
        mirror_store.append(["1+ disks Stripe", _("1+ disks Stripe")])
        mirror_store.append(["2+ disks Mirror", _("2+ disks Mirror")])
        mirror_store.append(["3 disks RAIDZ1", _("3 disks RAIDZ1")])
        mirror_store.append(["4 disks RAIDZ2", _("4 disks RAIDZ2")])
        mirror_store.append(["5 disks RAIDZ3", _("5 disks RAIDZ3")])
        mirror_box.set_model(mirror_store)
        renderer = Gtk.CellRendererText()
        mirror_box.pack_start(renderer, True)
        mirror_box.add_attribute(renderer, "text", 1)  # Display column 1 (translated text)
        mirror_box.connect('changed', cls.mirror_selection)
        mirror_box.set_active(0)

        # Pool Name
        cls.zpool = False
        pool_name_label = Gtk.Label(label=_('<b>Pool Name</b>'))
        pool_name_label.set_use_markup(True)
        cls.pool = Gtk.Entry()
        cls.pool.set_text('zroot')
        # Creating MBR or GPT drive
        scheme_label = Gtk.Label(label='<b>Partition Scheme</b>')
        scheme_label.set_use_markup(True)
        # Adding a combo box to selecting MBR or GPT sheme.
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
        encrypt_check = Gtk.CheckButton(label=_("Encrypt Disk"))
        encrypt_check.connect("toggled", cls.on_check_encrypt)
        encrypt_check.set_sensitive(True)
        # password
        cls.passwd_label = Gtk.Label(label=_("Password"))
        cls.password = Gtk.Entry()
        cls.password.set_sensitive(False)
        cls.password.set_visibility(False)
        cls.password.connect("changed", password_strength)
        cls.strenght_label = Gtk.Label()
        cls.strenght_label.set_alignment(0.1, 0.5)
        cls.vpasswd_label = Gtk.Label(label=_("Verify it"))
        cls.repassword = Gtk.Entry()
        cls.repassword.set_sensitive(False)
        cls.repassword.set_visibility(False)
        cls.repassword.connect("changed", cls.password_verification)
        # set image for password matching
        cls.img = Gtk.Image()
        cls.img.set_alignment(0.2, 0.5)
        # table = Gtk.Table(12, 12, True)
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        # grid.set_column_homogeneous(True)
        # grid.set_row_homogeneous(True)
        # grid.attach(Title, 1, 1, 10, 1)
        grid.attach(mirror_label, 1, 2, 1, 1)
        grid.attach(mirror_box, 2, 2, 1, 1)
        grid.attach(pool_name_label, 7, 2, 2, 1)
        grid.attach(cls.pool, 9, 2, 2, 1)
        grid.attach(cls.mirrorTips, 1, 3, 8, 1)
        # grid.attach(zfs4kcheck, 9, 3, 2, 1)
        grid.attach(sw, 1, 4, 10, 3)
        # grid.attach(scheme_label, 1, 9, 1, 1)
        # grid.attach(shemebox, 2, 9, 1, 1)
        # grid.attach(cls.swap_encrypt_check, 9, 15, 11, 12)
        # grid.attach(swap_mirror_check, 9, 15, 11, 12)
        # grid.attach(encrypt_check, 2, 8, 2, 1)
        # grid.attach(cls.passwd_label, 1, 9, 1, 1)
        # grid.attach(cls.password, 2, 9, 2, 1)
        # grid.attach(cls.strenght_label, 4, 9, 2, 1)
        # grid.attach(cls.vpasswd_label, 1, 10, 1, 1)
        # grid.attach(cls.repassword, 2, 10, 2, 1)
        # grid.attach(cls.img, 4, 10, 2, 1)
        cls.vbox1.pack_start(grid, True, True, 10)
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
            if cls.mirror == "1+ disks Stripe":
                if len(cls.zfs_disk_list) >= 1:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "2+ disks Mirror":
                if len(cls.zfs_disk_list) >= 2:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "3 disks RAIDZ1":
                if len(cls.zfs_disk_list) == 3:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "4 disks RAIDZ2":
                if len(cls.zfs_disk_list) == 4:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "5 disks RAIDZ3":
                if len(cls.zfs_disk_list) == 5:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
        else:
            if cls.check_if_small_disk(model[path][1]) is False:
                cls.zfs_disk_list.extend([model[path][0] + "-" + model[path][1]])
                if cls.mirror == "1+ disks Stripe":
                    if len(cls.zfs_disk_list) >= 1:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                elif cls.mirror == "2+ disks Mirror":
                    if len(cls.zfs_disk_list) >= 2:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                elif cls.mirror == "3 disks RAIDZ1":
                    if len(cls.zfs_disk_list) == 3:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                elif cls.mirror == "4 disks RAIDZ2":
                    if len(cls.zfs_disk_list) == 4:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                elif cls.mirror == "5 disks RAIDZ3":
                    if len(cls.zfs_disk_list) == 5:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
            else:
                cls.check_cell.set_sensitive(False)
                cls.small_disk_warning()

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
        window.set_title(_("Warning"))
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
        warning_text = _("Smallest disk need to be SELECTED first!\n")
        warning_text += _("All the disk selected will reset.")
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
            cls.img.set_from_stock(Gtk.STOCK_YES, 5)
            if cls.mirror == "1+ disks Stripe":
                if len(cls.zfs_disk_list) >= 1:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "2+ disks Mirror":
                if len(cls.zfs_disk_list) >= 2:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "3 disks RAIDZ1":
                if len(cls.zfs_disk_list) == 3:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "4 disks RAIDZ2":
                if len(cls.zfs_disk_list) == 4:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif cls.mirror == "5 disks RAIDZ3":
                if len(cls.zfs_disk_list) == 5:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
        else:
            cls.img.set_from_stock(Gtk.STOCK_NO, 5)
            Button.next_button.set_sensitive(False)
