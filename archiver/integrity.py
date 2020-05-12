import subprocess
from pathlib import Path
import os
import hashlib

from . import helpers


def check_integrity(source_path, deep_flag=False):
    if source_path.is_dir():
        archive_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz")
        archive_hash_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz.md5")
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, ".tar.lz")
        archive_file_path = source_path

        archive_directory_path = source_path.parents[0]
        archive_hash_file_path = helpers.get_file_with_type_in_directory_or_terminate(archive_directory_path, source_path.name + ".md5")

    print("Starting integrity check...")

    if not shallow_integrity_check(archive_file_path, archive_hash_file_path):
        print("Integrity check unsuccessful. Archive has been changed since creation.")
        return

    if deep_flag and not deep_integrity_check(archive_file_path):
        print("Deep integrity check unsuccessful. Archive has been changed since creation.")
        return

    if deep_flag:
        print("Deep integrity check successful")
        return

    print("Integrity check successful")

def shallow_integrity_check(archive_file_path, archive_hash_file_path):
    return compare_hashes_from_files(archive_file_path, archive_hash_file_path)

def deep_integrity_check(archive_file_path):
    return False

def compare_hashes_from_files(archive_file_path, archive_hash_file_path):
    # Generate hash of .tar.lz
    with open(archive_file_path, "rb") as file:
        archive_hash = hashlib.md5(file.read()).hexdigest()

    # Read hash of .tar.lz.md5
    with open(archive_hash_file_path, "r") as file:
        hash_file_content = file.read()

    return archive_hash == hash_file_content