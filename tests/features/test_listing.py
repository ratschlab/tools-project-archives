import pytest
import os
from pathlib import Path

from archiver.listing import create_listing
from tests import helpers

# Constants
DEEP = True


def test_list_archive_content_on_directory(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    expected_listing = helpers.get_listing_with_name("listing-full.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_encrypted_directory(capsys):
    archive_dir = helpers.get_directory_with_name("encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-full.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_split_directory(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-full-split.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_split_encrypted_directory(capsys):
    archive_dir = helpers.get_directory_with_name("split-encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-full-split.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_archive(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-full.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_encrypted_archive(capsys):
    archive_dir = helpers.get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")
    expected_listing = helpers.get_listing_with_name("listing-full.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_split_archive(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    archive_file = archive_dir.joinpath("large-folder.part3.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-split-part3.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_on_split_encrypted_archive(capsys):
    archive_dir = helpers.get_directory_with_name("split-encrypted-archive")
    archive_file = archive_dir.joinpath("large-folder.part3.tar.lz.gpg")
    expected_listing = helpers.get_listing_with_name("listing-split-part3.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_subpath(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    expected_listing = helpers.get_listing_with_name("listing-partial.lst")

    create_listing(archive_dir, "test-folder/folder-in-archive")

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_subpath_encrypte(capsys):
    archive_dir = helpers.get_directory_with_name("encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-partial.lst")

    create_listing(archive_dir, "test-folder/folder-in-archive")

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_subpath_split(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-partial.lst")

    create_listing(archive_dir, "large-folder/subfolder")

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_subpath_split_encrypted(capsys):
    archive_dir = helpers.get_directory_with_name("split-encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-partial.lst")

    create_listing(archive_dir, "large-folder/subfolder")

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_on_directory(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    expected_listing = helpers.get_listing_with_name("listing-full-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_on_encrypted_directory(capsys):
    archive_dir = helpers.get_directory_with_name("encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-full-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_on_split_directory(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_on_split_encrypted_directory(capsys):
    archive_dir = helpers.get_directory_with_name("split-encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_on_archive(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-full-deep.lst")

    create_listing(archive_file, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_on_encrypted_archive(capsys):
    archive_dir = helpers.get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")
    expected_listing = helpers.get_listing_with_name("listing-full-deep.lst")

    create_listing(archive_file, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_subpath(capsys):
    archive_dir = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_listing_with_name("listing-partial-deep.lst")

    create_listing(archive_file, "test-folder/folder-in-archive", DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_encrypted_subpath(capsys):
    archive_dir = helpers.get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")
    expected_listing = helpers.get_listing_with_name("listing-partial-deep.lst")

    create_listing(archive_file, "test-folder/folder-in-archive", DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_subpath_split(capsys):
    archive_dir = helpers.get_directory_with_name("split-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-partial-deep.lst")

    create_listing(archive_dir, "large-folder/subfolder", DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_deep_subpath_encrypted_split(capsys):
    archive_dir = helpers.get_directory_with_name("split-encrypted-archive")
    expected_listing = helpers.get_listing_with_name("listing-split-partial-deep.lst")

    create_listing(archive_dir, "large-folder/subfolder", DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_symlink(capsys):
    archive_dir = helpers.get_directory_with_name("symlink-archive")
    expected_listing = helpers.get_listing_with_name("listing-symlink.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


def test_list_archive_content_symlink_deep(capsys):
    archive_dir = helpers.get_directory_with_name("symlink-archive")
    expected_listing = helpers.get_listing_with_name("listing-symlink-deep.lst")

    create_listing(archive_dir, None, DEEP)

    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_listing, captured_std_out)


# MARK: Test helpers

def compare_listing_path_to_output(listing_path, output):
    with open(listing_path, "r") as file:
        compare_listing_text(output, file.read())


def compare_listing_text(listing_a, listing_b):
    listing_a_path_array = get_array_of_last_multiline_text_parts(listing_a)
    listing_b_path_array = get_array_of_last_multiline_text_parts(listing_b)

    # Assertion helper
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
