import logging
import re
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import List

from . import helpers
from .constants import LISTING_SUFFIX, COMPRESSED_ARCHIVE_SUFFIX, \
    ENCRYPTED_ARCHIVE_SUFFIX
from .encryption import decrypt_list_of_archives


def create_listing(source_path, subdir_path=None, deep=False, work_dir=None):
    if deep:
        listing_from_archive(source_path, subdir_path, work_dir)
    else:
        listing_from_listing_file(source_path, subdir_path)


def listing_from_listing_file(source_path, subdir_path):
    listing_files = get_listing_files_for_path(source_path)

    # TODO: Smarter dir-based search, not just filtering for string in path
    # only match actiual path instead of "contains" search
    for listing_file_path in listing_files:
        logging.info(f"Listing content of: {listing_file_path.name}")
        print(f"Listing content of: {listing_file_path.name}")

        with open(listing_file_path, "r", newline="\n") as file:
            for line in file:
                if not subdir_path or subdir_path in line:
                    print(line.rstrip())

        # Print empty new line for visibility, \n makes gap too large
        print("")


def listing_from_archive(source_path, subdir_path, work_dir):
    is_encrypted = helpers.path_target_is_encrypted(source_path)
    archives = helpers.get_archives_from_path(source_path, is_encrypted)

    if len(archives) > 1 and subdir_path:
        archives = relevant_splits_for_partial_path(source_path, subdir_path)

        if is_encrypted:
            archives = [f.parent / f.name.replace(COMPRESSED_ARCHIVE_SUFFIX,
                                                  ENCRYPTED_ARCHIVE_SUFFIX) for
                        f in archives]

    if is_encrypted:
        logging.info("Deep listing of encrypted archive.")
        decrypt_and_list(archives, subdir_path, work_dir)
    else:
        logging.info("Deep listing of compressed archive.")
        list_archives(archives, subdir_path)


def decrypt_and_list(archives, subdir_path, work_dir):
    # TODO: Check if enough disk space or warn
    with tempfile.TemporaryDirectory(dir=work_dir) as temp_path_string:
        temp_path = Path(temp_path_string)

        decrypt_list_of_archives(archives, temp_path)
        archives_encrypted = [temp_path / path.with_suffix("").name for path in archives]

        list_archives(archives_encrypted, subdir_path)


def list_archives(archives, subdir_path):
    for archive in archives:
        # Both log and print, since listing information is relevant to the user
        logging.info(f"Listing content of: {archive.name}")
        print(f"Listing content of: {archive.name}")
        if subdir_path:
            result = helpers.run_shell_cmd(["tar", "-tvf", archive, subdir_path], pipe_stdout=True)
        else:
            result = helpers.run_shell_cmd(["tar", "-tvf", archive], pipe_stdout=True)

        decoded_output = result.stdout.decode("utf-8")

        print(decoded_output)


# MARK: Helpers

def get_listing_files_for_path(path):
    if path.is_dir():
        return helpers.get_files_with_type_in_directory_or_terminate(path, LISTING_SUFFIX)

     # If specific file is used, maybe not all results of search path will be shown (since they could be in different file)
    helpers.file_is_valid_archive_or_terminate(path)
    listing_path = path.parent / (helpers.filename_without_archive_extensions(path) + ".tar.lst")
    helpers.terminate_if_path_nonexistent(path)

    return [listing_path]


ListingEntry=namedtuple('ListingEntry', ['permissions', 'owner',
                                         'group', 'size', 'mod_date', 'mod_time', 'path', 'link_target'])


def parse_tar_listing(path):
    LINK_RE_SEP = re.compile(r"\s?->\s?")

    def _process_path(fields, path_index, orig_line):
        # losing exact whitespace information in split(), get it back here
        re_prefix = r'\s+'.join(fields[0:path_index])
        re_remaining = re.compile(rf'{re_prefix}\s(.*)')
        remaining = re_remaining.match(orig_line).groups()[0]

        # last field may contain 'path' or 'path -> link target'
        link_parts = []
        if '->' in remaining:
            link_parts = LINK_RE_SEP.split(remaining)

        if len(link_parts) > 1:
            return link_parts[0], link_parts[1]
        else:
            return remaining, None

    def _process_gnutar(fields, orig_line):
        path, link_target = _process_path(fields, 5, orig_line)
        owner, group = fields[1].split('/')

        return ListingEntry(fields[0], owner, group, fields[2], fields[3],
                            fields[4], path, link_target)

    def _process_bsdtar(line, orig_line):
        path, link_target = _process_path(line, 8, orig_line)

        return ListingEntry(line[0], line[2], line[3], line[4],
                            ' '.join(line[5:7]), line[7], path, link_target)

    entries = []
    with open(path, 'r', newline='\n') as f:
        for l in f.readlines():
            fields = l.split()

            # assume field 3 is a date formatted like 2020-12-17 to determine listing format
            is_gnu_tar = '-' in fields[3]
            entry = _process_gnutar(fields, l) if is_gnu_tar else _process_bsdtar(
                fields, l)
            entries.append(entry)

    return entries


def relevant_splits_for_partial_path(archive_path: Path,
                                     partial_extraction_path: Path) -> List[
    Path]:
    # determine which part files are relevant for a path to be extracted
    # files of a directory may be spread across several splits
    listing_files = get_listing_files_for_path(archive_path)

    archive_file_set = set()
    for f in listing_files:
        for e in parse_tar_listing(f):
            if e.path.startswith(str(partial_extraction_path)):
                part_path = f.parent / f.name.replace(LISTING_SUFFIX,
                                                      COMPRESSED_ARCHIVE_SUFFIX)
                archive_file_set.add(part_path)

    return sorted(list(archive_file_set))
