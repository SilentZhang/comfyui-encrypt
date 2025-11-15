"""RSA encryption utilities for images and bytes.

Uses the cryptography library to handle RSA public key encryption with AES for large data.
For data larger than RSA key can handle directly, uses hybrid encryption (RSA + AES).

Supports key generation, encryption of raw bytes, and image encryption (as PNG).
"""

from typing import Optional, Union, Tuple
from pathlib import Path
from io import BytesIO
from PIL import Image

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os


def generate_rsa_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
    """Generate an RSA keypair (private and public keys in PEM format).

    Args:
        key_size: RSA key size in bits. Default 2048. Use 4096 for stronger security.

    Returns:
        (private_key_pem, public_key_pem) as bytes
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem


def encrypt_bytes(
    data: bytes,
    public_key_pem: bytes,
) -> bytes:
    """Encrypt raw bytes with RSA public key using hybrid encryption (AES + RSA).

    For data larger than RSA can directly encrypt, uses AES-256-CBC symmetric encryption
    with the symmetric key encrypted via RSA. This allows encrypting arbitrarily large files.

    Args:
        data: bytes to encrypt
        public_key_pem: public key in PEM format (bytes)

    Returns:
        encrypted bytes (format: 256 bytes of RSA-encrypted AES key + IV + AES-CBC encrypted data)
    """
    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())

    # Generate random AES key and IV
    aes_key = os.urandom(32)  # 256-bit key for AES-256
    iv = os.urandom(16)  # 128-bit IV

    # Encrypt the AES key with RSA
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Encrypt the data with AES-256-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Add PKCS7 padding to data
    padding_length = 16 - (len(data) % 16)
    padded_data = data + bytes([padding_length] * padding_length)

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Combine: RSA-encrypted AES key + IV + AES-encrypted data
    return encrypted_aes_key + iv + encrypted_data


def decrypt_bytes(
    encrypted_data: bytes,
    private_key_pem: bytes,
) -> bytes:
    """Decrypt RSA+AES-encrypted bytes with private key.

    Args:
        encrypted_data: encrypted bytes (RSA-encrypted AES key + IV + AES-CBC encrypted data)
        private_key_pem: private key in PEM format (bytes)

    Returns:
        decrypted bytes
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem, password=None, backend=default_backend()
    )

    # Detect RSA key size from the key
    key_bits = private_key.key_size
    key_size = key_bits // 8  # Convert bits to bytes

    iv_size = 16

    encrypted_aes_key = encrypted_data[:key_size]
    iv = encrypted_data[key_size:key_size + iv_size]
    ciphertext = encrypted_data[key_size + iv_size:]

    # Decrypt the AES key with RSA
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Decrypt the data with AES-256-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove PKCS7 padding
    padding_length = padded_plaintext[-1]
    plaintext = padded_plaintext[:-padding_length]

    return plaintext


def _ensure_bytes(obj: Union[bytes, Image.Image]) -> bytes:
    """Convert PIL Image or raw bytes to bytes (PNG format for images)."""
    if isinstance(obj, bytes):
        return obj
    if isinstance(obj, Image.Image):
        buf = BytesIO()
        obj.save(buf, format="PNG")
        return buf.getvalue()
    raise TypeError("input must be bytes or PIL.Image.Image")


def encrypt_image(
    img: Union[bytes, Image.Image],
    public_key_pem: bytes,
) -> bytes:
    """Encrypt an image with RSA public key.

    The image is saved as PNG before encryption to preserve transparency.

    Args:
        img: PIL Image or raw bytes
        public_key_pem: public key in PEM format (bytes)

    Returns:
        encrypted bytes
    """
    data = _ensure_bytes(img)
    return encrypt_bytes(data, public_key_pem)


def decrypt_image(
    encrypted_data: bytes,
    private_key_pem: bytes,
) -> Image.Image:
    """Decrypt an RSA-encrypted image and return as PIL Image.

    Args:
        encrypted_data: encrypted image bytes
        private_key_pem: private key in PEM format (bytes)

    Returns:
        PIL Image
    """
    data = decrypt_bytes(encrypted_data, private_key_pem)
    return Image.open(BytesIO(data))


def encrypt_file(
    in_path: str,
    out_path: str,
    public_key_pem: bytes,
) -> None:
    """Encrypt a file from disk and write encrypted bytes to out_path.

    Args:
        in_path: path to input file
        out_path: path to output (encrypted) file
        public_key_pem: public key in PEM format (bytes)
    """
    with open(in_path, "rb") as f:
        data = f.read()
    enc = encrypt_bytes(data, public_key_pem)
    with open(out_path, "wb") as f:
        f.write(enc)


def decrypt_file(
    in_path: str,
    out_path: str,
    private_key_pem: bytes,
) -> None:
    """Decrypt a file from disk and write decrypted bytes to out_path.

    Args:
        in_path: path to encrypted file
        out_path: path to output (decrypted) file
        private_key_pem: private key in PEM format (bytes)
    """
    with open(in_path, "rb") as f:
        enc_data = f.read()
    data = decrypt_bytes(enc_data, private_key_pem)
    with open(out_path, "wb") as f:
        f.write(data)
