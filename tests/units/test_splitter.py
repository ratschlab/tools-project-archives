import pytest
import os
from pathlib import Path

from archiver.splitter import split_directory
from archiver.helpers import get_size_of_path
from tests.helpers import generate_splitting_directory, flatten_nested_list, compare_list_content_ignoring_order


def test_split_archive(generate_splitting_directory):
    max_size = 1000 * 1000 * 50

    expected_result = ["large-test-folder/subfolder-small", "large-test-folder/file_a.txt", "large-test-folder/file_b.pdf", "large-test-folder/subfolder-large/folder_a",
                       "large-test-folder/subfolder-large/folder_b/file_b.txt", "large-test-folder/subfolder-large/folder_b/file_c.txt", "large-test-folder/subfolder-large/folder_b/file_a.pdf"]

    assert_archiving_splitting(generate_splitting_directory, max_size, expected_result)


def test_split_archive_large(generate_splitting_directory):
    max_size = 1000 * 1000 * 1000 * 1

    expected_result = ["large-test-folder/subfolder-small", "large-test-folder/file_a.txt", "large-test-folder/file_b.pdf", "large-test-folder/subfolder-large"]

    assert_archiving_splitting(generate_splitting_directory, max_size, expected_result)


def test_split_archive_invalid_inputs(generate_splitting_directory):
    with pytest.raises(ValueError):
        list(split_directory(generate_splitting_directory, 1000 * 1000 * -75))

    with pytest.raises(TypeError):
        list(split_directory(generate_splitting_directory, "some string"))

    with pytest.raises(TypeError):
        split_directory()


# MARK: Test helpers

def assert_archiving_splitting(path, max_size, expected_result):
    split_archive = split_directory(path, max_size)
    split_archive_relative_paths = relative_strings_from_archives_list(split_archive, path.parent)
    split_archive_relative_paths_flat = flatten_nested_list(split_archive_relative_paths)

    assert len(split_archive_relative_paths_flat) == len(expected_result)
    assert size_of_all_parts_below_maximum(split_archive, max_size)

    # Assertion helper
    compare_list_content_ignoring_order(split_archive_relative_paths_flat, expected_result)


def relative_strings_from_archives_list(archives, relative_to_path):
    # Return a list in order to assert length in test
    return [relatative_string_from_path_list(paths, relative_to_path) for paths in archives]


def relatative_string_from_path_list(path_list, relative_to_path):
    return [path.relative_to(relative_to_path).as_posix() for path in path_list]


def size_of_all_parts_below_maximum(archives, max_size):
    for archive_paths in archives:
        if size_of_path_list(archive_paths) > max_size:
            return False

    return True


def size_of_path_list(path_list):
    archive_size = 0

    for path in path_list:
        archive_size += get_size_of_path(path)

    return archive_size
