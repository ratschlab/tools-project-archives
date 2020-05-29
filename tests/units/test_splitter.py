import pytest
import os
from pathlib import Path

from archiver.splitter import split_directory
from tests.helpers import generate_splitting_directory, compare_nested_array_content_ignoring_order


def test_split_archive(generate_splitting_directory):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 50

    split_archive = split_directory(generate_splitting_directory, MAX_ARCHIVE_SIZE)
    split_archive_relative_paths = split_archive_to_realtive_string_paths(split_archive, generate_splitting_directory.parent)

    expected_result = [['large-test-folder/subfolder-small', 'large-test-folder/file_a.txt', 'large-test-folder/file_b.pdf', 'large-test-folder/subfolder-large/folder_a',
                        'large-test-folder/subfolder-large/folder_b/file_b.txt'], ['large-test-folder/subfolder-large/folder_b/file_c.txt', 'large-test-folder/subfolder-large/folder_b/file_a.pdf']]

    assert len(split_archive_relative_paths) == 2
    # Assertion helper
    compare_nested_array_content_ignoring_order(split_archive_relative_paths, expected_result)


def test_split_archive_large(generate_splitting_directory):
    MAX_ARCHIVE_SIZE = 1000 * 1000 * 1000 * 1

    split_archive = split_directory(generate_splitting_directory, MAX_ARCHIVE_SIZE)
    split_archive_relative_paths = split_archive_to_realtive_string_paths(split_archive, generate_splitting_directory.parent)

    expected_result = [['large-test-folder/subfolder-small', 'large-test-folder/file_a.txt', 'large-test-folder/file_b.pdf', 'large-test-folder/subfolder-large']]

    assert len(split_archive_relative_paths) == 1
    # Assertion helper
    compare_nested_array_content_ignoring_order(split_archive_relative_paths, expected_result)


def test_split_archive_invalid_inputs(generate_splitting_directory):
    with pytest.raises(ValueError):
        list(split_directory(generate_splitting_directory, 1000 * 1000 * -75))

    with pytest.raises(TypeError):
        list(split_directory(generate_splitting_directory, "some string"))

    with pytest.raises(TypeError):
        split_directory()


# MARK: Test helpers

def split_archive_to_realtive_string_paths(archives, tmp_path):
    relative_archives = []

    for archive in archives:
        relative_archive = []
        for path in archive:
            relative_path = path.relative_to(tmp_path).as_posix()
            relative_archive.append(relative_path)
        relative_archives.append(relative_archive)

    return relative_archives
