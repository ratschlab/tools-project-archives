import os
import subprocess
import hashlib
from pathlib import Path
import logging
import tempfile
import shutil

from . import helpers
from . import splitter
from .encryption import encrypt_list_of_archives
from .constants import COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX


def encrypt_existing_archive(archive_path, encryption_keys, remove_unencrypted=False):
    helpers.encryption_keys_must_exist(encryption_keys)

    if archive_path.is_dir():
        if helpers.get_files_with_type_in_directory(archive_path, ENCRYPTED_ARCHIVE_SUFFIX):
            helpers.terminate_with_message("Encrypted archvies present. Doing nothing.")

        archive_files = helpers.get_files_with_type_in_directory_or_terminate(archive_path, COMPRESSED_ARCHIVE_SUFFIX)

        encrypt_list_of_archives(archive_files, encryption_keys, remove_unencrypted)
        return

    helpers.terminate_if_path_not_file_of_type(archive_path, COMPRESSED_ARCHIVE_SUFFIX)

    logging.info("Start encryption of existing archive " + helpers.get_absolute_path_string(archive_path))
    encrypt_list_of_archives([archive_path], encryption_keys, remove_unencrypted)


def create_archive(source_path, destination_path, threads=None, encryption_keys=None, compression=6, splitting=None, remove_unencrypted=False):
    # Argparse already checks if arguments are present, so only argument format needs to be validated
    helpers.terminate_if_path_nonexistent(source_path)
    # Check if destination parent directory exist but not actual directory
    helpers.terminate_if_parent_directory_nonexistent(destination_path)
    helpers.terminate_if_path_exists(destination_path)

    if encryption_keys:
        helpers.encryption_keys_must_exist(encryption_keys)

    source_name = source_path.name

    logging.info(f"Start creating archive for: {helpers.get_absolute_path_string(source_path)}")

    destination_path.mkdir()

    if splitting:
        create_split_archive(source_path, destination_path, source_name, int(splitting), threads, encryption_keys, compression, remove_unencrypted)
    else:
        logging.info("Create and write hash list...")
        create_file_listing_hash(source_path, destination_path, source_name)

        logging.info("Create tar archive...")
        create_tar_archive(source_path, destination_path, source_name)
        create_and_write_archive_hash(destination_path, source_name)
        create_archive_listing(destination_path, source_name)

        logging.info("Starting compression...")
        compress_using_lzip(destination_path, source_name, threads, compression)
        create_and_write_compressed_archive_hash(destination_path, source_name)

        if encryption_keys:
            logging.info("Starting encryption...")
            archive_list = [destination_path.joinpath(source_name + COMPRESSED_ARCHIVE_SUFFIX)]
            encrypt_list_of_archives(archive_list, encryption_keys, remove_unencrypted)

    logging.info(f"Archive created: {helpers.get_absolute_path_string(destination_path)}")


def create_split_archive(source_path, destination_path, source_name, splitting, threads, encryption_keys, compression, remove_unencrypted):
    logging.info("Start creation of split archive")
    split_archives = splitter.split_directory(source_path, splitting)

    for index, archive in enumerate(split_archives):
        source_part_name = f"{source_name}.part{index + 1}"

        logging.info(f"Create and write hash list of part {index + 1}...")
        create_file_listing_hash(source_path, destination_path, source_part_name, archive)

        logging.info(f"Create tar archive part {index + 1}...")
        create_tar_archive(source_path, destination_path, source_part_name, archive)
        create_and_write_archive_hash(destination_path, source_part_name)
        create_archive_listing(destination_path, source_part_name)

        logging.info(f"Starting compression of part {index + 1}...")
        compress_using_lzip(destination_path, source_part_name, threads, compression)
        create_and_write_compressed_archive_hash(destination_path, source_part_name)

        if encryption_keys:
            logging.info(f"Starting encryption of part {index + 1}...")
            archive_list = [destination_path.joinpath(source_part_name + COMPRESSED_ARCHIVE_SUFFIX)]
            encrypt_list_of_archives(archive_list, encryption_keys, remove_unencrypted)


def create_file_listing_hash(source_path, destination_path, source_name, archive_list=None):
    if archive_list:
        paths_to_hash_list = archive_list
    else:
        paths_to_hash_list = [source_path]

    hashes = hashes_for_path_list(paths_to_hash_list, source_path.parent)
    file_path = destination_path.joinpath(source_name + ".md5")

    with open(file_path, "a") as hash_file:
        for line in hashes:
            file_path = line[0]
            file_hash = line[1]

            hash_file.write(f"{file_hash} {file_path}\n")


def hashes_for_path_list(path_list, parent_path):
    hash_list = []

    for path in path_list:
        if path.is_dir():
            hashes = helpers.hash_listing_for_files_in_folder(path, parent_path)
            hash_list = hash_list + hashes
        else:
            realtive_file_path_string = path.relative_to(parent_path).as_posix()
            file_hash = helpers.get_file_hash_from_path(path)
            hash_list.append([realtive_file_path_string, file_hash])

    return hash_list


def create_tar_archive(source_path, destination_path, source_name, archive_list=None):
    destination_file_path = destination_path.joinpath(source_name + ".tar")
    source_path_parent = source_path.absolute().parent

    if archive_list:
        create_tar_archive_from_list(source_path, archive_list, destination_file_path, source_path_parent)
        return

    # -C flag on tar necessary to get relative path in tar archive
    subprocess.run(["tar", "-cf", destination_file_path, "-C", source_path_parent, source_path.stem])


def create_tar_archive_from_list(source_path, archive_list, destination_file_path, source_path_parent):
    relative_archive_list = map(lambda path: path.absolute().relative_to(source_path.absolute().parent), archive_list)
    files_string_list = map(lambda path: path.as_posix(), relative_archive_list)

    # Using TemporaryDirectory instead of NamedTemporaryFile to have full control over file creation
    with tempfile.TemporaryDirectory() as temp_path_string:
        tmp_file_path = Path(temp_path_string) / "paths.txt"

        with open(tmp_file_path, "w") as tmp_file:
            tmp_file.write("\n".join(files_string_list))

        subprocess.run(["tar", "-cf", destination_file_path, "-C", source_path_parent, "--files-from", tmp_file_path])


def create_archive_listing(destination_path, source_name):
    listing_path = destination_path.joinpath(source_name + ".tar.lst")
    tar_path = destination_path.joinpath(source_name + ".tar")

    archive_listing_file = open(listing_path, "w")
    subprocess.run(["tar", "-tvf", tar_path], stdout=archive_listing_file)


def compress_using_lzip(destination_path, source_name, threads, compression):
    path = destination_path.joinpath(source_name + ".tar")

    additional_arguments = []

    if threads:
        logging.debug(f"Plzip compression extra argument: --threads " + str(threads))
        additional_arguments.extend(["--threads", str(threads)])

    subprocess.run(["plzip", path, f"-{compression}"] + additional_arguments)


def create_and_write_archive_hash(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar").absolute()

    helpers.create_and_write_file_hash(path)


def create_and_write_compressed_archive_hash(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar.lz").absolute()

    helpers.create_and_write_file_hash(path)
