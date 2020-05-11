import subprocess
from pathlib import Path
import os
import hashlib

from . import helpers


def check_integrity(source_path):
    archive_file_path = ""
    archive_hash_file_path = ""

    if source_path.is_dir():
        archive_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz")
        archive_hash_file_path = helpers.get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz.md5")
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, ".tar.lz")
        archive_file_path = source_path

        archive_directory_path = source_path.parents[0]
        archive_hash_file_path = helpers.get_file_with_type_in_directory_or_terminate(archive_directory_path, source_path.name + ".md5")

    print("Starting integrity check...")

    if compare_hashes_from_files(archive_file_path, archive_hash_file_path):
        print("Integrity check successful")
    else:
        print("Integrity check unsuccessful")



def compare_hashes_from_files(archive_file_path, archive_hash_file_path):
    # Generate hash of .tar.lz
    with open(archive_file_path, "rb") as file:
        archive_hash = hashlib.md5(file.read()).hexdigest()

    # Read hash of .tar.lz.md5
    with open(archive_hash_file_path, "r") as file:
        hash_file_content = file.read()

    return archive_hash == hash_file_content