"""ComfyUI Script node example for RSA image encryption.

Usage in ComfyUI Script node:

from rsa_comfy_node_example import comfy_encrypt_image

# Inside the node execute function, receive image and public_key_path
enc_bytes = comfy_encrypt_image(image, public_key_path)
# save or pass enc_bytes onward
"""

from typing import Union
from PIL import Image
from rsa_encrypt import encrypt_image


def comfy_encrypt_image(
    image: Union[bytes, Image.Image],
    public_key_pem: bytes,
) -> bytes:
    """Encrypt an image with RSA public key, suitable for ComfyUI Script nodes.

    Args:
        image: PIL Image or raw bytes
        public_key_pem: public key in PEM format (bytes)

    Returns:
        encrypted bytes
    """
    return encrypt_image(image, public_key_pem)
