"""Pure logic for mapping APK zip entries ``lib/<abi>/*.so`` to native libraries.

Works on an iterable of entry names so it is testable against synthetic zip
fixtures without any real APK.  PairIP ships its protection runtime as
``libpairipcore.so`` (see pairip-research/samples/pairipcore/README.md,
``VMRunner`` static initializer: ``System.loadLibrary("pairipcore")``).
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

# lib/<abi>/<name>.so where <abi> is one path segment without further slashes.
_LIB_ENTRY_RE = re.compile(r"^lib/([^/]+)/([^/]+\.so)$")

# A PairIP native library is named after the protection runtime, e.g.
# libpairipcore.so.  Match on the lowercase stem containing "pairip".
_PAIRIP_LIB_TOKEN = "pairip"


def map_native_libs(entry_names: Iterable[str]) -> Dict[str, List[str]]:
    """Group ``lib/<abi>/*.so`` entries into ``{abi: [so_name, ...]}``.

    Entries outside a ``lib/<abi>/`` directory or not ending in ``.so`` are
    ignored.  Names inside each ABI are de-duplicated and sorted.
    """
    libs: Dict[str, List[str]] = {}
    seen: Dict[str, set] = {}
    for name in entry_names or []:
        if not name:
            continue
        match = _LIB_ENTRY_RE.match(name)
        if not match:
            continue
        abi, so_name = match.group(1), match.group(2)
        bucket = seen.setdefault(abi, set())
        if so_name not in bucket:
            bucket.add(so_name)
    for abi, names in seen.items():
        libs[abi] = sorted(names)
    return libs


def is_pairip_lib(so_name: str) -> bool:
    """True when a .so name belongs to the PairIP runtime (contains 'pairip')."""
    return _PAIRIP_LIB_TOKEN in (so_name or "").lower()


def filter_pairip_libs(native_libs: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Subset of :func:`map_native_libs` output restricted to PairIP libraries."""
    out: Dict[str, List[str]] = {}
    for abi, names in (native_libs or {}).items():
        pairip = [n for n in names if is_pairip_lib(n)]
        if pairip:
            out[abi] = pairip
    return out
