import os
import subprocess
import sys
import hashlib
from pathlib import Path

# TODO: Validate arguments (valid paths)
# TODO: Get real path (could be with absolute, relative, with or without slash at the end)
# TODO: Handle case where directory already exists
# TODO: Handle case where no output directory is selected (create new directory where data to archive is located)
# TODO: Per default take name of project data folder for archived files, option to supply a name


def archive(args):
    # Path to a file or directory for which to create the archive
    input_path = Path(args.input)
    # Path to a directory which will be created (if it does yet exist)
    output_directory_path = args.output

    # Argparse already checks if argument is present, so only argument format needs to be validated
    terminate_if_path_nonexistent(input_path)

    if output_directory_path:
        output_directory_path = Path(output_directory_path)
    else:
        modified_path = input_path.absolute().as_posix() + "-archive"
        output_directory_path = Path(modified_path)

    create_directory_if_nonexistent(output_directory_path)
    create_file_listing_hash(input_path, output_directory_path)
    create_tar_archive(input_path, output_directory_path)
    create_archive_listing(input_path, output_directory_path)
    compress_using_lzip(output_directory_path)
    create_archive_hash(output_directory_path)

    print("Archive created: " + output_directory_path.as_posix())


# TODO: parallelization
def create_file_listing_hash(input_path, output_directory_path):
    for root, _, files in os.walk(input_path):
        hashes = []
        for file in files:
            # Read file content as binary for hash
            with open(os.path.join(root, file), "rb") as read_file:
                hashes.append([root, file, hashlib.md5(read_file.read()).hexdigest()])

        write_hash_list_to_file(Path.joinpath(output_directory_path, "archive.md5"), hashes)


def create_tar_archive(input_path, output_directory_path):
    path = Path.joinpath(output_directory_path, "archive.tar")
    subprocess.run(["tar", "-cf", path, input_path])


def create_archive_listing(input_path, output_directory_path):
    listing_path = Path.joinpath(output_directory_path, "archive.tar.lst")
    tar_path = Path.joinpath(output_directory_path, "archive.tar")

    archive_listing_file = open(listing_path, "w")
    subprocess.run(["tar", "-tvf", tar_path], stdout=archive_listing_file)


def compress_using_lzip(output_directory_path):
    path = Path.joinpath(output_directory_path, "archive.tar")
    subprocess.run(["plzip", path])


def create_archive_hash(output_directory_path):
    path = Path.joinpath(output_directory_path, "archive.tar.lz")

    hasher = hashlib.md5()
    # Read file content as binary for hash
    with open(path, 'rb') as read_file:
        buf = read_file.read()
        hasher.update(buf)

    hash_file = open(Path.joinpath(output_directory_path, "archive.tar.lz.md5"), "w")
    hash_file.write(hasher.hexdigest())


def write_hash_list_to_file(file_path, hashes):
    hash_file = open(file_path, "a")
    for file in hashes:
        path = os.path.join(file[0], file[1])
        hash_file.write(file[2] + " " + path + "\n")


def terminate_if_path_nonexistent(path):
    if not path.exists():
        sys.exit("Path does not exist: " + path.absolute())


def create_directory_if_nonexistent(path):
    if not path.exists():
        path.mkdir()
