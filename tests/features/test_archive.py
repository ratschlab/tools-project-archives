import os
import re
from pathlib import Path
import pytest

from archiver.archive import create_archive
from tests import helpers
from tests.helpers import generate_splitting_directory

ENCRYPTION_PUBLIC_KEY_A = "public.gpg"
ENCRYPTION_PUBLIC_KEY_B = "public_second.pub"


def test_create_archive(tmp_path):
    FOLDER_NAME = "test-folder"
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    archive_path = helpers.get_directory_with_name("normal-archive")

    tmp_path = tmp_path.joinpath("archive-normal")

    create_archive(folder_path, tmp_path, None, None, 5)

    dir_listing = os.listdir(tmp_path)

    # Test if all files exist
    expected_listing = ['.tar.lst', '.tar.lz.md5', '.md5', '.tar.lz', '.tar.md5']
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [tmp_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), tmp_path.joinpath(FOLDER_NAME + ".md5"))


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
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

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
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

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

    create_archive(folder_path, tmp_path, None, encryption_keys, 5)

    # Test if all files exist
    dir_listing = os.listdir(tmp_path)
    expected_listing = [".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz.gpg", ".tar.lz.gpg.md5", ".tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

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

    create_archive(generate_splitting_directory, tmp_path, None, encryption_keys, 6, MAX_ARCHIVE_BYTE_SIZE)

    # Test if all files exist
    dir_listing = os.listdir(tmp_path)
    expected_listing = [".part1.tar.lst", ".part1.tar.lz.md5", ".part1.md5", ".part1.tar.lz.gpg", ".part1.tar.lz.gpg.md5", ".part1.tar.md5",
                        ".part2.tar.lst", ".part2.tar.lz.md5", ".part2.md5", ".part2.tar.lz.gpg", ".part2.tar.lz.gpg.md5", ".part2.tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

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


# MARK: Test helpers


def add_prefix_to_list_elements(element_list, prefix):
    return map(lambda element_content: prefix + element_content, element_list)


def compare_text_file_ignoring_order(file_a_path, file_b_path):
    with open(file_a_path, "r") as file1, open(file_b_path, "r") as file2:
        helpers.compare_array_content_ignoring_order(file1.readlines(), file2.readlines())


def compare_hash_files(expected_path_list, actual_path_list):
    expected_hash_list = []
    actual_hash_list = []

    for path in expected_path_list:
        with open(path, "r") as hash_file:
            for line in hash_file:
                expected_hash_list.append(line.rstrip())

    for path in actual_path_list:
        with open(path, "r") as hash_file:
            for line in hash_file:
                actual_hash_list.append(line.rstrip())

    helpers.compare_array_content_ignoring_order(expected_hash_list, actual_hash_list)


def compare_listing_files(expected_path_list, actual_path_list):
    expected_union = []
    actual_union = []

    for path in expected_path_list:
        with open(path, "r") as listing_file:
            expected_union += get_array_of_last_multiline_text_parts(listing_file.read())

    for path in actual_path_list:
        with open(path, "r") as listing_file:
            actual_union += get_array_of_last_multiline_text_parts(listing_file.read())

    helpers.compare_array_content_ignoring_order(expected_union, actual_union)


def compare_listing_text(listing_a, listing_b):
    listing_a_path_array = get_array_of_last_multiline_text_parts(listing_a)
    listing_b_path_array = get_array_of_last_multiline_text_parts(listing_b)

    # Assertion helper
    helpers.compare_array_content_ignoring_order(listing_a_path_array, listing_b_path_array)


def get_array_of_last_multiline_text_parts(multiline_text):
    parts_array = []

    for line in multiline_text.splitlines():
        # ignore empty lines
        try:
            path = line.split()[-1]
            parts_array.append(path)
        except:
            pass

    return parts_array


def valid_md5_hash_in_file(hash_file_path):
    """Returns true if file contains valid md5 hash"""
    try:
        with open(hash_file_path, "r") as file:
            file_content = file.read().rstrip()
            if re.search(r"([a-fA-F\d]{32})", file_content):
                return True

            return False
    except:
        return False
