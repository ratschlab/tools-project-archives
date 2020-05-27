import pytest
import os
from pathlib import Path

from archiver.listing import create_listing
from tests import helpers

# Constants
SPLIT = True
DEEP = True


def test_list_archive_content_on_directory(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    expected_listing = helpers.get_listing_with_name("listing-full.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    with open(archive_dir.joinpath(expected_listing), "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_on_split_directory(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-full-split.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    with open(archive_dir.joinpath(expected_listing), "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_on_archive(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-full.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    with open(archive_dir.joinpath(expected_listing), "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_on_split_archive(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    archive_file = archive_dir.joinpath("large-folder.part3.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-split-part3.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    with open(archive_dir.joinpath(expected_listing), "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_subpath(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    expected_listing = helpers.get_listing_with_name("listing-partial.lst")

    create_listing(archive_dir, "test-folder/folder-in-archive")

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_subpath_split(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-partial.lst")

    create_listing(archive_dir, "large-folder/subfolder")

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_on_directory(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    expected_listing = helpers.get_listing_with_name("listing-full-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_on_split_directory(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_on_archive(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-full-deep.lst")

    create_listing(archive_file, None, DEEP)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_subpath(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-partial-deep.lst")

    create_listing(archive_file, "test-folder/folder-in-archive", DEEP)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_subpath_split(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-partial-deep.lst")

    create_listing(archive_dir, "large-folder/subfolder", DEEP)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


# MARK: Test helpers

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
