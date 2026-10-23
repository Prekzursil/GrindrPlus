"""Thin androguard adapter: the only module that touches the real APK file.

Everything downstream (nativelibs, assets, dexscan, census) is pure logic fed
by the small, mockable surface exposed here.  Requires androguard 4.1.x
(probed against 4.1.4: ``APK.get_files``/``get_dex_names``/``get_all_dex``/
``get_androidversion_name``/``get_androidversion_code``/
``get_attribute_value``; ``DEX(buff)``).
"""

from __future__ import annotations

import re
from typing import Iterator, List, Optional, Tuple

from androguard.core.apk import APK
from androguard.core.dex import DEX


class ApkError(Exception):
    """Raised when the APK cannot be opened or read."""


# Only "official" root-level dex files are enumerated (same rule as
# androguard's APK.get_dex_names, which get_all_dex iterates).
_DEX_NAME_RE = re.compile(r"^classes\d*\.dex$")


class ApkSource:
    """Read-only view over an APK via androguard."""

    def __init__(self, apk_path: str):
        self.path = str(apk_path)
        try:
            self._apk = APK(self.path)
        except Exception as exc:  # androguard raises many shapes; unify
            raise ApkError(f"failed to open APK {self.path!r}: {exc}") from exc

    # -- manifest facts ------------------------------------------------------

    @property
    def version_name(self) -> str:
        try:
            return self._apk.get_androidversion_name() or ""
        except Exception:
            return ""

    @property
    def version_code(self) -> str:
        try:
            return self._apk.get_androidversion_code() or ""
        except Exception:
            return ""

    @property
    def application_class(self) -> str:
        """The ``android:name`` of the ``<application>`` element (may be empty).

        Note: androguard's ``get_app_name()`` returns the display *label*;
        the Application class needs the ``name`` attribute.
        """
        try:
            return self._apk.get_attribute_value("application", "name") or ""
        except Exception:
            return ""

    # -- zip-level facts -----------------------------------------------------

    def entry_names(self) -> List[str]:
        """All zip entry names in the APK."""
        try:
            return list(self._apk.get_files())
        except Exception as exc:
            raise ApkError(f"failed to list APK entries: {exc}") from exc

    # -- dex units -----------------------------------------------------------

    def dex_units(self) -> Iterator[Tuple[str, Optional[object]]]:
        """Yield ``(dex_name, DEX_or_None)`` for every official dex file.

        A dex whose bytes fail to parse yields ``(name, None)`` so the census
        can record it as unreadable instead of aborting the whole audit.
        """
        try:
            names = [n for n in self._apk.get_files() if _DEX_NAME_RE.match(n)]
            blobs = list(self._apk.get_all_dex())
        except Exception as exc:
            raise ApkError(f"failed to read dex data: {exc}") from exc
        for index, blob in enumerate(blobs):
            name = names[index] if index < len(names) else f"classes{index + 1}.dex"
            try:
                yield name, DEX(blob)
            except Exception:
                yield name, None
