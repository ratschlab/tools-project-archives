import os
from pathlib import Path
from typing import Dict
import pytest

from archiver.preparation_checks import CmdBasedCheck
from tests.helpers import create_file_with_size

default_config_file_path = Path(
    __file__).parent.parent.parent / 'default_preparation_checks.ini'


@pytest.fixture(scope="module")
def default_checks():
    all_checks = CmdBasedCheck.checks_from_configfile(default_config_file_path)

    return {c.name: c for c in all_checks}


def test_readme_check(default_checks: Dict[str, CmdBasedCheck], tmpdir):
    check = default_checks['check_readme_present']

    tmp_file = Path(tmpdir, 'README.md')

    assert not check.run(tmpdir)

    tmp_file.touch()

    assert check.run(tmpdir)


def test_no_broken_links(default_checks: Dict[str, CmdBasedCheck], tmpdir):
    check = default_checks['check_no_broken_links']

    myfile = Path(tmpdir, 'myfile')
    myfile.touch()

    mylink = Path(tmpdir, 'mylink')
    mylink.symlink_to(myfile)

    assert check.run(tmpdir)

    myfile.unlink()
    assert not check.run(tmpdir)


def test_symlinks_within_dir_only(default_checks: Dict[str, CmdBasedCheck], tmpdir):
    check = default_checks['check_symlinks_within_dir_only']

    mydir = Path(tmpdir).parent.parent

    myfile = Path(tmpdir, 'myfile')
    myfile.touch()

    mylink = Path(tmpdir, 'mylink')
    mylink.symlink_to(myfile.relative_to(mylink.parent))

    mylink2 = Path(tmpdir, 'mylink2')
    mylink2.symlink_to(os.path.join('..', tmpdir.basename, myfile.name))

    assert check.run(tmpdir)

    my_dirlink_outside = Path(tmpdir, 'mydirlink')
    my_dirlink_outside.symlink_to(os.path.relpath(mydir, my_dirlink_outside))

    assert not check.run(tmpdir)


def test_no_absolute_symlinks(default_checks: Dict[str, CmdBasedCheck], tmpdir):
    check = default_checks['check_no_absolute_symlinks']

    myfile = Path(tmpdir, 'myfile')
    myfile.touch()

    mylink = Path(tmpdir, 'mylink')
    mylink.symlink_to(myfile.relative_to(mylink.parent))

    assert check.run(tmpdir)

    mylink_abs = Path(tmpdir, 'mylink_abs')
    mylink_abs.symlink_to(myfile)

    assert not check.run(tmpdir)


def test_no_duplicates(default_checks: Dict[str, CmdBasedCheck], tmpdir):
    check = default_checks['check_no_large_duplicates']

    myfile = Path(tmpdir, 'myfile')
    create_file_with_size(myfile, 2024**2)

    assert check.run(tmpdir)

    myfile_link = Path(tmpdir, 'myfile_link')
    os.link(myfile, myfile_link)

    assert not check.run(tmpdir)