from archiver.integrity import check_integrity, verify_relative_symbolic_links, get_archives_with_hashes_from_path
from tests.helpers import get_directory_with_name

DEEP = True

def test_integrity_check_on_archive(caplog):
    archive_dir = get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    assert_successful_shallow_check(archive_file, caplog)


def test_integrity_check_on_encrypted_archive(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")

    assert_successful_shallow_check(archive_file, caplog)


def test_integrity_check_on_directory(caplog):
    archive_dir = get_directory_with_name("normal-archive")

    assert_successful_shallow_check(archive_dir, caplog)


def test_integrity_check_on_encrypted_directory(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")

    assert_successful_shallow_check(archive_dir, caplog)


def test_integrity_check_on_split_archive(caplog):
    archive_dir = get_directory_with_name("split-archive")

    assert_successful_shallow_check(archive_dir, caplog)


def test_integrity_check_on_split_encrypted_archive(caplog):
    archive_dir = get_directory_with_name("split-encrypted-archive")

    assert_successful_shallow_check(archive_dir, caplog)


def test_integrity_check_on_split_encrypted_file(caplog, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz.gpg")

    assert_successful_shallow_check(archive_file, caplog)


def test_integrity_check_corrupted(caplog):
    archive_dir = get_directory_with_name("normal-archive-corrupted")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    expected_string = f"Basic integrity check unsuccessful. Archive has been changed since creation."

    assert_integrity_check_with_output(archive_file, expected_string, False, caplog)


def test_integrity_check_corrupted_encrypted(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive-corrupted")

    expected_string = f"Basic integrity check unsuccessful. Archive has been changed since creation."

    assert_integrity_check_with_output(archive_dir, expected_string, False, caplog)


def test_integrity_check_corrupted_on_split_archive(caplog):
    archive_dir = get_directory_with_name("split-archive-corrupted")

    expected_string = f"Basic integrity check unsuccessful. Archive has been changed since creation."

    assert_integrity_check_with_output(archive_dir, expected_string, False, caplog)


def test_integrity_check_deep(caplog):
    archive_dir = get_directory_with_name("normal-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz")

    assert_successful_deep_check(archive_file, caplog)


def test_integrity_check_deep_encrypted(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")

    assert_successful_deep_check(archive_dir, caplog)


def test_integrity_check_deep_encrypted_file(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    archive_file = archive_dir.joinpath("test-folder.tar.lz.gpg")

    assert_successful_deep_check(archive_file, caplog)


def test_integrity_check_deep_on_split_archive(caplog):
    archive_dir = get_directory_with_name("split-archive")
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz")

    assert_successful_deep_check(archive_file, caplog)

def test_integrity_check_deep_on_split_archive_name_conflict(caplog):
    archive_dir = get_directory_with_name("split-archive-name-conflict")
    archive_file = archive_dir.joinpath("project.part1.part1.tar.lz")

    assert_successful_deep_check(archive_file, caplog, archive_name="project.part1")

def test_integrity_check_deep_on_split_encrypted_archive(caplog, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    archive_file = archive_dir.joinpath("large-folder.part1.tar.lz.gpg")

    assert_successful_deep_check(archive_file, caplog)


def test_integrity_check_deep_corrupted(caplog):
    archive_dir = get_directory_with_name("normal-archive-corrupted-deep")

    expected_messages = [
        "Missing file test-folder/folder-in-archive/big file3.txt in archive!",
        'File test-folder/folder-in-archive/file2.txt in archive does not appear in list of md5sums!',
        "Hash of test-folder/file1.txt has changed: Expected 49dbcfb5e7ae8ca55cab5b0e4674d9fd but got 49dbcfb5e7ae8ca55cab6b0e4674d9fd",
        "Deep integrity check unsuccessful. Archive has been changed since creation."]

    check_integrity_and_validate_output_contains(archive_dir, caplog, expected_messages, False, DEEP)


def test_integrity_check_deep_corrupted_encrypted(caplog, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive-corrupted-deep")

    expected_messages = ["Hash of test-folder/folder-in-archive/file2.txt has changed: Expected 5762a5694bf3cb3dp59bf864ed71a4a8 but got 5762a5694bf3cb3df59bf864ed71a4a8",
                         "Deep integrity check unsuccessful. Archive has been changed since creation."]

    check_integrity_and_validate_output_contains(archive_dir, caplog, expected_messages, False, DEEP)

def test_incomplete_check_on_split_archive(caplog):
    archive_dir = get_directory_with_name("split-archive-incomplete")

    expected_messages = ["Integrity check unsuccessful. Files missing in archive.",
                         "Basic integrity check unsuccessful. But checksums of files in archive match."]

    check_integrity_and_validate_output_contains(archive_dir, caplog, expected_messages, False, DEEP)


def test_incomplete_check_on_split_archive_encrypted(caplog):
    archive_dir = get_directory_with_name("split-encrypted-archive-incomplete")

    expected_messages = ["Integrity check unsuccessful. Files missing in archive.",
                         "Basic integrity check unsuccessful. But checksums of files in archive match."]

    check_integrity_and_validate_output_contains(archive_dir, caplog, expected_messages, False, DEEP)

def test_integrity_check_symlink(caplog):
    archive_dir = get_directory_with_name("symlink-archive")
    archive_file = archive_dir.joinpath("symlink-folder.tar.lz")

    assert_successful_shallow_check(archive_file, caplog)

def test_integrity_check_symlink_split_archive(caplog):
    archive_dir = get_directory_with_name("symlink-archive2")

    assert_successful_shallow_check(archive_dir, caplog)

def test_integrity_check_deep_symlink(caplog):
    archive_dir = get_directory_with_name("symlink-archive")
    archive_file = archive_dir.joinpath("symlink-folder.tar.lz")

    assert_successful_deep_check(archive_file, caplog)

    assert "Symlink symlink-folder/invalid_link_abs found pointing to /not/existing . The archive contains the link itself, but possibly not the file it points to." in caplog.messages
    assert "Symlink symlink-folder/invalid_link pointing to not_existing is broken in archive" in caplog.messages

def test_integrity_check_deep_symlink_split_archive(caplog):
    archive_dir = get_directory_with_name("symlink-archive2")

    assert_successful_deep_check(archive_dir, caplog)

def test_verify_relative_symbolic_links():
    archive_dir = get_directory_with_name("symlink-archive")

    archives_with_hashes = get_archives_with_hashes_from_path(archive_dir)
    missing = verify_relative_symbolic_links(archives_with_hashes)

    link_key = 'symlink-folder/invalid_link'
    assert link_key in missing and missing[link_key] == 'not_existing'
    assert len(missing) == 1


# MARK: Helpers

def assert_successful_deep_check(archive_path, caplog, archive_name=None):
    expected_output = "Deep integrity check successful."
    assert_integrity_check_with_output(archive_path, expected_output, True, caplog, DEEP, archive_name)


def assert_successful_shallow_check(archive_path, caplog):
    expected_output = "Basic integrity check successful."
    assert_integrity_check_with_output(archive_path, expected_output, True, caplog)


def assert_integrity_check_with_output(archive_path, expected_output, expected_return, caplog, deep=False, archive_name=None):
    assert check_integrity(archive_path, deep, threads=2, archive_name=archive_name) == expected_return

    assert caplog.messages[-1] == expected_output


def check_integrity_and_validate_output_contains(archive_path, caplog, expected_messages, expected_return, deep=False):
    assert check_integrity(archive_path, deep, threads=2) == expected_return

    for message in expected_messages:
        assert message in caplog.messages
