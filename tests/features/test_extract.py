import os
import filecmp
import time
from pathlib import Path

from archiver.extract import extract_archive


def test_extract_archive(tmp_path):
    # access existing archive dir
    archive_path = get_archive_path()
    folder_path = get_folder_path()
    extraction_path = tmp_path

    # wait until this aciton has completed
    extract_archive(archive_path, extraction_path)
    # TODO: Find fix for this
    time.sleep(0.1)

    dir_listing = os.listdir(extraction_path)

    # assert listing of extracted folder
    assert dir_listing == ["test-folder"]

    # assert content of extracted file
    assert filecmp.cmp(folder_path.joinpath("folder-in-archive/file2.txt"), tmp_path.joinpath("test-folder/folder-in-archive/file2.txt"))


def get_archive_path():
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources/test-archive")


def get_folder_path():
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources/test-folder")
