import pytest
import os
from pathlib import Path

from archiver.splitter import Splitter


def test_split_archive(directory_for_splitting):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 50

    splitter = Splitter(MAX_ARCHIVE_SIZE)
    splitted_archive = splitter.split_directory(directory_for_splitting)
    splitted_archive_relative_paths = splitted_archive_to_realtive_string_paths(splitted_archive, directory_for_splitting.parent)

    expected_result = [['large-test-folder/subfolder-large/folder_b'], ['large-test-folder/subfolder-large/folder_a',
                                                                        'large-test-folder/file_b.pdf', 'large-test-folder/file_a.txt', 'large-test-folder/subfolder-small']]

    assert splitted_archive_relative_paths == expected_result


def test_split_archive_invalid_inputs(directory_for_splitting):
    with pytest.raises(ValueError):
        Splitter(1000 * 1000 * -75).split_directory(directory_for_splitting)

    with pytest.raises(TypeError):
        Splitter("some string").split_directory(directory_for_splitting)

    with pytest.raises(FileNotFoundError):
        Splitter(1000 * 1000 * 50).split_directory(directory_for_splitting.joinpath("XVofbeco3D9IT"))

    with pytest.raises(TypeError):
        Splitter(1000 * 1000 * 50).split_directory()


# MARK: Test helpers


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
        file.seek(int(round(byte_size)))
        file.write(b"\0")


def splitted_archive_to_realtive_string_paths(archives, tmp_path):
    relative_archives = []

    for archive in archives:
        relative_archive = []
        for path in archive:
            relative_path = path.relative_to(tmp_path).as_posix()
            relative_archive.append(relative_path)
        relative_archives.append(relative_archive)

    return relative_archives
