import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk
from install_station.partition import (
    DiskPartition,
    DeletePartition,
    bios_or_uefi,
    CreateSlice,
    AutoFreeSpace,
    CreatePartition,
    CreateLabel
)
from install_station.data import InstallationData, logo
from install_station.interface_controller import Button
import gettext

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext

bios_type = bios_or_uefi()

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class PartitionManager:
    """
    Utility class for partition management operations following the pattern of InstallTypes and ZFS.
    
    This class provides a GTK+ interface for managing disk partitions including creating,
    deleting, and configuring partitions with support for both GPT and MBR schemes.
    Supports ZFS, UFS, SWAP, BOOT, and UEFI filesystem types.
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the InstallationData system for configuration persistence.
    """
    # Class variables for state management
    fs = None
    mount_point = None
    window = None
    efi_exist = True
    fs_behind = None
    disk_index = None
    path = None
    disk = None
    vbox1 = None
    scheme = 'GPT'
    size = None
    slice = None
    label = None
    mount_point_behind = None
    change_schemes = False
    iter = None
    store = None
    treeview = None
    tree_selection = None
    
    # UI elements as class variables
    create_bt = None
    delete_bt = None
    revert_bt = None
    auto_bt = None
    fs_type = None
    entry = None
    mount_point_box = None

    @classmethod
    def set_fs(cls, widget):
        """
        Set the filesystem type from a ComboBoxText widget selection.
        
        Args:
            widget: GTK ComboBoxText widget containing filesystem type options
        """
        cls.fs = widget.get_active_text()

    @classmethod
    def get_mount_point(cls, widget):
        """
        Get the mount point from a ComboBoxText widget selection.
        
        Args:
            widget: GTK ComboBoxText widget containing mount point options
        """
        cls.mount_point = widget.get_active_text()

    @classmethod
    def get_model(cls):
        """
        Return the GTK widget model for the partition manager.
        
        Creates and initializes the UI if it doesn't exist yet.
        
        Returns:
            Gtk.Box: The main container widget for the partition manager interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @classmethod
    def initialize(cls):
        """
        Initialize the partition manager UI following the utility class pattern.
        
        Creates the main interface including the partition tree view, control buttons,
        and sets up the partition database. This method is called automatically
        by get_model() when the interface is first accessed.
        """
        DiskPartition.create_partition_database()
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        
        # Scrolled window for partition tree
        sw = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        cls.store = Gtk.TreeStore(str, str, str, str, bool)
        cls.tree_store()
        cls.treeview = Gtk.TreeView()
        cls.treeview.set_model(cls.store)
        cls.treeview.set_rules_hint(True)
        
        # Setup columns
        cls._setup_columns()
        
        cls.treeview.set_reorderable(True)
        cls.treeview.expand_all()
        cls.tree_selection = cls.treeview.get_selection()
        cls.tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        cls.tree_selection.connect("changed", cls.partition_selection)
        sw.add(cls.treeview)
        sw.show()
        cls.vbox1.pack_start(sw, True, True, 0)
        
        # Button box
        hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=0)
        hbox1.set_border_width(10)
        cls.vbox1.pack_start(hbox1, False, False, 0)
        hbox1.show()
        cls.scheme = 'GPT'
        hbox1.pack_start(cls.delete_create_button(), False, False, 10)

    @classmethod
    def _setup_columns(cls):
        """
        Setup treeview columns for the partition display.
        
        Creates columns for Partition, Size(MB), Mount Point, and System/Type
        with appropriate widths and header labels.
        """
        columns_config = [
            ('Partition', 0, 150),
            ('Size(MB)', 1, 150), 
            ('Mount Point', 2, 150),
            ('System/Type', 3, 150)
        ]
        
        for i, (title, text_col, width) in enumerate(columns_config):
            cell = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(None, cell, text=text_col)
            column_header = Gtk.Label(label=title)
            column_header.set_use_markup(True)
            column_header.show()
            column.set_widget(column_header)
            column.set_resizable(True)
            column.set_fixed_width(width)
            if i == 0:
                column.set_sort_column_id(0)
            cls.treeview.append_column(column)

    @classmethod
    def tree_store(cls):
        """
        Populate the tree store with disk and partition information from the disk database.
        
        Creates a hierarchical tree structure showing:
        - Disks (top level)
        - Partitions/slices (second level) 
        - Labels/partitions (third level)
        
        Each level displays relevant information like size, mount points, and filesystem types.
        
        Returns:
            Gtk.TreeStore: The populated tree store model
        """
        cls.store.clear()
        disk_db = DiskPartition.get_disk_database()
        cls.disk_index = list(disk_db.keys())
        for disk in disk_db:
            disk_info = disk_db[disk]
            disk_scheme = disk_info['scheme']
            mount_point = ''
            disk_size = str(disk_info['size'])
            disk_partitions = disk_info['partitions']
            partition_list = disk_info['partition-list']
            pinter1 = cls.store.append(None, [disk, disk_size, mount_point,
                                       disk_scheme, True])
            for partition in partition_list:
                partition_info = disk_partitions[partition]
                file_system = partition_info['file-system']
                mount_point = partition_info['mount-point']
                partition_size = str(partition_info['size'])
                partition_partitions = partition_info['partitions']
                label_list = partition_info['partition-list']
                pinter2 = cls.store.append(pinter1, [partition, partition_size, mount_point, file_system, True])
                for label in label_list:
                    label_info = partition_partitions[label]
                    file_system = label_info['file-system']
                    label_mount_point = label_info['mount-point']
                    label_size = str(label_info['size'])
                    cls.store.append(pinter2, [label, label_size, label_mount_point, file_system, True])
        return cls.store

    @classmethod
    def update(cls):
        """
        Update the treeview after partition operations.
        
        Refreshes the partition tree display, expands all rows, and attempts
        to restore the previously selected row if it still exists.
        """
        old_path = cls.path
        cls.tree_store()
        cls.treeview.expand_all()
        if old_path:
            cls.treeview.row_activated(old_path, cls.treeview.get_columns()[0])
            cls.treeview.set_cursor(old_path)

    @classmethod
    def delete_create_button(cls):
        """
        Create the button toolbar for partition operations.
        
        Creates a horizontal box containing Create, Delete, Revert, and Auto buttons
        for partition management operations.
        
        Returns:
            Gtk.Box: Container with partition operation buttons
        """
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True, spacing=10)
        bbox.set_border_width(5)
        bbox.set_spacing(10)
        cls.create_bt = Gtk.Button(label="Create")
        cls.create_bt.connect("clicked", cls.create_partition)
        cls.create_bt.set_sensitive(False)
        bbox.pack_start(cls.create_bt, True, True, 0)
        cls.delete_bt = Gtk.Button(label="Delete")
        cls.delete_bt.connect("clicked", cls.delete_partition)
        cls.delete_bt.set_sensitive(False)
        bbox.pack_start(cls.delete_bt, True, True, 0)
        cls.revert_bt = Gtk.Button(label="Revert")
        cls.revert_bt.connect("clicked", cls.revert_change)
        cls.revert_bt.set_sensitive(False)
        bbox.pack_start(cls.revert_bt, True, True, 0)
        cls.auto_bt = Gtk.Button(label="Auto")
        cls.auto_bt.connect("clicked", cls.auto_partition)
        cls.auto_bt.set_sensitive(False)
        bbox.pack_start(cls.auto_bt, True, True, 0)
        return bbox

    @classmethod
    def on_add_label(cls, _widget, entry, free_space, path):
        """
        Handle adding a new label/partition in MBR scheme.
        
        Args:
            _widget: The button widget (unused)
            entry: SpinButton containing the partition size
            free_space: Available space in MB
            path: TreePath indicating the parent location
        """
        create_size = entry.get_value_as_int()
        left_size = free_space - create_size
        CreateLabel(path, cls.disk, cls.slice, left_size, create_size,
                    cls.mount_point, cls.fs)
        cls.window.hide()
        cls.update()

    @classmethod
    def on_add_partition(cls, _widget, entry, free_space, path):
        """
        Handle adding a new partition in GPT scheme.
        
        Args:
            _widget: The button widget (unused)
            entry: SpinButton containing the partition size
            free_space: Available space in MB
            path: TreePath indicating the parent location
        """
        create_size = entry.get_value_as_int()
        left_size = int(free_space - create_size)
        CreatePartition(path, cls.disk, left_size, create_size,
                        cls.mount_point, cls.fs)
        cls.window.hide()
        cls.update()

    @classmethod
    def cancel(cls, _widget):
        """
        Cancel the current partition operation and close the dialog.
        
        Args:
            _widget: The cancel button widget (unused)
        """
        cls.window.hide()
        cls.update()

    @classmethod
    def label_editor(cls, path, size, scheme):
        """
        Open the partition/label editor dialog.
        
        Creates a dialog window for configuring a new partition with options for
        filesystem type, size, and mount point based on the partitioning scheme.
        
        Args:
            path: TreePath indicating where to create the partition
            size: Available free space in MB
            scheme: Partitioning scheme ('GPT' or 'MBR')
        """
        free_space = int(size)
        cls.window = Gtk.Window()
        cls.window.set_title(title="Add Partition")
        cls.window.set_border_width(0)
        cls.window.set_size_request(480, 200)
        cls.window.set_icon_from_file(logo)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        
        # Create partition configuration table
        table = Gtk.Table(1, 2, True)
        label1 = Gtk.Label(label="Type:")
        label2 = Gtk.Label(label="Size(MB):")
        label3 = Gtk.Label(label="Mount point:")
        cls.fs_type = Gtk.ComboBoxText()
        cls.fs_type.append_text('ZFS')
        cls.fs_type.append_text('SWAP')
        cls.fs_type.append_text('UFS')  # Add UFS option
        
        # Set filesystem options based on scheme and existing partitions
        if scheme == 'GPT':
            if bios_type == "UEFI":
                cls.fs_type.append_text("UEFI")
                if cls.efi_exist is False:
                    cls.fs_type.set_active(3)  # UEFI
                    cls.fs = "UEFI"
                elif cls.mount_point_behind == "/" or cls.fs_behind == "ZFS":
                    cls.fs_type.set_active(1)  # SWAP
                    cls.fs = "SWAP"
                else:
                    cls.fs_type.set_active(0)  # ZFS
                    cls.fs = "ZFS"
            else:
                cls.fs_type.append_text("BOOT")
                if not InstallationData.new_partition:
                    cls.fs_type.set_active(4)  # BOOT
                    cls.fs = "BOOT"
                elif len(InstallationData.new_partition) == 0:
                    cls.fs_type.set_active(4)  # BOOT
                    cls.fs = "BOOT"
                elif cls.mount_point_behind == "/" or cls.fs_behind == "ZFS":
                    cls.fs_type.set_active(1)  # SWAP
                    cls.fs = "SWAP"
                else:
                    cls.fs_type.set_active(0)  # ZFS
                    cls.fs = "ZFS"
        elif cls.mount_point_behind == "/" or cls.fs_behind == "ZFS":
            cls.fs_type.set_active(1)  # SWAP
            cls.fs = "SWAP"
        else:
            cls.fs_type.set_active(0)  # ZFS
            cls.fs = "ZFS"
        
        cls.fs_type.connect("changed", cls.set_fs)
        
        # Size spinner
        adj = Gtk.Adjustment(free_space, 0, free_space, 1, 100, 0)
        cls.entry = Gtk.SpinButton(adjustment=adj, numeric=True)
        cls.entry.set_editable(True)
        
        # Mount point selection
        cls.mount_point_box = Gtk.ComboBoxText()
        cls.mount_point = "none"
        cls.mount_point_box.append_text('none')
        cls.mount_point_box.append_text('/')
        if InstallationData.new_partition:
            if scheme == 'GPT' and len(InstallationData.new_partition) == 1:
                cls.mount_point_box.append_text('/boot')
            elif scheme == 'MBR' and len(InstallationData.new_partition) == 0:
                cls.mount_point_box.append_text('/boot')
        elif scheme == 'MBR' and not InstallationData.new_partition:
            cls.mount_point_box.append_text('/boot')
        cls.mount_point_box.append_text('/etc')
        cls.mount_point_box.append_text('/root')
        cls.mount_point_box.append_text('/tmp')
        cls.mount_point_box.append_text('/usr')
        cls.mount_point_box.append_text('/home')
        cls.mount_point_box.append_text('/var')
        cls.mount_point_box.set_active(0)
        
        # Enable mount point selection for UFS
        if 'UFS' in cls.fs:
            cls.mount_point_box.set_sensitive(True)
        else:
            cls.mount_point_box.set_sensitive(False)
        cls.mount_point_box.connect("changed", cls.get_mount_point)
        
        # Add to table
        table.attach(label1, 0, 1, 1, 2)
        table.attach(cls.fs_type, 1, 2, 1, 2)
        table.attach(label2, 0, 1, 2, 3)
        table.attach(cls.entry, 1, 2, 2, 3)
        table.attach(label3, 0, 1, 3, 4)
        table.attach(cls.mount_point_box, 1, 2, 3, 4)
        box2.pack_start(table, False, False, 0)
        
        # Buttons
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True, spacing=10)
        bbox.set_border_width(5)
        bbox.set_spacing(10)
        
        button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        button.connect("clicked", cls.cancel)
        bbox.pack_start(button, True, True, 0)
        
        button = Gtk.Button(stock=Gtk.STOCK_ADD)
        if scheme == 'MBR':
            button.connect(
                "clicked", cls.on_add_label, cls.entry, free_space, path
            )
        elif scheme == 'GPT' and cls.fs == 'BOOT':
            button.connect(
                "clicked", cls.on_add_partition, cls.entry, free_space, path
            )
        elif scheme == 'GPT' and cls.fs == 'UEFI' and cls.efi_exist is False:
            button.connect(
                "clicked", cls.on_add_partition, cls.entry, free_space, path
            )
        else:
            button.connect(
                "clicked", cls.on_add_partition, cls.entry, free_space, path
            )
        bbox.pack_start(button, True, True, 0)
        box2.pack_end(bbox, True, True, 5)
        cls.window.show_all()

    @classmethod
    def scheme_selection(cls, combobox):
        """
        Handle partition scheme selection from combo box.
        
        Args:
            combobox: ComboBox widget containing scheme options
        """
        model = combobox.get_model()
        index = combobox.get_active()
        data = model[index][0]
        value = data.partition(':')[0]
        cls.scheme = value

    @classmethod
    def add_gpt_mbr(cls, _widget):
        """
        Apply the selected partition scheme to the disk.
        
        Args:
            _widget: The add button widget (unused)
        """
        DiskPartition.set_disk_scheme(cls.scheme, cls.disk, cls.size)
        cls.update()
        cls.window.hide()

    @classmethod
    def scheme_editor(cls):
        """
        Create a partition scheme editor window.
        
        Opens a dialog allowing the user to select between GPT and MBR
        partition schemes for the selected disk.
        """
        cls.window = Gtk.Window()
        cls.window.set_title("Partition Scheme")
        cls.window.set_border_width(0)
        cls.window.set_size_request(400, 150)
        cls.window.set_icon_from_file(logo)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        
        # Creating MBR or GPT drive
        label = Gtk.Label(label='<b>Select a partition scheme for this drive:</b>')
        label.set_use_markup(True)
        
        # Adding a combo box to selecting MBR or GPT scheme.
        cls.scheme = 'GPT'
        scheme_box = Gtk.ComboBoxText()
        scheme_box.append_text("GPT: GUID Partition Table")
        scheme_box.append_text("MBR: DOS Partition")
        scheme_box.connect('changed', cls.scheme_selection)
        scheme_box.set_active(0)
        table = Gtk.Table(1, 2, True)
        table.attach(label, 0, 2, 0, 1)
        table.attach(scheme_box, 0, 2, 1, 2)
        box2.pack_start(table, False, False, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        
        # Add create_scheme button
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True, spacing=10)
        bbox.set_border_width(5)
        bbox.set_spacing(10)
        button = Gtk.Button(stock=Gtk.STOCK_ADD)
        button.connect("clicked", cls.add_gpt_mbr)
        bbox.pack_start(button, True, True, 0)
        box2.pack_end(bbox, True, True, 5)
        cls.window.show_all()

    @classmethod
    def get_value(cls, _widget, entry):
        """
        Handle slice creation from the slice editor dialog.
        
        Gets the partition size from the entry widget and creates a new slice
        in the MBR partition table.
        
        Args:
            _widget: The add button widget (unused)
            entry: SpinButton containing the partition size
        """
        partition_size = int(entry.get_value_as_int())
        rs = int(cls.size) - partition_size
        CreateSlice(partition_size, rs, cls.path, cls.disk)
        cls.update()
        cls.window.hide()

    @classmethod
    def slice_editor(cls):
        """
        Create a window for editing partition slices in MBR scheme.
        
        Opens a dialog for creating a new slice partition with size configuration.
        Used specifically for MBR partitioning scheme.
        """
        free_space = int(cls.size)
        cls.window = Gtk.Window()
        cls.window.set_title("Add Partition")
        cls.window.set_border_width(0)
        cls.window.set_size_request(400, 150)
        cls.window.set_icon_from_file(logo)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        
        # Create Partition slice
        table = Gtk.Table(1, 2, True)
        label1 = Gtk.Label(label="Size(MB):")
        adj = Gtk.Adjustment(free_space, 0, free_space, 1, 100, 0)
        cls.entry = Gtk.SpinButton(adjustment=adj, numeric=True)
        cls.entry.set_numeric(True)
        table.attach(label1, 0, 1, 1, 2)
        table.attach(cls.entry, 1, 2, 1, 2)
        box2.pack_start(table, False, False, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        
        # Add button
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True, spacing=10)
        bbox.set_border_width(5)
        bbox.set_spacing(10)
        button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        button.connect("clicked", cls.cancel)
        bbox.pack_start(button, True, True, 0)
        button = Gtk.Button(stock=Gtk.STOCK_ADD)
        button.connect("clicked", cls.get_value, cls.entry)
        bbox.pack_start(button, True, True, 0)
        box2.pack_end(bbox, True, True, 5)
        cls.window.show_all()

    @classmethod
    def delete_partition(cls, _widget):
        """
        Delete the currently selected partition.
        
        Removes the selected partition or slice from the disk and updates
        the partition display.
        
        Args:
            _widget: The delete button widget (unused)
        """
        part = cls.slice if cls.label == "Not selected" else cls.label
        DeletePartition(part, cls.path)
        cls.update()

    @classmethod
    def auto_partition(cls, _widget):
        """
        Automatically partition the disk with default ZFS configuration.
        
        Creates automatic partitions suitable for ZFS installation including
        boot partitions (if needed) and ZFS root partition.
        
        Args:
            _widget: The auto button widget (unused)
        """
        cls.create_bt.set_sensitive(False)
        cls.delete_bt.set_sensitive(False)
        cls.auto_bt.set_sensitive(False)
        cls.revert_bt.set_sensitive(False)
        if 'freespace' in cls.slice:
            AutoFreeSpace(cls.path, cls.size, 'ZFS', cls.efi_exist,
                          cls.disk, cls.scheme)
            cls.update()
        else:
            print('wrong utilization')

    @classmethod
    def revert_change(cls, _widget):
        """
        Revert all partition changes and restore original state.
        
        Clears all partition configuration data from InstallationData and
        recreates the original partition database, effectively undoing
        all partition modifications.
        
        Args:
            _widget: The revert button widget (unused)
        """
        # Reset all partition configuration data in InstallationData
        InstallationData.create = []
        InstallationData.scheme = ""
        InstallationData.disk = ""
        InstallationData.slice = ""
        InstallationData.delete = []
        InstallationData.destroy = {}
        InstallationData.new_partition = []
        DiskPartition.create_partition_database()
        cls.tree_store()
        cls.treeview.expand_all()

    @classmethod
    def create_partition(cls, _widget):
        """
        Create a new partition based on the current selection.
        
        Opens the appropriate editor dialog based on the selected item:
        - Scheme editor for un-partitioned disks
        - Label editor for free space in MBR or GPT
        - Slice editor for MBR primary partition creation
        
        Args:
            _widget: The create button widget (unused)
        """
        cls.create_bt.set_sensitive(False)
        cls.delete_bt.set_sensitive(False)
        cls.auto_bt.set_sensitive(False)
        cls.revert_bt.set_sensitive(False)
        if cls.change_schemes is True:
            cls.scheme_editor()
        elif 'freespace' in cls.label:
            cls.label_editor(cls.path, cls.size, 'MBR')
        elif 'freespace' in cls.slice:
            if cls.scheme == "MBR" and cls.path[1] < 4:
                cls.slice_editor()
            elif cls.scheme == "GPT":
                cls.label_editor(cls.path,  cls.size, 'GPT')
        else:
            print('This method of creating partition is not implemented')

    @classmethod
    def partition_selection(cls, widget):
        """
        Handle partition selection events and update UI button states.
        
        This method is called when a user selects a different item in the partition
        tree view. It analyzes the selection and enables/disables appropriate buttons
        based on what operations are valid for the selected item.
        
        The method handles complex logic for:
        - Determining partition hierarchy (disk/slice/label)
        - Checking partition scheme compatibility
        - Validating boot partition requirements
        - Managing button sensitivity states
        
        Args:
            widget: TreeSelection widget that triggered the selection change
        """
        efi_already_exist = False
        model, cls.iter, = widget.get_selected()
        if cls.iter is None:
            Button.next_button.set_sensitive(False)
            return None
        cls.path = model.get_path(cls.iter)
        main_tree_iter = model.get_iter(cls.path)
        cls.size = model.get_value(main_tree_iter, 1)
        tree_iter1 = model.get_iter(cls.path[0])
        cls.scheme = model.get_value(tree_iter1, 3)
        cls.disk = model.get_value(tree_iter1, 0)
        
        if len(cls.path) >= 2:
            tree_iter2 = model.get_iter(cls.path[:2])
            cls.slice = model.get_value(tree_iter2, 0)
            cls.change_schemes = False
        else:
            if len(cls.path) == 1:
                if DiskPartition.how_partition(cls.disk) == 0:
                    cls.change_schemes = True
                elif DiskPartition.how_partition(cls.disk) == 1:
                    slice_path = f'{cls.path[0]}:0'
                    try:
                        tree_iter2 = model.get_iter(slice_path)
                        if 'freespace' in model.get_value(tree_iter2, 0):
                            cls.change_schemes = True
                        else:
                            cls.change_schemes = False
                    except ValueError:
                        cls.change_schemes = True
                else:
                    cls.change_schemes = False
                cls.slice = 'Not selected'
            else:
                cls.slice = 'Not selected'
                cls.change_schemes = False
                
        if len(cls.path) == 3:
            tree_iter3 = model.get_iter(cls.path[:3])
            cls.label = model.get_value(tree_iter3, 0)
        else:
            cls.label = 'Not selected'
            
        # Get previous partition info for context
        if len(cls.path) == 2 and cls.path[1] > 0 and cls.scheme == "GPT":
            path_behind = f'{cls.path[0]}:{str(int(cls.path[1] - 1))}'
            tree_iter4 = model.get_iter(path_behind)
            cls.mount_point_behind = model.get_value(tree_iter4, 2)
            cls.fs_behind = model.get_value(tree_iter4, 3)
        elif len(cls.path) == 3 and cls.path[2] > 0 and cls.scheme == "MBR":
            path1 = cls.path[0]
            path2 = str(cls.path[1])
            path3 = str(int(cls.path[2] - 1))
            path_behind2 = f'{path1}:{path2}:{path3}'
            tree_iter1 = model.get_iter(path_behind2)
            cls.mount_point_behind = model.get_value(tree_iter1, 2)
            cls.fs_behind = model.get_value(tree_iter1, 3)
        else:
            cls.mount_point_behind = None
            cls.fs_behind = None
            
        # Set button states based on selection
        if 'freespace' in cls.slice:
            cls.create_bt.set_sensitive(True)
            cls.delete_bt.set_sensitive(False)
            cls.auto_bt.set_sensitive(True)
            # Scan for efi partition
            for num in range(cls.path[1]):
                partition_path = f"{cls.path[0]}:{num}"
                tree_iter_1 = model.get_iter(partition_path)
                first_fs = model.get_value(tree_iter_1, 3)
                if first_fs == "UEFI" or 'efi' in first_fs:
                    cls.efi_exist = True
                    break
            else:
                cls.efi_exist = False
        elif 'freespace' in cls.label:
            if cls.path[1] > 3:
                cls.create_bt.set_sensitive(False)
            else:
                cls.create_bt.set_sensitive(True)
                cls.auto_bt.set_sensitive(True)
            cls.delete_bt.set_sensitive(False)
        elif 's' in cls.slice and len(cls.path) > 1:
            cls.create_bt.set_sensitive(False)
            cls.delete_bt.set_sensitive(True)
            cls.auto_bt.set_sensitive(False)
        elif 'p' in cls.slice and len(cls.path) > 1:
            cls.create_bt.set_sensitive(False)
            cls.delete_bt.set_sensitive(True)
            cls.auto_bt.set_sensitive(False)
        else:
            cls.delete_bt.set_sensitive(False)
            cls.auto_bt.set_sensitive(False)
            if DiskPartition.how_partition(cls.disk) == 0:
                cls.create_bt.set_sensitive(True)
            elif cls.change_schemes is True:
                cls.create_bt.set_sensitive(True)
            else:
                cls.create_bt.set_sensitive(False)
                
        # Handle partition validation
        if InstallationData.new_partition:
            cls.partitions = InstallationData.new_partition
            if not cls.partitions:
                Button.next_button.set_sensitive(False)
                return None
            if 'GPT' in InstallationData.scheme:
                if InstallationData.disk:
                    disk = InstallationData.disk
                    disk_id = cls.disk_index.index(disk)
                    num = 0
                    while True:
                        partition_path = f"{disk_id}:{num}"
                        try:
                            tree_iter_1 = model.get_iter(partition_path)
                            first_fs = model.get_value(tree_iter_1, 3)
                            if 'efi' in first_fs:
                                efi_already_exist = True
                                break
                        except ValueError:
                            efi_already_exist = False
                            break
                        num += 1
                if 'BOOT' in cls.partitions[0] and bios_type == 'BIOS':
                    if len(cls.partitions) >= 2 and 'ZFS' in cls.partitions[1]:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                elif efi_already_exist is True and bios_type == 'UEFI':
                    if 'ZFS' in cls.partitions[0]:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                elif len(cls.partitions) >= 2 and 'UEFI' in cls.partitions[0] and 'ZFS' in cls.partitions[1]:
                    Button.next_button.set_sensitive(True)
                else:
                    Button.next_button.set_sensitive(False)
            elif 'MBR' in InstallationData.scheme:
                cls.efi_exist = False
                if len(cls.partitions) >= 1:
                    if "/boot\n" in cls.partitions[0]:
                        if len(cls.partitions) >= 2 and 'ZFS' in cls.partitions[1]:
                            Button.next_button.set_sensitive(True)
                        else:
                            Button.next_button.set_sensitive(False)
                    elif 'ZFS' in cls.partitions[0]:
                        Button.next_button.set_sensitive(True)
                    else:
                        Button.next_button.set_sensitive(False)
                else:
                    Button.next_button.set_sensitive(False)
            else:
                Button.next_button.set_sensitive(False)
        else:
            Button.next_button.set_sensitive(False)
                
        # Check if any configuration exists to enable revert button
        path_exist = [
            bool(InstallationData.create),
            bool(InstallationData.scheme),
            bool(InstallationData.disk),
            bool(InstallationData.slice),
            bool(InstallationData.delete),
            bool(InstallationData.destroy),
            bool(InstallationData.new_partition)
        ]
        if any(path_exist):
            cls.revert_bt.set_sensitive(True)
        else:
            cls.revert_bt.set_sensitive(False)
