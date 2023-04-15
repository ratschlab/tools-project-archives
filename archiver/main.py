#!/usr/bin/env python3

import argparse
import getpass
import logging
import os
import sys
from pathlib import Path

import multiprocessing_logging

from archiver import helpers, __version__
from archiver.archive import create_archive, encrypt_existing_archive, \
    create_filelist_and_hashes, \
    create_tar_archives_and_listings, compress_and_hash
from archiver.constants import DEFAULT_COMPRESSION_LEVEL
from archiver.extract import extract_archive, decrypt_existing_archive
from archiver.integrity import check_integrity
from archiver.listing import create_listing
from archiver.preparation_checks import CmdBasedCheck


def _get_tool_versions_str():
    plzip_version = helpers.run_shell_cmd(['plzip', '--version', '|', 'head', '-n', '1'], pipe_stdout=True).stdout.decode('UTF-8')
    tar_version = helpers.run_shell_cmd(['tar', '--version', '|', 'head', '-n', '1'],
                                          pipe_stdout=True).stdout.decode('UTF-8')
    gpg_version = helpers.run_shell_cmd(['gpg', '--version', '|', 'head', '-n', '1'],
                                          pipe_stdout=True, check_returncode=False).stdout.decode('UTF-8')
    if not gpg_version:
        gpg_version = "GPG not available."

    return f"archiver version {__version__}, with {plzip_version.strip()}, {tar_version.strip()}, {gpg_version.strip()}"


def main(args=tuple(sys.argv[1:])):
    parsed_arguments = parse_arguments(args)

    log_fmt = '%(asctime)s - %(levelname)s: %(message)s'
    log_level = logging.DEBUG if parsed_arguments.verbose else logging.INFO
    log_stream = sys.stdout

    logging.basicConfig(format=log_fmt, force=True, level=log_level, stream=log_stream)

    try:
        import coloredlogs
        coloredlogs.install(fmt=log_fmt, level=log_level, stream=log_stream)
    except ImportError:
        pass

    # handle logging in child processes properly
    # note, that this will work under linux only. If `fork` would be used a starting
    # method for child processes, it would also work on other systems. However, this
    # is not well supported: https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    multiprocessing_logging.install_mp_handler()

    logging.info(_get_tool_versions_str())
    logging.info(f"Executing as {getpass.getuser()} on {os.uname().nodename}")

    try:
        if parsed_arguments.func:
            parsed_arguments.func(parsed_arguments)
        else:
            sys.exit("Unknown function call")
    except Exception as e:
        logging.exception(e)
        raise(e)

def parse_arguments(args):
    # Main parser
    parser = argparse.ArgumentParser(prog="archiver", description='Archive large project data')
    parser.add_argument("-w", "--work-dir", type=str, help="Directory for temporary files")
    parser.add_argument("-v", "--verbose", action="store_const", const=True)
    parser.add_argument("--version", action='version',  version=f'%(prog)s {__version__}')

    subparsers = parser.add_subparsers(help="Available commands", required=True, dest="command")

    compression_help = f"Compression level between 0 (fastest) to 9 (slowest), default is {DEFAULT_COMPRESSION_LEVEL}"
    part_size_help = "Split archive into parts by specifying the maximum size of each " \
                     "part (based on uncompressed filesizes). Example: 5G for 5 gigibytes (2^30 bytes)."
    part_help = "Which part to process. If missing, process all"
    force_help = "Overwrite output directory if it already exists and create parents of folder if they don't exist."
    thread_help = "Set the number of workers"
    encryption_key_help = "Path to public key which will be used for encryption. Archive will be encrypted when this " \
                          "option is used. Can be used more than once."
    remove_unencrypted_help = "Remove unencrypted archive after encrypted archive has been created and stored."

    # Create Archive Parent Parser
    archive_parent_parser = argparse.ArgumentParser(add_help=False)
    archive_parent_parser.add_argument("source", type=str, help="Source directory")
    archive_parent_parser.add_argument("archive_dir", type=str, help="Path for archive directory (will be created)")
    archive_parent_parser.add_argument("-n", "--threads", type=int, help=thread_help)

    # Archiving parser
    parser_archive = subparsers.add_parser("archive", help="Create archive", parents=[archive_parent_parser])
    parser_archive.add_argument("-c", "--compression", type=int, help=compression_help)
    parser_archive.add_argument("-k", "--key", type=str, action="append",
                                help=encryption_key_help)
    parser_archive.add_argument("--part-size", type=str, help=part_size_help)
    parser_archive.add_argument("-r", "--remove", action="store_true", default=False, help=remove_unencrypted_help)
    parser_archive.add_argument("-f", "--force", action="store_true", default=False, help=force_help)
    parser_archive.set_defaults(func=handle_archive)

    parser_create = subparsers.add_parser("create", help="Create archives step-by-step (optimization possibilities for large split archives)")
    subparser_create = parser_create.add_subparsers(help="Available subcommands", required=True, dest="create_command")

    parser_create_filelist = subparser_create.add_parser("filelist", help="create list and hashes of all files to be archived", parents=[archive_parent_parser])
    parser_create_filelist.add_argument("--part-size", type=str, help=part_size_help)
    parser_create_filelist.add_argument("-f", "--force", action="store_true", default=False, help=force_help)
    parser_create_filelist.set_defaults(func=handle_create_filelist)

    parser_create_tar = subparser_create.add_parser("tar", help="create tar archives and listings", parents=[archive_parent_parser])
    parser_create_tar.add_argument("-p", "--part", type=int, help=part_help)
    parser_create_tar.set_defaults(func=handle_create_tar_archive)

    parser_create_compressed = subparser_create.add_parser("compressed-tar", help="compress tars")
    parser_create_compressed.add_argument("archive_dir", type=str, help="Path to directory which will be created")
    parser_create_compressed.add_argument("-n", "--threads", type=int, help=thread_help)
    parser_create_compressed.add_argument("-c", "--compression", type=int, help=compression_help)
    parser_create_compressed.add_argument("-p", "--part", type=str, help=part_help)
    parser_create_compressed.set_defaults(func=handle_create_compressed)

    # Encryption parser
    parser_encrypt = subparsers.add_parser("encrypt", help="Encrypt existing unencrypted archive")
    parser_encrypt.add_argument("source", type=str, help="Existing archive directory or .tar.lz file")
    parser_encrypt.add_argument("destination", type=str, nargs="?", help="Specify destination where encrypted archive should be stored")
    parser_encrypt.add_argument("-n", "--threads", type=int, help=f"{thread_help}. Applicable for split archives")
    parser_encrypt.add_argument("-k", "--key", type=str, action="append", required=True, help=encryption_key_help)
    parser_encrypt.add_argument("-r", "--remove", action="store_true", default=False, help=remove_unencrypted_help)
    parser_encrypt.add_argument("-e", "--reencrypt", action="store_true", default=False, help="Reencrypt already encrypted archive with a new set of keys. Only newly specified keys will have access.")
    parser_encrypt.add_argument("-f", "--force", action="store_true", default=False, help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
    parser_encrypt.set_defaults(func=handle_encryption)

    # Decryption parser
    parser_decrypt = subparsers.add_parser("decrypt", help="Decrypt existing encrypted archive")
    parser_decrypt.add_argument("source", type=str, help="Existing archive directory or .tar.lz file")
    parser_decrypt.add_argument("destination", type=str, nargs="?", help="Specify destination where unencrypted archive should be stored")
    parser_decrypt.add_argument("-n", "--threads", type=int, help=f"{thread_help}. Applicable for split archives")
    parser_decrypt.add_argument("-r", "--remove", action="store_true", default=False, help="Remove encrypted archive after unencrypted archive has been created and stored.")
    parser_decrypt.add_argument("-f", "--force", action="store_true", default=False, help=force_help)
    parser_decrypt.set_defaults(func=handle_decryption)

    # Extraction parser
    parser_extract = subparsers.add_parser("extract", help="Extract files from existing archive")
    parser_extract.add_argument("archive_dir", type=str, help="Select source archive tar.lz file")
    parser_extract.add_argument("destination", type=str, help="Path to directory where archive will be extracted")
    parser_extract.add_argument("-s", "--subpath", type=str, help="Directory or file inside archive to extract")
    parser_extract.add_argument("-n", "--threads", type=int, help=thread_help)
    parser_extract.add_argument("-f", "--force", action="store_true", default=False, help=force_help)
    parser_extract.set_defaults(func=handle_extract)

    # List parser
    parser_list = subparsers.add_parser("list", help="List content of archive")
    parser_list.add_argument("archive_dir", type=str, help="Select source archive directory or .tar.lz file")
    parser_list.add_argument("subpath", type=str, nargs="?", help="Only list selected subpath inside archive")
    parser_list.add_argument("-d", "--deep", action="store_true", help="Query actual archive instead of relying on existing listing file")
    parser_list.set_defaults(func=handle_list)

    # Integrity check
    parser_check = subparsers.add_parser("check", help="Check integrity of archive")
    parser_check.add_argument("archive_dir", type=str, help="Select source archive directory or .tar.lz file")
    parser_check.add_argument("-d", "--deep", action="store_true", help="Verify integrity by unpacking archive and hashing each file")
    parser_check.add_argument("-n", "--threads", type=int, help=thread_help)
    parser_check.set_defaults(func=handle_check)

    # Preparation checks
    parser_preparation_check = subparsers.add_parser("preparation-checks",
                                     help='Verify source directory has a sound structure before archiving')

    parser_preparation_check.add_argument("archive_source_dir", type=Path,
                        help="Archive Source directory")
    parser_preparation_check.add_argument("--check-file", type=Path,
                        help="path to config file with custom checks", default=DEFAULT_FILE_CHECK_PATH)
    parser_preparation_check.set_defaults(func=handle_preparation_check)

    return parser.parse_args(args)


def handle_archive(args):
    # Path to a file or directory which will be archived or encrypted
    source_path = Path(args.source)
    # Path to a directory which will be created (if it does yet exist)
    destination_path = Path(args.archive_dir)
    # Default compression level should be 6
    compression = args.compression if args.compression else DEFAULT_COMPRESSION_LEVEL

    threads = helpers.get_threads_from_args_or_environment(args.threads)

    bytes_splitting = None

    work_dir = args.work_dir

    if args.part_size:
        try:
            bytes_splitting = helpers.get_bytes_in_string_with_unit(args.part_size)
        except Exception as error:
            helpers.terminate_with_exception(error)

    create_archive(source_path, destination_path, threads, args.key, compression, bytes_splitting, args.remove, args.force, work_dir)


def handle_create_filelist(args):
    source_path = Path(args.source)
    destination_path = Path(args.archive_dir)
    threads = helpers.get_threads_from_args_or_environment(args.threads)

    bytes_splitting = None

    if args.part_size:
        try:
            bytes_splitting = helpers.get_bytes_in_string_with_unit(args.part_size)
        except Exception as error:
            helpers.terminate_with_exception(error)

    # Create destination folder if nonexistent or overwrite if --force option used
    helpers.handle_destination_directory_creation(destination_path, args.force)
    create_filelist_and_hashes(source_path, destination_path, bytes_splitting, threads)


def handle_create_tar_archive(args):
    work_dir = args.work_dir
    source_path = Path(args.source)
    destination_path = Path(args.archive_dir)
    threads = helpers.get_threads_from_args_or_environment(args.threads)

    part = args.part
    parts_list = [part] if part else []

    create_tar_archives_and_listings(source_path, destination_path, work_dir, parts_list, threads)


def handle_create_compressed(args):
    destination_path = Path(args.archive_dir)
    threads = helpers.get_threads_from_args_or_environment(args.threads)

    compression = args.compression if args.compression else DEFAULT_COMPRESSION_LEVEL

    part = args.part
    compress_and_hash(destination_path, threads, compression, part)


def handle_encryption(args):
    source_path = Path(args.source)
    destination_path = Path(args.destination) if args.destination else None

    remove_unencrypted = args.remove

    threads = args.threads if args.threads else 1

    if args.reencrypt:
        # Always remove the unencrypted archive when --reencrypt is used since there was no unencrypted archive present
        remove_unencrypted = True
        # Encrypted archive will be removed in any case, since new one will be created
        decrypt_existing_archive(source_path, remove_unencrypted=True, threads=threads)

    encrypt_existing_archive(source_path, args.key, destination_path, remove_unencrypted, args.force, threads=threads)


def handle_decryption(args):
    source_path = Path(args.source)
    destination_path = Path(args.destination) if args.destination else None

    threads = args.threads if args.threads else 1
    decrypt_existing_archive(source_path, destination_path, args.remove, args.force, threads=threads)


def handle_extract(args):
    # Path to archive file *.tar.lz
    source_path = Path(args.archive_dir)
    destination_directory_path = Path(args.destination)

    threads = helpers.get_threads_from_args_or_environment(args.threads)

    extract_archive(source_path, destination_directory_path, args.subpath, threads, args.force)


def handle_list(args):
    # Path to archive file *.tar.lz
    source_path = Path(args.archive_dir)

    create_listing(source_path, args.subpath, args.deep, args.work_dir)


def handle_check(args):
    # Path to archive file *.tar.lz
    source_path = Path(args.archive_dir)
    threads = helpers.get_threads_from_args_or_environment(args.threads)

    if not check_integrity(source_path, args.deep, threads, args.work_dir):
        # return a different error code to the default code of 1 to be able to distinguish
        # general errors from a successful run of the program with an unsuccessful outcome
        # not taking 2, as it usually stands for command line argument errors
        return sys.exit(3)

DEFAULT_FILE_CHECK_PATH = Path(__file__).parent / 'checks' / 'default_preparation_checks.ini'
def handle_preparation_check(parsed_args):
    wdir = Path(parsed_args.archive_source_dir).absolute()
    cfg_file = parsed_args.check_file

    # construct file check objects
    logging.debug(f"Reading config from {cfg_file}")
    file_checks = CmdBasedCheck.checks_from_configfile(Path(cfg_file))

    logging.debug("Verifying all preconditions for the checks are satisfied")
    all_precond = [(c.name, c.run_precondition()) for c in file_checks]

    all_precond_success = all(r for _, r in all_precond)

    if not all_precond_success:
        logging.warning(
            f"Skipping the following checks, since their precondition failed: "
            f"{', '.join([name for name, r in all_precond if not r])}")

    all_ret = [(c.name, c.run(wdir)) for c in file_checks]

    all_success = all(r for _, r in all_ret)

    if not all_precond_success:
        logging.warning("Skipped some tests")

    if all_success:
        logging.info("All performed checks successful :)")

        if not all_precond_success:
            sys.exit(1)
    else:
        logging.warning(f"Some checks failed: "
                        f"{', '.join([name for name, r in all_ret if not r])}")
        sys.exit(1)



if __name__ == "__main__":
    main()
