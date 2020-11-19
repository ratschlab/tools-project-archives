from pathlib import Path
import os

from archiver.integrity import check_integrity
from tests.helpers import get_directory_with_name

DEEP = True


def test_integrity_check_on_archive(capsys):
    archive_dir = get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    assert_successful_shallow_check(archive_file, capsys)


def test_integrity_check_on_encrypted_archive(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")

    assert_successful_shallow_check(archive_file, capsys)


def test_integrity_check_on_directory(capsys):
    archive_dir = get_directory_with_name("normal-archive")

    assert_successful_shallow_check(archive_dir, capsys)


def test_integrity_check_on_encrypted_directory(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")

    assert_successful_shallow_check(archive_dir, capsys)


def test_integrity_check_on_split_archive(capsys):
    archive_dir = get_directory_with_name("split-archive")

    assert_successful_shallow_check(archive_dir, capsys)


def test_integrity_check_on_split_encrypted_archive(capsys):
    archive_dir = get_directory_with_name("split-encrypted-archive")

    assert_successful_shallow_check(archive_dir, capsys)


def test_integrity_check_on_split_encrypted_file(capsys, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz.gpg")

    assert_successful_shallow_check(archive_file, capsys)


def test_integrity_check_corrupted(capsys):
    archive_dir = get_directory_with_name("normal-archive-corrupted")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    expected_string = f"Signature of file {archive_file.name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert_integrity_check_with_output(archive_file, expected_string, capsys)


def test_integrity_check_corrupted_encrypted(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive-corrupted")

    corrupted_file_name = "test-folder.tar.lz.gpg"
    expected_string = f"Signature of file {corrupted_file_name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert_integrity_check_with_output(archive_dir, expected_string, capsys)


def test_integrity_check_corrupted_on_split_archive(capsys):
    archive_dir = get_directory_with_name("split-archive-corrupted")

    corrupted_file_name = "large-folder.part1.tar.lz"
    expected_string = f"Signature of file {corrupted_file_name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert_integrity_check_with_output(archive_dir, expected_string, capsys)


def test_integrity_check_deep(capsys):
    archive_dir = get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    assert_successful_deep_check(archive_file, capsys)


def test_integrity_check_deep_encrypted(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")

    assert_successful_deep_check(archive_dir, capsys)


def test_integrity_check_deep_encrypted_file(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")

    assert_successful_deep_check(archive_file, capsys)


def test_integrity_check_deep_on_split_archive(capsys):
    archive_dir = get_directory_with_name("split-archive")
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz")

    assert_successful_deep_check(archive_file, capsys)


def test_integrity_check_deep_on_split_encrypted_archive(capsys, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz.gpg")

    assert_successful_deep_check(archive_file, capsys)


def test_integrity_check_deep_corrupted(caplog):
    archive_dir = get_directory_with_name("normal-archive-corrupted-deep")

    expected_messages = [
        "Missing file test-folder/folder-in-archive/file3.txt in archive!",
        'File test-folder/folder-in-archive/file2.txt in archive does not appear in list of md5sums!',
        "Hash of test-folder/file1.txt has changed: Expected 49dbcfb5e7ae8ca55cab5b0e4674d9fd but got 49dbcfb5e7ae8ca55cab6b0e4674d9fd",
        "Deep integrity check unsuccessful. Archive has been changed since creation."]

    check_integrity_and_validate_output_contains(archive_dir, caplog, expected_messages, DEEP)


def test_integrity_check_deep_corrupted_encrypted(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive-corrupted-deep")

    expected_messages = ["Hash of test-folder/folder-in-archive/file2.txt has changed: Expected 5762a5694bf3cb3dp59bf864ed71a4a8 but got 5762a5694bf3cb3df59bf864ed71a4a8",
                         "Deep integrity check unsuccessful. Archive has been changed since creation."]

    check_integrity_and_validate_output_contains(archive_dir, caplog, expected_messages, DEEP)


def test_integrity_check_symlink(capsys):
    archive_dir = get_directory_with_name("symlink-archive")
    archive_file = archive_dir.joinpath("symlink-folder.tar.lz")

    assert_successful_shallow_check(archive_file, capsys)


def test_integrity_check_deep_symlink(capsys):
    archive_dir = get_directory_with_name("symlink-archive")
    archive_file = archive_dir.joinpath("symlink-folder.tar.lz")

    assert_successful_deep_check(archive_file, capsys)


# MARK: Helpers

def assert_successful_deep_check(archive_path, capsys):
    expected_output = "Deep integrity check successful\n"
    assert_integrity_check_with_output(archive_path, expected_output, capsys, DEEP)


def assert_successful_shallow_check(archive_path, capsys):
    expected_output = "Integrity check successful\n"
    assert_integrity_check_with_output(archive_path, expected_output, capsys)


def assert_integrity_check_with_output(archive_path, expected_output, capsys, deep=False):
    check_integrity(archive_path, deep)

    assert capsys.readouterr().out == expected_output


def check_integrity_and_validate_output_contains(archive_path, caplog, expected_messages, deep=False):
    check_integrity(archive_path, deep)

    for message in expected_messages:
        assert message in caplog.messages
