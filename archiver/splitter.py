import os
from pathlib import Path

from . import helpers

SORT_ORDER_DESCENDING = True


def split_directory(directory_path, max_package_size):
    archives = []
    current_archive = []
    archive_size = 0
    appended = False

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = Path(root).joinpath(file)
            file_size = file_path.stat().st_size

            if archive_size + file_size < max_package_size:
                current_archive.append(file_path)
                archive_size += file_size
            elif file_size < max_package_size:
                archives.append(current_archive)
                appended = True

                archive_size = file_size
                current_archive = [file_path]
            else:
                raise ValueError("Some files are larger than the maximum package size")

    if not appended:
        archives.append(current_archive)

    return archives
