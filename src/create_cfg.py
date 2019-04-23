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
        if os.path.exists(zfs_config):
            # Disk Setup
            r = open(zfs_config, 'r')
            zfsconf = r.readlines()
            for line in zfsconf:
                if 'partscheme' in line:
                    f.writelines(line)
                    read = open(boot_file, 'r')
                    boot = read.readlines()[0].strip()
                    if boot == 'refind':
                        f.writelines('bootManager=none\n')
                        f.writelines('efiLoader=%s\n' % boot)
                    else:
                        f.writelines('bootManager=%s\n' % boot)
                        f.writelines('efiLoader=none\n')
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
                    if boot == 'refind':
                        f.writelines('bootManager=none\n')
                        f.writelines('efiLoader=%s\n' % boot)
                    else:
                        f.writelines('bootManager=%s\n' % boot)
                        f.writelines('efiLoader=none\n')
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
            if boot == 'refind':
                f.writelines('bootManager=none\n')
                f.writelines('efiLoader=%s\n' % boot)
            else:
                f.writelines('bootManager=%s\n' % boot)
                f.writelines('efiLoader=none\n')
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
        f.writelines('runExtCommand=cat /etc/rc.conf | grep kld_list >> $FSMNT/etc/rc.conf\n')
        if os.path.exists("/etc/X11/xorg.conf"):
            f.writelines('runExtCommand=cp /etc/X11/xorg.conf $FSMNT/etc/X11/xorg.conf\n')
        f.writelines('runScript=/root/iso_to_hd.sh\n')
        f.writelines('runCommand=rm -f /root/iso_to_hd.sh\n')
        if os.path.exists(zfs_config):
            zfsark = """echo 'vfs.zfs.arc_max="512M"' >> /boot/loader.conf"""
            f.writelines(f'runCommand={zfsark}')
        f.close()
