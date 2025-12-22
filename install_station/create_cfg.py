from install_station.data import InstallationData, installation_config


class Configuration:
    """
    Utility class for creating and validating GhostBSD installation configuration files.
    
    This class provides methods to generate the ghostbsd_installation.cfg file
    used by the GhostBSD installer and validate all required installation data
    before configuration file creation.
    
    The class follows a utility pattern with class methods for stateless operations,
    designed to integrate with the InstallationData system for configuration management.
    """

    @classmethod
    def sanity_check(cls):
        """
        Perform sanity checks on all installation data used by create_cfg.
        
        Validates that all required installation parameters are present and valid
        before attempting to create the configuration file.
        
        Returns:
            tuple: (bool, list) - (is_valid, list_of_errors)
                is_valid: True if all checks pass, False otherwise
                list_of_errors: List of error messages describing validation failures
        """
        errors = []

        # Check basic installation data
        if not hasattr(InstallationData, 'boot') or not InstallationData.boot:
            errors.append("Boot manager not specified")
        elif InstallationData.boot not in ['refind', 'grub', 'none']:
            errors.append(f"Invalid boot manager: {InstallationData.boot}")

        # Check ZFS configuration path
        if InstallationData.zfs_config_data:
            if not isinstance(InstallationData.zfs_config_data, list):
                errors.append("ZFS config data is not a list")
            else:
                # Check for required ZFS configuration elements
                has_partscheme = any('partscheme' in str(line) for line in InstallationData.zfs_config_data)
                if not has_partscheme:
                    errors.append("ZFS config missing partition scheme")

                has_disk = any('disk0=' in str(line) for line in InstallationData.zfs_config_data)
                if not has_disk:
                    errors.append("ZFS config missing disk specification")
        else:
            # Check custom partition configuration path
            if not hasattr(InstallationData, 'disk') or not InstallationData.disk:
                errors.append("Disk not specified for custom partitioning")

            if not hasattr(InstallationData, 'slice') or not InstallationData.slice:
                errors.append("Partition slice not specified")

            if not hasattr(InstallationData, 'scheme') or not InstallationData.scheme:
                errors.append("Partition scheme not specified")
            elif InstallationData.scheme not in ['partscheme=GPT', 'partscheme=MBR']:
                errors.append(f"Invalid partition scheme: {InstallationData.scheme}")

            if not hasattr(InstallationData, 'new_partition') or not InstallationData.new_partition:
                errors.append("No partitions defined for custom partitioning")
            elif not isinstance(InstallationData.new_partition, list):
                errors.append("Partition data is not a list")

        # Check installation config file path
        if not installation_config:
            errors.append("Installation config file path not defined")

        return not errors, errors

    @classmethod
    def create_cfg(cls):
        """
        Create the ghostbsd_installation.cfg file to install GhostBSD.
        
        Generates the configuration file used by the GhostBSD installer based on
        data stored in InstallationData. Supports both ZFS and custom partitioning
        configurations.
        
        The configuration includes:
        - Installation mode and type settings
        - Disk and partition configuration
        - Boot manager setup
        - Network configuration
        - First boot preparation commands
        
        Raises:
            ValueError: If sanity check fails, indicating invalid configuration data
            IOError: If unable to write to the configuration file
        """
        # Perform sanity check before creating configuration
        is_valid, errors = cls.sanity_check()
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)

        try:
            with open(installation_config, 'w') as f:
                # Installation Mode
                f.write('# Installation Mode\n')
                f.write('installMode=fresh\n')
                f.write('installInteractive=no\n')
                f.write('installType=GhostBSD\n')
                f.write('installMedium=livezfs\n')
                f.write('packageType=livezfs\n')

                if InstallationData.zfs_config_data:
                    # ZFS Configuration Path
                    for line in InstallationData.zfs_config_data:
                        if 'partscheme' in line:
                            f.write(line)
                            boot = InstallationData.boot
                            if boot == 'refind':
                                f.write('bootManager=none\n')
                                f.write(f'efiLoader={boot}\n')
                            else:
                                f.write(f'bootManager={boot}\n')
                                f.write('efiLoader=none\n')
                        else:
                            f.write(line)
                else:
                    # Custom Partition Configuration Path
                    d_output = InstallationData.disk
                    f.write('\n# Disk Setup\n')
                    f.write('ashift=12\n')
                    f.write(f'disk0={d_output}\n')
                    # Partition Slice.
                    f.write(f'partition={InstallationData.slice}\n')
                    # Boot Menu
                    boot = InstallationData.boot
                    if boot == 'refind':
                        f.write('bootManager=none\n')
                        f.write(f'efiLoader={boot}\n')
                    else:
                        f.write(f'bootManager={boot}\n')
                        f.write('efiLoader=none\n')
                    f.write(f'{InstallationData.scheme}\n')
                    f.write('commitDiskPart\n')
                    # Partition Setup
                    f.write('\n# Partition Setup\n')
                    for line in InstallationData.new_partition:
                        if 'BOOT' not in line and 'BIOS' not in line and 'UEFI' not in line:
                            f.write(f'disk0-part={line.strip()}\n')
                    f.write('commitDiskLabel\n')

                # Network Configuration
                f.write('\n# Network Configuration\n')
                f.write('hostname=installed\n')

                # First Boot Preparation Commands
                f.write('\n# command to prepare first boot\n')
                f.write("runCommand=sysrc hostname='installed'\n")
                f.write("runCommand=pw userdel -n ghostbsd -r\n")
                f.write("runCommand=sed -i '' 's/ghostbsd/root/g' /etc/gettytab\n")
                f.write("runCommand=sed -i '' 's/ghostbsd/root/g' /etc/ttys\n")
                f.write("runCommand=echo '# WARNING: Do NOT set initial_setup_enable=YES manually!' >> /etc/rc.conf\n")
                f.write("runCommand=echo '# This service is ONLY for first boot after installation.' >> /etc/rc.conf\n")
                f.write("runCommand=echo '# It will automatically disable itself after running.' >> /etc/rc.conf\n")
                f.write("runCommand=sysrc initial_setup_enable=YES\n")
                f.write("runCommand=sed -i '' '/^autologin-user=/d' /usr/local/etc/lightdm/lightdm.conf\n")
                f.write("runCommand=sed -i '' '/^autologin-session=/d' /usr/local/etc/lightdm/lightdm.conf\n")
        except IOError as e:
            raise IOError(f"Failed to write configuration file: {e}") from e
