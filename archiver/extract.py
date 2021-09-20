import logging
import subprocess

from . import helpers
from . import listing
from .constants import COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX, \
    REQUIRED_SPACE_MULTIPLIER
from .encryption import decrypt_list_of_archives


# Should there be a flag or automatically recongnize encrypted archives?
# Ensure gpg key is available


def decrypt_existing_archive(archive_path, destination_dir=None, remove_unencrypted=False, force=False, threads=1):
    if destination_dir:
        helpers.handle_destination_directory_creation(destination_dir, force)

    if archive_path.is_dir():
        if helpers.get_files_with_type_in_directory(archive_path, COMPRESSED_ARCHIVE_SUFFIX):
            helpers.terminate_with_message("Unencrypted archvies present. Doing nothing.")

        archive_files = helpers.get_files_with_type_in_directory_or_terminate(archive_path, ENCRYPTED_ARCHIVE_SUFFIX)

        decrypt_list_of_archives(archive_files, destination_dir, delete=remove_unencrypted, threads=threads)
        return

    helpers.terminate_if_path_not_file_of_type(archive_path, ENCRYPTED_ARCHIVE_SUFFIX)

    logging.info("Start decryption of existing archive " + helpers.get_absolute_path_string(archive_path))
    decrypt_list_of_archives([archive_path], destination_dir, delete=remove_unencrypted, threads=threads)


def extract_archive(source_path, destination_directory_path, partial_extraction_path=None, threads=None, force=False, extract_at_destination=False):
    # Create destination folder if nonexistent or overwrite if --force option used
    helpers.handle_destination_directory_creation(destination_directory_path, force)

    if not threads:
        threads=1

    is_encrypted = helpers.path_target_is_encrypted(source_path)
    archive_files_all = sorted(helpers.get_archives_from_path(source_path, is_encrypted))

    if partial_extraction_path:
        archive_files = listing.relevant_splits_for_partial_path(source_path, partial_extraction_path)
    else:
        archive_files = archive_files_all

    if is_encrypted:
        # It might make sense to check that enough space is available for:
        # archive encryption (encrypted archive size * multiplier) AND unencrypted archive size -> hard to estimate on encrypted archive
        # Workaround would be to require enough space for  "encrypted archive size" * 2
        ensure_sufficient_disk_capacity_for_encryption(archive_files, destination_directory_path)

        # Only pass destination path if encryption output was stored at destination
        # For example: deep integrity check should decrypt the archive in the tmp folder, in order to not touch the archive folder
        destination_path = destination_directory_path if extract_at_destination else None

        decrypt_list_of_archives(archive_files, destination_path, threads=threads)
        archive_files = get_archive_names_after_encryption(archive_files, destination_path)

    ensure_sufficient_disk_capacity_for_extraction(archive_files, destination_directory_path)

    uncompress_and_extract(archive_files, destination_directory_path, threads, partial_extraction_path=partial_extraction_path)

    logging.info("Archive extracted to: " + helpers.get_absolute_path_string(destination_directory_path))
    return destination_directory_path / helpers.filename_without_extensions(source_path)


def uncompress_and_extract(archive_file_paths, destination_directory_path, threads, partial_extraction_path=None, encrypted=False):
    for archive_path in archive_file_paths:
        logging.info(
            f"Extracting {partial_extraction_path if partial_extraction_path else 'all'} "
            f"from archive {helpers.get_absolute_path_string(archive_path)}")

        plzip_cmd = ["plzip", "--decompress", "--stdout", archive_path]
        if threads:
            plzip_cmd.extend(["--threads", str(threads)])

        tar_cmd = ["tar", "-x", "-C", destination_directory_path]
        if partial_extraction_path:
            tar_cmd.append(partial_extraction_path)

        logging.debug(f"Executing command: '{plzip_cmd} | {tar_cmd}'")
        try:
            p1 = subprocess.Popen(plzip_cmd, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(tar_cmd, stdin=p1.stdout)
            p1.stdout.close()
            p2.wait()
        except subprocess.CalledProcessError:
            helpers.terminate_with_message(f"Extraction of archive {archive_path} failed.")

        destination_directory_path_string = helpers.get_absolute_path_string(destination_directory_path)

        logging.info(f"Extracted archive {archive_path.stem} to {destination_directory_path_string}")


def get_archive_names_after_encryption(archive_files, destination_path=None):
    if destination_path:
        return [destination_path / path.with_suffix("").name for path in archive_files]

    return [path.with_suffix("") for path in archive_files]


def ensure_sufficient_disk_capacity_for_extraction(archive_files, extraction_path):
    archives_total_uncompressed_byte_size = 0
    available_bytes = helpers.get_device_available_capacity_from_path(extraction_path)

    for archive_path in archive_files:
        archives_total_uncompressed_byte_size += helpers.get_uncompressed_archive_size_in_bytes(archive_path)

    # multiply by REQUIRED_SPACE_MULTIPLIER for margin
    if available_bytes < archives_total_uncompressed_byte_size * REQUIRED_SPACE_MULTIPLIER:
        helpers.terminate_with_message("Not enough space available for archive extraction.")


def ensure_sufficient_disk_capacity_for_encryption(archive_files, extraction_path):
    total_archive_byte_size = 0
    available_bytes = helpers.get_device_available_capacity_from_path(extraction_path)

    for archive_path in archive_files:
        total_archive_byte_size += helpers.get_size_of_file(archive_path)

    if available_bytes < total_archive_byte_size * REQUIRED_SPACE_MULTIPLIER:
        helpers.terminate_with_message("Not enough space available for archive encryption.")
