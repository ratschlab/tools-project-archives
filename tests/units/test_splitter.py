import pytest
import os
from pathlib import Path

from archiver.splitter import split_directory
from tests.generate_folder import directory_for_splitting
from . import helpers


def test_split_archive(directory_for_splitting):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 50

    splitted_archive = split_directory(directory_for_splitting, MAX_ARCHIVE_SIZE)
    splitted_archive_relative_paths = splitted_archive_to_realtive_string_paths(splitted_archive, directory_for_splitting.parent)

    expected_result = [['large-test-folder/subfolder-small', 'large-test-folder/file_a.txt', 'large-test-folder/file_b.pdf', 'large-test-folder/subfolder-large/folder_a',
                        'large-test-folder/subfolder-large/folder_b/file_b.txt'], ['large-test-folder/subfolder-large/folder_b/file_c.txt', 'large-test-folder/subfolder-large/folder_b/file_a.pdf']]

    assert len(splitted_archive_relative_paths) == 2
    assert helpers.compare_nested_array_content_ignoring_order(splitted_archive_relative_paths, expected_result)


def test_split_archive_large(directory_for_splitting):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 1000 * 1

    splitted_archive = split_directory(directory_for_splitting, MAX_ARCHIVE_SIZE)
    splitted_archive_relative_paths = splitted_archive_to_realtive_string_paths(splitted_archive, directory_for_splitting.parent)

    expected_result = [['large-test-folder/subfolder-small', 'large-test-folder/file_a.txt', 'large-test-folder/file_b.pdf',
                        'large-test-folder/subfolder-large/folder_b', 'large-test-folder/subfolder-large/folder_a/file_b.txt', 'large-test-folder/subfolder-large/folder_a/file_a.pdf']]

    assert len(splitted_archive_relative_paths) == 1
    assert helpers.compare_nested_array_content_ignoring_order(splitted_archive_relative_paths, expected_result)


def test_split_archive_invalid_inputs(directory_for_splitting):
    with pytest.raises(ValueError):
        list(split_directory(directory_for_splitting, 1000 * 1000 * -75))

    with pytest.raises(TypeError):
        list(split_directory(directory_for_splitting, "some string"))

    with pytest.raises(TypeError):
        split_directory()


# MARK: Test helpers

def splitted_archive_to_realtive_string_paths(archives, tmp_path):
    relative_archives = []

    for archive in archives:
        relative_archive = []
        for path in archive:
            relative_path = path.relative_to(tmp_path).as_posix()
            relative_archive.append(relative_path)
        relative_archives.append(relative_archive)

    return relative_archives
