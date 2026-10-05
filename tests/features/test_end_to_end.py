import pytest

from tests.helpers import get_directory_with_name, get_test_ressources_path, \
    get_current_directory, run_archiver_tool

CODE_BASE_PATH=get_current_directory().parent

@pytest.mark.parametrize("archive_path,expected_return_code",
    [
        (get_directory_with_name('normal-archive'), 0),
        (get_test_ressources_path()/'doesn-exist', 1),
        (get_directory_with_name('normal-archive-corrupted'), 3),
    ])
def test_integrity_end_to_end(archive_path, expected_return_code):
    proc_ret = run_archiver_tool(['check', str(archive_path)])

    assert proc_ret.returncode == expected_return_code


@pytest.mark.parametrize("archive_path,expected_last_message",
    [
        (get_directory_with_name('normal-archive'), 'Basic integrity check successful.'),
        (get_directory_with_name('normal-archive-corrupted'), 'Basic integrity check unsuccessful.'),
    ])
def test_last_log_message_not_lost(archive_path, expected_last_message):
    proc_ret = run_archiver_tool(['check', str(archive_path)], capture_output=True, text=True)

    assert expected_last_message in proc_ret.stdout.splitlines()[-1]
