import argparse
import sys

import archiver
import extract

# Main parser
parser = argparse.ArgumentParser(prog="archiver", description='Handles the archiving of large project data')
subparsers = parser.add_subparsers(help="Available actions")

# Archiving parser
parser_archive = subparsers.add_parser("archive", help="Help for archive")
parser_archive.add_argument("input", type=str, help="Source input file or directory")
parser_archive.add_argument("-o", "--output", type=str, help="Target output file")
parser_archive.set_defaults(func=archiver.archive)

# Extraction parser
parser_extract = subparsers.add_parser("extract", help="Help for extraction")
parser_extract.add_argument("input")
parser_extract.add_argument("-o", "--output", type=str, help="Target output file")
parser_extract.set_defaults(func=extract.extract)

args = parser.parse_args()

if args.func:
    args.func(args)
else:
    print("Unknown function call", file=sys.stderr)
