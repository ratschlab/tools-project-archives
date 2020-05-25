import os
import re
from pathlib import Path

from archiver.archive import create_archive
from . import helpers


def test_create_archive(tmp_path):
    folder_path = helpers.get_folder_path()
    archive_path = helpers.get_archive_path()

    tmp_path = tmp_path.joinpath("go-here")

    create_archive(folder_path, tmp_path, None, 5)

    dir_listing = os.listdir(tmp_path)

    # Test if all files exist
    expected_listing = ['test-folder.tar.lst', 'test-folder.tar.lz.md5', 'test-folder.md5', 'test-folder.tar.lz', 'test-folder.tar.md5']
    assert helpers.compare_array_content_ignoring_order(dir_listing, expected_listing)

    # Test listing of tar
    assert compare_listing_files(archive_path.joinpath("test-folder.tar.lst"), tmp_path.joinpath("test-folder.tar.lst"))

    # Test md5 hash validity for tar
    assert valid_md5_hash_in_file(tmp_path.joinpath("test-folder.tar.md5"))

    # Test md5 hash validity for tar.lz
    assert valid_md5_hash_in_file(tmp_path.joinpath("test-folder.tar.lz.md5"))

    # Assert content md5 of archive content
    assert compare_text_file(archive_path.joinpath("test-folder.md5"), tmp_path.joinpath("test-folder.md5"))


def compare_text_file(file_a_path, file_b_path):
    try:
        with open(file_a_path, "r") as file1, open(file_b_path, "r") as file2:
            return file1.read().rstrip() == file2.read().rstrip()
    except:
        return False


def compare_listing_files(listing_file_path_a, listing_file_path_b):
    try:
        with open(listing_file_path_a, "r") as file1, open(listing_file_path_b, "r") as file2:
            return compare_listing_text(file1.read(), file2.read())
    except:
        return False


def compare_listing_text(listing_a, listing_b):
    listing_a_path_array = get_array_of_last_multiline_text_parts(listing_a)
    listing_b_path_array = get_array_of_last_multiline_text_parts(listing_b)

    return helpers.compare_array_content_ignoring_order(listing_a_path_array, listing_b_path_array)


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
