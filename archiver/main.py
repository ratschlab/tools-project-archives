#!/usr/bin/env python3

import argparse
import getpass
import logging
import os
import sys
from pathlib import Path

from . import helpers, __version__
from .archive import create_archive, encrypt_existing_archive, create_filelist_and_hashs, \
    create_tar_archives_and_listings, compress_and_hash
from .extract import extract_archive, decrypt_existing_archive
from .integrity import check_integrity
from .listing import create_listing
from .preparation_checks import CmdBasedCheck

# Configure logger
log_fmt = '%(asctime)s - %(levelname)s: %(message)s'
logging.basicConfig(format=log_fmt, level=logging.INFO)


def main(args=tuple(sys.argv[1:])):
    parsed_arguments = parse_arguments(args)

    logging.info(f"archiver version {__version__}")
    logging.info(f"Executing as {getpass.getuser()} on {os.uname().nodename}")

    if parsed_arguments.func:
        parsed_arguments.func(parsed_arguments)
    else:
        sys.exit("Unknown function call")


def parse_arguments(args):
    # Main parser
    parser = argparse.ArgumentParser(prog="archiver", description='Handles the archiving of large project data')
    parser.add_argument("-w", "--work-dir", type=str, help="Working directory")
    subparsers = parser.add_subparsers(help="Available actions", required=True, dest="command")

    # Create Archive Parent Parser
    archive_parent_parser = argparse.ArgumentParser(add_help=False)
    archive_parent_parser.add_argument("source", type=str, help="Source input file or directory")
    archive_parent_parser.add_argument("archive_dir", type=str, help="Path to directory which will be created")
    archive_parent_parser.add_argument("-n", "--threads", type=int,
                                help="Set the number of worker threads, overriding the system's default")

    # Archiving parser
    parser_archive = subparsers.add_parser("archive", help="Create archive", parents=[archive_parent_parser])
    parser_archive.add_argument("-c", "--compression", type=int, help="Compression level between 0 (fastest) to 9 (slowest), default is 6")
    parser_archive.add_argument("-k", "--key", type=str, action="append",
                                help="Path to public key which will be used for encryption. Archive will be encrypted when this option is used. Can be used more than once.")
    parser_archive.add_argument("--part-size", type=str, help="Split archive into parts by specifying the size of each part. Example: 5G for 5 gigibytes (2^30 bytes).")
    parser_archive.add_argument("-r", "--remove", action="store_true", default=False, help="Remove unencrypted archive after encrypted archive has been created and stored.")
    parser_archive.add_argument("-f", "--force", action="store_true", default=False, help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
    parser_archive.set_defaults(func=handle_archive)

    parser_create = subparsers.add_parser("create", help="Create archive")
    subparser_create = parser_create.add_subparsers(help="Available actions", required=True, dest="command")

    parser_create_filelist = subparser_create.add_parser("filelist", parents=[archive_parent_parser])
    parser_create_filelist.add_argument("--part-size", type=str,
                                help="Split archive into parts by specifying the size of each part. Example: 5G for 5 gigibytes (2^30 bytes).")
    parser_create_filelist.add_argument("-f", "--force", action="store_true",
                                default=False,
                                help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
    parser_create_filelist.set_defaults(func=handle_create_filelist)

    parser_create_tar = subparser_create.add_parser("tar", parents=[archive_parent_parser])
    parser_create_tar.add_argument("-p", "--part", type=int,
                                help="Which part to process")
    parser_create_tar.set_defaults(func=handle_create_tar_archive)

    parser_create_compressed = subparser_create.add_parser("compressed-tar")
    parser_create_compressed.add_argument("archive_dir", type=str, help="Path to directory which will be created")
    parser_create_compressed.add_argument("-n", "--threads", type=int,
                                help="Set the number of worker threads, overriding the system's default")
    parser_create_compressed.add_argument("-c", "--compression", type=int,
                                help="Compression level between 0 (fastest) to 9 (slowest), default is 6")
    parser_create_compressed.add_argument("-p", "--part", type=str,
                                help="Which part to process")
    parser_create_compressed.set_defaults(func=handle_create_compressed)

    # Encryption parser
    parser_encrypt = subparsers.add_parser("encrypt", help="Encrypt existing unencrypted archive")
    parser_encrypt.add_argument("source", type=str, help="Existing archive directory or .tar.lz file")
    parser_encrypt.add_argument("destination", type=str, nargs="?", help="Specify destination where encrypted archive should be stored")
    parser_encrypt.add_argument("-k", "--key", type=str, action="append", required=True, help="Path to public key which will be used for encryption. Can be used more than once.")
    parser_encrypt.add_argument("-r", "--remove", action="store_true", default=False, help="Remove unencrypted archive after encrypted archive has been created and stored.")
    parser_encrypt.add_argument("-e", "--reencrypt", action="store_true", default=False, help="Reencrypt already encrypted archive with a new set of keys. Only newly specified keys will have access.")
    parser_encrypt.add_argument("-f", "--force", action="store_true", default=False, help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
    parser_encrypt.set_defaults(func=handle_encryption)

    # Decryption parser
    parser_decrypt = subparsers.add_parser("decrypt", help="Decrypt existing encrypted archive")
    parser_decrypt.add_argument("source", type=str, help="Existing archive directory or .tar.lz file")
    parser_decrypt.add_argument("destination", type=str, nargs="?", help="Specify destination where unencrypted archive should be stored")
    parser_decrypt.add_argument("-r", "--remove", action="store_true", default=False, help="Remove encrypted archive after unencrypted archive has been created and stored.")
    parser_decrypt.add_argument("-f", "--force", action="store_true", default=False, help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
    parser_decrypt.set_defaults(func=handle_decryption)

    # Extraction parser
    parser_extract = subparsers.add_parser("extract", help="Extract archive")
    parser_extract.add_argument("archive_dir", type=str, help="Select source archive tar.lz file")
    parser_extract.add_argument("destination", type=str, help="Path to directory where archive will be extracted")
    parser_extract.add_argument("-s", "--subpath", type=str, help="Directory or file inside archive to extract")
    parser_extract.add_argument("-n", "--threads", type=int, help="Set the number of worker threads, overriding the system's default")
    parser_extract.add_argument("-f", "--force", action="store_true", default=False, help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
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
    parser_check.add_argument("-n", "--threads", type=int, help="Set the number of worker threads, overriding the system's default")
    parser_check.set_defaults(func=handle_check)

    # Preparation checks
    parser_preparation_check = subparsers.add_parser("preparation-checks",
                                     help='Check archiving directory before archiving for a sound structure')

    parser_preparation_check.add_argument("archive_source_dir", type=Path,
                        help="Archive Source directory")
    parser_preparation_check.add_argument("--check-file", type=Path,
                        help="config file", default=DEFAULT_FILE_CHECK_PATH)
    parser_preparation_check.set_defaults(func=handle_preparation_check)

    return parser.parse_args(args)


def handle_archive(args):
    # Path to a file or directory which will be archived or encrypted
    source_path = Path(args.source)
    # Path to a directory which will be created (if it does yet exist)
    destination_path = Path(args.archive_dir)
    # Default compression level should be 6
    compression = args.compression if args.compression else 6

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

    create_filelist_and_hashs(source_path, destination_path, bytes_splitting, threads, args.force)


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

    # TODO: add default comspression level
    compression = args.compression if args.compression else 6

    part = args.part
    compress_and_hash(destination_path, threads, compression, part)


def handle_encryption(args):
    source_path = Path(args.source)
    destination_path = Path(args.destination) if args.destination else None

    remove_unencrypted = args.remove

    if args.reencrypt:
        # Always remove the unencrypted archive when --reencrypt is used since there was no unencrypted archive present
        remove_unencrypted = True
        # Encrypted archive will be removed in any case, since new one will be created
        decrypt_existing_archive(source_path, remove_unencrypted=True)

    encrypt_existing_archive(source_path, args.key, destination_path, remove_unencrypted, args.force)


def handle_decryption(args):
    source_path = Path(args.source)
    destination_path = Path(args.destination) if args.destination else None

    decrypt_existing_archive(source_path, destination_path, args.remove, args.force)


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

DEFAULT_FILE_CHECK_PATH = Path(__file__).parent.parent / 'default_fs_checks.ini'
def handle_preparation_check(parsed_args):
    #parsed_args = arg_parser.parse_args(args)

    wdir = parsed_args.archive_source_dir
    cfg_file = parsed_args.check_file
    is_verbose = True # TODO fix parsed_args.verbose

    if is_verbose:
        # TODO find better way and refactor
        # https://stackoverflow.com/questions/20240464/python-logging-file-is-not-working-when-using-logging-basicconfig
        import importlib
        importlib.reload(logging)
        logging.basicConfig(format=log_fmt,
                            level=logging.DEBUG)

    os.chdir(wdir)

    # construct file check objects
    logging.debug(f"Reading config from {cfg_file}")
    file_checks = CmdBasedCheck.checks_from_configfile(cfg_file)

    # TODO: add in precondition check!

    all_ret = [ (c.name, c.run()) for c in file_checks]

    all_success = all(r for _, r in all_ret)

    # TODO: more? refactor?
    logging.info('---------------------------------------------------------')
    if all_success:
        logging.info("All checks successful")
    else:
        logging.warning(f"Some checks failed: {', '.join([name for name, r in all_ret if not r])}")
        sys.exit(1)



if __name__ == "__main__":
    main()
