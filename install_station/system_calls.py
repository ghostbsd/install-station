#!/usr/bin/env python

import re
import os
from subprocess import Popen, run, PIPE
from install_station.data import pc_sysinstall


def replace_pattern(current: str, new: str, file: str) -> None:
    """Replace text patterns in a file using regex substitution.
    
    Args:
        current: Regular expression pattern to search for
        new: Replacement text
        file: Path to file to modify
    """
    parser_file = open(file, 'r').read()
    parser_patched = re.sub(current, new, parser_file)
    save_parser_file = open(file, 'w')
    save_parser_file.writelines(parser_patched)
    save_parser_file.close()


def language_dictionary() -> dict[str, str]:
    """Get available system languages from pc-sysinstall.
    
    Returns:
        Dictionary mapping language names to language codes
    """
    langs = Popen(f'{pc_sysinstall} query-langs', shell=True, stdin=PIPE,
                  stdout=PIPE, universal_newlines=True,
                  close_fds=True).stdout.readlines()
    dictionary = {}
    for line in langs:
        lang_list = line.rstrip()
        lang_name = lang_list.partition(' ')[2]
        lang_code = lang_list.partition(' ')[0]
        dictionary[lang_name] = lang_code
    return dictionary


def localize_system(locale: str) -> None:
    """Apply localization settings to the system.
    
    Updates login.conf, profile files, and greeter configurations
    with the specified locale.
    
    Args:
        locale: Language code (e.g. 'en_US', 'fr_FR')
    """
    slick_greeter = "/usr/local/share/xgreeters/slick-greeter.desktop"
    gtk_greeter = "/usr/local/share/xgreeters/lightdm-gtk-greeter.desktop"
    replace_pattern('lang=C', f'lang={locale}', '/etc/login.conf')
    replace_pattern('en_US', locale, '/etc/profile')
    replace_pattern('en_US', locale, '/usr/share/skel/dot.profile')

    if os.path.exists(slick_greeter):
        replace_pattern(
            'Exec=slick-greeter',
            f'Exec=env LANG={locale}.UTF-8 slick-greeter',
            slick_greeter
        )
    elif os.path.exists(gtk_greeter):
        replace_pattern(
            'Exec=lightdm-gtk-greete',
            f'Exec=env LANG={locale}.UTF-8 lightdm-gtk-greeter',
            gtk_greeter
        )


def keyboard_dictionary() -> dict[str, dict[str, str | None]]:
    """Get available keyboard layouts and variants from pc-sysinstall.
    
    Returns:
        Dictionary mapping keyboard layout names to layout/variant dictionaries
    """
    xkeyboard_layouts = Popen(f'{pc_sysinstall} xkeyboard-layouts', shell=True,
                              stdout=PIPE,
                              universal_newlines=True).stdout.readlines()
    dictionary = {}
    for line in xkeyboard_layouts:
        keyboard_list = list(filter(None, line.rstrip().split('  ')))
        kb_name = keyboard_list[1].strip()
        kb_layouts = keyboard_list[0].strip()
        kb_variant = None
        # Skip the "custom" layout as it's not a real keyboard layout
        if kb_layouts != 'custom':
            dictionary[kb_name] = {'layout': kb_layouts, 'variant': kb_variant}

    xkeyboard_variants = Popen(f'{pc_sysinstall} xkeyboard-variants',
                               shell=True, stdout=PIPE,
                               universal_newlines=True).stdout.readlines()
    for line in xkeyboard_variants:
        xkb_variant = line.rstrip()
        kb_name = xkb_variant.partition(':')[2].strip()
        keyboard_list = list(filter
                             (None, xkb_variant.partition(':')[0].split()))
        kb_layouts = keyboard_list[1].strip()
        kb_variant = keyboard_list[0].strip()
        dictionary[kb_name] = {'layout': kb_layouts, 'variant': kb_variant}
    return dictionary


def keyboard_models() -> dict[str, str]:
    """Get available keyboard models from pc-sysinstall.
    
    Returns:
        Dictionary mapping keyboard model names to model codes
    """
    xkeyboard_models = Popen(f'{pc_sysinstall} xkeyboard-models', shell=True,
                             stdout=PIPE,
                             universal_newlines=True).stdout.readlines()
    dictionary = {}
    for line in xkeyboard_models:
        kbm_name = line.rstrip().partition(' ')[2]
        kbm_code = line.rstrip().partition(' ')[0]
        dictionary[kbm_name] = kbm_code
    return dictionary


def change_keyboard(kb_layout: str, kb_variant: str | None = None, kb_model: str | None = None) -> None:
    """Apply keyboard layout change immediately using setxkbmap.
    
    Args:
        kb_layout: Keyboard layout code
        kb_variant: Optional keyboard variant code
        kb_model: Optional keyboard model code
    """
    if kb_variant is None and kb_model is not None:
        run(f"setxkbmap -layout {kb_layout} -model {kb_model}", shell=True)
    elif kb_variant is not None and kb_model is None:
        run(f"setxkbmap -layout {kb_layout} -variant {kb_variant}", shell=True)
    elif kb_variant is not None and kb_model is not None:
        set_kb_cmd = f"setxkbmap -layout {kb_layout} -variant {kb_variant} " \
            f"-model {kb_model}"
        run(set_kb_cmd, shell=True)
    else:
        run(f"setxkbmap -layout {kb_layout}", shell=True)


def set_keyboard(kb_layout: str, kb_variant: str | None = None, kb_model: str | None = None) -> None:
    """
    Permanently configure keyboard layout for the live system.
    Based on pc-sysinstall's localize_x_keyboard function.
    """
    setxkbmap_cmd = ""
    
    # Build setxkbmap command
    if kb_model and kb_model != "NONE":
        setxkbmap_cmd = f"-model {kb_model}"
        kx_model = kb_model
    else:
        kx_model = "pc104"
    
    if kb_layout and kb_layout != "NONE":
        setxkbmap_cmd = f"{setxkbmap_cmd} -layout {kb_layout}".strip()
        kx_layout = kb_layout
    else:
        kx_layout = "us"
    
    if kb_variant and kb_variant != "NONE":
        setxkbmap_cmd = f"{setxkbmap_cmd} -variant {kb_variant}"
    
    # Apply the keyboard layout immediately
    if setxkbmap_cmd:
        run(f"setxkbmap {setxkbmap_cmd}", shell=True)
        
        # Create .xprofile for persistent keyboard layout
        xprofile_path = "/home/ghostbsd/.xprofile"
        try:
            # Read existing .xprofile or create new one
            if os.path.exists(xprofile_path):
                with open(xprofile_path, 'r') as f:
                    content = f.read()
                # Remove existing setxkbmap lines
                lines = [line for line in content.splitlines() if not line.strip().startswith('setxkbmap')]
            else:
                lines = ["#!/bin/sh"]
            
            # Add new setxkbmap command
            lines.append(f"setxkbmap {setxkbmap_cmd}")
            
            # Write back to .xprofile
            with open(xprofile_path, 'w') as f:
                f.write('\n'.join(lines) + '\n')
            
            # Make executable
            os.chmod(xprofile_path, 0o755)
            
        except (OSError, IOError) as e:
            print(f"Warning: Could not update .xprofile: {e}")
        
        # Set console keymap in rc.conf for live system persistence
        try:
            _set_console_keymap(kx_layout)
        except (OSError, IOError) as e:
            print(f"Warning: Could not update console keymap: {e}")


def _set_console_keymap(key_layout: str) -> None:
    """Helper function to set console keymap in rc.conf"""
    # Map X11 layouts to console keymaps (from pc-sysinstall)
    keymap_mapping = {
        'ca': 'ca-fr.kbd',
        'et': 'ee.kbd', 
        'es': 'es.acc.kbd',
        'gb': 'uk.kbd'
    }
    
    console_keymap = keymap_mapping.get(key_layout, f"{key_layout}.kbd")
    
    rc_conf_path = "/etc/rc.conf"
    keymap_line = f'keymap="{console_keymap}"\n'
    
    # Check if keymap already exists in rc.conf
    if os.path.exists(rc_conf_path):
        with open(rc_conf_path, 'r') as f:
            lines = f.readlines()
        
        # Remove existing keymap lines
        lines = [line for line in lines if not line.strip().startswith('keymap=')]
        
        # Add new keymap
        lines.append(keymap_line)
        
        with open(rc_conf_path, 'w') as f:
            f.writelines(lines)
    else:
        with open(rc_conf_path, 'w') as f:
            f.write(keymap_line)


def timezone_dictionary() -> dict[str, list[str]]:
    """Get available timezones from pc-sysinstall.
    
    Returns:
        Dictionary mapping continents to lists of cities/regions
    """
    tz_list = Popen(f'{pc_sysinstall} list-tzones', shell=True,
                    stdout=PIPE, universal_newlines=True).stdout.readlines()
    city_list = []
    dictionary = {}
    last_continent = ''
    for zone in tz_list:
        zone_list = zone.partition(':')[0].rstrip().split('/')
        continent = zone_list[0]
        if continent != last_continent:
            city_list = []
        if len(zone_list) == 3:
            city = zone_list[1] + '/' + zone_list[2]
        elif len(zone_list) == 4:
            city = zone_list[1] + '/' + zone_list[2] + '/' + zone_list[3]
        else:
            city = zone_list[1]
        city_list.append(city)
        dictionary[continent] = city_list
        last_continent = continent
    return dictionary


def zfs_disk_query() -> list[str]:
    """Query available disks for ZFS installation.
    
    Returns:
        List of available disk device names
    """
    disk_output = Popen(
        f"{pc_sysinstall} disk-list",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        universal_newlines=True,
        close_fds=True
    )
    return disk_output.stdout.readlines()


def zfs_disk_size_query(disk: str) -> str:
    """Query disk size information.
    
    Args:
        disk: Disk device name
        
    Returns:
        Disk size information string
    """
    disk_info_output = Popen(
        f"{pc_sysinstall} disk-info {disk}",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        universal_newlines=True,
        close_fds=True
    )
    return disk_info_output.stdout.readlines()[3].partition('=')[2]


def set_admin_user(username: str, name: str, password: str, shell: str, homedir: str, hostname: str) -> None:
    """Set up administrator user and system hostname.
    
    Args:
        username: Username for the admin user
        name: Full name for the admin user
        password: Password for the admin user
        shell: Default shell for the admin user
        homedir: Home directory path for the admin user
        hostname: System hostname to set
    """
    # Set Root user
    run(f"echo '{password}' | pw usermod -n root -h 0", shell=True)
    cmd = f"echo '{password}' | pw useradd {username} -c {name} -h 0" \
        f" -s {shell} -m -d {homedir} -g wheel,operator"
    run(cmd, shell=True)
    run(f"sysrc hostname={hostname}", shell=True)
    run(f"hostname {hostname}", shell=True)
