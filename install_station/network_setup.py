import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import re
import _thread
from time import sleep
from NetworkMgr.net_api import (
    network_dictionary,
    scan_networks,
    request_scan,
    wait_for_daemon,
    connect_to_ssid,
    wait_for_connection,
    enable_all_networks,
    wpa_reconfigure,
    wpa_save_config,
    ssid_is_saved,
    save_psk_network,
    update_psk_network,
    save_open_network,
    save_eap_network,
    nics_list,
    enable_wifi,
    get_system_ca_certificates,
    EAP_METHODS,
    PHASE2_METHODS
)
from install_station.data import get_text
from install_station.interface_controller import Button

logo = "/usr/local/lib/install-station/logo.png"
cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

# wpa_cli scan returns at once, the results land a few seconds later.
SCAN_WAIT = 4


class NetworkSetup:
    """
    Utility class for network setup following the utility class pattern.

    This class provides a GTK+ interface for network configuration including:
    - Wired network detection and status
    - WiFi network detection, rescan and connection
    - WPA-PSK, WEP, open and WPA-Enterprise authentication dialogs
    - Integration with Button class for navigation

    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the Interface controller for navigation flow.
    """
    # Class variables instead of instance variables
    vbox1: Gtk.Box | None = None
    network_info: dict | None = None
    networks: dict = {}
    wlan_card: str = ""
    wire_connection_label: Gtk.Label | None = None
    wire_connection_image: Gtk.Image | None = None
    wifi_connection_label: Gtk.Label | None = None
    wifi_connection_image: Gtk.Image | None = None
    wifi_spinner: Gtk.Spinner | None = None
    wifi_status_stack: Gtk.Stack | None = None
    rescan_button: Gtk.Button | None = None
    connection_box: Gtk.Box | None = None
    store: Gtk.ListStore | None = None
    treeview: Gtk.TreeView | None = None
    window: Gtk.Window | None = None
    password: Gtk.Entry | None = None
    eap_window: Gtk.Window | None = None
    eap_method_combo: Gtk.ComboBoxText | None = None
    phase2_box: Gtk.Box | None = None
    phase2_combo: Gtk.ComboBoxText | None = None
    identity_entry: Gtk.Entry | None = None
    anon_identity_entry: Gtk.Entry | None = None
    password_box: Gtk.Box | None = None
    eap_password: Gtk.Entry | None = None
    ca_cert_chooser: Gtk.FileChooserButton | None = None
    client_cert_box: Gtk.Box | None = None
    client_cert_chooser: Gtk.FileChooserButton | None = None
    private_key_box: Gtk.Box | None = None
    private_key_chooser: Gtk.FileChooserButton | None = None
    private_key_passwd_box: Gtk.Box | None = None
    private_key_passwd: Gtk.Entry | None = None

    @classmethod
    def get_model(cls) -> Gtk.Box:
        """
        Return the GTK widget model for the network setup interface.

        Returns the main container widget that was created during initialization.

        Returns:
            Gtk.Box: The main container widget for the network setup interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @staticmethod
    def wifi_stat(bar: int, secure: bool) -> str:
        """
        Get WiFi signal strength icon name based on signal bar percentage.

        Args:
            bar (int): Signal strength percentage
            secure (bool): True when the access point requires authentication

        Returns:
            str: Icon name for the signal strength
        """
        suffix = '-secure' if secure else ''
        if bar > 75:
            return f'nm-signal-100{suffix}'
        elif bar > 50:
            return f'nm-signal-75{suffix}'
        elif bar > 25:
            return f'nm-signal-50{suffix}'
        elif bar > 5:
            return f'nm-signal-25{suffix}'
        else:
            return f'nm-signal-00{suffix}'

    @staticmethod
    def bring_up_wlan_cards() -> None:
        """Bring every WiFi card up."""
        for card in nics_list():
            if card.startswith('wlan'):
                enable_wifi(card)

    @classmethod
    def update_network_detection(cls) -> None:
        """
        Update network detection status and UI elements.

        Checks both wired and wireless network connections and updates
        the UI with current status and enables/disables next button.
        """
        cards = cls.network_info['cards']
        card_list = list(cards.keys())
        r = re.compile("wlan")
        wlan_list = list(filter(r.match, card_list))
        wire_list = list(set(card_list).difference(wlan_list))

        # Update wired connection status
        if wire_list:
            for card in wire_list:
                if cards[card]['state']['connection'] == 'Connected':
                    wire_text = get_text('Network card connected to the internet')
                    cls.wire_connection_image.set_from_stock(Gtk.STOCK_YES, 5)
                    print('Connected True')
                    Button.next_button.set_sensitive(True)
                    break
            else:
                wire_text = get_text('Network card not connected to the internet')
                cls.wire_connection_image.set_from_stock(Gtk.STOCK_NO, 5)
        else:
            wire_text = get_text('No network card detected')
            cls.wire_connection_image.set_from_stock(Gtk.STOCK_NO, 5)

        cls.wire_connection_label.set_label(wire_text)

        # Update WiFi connection status
        if wlan_list:
            for wlan_card in wlan_list:
                if cards[wlan_card]['state']['connection'] == 'Connected':
                    wifi_text = get_text('WiFi card detected and connected to an access point')
                    cls.wifi_connection_image.set_from_stock(Gtk.STOCK_YES, 5)
                    break
            else:
                wifi_text = get_text('WiFi card detected but not connected to an access point')
                cls.wifi_connection_image.set_from_stock(Gtk.STOCK_NO, 5)
        else:
            wifi_text = get_text("WiFi card not detected or not supported")
            cls.wifi_connection_image.set_from_stock(Gtk.STOCK_NO, 5)

        cls.wifi_connection_label.set_label(wifi_text)

    @classmethod
    def populate_ssid_list(cls) -> None:
        """Fill the access point list from the latest scan of the WiFi card."""
        cls.store.clear()
        for ssid, network in cls.networks.items():
            secure = network['security'] != 'OPEN'
            cls.store.append([cls.wifi_stat(network['signal'], secure), ssid, network['security']])

    @classmethod
    def update_ui_text(cls) -> None:
        """
        Update all UI text elements with new translations after language change.
        """
        # Update button labels
        Button.update_button_labels()

        if cls.rescan_button:
            cls.rescan_button.set_label(get_text("Rescan"))

        # Update network status if elements exist
        if cls.network_info:
            cls.update_network_detection()

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the network setup UI following the utility class pattern.

        Creates the main interface including:
        - Network status indicators for wired and wireless
        - WiFi access point list and Rescan button if a WiFi card is detected
        - Grid-based layout with proper spacing and margins

        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.bring_up_wlan_cards()
        cls.network_info = network_dictionary()
        print(cls.network_info)

        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()

        wlan_list = [card for card in cls.network_info['cards'] if card.startswith('wlan')]
        cls.wlan_card = wlan_list[0] if wlan_list else ""
        if cls.wlan_card:
            cls.networks = scan_networks(cls.wlan_card)

        cls.wire_connection_label = Gtk.Label()
        cls.wire_connection_label.set_xalign(0.01)
        cls.wire_connection_image = Gtk.Image()
        cls.wifi_connection_label = Gtk.Label()
        cls.wifi_connection_label.set_xalign(0.01)
        cls.wifi_connection_image = Gtk.Image()
        cls.wifi_spinner = Gtk.Spinner()
        cls.wifi_status_stack = Gtk.Stack()
        cls.wifi_status_stack.add(cls.wifi_connection_image)
        cls.wifi_status_stack.add(cls.wifi_spinner)
        cls.update_network_detection()

        cls.connection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True, spacing=20)
        if cls.wlan_card:
            # Setup WiFi access point list
            sw = Gtk.ScrolledWindow()
            sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            cls.store = Gtk.ListStore(str, str, str)
            cls.populate_ssid_list()
            cls.treeview = Gtk.TreeView()
            cls.treeview.set_model(cls.store)
            cls.treeview.set_rules_hint(True)
            pixbuf_cell = Gtk.CellRendererPixbuf()
            pixbuf_cell.set_property('stock-size', Gtk.IconSize.DND)
            pixbuf_column = Gtk.TreeViewColumn('Stat', pixbuf_cell)
            pixbuf_column.add_attribute(pixbuf_cell, "icon-name", 0)
            pixbuf_column.set_resizable(True)
            cls.treeview.append_column(pixbuf_column)
            cell = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn('SSID', cell, text=1)
            column.set_sort_column_id(1)
            cls.treeview.append_column(column)
            cls.treeview.get_selection().set_mode(Gtk.SelectionMode.NONE)
            cls.treeview.set_activate_on_single_click(True)
            cls.treeview.connect("row-activated", cls.wifi_setup, cls.wlan_card)
            sw.add(cls.treeview)
            cls.connection_box.pack_start(sw, True, True, 50)

            cls.rescan_button = Gtk.Button(label=get_text("Rescan"))
            cls.rescan_button.set_image(
                Gtk.Image.new_from_icon_name('view-refresh', Gtk.IconSize.BUTTON)
            )
            cls.rescan_button.set_always_show_image(True)
            cls.rescan_button.set_halign(Gtk.Align.END)
            cls.rescan_button.set_valign(Gtk.Align.CENTER)
            cls.rescan_button.connect("clicked", cls.rescan)

        # Layout the interface
        main_grid = Gtk.Grid()
        main_grid.set_row_spacing(10)
        main_grid.set_column_spacing(10)
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        cls.vbox1.pack_start(main_grid, True, True, 10)
        main_grid.attach(cls.wire_connection_image, 2, 1, 1, 1)
        main_grid.attach(cls.wire_connection_label, 3, 1, 6, 1)
        if cls.rescan_button:
            main_grid.attach(cls.rescan_button, 9, 1, 2, 1)
        main_grid.attach(cls.wifi_status_stack, 2, 2, 1, 1)
        main_grid.attach(cls.wifi_connection_label, 3, 2, 8, 1)
        main_grid.attach(cls.connection_box, 1, 4, 10, 5)

        # The card may have just come up with an empty or stale scan table.
        if cls.wlan_card:
            cls.rescan(None)

    @classmethod
    def rescan(cls, _widget: Gtk.Button) -> None:
        """
        Rescan the WiFi card for access points without blocking the UI.

        Args:
            _widget: Button widget that triggered the action (unused)
        """
        cls.rescan_button.set_sensitive(False)
        cls.treeview.set_sensitive(False)
        _thread.start_new_thread(cls.scan_and_refresh, ())

    @classmethod
    def scan_and_refresh(cls) -> None:
        """Scan the WiFi card and hand the results to the UI thread."""
        try:
            if wait_for_daemon(cls.wlan_card) and request_scan(cls.wlan_card):
                sleep(SCAN_WAIT)
            GLib.idle_add(cls.refresh_networks, network_dictionary(),
                          scan_networks(cls.wlan_card))
        finally:
            GLib.idle_add(cls.rescan_button.set_sensitive, True)
            GLib.idle_add(cls.treeview.set_sensitive, True)

    @classmethod
    def refresh_networks(cls, network_info: dict, networks: dict) -> None:
        """
        Show new network information on the page.

        Args:
            network_info: Dictionary returned by network_dictionary()
            networks: Access points returned by scan_networks()
        """
        cls.network_info = network_info
        cls.networks = networks
        cls.update_network_detection()
        if cls.wlan_card in network_info['cards']:
            cls.populate_ssid_list()

    @classmethod
    def wifi_setup(cls, _treeview: Gtk.TreeView, path: Gtk.TreePath,
                   _column: Gtk.TreeViewColumn, wifi_card: str) -> None:
        """
        Handle WiFi access point activation and connection setup.

        Args:
            _treeview: TreeView holding the access point list (unused)
            path: Path of the activated access point row
            _column: Column that was activated (unused)
            wifi_card: WiFi card interface name
        """
        ssid = cls.store[path][1]
        network = cls.networks[ssid]
        # Drop whatever an abandoned attempt left unsaved in the daemon.
        wpa_reconfigure(wifi_card)
        if ssid_is_saved(ssid, wifi_card):
            cls.connect_in_background(network, wifi_card)
        elif network['security'] == 'OPEN':
            if save_open_network(ssid, wifi_card) is None:
                cls.update_network_detection()
            else:
                cls.connect_in_background(network, wifi_card)
        elif network['enterprise']:
            cls.enterprise_authentication(network, wifi_card, False)
        else:
            cls.authentication(network, wifi_card, False)

    @classmethod
    def add_to_wpa_supplicant(cls, _widget: Gtk.Button, network: dict, card: str) -> None:
        """
        Add WiFi credentials to wpa_supplicant and connect.

        Args:
            _widget: Button widget that triggered the action (unused)
            network: Access point record from scan_networks()
            card: WiFi card interface name
        """
        pwd = cls.password.get_text()
        ssid = network['ssid']
        cls.window.hide()
        wpa_reconfigure(card)
        if ssid_is_saved(ssid, card):
            stored = update_psk_network(ssid, pwd, card)
        else:
            stored = save_psk_network(ssid, network['security'], pwd, card) is not None
        if stored:
            cls.connect_in_background(network, card)
        else:
            cls.authentication(network, card, True)

    @classmethod
    def connect_in_background(cls, network: dict, card: str) -> None:
        """
        Show the connection attempt in the WiFi status line and run it in a thread.

        Args:
            network: Access point record from scan_networks()
            card: WiFi card interface name
        """
        connecting = get_text("Connecting to {ssid}...").format(ssid=network['ssid'])
        cls.wifi_connection_label.set_label(connecting)
        cls.wifi_spinner.start()
        cls.wifi_status_stack.set_visible_child(cls.wifi_spinner)
        cls.treeview.set_sensitive(False)
        cls.rescan_button.set_sensitive(False)
        _thread.start_new_thread(cls.try_to_connect_to_ssid, (network, card))

    @classmethod
    def end_connection_attempt(cls) -> None:
        """Put the WiFi status line back and unlock the access point list."""
        cls.wifi_spinner.stop()
        cls.wifi_status_stack.set_visible_child(cls.wifi_connection_image)
        cls.treeview.set_sensitive(True)
        cls.rescan_button.set_sensitive(True)
        cls.update_network_detection()

    @classmethod
    def connection_finished(cls, network_info: dict, networks: dict) -> None:
        """
        Show the new connection state once the card is connected.

        Args:
            network_info: Dictionary returned by network_dictionary()
            networks: Access points returned by scan_networks()
        """
        cls.refresh_networks(network_info, networks)
        cls.end_connection_attempt()

    @classmethod
    def try_to_connect_to_ssid(cls, network: dict, card: str) -> None:
        """
        Attempt to connect to the specified WiFi network.

        Args:
            network: Access point record from scan_networks()
            card: WiFi card interface name
        """
        ssid = network['ssid']
        try:
            if connect_to_ssid(ssid, card) and wait_for_connection(card, ssid):
                # Only now is the network worth writing to wpa_supplicant.conf.
                wpa_save_config(card)
                GLib.idle_add(cls.connection_finished, network_dictionary(),
                              scan_networks(card))
            else:
                wpa_reconfigure(card)
                GLib.idle_add(cls.restart_authentication, network, card)
        finally:
            # select_network disabled every other saved network.
            enable_all_networks(card)

    @classmethod
    def restart_authentication(cls, network: dict, card: str) -> None:
        """
        Restart WiFi authentication after a failed connection attempt.

        Args:
            network: Access point record from scan_networks()
            card: WiFi card interface name
        """
        cls.end_connection_attempt()
        if network['enterprise']:
            cls.enterprise_authentication(network, card, True)
        elif network['security'] != 'OPEN':
            cls.authentication(network, card, True)

    @classmethod
    def on_check(cls, widget: Gtk.CheckButton) -> None:
        """
        Toggle password visibility in authentication dialog.

        Args:
            widget: CheckButton widget for show/hide password
        """
        cls.password.set_visibility(widget.get_active())

    @classmethod
    def authentication(cls, network: dict, card: str, failed: bool) -> str:
        """
        Show WiFi authentication dialog.

        Args:
            network: Access point record from scan_networks()
            card: WiFi card interface name
            failed: Boolean indicating if this is a retry after failed authentication
        """
        cls.window = Gtk.Window()
        cls.window.set_title(get_text("Wi-Fi Network Authentication Required"))
        cls.window.set_border_width(0)
        cls.window.set_size_request(500, 200)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()

        # Set dialog title based on authentication status
        if failed:
            title = get_text("{ssid} Wi-Fi Network Authentication failed").format(ssid=network['ssid'])
        else:
            title = get_text("Authentication required by {ssid} Wi-Fi Network").format(ssid=network['ssid'])
        label = Gtk.Label(label=f"<b><span size='large'>{title}</span></b>")
        label.set_use_markup(True)
        pwd_label = Gtk.Label(label=get_text("Password:"))
        cls.password = Gtk.Entry()
        cls.password.set_visibility(False)
        check = Gtk.CheckButton(label=get_text("Show password"))
        check.connect("toggled", cls.on_check)
        table = Gtk.Table(1, 2, True)
        table.attach(label, 0, 5, 0, 1)
        table.attach(pwd_label, 1, 2, 2, 3)
        table.attach(cls.password, 2, 4, 2, 3)
        table.attach(check, 2, 4, 3, 4)
        box2.pack_start(table, False, False, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()

        # Add authentication buttons
        cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        cancel.connect("clicked", cls.close)
        connect = Gtk.Button(stock=Gtk.STOCK_CONNECT)
        connect.connect("clicked", cls.add_to_wpa_supplicant, network, card)
        table = Gtk.Table(1, 2, True)
        table.set_col_spacings(10)
        table.attach(connect, 4, 5, 0, 1)
        table.attach(cancel, 3, 4, 0, 1)
        box2.pack_end(table, True, True, 5)
        cls.window.show_all()
        return 'Done'

    @classmethod
    def close(cls, _widget: Gtk.Button) -> None:
        """
        Close the authentication dialog.

        Args:
            _widget: Button widget that triggered the action (unused)
        """
        cls.window.hide()

    @classmethod
    def add_enterprise_to_wpa_supplicant(cls, _widget: Gtk.Button, network: dict, card: str) -> None:
        """
        Add the WPA-Enterprise credentials to wpa_supplicant and connect.

        Args:
            _widget: Button widget that triggered the action (unused)
            network: Access point record from scan_networks()
            card: WiFi card interface name
        """
        eap_config = {
            'eap_method': cls.eap_method_combo.get_active_text(),
            'identity': cls.identity_entry.get_text(),
            'password': cls.eap_password.get_text(),
            'phase2': cls.phase2_combo.get_active_text(),
            'anonymous_identity': cls.anon_identity_entry.get_text(),
        }
        ca_file = cls.ca_cert_chooser.get_filename()
        if ca_file:
            eap_config['ca_cert'] = ca_file
        if eap_config['eap_method'] == 'TLS':
            client_cert = cls.client_cert_chooser.get_filename()
            if client_cert:
                eap_config['client_cert'] = client_cert
            private_key = cls.private_key_chooser.get_filename()
            if private_key:
                eap_config['private_key'] = private_key
            eap_config['private_key_passwd'] = cls.private_key_passwd.get_text()

        cls.eap_window.hide()
        wpa_reconfigure(card)
        if save_eap_network(network['ssid'], eap_config, card) is None:
            cls.enterprise_authentication(network, card, True)
        else:
            cls.connect_in_background(network, card)

    @classmethod
    def on_eap_method_changed(cls, combo: Gtk.ComboBoxText) -> None:
        """
        Show only the fields used by the selected EAP method.

        Args:
            combo: ComboBoxText holding the EAP method
        """
        method = combo.get_active_text()
        tls_mode = method == 'TLS'
        cls.client_cert_box.set_visible(tls_mode)
        cls.private_key_box.set_visible(tls_mode)
        cls.private_key_passwd_box.set_visible(tls_mode)
        cls.password_box.set_visible(not tls_mode)
        cls.phase2_box.set_visible(method in ('PEAP', 'TTLS'))

    @classmethod
    def close_eap_window(cls, _widget: Gtk.Button) -> None:
        """
        Close the enterprise authentication dialog.

        Args:
            _widget: Button widget that triggered the action (unused)
        """
        cls.eap_window.hide()

    @classmethod
    def on_eap_password_check(cls, widget: Gtk.CheckButton) -> None:
        """
        Toggle password visibility in the enterprise authentication dialog.

        Args:
            widget: CheckButton widget for show/hide password
        """
        cls.eap_password.set_visibility(widget.get_active())

    @staticmethod
    def form_label(text: str) -> Gtk.Label:
        """
        Create a right-aligned label for the enterprise authentication form.

        Args:
            text: Translated label text

        Returns:
            Gtk.Label: The label widget
        """
        label = Gtk.Label(label=text)
        label.set_halign(Gtk.Align.END)
        return label

    @staticmethod
    def file_chooser(title: str, name: str, patterns: list) -> Gtk.FileChooserButton:
        """
        Create a file chooser filtered on certificate or key files.

        Args:
            title: Translated dialog title
            name: Translated filter name
            patterns: Glob patterns accepted by the filter

        Returns:
            Gtk.FileChooserButton: The file chooser widget
        """
        chooser = Gtk.FileChooserButton(title=title, action=Gtk.FileChooserAction.OPEN)
        file_filter = Gtk.FileFilter()
        file_filter.set_name(name)
        for pattern in patterns:
            file_filter.add_pattern(pattern)
        chooser.add_filter(file_filter)
        return chooser

    @classmethod
    def enterprise_authentication(cls, network: dict, card: str, failed: bool) -> str:
        """
        Show the WPA-Enterprise (802.1X/EAP) authentication dialog.

        Args:
            network: Access point record from scan_networks()
            card: WiFi card interface name
            failed: Boolean indicating if this is a retry after failed authentication
        """
        cls.eap_window = Gtk.Window()
        cls.eap_window.set_title(get_text("Enterprise Wi-Fi Authentication"))
        cls.eap_window.set_border_width(10)
        cls.eap_window.set_size_request(550, 450)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        cls.eap_window.add(main_box)

        if failed:
            title = get_text("{ssid} Enterprise Authentication Failed").format(ssid=network['ssid'])
        else:
            title = get_text("Enterprise Authentication for {ssid}").format(ssid=network['ssid'])
        title_label = Gtk.Label()
        title_label.set_markup(f"<b><span size='large'>{title}</span></b>")
        main_box.pack_start(title_label, False, False, 5)

        security_label = Gtk.Label(
            label=get_text("Security: {security}").format(security=network['security'])
        )
        main_box.pack_start(security_label, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(8)
        main_box.pack_start(grid, True, True, 5)

        cls.eap_method_combo = Gtk.ComboBoxText()
        for method in EAP_METHODS:
            cls.eap_method_combo.append_text(method)
        cls.eap_method_combo.set_active(0)
        cls.eap_method_combo.connect("changed", cls.on_eap_method_changed)
        grid.attach(cls.form_label(get_text("EAP Method:")), 0, 0, 1, 1)
        grid.attach(cls.eap_method_combo, 1, 0, 2, 1)

        cls.phase2_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cls.phase2_combo = Gtk.ComboBoxText()
        for method in PHASE2_METHODS:
            cls.phase2_combo.append_text(method)
        cls.phase2_combo.set_active(0)
        cls.phase2_box.pack_start(cls.phase2_combo, True, True, 0)
        grid.attach(cls.form_label(get_text("Inner Auth:")), 0, 1, 1, 1)
        grid.attach(cls.phase2_box, 1, 1, 2, 1)

        cls.identity_entry = Gtk.Entry()
        cls.identity_entry.set_hexpand(True)
        grid.attach(cls.form_label(get_text("Username:")), 0, 2, 1, 1)
        grid.attach(cls.identity_entry, 1, 2, 2, 1)

        cls.anon_identity_entry = Gtk.Entry()
        cls.anon_identity_entry.set_placeholder_text(get_text("Optional - for privacy"))
        grid.attach(cls.form_label(get_text("Anonymous ID:")), 0, 3, 1, 1)
        grid.attach(cls.anon_identity_entry, 1, 3, 2, 1)

        cls.password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cls.eap_password = Gtk.Entry()
        cls.eap_password.set_visibility(False)
        cls.eap_password.set_hexpand(True)
        cls.password_box.pack_start(cls.eap_password, True, True, 0)
        show_pwd_check = Gtk.CheckButton(label=get_text("Show"))
        show_pwd_check.connect("toggled", cls.on_eap_password_check)
        cls.password_box.pack_start(show_pwd_check, False, False, 0)
        grid.attach(cls.form_label(get_text("Password:")), 0, 4, 1, 1)
        grid.attach(cls.password_box, 1, 4, 2, 1)

        cert_patterns = ["*.pem", "*.crt", "*.cer"]
        cert_filter_name = get_text("Certificates (*.pem, *.crt, *.cer)")
        cls.ca_cert_chooser = cls.file_chooser(
            get_text("Select CA Certificate"), cert_filter_name, cert_patterns
        )
        system_cas = get_system_ca_certificates()
        if system_cas:
            cls.ca_cert_chooser.set_filename(system_cas[0])
        grid.attach(cls.form_label(get_text("CA Certificate:")), 0, 5, 1, 1)
        grid.attach(cls.ca_cert_chooser, 1, 5, 2, 1)

        cls.client_cert_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cls.client_cert_chooser = cls.file_chooser(
            get_text("Select Client Certificate"), cert_filter_name, cert_patterns
        )
        cls.client_cert_box.pack_start(cls.client_cert_chooser, True, True, 0)
        grid.attach(cls.form_label(get_text("Client Cert:")), 0, 6, 1, 1)
        grid.attach(cls.client_cert_box, 1, 6, 2, 1)

        cls.private_key_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cls.private_key_chooser = cls.file_chooser(
            get_text("Select Private Key"),
            get_text("Key files (*.pem, *.key, *.p12)"),
            ["*.pem", "*.key", "*.p12"]
        )
        cls.private_key_box.pack_start(cls.private_key_chooser, True, True, 0)
        grid.attach(cls.form_label(get_text("Private Key:")), 0, 7, 1, 1)
        grid.attach(cls.private_key_box, 1, 7, 2, 1)

        cls.private_key_passwd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cls.private_key_passwd = Gtk.Entry()
        cls.private_key_passwd.set_visibility(False)
        cls.private_key_passwd_box.pack_start(cls.private_key_passwd, True, True, 0)
        grid.attach(cls.form_label(get_text("Key Password:")), 0, 8, 1, 1)
        grid.attach(cls.private_key_passwd_box, 1, 8, 2, 1)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        main_box.pack_start(button_box, False, False, 5)
        cancel_btn = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        cancel_btn.connect("clicked", cls.close_eap_window)
        button_box.pack_start(cancel_btn, False, False, 0)
        connect_btn = Gtk.Button(stock=Gtk.STOCK_CONNECT)
        connect_btn.connect("clicked", cls.add_enterprise_to_wpa_supplicant, network, card)
        button_box.pack_start(connect_btn, False, False, 0)

        cls.eap_window.show_all()
        cls.on_eap_method_changed(cls.eap_method_combo)
        return 'Done'