"""ComfyUI custom node for RSA-encrypting an input image.

Placement: put this file into ComfyUI's `custom_nodes` folder.
Requires: rsa_encrypt.py and rsa_comfy_node_example.py to be in the same directory or on Python path.

This node accepts an IMAGE input, encrypts it with an RSA public key, and outputs
the encrypted bytes written to a file, returning the file path as a string.
"""


import sys
import traceback
print("[nodes.py] Importing dependencies for ComfyUI RSA nodes...")
from pathlib import Path
from typing import Optional
from PIL import Image
import os
import io

try:
    from .rsa_encrypt import generate_rsa_keypair, encrypt_image
    print("[nodes.py] Successfully imported generate_rsa_keypair, encrypt_image from .rsa_encrypt")
except Exception as e:
    print(f"[nodes.py] ImportError: {e}", file=sys.stderr)
    traceback.print_exc()
    raise


class RSAEncryptNode:
    """Encrypt an input IMAGE with RSA and write the encrypted bytes to disk.

    Outputs a string containing the written file path.
    """

    @classmethod
    def INPUT_TYPES(cls):
        print("[RSAEncryptNode] INPUT_TYPES called")
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
    OUTPUT_NODE = False
    CATEGORY = "Encryption"

    def encrypt(
        self,
        image,
        public_key_pem: str,
        out_path: Optional[str] = None,
    ):
        print(f"[RSAEncryptNode] encrypt called with out_path={out_path}")
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
        try:
            import numpy as np
            
            # Check if it's a PyTorch Tensor
            if hasattr(image, "numpy"):
                print(f"[RSAEncryptNode] Detected PyTorch Tensor with shape {image.shape}, dtype {image.dtype}")
                # Convert Tensor to numpy array
                arr = image.numpy()
                print(f"[RSAEncryptNode] Converted Tensor to numpy array with shape {arr.shape}, dtype {arr.dtype}")
            elif isinstance(image, np.ndarray):
                arr = image
                print(f"[RSAEncryptNode] Detected numpy array with shape {arr.shape}, dtype {arr.dtype}")
            elif hasattr(image, "convert"):
                # It's already a PIL Image
                pil_img = image
                print(f"[RSAEncryptNode] Detected PIL Image")
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")
            
            # If we have a numpy array, convert to PIL Image
            if pil_img is None and arr is not None:
                # Handle float arrays (ComfyUI typically uses float32 in range [0, 1])
                if arr.dtype == np.float32 or arr.dtype == np.float64:
                    print(f"[RSAEncryptNode] Converting float array to uint8 (range 0-255)")
                    # Clamp and scale to 0-255
                    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
                
                # Remove batch dimension if present (shape is (batch, height, width, channels))
                if len(arr.shape) == 4:
                    print(f"[RSAEncryptNode] Removing batch dimension from shape {arr.shape}")
                    arr = arr[0]  # Take first image from batch
                    print(f"[RSAEncryptNode] New shape after removing batch: {arr.shape}")
                
                # Handle different array shapes
                if len(arr.shape) == 3:
                    if arr.shape[2] == 4:  # RGBA
                        pil_img = Image.fromarray(arr, mode='RGBA')
                    elif arr.shape[2] == 3:  # RGB
                        pil_img = Image.fromarray(arr, mode='RGB')
                    else:
                        raise ValueError(f"Unsupported number of channels: {arr.shape[2]}")
                elif len(arr.shape) == 2:  # Grayscale
                    pil_img = Image.fromarray(arr, mode='L')
                else:
                    raise ValueError(f"Unsupported array shape: {arr.shape}")
                
                print(f"[RSAEncryptNode] Converted array to PIL Image: {pil_img.size}, mode {pil_img.mode}")
        except Exception as e:
            print(f"[RSAEncryptNode] Exception in image conversion: {e}", file=sys.stderr)
            traceback.print_exc()
            raise ValueError(f"Unsupported image input: {e}")

        # Convert public key string to bytes
        if isinstance(public_key_pem, str):
            public_key_pem_bytes = public_key_pem.encode("utf-8")
        else:
            public_key_pem_bytes = public_key_pem

        # Encrypt
        try:
            enc_bytes = encrypt_image(pil_img, public_key_pem_bytes)
        except Exception as e:
            print(f"[RSAEncryptNode] Error in encrypt_image: {e}", file=sys.stderr)
            traceback.print_exc()
            raise

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
        try:
            with open(target, "wb") as f:
                f.write(enc_bytes)
            print(f"[RSAEncryptNode] Encrypted image written to {target}")
        except Exception as e:
            print(f"[RSAEncryptNode] Error writing encrypted file: {e}", file=sys.stderr)
            traceback.print_exc()
            raise

        return (str(target),)


class RSAKeyGeneratorNode:
    """Generate an RSA keypair and optionally save to disk."""

    @classmethod
    def INPUT_TYPES(cls):
        print("[RSAKeyGeneratorNode] INPUT_TYPES called")
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
    OUTPUT_NODE = False
    CATEGORY = "Encryption"

    def generate(
        self,
        key_size: str,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
    ):
        print(f"[RSAKeyGeneratorNode] generate called with key_size={key_size}, private_key_path={private_key_path}, public_key_path={public_key_path}")
        """Generate RSA keypair.

        Args:
            key_size: "2048" or "4096"
            private_key_path: optional path to save private key
            public_key_path: optional path to save public key

        Returns:
            (private_key_pem_str, public_key_pem_str)
        """
        try:
            size = int(key_size)
            private_pem, public_pem = generate_rsa_keypair(key_size=size)

            # Save if paths provided
            if private_key_path:
                Path(private_key_path).parent.mkdir(parents=True, exist_ok=True)
                with open(private_key_path, "wb") as f:
                    f.write(private_pem)
                print(f"[RSAKeyGeneratorNode] Private key written to {private_key_path}")

            if public_key_path:
                Path(public_key_path).parent.mkdir(parents=True, exist_ok=True)
                with open(public_key_path, "wb") as f:
                    f.write(public_pem)
                print(f"[RSAKeyGeneratorNode] Public key written to {public_key_path}")

            # Return as strings
            return (private_pem.decode("utf-8"), public_pem.decode("utf-8"))
        except Exception as e:
            print(f"[RSAKeyGeneratorNode] Error in generate: {e}", file=sys.stderr)
            traceback.print_exc()
            raise


# Expose node classes in the same pattern as ComfyUI-NodeSample so the
# ComfyUI loader can discover and register them.
print("[nodes.py] Registering NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS")
NODE_CLASS_MAPPINGS = {
    "RSAEncryptNode": RSAEncryptNode,
    "RSAKeyGeneratorNode": RSAKeyGeneratorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RSAEncryptNode": "RSA Encrypt Image",
    "RSAKeyGeneratorNode": "RSA Key Generator",
}
print("[nodes.py] NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS registered")
