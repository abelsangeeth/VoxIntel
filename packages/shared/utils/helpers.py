"""Shared utility helpers."""

import hashlib
import re
from typing import Any, Dict


def slugify(text: str) -> str:
    """Convert arbitrary text to a lowercase URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


def sha256_hex(data: bytes) -> str:
    """Return SHA-256 hex digest of raw bytes — used for dedup checks."""
    return hashlib.sha256(data).hexdigest()


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dict using dot-notation keys."""
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
