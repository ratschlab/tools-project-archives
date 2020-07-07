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


def test_create_archive(tmp_path):
    FOLDER_NAME = "test-folder"
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    archive_path = helpers.get_directory_with_name("normal-archive")

    destination_path = tmp_path / "archive-normal"

    create_archive(folder_path, destination_path, None, None, 5)

    dir_listing = os.listdir(destination_path)

    # Test if all files exist
    expected_listing = ['.tar.lst', '.tar.lz.md5', '.md5', '.tar.lz', '.tar.md5']
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [destination_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(destination_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(destination_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), destination_path.joinpath(FOLDER_NAME + ".md5"))


def test_create_archive_split(tmp_path, generate_splitting_directory):
    MAX_ARCHIVE_BYTE_SIZE = 1000 * 1000 * 50
    FOLDER_NAME = "large-test-folder"

    tmp_path = tmp_path.joinpath("archive-split")
    archive_path = helpers.get_directory_with_name("split-archive-ressources")

    create_archive(generate_splitting_directory, tmp_path, None, None, 6, MAX_ARCHIVE_BYTE_SIZE)

    dir_listing = os.listdir(tmp_path)

    # Test if all files exist
    expected_listing = ['.part1.tar.lst', '.part1.tar.lz.md5', '.part1.md5', '.part1.tar.lz', '.part1.tar.md5',
                        '.part2.tar.lst', '.part2.tar.lz.md5', '.part2.md5', '.part2.tar.lz', '.part2.tar.md5']

    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    # Tar listings
    expected_listing_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), archive_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    actual_listing_file_paths = [tmp_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), tmp_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    compare_listing_files(expected_listing_file_paths, actual_listing_file_paths)

    # Test hashes
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.lz.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.lz.md5"))

    # Test md5 of archive content
    expected_hash_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.md5"), archive_path.joinpath(FOLDER_NAME + ".part2.md5")]
    actual_hash_file_paths = [tmp_path.joinpath(FOLDER_NAME + ".part1.md5"), tmp_path.joinpath(FOLDER_NAME + ".part2.md5")]
    compare_hash_files(expected_hash_file_paths, actual_hash_file_paths)


def test_create_symlink_archive(tmp_path, caplog):
    FOLDER_NAME = "symlink-folder"
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    archive_path = helpers.get_directory_with_name("symlink-archive")

    tmp_path = tmp_path.joinpath("archive-symlink")

    create_archive(folder_path, tmp_path, None, None, 2)

    dir_listing = os.listdir(tmp_path)

    expected_warning = "Symlink link.txt found. The link itself will be archived and hashed but not the files that it points to."

    assert expected_warning in caplog.text

    # Test if all files exist
    expected_listing = ['.tar.lst', '.tar.lz.md5', '.md5', '.tar.lz', '.tar.md5']
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [tmp_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), tmp_path.joinpath(FOLDER_NAME + ".md5"))


# test encrypt normal archive
def test_create_encrypted_archive(tmp_path):
    FOLDER_NAME = "test-folder"
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    archive_path = helpers.get_directory_with_name("encrypted-archive")

    # New archive will be saved here
    tmp_path = tmp_path.joinpath("archive-encrypted")

    # Get public keys
    key_directory = helpers.get_directory_with_name("encryption-keys")
    encryption_keys = [key_directory / ENCRYPTION_PUBLIC_KEY_A, key_directory / ENCRYPTION_PUBLIC_KEY_B]

    create_archive(folder_path, tmp_path, None, encryption_keys, 5, None, True)

    # Test if all files exist
    dir_listing = os.listdir(tmp_path)
    expected_listing = [".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz.gpg", ".tar.lz.gpg.md5", ".tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [tmp_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.lz.gpg.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), tmp_path.joinpath(FOLDER_NAME + ".md5"))


# test encrypt with splitting
def test_create_archive_split_encrypted(tmp_path, generate_splitting_directory):
    MAX_ARCHIVE_BYTE_SIZE = 1000 * 1000 * 50
    FOLDER_NAME = "large-test-folder"

    tmp_path = tmp_path.joinpath("archive-split")
    archive_path = helpers.get_directory_with_name("split-archive-ressources")

    # Get public keys
    key_directory = helpers.get_directory_with_name("encryption-keys")
    encryption_keys = [key_directory / ENCRYPTION_PUBLIC_KEY_A, key_directory / ENCRYPTION_PUBLIC_KEY_B]

    create_archive(generate_splitting_directory, tmp_path, None, encryption_keys, 6, MAX_ARCHIVE_BYTE_SIZE, True)

    # Test if all files exist
    dir_listing = os.listdir(tmp_path)
    expected_listing = [".part1.tar.lst", ".part1.tar.lz.md5", ".part1.md5", ".part1.tar.lz.gpg", ".part1.tar.lz.gpg.md5", ".part1.tar.md5",
                        ".part2.tar.lst", ".part2.tar.lz.md5", ".part2.md5", ".part2.tar.lz.gpg", ".part2.tar.lz.gpg.md5", ".part2.tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    # Tar listings
    expected_listing_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), archive_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    actual_listing_file_paths = [tmp_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), tmp_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    compare_listing_files(expected_listing_file_paths, actual_listing_file_paths)

    # Test hashes
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.lz.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.lz.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.lz.gpg.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.lz.gpg.md5"))

    # Test md5 of archive content
    expected_hash_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.md5"), archive_path.joinpath(FOLDER_NAME + ".part2.md5")]
    actual_hash_file_paths = [tmp_path.joinpath(FOLDER_NAME + ".part1.md5"), tmp_path.joinpath(FOLDER_NAME + ".part2.md5")]
    compare_hash_files(expected_hash_file_paths, actual_hash_file_paths)
