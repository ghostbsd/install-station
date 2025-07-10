Install Station
===
It is a strip down version of install-station and it is the new installer for GhostBSD.

Install Station only edit disk, partition and will install GhostBSD. Users and system setup will be done with at the first boot after installation with Setup Station.

## Managing Translations
To create a translation file.
```shell
./setup.py create_translation --locale=fr
```

To update translation files
```shell
./setup.py update_translations
```