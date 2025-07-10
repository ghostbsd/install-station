#!/usr/bin/env python
import os
import sys
from setuptools import setup, Command, glob
from DistUtilsExtra.command.build_extra import build_extra
from DistUtilsExtra.command.build_i18n import build_i18n
from DistUtilsExtra.command.clean_i18n import clean_i18n

prefix = sys.prefix
__VERSION__ = '0.1'
PROGRAM_VERSION = __VERSION__


def data_file_list(install_base, source_base):
    data = []
    for root, subFolders, files in os.walk(source_base):
        file_list = []
        for f in files:
            file_list.append(os.path.join(root, f))
        # Only add directories that actually have files
        if file_list:
            data.append((root.replace(source_base, install_base), file_list))
    return data


class UpdateTranslationsCommand(Command):
    """Custom command to extract messages and update .po files."""

    description = 'Extract messages to .pot and update .po'
    user_options = []  # No custom options

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Define paths
        pot_file = 'po/install-station.pot'
        po_files = glob.glob('po/*.po')
        # Step 1: Extract messages to .pot file
        print("Extracting messages to .pot file...")
        os.system(f'xgettext --from-code=UTF-8 -L Python -o {pot_file} install_station/*.py install-station')
        # Step 2: Update .po files with the new .pot file
        print("Updating .po files with new translations...")
        for po_file in po_files:
            print(f"Updating {po_file}...")
            os.system(f'msgmerge -U {po_file} {pot_file}')
        print("Translation update complete.")


class CreateTranslationCommand(Command):
    """Custom command to create a new .po file for a specific language."""
    locale = None
    description = 'Create a new .po file for the specified language'
    user_options = [
        ('locale=', 'l', 'Locale code for the new translation (e.g., fr, es)')
    ]

    def initialize_options(self):
        self.locale = None  # Initialize the locale option to None

    def finalize_options(self):
        if self.locale is None:
            raise Exception("You must specify the locale code (e.g., --locale=fr)")

    def run(self):
        # Define paths
        pot_file = 'po/install-station.pot'
        po_dir = 'po'
        po_file = os.path.join(po_dir, f'{self.locale}.po')
        # Check if the .pot file exists
        if not os.path.exists(pot_file):
            print("Extracting messages to .pot file...")
            os.system(f'xgettext --from-code=UTF-8 -L Python -o {pot_file} install_station/*.py install-station')
        # Create the new .po file
        if not os.path.exists(po_file):
            print(f"Creating new {po_file} for locale '{self.locale}'...")
            os.makedirs(po_dir, exist_ok=True)
            os.system(f'msginit --locale={self.locale} --input={pot_file} --output-file={po_file}')
        else:
            print(f"PO file for locale '{self.locale}' already exists: {po_file}")


lib_install_station_image = [
    'src/image/G_logo.gif',
    'src/image/install-gbsd.png',
    'src/image/logo.png',
    'src/image/disk.png',
    'src/image/laptop.png',
    'src/image/installation.jpg'
]

lib_install_station_backend_query = [
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

data_files = [
    (f'{prefix}/lib/install-station/backend-query', lib_install_station_backend_query),
    (f'{prefix}/lib/install-station/image', lib_install_station_image)
]

data_files.extend(data_file_list(f'{prefix}/share/locale', 'build/mo'))

setup(
    name="install-station",
    version=PROGRAM_VERSION,
    description="Install Station is a strip down version of gbi",
    license='BSD',
    author='Eric Turgeon',
    url='https://github/GhostBSD/install-station/',
    package_dir={'': '.'},
    install_requires=['setuptools'],
    packages=['install_station'],
    scripts=['install-station'],
    data_files=data_files,
    cmdclass={
            'create_translation': CreateTranslationCommand,
            'update_translations': UpdateTranslationsCommand,
            "build": build_extra,
            "build_i18n": build_i18n,
            "clean": clean_i18n
        }
)
