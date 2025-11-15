"""Unit tests for RSA encryption functions."""

import os
from pathlib import Path
import pytest
from PIL import Image
import io

from rsa_encrypt import (
    generate_rsa_keypair,
    encrypt_bytes,
    decrypt_bytes,
    encrypt_image,
    decrypt_image,
    encrypt_file,
    decrypt_file,
)


def test_generate_keypair():
    """Test RSA keypair generation."""
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)
    assert isinstance(private_pem, bytes)
    assert isinstance(public_pem, bytes)
    assert b"BEGIN RSA PRIVATE KEY" in private_pem or b"BEGIN PRIVATE KEY" in private_pem
    assert b"BEGIN PUBLIC KEY" in public_pem


def test_encrypt_decrypt_bytes():
    """Test encrypting and decrypting raw bytes."""
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)

    original = b"Hello, RSA encryption!"
    encrypted = encrypt_bytes(original, public_pem)

    assert encrypted != original
    assert isinstance(encrypted, bytes)

    decrypted = decrypt_bytes(encrypted, private_pem)
    assert decrypted == original


def test_encrypt_decrypt_image():
    """Test encrypting and decrypting a PIL Image."""
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)

    # Create a small test image
    img = Image.new("RGB", (100, 100), color="red")

    # Encrypt
    encrypted = encrypt_image(img, public_pem)
    assert isinstance(encrypted, bytes)
    assert encrypted != b""

    # Decrypt
    decrypted_img = decrypt_image(encrypted, private_pem)
    assert isinstance(decrypted_img, Image.Image)
    assert decrypted_img.size == (100, 100)


def test_encrypt_file_decrypt_file(tmp_path):
    """Test file encryption and decryption."""
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)

    # Create a test file
    input_file = tmp_path / "test_input.txt"
    output_file = tmp_path / "test_encrypted.rsa"
    decrypted_file = tmp_path / "test_decrypted.txt"

    test_data = b"Secret message for file encryption"
    input_file.write_bytes(test_data)

    # Encrypt
    encrypt_file(str(input_file), str(output_file), public_pem)
    assert output_file.exists()

    # Decrypt
    decrypt_file(str(output_file), str(decrypted_file), private_pem)
    assert decrypted_file.exists()

    result = decrypted_file.read_bytes()
    assert result == test_data


def test_larger_key_size():
    """Test with RSA-4096 key."""
    private_pem, public_pem = generate_rsa_keypair(key_size=4096)

    original = b"Testing with larger RSA-4096 key"
    encrypted = encrypt_bytes(original, public_pem)
    decrypted = decrypt_bytes(encrypted, private_pem)

    assert decrypted == original
