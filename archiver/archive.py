import os
import subprocess
import hashlib
from pathlib import Path

from . import helpers


def create_archive(source_path, destination_path, threads=None, compression=6):
    # Argparse already checks if arguments are present, so only argument format needs to be validated
    helpers.terminate_if_path_nonexistent(source_path)

    # Check if destination parent directory exist but not actual directory
    helpers.terminate_if_parent_directory_nonexistent(destination_path)
    helpers.terminate_if_path_exists(destination_path)

    source_name = source_path.name

    # TODO: Validate threads is a valid number (if argparse doesn't do this)
    # TODO: Make sure compression level is number between 0 and 9

    print(f"Start creating archive for: {helpers.get_absolute_path_string(source_path)}")

    destination_path.mkdir()
    create_file_listing_hash(source_path, destination_path, source_name)
    create_tar_archive(source_path, destination_path, source_name)
    create_and_write_archive_hash(destination_path, source_name)
    create_archive_listing(destination_path, source_name)

    print("Starting compression...")

    compress_using_lzip(destination_path, source_name, threads, compression)
    create_and_write_compressed_archive_hash(destination_path, source_name)

    print(f"Archive created: {helpers.get_absolute_path_string(destination_path)}")


# TODO: parallelization
def create_file_listing_hash(source_path, destination_path, source_name):
    hashes = helpers.hash_listing_for_files_in_folder(source_path)
    file_path = destination_path.joinpath(source_name + ".md5")

    with open(file_path, "a") as hash_file:
        for hash in hashes:
            hash_file.write(hash[1] + " " + hash[0] + "\n")


def create_tar_archive(source_path, destination_path, source_name):
    destination_file_path = destination_path.joinpath(source_name + ".tar")

    # -C flag necessary to get relative path in tar archive
    subprocess.run(["tar", "-cf", destination_file_path, "-C", source_path.parent, source_path.stem])


def create_archive_listing(destination_path, source_name):
    listing_path = destination_path.joinpath(source_name + ".tar.lst")
    tar_path = destination_path.joinpath(source_name + ".tar")

    archive_listing_file = open(listing_path, "w")
    subprocess.run(["tar", "-tvf", tar_path], stdout=archive_listing_file)


def compress_using_lzip(destination_path, source_name, threads, compression):
    path = destination_path.joinpath(source_name + ".tar")

    additional_arguments = []

    if threads:
        additional_arguments.extend(["--threads", str(threads)])

    subprocess.run(["plzip", path, f"-{compression}"] + additional_arguments)


def create_and_write_archive_hash(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar").absolute()

    helpers.create_and_write_file_hash(path)


def create_and_write_compressed_archive_hash(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar.lz").absolute()

    helpers.create_and_write_file_hash(path)
