import os
import re
from pathlib import Path
import pytest

from archiver.archive import create_archive
from tests import helpers
from .archiving_helpers import assert_successful_archive_creation, get_public_key_paths
from tests.helpers import generate_splitting_directory


def test_create_archive(tmp_path):
    folder_name = "test-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("normal-archive")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5)
    assert_successful_archive_creation(destination_path, archive_path, folder_name)


def test_create_archive_split(tmp_path, generate_splitting_directory):
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(source_path, destination_path, compression=6, splitting=max_size)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, split=True)


def test_create_symlink_archive(tmp_path, caplog):
    folder_name = "symlink-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("symlink-archive")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5)
    assert_successful_archive_creation(destination_path, archive_path, folder_name)

    expected_warning = "Symlink link.txt found. The link itself will be archived and hashed but not the files that it points to."
    assert expected_warning in caplog.text


def test_create_encrypted_archive(tmp_path):
    folder_name = "test-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / "name-of-destination-folder"
    keys = get_public_key_paths()

    create_archive(folder_path, destination_path, encryption_keys=keys, compression=5, remove_unencrypted=True)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, encrypted=True)


def test_create_archive_split_encrypted(tmp_path, generate_splitting_directory):
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"
    keys = get_public_key_paths()

    create_archive(source_path, destination_path, encryption_keys=keys, compression=6, remove_unencrypted=True, splitting=max_size)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, split=True, encrypted=True)
