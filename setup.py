#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
# from glob import glob
from setuptools import setup

# import DistUtilsExtra.command.build_extra
# import DistUtilsExtra.command.build_i18n
# import DistUtilsExtra.command.clean_i18n

# to update i18n .mo files (and merge .pot file into .po files) run on Linux:
# ,,python setup.py build_i18n -m''

# silence pyflakes, __VERSION__ is properly assigned below...
__VERSION__ = '0.1'

# for line in open('gbinstall', 'r').readlines():
#     if (line.startswith('__VERSION__')):
#         exec(line.strip())
PROGRAM_VERSION = __VERSION__


def datafilelist(installbase, sourcebase):
    datafileList = []
    for root, subFolders, files in os.walk(sourcebase):
        fileList = []
        for f in files:
            fileList.append(os.path.join(root, f))
        datafileList.append((root.replace(sourcebase, installbase), fileList))
    return datafileList


prefix = sys.prefix

lib_gbinstall = [
    'src/confirm_installation.py',
    'src/create_cfg.py',
    'src/db_partition.py',
    'src/end.py',
    'src/error.py',
    'src/gbiWindow.py',
    'src/ghostbsd-style.css',
    'src/install.png',
    'src/install.py',
    'src/installType.py',
    'src/language.py',
    'src/logo.png',
    'src/partition.py',
    'src/slides.py',
    'src/sys_handler.py',
    'src/use_ufs.py',
    'src/use_zfs.py'
]

slide_images = [
    'src/slide-images/ghostbsd/browser.png',
    'src/slide-images/ghostbsd/customize.png',
    'src/slide-images/ghostbsd/email.png',
    'src/slide-images/ghostbsd/help.png',
    'src/slide-images/ghostbsd/G-logo.png',
    'src/slide-images/ghostbsd/music.png',
    'src/slide-images/ghostbsd/office.png',
    'src/slide-images/ghostbsd/photo.png',
    'src/slide-images/ghostbsd/social.png',
    'src/slide-images/ghostbsd/software.png',
    'src/slide-images/ghostbsd/welcome.png'
]


backend_query = [
    'src/backend-query/detect-laptop.sh',
    'src/backend-query/detect-nics.sh',
    'src/backend-query/detect-sheme.sh',
    'src/backend-query/detect-vmware.sh',
    'src/backend-query/detect-wifi.sh',
    'src/backend-query/disk-info.sh',
    'src/backend-query/disk-label.sh',
    'src/backend-query/disk-list.sh',
    'src/backend-query/disk-part.sh',
    'src/backend-query/enable-net.sh',
    'src/backend-query/list-components.sh',
    'src/backend-query/list-rsync-backups.sh',
    'src/backend-query/list-tzones.sh',
    'src/backend-query/query-langs.sh',
    'src/backend-query/send-logs.sh',
    'src/backend-query/setup-ssh-keys.sh',
    'src/backend-query/sys-mem.sh',
    'src/backend-query/test-live.sh',
    'src/backend-query/test-netup.sh',
    'src/backend-query/update-part-list.sh',
    'src/backend-query/xkeyboard-layouts.sh',
    'src/backend-query/xkeyboard-models.sh',
    'src/backend-query/xkeyboard-variants.sh'

]

# '{prefix}/share/man/man1'.format(prefix=sys.prefix), glob('data/*.1')),

data_files = [
    (f'{prefix}/share/applications', ['src/gbinstall.desktop']),
    (f'{prefix}/lib/gbinstall', lib_gbinstall),
    (f'{prefix}/lib/gbinstall/backend-query', backend_query),
    (f'{prefix}/lib/gbinstall/slide-images/ghostbsd', slide_images)
]

# data_files.extend(datafilelist('{prefix}/share/locale'.format(prefix=sys.prefix), 'build/mo'))

# cmdclass ={
#             "build" : DistUtilsExtra.command.build_extra.build_extra,
#             "build_i18n" :  DistUtilsExtra.command.build_i18n.build_i18n,
#             "clean": DistUtilsExtra.command.clean_i18n.clean_i18n,
# }

setup(name="gbinstall",
      version=PROGRAM_VERSION,
      description="Gbinstall is a GTK front end user interface for pc-sysinstall",
      license='BSD',
      author='Eric Turgeon',
      url='https://github/GhostBSD/gbinstall/',
      package_dir={'': '.'},
      data_files=data_files,
      # install_requires = [ 'setuptools', ],
      scripts=['gbinstall'],)
# cmdclass = cmdclass,
