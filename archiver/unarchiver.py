import subprocess
import os
import sys
from pathlib import Path

import helpers

# TODO: Handle subprocess exceptions
# TODO: What should happen with the archive after extraction?
# TODO: Only extract certain files


def unarchive(args):
    # Path to archive file *.tar.lz
    source_file_path = Path(args.source)
    destination_directory_path = Path(args.destination)
    partial_unarchive_part = args.part

    # Path validation
    helpers.terminate_if_partent_directory_nonexistent(destination_directory_path)
    helpers.terminate_if_path_not_file_of_type(source_file_path, ".tar.lz")

    decompress_and_extract(source_file_path, destination_directory_path)


def decompress_and_extract(source_file_path, destination_directory_path):
    ps = subprocess.Popen(["plzip", "-dc", source_file_path], stdout=subprocess.PIPE)
    subprocess.Popen(["tar", "-x", "--directory", destination_directory_path], stdin=ps.stdout)
    ps.stdout.close()
    ps.wait()


def partial_unarchive(source_file_path, destination_directory_path, partial_unarchive_part):
    subprocess.run(["tar", "-xvf", source_file_path, partial_unarchive_part])
