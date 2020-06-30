import os
import shutil
import re
import pytest

from archiver.extract import decrypt_existing_archive
from archiver.helpers import get_absolute_path_string
from .archiving_helpers import add_prefix_to_list_elements, compare_listing_files, valid_md5_hash_in_file, compare_text_file_ignoring_order, compare_hash_files
from tests import helpers

ENCRYPTION_PUBLIC_KEY_A = "public.gpg"
ENCRYPTION_PUBLIC_KEY_B = "public_second.pub"


def test_decrypt_regular_archive(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    copied_archive_path = tmp_path / FOLDER_NAME

    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path)

    # Test if all files exist
    dir_listing = os.listdir(copied_archive_path)
    expected_listing = [".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz.gpg", ".tar.lz", ".tar.lz.gpg.md5", ".tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [copied_archive_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.lz.gpg.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), copied_archive_path.joinpath(FOLDER_NAME + ".md5"))


def test_decrypt_regular_archive_remove_unencrypted(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    copied_archive_path = tmp_path / FOLDER_NAME

    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path, remove_unencrypted=True)

    # Test if all files exist
    dir_listing = os.listdir(copied_archive_path)
    expected_listing = [".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz", ".tar.lz.gpg.md5", ".tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [copied_archive_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.lz.gpg.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), copied_archive_path.joinpath(FOLDER_NAME + ".md5"))


def test_decrypt_regular_archive_to_destination(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / FOLDER_NAME

    decrypt_existing_archive(archive_path, destination_path)

    # Test if all files exist
    dir_listing = os.listdir(destination_path)
    expected_listing = [".tar.lz"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)


def test_decrypt_regular_archive_error_existing(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / FOLDER_NAME
    destination_path.mkdir()

    with pytest.raises(SystemExit) as error:
        decrypt_existing_archive(archive_path, destination_path)

    assert error.type == SystemExit
    assert str(error.value) == f"Path {get_absolute_path_string(destination_path)} must not exist. Use --force to override"


def test_decrypt_regular_archive_force_override_existing(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / FOLDER_NAME
    destination_path.mkdir()

    decrypt_existing_archive(archive_path, destination_path, force=True)

    # Test if all files exist
    dir_listing = os.listdir(destination_path)
    expected_listing = [".tar.lz"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)


def test_decrypt_regular_file(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    copied_archive_path = tmp_path / FOLDER_NAME
    archive_file = copied_archive_path / f"{FOLDER_NAME}.tar.lz.gpg"

    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(archive_file)

    # Test if all files exist
    dir_listing = os.listdir(copied_archive_path)
    expected_listing = [".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz.gpg", ".tar.lz", ".tar.lz.gpg.md5", ".tar.md5"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Test listing of tar
    compare_listing_files([archive_path.joinpath(FOLDER_NAME + ".tar.lst")], [copied_archive_path.joinpath(FOLDER_NAME + ".tar.lst")])

    # Test hash validity
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.lz.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".tar.lz.gpg.md5"))

    # Test md5 of archive content
    compare_text_file_ignoring_order(archive_path.joinpath(FOLDER_NAME + ".md5"), copied_archive_path.joinpath(FOLDER_NAME + ".md5"))


def test_decrypt_regular_file_to_destination(tmp_path, setup_gpg):
    FOLDER_NAME = "test-folder"

    archive_path = helpers.get_directory_with_name("encrypted-archive")
    archive_file = archive_path / f"{FOLDER_NAME}.tar.lz.gpg"
    destination_path = tmp_path / FOLDER_NAME

    decrypt_existing_archive(archive_file, destination_path)

    # Test if all files exist
    dir_listing = os.listdir(destination_path)
    expected_listing = [".tar.lz"]
    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)


def test_decrypt_archive_split(tmp_path, setup_gpg):
    FOLDER_NAME = "large-folder"

    archive_path = helpers.get_directory_with_name("split-encrypted-archive")
    copied_archive_path = tmp_path / FOLDER_NAME

    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path)

    dir_listing = os.listdir(copied_archive_path)

    # Test if all files exist
    expected_listing = [".part1.tar.lst", ".part1.tar.lz.md5", ".part1.md5", ".part1.tar.lz", ".part1.tar.lz.gpg", ".part1.tar.lz.gpg.md5", ".part1.tar.md5",
                        ".part2.tar.lst", ".part2.tar.lz.md5", ".part2.md5", ".part2.tar.lz", ".part2.tar.lz.gpg", ".part2.tar.lz.gpg.md5", ".part2.tar.md5",
                        ".part3.tar.lst", ".part3.tar.lz.md5", ".part3.md5", ".part3.tar.lz", ".part3.tar.lz.gpg", ".part3.tar.lz.gpg.md5", ".part3.tar.md5"]

    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Tar listings
    expected_listing_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), archive_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    actual_listing_file_paths = [copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    compare_listing_files(expected_listing_file_paths, actual_listing_file_paths)

    # Test hashes
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.lz.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.lz.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.lz.gpg.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.lz.gpg.md5"))

    # Test md5 of archive content
    expected_hash_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.md5"), archive_path.joinpath(FOLDER_NAME + ".part2.md5")]
    actual_hash_file_paths = [copied_archive_path.joinpath(FOLDER_NAME + ".part1.md5"), copied_archive_path.joinpath(FOLDER_NAME + ".part2.md5")]
    compare_hash_files(expected_hash_file_paths, actual_hash_file_paths)


def test_decrypt_archive_split_remove_unencrypted(tmp_path, setup_gpg):
    FOLDER_NAME = "large-folder"

    archive_path = helpers.get_directory_with_name("split-encrypted-archive")
    copied_archive_path = tmp_path / FOLDER_NAME

    shutil.copytree(archive_path, copied_archive_path)

    decrypt_existing_archive(copied_archive_path, remove_unencrypted=True)

    dir_listing = os.listdir(copied_archive_path)

    # Test if all files exist
    expected_listing = [".part1.tar.lst", ".part1.tar.lz.md5", ".part1.md5", ".part1.tar.lz", ".part1.tar.lz.gpg.md5", ".part1.tar.md5",
                        ".part2.tar.lst", ".part2.tar.lz.md5", ".part2.md5", ".part2.tar.lz", ".part2.tar.lz.gpg.md5", ".part2.tar.md5",
                        ".part3.tar.lst", ".part3.tar.lz.md5", ".part3.md5", ".part3.tar.lz", ".part3.tar.lz.gpg.md5", ".part3.tar.md5"]

    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)

    # Tar listings
    expected_listing_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), archive_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    actual_listing_file_paths = [copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.lst"), copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.lst")]
    compare_listing_files(expected_listing_file_paths, actual_listing_file_paths)

    # Test hashes
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part1.tar.lz.md5"))
    assert valid_md5_hash_in_file(copied_archive_path.joinpath(FOLDER_NAME + ".part2.tar.lz.md5"))

    # Test md5 of archive content
    expected_hash_file_paths = [archive_path.joinpath(FOLDER_NAME + ".part1.md5"), archive_path.joinpath(FOLDER_NAME + ".part2.md5")]
    actual_hash_file_paths = [copied_archive_path.joinpath(FOLDER_NAME + ".part1.md5"), copied_archive_path.joinpath(FOLDER_NAME + ".part2.md5")]
    compare_hash_files(expected_hash_file_paths, actual_hash_file_paths)


def test_decrypt_archive_split_to_destination(tmp_path):
    FOLDER_NAME = "large-folder"

    archive_path = helpers.get_directory_with_name("split-encrypted-archive")
    destination_path = tmp_path / FOLDER_NAME

    decrypt_existing_archive(archive_path, destination_path)

    dir_listing = os.listdir(destination_path)

    # Test if all files exist
    expected_listing = [".part1.tar.lz", ".part2.tar.lz", ".part3.tar.lz"]

    expected_named_listing = add_prefix_to_list_elements(expected_listing, FOLDER_NAME)

    # Directory listings
    helpers.compare_array_content_ignoring_order(dir_listing, expected_named_listing)
