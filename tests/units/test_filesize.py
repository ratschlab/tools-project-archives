import pytest
from pathlib import Path

from archiver.helpers import get_bytes_in_string_with_unit, get_size_of_path

K_BASE = 1024
M_BASE = 2**20
G_BASE = 2**30
T_BASE = 2**40


def test_bytes_in_size_string():
    assert get_bytes_in_string_with_unit("77b") == 77
    assert get_bytes_in_string_with_unit("1kb") == K_BASE
    assert get_bytes_in_string_with_unit("724k") == K_BASE * 724
    assert get_bytes_in_string_with_unit("2mb") == M_BASE * 2
    assert get_bytes_in_string_with_unit("45M") == M_BASE * 45
    assert get_bytes_in_string_with_unit("2tb") == T_BASE * 2
    assert get_bytes_in_string_with_unit("7.0t") == T_BASE * 7
    assert get_bytes_in_string_with_unit("3.0mb") == M_BASE * 3
    assert get_bytes_in_string_with_unit("0145tb") == T_BASE * 145
    assert get_bytes_in_string_with_unit("0263t") == T_BASE * 263

    assert get_bytes_in_string_with_unit("1  KB") == K_BASE
    assert get_bytes_in_string_with_unit("2  mB") == M_BASE * 2
    assert get_bytes_in_string_with_unit("97  M") == M_BASE * 97
    assert get_bytes_in_string_with_unit("3.0 MB") == M_BASE * 3
    assert get_bytes_in_string_with_unit("0145      tb") == T_BASE * 145

    # Bad inputs
    with pytest.raises(ValueError):
        get_bytes_in_string_with_unit("1 -  KB")
        get_bytes_in_string_with_unit("77")
        get_bytes_in_string_with_unit("77bb")
        get_bytes_in_string_with_unit("7.4 eb")
        get_bytes_in_string_with_unit(22)
        get_bytes_in_string_with_unit(-52.357)
        get_bytes_in_string_with_unit()


@pytest.mark.skip(reason="Not yet working due to artificial file sizes")
def test_size_of_path(tmp_path):
    test_path = tmp_path.joinpath("test-folder")
    test_path.mkdir()
    empty_path = tmp_path.joinpath("empty-path")
    empty_path.mkdir()

    small_test_file = test_path.joinpath("small-testfile.txt")
    small_file_size = K_BASE * 7
    create_file_with_size(small_test_file, small_file_size)

    large_test_file = test_path.joinpath("large-testfile.psd")
    large_file_size = M_BASE * 122
    create_file_with_size(large_test_file, large_file_size)

    assert get_size_of_path(test_path) == small_file_size + large_file_size


def create_file_with_size(path, byte_size):
    with open(path, "wb") as file:
        # sparse file that doesn't actually take up that amount of space on disk
        file.seek(int(round(byte_size)))
        file.write(b"\0")
