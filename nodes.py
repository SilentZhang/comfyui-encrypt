"""ComfyUI custom node for RSA-encrypting an input image.

Placement: put this file into ComfyUI's `custom_nodes` folder.
Requires: rsa_encrypt.py and rsa_comfy_node_example.py to be in the same directory or on Python path.

This node accepts an IMAGE input, encrypts it with an RSA public key, and outputs
the encrypted bytes written to a file, returning the file path as a string.
"""

from pathlib import Path
from typing import Optional
from PIL import Image
import os
import io

from rsa_encrypt import generate_rsa_keypair, encrypt_image


class RSAEncryptNode:
    """Encrypt an input IMAGE with RSA and write the encrypted bytes to disk.

    Outputs a string containing the written file path.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "public_key_pem": ("STRING",),
            },
            "optional": {
                "out_path": ("STRING",),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    FUNCTION = "encrypt"
    CATEGORY = "Encryption"

    def encrypt(
        self,
        image,
        public_key_pem: str,
        out_path: Optional[str] = None,
    ):
        """Encrypt an image with RSA public key.

        Args:
            image: ComfyUI IMAGE object (numpy array or PIL Image)
            public_key_pem: RSA public key in PEM format (as string)
            out_path: optional output file path; if not provided, writes to cwd with auto-generated name

        Returns:
            (file_path_str,)
        """
        # Convert ComfyUI image input to PIL Image
        pil_img = None
        if hasattr(image, "convert"):
            pil_img = image
        else:
            try:
                import numpy as np
                arr = np.array(image)
                pil_img = Image.fromarray(arr)
            except Exception:
                try:
                    pil_img = Image.open(io.BytesIO(image))
                except Exception as e:
                    raise ValueError(f"Unsupported image input: {e}")

        # Convert public key string to bytes
        if isinstance(public_key_pem, str):
            public_key_pem_bytes = public_key_pem.encode("utf-8")
        else:
            public_key_pem_bytes = public_key_pem

        # Encrypt
        enc_bytes = encrypt_image(pil_img, public_key_pem_bytes)

        # Determine output path
        if out_path:
            target = Path(out_path)
        else:
            base = Path(os.getcwd()) / "encrypted_image"
            i = 0
            while True:
                candidate = base.with_name(f"encrypted_image_{i}.rsa")
                if not candidate.exists():
                    target = candidate
                    break
                i += 1

        # Ensure parent dir exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Write encrypted data
        with open(target, "wb") as f:
            f.write(enc_bytes)

        return (str(target),)


class RSAKeyGeneratorNode:
    """Generate an RSA keypair and optionally save to disk."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "key_size": (["2048", "4096"],),
            },
            "optional": {
                "private_key_path": ("STRING",),
                "public_key_path": ("STRING",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("private_key_pem", "public_key_pem")
    FUNCTION = "generate"
    CATEGORY = "Encryption"

    def generate(
        self,
        key_size: str,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
    ):
        """Generate RSA keypair.

        Args:
            key_size: "2048" or "4096"
            private_key_path: optional path to save private key
            public_key_path: optional path to save public key

        Returns:
            (private_key_pem_str, public_key_pem_str)
        """
        size = int(key_size)
        private_pem, public_pem = generate_rsa_keypair(key_size=size)

        # Save if paths provided
        if private_key_path:
            Path(private_key_path).parent.mkdir(parents=True, exist_ok=True)
            with open(private_key_path, "wb") as f:
                f.write(private_pem)

        if public_key_path:
            Path(public_key_path).parent.mkdir(parents=True, exist_ok=True)
            with open(public_key_path, "wb") as f:
                f.write(public_pem)

        # Return as strings
        return (private_pem.decode("utf-8"), public_pem.decode("utf-8"))


# Expose node classes in the same pattern as ComfyUI-NodeSample so the
# ComfyUI loader can discover and register them.
NODE_CLASS_MAPPINGS = {
    "RSAEncryptNode": RSAEncryptNode,
    "RSAKeyGeneratorNode": RSAKeyGeneratorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RSAEncryptNode": "RSA Encrypt Image",
    "RSAKeyGeneratorNode": "RSA Key Generator",
}
