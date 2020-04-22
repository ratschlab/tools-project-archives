import subprocess
import os

# TODO: Validate input path
# TODO: Add option for output path


def extract(args):
    input_path = args.input

    path = os.path.join(input_path, "archive.tar.lz")
    decompress_and_extract(path)

    print("Archive extracted")


def decompress_and_extract(archive_path):
    ps = subprocess.run(["plzip", "-dc", archive_path], stdout=subprocess.PIPE)
    subprocess.Popen(["tar", "-x"], stdin=ps.stdout)
    ps.stdout.close()
    ps.wait()
