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


def deep_integrity_check(archive_file_path, listing_file_path, expected_hash_listing):
    with tempfile.TemporaryDirectory() as temp_path_string:
        temp_path = Path(temp_path_string)

        ensure_sufficient_disk_capacity_for_extraction(archive_file_path, temp_path_string)

        # extract archive
        extract_archive(archive_file_path, temp_path)
        # TODO: Again, when extraction runs fast files are not yet readable (listdir) immediately after - fix this
        time.sleep(0.1)

        archive_content_path = get_extracted_archive_path_or_terminate(temp_path)
        hash_result = helpers.hash_listing_for_files_in_folder(archive_content_path)

        return compare_archive_listing_hashes(hash_result, expected_hash_listing)


def ensure_sufficient_disk_capacity_for_extraction(archive_file_path, extraction_path):
    archive_uncompressed_byte_size = helpers.get_uncompressed_archive_size_in_bytes(archive_file_path)
    available_bytes = helpers.get_device_available_capacity_from_path(extraction_path)

    # multiply by REQUIRED_SPACE_MULTIPLIER for margin
    if available_bytes < archive_uncompressed_byte_size * REQUIRED_SPACE_MULTIPLIER:
        helpers.terminate_with_message("Not enough space available for deep integrity check")


def get_extracted_archive_path_or_terminate(temp_path):
    # generate hash listing using existing method and compare with test-folder.md5
    try:
        archive_content = os.listdir(temp_path)[0]
        return temp_path.joinpath(archive_content)
    except:
        helpers.terminate_with_message("Extraction of archive for deep integrity check failed")


def compare_archive_listing_hashes(hash_result, expected_hash_listing):
    with open(expected_hash_listing, "r") as file:
        file_string = file.read().rstrip()

    for line in hash_result:
        file_path = line[0]
        file_hash = line[1]

        search_content = f"{file_hash} {file_path}"

        if search_content not in file_string:
            return False

    return True


def compare_hashes_from_files(archive_file_path, archive_hash_file_path):
    # Generate hash of .tar.lz
    archive_hash = helpers.get_file_hash_from_path(archive_file_path)

    # Read hash of .tar.lz.md5
    with open(archive_hash_file_path, "r") as file:
        hash_file_content = file.read()

        return archive_hash == hash_file_content
