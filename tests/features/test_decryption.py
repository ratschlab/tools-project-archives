import os
import shutil
import re
import pytest

from archiver.extract import decrypt_existing_archive
from archiver.helpers import get_absolute_path_string
from .archiving_helpers import assert_successful_archive_creation, assert_successful_action_to_destination, add_prefix_to_list_elements, compare_listing_files, valid_md5_hash_in_file, compare_text_file_ignoring_order, compare_hash_files
from tests import helpers

ENCRYPTION_PUBLIC_KEY_A = "public.gpg"
ENCRYPTION_PUBLIC_KEY_B = "public_second.pub"


def test_decrypt_regular_archive(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted="all", unencrypted="all")


def test_decrypt_regular_archive_remove_unencrypted(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path, remove_unencrypted=True)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted="hash", unencrypted="all")


def test_decrypt_regular_archive_to_destination(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / folder_name

    decrypt_existing_archive(archive_path, destination_path)
    assert_successful_action_to_destination(destination_path, archive_path, folder_name, encrypted=False)


def test_decrypt_regular_archive_error_existing(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / folder_name
    destination_path.mkdir()

    with pytest.raises(SystemExit) as error:
        decrypt_existing_archive(archive_path, destination_path)

        assert error.type == SystemExit


def test_decrypt_regular_archive_force_override_existing(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / folder_name
    destination_path.mkdir()

    decrypt_existing_archive(archive_path, destination_path, force=True)
    assert_successful_action_to_destination(destination_path, archive_path, folder_name, encrypted=False)


def test_decrypt_regular_file(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    copied_archive_path = tmp_path / folder_name
    archive_file = copied_archive_path / f"{folder_name}.tar.lz.gpg"
    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(archive_file)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted="all", unencrypted="all")


def test_decrypt_regular_file_to_destination(tmp_path, setup_gpg):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    archive_file = archive_path / f"{folder_name}.tar.lz.gpg"
    destination_path = tmp_path / folder_name

    decrypt_existing_archive(archive_file, destination_path)
    assert_successful_action_to_destination(destination_path, archive_path, folder_name, encrypted=False)


def test_decrypt_archive_split(tmp_path, setup_gpg):
    folder_name = "large-folder"
    archive_path = helpers.get_directory_with_name("split-encrypted-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted="all", unencrypted="all", split=3)


def test_decrypt_archive_split_remove_unencrypted(tmp_path, setup_gpg):
    folder_name = "large-folder"
    archive_path = helpers.get_directory_with_name("split-encrypted-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path, remove_unencrypted=True)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted="hash", unencrypted="all", split=3)


def test_decrypt_archive_split_to_destination(tmp_path):
    folder_name = "large-folder"
    archive_path = helpers.get_directory_with_name("split-encrypted-archive")
    destination_path = tmp_path / folder_name

    decrypt_existing_archive(archive_path, destination_path)
    assert_successful_action_to_destination(destination_path, archive_path, folder_name, encrypted=False, split=3)
