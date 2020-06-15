import subprocess
from pathlib import Path
import logging
import tempfile

from . import helpers
from .constants import LISTING_SUFFIX, COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX


def create_listing(source_path, subdir_path=None, deep=False):
    if deep:
        listing_from_archive(source_path, subdir_path)
    else:
        listing_from_file(source_path, subdir_path)


def listing_from_file(source_path, subdir_path):
    listing_files = []

    if source_path.is_dir():
        try:
            listing_files = helpers.get_all_files_with_type_in_directory(source_path, LISTING_SUFFIX)
        except LookupError as error:
            helpers.terminate_with_exception(error)
    else:
        # If specific file is used, maybe not all results of search path will be shown (since they could be in different file)
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        listing_files = [source_path.with_suffix(".lst")]
        helpers.terminate_if_path_nonexistent(listing_files[0])

    # TODO: Smarter dir-based search, not just filtering for string in path
    # only match actiual path instead of "contains" search
    for listing_file_path in listing_files:
        # Both log and print, since listing information is relevant to the user
        logging.info(f"Listing content of: {listing_file_path.name}")
        print(f"Listing content of: {listing_file_path.name}")
        with open(listing_file_path, "r") as file:
            for line in file:
                if not subdir_path or subdir_path in line:
                    print(line.rstrip())

        # Print empty new line for visibility, \n makes gap too large
        print("")


def listing_from_archive(source_path, subdir_path):
    archives = []
    is_encrypted = False

    # if dir list all parts of archive
    # if specific file, only list content of file
    if source_path.is_dir():
        encrypted_archive_files = helpers.get_files_with_type_in_directory(source_path, ENCRYPTED_ARCHIVE_SUFFIX)
        try:
            if encrypted_archive_files:
                is_encrypted = True
                archives = encrypted_archive_files
            else:
                archives = helpers.get_files_with_type_in_directory(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        except LookupError as error:
            helpers.terminate_with_exception(error)
    else:
        file_is_valid_archive_or_terminate(source_path)
        is_encrypted = True if helpers.file_has_type(source_path, ENCRYPTED_ARCHIVE_SUFFIX) else False

        archives = [source_path]

    if is_encrypted:
        logging.info("Deep listing of encrypted archive.")
        decrypt_and_list(archives, subdir_path)
    else:
        for archive in archives:
            # Both log and print, since listing information is relevant to the user
            logging.info(f"Listing content of: {archive.name}")
            print(f"Listing content of: {archive.name}")
            if subdir_path:
                result = subprocess.run(["tar", "-tvf", archive, subdir_path], stdout=subprocess.PIPE)
            else:
                result = subprocess.run(["tar", "-tvf", archive], stdout=subprocess.PIPE)

            decoded_output = result.stdout.decode("utf-8")

            print(decoded_output)


def decrypt_and_list(archives, subdir_path):
    # TODO: Check if enough disk space or warn
    with tempfile.TemporaryDirectory() as temp_path_string:
        temp_path = Path(temp_path_string)

        decrypt_archives(archives, temp_path)
        archives = map(lambda path: temp_path / path.with_suffix("").name, archives)

        for archive in archives:
            # Both log and print, since listing information is relevant to the user
            logging.info(f"Listing content of: {archive.name}")
            print(f"Listing content of: {archive.name}")
            if subdir_path:
                result = subprocess.run(["tar", "-tvf", archive, subdir_path], stdout=subprocess.PIPE)
            else:
                result = subprocess.run(["tar", "-tvf", archive], stdout=subprocess.PIPE)

            decoded_output = result.stdout.decode("utf-8")

            print(decoded_output)


def decrypt_archives(archive_file_paths, parent_dir):
    for archive_path in archive_file_paths:
        logging.info("Decrypting archive: " + helpers.get_absolute_path_string(archive_path))

        output_path = parent_dir / archive_path.with_suffix("").name
        try:
            subprocess.check_output(["gpg", "--output", output_path, "--decrypt", archive_path.absolute()])
        except subprocess.CalledProcessError:
            helpers.terminate_with_message("Decryption of archive failed. Make sure the necessary private key added to GPG.")


def file_is_valid_archive_or_terminate(file_path):
    if not helpers.file_has_type(file_path, COMPRESSED_ARCHIVE_SUFFIX) or helpers.file_has_type(file_path, ENCRYPTED_ARCHIVE_SUFFIX):
        helpers.terminate_with_message(f"File is not a valid archive of type {COMPRESSED_ARCHIVE_SUFFIX} or {ENCRYPTED_ARCHIVE_SUFFIX}")
