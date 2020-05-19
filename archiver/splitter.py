import os
from pathlib import Path

from . import helpers

SORT_ORDER_DESCENDING = True


def split_directory(directory_path, max_package_size):
    # all file sizes are in bytes
    archives = []
    current_archive = []
    archive_size = 0

    for root, dirs, files in os.walk(directory_path):
        for index, dir in enumerate(dirs):
            dir_path = Path(root).joinpath(dir)
            dir_size = helpers.get_size_of_path(dir_path)

            if archive_size + dir_size < max_package_size:
                current_archive.append(dir_path)
                archive_size += dir_size

                del dirs[index]
            elif dir_size < max_package_size:
                archives.append(current_archive)

                current_archive = [dir_path]
                archive_size = dir_size

                del dirs[index]

        for file in files:
            file_path = Path(root).joinpath(file)
            file_size = file_path.stat().st_size

            if archive_size + file_size < max_package_size:
                current_archive.append(file_path)
                archive_size += file_size
            elif file_size < max_package_size:
                archives.append(current_archive)

                current_archive = [file_path]
                archive_size = file_size
            else:
                raise ValueError("Some files are larger than the maximum package size")

    archives.append(current_archive)

    return archives
