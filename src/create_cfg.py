#!/usr/bin/env python
#
# Copyright (c) 2013 GhostBSD
#
# See COPYING for licence terms.
#
# create_cfg.py v 1.4 Friday, January 17 2014 Eric Turgeon
#

import os
import pickle

# Directory use from the installer.
tmp = "/tmp/.gbinstall/"
installer = "/usr/local/lib/gbinstall/"
# Installer data file.
disk = f'{tmp}disk'
layout = f'{tmp}layout'
model = f'{tmp}model'
pcinstallcfg = f'{tmp}pcinstall.cfg'
user_passwd = f'{tmp}user'
language = f'{tmp}language'
dslice = f'{tmp}slice'
left = f'{tmp}left'
partlabel = f'{tmp}partlabel'
timezone = f'{tmp}timezone'
KBFile = f'{tmp}keyboard'
boot_file = f'{tmp}boot'
disk_schem = f'{tmp}scheme'
zfs_config = f'{tmp}zfs_config'
ufs_config = f'{tmp}ufs_config'


class gbsd_cfg():
    def __init__(self):
        f = open(pcinstallcfg, 'w')
        # Installation Mode
        f.writelines('# Installation Mode\n')
        f.writelines('installMode=fresh\n')
        f.writelines('installInteractive=no\n')
        f.writelines('installType=GhostBSD\n')
        f.writelines('installMedium=livecd\n')
        f.writelines('packageType=livecd\n')
        # System Language
        if os.path.exists(language):
            langfile = open(language, 'r')
            lang = langfile.readlines()[0].rstrip()
            f.writelines('\n# System Language\n\n')
            f.writelines(f'localizeLang={lang}\n')
            os.remove(language)
        # Keyboard Setting
        if os.path.exists(KBFile):
            f.writelines('\n# Keyboard Setting\n')
            rkb = open(KBFile, 'r')
            kb = rkb.readlines()
            kbl = kb[0].rstrip()
            f.writelines(f'localizeKeyLayout={kbl}\n')
            kbv = kb[1].rstrip()
            if kbv != 'None':
                f.writelines(f'localizeKeyVariant={kbv}\n')
            kbm = kb[2].rstrip()
            if kbm != 'None':
                f.writelines(f'localizeKeyModel={kbm}\n')
        # Timezone
        if os.path.exists(timezone):
            time = open(timezone, 'r')
            t_output = time.readlines()[0].strip()
            f.writelines('\n# Timezone\n')
            f.writelines(f'timeZone={t_output}\n')
            f.writelines('enableNTP=yes\n')
            os.remove(timezone)
        if os.path.exists(zfs_config):
            # Disk Setup
            r = open(zfs_config, 'r')
            zfsconf = r.readlines()
            for line in zfsconf:
                if 'partscheme' in line:
                    f.writelines(line)
                    read = open(boot_file, 'r')
                    boot = read.readlines()[0].strip()
                    f.writelines(f'bootManager={boot}\n')
                    os.remove(boot_file)
                else:
                    f.writelines(line)
            # os.remove(zfs_config)
        elif os.path.exists(ufs_config):
            # Disk Setup
            r = open(ufs_config, 'r')
            ufsconf = r.readlines()
            for line in ufsconf:
                if 'partscheme' in line:
                    f.writelines(line)
                    read = open(boot_file, 'r')
                    boot = read.readlines()[0].strip()
                    f.writelines(f'bootManager={boot}\n')
                    os.remove(boot_file)
                else:
                    f.writelines(line)
        else:
            # Disk Setup
            r = open(disk, 'r')
            drive = r.readlines()
            d_output = drive[0].strip()
            f.writelines('\n# Disk Setup\n')
            f.writelines(f'disk0={d_output}\n')
            os.remove(disk)
            # Partition Slice.
            p = open(dslice, 'r')
            line = p.readlines()
            part = line[0].rstrip()
            f.writelines(f'partition={part}\n')
            os.remove(dslice)
            # Boot Menu
            read = open(boot_file, 'r')
            line = read.readlines()
            boot = line[0].strip()
            f.writelines(f'bootManager={boot}\n')
            # os.remove(boot_file)
            # Sheme sheme
            read = open(disk_schem, 'r')
            shem = read.readlines()[0]
            f.writelines(shem + '\n')
            f.writelines('commitDiskPart\n')
            # os.remove(disk_schem)
            # Partition Setup
            f.writelines('\n# Partition Setup\n')
            part = open(partlabel, 'r')
            # If slice and auto file exist add first partition line.
            # But Swap need to be 0 it will take the rest of the freespace.
            for line in part:
                if 'BOOT' in line or 'BIOS' in line or 'UEFI' in line:
                    pass
                else:
                    f.writelines(f'disk0-part={line.strip()}\n')
            f.writelines('commitDiskLabel\n')
            os.remove(partlabel)
        # Network Configuration
        f.writelines('\n# Network Configuration\n')
        if os.path.exists(user_passwd):
            readu = open(user_passwd, 'rb')
            uf = pickle.load(readu)
            net = uf[5]
            f.writelines(f'hostname={net}\n')
            # Set the root pass
        if os.path.exists(f'{tmp}root'):
            readr = open(f'{tmp}root', 'rb')
            rf = pickle.load(readr)
            root = rf[0]
            f.writelines('\n# Set the root pass\n')
            f.writelines(f'rootPass={root}\n')
        if os.path.exists(user_passwd):
            # Network Configuration
            f.writelines('\n# Network Configuration\n')
            readu = open(user_passwd, 'rb')
            uf = pickle.load(readu)
            net = uf[5]
            f.writelines(f'hostname={net}\n')
            user = uf[0]
            # Setup our users
            f.writelines('\n# Setup user\n')
            f.writelines(f'userName={user}\n')
            name = uf[1]
            f.writelines(f'userComment={name}\n')
            passwd = uf[2]
            f.writelines(f'userPass={passwd.rstrip()}\n')
            shell = uf[3]
            f.writelines(f'userShell={shell}\n')
            upath = uf[4]
            f.writelines(f'userHome={upath.rstrip()}\n')
            f.writelines(f'defaultGroup=wheel\n')
            f.writelines(f'userGroups=operator\n')
            f.writelines('commitUser\n')
        f.writelines('runScript=/root/iso_to_hd.sh\n')
        f.writelines('runCommand=rm -f /root/iso_to_hd.sh\n')
        if os.path.exists(zfs_config):
            zfsark = """echo 'vfs.zfs.arc_max="512M"' >> /boot/loader.conf"""
            f.writelines(f'runCommand={zfsark}')
        # adding setting for keyboard in slim
        keyboard_conf = '/usr/local/etc/X11/xorg.conf.d/keyboard.conf'
        k_conf_list = [
            'Section "InputClass"',
            '        Identifier "Keyboard0"',
            '        Driver "kbd"',
            f'        Option "XkbLayout"      "{kbl}"'
        ]
        if kbv != 'None':
            k_conf_list.append(f'        Option "XkbVariant"     "{kbv}"')
        if kbm != 'None':
            k_conf_list.append(f'        Option "XkbModel"       "{kbm}"')
        k_conf_list.append('EndSection')
        for conf_line in k_conf_list:
            if 'Section "InputClass"' == conf_line:
                cmd = f"""echo '{conf_line}' > {keyboard_conf}"""
            else:
                cmd = f"""echo '{conf_line}' >> {keyboard_conf}"""
            f.writelines(f'runCommand={cmd}\n')
        f.close()
        os.remove(user_passwd)
