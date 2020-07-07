import os
import re
from pathlib import Path
import pytest

from archiver.archive import create_archive
from tests import helpers
from .archiving_helpers import add_prefix_to_list_elements, compare_listing_files, valid_md5_hash_in_file, compare_text_file_ignoring_order, compare_hash_files
from tests.helpers import generate_splitting_directory

ENCRYPTION_PUBLIC_KEY_A = "public.gpg"
ENCRYPTION_PUBLIC_KEY_B = "public_second.pub"

ENCRYPTED_HASH_FILENAMES = [".tar.md5", ".tar.lz.md5", ".tar.lz.gpg.md5"]
UNENCRYPTED_HASH_FILENAMES = [".tar.md5", ".tar.lz.md5"]
SPLIT_ENCRYPTED_HASH_FILENAMES = [".part1.tar.md5", ".part2.tar.md5", ".part1.tar.lz.md5", ".part2.tar.lz.md5", ".part1.tar.lz.gpg.md5", ".part2.tar.lz.gpg.md5"]
SPLIT_UNENCRYPTED_HASH_FILENAMES = [".part1.tar.md5", ".part2.tar.md5", ".part1.tar.lz.md5", ".part2.tar.lz.md5"]

ENCRYPTED_LISTING = [".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz.gpg", ".tar.lz.gpg.md5", ".tar.md5"]
UNENCRYPTED_LISTING = ['.tar.lst', '.tar.lz.md5', '.md5', '.tar.lz', '.tar.md5']
SPLIT_UNENCRYPTED_LISTINGS = ['.part1.tar.lst', '.part1.tar.lz.md5', '.part1.md5', '.part1.tar.lz', '.part1.tar.md5',
                              '.part2.tar.lst', '.part2.tar.lz.md5', '.part2.md5', '.part2.tar.lz', '.part2.tar.md5']
SPLIT_ENCRYPTED_LISTINGS = [".part1.tar.lst", ".part1.tar.lz.md5", ".part1.md5", ".part1.tar.lz.gpg", ".part1.tar.lz.gpg.md5", ".part1.tar.md5",
                            ".part2.tar.lst", ".part2.tar.lz.md5", ".part2.md5", ".part2.tar.lz.gpg", ".part2.tar.lz.gpg.md5", ".part2.tar.md5"]


def test_create_archive(tmp_path):
    folder_name = "test-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("normal-archive")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5)
    assert_successful_archive_creation(destination_path, archive_path, folder_name)


def test_create_archive_split(tmp_path, generate_splitting_directory):
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(source_path, destination_path, compression=6, splitting=max_size)
    assert_successful_split_archive_creation(destination_path, archive_path, folder_name)


def test_create_symlink_archive(tmp_path, caplog):
    folder_name = "symlink-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("symlink-archive")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5)
    assert_successful_archive_creation(destination_path, archive_path, folder_name)

    expected_warning = "Symlink link.txt found. The link itself will be archived and hashed but not the files that it points to."
    assert expected_warning in caplog.text


def test_create_encrypted_archive(tmp_path):
    folder_name = "test-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / "name-of-destination-folder"
    keys = get_public_key_paths()

    create_archive(folder_path, destination_path, encryption_keys=keys, compression=5, remove_unencrypted=True)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, encrypted=True)


def test_create_archive_split_encrypted(tmp_path, generate_splitting_directory):
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"
    keys = get_public_key_paths()

    create_archive(source_path, destination_path, encryption_keys=keys, compression=6, remove_unencrypted=True, splitting=max_size)
    assert_successful_split_archive_creation(destination_path, archive_path, folder_name, encrypted=True)


# MARK: Helpers

def assert_successful_archive_creation(destination_path, archive_path, folder_name, encrypted=False):
    expected_listing = ENCRYPTED_LISTING if encrypted else UNENCRYPTED_LISTING

    dir_listing = os.listdir(destination_path)
    expected_named_listing = add_prefix_to_list_elements(expected_listing, folder_name)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    compare_listing_files([archive_path / (folder_name + ".tar.lst")], [destination_path / (folder_name + ".tar.lst")])

    hash_filenames = ENCRYPTED_HASH_FILENAMES if encrypted else UNENCRYPTED_HASH_FILENAMES
    hash_file_paths = create_full_filename_path(hash_filenames, destination_path, folder_name)
    assert_hashes_in_file_list_valid(hash_file_paths)

    compare_text_file_ignoring_order(archive_path / (folder_name + ".md5"), destination_path / (folder_name + ".md5"))


def assert_successful_split_archive_creation(destination_path, archive_path, folder_name, encrypted=False):
    expected_listing = SPLIT_ENCRYPTED_LISTINGS if encrypted else SPLIT_UNENCRYPTED_LISTINGS

    dir_listing = os.listdir(destination_path)
    expected_named_listing = add_prefix_to_list_elements(expected_listing, folder_name)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    expected_listing_file_paths = [archive_path / (folder_name + ".part1.tar.lst"), archive_path / (folder_name + ".part2.tar.lst")]
    actual_listing_file_paths = [destination_path / (folder_name + ".part1.tar.lst"), destination_path / (folder_name + ".part2.tar.lst")]
    compare_listing_files(expected_listing_file_paths, actual_listing_file_paths)

    hash_filenames = SPLIT_ENCRYPTED_HASH_FILENAMES if encrypted else SPLIT_UNENCRYPTED_HASH_FILENAMES
    hash_file_paths = create_full_filename_path(hash_filenames, destination_path, folder_name)
    assert_hashes_in_file_list_valid(hash_file_paths)

    expected_hash_file_paths = [archive_path / (folder_name + ".part1.md5"), archive_path / (folder_name + ".part2.md5")]
    actual_hash_file_paths = [destination_path / (folder_name + ".part1.md5"), destination_path / (folder_name + ".part2.md5")]
    compare_hash_files(expected_hash_file_paths, actual_hash_file_paths)


def assert_hashes_in_file_list_valid(hash_files):
    # Not optimal since assert won't tell you which path is invalid
    valid = True
    for path in hash_files:
        if not valid_md5_hash_in_file(path):
            valid = False

    assert valid


def get_public_key_paths():
    key_directory = helpers.get_directory_with_name("encryption-keys")
    return [key_directory / ENCRYPTION_PUBLIC_KEY_A, key_directory / ENCRYPTION_PUBLIC_KEY_B]


def create_full_filename_path(filenames, directory, prefix):
    prefixed = add_prefix_to_list_elements(filenames, prefix)
    return [directory / filename for filename in prefixed]
