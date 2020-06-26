import subprocess
from pathlib import Path
import logging
import tempfile

from . import helpers
from .encryption import decrypt_list_of_archives
from .constants import LISTING_SUFFIX, COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX


def create_listing(source_path, subdir_path=None, deep=False):
    if deep:
        listing_from_archive(source_path, subdir_path)
    else:
        listing_from_listing_file(source_path, subdir_path)


def listing_from_listing_file(source_path, subdir_path):
    listing_files = get_listing_files_for_path(source_path)

    # TODO: Smarter dir-based search, not just filtering for string in path
    # only match actiual path instead of "contains" search
    for listing_file_path in listing_files:
        logging.info(f"Listing content of: {listing_file_path.name}")
        print(f"Listing content of: {listing_file_path.name}")

        with open(listing_file_path, "r") as file:
            for line in file:
                if not subdir_path or subdir_path in line:
                    print(line.rstrip())

        # Print empty new line for visibility, \n makes gap too large
        print("")


def listing_from_archive(source_path, subdir_path):
    is_encrypted = helpers.path_target_is_encrypted(source_path)
    archives = helpers.get_archives_from_path(source_path, is_encrypted)

    if is_encrypted:
        logging.info("Deep listing of encrypted archive.")
        decrypt_and_list(archives, subdir_path)
    else:
        logging.info("Deep listing of compressed archive.")
        list_archives(archives, subdir_path)


def decrypt_and_list(archives, subdir_path):
    # TODO: Check if enough disk space or warn
    with tempfile.TemporaryDirectory() as temp_path_string:
        temp_path = Path(temp_path_string)

        decrypt_list_of_archives(archives, temp_path)
        archives_encrypted = [temp_path / path.with_suffix("").name for path in archives]

        list_archives(archives_encrypted, subdir_path)


def list_archives(archives, subdir_path):
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


# MARK: Helpers

def get_listing_files_for_path(path):
    if path.is_dir():
        return helpers.get_files_with_type_in_directory_or_terminate(path, LISTING_SUFFIX)

     # If specific file is used, maybe not all results of search path will be shown (since they could be in different file)
    helpers.file_is_valid_archive_or_terminate(path)
    listing_path = path.parent / (helpers.filename_without_extension(path) + ".tar.lst")
    helpers.terminate_if_path_nonexistent(path)

    return [listing_path]
