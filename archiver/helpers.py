import sys
import os
import hashlib
from pathlib import Path
import subprocess


def terminate_if_path_nonexistent(path):
    if not path.exists():
        terminate_with_message(f"No such file or directory: {get_absolute_path_string(path)}")


def terminate_if_path_not_file_of_type(path, file_type):
    if not path.is_file():
        terminate_with_message(f"No such file: {get_absolute_path_string(path)}")

    # Combine all suffixes to one string
    suffix_list = path.suffixes
    complete_suffix_string = "".join(suffix_list)

    if not complete_suffix_string == file_type:
        terminate_with_message(f"File does not have suffix {file_type}: {get_absolute_path_string(path)}")


def terminate_if_parent_directory_nonexistent(path):
    # Make sure path is absolute
    absolute_path = path.absolute()
    parent_directory = absolute_path.parents[0]

    terminate_if_directory_nonexistent(parent_directory)


def terminate_if_directory_nonexistent(path):
    if not path.is_dir():
        terminate_with_message(f"No such directory: {get_absolute_path_string(path)}")


def terminate_if_path_exists(path):
    if path.exists():
        terminate_with_message(f"Path must not exist: {get_absolute_path_string(path)}")


def get_file_with_type_in_directory_or_terminate(directory, file_type):
    archives_in_directory = []

    for file in os.listdir(directory):
        if file.endswith(file_type):
            path = directory.joinpath(file).absolute()
            archives_in_directory.append(path)

    if len(archives_in_directory) > 1:
        terminate_with_message(f"Multiple files of type {file_type} found, please specify file path")

    if len(archives_in_directory) == 0:
        terminate_with_message(f"No archive found in directory: {get_absolute_path_string(directory)}")

    return archives_in_directory[0]


def get_absolute_path_string(path):
    return path.absolute().as_posix()


def terminate_with_message(message):
    sys.exit(message)


def create_and_write_file_hash(file_path):
    """ Will save the file in same directory """

    hash_output = file_hash_from_path(file_path)

    hash_file = open(file_path.as_posix() + ".md5", "w")
    hash_file.write(hash_output)


def file_hash_from_path(file_path):
    hasher = hashlib.md5()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def hash_listing_for_files_in_folder(source_path):
    hashes_list = []
    for root, _, files in os.walk(source_path):
        for file in files:
            reative_path_to_file_string = Path(root).relative_to(source_path.parent).joinpath(file).as_posix()
            # TODO: Switch to Pathlib
            file_hash = file_hash_from_path(os.path.join(root, file))

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


def get_size_of_path(path):
    if path.is_dir():
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

    return path.stat().st_size


def get_sorted_listing(directory_path, sort_order):
    dir_listing = os.listdir(directory_path)

    return sorted(dir_listing, key=lambda e: get_size_of_path(directory_path.joinpath(e)), reverse=sort_order)
