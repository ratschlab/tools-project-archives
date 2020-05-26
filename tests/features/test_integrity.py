from pathlib import Path
import os

from archiver.integrity import check_integrity
from . import helpers

# shallow
# on splitted archive

# deep
# on splitted archive


def test_integrity_check_on_archive(capsys):
    archive_dir = helpers.get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    check_integrity(archive_file)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out == "Starting integrity check...\nIntegrity check successful\n"


def test_integrity_check_on_directory(capsys):
    archive_dir = helpers.get_archive_path()

    check_integrity(archive_dir)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out == "Starting integrity check...\nIntegrity check successful\n"


def test_integrity_check_on_splitted_archive(capsys):
    SPLITTED = True
    archive_dir = helpers.get_archive_path(SPLITTED)

    check_integrity(archive_dir)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out == "Starting integrity check...\nIntegrity check successful\n"


def test_integrity_check_corrupted(capsys):
    archive_dir = helpers.get_corrupted_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    check_integrity(archive_file)

    captured_std_out = capsys.readouterr().out

    expected_string = f"Starting integrity check...\nSignature of file {archive_file.name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert captured_std_out == expected_string


def test_integrity_check_corrupted_on_splitted_archive(capsys):
    CORRUPTED_FILE_NAME = "large-folder.part1.tar.lz"

    archive_dir = helpers.get_corrupted_split_archive_path()

    check_integrity(archive_dir)

    captured_std_out = capsys.readouterr().out

    expected_string = f"Starting integrity check...\nSignature of file {CORRUPTED_FILE_NAME} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert captured_std_out == expected_string


def test_integrity_check_deep(capsys):
    archive_dir = helpers.get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    check_integrity(archive_file, True)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out.startswith("Starting integrity check...") and captured_std_out.endswith("Deep integrity check successful\n")


def test_integrity_check_deep_on_splitted_archive(capsys):
    SPLITTED = True
    DEEP = True

    archive_dir = helpers.get_archive_path(SPLITTED)
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz")

    check_integrity(archive_file, DEEP)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out.startswith("Starting integrity check...") and captured_std_out.endswith("Deep integrity check successful\n")


def test_integrity_check_deep_corrupted(capsys):
    CORRUPTED_DEEP = True
    archive_dir = helpers.get_corrupted_archive_path(CORRUPTED_DEEP)

    check_integrity(archive_dir, True)

    captured_std_out = capsys.readouterr().out

    assert "Starting integrity check..." in captured_std_out
    assert "Signature of test-folder/file1.txt has changed." in captured_std_out
    assert "Deep integrity check unsuccessful. Archive has been changed since creation." in captured_std_out
