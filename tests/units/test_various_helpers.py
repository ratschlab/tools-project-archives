import pytest

from archiver.helpers import read_hash_file

special_file_name = (
            'special_file'.encode('utf-8') + bytearray.fromhex('0D')).decode(
    'utf-8')


@pytest.fixture()
def example_hash_file(tmpdir):
    file = tmpdir / 'example.md5'

    example_hash = 'd1dd210d6b1312cb342b56d02bd5e651'

    file_names = ['myfile.txt', special_file_name]

    with open(file, 'w') as  f:
        for fn in file_names:
            f.write(f"{example_hash}  {fn}\n")

    return file


def test_read_hash_file(example_hash_file):
    lst = read_hash_file(example_hash_file)

    file_names = set(lst.keys())

    assert len(lst) == 2
    assert special_file_name in file_names
