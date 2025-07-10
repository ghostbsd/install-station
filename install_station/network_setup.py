import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import re
import _thread
from time import sleep
from NetworkMgr.net_api import (
    networkdictionary,
    connectToSsid,
    delete_ssid_wpa_supplicant_config,
    nic_status
)
import gettext

gettext.bindtextdomain('install-station', '/usr/local/share/locale')
gettext.textdomain('install-station')
_ = gettext.gettext

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


class NetworkSetup:
    _instance = None

    def __new__(cls, button3=None):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(NetworkSetup, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_model(cls):
        return cls().vbox1

    @staticmethod
    def wifi_stat(bar):
        if bar > 75:
            return 'nm-signal-100'
        elif bar > 50:
            return 'nm-signal-75'
        elif bar > 25:
            return 'nm-signal-50'
        elif bar > 5:
            return 'nm-signal-25'
        else:
            return 'nm-signal-00'

    def update_network_detection(self):
        cards = self.network_info['cards']
        card_list = list(cards.keys())
        r = re.compile("wlan")
        wlan_list = list(filter(r.match, card_list))
        wire_list = list(set(card_list).difference(wlan_list))
        cards = self.network_info['cards']
        if wire_list:
            for card in wire_list:
                if cards[card]['state']['connection'] == 'Connected':

                    wire_text = _('Network card connected to the internet')
                    self.wire_connection_image.set_from_stock(Gtk.STOCK_YES, 5)
                    print('Connected True')
                    self.next_button.set_sensitive(True)
                    break
            else:
                wire_text = _('Network card not connected to the internet')
                self.wire_connection_image.set_from_stock(Gtk.STOCK_NO, 5)
        else:
            wire_text = _('No network card detected')
            self.wire_connection_image.set_from_stock(Gtk.STOCK_NO, 5)

        self.wire_connection_label.set_label(wire_text)

        if wlan_list:
            for wlan_card in wlan_list:
                if cards[wlan_card]['state']['connection'] == 'Connected':
                    wifi_text = _('WiFi card detected and connected to an access point')
                    self.wifi_connection_image.set_from_stock(Gtk.STOCK_YES, 5)
                    break
            else:
                wifi_text = _('WiFi card detected but not connected to an access point')
                self.wifi_connection_image.set_from_stock(Gtk.STOCK_NO, 5)
        else:
            wifi_text = _("WiFi card not detected or not supported")
            self.wifi_connection_image.set_from_stock(Gtk.STOCK_NO, 5)

        self.wifi_connection_label.set_label(wifi_text)

    def __init__(self, next_button=None):
        """Initialize only once."""
        if not self._initialized:
            self.next_button = next_button
            self._initialize_ui()
            self._initialized = True

    def _initialize_ui(self):
        self.network_info = networkdictionary()
        print(self.network_info)
        self.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        self.vbox1.show()
        title = Gtk.Label(label=_('Network Setup'), name="Header")
        title.set_property("height-request", 50)
        self.vbox1.pack_start(title, False, False, 0)
        cards = self.network_info['cards']
        card_list = list(cards.keys())
        r = re.compile("wlan")
        wlan_list = list(filter(r.match, card_list))
        wire_list = list(set(card_list).difference(wlan_list))

        self.wire_connection_label = Gtk.Label()
        self.wire_connection_label.set_xalign(0.01)
        self.wire_connection_image = Gtk.Image()
        self.wifi_connection_label = Gtk.Label()
        self.wifi_connection_label.set_xalign(0.01)
        self.wifi_connection_image = Gtk.Image()

        if wire_list:
            for card in wire_list:
                if cards[card]['state']['connection'] == 'Connected':
                    wire_text = _('Network card connected to the internet')
                    self.wire_connection_image.set_from_stock(Gtk.STOCK_YES, 5)
                    print('Connected True')
                    self.next_button.set_sensitive(True)
                    break
            else:
                wire_text = _('Network card not connected to the internet')
                self.wire_connection_image.set_from_stock(Gtk.STOCK_NO, 5)
        else:
            wire_text = _('No network card detected')
            self.wire_connection_image.set_from_stock(Gtk.STOCK_NO, 5)

        self.wire_connection_label.set_label(wire_text)
        wlan_card = ""
        if wlan_list:
            for wlan_card in wlan_list:
                if cards[wlan_card]['state']['connection'] == 'Connected':
                    wifi_text = _('WiFi card detected and connected to an access point')
                    self.wifi_connection_image.set_from_stock(Gtk.STOCK_YES, 5)
                    break
            else:
                wifi_text = _('WiFi card detected but not connected to an access point')
                self.wifi_connection_image.set_from_stock(Gtk.STOCK_NO, 5)
        else:
            wifi_text = _('WiFi card not detected or not supported')
            self.wifi_connection_image.set_from_stock(Gtk.STOCK_NO, 5)

        self.wifi_connection_label.set_label(wifi_text)

        self.connection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True, spacing=20)
        if wlan_card:
            # add a default card variable
            sw = Gtk.ScrolledWindow()
            sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
            for ssid in self.network_info['cards'][wlan_card]['info']:
                ssid_info = self.network_info['cards'][wlan_card]['info'][ssid]
                bar = ssid_info[4]
                stat = NetworkSetup.wifi_stat(bar)
                pixbuf = Gtk.IconTheme.get_default().load_icon(stat, 32, 0)
                self.store.append([pixbuf, ssid, f'{ssid_info}'])
            treeview = Gtk.TreeView()
            treeview.set_model(self.store)
            treeview.set_rules_hint(True)
            pixbuf_cell = Gtk.CellRendererPixbuf()
            pixbuf_column = Gtk.TreeViewColumn('Stat', pixbuf_cell)
            pixbuf_column.add_attribute(pixbuf_cell, "pixbuf", 0)
            pixbuf_column.set_resizable(True)
            treeview.append_column(pixbuf_column)
            cell = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn('SSID', cell, text=1)
            column.set_sort_column_id(1)
            treeview.append_column(column)
            tree_selection = treeview.get_selection()
            tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
            tree_selection.connect("changed", self.wifi_setup, wlan_card)
            sw.add(treeview)
            self.connection_box.pack_start(sw, True, True, 50)

        main_grid = Gtk.Grid()
        main_grid.set_row_spacing(10)
        main_grid.set_column_spacing(10)
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        self.vbox1.pack_start(main_grid, True, True, 10)
        main_grid.attach(self.wire_connection_image, 2, 1, 1, 1)
        main_grid.attach(self.wire_connection_label, 3, 1, 8, 1)
        main_grid.attach(self.wifi_connection_image, 2, 2, 1, 1)
        main_grid.attach(self.wifi_connection_label, 3, 2, 8, 1)
        main_grid.attach(self.connection_box, 1, 4, 10, 5)

    def wifi_setup(self, tree_selection, wifi_card):
        model, treeiter = tree_selection.get_selected()
        if treeiter is not None:
            ssid = model[treeiter][1]
            ssid_info = self.network_info['cards'][wifi_card]['info'][ssid]
            caps = ssid_info[6]
            print(ssid)  # added the code to authenticate.
            print(ssid_info)
            if caps == 'E' or caps == 'ES':
                if f'"{ssid}"' in open("/etc/wpa_supplicant.conf").read():
                    self.try_to_connect_to_ssid(ssid, ssid_info, wifi_card)
                else:
                    NetworkSetup.open_wpa_supplicant(ssid)
                    self.try_to_connect_to_ssid(ssid, ssid_info, wifi_card)
            else:
                if f'"{ssid}"' in open('/etc/wpa_supplicant.conf').read():
                    self.try_to_connect_to_ssid(ssid, ssid_info, wifi_card)
                else:
                    self.authentication(ssid_info, wifi_card, False)

    def add_to_wpa_supplicant(self, _widget, ssid_info, card):
        pwd = self.password.get_text()
        NetworkSetup.setup_wpa_supplicant(ssid_info[0], ssid_info, pwd)
        _thread.start_new_thread(
            self.try_to_connect_to_ssid,
            (ssid_info[0], ssid_info, card)
        )
        self.window.hide()

    def try_to_connect_to_ssid(self, ssid, ssid_info, card):
        if connectToSsid(ssid, card) is False:
            delete_ssid_wpa_supplicant_config(ssid)
            GLib.idle_add(self.restart_authentication, ssid_info, card)
        else:
            for _ in list(range(30)):
                if nic_status(card) == 'associated':
                    self.network_info = networkdictionary()
                    print(self.network_info)
                    self.update_network_detection()
                    break
                sleep(1)
            else:
                delete_ssid_wpa_supplicant_config(ssid)
                GLib.idle_add(self.restart_authentication, ssid_info, card)
        return

    def restart_authentication(self, ssid_info, card):
        self.authentication(ssid_info, card, True)

    def on_check(self, widget):
        if widget.get_active():
            self.password.set_visibility(True)
        else:
            self.password.set_visibility(False)

    def authentication(self, ssid_info, card, failed):
        self.window = Gtk.Window()
        self.window.set_title(_("Wi-Fi Network Authentication Required"))
        self.window.set_border_width(0)
        self.window.set_size_request(500, 200)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        self.window.add(box1)
        box1.show()
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        # Creating MBR or GPT drive
        if failed:
            title = _("{ssid} Wi-Fi Network Authentication failed").format(ssid=ssid_info[0])
        else:
            title = _("Authentication required by {ssid} Wi-Fi Network").format(ssid=ssid_info[0])
        label = Gtk.Label(label=f"<b><span size='large'>{title}</span></b>")
        label.set_use_markup(True)
        pwd_label = Gtk.Label(label=_("Password:"))
        self.password = Gtk.Entry()
        self.password.set_visibility(False)
        check = Gtk.CheckButton(label=_("Show password"))
        check.connect("toggled", self.on_check)
        table = Gtk.Table(1, 2, True)
        table.attach(label, 0, 5, 0, 1)
        table.attach(pwd_label, 1, 2, 2, 3)
        table.attach(self.password, 2, 4, 2, 3)
        table.attach(check, 2, 4, 3, 4)
        box2.pack_start(table, False, False, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=False, spacing=10)
        box2.set_border_width(5)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        # Add create_scheme button
        cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.close)
        connect = Gtk.Button(stock=Gtk.STOCK_CONNECT)
        connect.connect("clicked", self.add_to_wpa_supplicant, ssid_info, card)
        table = Gtk.Table(1, 2, True)
        table.set_col_spacings(10)
        table.attach(connect, 4, 5, 0, 1)
        table.attach(cancel, 3, 4, 0, 1)
        box2.pack_end(table, True, True, 5)
        self.window.show_all()
        return 'Done'

    def close(self, _widget):
        self.window.hide()

    @staticmethod
    def setup_wpa_supplicant(ssid, ssid_info, pwd):
        if 'RSN' in ssid_info[-1]:
            ws = '\nnetwork={'
            ws += f'\n ssid="{ssid}"'
            ws += '\n key_mgmt=WPA-PSK'
            ws += '\n proto=RSN'
            ws += f'\n psk="{pwd}"\n'
            ws += '}\n'
        elif 'WPA' in ssid_info[-1]:
            ws = '\nnetwork={'
            ws += f'\n ssid="{ssid}"'
            ws += '\n key_mgmt=WPA-PSK'
            ws += '\n proto=WPA'
            ws += f'\n psk="{pwd}"\n'
            ws += '}\n'
        else:
            ws = '\nnetwork={'
            ws += f'\n ssid="{ssid}"'
            ws += '\n key_mgmt=NONE'
            ws += '\n wep_tx_keyidx=0'
            ws += f'\n wep_key0={pwd}\n'
            ws += '}\n'
        wsf = open("/etc/wpa_supplicant.conf", 'a')
        wsf.writelines(ws)
        wsf.close()

    @staticmethod
    def open_wpa_supplicant(ssid):
        ws = '\nnetwork={'
        ws += f'\n ssid={ssid}'
        ws += '\n key_mgmt=NONE\n}\n'
        with open("/etc/wpa_supplicant.conf", 'a') as wsf:
            wsf.writelines(ws)
