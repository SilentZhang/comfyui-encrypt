"""Test script to verify ComfyUI Tensor image handling.

This script simulates what ComfyUI passes to the RSAEncryptNode
and tests the image conversion logic.
"""

import numpy as np
from PIL import Image
import torch
import sys
import os

# Add the repo to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rsa_encrypt import generate_rsa_keypair, encrypt_image, decrypt_image

def test_comfyui_tensor_image():
    """Test with a simulated ComfyUI Tensor (float32, [0-1])."""
    print("=" * 60)
    print("Test 1: ComfyUI Tensor (float32, [0-1])")
    print("=" * 60)
    
    # Generate keypair
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)
    
    # Create a simulated ComfyUI Tensor image
    # ComfyUI typically passes (batch, height, width, channels) with float32 in [0, 1]
    tensor = torch.rand(1, 256, 256, 3, dtype=torch.float32)
    print(f"Input Tensor shape: {tensor.shape}, dtype: {tensor.dtype}")
    
    # Simulate the conversion logic from nodes.py
    arr = tensor.numpy()
    print(f"After .numpy(): shape {arr.shape}, dtype {arr.dtype}, min {arr.min():.3f}, max {arr.max():.3f}")
    
    # Convert float to uint8
    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
    print(f"After float->uint8: shape {arr.shape}, dtype {arr.dtype}, min {arr.min()}, max {arr.max()}")
    
    # Remove batch dimension if present
    if len(arr.shape) == 4:
        print(f"Removing batch dimension from shape {arr.shape}")
        arr = arr[0]
        print(f"New shape after removing batch: {arr.shape}")
    
    # Convert to PIL Image (assuming 3 channels = RGB)
    pil_img = Image.fromarray(arr, mode='RGB')
    print(f"PIL Image: size {pil_img.size}, mode {pil_img.mode}")
    
    # Encrypt
    encrypted = encrypt_image(pil_img, public_pem)
    print(f"Encrypted data size: {len(encrypted)} bytes")
    
    # Decrypt
    decrypted_img = decrypt_image(encrypted, private_pem)
    print(f"Decrypted Image: size {decrypted_img.size}, mode {decrypted_img.mode}")
    
    # Verify
    assert decrypted_img.size == pil_img.size
    assert decrypted_img.mode == pil_img.mode
    print("✓ Tensor conversion test PASSED")
    print()

def test_numpy_array_image():
    """Test with a numpy array."""
    print("=" * 60)
    print("Test 2: Numpy array (uint8)")
    print("=" * 60)
    
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)
    
    # Create a simple numpy array
    arr = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    print(f"Input array shape: {arr.shape}, dtype {arr.dtype}")
    
    # Convert to PIL
    pil_img = Image.fromarray(arr, mode='RGB')
    print(f"PIL Image: size {pil_img.size}, mode {pil_img.mode}")
    
    # Encrypt and decrypt
    encrypted = encrypt_image(pil_img, public_pem)
    decrypted_img = decrypt_image(encrypted, private_pem)
    
    assert decrypted_img.size == pil_img.size
    print("✓ Numpy array test PASSED")
    print()

def test_pil_image():
    """Test with a PIL Image directly."""
    print("=" * 60)
    print("Test 3: PIL Image")
    print("=" * 60)
    
    private_pem, public_pem = generate_rsa_keypair(key_size=2048)
    
    # Create PIL image
    pil_img = Image.new('RGB', (256, 256), color=(73, 109, 137))
    print(f"PIL Image: size {pil_img.size}, mode {pil_img.mode}")
    
    # Encrypt and decrypt
    encrypted = encrypt_image(pil_img, public_pem)
    decrypted_img = decrypt_image(encrypted, private_pem)
    
    # Verify pixels match
    orig_pixels = list(pil_img.getdata())
    decr_pixels = list(decrypted_img.getdata())
    assert orig_pixels == decr_pixels
    print("✓ PIL Image test PASSED")
    print()

if __name__ == "__main__":
    try:
        test_comfyui_tensor_image()
        test_numpy_array_image()
        test_pil_image()
        print("=" * 60)
        print("All tests PASSED! ✓")
        print("=" * 60)
    except ImportError as e:
        print(f"ImportError: {e}")
        print("Make sure torch is installed: pip install torch")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
