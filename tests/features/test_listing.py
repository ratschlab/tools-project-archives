import pytest
import os
from pathlib import Path

from archiver.listing import create_listing
from . import helpers


def test_list_archive_content_on_directory(capsys):
    archive_dir = helpers.get_archive_path()
    expected_listing = helpers.get_test_ressources_path().joinpath("listing-full.lst")

    create_listing(archive_dir)

    captured_std_out = capsys.readouterr().out

    with open(archive_dir.joinpath(expected_listing), "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_on_archive(capsys):
    archive_dir = helpers.get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_test_ressources_path().joinpath("listing-full.lst")

    create_listing(archive_file)

    captured_std_out = capsys.readouterr().out

    with open(archive_dir.joinpath(expected_listing), "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_subpath(capsys):
    archive_dir = helpers.get_archive_path()
    expected_listing = helpers.get_test_ressources_path().joinpath("listing-partial.lst")

    create_listing(archive_dir, "test-folder/folder-in-archive")

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_on_directory(capsys):
    archive_dir = helpers.get_archive_path()
    expected_listing = helpers.get_test_ressources_path().joinpath("listing-full-deep.lst")

    create_listing(archive_dir, None, True)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_on_archive(capsys):
    archive_dir = helpers.get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_test_ressources_path().joinpath("listing-full-deep.lst")

    create_listing(archive_file, None, True)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


def test_list_archive_content_deep_subpath(capsys):
    archive_dir = helpers.get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")
    expected_listing = helpers.get_test_ressources_path().joinpath("listing-partial-deep.lst")

    create_listing(archive_file, "test-folder/folder-in-archive", True)

    captured_std_out = capsys.readouterr().out

    with open(expected_listing, "r") as file:
        assert compare_listing_text(captured_std_out, file.read())


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
