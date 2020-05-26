import pytest
from pathlib import Path


@ pytest.fixture(scope="session")
def directory_for_splitting(tmpdir_factory):
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
        # sparse file that doesn't actually take up that amount of space on disk
        multiplier = int(round(byte_size))
        file.write(b"\0" * multiplier)
