import subprocess
import os
import sys
from pathlib import Path
import logging

from . import helpers
from .constants import COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX

# TODO: Handle subprocess exceptions
# TODO: What should happen with the archive after extraction?

# Should there be a flag or automatically recongnize encrypted archives?
# Ensure gpg key is available


def extract_archive(source_path, destination_directory_path, partial_extraction_path=None, threads=None):
    archive_files = []
    is_encrypted = False

    # Make sure destination path directory existts
    helpers.terminate_if_directory_nonexistent(destination_directory_path)

    if source_path.is_dir():
        # TODO: What happens if both encrypted and unencrypted archive files?
        # Fail in case this happens
        encrypted_archive_files = helpers.get_files_with_type_in_directory(source_path, ENCRYPTED_ARCHIVE_SUFFIX)

        try:
            if encrypted_archive_files:
                is_encrypted = True
                archive_files = encrypted_archive_files
            else:
                archive_files = helpers.get_files_with_type_in_directory(source_path, COMPRESSED_ARCHIVE_SUFFIX)
        except LookupError as error:
            helpers.terminate_with_exception(error)
    else:
        file_is_valid_archive_or_terminate(source_path)
        is_encrypted = True if helpers.file_has_type(source_path, ENCRYPTED_ARCHIVE_SUFFIX) else False

        archive_files = [source_path]

    if is_encrypted:
        decrypt_archives(archive_files)
        archive_files = map(lambda path: path.with_suffix(""), archive_files)

    if partial_extraction_path:
        partial_extraction(archive_files, destination_directory_path, partial_extraction_path)
    else:
        uncompress_and_extract(archive_files, destination_directory_path, threads)

    logging.info("Archive extracted to: " + helpers.get_absolute_path_string(destination_directory_path))


def decrypt_archives(archive_file_paths):
    for archive_path in archive_file_paths:
        logging.info("Decrypting archive: " + helpers.get_absolute_path_string(archive_path))

        output_path = archive_path.with_suffix("").absolute()
        try:
            subprocess.check_output(["gpg", "--output", output_path, "--decrypt", archive_path.absolute()])
        except subprocess.CalledProcessError:
            helpers.terminate_with_message("Decryption of archive failed. Make sure the necessary private key added to GPG.")


def uncompress_and_extract(archive_file_paths, destination_directory_path, threads, encrypted=False):
    for archive_path in archive_file_paths:
        logging.info(f"Complete extraction of archive " + helpers.get_absolute_path_string(archive_path))
        decrypted_archive_path = archive_path

        if encrypted:
            logging.info("Decrypting archive...")
            decrypted_archive_path = archive_path.with_suffix("")

            try:
                subprocess.run(["gpg", "--output", decrypted_archive_path, "--decrypt", archive_path])
            except subprocess.CalledProcessError:
                helpers.terminate_with_message(f"Decryption of archive {archive_path} failed.")

        additional_arguments = []

        if threads:
            additional_arguments.extend(["--threads", str(threads)])

        ps = subprocess.Popen(["plzip", "-dc", decrypted_archive_path] + additional_arguments, stdout=subprocess.PIPE)
        subprocess.Popen(["tar", "-x", "-C", destination_directory_path], stdin=ps.stdout)
        ps.stdout.close()
        ps.wait()
        # TODO: terminate (with)

        destination_directory_path_string = helpers.get_absolute_path_string(destination_directory_path)

        logging.info(f"Extracted archive {decrypted_archive_path.stem} to {destination_directory_path_string}")


def partial_extraction(archive_file_paths, destination_directory_path, partial_extraction_path):
    # TODO: Make this more efficient. No need to decompress every single archive
    logging.info(f"Start extracting {partial_extraction_path} from archive...")

    for archive_path in archive_file_paths:
        subprocess.run(["tar", "-xvf", archive_path, "-C", destination_directory_path, partial_extraction_path])

        logging.info(f"Extracted {partial_extraction_path} from {archive_path.stem}")


def file_is_valid_archive_or_terminate(file_path):
    if not helpers.file_has_type(file_path, COMPRESSED_ARCHIVE_SUFFIX) or helpers.file_has_type(file_path, ENCRYPTED_ARCHIVE_SUFFIX):
        helpers.terminate_with_message(f"File is not a valid archive of type {COMPRESSED_ARCHIVE_SUFFIX} or {ENCRYPTED_ARCHIVE_SUFFIX}")
