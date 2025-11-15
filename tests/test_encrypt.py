import os
import tempfile

import gnupg
import shutil
import pytest
from comfyui_gpg.gpg_encrypt import encrypt_bytes

# If gpg is not available on the system and no GPG_BINARY env var is set,
# skip these tests because python-gnupg requires the gpg executable.
gpg_binary = os.environ.get("GPG_BINARY") or shutil.which("gpg")
if not gpg_binary:
    pytest.skip("gpg not found in PATH and GPG_BINARY not set; skipping gnupg tests", allow_module_level=True)


def test_encrypt_symmetric_armored(tmp_path):
    # create isolated GNUPG home
    gpg_home = tmp_path / "gpg_home"
    gpg_home.mkdir()
    gpg = gnupg.GPG(gnupghome=str(gpg_home))

    # sample data
    data = b"hello world image bytes"

    # symmetric encrypt
    enc = encrypt_bytes(data, passphrase="testpass", gpg_home=str(gpg_home), armor=True)
    assert b"BEGIN PGP MESSAGE" in enc


def test_generate_key_and_encrypt_public(tmp_path):
    # create isolated GNUPG home and generate a key
    gpg_home = tmp_path / "gpg_home2"
    gpg_home.mkdir()
    gpg = gnupg.GPG(gnupghome=str(gpg_home))

    input_data = gpg.gen_key_input(
        name_email="test@example.com",
        key_type="RSA",
        key_length=1024,
        passphrase="",
    )
    key = gpg.gen_key(input_data)
    assert key is not None

    # encrypt for the generated key (use fingerprint)
    fingerprint = key.fingerprint
    data = b"some image bytes"
    enc = encrypt_bytes(data, recipients=[fingerprint], gpg_home=str(gpg_home), armor=True)
    assert b"BEGIN PGP MESSAGE" in enc
