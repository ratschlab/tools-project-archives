import subprocess
from pathlib import Path

from . import helpers
from .constants import LISTING_SUFFIX, COMPRESSED_ARCHIVE_SUFFIX


def create_listing(source_path, subdir_path=None, deep=False):
    if deep:
        listing_from_archive(source_path, subdir_path)
    else:
        listing_from_file(source_path, subdir_path)


def listing_from_file(source_path, subdir_path):
    listing_files = []

    if source_path.is_dir():
        # listing_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, LISTING_SUFFIX)
        listing_files = helpers.get_all_files_with_type_in_directory_or_terminate(source_path, LISTING_SUFFIX)
    else:
        # If specific file is used, maybe not all results of search path will be shown (since they could be in different file)
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        listing_files = [source_path.with_suffix(".lst")]
        helpers.terminate_if_path_nonexistent(listing_files[0])

    # TODO: Smarter dir-based search, not just filtering for string in path
    # only match actiual path instead of "contains" search
    for listing_file_path in listing_files:
        print(f"Listing content of: {listing_file_path.name}")
        with open(listing_file_path, "r") as file:
            for line in file:
                if not subdir_path or subdir_path in line:
                    print(line.rstrip())

        # Print empty new line for visibility, \n makes gap too large
        print("")


def listing_from_archive(source_path, subdir_path):
    archives = []

    # if dir list all parts of archive
    # if specific file, only list content of file
    if source_path.is_dir():
        archives = helpers.get_all_files_with_type_in_directory_or_terminate(source_path, COMPRESSED_ARCHIVE_SUFFIX)
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        archives = [source_path]

    for archive in archives:
        print(f"Listing content of: {archive.name}")
        if subdir_path:
            result = subprocess.run(["tar", "-tvf", archive, subdir_path], stdout=subprocess.PIPE)
        else:
            result = subprocess.run(["tar", "-tvf", archive], stdout=subprocess.PIPE)

        decoded_output = result.stdout.decode("utf-8")

        print(decoded_output)
