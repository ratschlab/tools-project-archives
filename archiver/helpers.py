import sys
import os
import hashlib


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

    hasher = hashlib.md5()

    with open(file_path, "rb") as read_file:
        buffer = read_file.read()
        hasher.update(buffer)

    hash_file = open(file_path.as_posix() + ".md5", "w")
    hash_file.write(hasher.hexdigest())
