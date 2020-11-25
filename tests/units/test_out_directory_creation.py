import pytest
import os

from archiver.helpers import handle_destination_directory_creation, get_absolute_path_string
from tests import helpers

FORCE = True


def test_create_target_when_nonexistent(tmp_path):
    """Parents exist but target does not"""
    target_path = tmp_path / "target-dir"
    handle_destination_directory_creation(target_path)

    target_path_2 = tmp_path / "target-dir-2"
    handle_destination_directory_creation(target_path_2, FORCE)

    dir_listing = os.listdir(tmp_path)
    expected_listing = ["target-dir", "target-dir-2"]
    helpers.compare_list_content_ignoring_order(dir_listing, expected_listing)


def test_fail_on_existing_target(tmp_path):
    """Target exists"""
    target_path = tmp_path / "target-dir"
    target_path.mkdir()

    with pytest.raises(SystemExit) as error:
        handle_destination_directory_creation(target_path)

        assert error.type == SystemExit


def test_force_override_existing_target(tmp_path):
    """Target exists, should be overriden"""
    target_path = tmp_path / "target-dir"
    target_path.mkdir()
    target_path.joinpath("some-subdir").mkdir()
    target_path.joinpath("other-subdir").mkdir()

    handle_destination_directory_creation(target_path, FORCE)

    dir_listing = os.listdir(tmp_path)
    assert dir_listing == ["target-dir"]

    subdir_listing = os.listdir(target_path)
    assert subdir_listing == []


def test_fail_on_nonexistent_target_and_parents(tmp_path):
    """Target and target parents do not exist"""
    target_path = tmp_path / "parent-dir/target-dir"

    with pytest.raises(SystemExit) as error:
        handle_destination_directory_creation(target_path)

        assert error.type == SystemExit


def test_force_create_parents_and_target_when_nonexistent(tmp_path):
    """Target and target parents do not exist"""
    target_path = tmp_path / "parent-dir/target-dir"

    handle_destination_directory_creation(target_path, FORCE)

    dir_listing = os.listdir(target_path.parent)
    assert dir_listing == ["target-dir"]
