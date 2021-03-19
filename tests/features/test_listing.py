import pytest

from archiver.listing import create_listing, parse_tar_listing
from tests.helpers import get_directory_with_name, get_listing_with_name, \
    compare_list_content_ignoring_order

DEEP = True


def test_list_archive_content_on_directory(capsys):
    archive_dir = get_directory_with_name("normal-archive")
    expected_listing = get_listing_with_name("listing-full.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys)


def test_list_archive_content_on_encrypted_directory(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    expected_listing = get_listing_with_name("listing-full.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys)


def test_list_archive_content_on_split_directory(capsys):
    archive_dir = get_directory_with_name("split-archive")
    expected_listing = get_listing_with_name("listing-full-split.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys)


def test_list_archive_content_on_split_encrypted_directory(capsys, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    expected_listing = get_listing_with_name("listing-full-split.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys)


def test_list_archive_content_on_archive(capsys):
    archive_file = get_directory_with_name("normal-archive") / "test-folder.tar.lz"
    expected_listing = get_listing_with_name("listing-full.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys)


def test_list_archive_content_on_encrypted_archive(capsys, setup_gpg):
    archive_file = get_directory_with_name("encrypted-archive") / "test-folder.tar.lz.gpg"
    expected_listing = get_listing_with_name("listing-full.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys)


def test_list_archive_content_on_split_archive(capsys):
    archive_file = get_directory_with_name("split-archive") / "large-folder.part3.tar.lz"
    expected_listing = get_listing_with_name("listing-split-part3.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys)


def test_list_archive_content_on_split_encrypted_archive(capsys, setup_gpg):
    archive_file = get_directory_with_name("split-encrypted-archive") / "large-folder.part3.tar.lz.gpg"
    expected_listing = get_listing_with_name("listing-split-part3.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys)


def test_list_archive_content_subpath(capsys):
    archive_dir = get_directory_with_name("normal-archive")
    expected_listing = get_listing_with_name("listing-partial.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, "test-folder/folder-in-archive")


def test_list_archive_content_subpath_encrypted(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    expected_listing = get_listing_with_name("listing-partial.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, "test-folder/folder-in-archive")


def test_list_archive_content_subpath_split(capsys):
    archive_dir = get_directory_with_name("split-archive")
    expected_listing = get_listing_with_name("listing-split-partial.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, "large-folder/subfolder")


def test_list_archive_content_subpath_split_encrypted(capsys, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    expected_listing = get_listing_with_name("listing-split-partial.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, "large-folder/subfolder")


def test_list_archive_content_deep_on_directory(capsys):
    archive_dir = get_directory_with_name("normal-archive")
    expected_listing = get_listing_with_name("listing-full-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, None, DEEP)


def test_list_archive_content_deep_on_encrypted_directory(capsys, setup_gpg):
    archive_dir = get_directory_with_name("encrypted-archive")
    expected_listing = get_listing_with_name("listing-full-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, None, DEEP)


def test_list_archive_content_deep_on_split_directory(capsys):
    archive_dir = get_directory_with_name("split-archive")
    expected_listing = get_listing_with_name("listing-split-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, None, DEEP)


def test_list_archive_content_deep_on_split_encrypted_directory(capsys, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    expected_listing = get_listing_with_name("listing-split-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, None, DEEP)


def test_list_archive_content_deep_on_archive(capsys):
    archive_file = get_directory_with_name("normal-archive") / "test-folder.tar.lz"
    expected_listing = get_listing_with_name("listing-full-deep.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys, None, DEEP)


def test_list_archive_content_deep_on_encrypted_archive(capsys, setup_gpg):
    archive_file = get_directory_with_name("encrypted-archive") / "test-folder.tar.lz.gpg"
    expected_listing = get_listing_with_name("listing-full-deep.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys, None, DEEP)


def test_list_archive_content_deep_subpath(capsys):
    archive_file = get_directory_with_name("normal-archive") / "test-folder.tar.lz"
    expected_listing = get_listing_with_name("listing-partial-deep.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys, "test-folder/folder-in-archive", DEEP)

@pytest.mark.skip(reason="TODO: feature not correctly implemented")
def test_list_archive_content_deep_encrypted_subpath(capsys, setup_gpg):
    archive_file = get_directory_with_name("encrypted-archive") / "test-folder.tar.lz.gpg"
    expected_listing = get_listing_with_name("listing-partial-deep.lst")

    create_file_listing_and_assert_output_equals(archive_file, expected_listing, capsys, "test-folder/subfolder", DEEP)

@pytest.mark.skip(reason="TODO: feature not correctly implemented")
def test_list_archive_content_deep_subpath_split(capsys):
    archive_dir = get_directory_with_name("split-archive")
    expected_listing = get_listing_with_name("listing-split-partial-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, "large-folder/subfolder", DEEP)

@pytest.mark.skip(reason="TODO: feature not correctly implemented")
def test_list_archive_content_deep_subpath_encrypted_split(capsys, setup_gpg):
    archive_dir = get_directory_with_name("split-encrypted-archive")
    expected_listing = get_listing_with_name("listing-split-partial-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, "large-folder/subfolder", DEEP)


def test_list_archive_content_symlink(capsys):
    archive_dir = get_directory_with_name("symlink-archive")
    expected_listing = get_listing_with_name("listing-symlink.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys)


def test_list_archive_content_symlink_deep(capsys):
    archive_dir = get_directory_with_name("symlink-archive")
    expected_listing = get_listing_with_name("listing-symlink-deep.lst")

    create_file_listing_and_assert_output_equals(archive_dir, expected_listing, capsys, None, DEEP)


@pytest.mark.parametrize('listing_name', ['tar-listing-symlink.lst', 'tar-listing-symlink-gnutar.lst'])
def test_parse_tar_listing(listing_name):
    listing_path = get_listing_with_name(listing_name)

    listing = parse_tar_listing(listing_path)

    assert len(listing) == 7
    assert all(e.owner == 'marc' for e in listing)
    assert all(e.group == 'staff' for e in listing)
    assert all(int(e.size) >= 0 for e in listing)
    assert listing[-1].link_target == '../file1.txt'


# MARK: Test helpers

def create_file_listing_and_assert_output_equals(listing_path, expected_output_file, capsys, subpath=None, deep=False):
    create_listing(listing_path, subpath, deep)
    captured_std_out = capsys.readouterr().out

    compare_listing_path_to_output(expected_output_file, captured_std_out)


def compare_listing_path_to_output(listing_path, output):
    with open(listing_path, "r") as file:
        compare_listing_text(output, file.read())


def compare_listing_text(listing_a, listing_b):
    listing_a_path_array = get_array_of_last_multiline_text_parts(listing_a)
    listing_b_path_array = get_array_of_last_multiline_text_parts(listing_b)

    # Assertion helper
    compare_list_content_ignoring_order(listing_a_path_array, listing_b_path_array)


def get_array_of_last_multiline_text_parts(multiline_text):
    parts_array = []

    for line in multiline_text.splitlines():
        # ignore empty lines
        try:
            path = line.split()[-1]
            parts_array.append(path)
        except:
            pass

    return parts_array
