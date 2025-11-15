"""comfyui_encrypt package for ComfyUI custom nodes.

This package follows the ComfyUI-NodeSample pattern for node discovery.
"""

# Only import when run as a package (not when pytest discovers the root)
try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    __all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
except ImportError:
    # Fallback for when run directly or during testing
    __all__ = []


