"""Disk partition management module for GhostBSD Install Station.

Provides disk partitioning functionality including detection, creation, deletion
of partitions for GPT/MBR schemes with ZFS support and manages the partition database.
"""
import re
from time import sleep
from subprocess import Popen, PIPE, STDOUT, call
from install_station.data import query, zfs_datasets, InstallationData

# Define required file paths


def get_disk_from_partition(part):
    """Extract the disk name from a partition identifier.
    
    Args:
        part (str): Partition identifier (e.g., 'ada0p1', 'ada0s1a')
        
    Returns:
        str: Disk name (e.g., 'ada0')
    """
    if set("p") & set(part):
        return part.partition('p')[0]
    else:
        return part.partition('s')[0]


def slice_number(part):
    """Extract the slice/partition number from a partition identifier.
    
    Args:
        part (str): Partition identifier (e.g., 'ada0p1', 'ada0s1')
        
    Returns:
        int: Slice/partition number
    """
    if set("p") & set(part):
        return int(part.partition('p')[2])
    else:
        return int(part.partition('s')[2])


def find_next_partition(partition_name, partition_list):
    """Find the next available partition name with sequential numbering.
    
    Args:
        partition_name (str): Base partition name (e.g., 'freespace', 'ada0p')
        partition_list (list): List of existing partition names
        
    Returns:
        str: Next available partition name (e.g., 'freespace1', 'ada0p2')
    """
    for num in range(1, 10000):
        if f'{partition_name}{num}' not in partition_list:
            return f'{partition_name}{num}'


def disk_list():
    """Get a list of available disk devices on the system.
    
    Queries the FreeBSD kernel for available disks and filters out
    optical drives (CD/DVD devices).
    
    Returns:
        list: Sorted list of disk device names (e.g., ['ada0', 'ada1'])
    """
    disk_popen = Popen(
        'sysctl -n kern.disks',
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        universal_newlines=True,
        close_fds=True
    )
    disks = disk_popen.stdout.read()
    cleaned_disk = re.sub(r'acd[0-9]*|cd[0-9]*|scd[0-9]*', '', disks)
    return sorted(cleaned_disk.split())


def device_model(disk):
    """Get the model description of a disk device.
    
    Args:
        disk (str): Disk device name (e.g., 'ada0')
        
    Returns:
        str: Device model description
    """
    device_popen = Popen(
        f"diskinfo -v {disk} 2>/dev/null | grep 'Disk descr' | cut -d '#' -f1 | tr -d '\t'",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        universal_newlines=True,
        close_fds=True
    )
    return device_popen.stdout.read().strip()


def disk_size(disk):
    """Get the size of a disk device.
    
    Args:
        disk (str): Disk device name (e.g., 'ada0')
        
    Returns:
        str: Disk size information
    """
    disk_size_output = Popen(
        f"{query}/disk-info.sh {disk}",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        universal_newlines=True,
        stderr=STDOUT,
        close_fds=True
    )
    return disk_size_output.stdout.readlines()[0].rstrip()


def get_scheme(disk):
    """Detect the partition scheme of a disk device.
    
    Args:
        disk (str): Disk device name (e.g., 'ada0')
        
    Returns:
        str: Partition scheme ('GPT', 'MBR', or empty if none)
    """
    scheme_output = Popen(
        f"{query}/detect-sheme.sh {disk}",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        universal_newlines=True,
        stderr=STDOUT,
        close_fds=True
    )
    return scheme_output.stdout.readlines()[0].rstrip()


class DiskPartition:
    """Main class for disk partition detection and database management.
    
    This class provides methods to scan disk devices, detect existing partitions,
    and maintain an in-memory database of partition information for both GPT and
    MBR partition schemes.
    
    Attributes:
        disk_database (dict): In-memory database of disk and partition information
        query_partition (str): Path to disk partition query script
    """
    disk_database: dict = {}

    query_partition = f'{query}/disk-part.sh'

    @classmethod
    def mbr_partition_slice_db(cls, disk):
        """Create database of MBR slices and their partitions.
        
        Args:
            disk (str): Disk device name (e.g., 'ada0')
            
        Returns:
            dict: Database of slices with their partition information
        """
        partition_output = Popen(
            f'{cls.query_partition} {disk}',
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            universal_newlines=True
        )
        slice_db = {}
        free_num = 1
        for line in partition_output.stdout:
            info = line.strip().split()
            slice_name = info[0]
            if 'freespace' in line:
                slice_name = f'freespace{free_num}'
                free_num += 1
            part_db = cls.mbr_partition_db(info[0])
            part_list = [] if part_db is None else list(part_db.keys())
            partitions = {
                'name': slice_name,
                'size': info[1].partition('M')[0],
                'mount-point': '',
                'file-system': info[2],
                'stat': None,
                'partitions': part_db,
                'partition-list': part_list
            }
            slice_db[slice_name] = partitions
        return slice_db

    @classmethod
    def mbr_partition_db(cls, partition_slice):
        """Create database of partitions within an MBR slice.
        
        Args:
            partition_slice (str): Slice identifier (e.g., 'ada0s1')
            
        Returns:
            dict or None: Database of partitions within the slice, or None for freespace
        """
        if 'freespace' in partition_slice:
            return None
        else:
            slice_output = Popen(
                f'{query}/disk-label.sh {partition_slice}',
                shell=True,
                stdin=PIPE,
                stdout=PIPE,
                universal_newlines=True
            )
            partition_db = {}
            alph = ord('a')
            free_num = 1
            for line in slice_output.stdout:
                info = line.strip().split()
                if 'freespace' in line:
                    partition_name = f'freespace{free_num}'
                    free_num += 1
                else:
                    letter = chr(alph)
                    partition_name = f'{partition_slice}{letter}'
                    alph += 1
                partitions = {
                    'name': partition_name,
                    'size': info[0].partition('M')[0],
                    'mount-point': '',
                    'file-system': info[2],
                    'stat': None,
                }
                partition_db[partition_name] = partitions
            if not partition_db:
                return None
            return partition_db

    @classmethod
    def gpt_partition_db(cls, disk):
        """Create database of GPT partitions on a disk.
        
        Args:
            disk (str): Disk device name (e.g., 'ada0')
            
        Returns:
            dict: Database of GPT partitions
        """
        partition_output = Popen(
            f'{cls.query_partition} {disk}',
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            universal_newlines=True
        )
        partition_db = {}
        free_num = 1
        for line in partition_output.stdout:
            info = line.strip().split()
            slice_name = info[0]
            if 'freespace' in line:
                slice_name = f'freespace{free_num}'
                free_num += 1
            partitions = {
                'name': info[0],
                'size': info[1].partition('M')[0],
                'mount-point': '',
                'file-system': info[2],
                'stat': None,
                'partitions': {},
                'partition-list': []
            }
            partition_db[slice_name] = partitions
        return partition_db

    @classmethod
    def create_partition_database(cls):
        """Scan all disks and create comprehensive partition database.
        
        This method queries all available disks, detects their partition schemes,
        and builds a complete database of disk and partition information.
        """
        # if os.path.exists(disk_db_file):
        #     os.remove(disk_db_file)
        # drives_database = open(disk_db_file, 'wb')
        disk_db = {}
        for disk in disk_list():
            disk_info_db = {}
            disk_info_db.setdefault('scheme', get_scheme(disk))
            if disk_info_db['scheme'] == "GPT":
                part_db = cls.gpt_partition_db(disk)
            elif disk_info_db['scheme'] == "MBR":
                part_db = cls.mbr_partition_slice_db(disk)
            else:
                disk_info_db['scheme'] = None
                part_db = {}
            part_list = [] if part_db is None else list(part_db.keys())
            disk_info_db['size'] = disk_size(disk)
            disk_info_db['device_model'] = device_model(disk)
            disk_info_db['partitions'] = part_db
            disk_info_db['partition-list'] = part_list
            disk_info_db['stat'] = None
            disk_db[disk] = disk_info_db
        cls.disk_database = disk_db

    @classmethod
    def get_disk_database(cls):
        """Get the current disk database.
        
        Returns:
            dict: Current disk and partition database
        """
        return cls.disk_database.copy()

    @classmethod
    def how_partition(cls, disk):
        """Get the number of partitions on a disk.
        
        Args:
            disk (str): Disk device name
            
        Returns:
            int: Number of partitions on the disk
        """
        return len(cls.disk_database[disk]['partitions'])

    @classmethod
    def set_disk_scheme(cls, scheme, disk, size):
        """Set or update the partitioning scheme for a disk.
        
        Args:
            scheme (str or None): Partition scheme ('GPT' or 'MBR')
            disk (str): Disk device name
            size (str): Disk size
        """
        if scheme is None:
            cls.disk_database[disk]['scheme'] = 'GPT'
        else:
            cls.disk_database[disk]['scheme'] = scheme
        # this need to data and not use pickle with open.
        InstallationData.destroy[disk] = scheme
        if not cls.disk_database[disk]['partitions']:
            cls.disk_database[disk]['partitions'] = {
                'freespace1': {
                    'name': 'freespace1',
                    'size': size,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
            }
            cls.disk_database[disk]['partition-list'] = [
                'freespace1'
            ]


class DeletePartition:
    """Class for handling partition deletion operations.
    
    This class provides methods to delete partitions from both GPT and MBR
    partition schemes, handling the consolidation of free space and updating
    the partition database accordingly.
    """

    def find_if_label(self, part):
        """Check if a partition identifier represents a BSD label.
        
        Args:
            part (str): Partition identifier
            
        Returns:
            bool: True if the partition has a BSD label suffix (letter)
        """
        last = part[-1]
        if re.search('[a-z]', last):
            return True
        return False

    def delete_label(self, drive, label, partition, path):
        """Delete a BSD label partition and consolidate free space.
        
        Args:
            drive (str): Disk device name
            label (str): Label partition to delete
            partition (str): Parent slice containing the label
            path (list): Path information for partition location
        """
        disk_partitions = DiskPartition.disk_database[drive]['partitions'][partition]
        partitions_info = disk_partitions['partitions']
        label_list = disk_partitions['partition-list']
        last_list_number = len(label_list) - 1
        store_list_number = path[2]
        size_free = int(partitions_info[label]['size'])

        if last_list_number == store_list_number and len(label_list) > 1:
            label_behind = label_list[store_list_number - 1]
            if 'freespace' in label_behind:
                size_free += int(partitions_info[label_behind]['size'])
                label_list.remove(label)
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'][label_behind] = {
                    'name': label_behind,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
            else:
                free_name = find_next_partition('freespace', label_list)
                label_list[store_list_number] = free_name
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'][free_name] = {
                    'name': free_name,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
        elif store_list_number == 0 and len(label_list) > 1:
            label_after = label_list[store_list_number + 1]
            if 'freespace' in label_after:
                size_free += int(partitions_info[label_after]['size'])
                label_list.remove(label)
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'][label_after] = {
                    'name': label_after,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
            else:
                free_name = find_next_partition('freespace', label_list)
                label_list[store_list_number] = free_name
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'][free_name] = {
                    'name': free_name,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
        elif len(label_list) > 2:
            label_behind = label_list[store_list_number - 1]
            label_after = label_list[store_list_number + 1]
            size_behind = int(partitions_info[label_behind]['size'])
            size_after = int(partitions_info[label_after]['size'])
            if ('freespace' in label_behind
                    and 'freespace' in label_after):
                size_free += size_behind + size_after
                label_list.remove(label)
                label_list.remove(label_after)
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'].pop(label_after, None)
                disk_partitions['partitions'][label_behind] = {
                    'name': label_behind,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
            elif 'freespace' in label_behind:
                size_free += size_behind
                label_list.remove(label)
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'][label_behind] = {
                    'name': label_behind,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
            elif 'freespace' in label_after:
                size_free += size_after
                label_list.remove(label)
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'].pop(label_after, None)
                disk_partitions['partitions'][label_after] = {
                    'name': label_after,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
            else:
                free_name = find_next_partition('freespace', label_list)
                label_list[store_list_number] = free_name
                disk_partitions['partitions'].pop(label, None)
                disk_partitions['partitions'][free_name] = {
                    'name': free_name,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_partitions['partition-list'] = label_list
        else:
            free_name = find_next_partition('freespace', label_list)
            label_list[store_list_number] = free_name
            disk_partitions['partitions'].pop(label, None)
            disk_partitions['partitions'][free_name] = {
                'name': free_name,
                'size': size_free,
                'mount-point': '',
                'file-system': 'none',
                'stat': None,
                'partitions': {},
                'partition-list': []
            }
            disk_partitions['partition-list'] = label_list

        # Data is already updated in DiskPartition.disk_database - no need to save to file
        remaining_partition = []
        for part in label_list:
            partitions_info = disk_partitions['partitions']
            if part in partitions_info:
                size = partitions_info[part]['size']
                mount_point = partitions_info[part]['mount-point']
                file_system = partitions_info[part]['file-system']
                stat = partitions_info[part]['stat']
                if stat == 'New':
                    remaining_partition.append(f'{file_system} {size} {mount_point}\n')
        InstallationData.new_partition = remaining_partition

    def __init__(self, part, path):
        """Initialize partition deletion operation.
        
        Args:
            part (str): Partition identifier to delete
            path (list): Path information for partition location
        """
        drive = get_disk_from_partition(part)
        if part == "freespace":
            pass
        elif self.find_if_label(part) is True:
            spart = part[:-1]
            self.delete_label(drive, part, spart, path)
        else:
            self.delete_slice(drive, part, path)

    def delete_slice(self, drive, partition, path):
        """Delete a slice/partition and consolidate adjacent free space.
        
        Args:
            drive (str): Disk device name
            partition (str): Partition to delete
            path (list): Path information for partition location
        """
        disk_data = DiskPartition.disk_database
        partitions_info = disk_data[drive]['partitions']
        partition_list = disk_data[drive]['partition-list']
        last_list_number = len(partition_list) - 1
        store_list_number = path[1]
        size_free = int(partitions_info[partition]['size'])
        if last_list_number == store_list_number and len(partition_list) > 1:
            partition_behind = partition_list[store_list_number - 1]
            if 'freespace' in partition_behind:
                size_free += int(partitions_info[partition_behind]['size'])
                partition_list.remove(partition)
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][partition_behind] = {
                    'name': partition_behind,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
            else:
                free_name = find_next_partition('freespace', partition_list)
                partition_list[store_list_number] = free_name
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][free_name] = {
                    'name': free_name,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
        elif store_list_number == 0 and len(partition_list) > 1:
            partition_after = partition_list[store_list_number + 1]
            if 'freespace' in partition_after:
                size_free += int(partitions_info[partition_after]['size'])
                partition_list.remove(partition)
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][partition_after] = {
                    'name': partition_after,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
            else:
                free_name = find_next_partition('freespace', partition_list)
                partition_list[store_list_number] = free_name
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][free_name] = {
                    'name': free_name,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
        elif len(partition_list) > 2:
            partition_behind = partition_list[store_list_number - 1]
            partition_after = partition_list[store_list_number + 1]
            size_behind = int(partitions_info[partition_behind]['size'])
            size_after = int(partitions_info[partition_after]['size'])
            if ('freespace' in partition_behind
                    and 'freespace' in partition_after):
                size_free += size_behind + size_after
                partition_list.remove(partition)
                partition_list.remove(partition_after)
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][partition_behind] = {
                    'name': partition_behind,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
            elif 'freespace' in partition_behind:
                size_free += size_behind
                partition_list.remove(partition)
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][partition_behind] = {
                    'name': partition_behind,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
            elif 'freespace' in partition_after:
                size_free += size_after
                partition_list.remove(partition)
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][partition_after] = {
                    'name': partition_after,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
            else:
                free_name = find_next_partition('freespace', partition_list)
                partition_list[store_list_number] = free_name
                disk_data[drive]['partitions'].pop(partition, None)
                disk_data[drive]['partitions'][free_name] = {
                    'name': free_name,
                    'size': size_free,
                    'mount-point': '',
                    'file-system': 'none',
                    'stat': None,
                    'partitions': {},
                    'partition-list': []
                }
                disk_data[drive]['partition-list'] = partition_list
        else:
            free_name = find_next_partition('freespace', partition_list)
            partition_list[store_list_number] = free_name
            disk_data[drive]['partitions'].pop(partition, None)
            disk_data[drive]['partitions'][free_name] = {
                'name': free_name,
                'size': size_free,
                'mount-point': '',
                'file-system': 'none',
                'stat': None,
                'partitions': {},
                'partition-list': []
            }
            disk_data[drive]['partition-list'] = partition_list

        # if delete file exist check if slice is in the list

        if partition not in InstallationData.delete:
            InstallationData.delete.append(partition)

        if "p" in partition and InstallationData.new_partition:
            remaining_partition = []
            for part in partition_list:
                partitions_info = disk_data[drive]['partitions']
                size = partitions_info[part]['size']
                mount_point = partitions_info[part]['mount-point']
                file_system = partitions_info[part]['file-system']
                stat = partitions_info[part]['stat']
                if stat == 'New':
                    remaining_partition.append(f'{file_system} {size} {mount_point}\n')
            InstallationData.new_partition = remaining_partition


class AutoFreeSpace:
    """Class for automatic partition creation in free space.
    
    This class handles automatic partitioning of free space on disks,
    creating appropriate partition layouts for both MBR and GPT schemes
    with support for different filesystems.
    """

    def create_mbr_partiton(self, drive, size, path, fs):
        """Create MBR partitions automatically in free space.
        
        Creates a BSD slice with root and swap partitions.
        
        Args:
            drive (str): Disk device name
            size (str): Available size in MB
            path (list): Path information for partition location
            fs (str): Filesystem type ('ZFS' or 'UFS')
        """
        # remove 1M to size to avoid no space left
        main_size = int(size) - 1
        InstallationData.disk = drive

        InstallationData.scheme = 'partscheme=MBR'

        disk_db = DiskPartition.disk_database
        slice_list = disk_db[drive]['partition-list']
        store_list_number = path[1]
        main_slice = find_next_partition(f'{drive}s', slice_list)
        slice_list[store_list_number] = main_slice
        disk_db[drive]['partitions'][main_slice] = {
            'name': main_slice,
            'size': size,
            'mount-point': 'none',
            'file-system': 'BSD',
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }
        disk_db[drive]['partition-list'] = slice_list

        InstallationData.slice = main_slice.replace(drive, "")

        root_size = int(main_size)
        swap_size = 2048
        root_size -= swap_size

        part_list = disk_db[drive]['partitions'][main_slice]['partition-list']

        if fs == "ZFS":
            layout = zfs_datasets
        else:
            layout = '/'

        root_part = f'{main_slice}a'
        part_list.append(root_part)
        disk_db[drive]['partitions'][main_slice]['partitions'][root_part] = {
            'name': root_part,
            'size': root_size,
            'mount-point': layout,
            'file-system': fs,
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }

        swap_part = f'{main_slice}b'
        part_list.append(swap_part)
        disk_db[drive]['partitions'][main_slice]['partitions'][swap_part] = {
            'name': swap_part,
            'size': swap_size,
            'mount-point': 'none',
            'file-system': 'SWAP',
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }

        disk_db[drive]['partitions'][main_slice]['partition-list'] = part_list

        # Data is already updated in DiskPartition.disk_database - no need to save to file
        
        # Add new partitions to InstallationData
        InstallationData.new_partition = [
            f'{fs} {root_size} {layout}\n',
            f'SWAP {swap_size} none\n'
        ]
        
        # Add to create list for partition creation operations
        InstallationData.create.append([main_slice, main_size])

    def __init__(self, path, size, fs, efi_exist, disk, scheme):
        """Initialize automatic partition creation.
        
        Args:
            path (list): Path information for partition location
            size (str): Available size in MB
            fs (str): Filesystem type ('ZFS' or 'UFS')
            efi_exist (bool): Whether EFI partition already exists
            disk (str): Disk device name
            scheme (str): Partition scheme ('GPT' or 'MBR')
        """
        self.bios_type = bios_or_uefi()
        if scheme == "GPT":
            self.create_gpt_partiton(disk, size, path, fs, efi_exist)
        elif scheme == "MBR":
            self.create_mbr_partiton(disk, size, path, fs)

    def create_gpt_partiton(self, drive, size, path, fs, efi_exist):
        """Create GPT partitions automatically in free space.
        
        Creates boot (if needed), root, and swap partitions with appropriate
        sizing for the target filesystem.
        
        Args:
            drive (str): Disk device name
            size (str): Available size in MB
            path (list): Path information for partition location
            fs (str): Filesystem type ('ZFS' or 'UFS')
            efi_exist (bool): Whether EFI partition already exists
        """
        # remove 1M to size to avoid no space left
        main_size = int(size) - 1
        InstallationData.disk = drive
        InstallationData.scheme = 'partscheme=GPT'
        root_size = int(main_size)
        swap_size = 2048
        root_size -= int(swap_size)
        if self.bios_type == "UEFI" and efi_exist is False:
            boot_size = 256
        else:
            boot_size = 1 if self.bios_type == "BIOS" else 0
        boot_name = 'UEFI' if self.bios_type == "UEFI" else 'BOOT'
        root_size -= boot_size
        disk_data = DiskPartition.disk_database
        partition_list = disk_data[drive]['partition-list']
        store_list_number = path[1]
        if boot_size != 0:
            boot_partition = find_next_partition(f'{drive}p', partition_list)
            partition_list[store_list_number] = boot_partition
            store_list_number += 1
            disk_data[drive]['partitions'][boot_partition] = {
                'name': boot_partition,
                'size': boot_size,
                'mount-point': 'none',
                'file-system': boot_name,
                'stat': 'New',
                'partitions': {},
                'partition-list': []
            }
            # Add boot partition to create list
            InstallationData.create.append([boot_partition, boot_size])

        if fs == "ZFS":
            layout = zfs_datasets
        else:
            layout = '/'

        root_partition = find_next_partition(f'{drive}p', partition_list)
        if store_list_number == path[1]:
            partition_list[store_list_number] = root_partition
        else:
            partition_list.insert(store_list_number, root_partition)
        store_list_number += 1
        disk_data[drive]['partitions'][root_partition] = {
            'name': root_partition,
            'size': root_size,
            'mount-point': layout,
            'file-system': fs,
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }

        InstallationData.slice = root_partition.replace(drive, '')

        swap_partition = find_next_partition(f'{drive}p', partition_list)
        partition_list.insert(store_list_number, swap_partition)
        disk_data[drive]['partitions'][swap_partition] = {
            'name': swap_partition,
            'size': swap_size,
            'mount-point': 'none',
            'file-system': 'SWAP',
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }

        disk_data[drive]['partition-list'] = partition_list
        
        # Data is already updated in DiskPartition.disk_database - no need to save to file
        
        # Add new partitions to InstallationData
        new_partitions = []
        if self.bios_type == "UEFI" and efi_exist is False:
            new_partitions.append(f'UEFI {boot_size} none\n')
        elif self.bios_type == "BIOS":
            new_partitions.append(f'BOOT {boot_size} none\n')
        new_partitions.extend([
            f'{fs} {root_size} {layout}\n',
            f'SWAP {swap_size} none\n'
        ])
        InstallationData.new_partition = new_partitions


class CreateLabel:
    """Class for creating BSD label partitions within MBR slices.
    
    This class handles the creation of individual partitions (labels)
    within BSD slices in MBR partition schemes.
    """
    def __init__(self, path, drive, main_slice, size_left, create_size,
                 mountpoint, fs):
        """Create a new BSD label partition within a slice.
        
        Args:
            path (list): Path information for partition location
            drive (str): Disk device name
            main_slice (str): Parent slice identifier
            size_left (int): Remaining size after partition creation
            create_size (int): Size of new partition in MB
            mountpoint (str): Mount point for the partition
            fs (str): Filesystem type
        """
        InstallationData.disk = drive
        InstallationData.scheme = 'partscheme=MBR'
        InstallationData.slice = main_slice.replace(drive, "")
        disk_db = DiskPartition.disk_database
        store_list_number = path[2]
        part_list = disk_db[drive]['partitions'][main_slice]['partition-list']
        alpha_num = ord('a')
        alpha_num += store_list_number
        letter = chr(alpha_num)
        if fs == "ZFS":
            mountpoint = zfs_datasets

        partition = f'{main_slice}{letter}'
        part_list[store_list_number] = partition
        disk_db[drive]['partitions'][main_slice]['partitions'][partition] = {
            'name': partition,
            'size': create_size,
            'mount-point': mountpoint,
            'file-system': fs,
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }
        if size_left != 0:
            free = find_next_partition('freespace', part_list)
            part_list.append(free)
            disk_db[drive]['partitions'][main_slice]['partitions'][free] = {
                'name': free,
                'size': size_left,
                'mount-point': '',
                'file-system': 'none',
                'stat': None,
                'partitions': {},
                'partition-list': []
            }

        disk_db[drive]['partitions'][main_slice]['partition-list'] = part_list

        # Data is already updated in DiskPartition.disk_database - no need to save to file
        
        # Update InstallationData with new partition information
        new_partitions = []
        for partition_name in part_list:
            drive_part = disk_db[drive]['partitions']
            part_info = drive_part[main_slice]['partitions'][partition_name]
            if part_info['stat'] == 'New':
                partition_text = f'{part_info["file-system"]} ' \
                    f'{part_info["size"]} ' \
                    f'{part_info["mount-point"]}\n'
                new_partitions.append(partition_text)
        
        InstallationData.new_partition = new_partitions


# class modifyLabel():

#     def __init__(self, path, size_left, create_size, mount_point, fs,
#                  data, disk):
#         if not os.path.exists(disk_file):
#             file_disk = open(disk_file, 'w')
#             file_disk.writelines('%s\n' % disk)
#             file_disk.close()
#         sl = path[1] + 1
#         lv = path[2]
#         write_scheme = open(scheme_file, 'w')
#         write_scheme.writelines('partscheme=MBR')
#         write_scheme.close()
#         write_slice = open(slice_file, 'w')
#         write_slice.writelines('s%s\n' % sl)
#         write_slice.close()
#         alph = ord('a')
#         alph += lv
#         letter = chr(alph)
#         llist = []
#         mllist = label_query(disk + 's%s' % sl)
#         plf = open(partitiondb + disk + 's%s' % sl, 'wb')
#         if size_left == 0:
#             create_size -= 1
#         llist.extend(([disk + 's%s' % sl + letter, create_size, mount_point,
#                       fs]))
#         mllist[lv] = llist
#         llist = []
#         if size_left > 0:
#             llist.extend((['freespace', size_left, '', '']))
#             mllist.append(llist)
#         pickle.dump(mllist, plf)
#         plf.close()
#         llist = open(partitiondb + disk + 's%s' % sl, 'rb')
#         sabeltlist = pickle.load(llist)
#         write_partition = open(partition_label_file, 'w')
#         for partlist in sabeltlist:
#             if partlist[2] != '':
#                 write_partition.writelines('%s %s %s\n' % (partlist[3],
#                                            partlist[1], partlist[2]))
#         write_partition.close()


class CreateSlice:
    """Class for creating MBR slices (BSD partitions).
    
    This class handles the creation of BSD slices within MBR partition
    schemes, which can then contain multiple BSD label partitions.
    """

    def __init__(self, create_size, size_left, path, drive):
        """Create a new MBR slice.
        
        Args:
            create_size (int): Size of new slice in MB
            size_left (int): Remaining size after slice creation
            path (list): Path information for slice location
            drive (str): Disk device name
        """
        InstallationData.disk = drive
        InstallationData.scheme = 'partscheme=MBR'

        disk_db = DiskPartition.disk_database
        store_list_number = path[1]
        partition_list = disk_db[drive]['partition-list']

        partition = find_next_partition(f'{drive}s', partition_list)

        partition_list[store_list_number] = partition
        # Store slice partition
        disk_db[drive]['partitions'][partition] = {
            'name': partition,
            'size': create_size,
            'mount-point': 'none',
            'file-system': 'BSD',
            'stat': 'New',
            'partitions': {},
            'partition-list': ['freespace1']
        }
        # Store freespace for partition partition
        disk_db[drive]['partitions'][partition]['partitions']['freespace1'] = {
            'name': 'freespace1',
            'size': create_size,
            'mount-point': '',
            'file-system': 'none',
            'stat': None,
            'partitions': {},
            'partition-list': []
        }
        # Store freespace if some left
        if size_left != 0:
            free_name = find_next_partition('freespace', partition_list)
            partition_list.append(free_name)
            disk_db[drive]['partitions'][free_name] = {
                'name': free_name,
                'size': size_left,
                'mount-point': '',
                'file-system': 'none',
                'stat': None,
                'partitions': {},
                'partition-list': []
            }

        disk_db[drive]['partition-list'] = partition_list

        # Data is already updated in DiskPartition.disk_database - no need to save to file

        InstallationData.slice = partition.replace(drive, '')

        # Add to create list for partition creation operations
        InstallationData.create.append([partition, create_size])


class CreatePartition():
    """Class for creating GPT partitions.
    
    This class handles the creation of individual partitions within
    GPT partition schemes, supporting various filesystem types and
    mount points.
    """
    def __init__(self, path, drive, size_left, create_size, mount_point, fs):
        """Create a new GPT partition.
        
        Args:
            path (list): Path information for partition location
            drive (str): Disk device name
            size_left (int): Remaining size after partition creation
            create_size (int): Size of new partition in MB
            mount_point (str): Mount point for the partition
            fs (str): Filesystem type
        """
        InstallationData.disk = drive

        InstallationData.scheme = 'partscheme=GPT'

        if fs == "ZFS":
            mount_point = zfs_datasets

        disk_data = DiskPartition.disk_database
        store_list_number = path[1]
        partition_list = disk_data[drive]['partition-list']

        partition = find_next_partition(f'{drive}p', partition_list)

        partition_list[store_list_number] = partition
        # Store slice partition
        disk_data[drive]['partitions'][partition] = {
            'name': partition,
            'size': create_size,
            'mount-point': mount_point,
            'file-system': fs,
            'stat': 'New',
            'partitions': {},
            'partition-list': []
        }
        # Store freespace if some left
        if size_left != 0:
            free_name = find_next_partition('freespace', partition_list)
            partition_list.append(free_name)
            disk_data[drive]['partitions'][free_name] = {
                'name': free_name,
                'size': size_left,
                'mount-point': '',
                'file-system': 'none',
                'stat': None,
                'partitions': {},
                'partition-list': []
            }

        disk_data[drive]['partition-list'] = partition_list

        # Data is already updated in DiskPartition.disk_database - no need to save to file

        if mount_point == '/' or fs == "ZFS":
            InstallationData.slice = partition.replace(drive, '')

        if fs == "UEFI" or fs == "BOOT":
            # Add to create list for partition creation operations
            InstallationData.create.append([partition, create_size])

        # Update InstallationData with new partition information
        new_partitions = []
        for partition_name in partition_list:
            partition_info = disk_data[drive]['partitions'][partition_name]
            if partition_info['stat'] == 'New':
                partition_text = f'{partition_info["file-system"]} ' \
                    f'{partition_info["size"]} ' \
                    f'{partition_info["mount-point"]}\n'
                new_partitions.append(partition_text)

        InstallationData.new_partition = new_partitions


def delete_partition():
    """Execute physical deletion of partitions marked for deletion.
    
    Iterates through partitions marked for deletion in InstallationData
    and removes them from the disk using FreeBSD gpart commands.
    
    Raises:
        RuntimeError: If no partitions are marked for deletion
    """
    if InstallationData.delete:
        for partition in InstallationData.delete:
            num = slice_number(partition)
            drive = get_disk_from_partition(partition)
            call(f"sudo zpool labelclear -f {partition}", shell=True)
            sleep(1)
            call(f'sudo gpart delete -i {num} {drive}', shell=True)
            sleep(1)
    else:
        raise RuntimeError('No partitions to delete')


def destroy_partition():
    """Destroy and recreate partition tables on disks.
    
    Completely destroys existing partition tables and creates new ones
    with the specified scheme for disks marked for destruction.
    
    Raises:
        RuntimeError: If no disks are marked for destruction
    """
    if InstallationData.destroy:
        for drive, scheme in InstallationData.destroy.items():
            # Destroy the disk geom
            gpart_destroy = f"sudo gpart destroy -F {drive}"
            call(gpart_destroy, shell=True)
            sleep(1)
            clear_drive = f"sudo dd if=/dev/zero of={drive} bs=1m count=1"
            call(clear_drive, shell=True)
            sleep(1)
            call(f'sudo gpart create -s {scheme} {drive}', shell=True)
            sleep(1)
    else:
        raise RuntimeError('No disks to destroy')


def bios_or_uefi():
    """Detect the system boot method (BIOS or UEFI).
    
    Returns:
        str: 'BIOS' or 'UEFI' depending on the system boot method
    """
    cmd = "sysctl -n machdep.bootmethod"
    output1 = Popen(cmd, shell=True, stdout=PIPE,
                    universal_newlines=True, close_fds=True)
    return output1.stdout.readlines()[0].rstrip()


def add_partition():
    """Execute physical creation of partitions marked for creation.
    
    Creates actual partitions on disk using FreeBSD gpart commands
    for all partitions marked for creation in InstallationData.
    Handles different partition types (EFI, BIOS boot, FreeBSD, etc.).
    
    Raises:
        RuntimeError: If no partitions are marked for creation
    """
    if InstallationData.create:
        boot = InstallationData.boot
        for partition_info in InstallationData.create:
            part = partition_info[0]
            size = int(partition_info[1])
            drive = get_disk_from_partition(part)
            sl = slice_number(part)
            if set("p") & set(part):
                if bios_or_uefi() == 'UEFI':
                    cmd = f'sudo gpart add -a 4k -s {size}M -t efi ' \
                        f'-i {sl} {drive}'
                    call(cmd, shell=True)
                    sleep(1)
                    call(f'sudo zpool labelclear -f {drive}p{sl}', shell=True)
                    cmd2 = f'sudo newfs_msdos -F 16 {drive}p{sl}'
                    call(cmd2, shell=True)
                else:
                    if boot == "grub":
                        cmd = f'sudo gpart add -a 4k -s {size}M -t ' \
                            'bios-boot -i {sl} {drive}'
                    else:
                        # freebsd-boot partition must never be larger
                        # than 512B blocks.
                        cmd = 'sudo gpart add -a 4k -s 512 -t ' \
                            f'freebsd-boot -i {sl} {drive}'
                    call(cmd, shell=True)
                    call(f'sudo zpool labelclear -f {drive}p{sl}', shell=True)
            elif set("s") & set(part):
                cmd = f'sudo gpart add -a 4k -s {size}M -t freebsd ' \
                    f'-i {sl} {drive}'
                call(cmd, shell=True)
            sleep(2)
    else:
        raise RuntimeError('No partitions to create')
