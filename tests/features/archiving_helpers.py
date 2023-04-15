from tests import helpers
import re
import os

ENCRYPTION_PUBLIC_KEY_A = "public.gpg"
ENCRYPTION_PUBLIC_KEY_B = "public_second.pub"

ENCRYPTED_HASH_FILENAMES = [".tar.md5", ".tar.lz.md5", ".tar.lz.gpg.md5"]
UNENCRYPTED_HASH_FILENAMES = [".tar.md5", ".tar.lz.md5"]
SPLIT_ENCRYPTED_HASH_FILENAMES = [".part1.tar.md5", ".part2.tar.md5", ".part1.tar.lz.md5", ".part2.tar.lz.md5", ".part1.tar.lz.gpg.md5", ".part2.tar.lz.gpg.md5"]
SPLIT_UNENCRYPTED_HASH_FILENAMES = [".part1.tar.md5", ".part2.tar.md5", ".part1.tar.lz.md5", ".part2.tar.lz.md5"]

ENCRYPTED_LISTING = [".lst", ".tar.lst", ".tar.lz.md5", ".md5", ".tar.lz.gpg", ".tar.lz.gpg.md5", ".tar.md5"]
UNENCRYPTED_LISTING = ['.lst', '.tar.lst', '.tar.lz.md5', '.md5', '.tar.lz', '.tar.md5']
SPLIT_UNENCRYPTED_LISTINGS = ['.part1.tar.lst', '.part1.tar.lz.md5', '.part1.md5', '.part1.tar.lz', '.part1.tar.md5',
                              '.part2.tar.lst', '.part2.tar.lz.md5', '.part2.md5', '.part2.tar.lz', '.part2.tar.md5']
SPLIT_ENCRYPTED_LISTINGS = [".part1.tar.lst", ".part1.tar.lz.md5", ".part1.md5", ".part1.tar.lz.gpg", ".part1.tar.lz.gpg.md5", ".part1.tar.md5",
                            ".part2.tar.lst", ".part2.tar.lz.md5", ".part2.md5", ".part2.tar.lz.gpg", ".part2.tar.lz.gpg.md5", ".part2.tar.md5"]

HASH_SUFFIX = [".md5"]
SPLIT_HASH_SUFFIX = [".part1.md5", ".part2.md5"]

CONTENT_LISTING = [".tar.lst"]
SPLIT_CONTENT_LISTING = [".part1.tar.lst", ".part2.tar.lst"]


def assert_successful_archive_creation(destination_path, archive_path, folder_name, split=None, encrypted=None, unencrypted=None):
    # Specify which files are expected in the listing
    expected_listing_suffixes = get_required_listing_suffixes(encrypted, unencrypted)
    # Will return unmodified given list if split is None
    expected_listing = add_split_prefix_to_file_suffixes(expected_listing_suffixes, split)

    if split:
        expected_listing += ['.parts.txt']
        
    # Get all hash filesnames from expected listing
    hash_filenames = hash_filenames_from_list(expected_listing)

    dir_listing = os.listdir(destination_path)
    expected_named_listing = add_prefix_to_list_elements(expected_listing, folder_name)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    listing = SPLIT_CONTENT_LISTING if split else CONTENT_LISTING
    expected_listing_file_paths = create_full_filename_path(listing, archive_path, folder_name)
    actual_listing_file_paths = create_full_filename_path(listing, archive_path, folder_name)
    compare_listing_files(expected_listing_file_paths, actual_listing_file_paths)

    hash_file_paths = create_full_filename_path(hash_filenames, destination_path, folder_name)
    assert_hashes_in_file_list_valid(hash_file_paths)

    suffix = SPLIT_HASH_SUFFIX if split else HASH_SUFFIX

    expected_hash_file_paths = create_full_filename_path(suffix, archive_path, folder_name)
    actual_hash_file_paths = create_full_filename_path(suffix, destination_path, folder_name)
    compare_hash_files(expected_hash_file_paths, actual_hash_file_paths)


def assert_successful_action_to_destination(destination_path, archive_path, folder_name, split=None, encrypted=False):
    expected_listing_suffixes = [".tar.lz.gpg", ".tar.lz.gpg.md5"] if encrypted else [".tar.lz"]
    expected_listing = add_split_prefix_to_file_suffixes(expected_listing_suffixes, split)
    hash_filenames = hash_filenames_from_list(expected_listing)

    dir_listing = os.listdir(destination_path)
    expected_named_listing = add_prefix_to_list_elements(expected_listing, folder_name)
    helpers.compare_list_content_ignoring_order(dir_listing, expected_named_listing)

    hash_file_paths = create_full_filename_path(hash_filenames, destination_path, folder_name)
    assert_hashes_in_file_list_valid(hash_file_paths)


def get_required_listing_suffixes(encrypted, unencrypted):
    expected_listing = []

    if encrypted == "all":
        expected_listing = ENCRYPTED_LISTING

    if encrypted == "hash":
        expected_listing = [".tar.lz.gpg.md5"]

    if unencrypted == "all":
        expected_listing = expected_listing + list(set(UNENCRYPTED_LISTING) - set(expected_listing))

    if unencrypted == "hash":
        expected_listing = expected_listing + list(set([".tar.lz.md5"]) - set(".tar.lz.md5"))

    return expected_listing


def hash_filenames_from_list(filenames):
    return [element for element in filenames if element.endswith(".md5")]


def add_split_prefix_to_file_suffixes(suffixes, number):
    if not number or number <= 1:
        return suffixes

    prefixed_filenames = []

    for index in range(1, number + 1):
        prefixed_filenames += [f".part{str(index)}{suffix}" for suffix in suffixes]

    return prefixed_filenames


def assert_hashes_in_file_list_valid(hash_files):
    # Not optimal since assert won't tell you which path is invalid
    valid = True
    for path in hash_files:
        if not valid_md5_hash_in_file(path):
            valid = False

    assert valid


def get_public_key_paths():
    key_directory = helpers.get_directory_with_name("encryption-keys")
    return [key_directory / ENCRYPTION_PUBLIC_KEY_A, key_directory / ENCRYPTION_PUBLIC_KEY_B]


def create_full_filename_path(filenames, directory, prefix):
    prefixed = add_prefix_to_list_elements(filenames, prefix)
    return [directory / filename for filename in prefixed]


def add_prefix_to_list_elements(element_list, prefix):
    return [prefix + element_content for element_content in element_list]


def compare_text_file_ignoring_order(file_a_path, file_b_path):
    with open(file_a_path, "r") as file1, open(file_b_path, "r") as file2:
        helpers.compare_list_content_ignoring_order(file1.readlines(), file2.readlines())


def compare_hash_files(expected_path_list, actual_path_list):
    expected_hash_list = []
    actual_hash_list = []

    for path in expected_path_list:
        with open(path, "r") as hash_file:
            for line in hash_file:
                expected_hash_list.append(line.rstrip())

    for path in actual_path_list:
        with open(path, "r") as hash_file:
            for line in hash_file:
                actual_hash_list.append(line.rstrip())

    helpers.compare_list_content_ignoring_order(expected_hash_list, actual_hash_list)


def compare_listing_files(expected_path_list, actual_path_list):
    expected_union = []
    actual_union = []

    for path in expected_path_list:
        with open(path, "r") as listing_file:
            expected_union += get_array_of_last_multiline_text_parts(listing_file.read())

    for path in actual_path_list:
        with open(path, "r") as listing_file:
            actual_union += get_array_of_last_multiline_text_parts(listing_file.read())

    helpers.compare_list_content_ignoring_order(expected_union, actual_union)


def compare_listing_text(listing_a, listing_b):
    listing_a_path_array = get_array_of_last_multiline_text_parts(listing_a)
    listing_b_path_array = get_array_of_last_multiline_text_parts(listing_b)

    # Assertion helper
    helpers.compare_list_content_ignoring_order(listing_a_path_array, listing_b_path_array)


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


def valid_md5_hash_in_file(hash_file_path):
    """Returns true if file contains valid md5 hash"""
    try:
        with open(hash_file_path, "r") as file:
            file_content = file.read().rstrip()
            if re.search(r"([a-fA-F\d]{32})", file_content):
                return True

            return False
    except:
        return False
