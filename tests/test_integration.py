import pytest
import os
from pathlib import Path

from archiver.archive import create_archive
from archiver.extract import extract_archive
from archiver.listing import create_listing

# TODO: How to only have one assertion per test and do setup once for many test cases?
# Fixtures won't work because tmp_path unique per test


def test_create_archive(tmp_path):
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    archive_dir = Path(os.path.join(dir_path, "test-folder"))

    tmp_path = tmp_path.joinpath("go-here")

    create_archive(archive_dir, tmp_path)

    dir_listing = os.listdir(tmp_path)

    assert dir_listing == ["test-folder.tar.lst", "test-folder.tar.lz.md5",
                           "test-folder.tar.lz", "test-folder.tar.md5", "test-folder.md5"]

    # do many assertions

    # assert content tar listing
    # assert content md5 tar
    # assert content md5 tar.lz
    # assert content md5 of archive content


def test_extract_archive(tmp_path):
    # access existing archive dir from
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    archive_dir = Path(os.path.join(dir_path, "test-archive"))

    extract_archive(archive_dir, tmp_path)

    destination_path = tmp_path.joinpath("test-folder")

    assert 1

    # assert listing of extracted folder
    # assert content / hash of an extracted file


def test_list_archive_content():
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    archive_dir = Path(os.path.join(dir_path, "test-archive"))

    create_listing(archive_dir)
    # capture stdout
    # assert output is correct up

    create_listing(archive_dir, "test-folder/folder-in-archive")
    # capture stdout
    # assert output is correct up
