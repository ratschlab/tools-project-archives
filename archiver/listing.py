import subprocess
from pathlib import Path

import helpers


def list(args):
    # Path to archive file *.tar.lz
    source_path = Path(args.source)
    subdir_path = args.subdir

    helpers.terminate_if_path_not_file_of_type(source_path, ".tar.lz")

    create_listing(source_path, subdir_path)


def create_listing(source_path, subdir_path):
    if subdir_path:
        subprocess.run(["tar", "-tvf", source_path, subdir_path])
        return

    subprocess.run(["tar", "-tvf", source_path])
