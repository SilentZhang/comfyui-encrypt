"""comfyui_encrypt package for ComfyUI custom nodes.

This package follows the ComfyUI-NodeSample pattern for node discovery.
"""


import sys
import traceback
print("[__init__.py] Importing NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS from nodes.py")
try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    print("[__init__.py] Successfully imported NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS")
    __all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
except ImportError as e:
    print(f"[__init__.py] ImportError: {e}", file=sys.stderr)
    traceback.print_exc()
    # Fallback for when run directly or during testing
    __all__ = []


