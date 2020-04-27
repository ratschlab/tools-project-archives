import sys


def terminate_if_path_nonexistent(path):
    if not path.exists():
        terminate_with_message("No such file or directory: " + get_absolute_path_string(path))


def terminate_if_path_not_file_of_type(path, file_type):
    if not path.is_file():
        terminate_with_message("No such file: " + get_absolute_path_string(path))

    # Combine all suffixes to one string
    suffix_list = path.suffixes
    complete_suffix_string = "".join(suffix_list)

    if not complete_suffix_string == file_type:
        terminate_with_message("File does not have suffix " + file_type + " : " + path.absolute().as_posix())


def terminate_if_partent_directory_nonexistent(path):
    # Make sure path is absolute
    absolute_path = path.absolute()
    parent_directory = output_directory_path.parents[0]

    terminate_if_directory_nonexistent(parent_directory)


def terminate_if_directory_nonexistent(path):
    if not path.is_dir():
        terminate_with_message("No such directory: " + get_absolute_path_string(path))


def get_absolute_path_string(path):
    return path.absolute().as_posix()


def terminate_with_message(message):
    sys.exit(message)
