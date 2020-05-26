import pytest
from pathlib import Path

from archiver.helpers import get_bytes_in_string_with_unit, get_size_of_path
from .helpers import create_file_with_size

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


def test_size_of_path(tmp_path):
    test_path = tmp_path.joinpath("test-folder")
    test_path.mkdir()

    small_test_file = test_path.joinpath("small-testfile.txt")
    small_file_size = K_BASE * 7
    create_file_with_size(small_test_file, small_file_size)

    large_test_file = test_path.joinpath("large-testfile.psd")
    large_file_size = M_BASE * 5
    create_file_with_size(large_test_file, large_file_size)

    # du -h returns block size, which may differ from actual file size
    BLOCK_SIZE_TOLERANCE = K_BASE * 8
    expected_size = small_file_size + large_file_size
    expected_size_high = expected_size + BLOCK_SIZE_TOLERANCE
    expected_size_low = expected_size - BLOCK_SIZE_TOLERANCE

    assert expected_size_low <= get_size_of_path(test_path) <= expected_size_high

    # du isn't used for file sizes, so block size is irrelevant
    assert get_size_of_path(large_test_file) == large_file_size
    assert get_size_of_path(small_test_file) == small_file_size
