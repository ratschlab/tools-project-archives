import os
import subprocess
import hashlib
from pathlib import Path

from . import helpers
# from .splitter import Splitter
from . import splitter


def create_archive(source_path, destination_path, threads=None, compression=6, splitting=None):
    # Set compression to 6 if None value is provided
    compression = compression if compression else 6

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

    if splitting:
        create_splitted_archives(source_path, destination_path, source_name, int(splitting), threads, compression)
    else:
        create_file_listing_hash(source_path, destination_path, source_name)
        create_tar_archive(source_path, destination_path, source_name)
        create_and_write_archive_hash(destination_path, source_name)
        create_archive_listing(destination_path, source_name)

        print("Starting compression...")
        compress_using_lzip(destination_path, source_name, threads, compression)
        create_and_write_compressed_archive_hash(destination_path, source_name)

    print(f"Archive created: {helpers.get_absolute_path_string(destination_path)}")


def create_splitted_archives(source_path, destination_path, source_name, splitting, threads, compression):
    splitted_archives = splitter.split_directory(source_path, splitting)

    for index, archive in enumerate(splitted_archives):
        source_part_name = f"{source_name}.part{index + 1}"

        create_file_listing_hash(source_path, destination_path, source_part_name, archive)
        create_tar_archive(source_path, destination_path, source_part_name, archive)
        create_and_write_archive_hash(destination_path, source_part_name)
        create_archive_listing(destination_path, source_part_name)

        print(f"Starting compression of part {index + 1}")
        compress_using_lzip(destination_path, source_part_name, threads, compression)
        create_and_write_compressed_archive_hash(destination_path, source_part_name)


def create_file_listing_hash(source_path, destination_path, source_name, archive_list=None):
    if archive_list:
        paths_to_hash_list = archive_list
    else:
        paths_to_hash_list = [source_path]

    hashes = hashes_for_path_list(paths_to_hash_list, source_path.parent)
    file_path = destination_path.joinpath(source_name + ".md5")

    with open(file_path, "a") as hash_file:
        for line in hashes:
            file_path = line[0]
            file_hash = line[1]

            hash_file.write(f"{file_hash} {file_path}\n")


# TODO: Needs refactoring
def hashes_for_path_list(path_list, parent_path):
    hash_list = []

    for path in path_list:
        if path.is_dir():
            hashes = helpers.hash_listing_for_files_in_folder(path, parent_path)
            hash_list = hash_list + hashes
        else:
            file_hash = helpers.get_file_hash_from_path(path)
            realtive_file_path_string = path.relative_to(parent_path).as_posix()
            hash_list.append([realtive_file_path_string, file_hash])

    return hash_list


def create_tar_archive(source_path, destination_path, source_name, archive_list=None):
    destination_file_path = destination_path.joinpath(source_name + ".tar")

    # -C flag on tar necessary to get relative path in tar archive
    # Temporary workaround with shell=true
    # TODO: Implement properly without directly running on the shell
    # TODO: Excape file names -> will be done automatically by no directly executing with shell=True

    source_path_parent = source_path.absolute().parent

    if archive_list:
        relative_archive_list = map(lambda path: path.absolute().relative_to(source_path.absolute().parent), archive_list)
        files_string_list = " ".join(map(lambda path: path.as_posix(), relative_archive_list))

        subprocess.run([f"tar -cf {destination_file_path} -C {source_path_parent} {files_string_list}"], shell=True)
        return

    subprocess.run(["tar", "-cf", destination_file_path, "-C", source_path_parent, source_path.stem])


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
