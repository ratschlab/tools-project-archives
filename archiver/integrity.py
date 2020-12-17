import logging
import tempfile
from pathlib import Path


from . import helpers
from .constants import COMPRESSED_ARCHIVE_SUFFIX, ENCRYPTED_ARCHIVE_SUFFIX, MD5_LINE_REGEX, LISTING_SUFFIX
from .extract import extract_archive
from .listing import parse_tar_listing


def check_integrity(source_path, deep_flag=False, threads=None, work_dir=None):
    archives_with_hashes = get_archives_with_hashes_from_path(source_path)
    is_encrypted = helpers.path_target_is_encrypted(source_path)

    logging.info("Starting integrity check on: " + source_path.as_posix())

    check_result = shallow_integrity_check(archives_with_hashes)

    if deep_flag:
        # with deep flag still continue, no matter what the result of the previous test was
        deep_check_result = deep_integrity_check(archives_with_hashes,
                                                 is_encrypted, threads, work_dir)

        if check_result and deep_check_result:
            logging.info("Deep integrity check successful.")
        elif not check_result and deep_check_result:
            logging.error(
                "Basic integrity check unsuccessful. But checksums of files in archive match.")
        else:
            logging.error(
                "Deep integrity check unsuccessful. Archive has been changed since creation.")
        return check_result and deep_check_result

    if not check_result:
        logging.error(
            "Basic integrity check unsuccessful. Archive has been changed since creation.")
    else:
        logging.info("Basic integrity check successful.")

    return check_result


def shallow_integrity_check(archives_with_hashes):
    # Check each archive file separately
    for archive in archives_with_hashes:
        archive_file_path = archive[0]
        archive_hash_file_path = archive[1]

        logging.info(f"Verifying hash of {archive_file_path}")
        if not compare_hashes_from_files(archive_file_path, archive_hash_file_path):
            logging.warning(f"Hash of file {archive_file_path.name} has changed.")
            return False

    return True


def verify_relative_symbolic_links(archives_with_hashes):
    """
    Checks whether relative links in archives can be resolved.

    It considers listing files only, which may only yield approximative results. Note, that in case
    of split archives, we would need to unpack all splits, since a link may point to a file in some other
    split. However, unpacking all splits may turn out to not feasible, e.g. for space reasons.

    :param archives_with_hashes:
    :return: dictionary of paths to symlinks where target is missing and is relative
    """
    file_set = set() # the set of all files in the archive (parts)
    symlink_dict = {} # all symlinks found across listing
    for archive in archives_with_hashes:
        part_path = archive[0]
        part_listing = part_path.parent / (helpers.filename_without_archive_extensions(part_path) + LISTING_SUFFIX)
        entries = parse_tar_listing(part_listing)

        file_set.update([e.path for e in entries])
        symlink_dict.update(
            {e.path: e.link_target for e in entries if e.link_target})

    missing = {}
    for path, target in symlink_dict.items():
        # for absolute targets we already gave warning during hash_listing_for_files_in_folder
        if not Path(target).is_absolute():
            target_path = (Path(path).parent / Path(target)).resolve()
            relative_target_path = target_path.relative_to(Path().resolve())

            if str(relative_target_path) not in file_set:
                missing[path] = target

    return missing


def deep_integrity_check(archives_with_hashes, is_encrypted, threads, work_dir):
    # Unpack each archive separately
    successful = True
    for archive in archives_with_hashes:
        archive_file_path = archive[0]
        expected_listing_hash_path = archive[2]

        # Create temporary directory to unpack archive
        with tempfile.TemporaryDirectory(dir=work_dir) as temp_path_string:
            temp_path = Path(temp_path_string) / "extraction-folder"
            archive_content_path = extract_archive(archive_file_path, temp_path, threads=threads, extract_at_destination=True)

            terminate_if_extracted_archive_not_existing(archive_content_path)
            hash_result = helpers.hash_listing_for_files_in_folder(archive_content_path, max_workers=threads, integrity_check=True)

            r = compare_archive_listing_hashes(hash_result, expected_listing_hash_path)
            successful = successful and r

    missing_links = verify_relative_symbolic_links(archives_with_hashes)

    for path, target in missing_links.items():
        logging.warning(f"Symbolic link {path} pointing to {target} cannot be found in archive")

    return successful


# MARK: Helpers

def terminate_if_extracted_archive_not_existing(extracted_archive):
    # generate hash listing using existing method and compare with test-folder.md5
    if not extracted_archive.is_dir():
        helpers.terminate_with_message("Extraction of archive for deep integrity check failed")


def compare_archive_listing_hashes(hash_result, expected_hash_listing_path):
    hash_result_dict = {fn: hash for (fn, hash) in hash_result}

    with open(expected_hash_listing_path, "r") as file:
        expected_dict = {}
        for l in file.readlines():
            m = MD5_LINE_REGEX.match(l)

            if not m:
                logging.error(
                    f"Not properly formatted MD5 checksum line found in file {expected_hash_listing_path}: {l}")
                return False

            expected_dict[m.groups()[1].lstrip('./')] = m.groups()[0]

    corruption_found = False

    if hash_result_dict.keys() != expected_dict.keys():
        corruption_found = True
        for k in expected_dict.keys() - hash_result_dict.keys():
            logging.error(f"Missing file {k} in archive!")
        for k in hash_result_dict.keys() - expected_dict.keys():
            logging.error(f"File {k} in archive does not appear in list of md5sums!")

    for k in expected_dict.keys():
        if k in hash_result_dict.keys() and hash_result_dict[k] != expected_dict[k]:
            logging.error(f"Hash of {k} has changed: Expected {expected_dict[k]} but got {hash_result_dict[k]}")
            corruption_found = True
    return not corruption_found


def compare_hashes_from_files(archive_file_path, archive_hash_file_path):
    # Generate hash of .tar.lz
    archive_hash = helpers.get_file_hash_from_path(archive_file_path)

    # Read hash of .tar.lz.md5
    with open(archive_hash_file_path, "r") as file:
        hash_file_content = file.read()

    # hash_file_content may contain path of file
    return hash_file_content.startswith(archive_hash)


def get_archives_with_hashes_from_path(path):
    if path.is_dir():
        return get_archives_with_hashes_from_directory(path)

    return get_hashes_for_archive(path)


def get_hashes_for_archive(archive_path):
    file_is_valid_archive_or_terminate(archive_path)

    archive_file_path = archive_path

    hash_file_path = archive_path.parent / (archive_path.name + ".md5")
    helpers.terminate_if_path_nonexistent(hash_file_path)

    hash_listing_path = archive_path.parent / (helpers.filename_without_archive_extensions(archive_path) + ".md5")
    helpers.terminate_if_path_nonexistent(hash_listing_path)

    return [(archive_file_path, hash_file_path, hash_listing_path)]


def get_archives_with_hashes_from_directory(source_path):
    encrypted_archive_files = helpers.get_files_with_type_in_directory(source_path, ENCRYPTED_ARCHIVE_SUFFIX)

    try:
        if encrypted_archive_files:
            archives = encrypted_archive_files
        else:
            archives = helpers.get_files_with_type_in_directory(source_path, COMPRESSED_ARCHIVE_SUFFIX)
    except LookupError as error:
        helpers.terminate_with_exception(error)

    archives_with_hashes = []

    for archive in archives:
        hash_path = archive.parent / (archive.name + ".md5")
        helpers.terminate_if_path_nonexistent(hash_path)

        hash_listing_path = Path(archive.parent) / (helpers.filename_without_archive_extensions(archive) + ".md5")
        helpers.terminate_if_path_nonexistent(hash_listing_path)

        archive_with_hash_path = (archive, hash_path, hash_listing_path)

        archives_with_hashes.append(archive_with_hash_path)

    return archives_with_hashes


def file_is_valid_archive_or_terminate(file_path):
    if not (helpers.file_has_type(file_path, COMPRESSED_ARCHIVE_SUFFIX) or helpers.file_has_type(file_path, ENCRYPTED_ARCHIVE_SUFFIX)):
        helpers.terminate_with_message(f"File {file_path.name} is not a valid archive of type {COMPRESSED_ARCHIVE_SUFFIX} or {ENCRYPTED_ARCHIVE_SUFFIX}")


def path_target_is_encrypted(path):
    if path.is_dir():
        return archive_is_encrypted(path)

    return helpers.file_has_type(path, ENCRYPTED_ARCHIVE_SUFFIX)


def archive_is_encrypted(archive_path):
    # We'll assume archive is encrypted if there are any encrypted files
    if helpers.get_files_with_type_in_directory(archive_path, ENCRYPTED_ARCHIVE_SUFFIX):
        return True

    return False
