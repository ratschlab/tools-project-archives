#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import logging

from .archive import create_archive, encrypt_existing_archive
from .extract import extract_archive, decrypt_existing_archive
from .listing import create_listing
from .integrity import check_integrity
from . import helpers

# Configure logger
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


def main():
    parsed_arguments = parse_arguments(sys.argv[1:])

    if parsed_arguments.func:
        parsed_arguments.func(parsed_arguments)
    else:
        sys.exit("Unknown function call")


def parse_arguments(args):
    # Main parser
    parser = argparse.ArgumentParser(prog="archiver", description='Handles the archiving of large project data')
    parser.add_argument("-w", "--work-dir", type=str, help="Working directory")
    subparsers = parser.add_subparsers(help="Available actions", required=True, dest="command")

    # Archiving parser
    parser_archive = subparsers.add_parser("archive", help="Create archive")
    parser_archive.add_argument("source", type=str, help="Source input file or directory")
    parser_archive.add_argument("archive_dir", type=str, nargs="?", help="Path to directory which will be created")
    parser_archive.add_argument("-n", "--threads", type=int, help="Set the number of worker threads, overriding the system's default")
    parser_archive.add_argument("-c", "--compression", type=int, help="Compression level between 0 (fastest) to 9 (slowest), default is 6")
    parser_archive.add_argument("-k", "--key", type=str, action="append",
                                help="Path to public key which will be used for encryption. Archive will be encrypted when this option is used. Can be used more than once.")
    parser_archive.add_argument("-p", "--part", type=str, help="Split archive into parts by specifying the size of each part. Example: 5G for 5 gigibytes (2^30 bytes).")
    parser_archive.add_argument("-r", "--remove", action="store_true", default=False, help="Remove unencrypted archive after encrypted archive has been created and stored.")
    parser_archive.add_argument("-f", "--force", action="store_true", default=False, help="Overwrite output directory if it already exists and create parents of folder if they don't exist.")
    parser_archive.set_defaults(func=handle_archive)

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

    return parser.parse_args()


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

    if args.part:
        try:
            bytes_splitting = helpers.get_bytes_in_string_with_unit(args.part)
        except Exception as error:
            helpers.terminate_with_exception(error)

    create_archive(source_path, destination_path, threads, args.key, compression, bytes_splitting, args.remove, args.force, work_dir)


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

    check_integrity(source_path, args.deep, threads, args.work_dir)


if __name__ == "__main__":
    main()
