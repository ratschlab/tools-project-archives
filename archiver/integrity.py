import subprocess
from pathlib import Path
import os
import hashlib
import tempfile
import time

from . import helpers
from .extract import extract_archive

REQUIRED_SPACE_MULTIPLIER = 1.1


def check_integrity(source_path, deep_flag=False):
    if source_path.is_dir():
        archive_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz")
        archive_hash_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz.md5")
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, ".tar.lz")
        archive_file_path = source_path
        archive_directory_path = source_path.parents[0]

        archive_hash_file_path = helpers.get_file_with_type_in_directory_or_terminate(
            archive_directory_path, source_path.name + ".md5")

    archive_listing_file_path = source_path.joinpath(Path(archive_file_path.stem).stem + ".md5")

    print("Starting integrity check...")

    if not shallow_integrity_check(archive_file_path, archive_hash_file_path):
        print("Integrity check unsuccessful. Archive has been changed since creation.")
        return

    if deep_flag and not deep_integrity_check(archive_file_path, archive_listing_file_path, archive_listing_file_path):
        print("Deep integrity check unsuccessful. Archive has been changed since creation.")
        return

    if deep_flag:
        print("Deep integrity check successful")
        return

    print("Integrity check successful")


def shallow_integrity_check(archive_file_path, archive_hash_file_path):
    return compare_hashes_from_files(archive_file_path, archive_hash_file_path)


# TODO: Needs refactoring
# TODO: Better exception handling
def deep_integrity_check(archive_file_path, listing_file_path, expected_hash_listing):
    output = subprocess.check_output(["plzip", "-l", archive_file_path])

    # define exception to throw if this fails and display this instead of "Integrity check unsuccessful"
    archive_uncompressed_byte_size = int(output.decode("utf-8").splitlines()[-1].lstrip().split(' ', 1)[0])

    with tempfile.TemporaryDirectory() as temp_path_string:
        temp_path = Path(temp_path_string)

        fs_stats = os.statvfs(temp_path)
        available_bytes = fs_stats.f_frsize * fs_stats.f_bavail

        # multiply by REQUIRED_SPACE_MULTIPLIER to make sure there's definetly enough space
        if available_bytes < archive_uncompressed_byte_size * REQUIRED_SPACE_MULTIPLIER:
            raise Exception("Not enough space available for deep integrity check")

        # extract archive
        extract_archive(archive_file_path, temp_path)
        time.sleep(0.1)

        # generate hash listing using existing method and compare with test-folder.md5
        try:
            archive_content = os.listdir(temp_path)[0]
        except:
            raise Exception("Extraction of archive for deep integrity check failed")

        result = helpers.hash_listing_for_files_in_folder(temp_path.joinpath(archive_content))

        with open(expected_hash_listing, "r") as file:
            file_string = file.read().rstrip()

        for line in result:
            search_content = line[1] + " " + line[0]
            if search_content not in file_string:
                return False

    return True


def compare_hashes_from_files(archive_file_path, archive_hash_file_path):
    # Generate hash of .tar.lz
    with open(archive_file_path, "rb") as file:
        archive_hash = hashlib.md5(file.read()).hexdigest()

    # Read hash of .tar.lz.md5
    with open(archive_hash_file_path, "r") as file:
        hash_file_content = file.read()

    return archive_hash == hash_file_content
