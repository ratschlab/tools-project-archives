from pathlib import Path
import os

from archiver.integrity import check_integrity
from tests.helpers import get_directory_with_name, setup_gpg

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

    expected_string = f"Starting integrity check...\nSignature of file {archive_file.name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert_integrity_check_with_output(archive_file, expected_string, capsys)


def test_integrity_check_corrupted_encrypted(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive-corrupted")

    corrupted_file_name = "test-folder.tar.lz.gpg"
    expected_string = f"Starting integrity check...\nSignature of file {corrupted_file_name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert_integrity_check_with_output(archive_dir, expected_string, capsys)


def test_integrity_check_corrupted_on_split_archive(capsys):
    archive_dir = get_directory_with_name("split-archive-corrupted")

    corrupted_file_name = "large-folder.part1.tar.lz"
    expected_string = f"Starting integrity check...\nSignature of file {corrupted_file_name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

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


def test_integrity_check_deep_corrupted(capsys):
    archive_dir = get_directory_with_name("normal-archive-corrupted-deep")

    expected_messages = ["Starting integrity check...", "Signature of test-folder/file1.txt has changed.", "Deep integrity check unsuccessful. Archive has been changed since creation."]

    check_integrity_and_validate_output_contains(archive_dir, capsys, expected_messages, DEEP)


def test_integrity_check_deep_corrupted_encrypted(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive-corrupted-deep")

    expected_messages = ["Starting integrity check...", "Signature of test-folder/folder-in-archive/file2.txt has changed.",
                         "Deep integrity check unsuccessful. Archive has been changed since creation."]

    check_integrity_and_validate_output_contains(archive_dir, capsys, expected_messages, DEEP)


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
    check_integrity(archive_path, DEEP)

    output = capsys.readouterr().out

    output.startswith("Starting integrity check...") and output.endswith("Deep integrity check successful\n")


def assert_successful_shallow_check(archive_path, capsys):
    expected_output = "Starting integrity check...\nIntegrity check successful\n"

    assert_integrity_check_with_output(archive_path, expected_output, capsys)


def assert_integrity_check_with_output(archive_path, expected_output, capsys):
    check_integrity(archive_path)

    assert capsys.readouterr().out == expected_output


def check_integrity_and_validate_output_contains(archive_path, capsys, messages, deep=False):
    check_integrity(archive_path, deep)

    output = capsys.readouterr().out

    for message in messages:
        assert message in output
