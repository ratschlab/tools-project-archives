import subprocess
from pathlib import Path

from .helpers import terminate_if_path_not_file_of_type


def create_listing(source_path, subdir_path):
    terminate_if_path_not_file_of_type(source_path, ".tar.lz")

    if subdir_path:
        subprocess.run(["tar", "-tvf", source_path, subdir_path])
        return

    subprocess.run(["tar", "-tvf", source_path])
