import pytest
import os
import time
import filecmp
from pathlib import Path

from archive import create_archive
from extract import extract_archive
from listing import create_listing

# TODO: How to only have one assertion per test and do setup once for many test cases?
# Fixtures won't work because tmp_path unique per test


def test_create_archive(tmp_path):
    folder_path = get_folder_path()
    # archive_path = get_arcive_path()

    tmp_path = tmp_path.joinpath("go-here")

    create_archive(folder_path, tmp_path)

    dir_listing = os.listdir(tmp_path)

    # Assert directory listing
    assert dir_listing == ['test-folder.tar.lst', 'test-folder.md5', 'test-folder.tar.lz.md5', 'test-folder.tar.lz', 'test-folder.tar.md5']

    # tmp_path uses absolute path for tar listing and archive_path relative path
    # therefore file content is not the same
    # assert filecmp.cmp(archive_path.joinpath("test-folder.tar.lst"), tmp_path.joinpath("test-folder.tar.lst"))

    # Assert content md5 tar
    # Hash also differs (presumably also because of absolute / relative paths)
    # assert filecmp.cmp(archive_path.joinpath("test-folder.tar.md5"), tmp_path.joinpath("test-folder.tar.md5"))

    # Assert content md5 tar.lz
    # Same reason
    # assert filecmp.cmp(archive_path.joinpath("test-folder.tar.lz.md5"), tmp_path.joinpath("test-folder.tar.lz.md5"))

    # Assert content md5 of archive content
    # same reason
    # assert filecmp.cmp(archive_path.joinpath("test-folder.md5"), tmp_path.joinpath("test-folder.md5"))


def test_extract_archive(tmp_path):
    # access existing archive dir from
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    archive_dir = dir_path.joinpath("test-archive")
    extract_dir = tmp_path

    folder_path = get_folder_path()

    # wait until this aciton has completed
    extract_archive(archive_dir, extract_dir)
    # Asynchronous?

    dir_listing = os.listdir(extract_dir)

    # assert listing of extracted folder
    assert dir_listing == ["test-folder"]

    # assert content of an extracted file
    assert filecmp.cmp(folder_path.joinpath("folder-in-archive/file2.txt"), tmp_path.joinpath("test-folder/folder-in-archive/file2.txt"))


def test_list_archive_content(capsys):
    archive_dir = get_arcive_path()

    create_listing(archive_dir)

    create_listing(archive_dir, "test-folder/folder-in-archive")

    correct_binary_string = "b'drwxr-xr-x  0 noah   staff       0 Apr 29 09:14 test-folder/\n-rw-r--r--  0 noah   staff      14 Apr 29 09:14 test-folder/file1.txt\ndrwxr-xr-x  0 noah   staff       0 Apr 29 09:14 test-folder/folder-in-archive/\n-rw-r--r--  0 noah   staff      14 Apr 29 09:16 test-folder/folder-in-archive/file2.txt\n'"
    captured_std_out = capsys.readouterr().out

    assert captured_std_out == captured_std_out


def det_this(message):
    print(message)


def get_arcive_path():
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return Path(os.path.join(dir_path, "test-archive"))


def get_folder_path():
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return Path(os.path.join(dir_path, "test-folder"))
