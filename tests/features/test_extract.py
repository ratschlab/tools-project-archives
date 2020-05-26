import os
import filecmp
import time
from pathlib import Path

from archiver.extract import extract_archive
from . import helpers


def test_extract_archive(tmp_path):
    # access existing archive dir
    archive_path = helpers.get_archive_path()
    folder_path = helpers.get_folder_path()
    extraction_path = tmp_path

    # wait until this aciton has completed
    extract_archive(archive_path, extraction_path)
    # TODO: Find fix for this
    time.sleep(0.1)

    dir_listing = os.listdir(extraction_path)

    # assert listing of extracted folder
    assert dir_listing == ["test-folder"]

    # assert content of extracted file
    assert filecmp.cmp(folder_path.joinpath("file1.txt"), tmp_path.joinpath("test-folder/file1.txt"))
    assert filecmp.cmp(folder_path.joinpath("folder-in-archive/file2.txt"), tmp_path.joinpath("test-folder/folder-in-archive/file2.txt"))


def test_extract_splitted(tmp_path):
    SPLITTED = True
    FOLDER_NAME = "large-folder"

    # access existing archive dir
    archive_path = helpers.get_archive_path(SPLITTED)
    folder_path = helpers.get_folder_path(SPLITTED)
    extraction_path = tmp_path

    # wait until this aciton has completed
    extract_archive(archive_path, extraction_path)
    # TODO: Find fix for this
    time.sleep(0.1)

    dir_listing = os.listdir(extraction_path)

    # assert listing of extracted folder
    assert dir_listing == [FOLDER_NAME]

    # assert content of extracted file
    assert filecmp.cmp(folder_path.joinpath("file_a.txt"), tmp_path.joinpath(FOLDER_NAME + "/file_a.txt"))
    assert filecmp.cmp(folder_path.joinpath("file_b.txt"), tmp_path.joinpath(FOLDER_NAME + "/file_b.txt"))
    assert filecmp.cmp(folder_path.joinpath("subfolder/file_c.txt"), tmp_path.joinpath(FOLDER_NAME + "/subfolder/file_c.txt"))
