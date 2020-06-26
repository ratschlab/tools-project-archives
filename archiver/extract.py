import subprocess
import os
import sys
from pathlib import Path
import logging

from . import helpers
from .encryption import decrypt_list_of_archives
from .constants import COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX

# TODO: Handle subprocess exceptions
# TODO: What should happen with the archive after extraction?

# Should there be a flag or automatically recongnize encrypted archives?
# Ensure gpg key is available


def extract_archive(source_path, destination_directory_path, partial_extraction_path=None, threads=None):
    # Make sure destination path directory existts
    helpers.terminate_if_directory_nonexistent(destination_directory_path)

    is_encrypted = helpers.path_target_is_encrypted(source_path)
    archive_files = helpers.get_archives_from_path(source_path, is_encrypted)

    if is_encrypted:
        decrypt_list_of_archives(archive_files)
        archive_files = [path.with_suffix("") for path in archive_files]

    if partial_extraction_path:
        partial_extraction(archive_files, destination_directory_path, partial_extraction_path)
    else:
        uncompress_and_extract(archive_files, destination_directory_path, threads)

    logging.info("Archive extracted to: " + helpers.get_absolute_path_string(destination_directory_path))


def uncompress_and_extract(archive_file_paths, destination_directory_path, threads, encrypted=False):
    for archive_path in archive_file_paths:
        logging.info(f"Complete extraction of archive " + helpers.get_absolute_path_string(archive_path))

        additional_arguments = []

        if threads:
            additional_arguments.extend(["--threads", str(threads)])

        ps = subprocess.Popen(["plzip", "-dc", archive_path] + additional_arguments, stdout=subprocess.PIPE)
        subprocess.Popen(["tar", "-x", "-C", destination_directory_path], stdin=ps.stdout)
        ps.stdout.close()
        ps.wait()
        # TODO: terminate (with)

        destination_directory_path_string = helpers.get_absolute_path_string(destination_directory_path)

        logging.info(f"Extracted archive {archive_path.stem} to {destination_directory_path_string}")


def partial_extraction(archive_file_paths, destination_directory_path, partial_extraction_path):
    # TODO: Make this more efficient. No need to decompress every single archive
    logging.info(f"Start extracting {partial_extraction_path} from archive...")

    for archive_path in archive_file_paths:
        subprocess.run(["tar", "-xvf", archive_path, "-C", destination_directory_path, partial_extraction_path])

        logging.info(f"Extracted {partial_extraction_path} from {archive_path.stem}")
