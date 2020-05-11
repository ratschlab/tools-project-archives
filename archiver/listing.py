import subprocess
from pathlib import Path

from . import helpers

LISTING_SUFFIX = ".tar.lst"
COMPRESSED_ARCHIVE_SUFFIX = ".tar.lz"

def create_listing(source_path, subdir_path=None, deep=False):
    if deep:
        listing_from_archive(source_path, subdir_path)
        return
    
    listing_from_file(source_path, subdir_path)

def listing_from_file(source_path, subdir_path):
    if source_path.is_dir():
        listing_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, LISTING_SUFFIX)
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        # Search for listing file in directory of tar.lz file
        listing_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path.parent, LISTING_SUFFIX)


    # TODO: Smarter dir-based search, not just filtering for string in path
    with open(listing_file_path, "r") as file:
        for line in file:
            if not subdir_path or subdir_path in line:
                print(line.rstrip())
                

def listing_from_archive(source_path, subdir_path):
    if source_path.is_dir():
        source_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, COMPRESSED_ARCHIVE_SUFFIX)
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        source_file_path = source_path

    if subdir_path:
        result = subprocess.run(["tar", "-tvf", source_file_path, subdir_path], stdout=subprocess.PIPE)
    else:
        result = subprocess.run(["tar", "-tvf", source_file_path], stdout=subprocess.PIPE)

    print(result.stdout.decode("utf-8"))