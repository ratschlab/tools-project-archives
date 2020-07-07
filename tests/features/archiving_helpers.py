from tests import helpers
import re


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
