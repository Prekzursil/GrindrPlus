"""Pure detection of PairIP VM bytecode assets inside an APK.

Grounding: the PairIP "pseudo-VM files" needed for the app to work are placed
in the ``assets`` folder (pairip-research/samples/pairipcore/README.md, the
paragraph starting "pairipcore creates pseudo-VM files"); the companion
research operates on ``./assets/data.vmcode``
(pairip-research/samples/pairipcore-vm/README.md, ``pairip find-key`` usage).
"""

from __future__ import annotations

from typing import Iterable, List

_VMCODE_SUFFIX = ".vmcode"
_ASSETS_PREFIX = "assets/"


def find_vmcode_assets(entry_names: Iterable[str]) -> List[str]:
    """Return sorted asset entry names that look like PairIP VM bytecode files.

    Marker: any entry under ``assets/`` whose name ends with ``.vmcode``.
    """
    found = set()
    for name in entry_names or []:
        if not name:
            continue
        if name.startswith(_ASSETS_PREFIX) and name.endswith(_VMCODE_SUFFIX):
            found.add(name)
    return sorted(found)
