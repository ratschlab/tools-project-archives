import os
import filecmp
import time
from pathlib import Path

from archiver.extract import extract_archive
from tests import helpers


def test_extract_archive(tmp_path):
    FOLDER_NAME = "test-folder"

    # access existing archive dir
    archive_path = helpers.get_directory_with_name("normal-archive")
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    extraction_path = tmp_path

    # wait until this aciton has completed
    extract_archive(archive_path, extraction_path)
    # TODO: Will be fixed in "develop" branch
    time.sleep(0.1)

    dir_listing = os.listdir(extraction_path)

    # assert listing of extracted folder
    assert dir_listing == [FOLDER_NAME]

    # assert content of extracted file
    assert filecmp.cmp(folder_path.joinpath("file1.txt"), tmp_path.joinpath(FOLDER_NAME + "/file1.txt"))
    assert filecmp.cmp(folder_path.joinpath("folder-in-archive/file2.txt"), tmp_path.joinpath(FOLDER_NAME + "/folder-in-archive/file2.txt"))


def test_extract_split(tmp_path):
    FOLDER_NAME = "large-folder"

    # access existing archive dir
    archive_path = helpers.get_directory_with_name("split-archive")
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    extraction_path = tmp_path

    # wait until this aciton has completed
    extract_archive(archive_path, extraction_path)
    # TODO: Will be fixed in "develop" branch
    time.sleep(0.1)

    dir_listing = os.listdir(extraction_path)

    # assert listing of extracted folder
    assert dir_listing == [FOLDER_NAME]

    # assert content of extracted file
    assert filecmp.cmp(folder_path.joinpath("file_a.txt"), tmp_path.joinpath(FOLDER_NAME + "/file_a.txt"))
    assert filecmp.cmp(folder_path.joinpath("file_b.txt"), tmp_path.joinpath(FOLDER_NAME + "/file_b.txt"))
    assert filecmp.cmp(folder_path.joinpath("subfolder/file_c.txt"), tmp_path.joinpath(FOLDER_NAME + "/subfolder/file_c.txt"))


def test_extract_symlink(tmp_path):
    FOLDER_NAME = "symlink-folder"

    # access existing archive dir
    archive_path = helpers.get_directory_with_name("symlink-archive")
    folder_path = helpers.get_directory_with_name(FOLDER_NAME)
    extraction_path = tmp_path

    # wait until this aciton has completed
    extract_archive(archive_path, extraction_path)
    # TODO: Will be fixed in "develop" branch
    time.sleep(0.1)

    dir_listing = os.listdir(extraction_path)

    # assert listing of extracted folder
    assert dir_listing == [FOLDER_NAME]

    # check if symlink exists
    assert tmp_path.joinpath(FOLDER_NAME + "/link.txt").is_symlink()

    # assert content of extracted file
    assert filecmp.cmp(folder_path.joinpath("file1.txt"), tmp_path.joinpath(FOLDER_NAME + "/file1.txt"))
    assert filecmp.cmp(folder_path.joinpath("folder-in-archive/file2.txt"), tmp_path.joinpath(FOLDER_NAME + "/folder-in-archive/file2.txt"))
