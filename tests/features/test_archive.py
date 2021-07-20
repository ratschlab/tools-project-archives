import tarfile

import pytest

import archiver
from archiver import integrity
from archiver.archive import create_archive
from tests import helpers
from tests.helpers import run_archiver_tool, generate_splitting_directory
from .archiving_helpers import assert_successful_archive_creation, \
    get_public_key_paths


def test_create_archive(tmp_path):
    folder_name = "test-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("normal-archive")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, unencrypted="all")


@pytest.mark.parametrize("workers", [2, 1])
def test_create_archive_split(tmp_path, generate_splitting_directory, workers):
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(source_path, destination_path, compression=6, splitting=max_size, threads=workers)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, split=2, unencrypted="all")


def test_create_archive_split_granular(tmp_path, generate_splitting_directory):
    """
    end-to-end test for granular splitting workflow
    """
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"

    run_archiver_tool(['create', 'filelist', '--part', f"{max_size}B",
                       source_path, destination_path])

    run_archiver_tool(['create', 'tar', '--threads', str(2),
                       source_path, destination_path])

    run_archiver_tool(['create', 'compressed-tar', '--threads', str(2),
                       destination_path])

    assert_successful_archive_creation(destination_path, archive_path,
                                       folder_name, split=2, unencrypted="all")

    assert run_archiver_tool(['check', '--deep', destination_path]).returncode == 0


def test_create_symlink_archive(tmp_path, caplog):
    folder_name = "symlink-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("symlink-archive")
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, unencrypted="all")

    assert "Broken symlink symlink-folder/invalid_link found pointing to a non-existing file " in caplog.text
    assert "Symlink with outside target symlink-folder/invalid_link_abs found pointing to /not/existing which is outside the archiving directory" in caplog.text


def test_create_symlink_archive_split(tmp_path, caplog):
    folder_name = "symlink-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    destination_path = tmp_path / "name-of-destination-folder"

    create_archive(folder_path, destination_path, compression=5, splitting=20, threads=2)

    assert "Broken symlink symlink-folder/invalid_link found pointing to a non-existing file " in caplog.text
    assert "Symlink with outside target symlink-folder/invalid_link_abs found pointing to /not/existing which is outside the archiving directory" in caplog.text


def test_create_encrypted_archive(tmp_path):
    folder_name = "test-folder"

    folder_path = helpers.get_directory_with_name(folder_name)
    archive_path = helpers.get_directory_with_name("encrypted-archive")
    destination_path = tmp_path / "name-of-destination-folder"
    keys = get_public_key_paths()

    create_archive(folder_path, destination_path, encryption_keys=keys, compression=5, remove_unencrypted=True)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, encrypted="all")


def test_create_archive_split_encrypted(tmp_path, generate_splitting_directory):
    max_size = 1000 * 1000 * 50
    folder_name = "large-test-folder"
    source_path = generate_splitting_directory

    archive_path = helpers.get_directory_with_name("split-archive-ressources")
    destination_path = tmp_path / "name-of-destination-folder"
    keys = get_public_key_paths()

    create_archive(source_path, destination_path, encryption_keys=keys, compression=6, remove_unencrypted=True, splitting=max_size)
    assert_successful_archive_creation(destination_path, archive_path, folder_name, split=2, encrypted="all")


@pytest.mark.parametrize('splitting_param', [None, 1000**5])
def test_split_archive_with_exotic_filenames(tmp_path, splitting_param):
    # file name with trailing \r
    back_slash_r = ('back_slash_r'.encode('UTF-8') + bytearray.fromhex('0D')).decode('utf-8')
    back_slash_r

    file_names = sorted(['file.txt', 'file',
                  'with space', 'more   spaces', 'space at the end ',
                  "tips'n tricks", 'back\rlashes', back_slash_r,
                  "double_slash_\\r", "double_slash_\\\r", r'many_slashes_\\\X',
                  'newline_with_\\n_slash', 'newline_with_\\\n_slash',
                  "öéeé", '你好',
                  'back_slash_r_explicit\r.txt', 'new\n\nline.txt', 'newlineatend\n'])

    # TODO: this fails: 'öé\\reé\\n',

    file_dir = tmp_path/'files'
    file_dir.mkdir()

    for f in file_names:
        helpers.create_file_with_size(file_dir/f, 100)

    dest = tmp_path/'myarchive'
    create_archive(file_dir, dest, encryption_keys=None,
                   compression=6, remove_unencrypted=True, splitting=splitting_param)

    assert integrity.check_integrity(dest, deep_flag=True, threads=1)

    archive_name = 'files' if not splitting_param else 'files.part1'
    # don't use listing to check tar content, but check it directly.
    # listing is tricky to process with special characters
    archiver.helpers.run_shell_cmd(
        ['plzip', '--decompress', str(dest / f'{archive_name}.tar.lz')])
    with tarfile.open(dest / f'{archive_name}.tar') as f:
        file_names_in_tar = {p[len('files/'):] for p in f.getnames()}
        file_names_in_tar = {n for n in file_names_in_tar if n} # removing 'files/' directory entry

    assert file_names_in_tar == set(file_names)



