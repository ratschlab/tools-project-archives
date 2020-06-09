import re
import sys
import os
import hashlib
from pathlib import Path
import subprocess

from .constants import READ_CHUNK_BYTE_SIZE


def get_all_files_with_type_in_directory(directory, file_type):
    files = get_files_with_type_in_directory(directory, file_type)

    if not files:
        raise LookupError(f"Multiple files of type {file_type} found, please specify file path")

    return files


def get_files_with_type_in_directory(directory, file_type):
    files = []

    for file in os.listdir(directory):
        if file.endswith(file_type):
            path = directory.joinpath(file).absolute()
            files.append(path)

    return files


def get_absolute_path_string(path):
    return path.absolute().as_posix()


def create_and_write_file_hash(file_path):
    """ Will save the file in same directory """

    hash_output = get_file_hash_from_path(file_path)

    hash_file = open(file_path.as_posix() + ".md5", "w")
    hash_file.write(hash_output)


def get_file_hash_from_path(file_path):
    if file_path.is_symlink():
        print(f"WARNING: Symlink {file_path.name} found. The link itself will be archived and hashed but not the files that it points to.")
        return get_symlink_path_hash(file_path)

    hasher = hashlib.md5()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(READ_CHUNK_BYTE_SIZE), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_symlink_path_hash(symlink_path):
    hasher = hashlib.md5()
    encoded_text_symlink = os.readlink(symlink_path).encode("utf-8")
    hasher.update(encoded_text_symlink)

    return hasher.hexdigest()


def hash_listing_for_files_in_folder(source_path, relative_to_path=None):
    if not relative_to_path:
        relative_to_path = source_path.parent

    hashes_list = []
    for root, _, files in os.walk(source_path):
        root_path = Path(root)
        for file in files:
            reative_path_to_file_string = root_path.relative_to(relative_to_path).joinpath(file).as_posix()
            file_hash = get_file_hash_from_path(root_path.joinpath(file))

            hashes_list.append([reative_path_to_file_string, file_hash])

    return hashes_list


def get_uncompressed_archive_size_in_bytes(archive_file_path):
    try:
        output = subprocess.check_output(["plzip", "-l", archive_file_path])
        return int(output.decode("utf-8").splitlines()[-1].lstrip().split(' ', 1)[0])
    except:
        terminate_with_message("Failed to fetch uncompressed archive size.")


def get_device_available_capacity_from_path(path):
    fs_stats = os.statvfs(path)
    return fs_stats.f_frsize * fs_stats.f_bavail


def get_sorted_listing(directory_path, sort_order):
    dir_listing = os.listdir(directory_path)

    return sorted(dir_listing, key=lambda e: get_size_of_path(directory_path.joinpath(e)), reverse=sort_order)


def get_size_of_path(path):
    if path.is_dir():
        return get_size_of_directory(path)

    return path.stat().st_size


def get_size_of_directory(path, deep=False):
    if deep:
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

    try:
        command = ["du", "-shb", path] if plattform_is_linux() else ["du", "-sh", path]
        parsed_output = subprocess.check_output(command).decode("utf-8")

        dir_size = re.split(r'\t+', parsed_output.lstrip())[0]

        return int(dir_size)
    except:
        return get_bytes_in_string_with_unit(dir_size)


def plattform_is_linux():
    return sys.platform == "linux" or sys.platform == "linux2"


units = {"B": 1, "KB": 2**10, "K": 2**10, "MB": 2**20, "M": 2**20, "GB": 2**30, "G": 2**30, "TB": 2**40, "T": 2**40}


def get_bytes_in_string_with_unit(size_string):
    size = size_string.upper()

    try:
        if not re.match(r' ', size):
            size = re.sub(r'([KMGT]?B|[KMGT])', r' \1', size)

        number, unit = [string.strip() for string in size.split()]
        return int(float(number)*units[unit])
    except:
        raise ValueError("Unable to parse provided size string: " + size_string)


# MARK: Termination helpers

def terminate_if_parent_directory_nonexistent(path):
    # Make sure path is absolute
    absolute_path = path.absolute()
    parent_directory = absolute_path.parents[0]

    terminate_if_directory_nonexistent(parent_directory)


def terminate_if_path_not_file_of_type(path, file_type):
    if not path.is_file():
        terminate_with_message(f"Must of be of type {file_type}: {get_absolute_path_string(path)}")


def terminate_if_path_nonexistent(path):
    if not path.exists():
        terminate_with_message(f"No such file or directory: {get_absolute_path_string(path)}")


def terminate_if_directory_nonexistent(path):
    if not path.is_dir():
        terminate_with_message(f"No such directory: {get_absolute_path_string(path)}")


def terminate_if_path_exists(path):
    if path.exists():
        terminate_with_message(f"Path must not exist: {get_absolute_path_string(path)}")


def terminate_with_exception(exception):
    terminate_with_message(str(exception))


def terminate_with_message(message):
    sys.exit(message)
