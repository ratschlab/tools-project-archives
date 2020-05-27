import pytest
from pathlib import Path
import os


@ pytest.fixture(scope="session")
def generate_splitting_directory(tmpdir_factory):
    """Programmatically generate folder for splitting"""
    tmp_path = tmpdir_factory.mktemp("directory_for_splitting")
    test_path = Path(tmp_path).joinpath("large-test-folder")
    test_path.mkdir()

    # Create subfolders
    subpath_a = test_path.joinpath("subfolder-large")
    subpath_a.mkdir()
    subpath_b = test_path.joinpath("subfolder-small")
    subpath_b.mkdir()

    # Create files main folder
    file_a = test_path.joinpath("file_a.txt")
    create_file_with_size(file_a, 1000 * 1000 * 5)
    file_b = test_path.joinpath("file_b.pdf")
    create_file_with_size(file_b, 1000 * 1000 * 7)

    # Create files subfolders
    file_subfolder_large_a = subpath_b.joinpath("file_a.txt")
    create_file_with_size(file_subfolder_large_a, 1000 * 1000 * 1)
    file_subfolder_large_b = subpath_b.joinpath("file_a.txt")
    create_file_with_size(file_subfolder_large_b, 1000 * 1000 * 1)

    subfolder_large_folder_a = subpath_a.joinpath("folder_a")
    subfolder_large_folder_a.mkdir()
    subfolder_large_folder_b = subpath_a.joinpath("folder_b")
    subfolder_large_folder_b.mkdir()

    subfolder_large_folder_a_file_a = subfolder_large_folder_a.joinpath("file_a.pdf")
    create_file_with_size(subfolder_large_folder_a_file_a, 1000 * 1000 * 17)
    subfolder_large_folder_a_file_b = subfolder_large_folder_a.joinpath("file_b.txt")
    create_file_with_size(subfolder_large_folder_a_file_b, 1000 * 1000 * 9)

    subfolder_large_folder_b_file_a = subfolder_large_folder_b.joinpath("file_a.pdf")
    create_file_with_size(subfolder_large_folder_b_file_a, 1000 * 1000 * 17)
    subfolder_large_folder_b_file_b = subfolder_large_folder_b.joinpath("file_b.txt")
    create_file_with_size(subfolder_large_folder_b_file_b, 1000 * 1000 * 9)
    subfolder_large_folder_b_file_c = subfolder_large_folder_b.joinpath("file_c.txt")
    create_file_with_size(subfolder_large_folder_b_file_c, 1000 * 1000 * 15)

    return test_path


def create_file_with_size(path, byte_size):
    with open(path, "wb") as file:
        multiplier = int(round(byte_size))
        file.write(b"\0" * multiplier)


def compare_nested_array_content_ignoring_order(array_a, array_b):
    """Works for arrays that can be sorted"""
    array_a_sorted_inner = map(lambda element: sorted(element), array_a)
    array_b_sorted_inner = map(lambda element: sorted(element), array_b)

    return sorted(array_a_sorted_inner) == sorted(array_b_sorted_inner)


def compare_array_content_ignoring_order(array_a, array_b):
    """Works for arrays that can be sorted"""
    return sorted(array_a) == sorted(array_b)


# MARK: Test ressources helpers

RESSOURCES_NAME = "test-ressources"


def get_test_ressources_path():
    """Get path of test ressources directory"""
    current_dir_path = get_current_directory()
    return current_dir_path.joinpath(RESSOURCES_NAME)


def get_directory_with_name(dir_name):
    """Get directory for tests by name"""
    current_dir_path = get_current_directory()
    ressource_dir_path = current_dir_path.joinpath(f"{RESSOURCES_NAME}/{dir_name}")

    if not ressource_dir_path.is_dir():
        raise NotADirectoryError(f"Could not locate listing file with name: {dir_name}")

    return ressource_dir_path


def get_listing_with_name(listing_name):
    """Get an expected listing by name"""
    current_dir_path = get_current_directory()
    file_path = current_dir_path.joinpath(f"{RESSOURCES_NAME}/listings/{listing_name}")

    if not file_path.is_file():
        raise FileNotFoundError(f"Could not locate listing file with name: {listing_name}")

    return file_path


def get_current_directory():
    return Path(os.path.dirname(os.path.realpath(__file__)))
