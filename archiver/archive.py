import os
import subprocess
import hashlib
from pathlib import Path

import helpers


def create_archive(source_path, destination_path):
    # Argparse already checks if arguments are present, so only argument format needs to be validated
    helpers.terminate_if_path_nonexistent(source_path)

    # Check if destination parent directory exist but not actual directory
    helpers.terminate_if_parent_directory_nonexistent(destination_path)
    helpers.terminate_if_path_exists(destination_path)

    source_name = source_path.name

    destination_path.mkdir()
    create_file_listing_hash(source_path, destination_path, source_name)
    create_tar_archive(source_path, destination_path, source_name)
    create_and_write_archive_hash(destination_path, source_name)
    create_archive_listing(destination_path, source_name)
    compress_using_lzip(destination_path, source_name)
    create_and_write_compressed_archive_hash(destination_path, source_name)

    print("Archive created: " + helpers.get_absolute_path_string(destination_path))


# TODO: parallelization
def create_file_listing_hash(source_path, destination_path, source_name):
    for root, dirs, files in os.walk(source_path):
        hashes = []
        for file in files:
            # Read file content as binary for hash
            with open(os.path.join(root, file), "rb") as read_file:
                reative_path_to_file_string = Path(root).relative_to(source_path.parent).joinpath(file).as_posix()
                hashes.append([reative_path_to_file_string, hashlib.md5(read_file.read()).hexdigest()])

        write_hash_list_to_file(destination_path.joinpath(source_name + ".md5"), hashes)


def create_tar_archive(source_path, destination_path, source_name):
    destination_file_path = destination_path.joinpath(source_name + ".tar")

    # -C flag necessary to get relative path in tar archive
    subprocess.run(["tar", "-cf", destination_file_path, "-C", source_path.parent, source_path.stem])


def create_archive_listing(destination_path, source_name):
    listing_path = destination_path.joinpath(source_name + ".tar.lst")
    tar_path = destination_path.joinpath(source_name + ".tar")

    archive_listing_file = open(listing_path, "w")
    subprocess.run(["tar", "-tvf", tar_path], stdout=archive_listing_file)


def compress_using_lzip(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar")
    subprocess.run(["plzip", path])


def create_and_write_archive_hash(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar").absolute()

    helpers.create_and_write_file_hash(path)


def create_and_write_compressed_archive_hash(destination_path, source_name):
    path = destination_path.joinpath(source_name + ".tar.lz").absolute()

    helpers.create_and_write_file_hash(path)


def write_hash_list_to_file(file_path, hashes):
    hash_file = open(file_path, "a")
    for file in hashes:
        hash_file.write(file[1] + " " + file[0] + "\n")
