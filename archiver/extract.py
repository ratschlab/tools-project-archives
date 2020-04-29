import subprocess
import os
import sys
from pathlib import Path

from .helpers import terminate_if_directory_nonexistent, get_file_with_type_in_directory_or_terminate, terminate_if_path_not_file_of_type

# TODO: Handle subprocess exceptions
# TODO: What should happen with the archive after extraction?


def extract_archive(source_path, destination_directory_path, partial_extraction_path):
    source_file_path = ""

    #  Validation
    terminate_if_directory_nonexistent(destination_directory_path)

    if (source_path.is_dir()):
        source_file_path = get_file_with_type_in_directory_or_terminate(source_path, ".tar.lz")
    else:
        terminate_if_path_not_file_of_type(source_path, ".tar.lz")
        source_file_path = source_path

    if partial_extraction_path:
        partial_extraction(source_file_path, destination_directory_path, partial_extraction_path)
    else:
        uncompress_and_extract(source_file_path, destination_directory_path)


def uncompress_and_extract(source_file_path, destination_directory_path):
    ps = subprocess.Popen(["plzip", "-dc", source_file_path], stdout=subprocess.PIPE)
    subprocess.Popen(["tar", "-x", "-C", destination_directory_path], stdin=ps.stdout)
    ps.stdout.close()
    ps.wait()


def partial_extraction(source_file_path, destination_directory_path, partial_extraction_path):
    subprocess.run(["tar", "-xvf", source_file_path, "-C", destination_directory_path, partial_extraction_path])
