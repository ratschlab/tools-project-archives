import logging
import subprocess
from pathlib import Path
import os
import multiprocessing

from . import helpers
from .constants import REQUIRED_SPACE_MULTIPLIER, COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTION_ALGORITHM


def _encrypt_list_of_archives_fnc(output_dir, archive_path, encryption_keys, delete):
    output_file = output_dir / archive_path.name if output_dir else archive_path
    output_path = helpers.add_suffix_to_path(output_file, ".gpg")
    encrypt_archive(archive_path, output_path, encryption_keys, delete)
    helpers.create_and_write_file_hash(output_path)


def encrypt_list_of_archives(archive_list, encryption_keys, delete=False, output_dir=None, threads=1):
    eff_threads = min(threads, len(archive_list))

    if eff_threads == 1:
        for archive_path in archive_list:
            _encrypt_list_of_archives_fnc(output_dir, archive_path, encryption_keys, delete)
    else:
        with multiprocessing.Pool(eff_threads) as pool:
            pool.starmap(_encrypt_list_of_archives_fnc, [(output_dir, p, encryption_keys, delete) for p in sorted(archive_list)])


def encrypt_archive(archive_path, output_path, encryption_keys, delete=False):
    logging.info("Encrypting archive: " + helpers.get_absolute_path_string(archive_path))

    argument_encryption_list = []

    for key_path_string in encryption_keys:
        key_path = Path(key_path_string).absolute().as_posix()

        argument_encryption_list.append("--recipient-file")
        argument_encryption_list.append(key_path)

    try:
        subprocess.check_output(["gpg", "--cipher-algo", ENCRYPTION_ALGORITHM, "-z", "0", "--batch", "--output", output_path, "--encrypt"] + argument_encryption_list + [archive_path])
        # Is there a way to overwrite the .tar.lz file instead of creating a new encrypted archive before deleting the old one? Eg. by directly piping
        if delete:
            logging.debug("Deleting unencrypted archive: " + helpers.get_absolute_path_string(archive_path))
            os.remove(archive_path)
    except subprocess.CalledProcessError:
        helpers.terminate_with_message(f"Encryption of archive {archive_path} failed.")

    logging.info(f"Encryption of archive {archive_path} complete.")


def decrypt_list_of_archives(archives, target_directory=None, delete=False):
    for archive_path in sorted(archives):
        decrypt_archive(archive_path, target_directory, delete)


def decrypt_archive(archive_path, target_directory, delete=False):
    logging.info("Decrypting archive: " + helpers.get_absolute_path_string(archive_path))

    if target_directory:
        ensure_sufficient_disk_capacity_for_decryption(archive_path, target_directory)
        output_path = target_directory / archive_path.with_suffix("").name
    else:
        ensure_sufficient_disk_capacity_for_decryption(archive_path, archive_path.parent)
        output_path = archive_path.with_suffix("").absolute()

    try:
        subprocess.check_output(["gpg", "--output", output_path, "--decrypt", archive_path.absolute()])
        if delete:
            logging.info("Deleting encrypted archive: " + helpers.get_absolute_path_string(archive_path))
            os.remove(archive_path)
    except subprocess.CalledProcessError:
        helpers.terminate_with_message("Decryption of archive failed. Make sure the necessary private key added to GPG.")


# MARK: Helpers

def ensure_sufficient_disk_capacity_for_decryption(file_path, extraction_path):
    file_size = helpers.get_size_of_path(file_path)
    available_bytes = helpers.get_device_available_capacity_from_path(extraction_path)

    if available_bytes < file_size * REQUIRED_SPACE_MULTIPLIER:
        helpers.terminate_with_message("Not enough space available for decryption")
