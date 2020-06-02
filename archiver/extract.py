import subprocess
import os
import sys
from pathlib import Path

from . import helpers
from .constants import COMPRESSED_ARCHIVE_SUFFIX

# TODO: Handle subprocess exceptions
# TODO: What should happen with the archive after extraction?


def extract_archive(source_path, destination_directory_path, partial_extraction_path=None, threads=None):
    archive_files = []

    # Make sure destination path directory existts
    helpers.terminate_if_directory_nonexistent(destination_directory_path)

    if source_path.is_dir():
        archive_files = helpers.get_all_files_with_type_in_directory_or_terminate(source_path, COMPRESSED_ARCHIVE_SUFFIX)
    else:
        helpers.terminate_if_path_not_file_of_type(source_path, COMPRESSED_ARCHIVE_SUFFIX)

        archive_files = [source_path]

    if partial_extraction_path:
        partial_extraction(archive_files, destination_directory_path, partial_extraction_path)
    else:
        uncompress_and_extract(archive_files, destination_directory_path, threads)

    print("Archive extracted to: " + helpers.get_absolute_path_string(destination_directory_path))


def uncompress_and_extract(archive_file_paths, destination_directory_path, threads):
    print(f"Starting complete archive extraction...")

    for archive_path in archive_file_paths:
        additional_arguments = []

        if threads:
            additional_arguments.extend(["--threads", str(threads)])

        ps = subprocess.Popen(["plzip", "-dc", archive_path] + additional_arguments, stdout=subprocess.PIPE)
        subprocess.Popen(["tar", "-x", "-C", destination_directory_path], stdin=ps.stdout)
        ps.stdout.close()
        ps.wait()
        # TODO: terminate (with)

        destination_directory_path_string = helpers.get_absolute_path_string(destination_directory_path)

        print(f"Extracted archive {archive_path.stem} to {destination_directory_path_string}")


def partial_extraction(archive_file_paths, destination_directory_path, partial_extraction_path):
    print(f"Start extracting {partial_extraction_path} from archive...")

    for archive_path in archive_file_paths:
        print(archive_path)

        subprocess.run(["tar", "-xvf", archive_path, "-C", destination_directory_path, partial_extraction_path])

        print(f"Extracted {partial_extraction_path} from {archive_path.stem}")
