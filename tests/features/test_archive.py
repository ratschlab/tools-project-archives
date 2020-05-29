import os
import re
from pathlib import Path
import pytest

from archiver.archive import create_archive
from tests import helpers
from tests.helpers import generate_splitting_directory


def test_create_archive(tmp_path):
    FOLDER_NAME = "test-folder"
    folder_path = helpers.get_directory_with_name("test-folder")
    archive_path = helpers.get_directory_with_name("normal-archive")

    tmp_path = tmp_path.joinpath("archive-normal")

    create_archive(folder_path, tmp_path, None, 5)

    dir_listing = os.listdir(tmp_path)

    # Test if all files exist
    expected_listing = ['.tar.lst', '.tar.lz.md5', '.md5', '.tar.lz', '.tar.md5']
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    assert compare_listing_files(archive_path.joinpath(FOLDER_NAME + ".tar.lst"), tmp_path.joinpath(FOLDER_NAME + ".tar.lst"))

    # Test hash validity
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))

    # Test md5 of archive content
    assert compare_text_file(archive_path.joinpath(FOLDER_NAME + ".md5"), tmp_path.joinpath(FOLDER_NAME + ".md5"))


def test_create_archive_splitted(tmp_path, generate_splitting_directory):
    MAX_ARCHIVE_BYTE_SIZE = 1000 * 1000 * 50
    FOLDER_NAME = "large-test-folder"

    tmp_path = tmp_path.joinpath("archive-splitted")
    archive_path = helpers.get_directory_with_name("split-archive-ressources")

    create_archive(generate_splitting_directory, tmp_path, None, 6, MAX_ARCHIVE_BYTE_SIZE)

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
    compare_files_ignoring_order(expected_listing_file_paths, actual_listing_file_paths, compare_listing_files)

    # Test hashes
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part1.tar.lz.md5"))
    assert valid_md5_hash_in_file(tmp_path.joinpath(FOLDER_NAME + ".part2.tar.lz.md5"))

    # Test md5 of archive content
    expected_hash_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.md5"), archive_path.joinpath(FOLDER_NAME + ".part1.md5")]
    actual_hash_file_paths = [tmp_path.joinpath(FOLDER_NAME + ".part1.md5"), tmp_path.joinpath(FOLDER_NAME + ".part2.md5")]
    compare_files_ignoring_order(expected_hash_file_paths, actual_hash_file_paths, compare_text_file)


# MARK: Test helpers

def add_prefix_to_list_elements(element_list, prefix):
    return list(map(lambda element_content: prefix + element_content, element_list))


def compare_text_file(file_a_path, file_b_path):
    try:
        with open(file_a_path, "r") as file1, open(file_b_path, "r") as file2:
            return file1.read().rstrip() == file2.read().rstrip()
    except:
        return False


def compare_files_ignoring_order(expected_path_list, actual_path_list, compare):
    for expected_path in expected_path_list:
        match = False

        for actual_path in actual_path_list:
            if compare(expected_path, actual_path):
                match = True
                break

        if not match:
            assert False

    assert True


def compare_listing_files(file_path_a, file_path_b):
    try:
        with open(file_path_a, "r") as file1, open(file_path_b, "r") as file2:
            # compare_listing_text(file1.read(), file2.read())
            listing_a_path_array = get_array_of_last_multiline_text_parts(file1.read())
            listing_b_path_array = get_array_of_last_multiline_text_parts(file2.read())

            return sorted(listing_a_path_array) == sorted(listing_b_path_array)
    except:
        return False


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
