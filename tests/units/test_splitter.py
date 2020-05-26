import pytest
import os
from pathlib import Path

from archiver.splitter import split_directory
from .helpers import create_file_with_size


def test_split_archive(directory_for_splitting):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 50

    splitted_archive = split_directory(directory_for_splitting, MAX_ARCHIVE_SIZE)
    splitted_archive_relative_paths = splitted_archive_to_realtive_string_paths(splitted_archive, directory_for_splitting.parent)

    expected_result = [['large-test-folder/subfolder-small', 'large-test-folder/file_a.txt', 'large-test-folder/file_b.pdf', 'large-test-folder/subfolder-large/folder_a',
                        'large-test-folder/subfolder-large/folder_b/file_b.txt'], ['large-test-folder/subfolder-large/folder_b/file_c.txt', 'large-test-folder/subfolder-large/folder_b/file_a.pdf']]

    assert len(splitted_archive_relative_paths) == 2
    assert sorted(splitted_archive_relative_paths) == sorted(expected_result)


def test_split_archive_large(directory_for_splitting):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 1000 * 1

    splitted_archive = split_directory(directory_for_splitting, MAX_ARCHIVE_SIZE)
    splitted_archive_relative_paths = splitted_archive_to_realtive_string_paths(splitted_archive, directory_for_splitting.parent)

    expected_result = [['large-test-folder/subfolder-small', 'large-test-folder/file_a.txt', 'large-test-folder/file_b.pdf',
                        'large-test-folder/subfolder-large/folder_b', 'large-test-folder/subfolder-large/folder_a/file_b.txt', 'large-test-folder/subfolder-large/folder_a/file_a.pdf']]

    assert len(splitted_archive_relative_paths) == 1
    assert sorted(splitted_archive_relative_paths) == sorted(expected_result)


def test_split_archive_invalid_inputs(directory_for_splitting):
    with pytest.raises(ValueError):
        list(split_directory(directory_for_splitting, 1000 * 1000 * -75))

    with pytest.raises(TypeError):
        list(split_directory(directory_for_splitting, "some string"))

    with pytest.raises(TypeError):
        split_directory()

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


def splitted_archive_to_realtive_string_paths(archives, tmp_path):
    relative_archives = []

    for archive in archives:
        relative_archive = []
        for path in archive:
            relative_path = path.relative_to(tmp_path).as_posix()
            relative_archive.append(relative_path)
        relative_archives.append(relative_archive)

    return relative_archives
