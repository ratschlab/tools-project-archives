from pathlib import Path
import os

from archiver.integrity import check_integrity

# shallow
# on splitted archive

# deep
# on splitted archive


def test_integrity_check_on_archive(capsys):
    archive_dir = get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    check_integrity(archive_file)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out == "Starting integrity check...\nIntegrity check successful\n"


def test_integrity_check_on_directory(capsys):
    archive_dir = get_archive_path()

    check_integrity(archive_dir)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out == "Starting integrity check...\nIntegrity check successful\n"


def test_integrity_check_corrupted(capsys):
    archive_dir = get_corrupted_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    check_integrity(archive_file)

    captured_std_out = capsys.readouterr().out

    expected_string = f"Starting integrity check...\nSignature of file {archive_file.name} has changed.\nIntegrity check unsuccessful. Archive has been changed since creation.\n"

    assert captured_std_out == expected_string


def test_integrity_check_deep(capsys):
    archive_dir = get_archive_path()
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    check_integrity(archive_file, True)

    captured_std_out = capsys.readouterr().out

    assert captured_std_out.startswith("Starting integrity check...") and captured_std_out.endswith("Deep integrity check successful\n")


def test_integrity_check_deep_corrupted(capsys):
    CORRUPTED_DEEP = True
    archive_dir = get_corrupted_archive_path(CORRUPTED_DEEP)

    check_integrity(archive_dir, True)

    captured_std_out = capsys.readouterr().out

    assert "Starting integrity check..." in captured_std_out
    assert "Signature of test-folder/file1.txt has changed." in captured_std_out
    assert "Deep integrity check unsuccessful. Archive has been changed since creation." in captured_std_out


def get_archive_path():
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources/test-archive")


def get_corrupted_archive_path(deep=False):
    """Get path of archive used for tests"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))

    if deep:
        return dir_path.parent.joinpath("test-ressources/test-archive-corrupted-deep")

    return dir_path.parent.joinpath("test-ressources/test-archive-corrupted")


def get_test_ressources_path():
    """Get path of test directory"""
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return dir_path.parent.joinpath("test-ressources")
