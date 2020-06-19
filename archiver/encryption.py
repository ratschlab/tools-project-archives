import logging
import subprocess
from . import helpers
from .constants import REQUIRED_SPACE_MULTIPLIER, COMPRESSED_ARCHIVE_SUFFIX


def decrypt_list_of_archives(archives, target_directory=None):
    for archive_path in archives:
        decrypt_archive(archive_path, target_directory)


def decrypt_archive(archive_path, target_directory):
    logging.info("Decrypting archive: " + helpers.get_absolute_path_string(archive_path))

    if target_directory:
        ensure_sufficient_disk_capacity_for_decryption(archive_path, target_directory)
        output_path = target_directory / archive_path.with_suffix("").name
    else:
        ensure_sufficient_disk_capacity_for_decryption(archive_path, archive_path.parent)
        output_path = archive_path.with_suffix("").absolute()

    try:
        subprocess.check_output(["gpg", "--output", output_path, "--decrypt", archive_path.absolute()])
    except subprocess.CalledProcessError:
        helpers.terminate_with_message("Decryption of archive failed. Make sure the necessary private key added to GPG.")


# MARK: Helpers

def ensure_sufficient_disk_capacity_for_decryption(file_path, extraction_path):
    file_size = helpers.get_size_of_path(file_path)
    available_bytes = helpers.get_device_available_capacity_from_path(extraction_path)

    if available_bytes < file_size * REQUIRED_SPACE_MULTIPLIER:
        helpers.terminate_with_message("Not enough space available for decryption")
