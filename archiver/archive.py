import os
import subprocess
import hashlib
from pathlib import Path
import logging

from . import helpers
from . import splitter
from .constants import ENCRYPTION_ALGORITHM, COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX

DELETE_UNENCRYPTED_ARCHIVE = True


def encrypt_existing_archive(archive_path, encryption_keys):
    encryption_keys_must_exist(encryption_keys)

    if helpers.file_has_type(archive_path, COMPRESSED_ARCHIVE_SUFFIX):
        logging.info("Start encryption of existing archive " + helpers.get_absolute_path_string(archive_path))
        encrypt_list_of_archives([archive_path], encryption_keys)
        return

    if archive_path.is_dir():
        try:
            # If there are already encrypted archives in a folder, we'll do nothing
            if helpers.get_files_with_type_in_directory(archive_path, ENCRYPTED_ARCHIVE_SUFFIX):
                raise ValueError("Encrypted archvies present. Doing nothing.")

            archive_files = helpers.get_all_files_with_type_in_directory(archive_path, COMPRESSED_ARCHIVE_SUFFIX)
        except LookupError as error:
            helpers.terminate_with_exception(error)
        except ValueError as error:
            helpers.terminate_with_exception(error)

        encrypt_list_of_archives(archive_files, encryption_keys)


def create_archive(source_path, destination_path, threads=None, encrypt=None, compression=6, splitting=None):
    # Argparse already checks if arguments are present, so only argument format needs to be validated
    helpers.terminate_if_path_nonexistent(source_path)

    # Check if destination parent directory exist but not actual directory
    helpers.terminate_if_parent_directory_nonexistent(destination_path)
    helpers.terminate_if_path_exists(destination_path)

    source_name = source_path.name

    # TODO: Validate threads is a valid number (if argparse doesn't do this)
    # TODO: Make sure compression level is number between 0 and 9

    if not encrypt == None:
        encryption_keys_must_exist(encrypt)

    logging.info(f"Start creating archive for: {helpers.get_absolute_path_string(source_path)}")

    destination_path.mkdir()

    if splitting:
        create_split_archive(source_path, destination_path, source_name, int(splitting), threads, encrypt, compression)
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

        if encrypt:
            archive_list = [destination_path.joinpath(source_name + COMPRESSED_ARCHIVE_SUFFIX)]
            encrypt_list_of_archives(archive_list, encrypt, DELETE_UNENCRYPTED_ARCHIVE)

    logging.info(f"Archive created: {helpers.get_absolute_path_string(destination_path)}")


def create_split_archive(source_path, destination_path, source_name, splitting, threads, encryption_keys, compression):
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
            archive_list = [destination_path.joinpath(source_part_name + COMPRESSED_ARCHIVE_SUFFIX)]
            encrypt_list_of_archives(archive_list, encryption_keys, DELETE_UNENCRYPTED_ARCHIVE)


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

    # -C flag on tar necessary to get relative path in tar archive
    # Temporary workaround with shell=true
    # TODO: Implement properly without directly running on the shell
    # TODO: Excape file names -> will be done automatically by no directly executing with shell=True

    source_path_parent = source_path.absolute().parent

    if archive_list:
        relative_archive_list = map(lambda path: path.absolute().relative_to(source_path.absolute().parent), archive_list)
        files_string_list = " ".join(map(lambda path: path.as_posix(), relative_archive_list))

        subprocess.run([f"tar -cf {destination_file_path} -C {source_path_parent} {files_string_list}"], shell=True)
        return

    subprocess.run(["tar", "-cf", destination_file_path, "-C", source_path_parent, source_path.stem])


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


# Encryption

def encrypt_list_of_archives(archive_list, encryption_keys, delete=False):
    for archive_path in archive_list:
        output_path = helpers.add_suffix_to_path(archive_path, ".gpg")
        encrypt_archive(archive_path, output_path, encryption_keys, delete)
        helpers.create_and_write_file_hash(output_path)


def encrypt_archive(archive_path, output_path, encryption_keys, delete=False):
    logging.info("Encrypting archive: " + helpers.get_absolute_path_string(archive_path))

    argument_encryption_list = []

    for key_path_string in encryption_keys:
        key_path = Path(key_path_string).absolute().as_posix()

        argument_encryption_list.append("--recipient-file")
        argument_encryption_list.append(key_path)

    try:
        subprocess.check_output(["gpg", "--cipher-algo", ENCRYPTION_ALGORITHM, "--batch", "--output", output_path, "--encrypt"] + argument_encryption_list + [archive_path])
        # Is there a way to overwrite the .tar.lz file instead of creating a new one for encryption?
        if delete:
            logging.debug("Deleting unencrypted archive: " + helpers.get_absolute_path_string(archive_path))
            os.remove(archive_path)
    except subprocess.CalledProcessError:
        helpers.terminate_with_message(f"Encryption of archive {archive_path} failed.")

    logging.info(f"Encryption of archive {archive_path} complete.")


def encryption_keys_must_exist(key_list):
    for key in key_list:
        helpers.terminate_if_file_nonexistent(Path(key))
