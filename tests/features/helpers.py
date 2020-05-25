from pathlib import Path
import os


# Get paths for directories

def get_archive_path():
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources/test-archive")


def get_folder_path():
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources/test-folder")


def get_corrupted_archive_path(deep=False):
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))

    if deep:
        return dir_path.parent.joinpath("test-ressources/test-archive-corrupted-deep")

    return dir_path.parent.joinpath("test-ressources/test-archive-corrupted")


def get_test_ressources_path():
    """Get path of test directory"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources")


# Other hepers

def compare_array_content_ignoring_order(array_a, array_b):
    """Works for arrays that can be sorted"""
    return sorted(array_a) == sorted(array_b)
