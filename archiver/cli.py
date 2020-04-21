import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(prog="archiver", description='List the content of a folder')

    parser.add_argument('-compress', action="store_true", help='compressing a file')
    parser.add_argument('-decompress', action="store_true", help='decompressing a file')
    parser.add_argument('Path', metavar='path', type=str, help='path to the file')

    args = parser.parse_args()

    input_path = args.Path

    if not os.path.isdir(input_path):
        print('The path specified does not exist')
        sys.exit()

    print('\n'.join(os.listdir(input_path)))
