import re
import sys
import os
import hashlib
from pathlib import Path
import subprocess
import logging
import shutil
import multiprocessing
from typing import List, Union, Sequence
import unicodedata

from .constants import READ_CHUNK_BYTE_SIZE, COMPRESSED_ARCHIVE_SUFFIX, \
    ENCRYPTED_ARCHIVE_SUFFIX, ENV_VAR_MAPPER_MAX_CPUS, MD5_LINE_REGEX


def get_files_with_type_in_directory_or_terminate(directory, file_type):
    files = get_files_with_type_in_directory(directory, file_type)

    if not files:
        error = LookupError(f"No files of type {file_type} found.")
        terminate_with_exception(error)

    return files


def get_files_with_type_in_directory(directory, file_type):
    files = []

    for file in os.listdir(directory):
        if file.endswith(file_type):
            path = directory.joinpath(file).absolute()
            files.append(path)

    return sorted(files)


def get_absolute_path_string(path):
    return path.absolute().as_posix()


def create_and_write_file_hash(file_path):
    """Will save the file in same directory"""

    hash_output = get_file_hash_from_path(file_path)

    with open(file_path.as_posix() + ".md5", "w") as hash_file:
        hash_file.write(f"{hash_output}  {file_path.name}\n")


def read_file_listing(file_path):

    listing = []

    with open(file_path, "r", newline='\n') as file:
        for file_path in file.readlines():
            file_path = file_path.strip('\n')
            if file_path.startswith('\\'):
                # reverse of archive.create_file_listing_hash
                file_path = file_path[1:]
                # following https://stackoverflow.com/questions/1885181/how-to-un-escape-a-backslash-escaped-string
                file_path = file_path.encode('latin-1', 'backslashreplace').decode('unicode_escape')
            listing.append(Path(file_path))

    return listing


def read_hash_file(file_path):
    hash_dict = {}

    with open(file_path, "r", newline='\n') as file:
        for l in file.readlines():
            m = MD5_LINE_REGEX.match(l)

            if not m:
                logging.error(
                    f"Not properly formatted MD5 checksum line found in file {file_path}: {l}")
                return False

            hash_val = m.groups()[0]

            path = m.groups()[1]
            path = path[2:] if path.startswith('./') else path

            if hash_val.startswith('\\'):
                # reverse of archive.create_file_listing_hash
                hash_val = hash_val[1:]
                # following https://stackoverflow.com/questions/1885181/how-to-un-escape-a-backslash-escaped-string
                path = path.encode('latin-1', 'backslashreplace').decode('unicode_escape')

            hash_dict[path] = hash_val
    return hash_dict


def get_file_hash_from_path(file_path):
    if file_path.is_symlink():
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


def _check_symlinks(abs_file, relative_to_path, integrity_check=False):
    if not abs_file.is_symlink():
        return

    link = Path(os.readlink(abs_file))

    if integrity_check:
        if link.is_absolute():
            logging.warning(
                f"Symlink {abs_file.relative_to(relative_to_path.parent)} found pointing to {str(link)} ."
                f" The archive contains the link itself, but possibly not the file it points to.")
        # if the link is relative, check existence in a later step using file listings
    else:
        # archiving
        absolute_root = relative_to_path.resolve().absolute()
        if absolute_root not in abs_file.resolve().parents:
            logging.warning(
                f"Symlink with outside target {abs_file.relative_to(relative_to_path.parent)} found pointing to {abs_file.resolve()} "
                f"which is outside the archiving directory {relative_to_path.resolve().absolute()}."
                f" The archive will contain the link itself, but not the file it points to.")
        elif not abs_file.resolve().exists():
            logging.warning(
                f"Broken symlink {abs_file.relative_to(relative_to_path.parent)} found pointing to a non-existing file {abs_file.resolve()} ."
                f" The archive will only contain the link itself")
        elif link.is_absolute():
            # target exists and is within tree to be archived, however, link is absolute,
            # so will be broken if unpacked on another system
            logging.warning(f"Absolute symlink {abs_file.relative_to(relative_to_path.parent)} found with target {link} . "
                            f" Consider making it a relative link to {relative_to_path} s.t. it gets properly "
                            f"resolved when unpacking the archive on another system.")


def hash_files_and_check_symlinks(source_path, abs_paths, max_workers=1, integrity_check=False):
    # ignoring other file types like FIFO, sockets etc
    file_list = [f for f in abs_paths if f.is_symlink() or f.is_file()]

    [_check_symlinks(f, source_path, integrity_check=integrity_check) for f in file_list]

    hashes_list = exec_parallel(get_file_hash_from_path, file_list, lambda f: (f,), max_workers)

    return [[unicodedata.normalize('NFC', e[0].relative_to(source_path.parent).as_posix()), e[1]] for e
            in zip(file_list, hashes_list)]


def get_files_in_folder(folder_path, include_dirs=False):
    listing = []
    for root, dirs, files in os.walk(folder_path):
        root_path = Path(root)
        for file in files:
            abs_file = root_path.joinpath(file)
            listing.append(abs_file)
        dirs_ = []
        for dir in dirs:
            abs_dir = root_path.joinpath(dir)
            if Path(abs_dir).is_symlink():
                listing.append(abs_dir)
            else:
                if include_dirs:
                    listing.append(abs_dir)
                dirs_.append(dir)
        dirs[:] = dirs_

    return listing


def get_threads_from_args_or_environment(threads_arg):
    if threads_arg:
        return threads_arg

    threads = get_number_of_threads()
    logging.info(f"Number of threads is not set, using {threads} threads")
    return threads


def get_number_of_threads():
    number_of_threads_from_env = get_number_of_threads_from_env()

    if not number_of_threads_from_env:
        return get_max_number_of_threads()

    return number_of_threads_from_env


def get_number_of_threads_from_env():
    env_variable_name = os.environ.get(ENV_VAR_MAPPER_MAX_CPUS)

    if not env_variable_name:
        logging.debug(f"Environment variable {ENV_VAR_MAPPER_MAX_CPUS} is not set")
        return None

    env_variable_threads = os.environ.get(env_variable_name)

    if not env_variable_threads:
        logging.debug(
            f"Environment variable {env_variable_name} is not set")
        return None

    env_variable_threads_number = None
    try:
        env_variable_threads_number = int(env_variable_threads)
    except ValueError:
        pass

    if not env_variable_threads_number:
        logging.warning(f"Environment variable {env_variable_name} doesn't contain a valid number of threads")
        return

    return env_variable_threads_number


def get_max_number_of_threads():
    return multiprocessing.cpu_count()


def get_uncompressed_archive_size_in_bytes(archive_file_path):
    # Not providing the option to manually specify number of threads to keep the API simple
    threads_argument = ["--threads", str(get_number_of_threads())]

    try:
        # Using
        sp = run_shell_cmd(["plzip", "-l", archive_file_path] + threads_argument)
        return int(sp.stdout.decode("utf-8").splitlines()[-1].lstrip().split(' ', 1)[0])
    except subprocess.CalledProcessError:
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

    return get_size_of_file(path)


def get_size_of_file(path):
    if not path.is_file():
        raise ValueError(f"Path {get_absolute_path_string(path)} must be a file.")

    return path.stat().st_size


def get_size_of_directory(path, deep=False):
    if deep:
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

    command = ["du", "-shb", '"' + str(path) + '"' ] if plattform_is_linux() else ["du", "-sh", '"' + str(path) + '"' ]

    parsed_output = run_shell_cmd(command).stdout.decode("utf-8")

    dir_size = re.split(r'\t+', parsed_output.lstrip())[0]

    try:
        return int(dir_size)
    except ValueError:
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
        raise ValueError(f"Unable to parse provided size string {size_string}. Specify file size with unit, for example: 5G for 5 gigibytes (2^30 bytes).")


def file_has_type(path, file_type):
    return path.is_file() and path.as_posix().endswith(file_type)


def add_suffix_to_path(path, suffix):
    return path.parent / (path.name + suffix)


def replace_suffix_of_path(path, new_suffix):
    return path.parent / (path.stem.split('.')[0] + new_suffix)


def path_target_is_encrypted(path):
    if path.is_dir():
        return archive_is_encrypted(path)

    return file_has_type(path, ENCRYPTED_ARCHIVE_SUFFIX)


def archive_is_encrypted(archive_path):
    # We'll assume archive is encrypted if there are any encrypted files
    return get_files_with_type_in_directory(archive_path, ENCRYPTED_ARCHIVE_SUFFIX)


def get_archives_from_path(path, is_encrypted):
    if path.is_dir():
        archive_suffix = ENCRYPTED_ARCHIVE_SUFFIX if is_encrypted else COMPRESSED_ARCHIVE_SUFFIX
        return get_files_with_type_in_directory(path, archive_suffix)

    file_is_valid_archive_or_terminate(path)
    return [path]


def file_is_valid_archive_or_terminate(file_path):
    if not (file_has_type(file_path, COMPRESSED_ARCHIVE_SUFFIX) or file_has_type(file_path, ENCRYPTED_ARCHIVE_SUFFIX)):
        terminate_with_message(f"File {file_path.as_posix()} is not a valid archive of type {COMPRESSED_ARCHIVE_SUFFIX} or {ENCRYPTED_ARCHIVE_SUFFIX} or doesn't exist.")


def filename_without_extensions(path):
    """Removes every suffix, including .partX"""
    suffixes_string = "".join(path.suffixes)

    return path.name[:-len(suffixes_string)]


def filepath_without_extensions(path:Path) -> Path:
    """Removes every suffix, including .partX"""
    suffixes_string = "".join(path.suffixes)

    return path.parent / path.name[:-len(suffixes_string)]

def infer_source_name(source_path: Path) -> Path:

    if not source_path.is_dir():
        return filepath_without_extensions(source_path)
    else:
        all_files = [p for p in source_path.iterdir() if p.is_file()]
        unique_names = list(set([filepath_without_extensions(f) for f in all_files]))

        if len(unique_names) == 0:
            terminate_with_message('There are no archive files present')
        elif len(unique_names) > 1:
            terminate_with_message(f'More than one possible archive name detected: {str(unique_names)}')

        return unique_names[0]


def filename_without_archive_extensions(path):
    """Removes known archive extensions but keeps extensions like .partX"""
    name = path.name

    if name.endswith(ENCRYPTED_ARCHIVE_SUFFIX):
        return name[:-len(ENCRYPTED_ARCHIVE_SUFFIX)]

    if name.endswith(COMPRESSED_ARCHIVE_SUFFIX):
        return name[:-len(COMPRESSED_ARCHIVE_SUFFIX)]

    raise ValueError("Unknown file extension")


def sort_paths_with_part(paths: Sequence[Path]) -> List[Path]:
    part_re = re.compile(r'.*\.part([0-9]+)\.')
    def extract_part(p):
        m = part_re.match(p.name)

        if m:
            return int(m.groups()[0])
        return 0

    return sorted(paths, key=extract_part)


def get_parts(source_path: Path) -> int:

    parts_file = list(source_path.glob('*.parts.txt'))
    if len(parts_file) > 1:
        terminate_with_message(f'More than 1 file (total {len(parts_file)}) are matching the pattern *.parts.txt')
    if parts_file:
        with open(parts_file[0], 'r') as pf:
           parts = int(pf.readline().strip())
    else:
        parts = 0

    return parts

def list_files_matching_name(path: Path, regex) -> List[Path]:
    return [p for p in path.iterdir() if p.is_file() and regex.match(p.name)]


def handle_destination_directory_creation(destination_path, force=False):
    if not destination_path.exists() and destination_path.parent.exists():
        destination_path.mkdir()
        return

    if force and destination_path.exists():
        logging.warning("Deleting existing directory: " + get_absolute_path_string(destination_path))
        shutil.rmtree(destination_path)

    if force:
        destination_path.mkdir(parents=True)
        return

    if not destination_path.parent.exists():
        terminate_with_message(f"Directory {get_absolute_path_string(destination_path.parent)} must exist. Use --force to automatically create missing parents")
        return

    terminate_with_message(f"Path {get_absolute_path_string(destination_path)} must not exist. Use --force to override")


# MARK: Termination helpers


def terminate_if_parent_directory_nonexistent(path):
    # Make sure path is absolute
    absolute_path = path.absolute()
    parent_directory = absolute_path.parents[0]

    terminate_if_directory_nonexistent(parent_directory)


def terminate_if_path_not_file_of_type(path, file_type):
    if not file_has_type(path, file_type):
        terminate_with_message(f"Must of be of type {file_type}: {get_absolute_path_string(path)}")


def terminate_if_path_nonexistent(path):
    if not path.exists():
        terminate_with_message(f"No such file or directory: {get_absolute_path_string(path)}")


def terminate_if_directory_nonexistent(path):
    if not path.is_dir():
        terminate_with_message(f"No such directory: {get_absolute_path_string(path)}")


def terminate_if_file_nonexistent(path):
    if not path.is_file():
        terminate_with_message(f"No such file: {get_absolute_path_string(path)}")

def terminate_if_files_nonexistent(paths):
    files = ';'.join([str(get_absolute_path_string(path)) for path in paths])
    if not min([_.is_file() for _ in paths]):
        terminate_with_message(f"None of the files exist: {files}")

def terminate_if_path_exists(path):
    if path.exists():
        terminate_with_message(f"Path must not exist: {get_absolute_path_string(path)}")


def terminate_with_exception(exception):
    terminate_with_message(str(exception))


def terminate_with_message(message):
    logging.error(message)
    sys.exit(1)


def encryption_keys_must_exist(key_list):
    for key in key_list:
        terminate_if_file_nonexistent(Path(key))


def run_shell_cmd(cmd: Union[str, List], file_output: Path = None, pipe_stdout=False, check_returncode=True):
    if isinstance(cmd, list):
        cmd_str = ' '.join([str(e) for e in cmd])
    else:
        cmd_str = cmd

    logging.debug(f"Executing command: '{cmd_str}'")

    try:
        if file_output:
            with open(file_output, "w") as f:
                return subprocess.run(cmd_str, stdout=f, stderr=subprocess.STDOUT, shell=True, check=check_returncode)
        elif pipe_stdout:
            return subprocess.run(cmd_str, stdout=subprocess.PIPE, shell=True, check=check_returncode)
        else:
            return subprocess.run(cmd_str, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, shell=True, check=check_returncode)
    except subprocess.CalledProcessError as e:
        logging.exception(e)
        logging.error(f"subprocess stdout was: {e.stdout.decode() if e.stdout else '<empty>'}")
        logging.error(f"subprocess stderr was: {e.stderr.decode() if e.stderr else '<empty>'}")
        raise(e)


def exec_parallel(fnc, loop_var, args_fnc, threads):
    args = [args_fnc(l) for l in loop_var]
    if threads == 1:
        # if only one thread, don't invoke multiprocessing in order to avoid potential issues
        return [fnc(*a) for a in args]
    else:
        with multiprocessing.Pool(threads) as pool:
            # using starmap instead of map with lambdas taking a loop parameter
            # and invoking the function of interest in order to avoid serialization issues
            # with multiprocessing
            return pool.starmap(fnc, args)
