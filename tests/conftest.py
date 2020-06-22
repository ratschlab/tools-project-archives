import os
import subprocess

import pytest

from tests import helpers


@pytest.fixture(scope="session")
def setup_gpg():
    # Using a pytest tmp_path would be preferred, but gnupghome path needs to be short for gpg
    # See: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=847206

    gpg_path = helpers.get_test_ressources_path() / "gpg-home"

    os.environ["GNUPGHOME"] = gpg_path.absolute().as_posix()

    if not gpg_path.exists():
        gpg_path.mkdir()

    archive_path = helpers.get_directory_with_name("encryption-keys")
    secret_key = archive_path / "private.gpg"

    subprocess.run(["gpg", "--import", secret_key])
