import subprocess
from pathlib import Path
import os
import hashlib
import tempfile
import time

from . import helpers
from .extract import extract_archive
from .constants import REQUIRED_SPACE_MULTIPLIER, COMPRESSED_ARCHIVE_SUFFIX, COMPRESSED_ARCHIVE_HASH_SUFFIX


def check_integrity(source_path, deep_flag=False):
    archives_with_hashes = []

    if source_path.is_dir():
        archives_with_hashes = get_archives_with_hashes(source_path)
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)

        archive_file_path = source_path

        hash_file_path = Path(source_path.as_posix() + ".md5")
        helpers.terminate_if_path_nonexistent(hash_file_path)

        hash_listing_path = source_path.with_suffix("").with_suffix(".md5")

        archives_with_hashes = [(archive_file_path, hash_file_path, hash_listing_path)]

    print("Starting integrity check...")

    if not shallow_integrity_check(archives_with_hashes):
        print("Integrity check unsuccessful. Archive has been changed since creation.")
        return

    if deep_flag and not deep_integrity_check(archives_with_hashes):
        print("Deep integrity check unsuccessful. Archive has been changed since creation.")
        return

    if deep_flag:
        print("Deep integrity check successful")
        return

    print("Integrity check successful")


def shallow_integrity_check(archives_with_hashes):
    # Check each archive file separately
    for archive in archives_with_hashes:
        archive_file_path = archive[0]
        archive_hash_file_path = archive[1]

        if not compare_hashes_from_files(archive_file_path, archive_hash_file_path):
            print(f"Signature of file {archive_file_path.as_posix()} has changed.")
            return False

    return True


def deep_integrity_check(archives_with_hashes):
    # Unpack each archive separately
    for archive in archives_with_hashes:
        archive_file_path = archive[0]
        expected_listing_hash_path = archive[2]

        # Create temporary directory to unpack archive
        with tempfile.TemporaryDirectory() as temp_path_string:
            temp_path = Path(temp_path_string)

            ensure_sufficient_disk_capacity_for_extraction(archive_file_path, temp_path_string)

            # extract archive
            extract_archive(archive_file_path, temp_path)
            # TODO: Again, when extraction runs fast files are not yet readable (listdir) immediately after - fix this
            time.sleep(0.1)

            archive_content_path = get_extracted_archive_path_or_terminate(temp_path)
            hash_result = helpers.hash_listing_for_files_in_folder(archive_content_path)

            return compare_archive_listing_hashes(hash_result, expected_listing_hash_path)


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


def compare_archive_listing_hashes(hash_result, expected_hash_listing_path):
    corrupted_file_paths = []

    with open(expected_hash_listing_path, "r") as file:
        file_string = file.read().rstrip()

    for line in hash_result:
        file_path = line[0]
        file_hash = line[1]

        search_content = f"{file_hash} {file_path}"

        if search_content not in file_string:
            corrupted_file_paths.append(file_path)

    if not corrupted_file_paths:
        return True

    for path in corrupted_file_paths:
        print(f"Signature of {path} has changed.")

    return False


def compare_hashes_from_files(archive_file_path, archive_hash_file_path):
    # Generate hash of .tar.lz
    archive_hash = helpers.get_file_hash_from_path(archive_file_path)

    # Read hash of .tar.lz.md5
    with open(archive_hash_file_path, "r") as file:
        hash_file_content = file.read()

        return archive_hash == hash_file_content


def get_archives_with_hashes(source_path):
    archives = helpers.get_all_files_with_type_in_directory_or_terminate(source_path, COMPRESSED_ARCHIVE_SUFFIX)
    archives_with_hashes = []

    for archive in archives:
        hash_path = Path(archive.as_posix() + ".md5")
        hash_listing_path = archive.with_suffix("").with_suffix(".md5")
        archive_with_hash_path = (archive, hash_path, hash_listing_path)

        archives_with_hashes.append(archive_with_hash_path)

    return archives_with_hashes
