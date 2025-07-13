"""
Contains the data class and some commonly use variables
"""
import os
import gettext

be_name = "default"
logo = "/usr/local/lib/install-station/image/logo.png"
gif_logo = "/usr/local/lib/install-station/image/G_logo.gif"
pc_sysinstall = "/usr/local/sbin/pc-sysinstall"
query = "sh /usr/local/lib/install-station/backend-query"
tmp = "/tmp"
installation_config = f'{tmp}/ghostbsd_installation.cfg'
zfs_datasets = "/," \
    "/home(mountpoint=/home)," \
    "/tmp(mountpoint=/tmp|exec=on|setuid=off)," \
    "/usr(mountpoint=/usr|canmount=off)," \
    "/usr/ports(setuid=off)," \
    "/usr/src," \
    "/var(mountpoint=/var|canmount=off)," \
    "/var/audit(exec=off|setuid=off)," \
    "/var/crash(exec=off|setuid=off)," \
    "/var/log(exec=off|setuid=off)," \
    "/var/mail(atime=on)," \
    "/var/tmp(setuid=off)"


class InstallationData:
    """
    Centralized data storage for installation configuration
    """
    # Partition configuration
    destroy: dict = {}
    delete: list = []
    new_partition: list = []
    create: list = []
    scheme: str = ""
    disk: str = ""
    slice: str = ""
    boot: str = ""
    
    # ZFS configuration data (instead of zfs_config file)
    zfs_config_data: list = []
    
    # UFS configuration data (instead of ufs_config file)  
    ufs_config_data: list = []
    
    # Installation type and mode
    install_mode: str = ""  # "install" or "try"
    filesystem_type: str = ""  # "zfs", "ufs", or "custom"
    
    # Language and localization
    language: str = ""
    language_code: str = ""
    
    # Keyboard configuration
    keyboard_layout: str = ""
    keyboard_layout_code: str = ""
    keyboard_variant: str = ""
    keyboard_model: str = ""
    keyboard_model_code: str = ""
    
    # Boot manager configuration
    boot_manager: str = ""
    
    # Network configuration (for live mode)
    network_config: dict = {}
    
    @classmethod
    def reset(cls):
        """Reset all installation data"""
        cls.destroy = {}
        cls.delete = []
        cls.new_partition = []
        cls.create = []
        cls.scheme = ""
        cls.disk = ""
        cls.slice = ""
        cls.boot = ""
        cls.zfs_config_data = []
        cls.ufs_config_data = []
        cls.install_mode = ""
        cls.filesystem_type = ""
        cls.language = ""
        cls.language_code = ""
        cls.keyboard_layout = ""
        cls.keyboard_layout_code = ""
        cls.keyboard_variant = ""
        cls.keyboard_model = ""
        cls.keyboard_model_code = ""
        cls.boot_manager = ""
        cls.network_config = {}


def get_text(text):
    """
    Global translation function that always returns current language translation.
    
    Args:
        text: Text to translate
        
    Returns:
        str: Translated text in current language
    """
    # Force reload of translations for current language
    gettext.bindtextdomain('install-station', '/usr/local/share/locale')
    gettext.textdomain('install-station')
    return gettext.gettext(text)
