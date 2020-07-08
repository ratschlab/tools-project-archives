import os
import shutil
import re
import pytest

from archiver.archive import encrypt_existing_archive
from archiver.helpers import get_absolute_path_string
from .archiving_helpers import assert_successful_archive_creation, assert_successful_encryption_to_destination, get_public_key_paths, add_prefix_to_list_elements, compare_listing_files, valid_md5_hash_in_file, compare_text_file_ignoring_order, compare_hash_files
from tests import helpers

ENCRYPTION_PUBLIC_KEY_A = "public.gpg"
ENCRYPTION_PUBLIC_KEY_B = "public_second.pub"


def test_encrypt_regular_archive(tmp_path):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("normal-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    keys = get_public_key_paths()
    encrypt_existing_archive(copied_archive_path, keys)

    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted=True, remove_unencrypted=False)


def test_encrypt_regular_archive_remove_unencrypted(tmp_path):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("normal-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    keys = get_public_key_paths()
    encrypt_existing_archive(copied_archive_path, keys, remove_unencrypted=True)

    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted=True, remove_unencrypted=True)


def test_encrypt_regular_archive_to_destination(tmp_path):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("normal-archive")
    destination_path = tmp_path / folder_name
    keys = get_public_key_paths()

    encrypt_existing_archive(archive_path, keys, destination_path)
    assert_successful_encryption_to_destination(destination_path, archive_path, folder_name)


def test_encrypt_regular_archive_error_existing(tmp_path):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("normal-archive")
    destination_path = tmp_path / folder_name
    destination_path.mkdir()

    keys = get_public_key_paths()

    with pytest.raises(SystemExit) as error:
        encrypt_existing_archive(archive_path, keys, destination_path)

    assert error.type == SystemExit
    assert str(error.value) == f"Path {get_absolute_path_string(destination_path)} must not exist. Use --force to override"


def test_encrypt_regular_archive_force_override_existing(tmp_path):
    folder_name = "test-folder"

    archive_path = helpers.get_directory_with_name("normal-archive")
    destination_path = tmp_path / folder_name
    destination_path.mkdir()
    keys = get_public_key_paths()

    encrypt_existing_archive(archive_path, keys, destination_path, force=True)
    assert_successful_encryption_to_destination(destination_path, archive_path, folder_name)


def test_encrypt_regular_file(tmp_path):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("normal-archive")
    copied_archive_path = tmp_path / folder_name
    archive_file = copied_archive_path / f"{folder_name}.tar.lz"

    shutil.copytree(archive_path, copied_archive_path)
    keys = get_public_key_paths()

    encrypt_existing_archive(archive_file, keys)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, encrypted=True, remove_unencrypted=False)


def test_encrypt_regular_file_to_destination(tmp_path):
    folder_name = "test-folder"
    archive_path = helpers.get_directory_with_name("normal-archive")
    archive_file = archive_path / f"{folder_name}.tar.lz"
    destination_path = tmp_path / folder_name
    keys = get_public_key_paths()

    encrypt_existing_archive(archive_file, keys, destination_path)
    assert_successful_encryption_to_destination(destination_path, archive_path, folder_name, split=1)

    # Test if all files exist
    dir_listing = os.listdir(destination_path)
    expected_listing = [".tar.lz.gpg", ".tar.lz.gpg.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, folder_name)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    # Test hash validity
    assert valid_md5_hash_in_file(destination_path.joinpath(folder_name + ".tar.lz.gpg.md5"))


def test_encrypt_archive_split(tmp_path):
    folder_name = "large-folder"
    archive_path = helpers.get_directory_with_name("split-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    keys = get_public_key_paths()
    encrypt_existing_archive(copied_archive_path, keys)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, split=3, encrypted=True, remove_unencrypted=False)


def test_encrypt_archive_split_remove_unencrypted(tmp_path):
    folder_name = "large-folder"
    archive_path = helpers.get_directory_with_name("split-archive")
    copied_archive_path = tmp_path / folder_name
    shutil.copytree(archive_path, copied_archive_path)

    keys = get_public_key_paths()
    encrypt_existing_archive(copied_archive_path, keys, remove_unencrypted=True)
    assert_successful_archive_creation(copied_archive_path, archive_path, folder_name, split=3, encrypted=True, remove_unencrypted=True)


def test_encrypt_archive_split_to_destination(tmp_path):
    folder_name = "large-folder"
    archive_path = helpers.get_directory_with_name("split-archive")
    destination_path = tmp_path / folder_name

    keys = get_public_key_paths()
    encrypt_existing_archive(archive_path, keys, destination_path)
    assert_successful_encryption_to_destination(destination_path, archive_path, folder_name, split=3)
