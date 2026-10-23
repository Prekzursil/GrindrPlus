"""pairip-audit: read-only static census of PairIP (Play Integrity Protect) in an APK.

The tool inspects a publicly distributed APK artifact and reports structural
facts only: whether PairIP markers are present (``com.pairip.*`` classes,
``libpairip*.so`` native libraries, ``assets/*.vmcode`` VM bytecode files),
which methods look like PairIP VM stubs, and where integrity entry points
live.  It performs no patching, repacking, or bypass of any protection.

Submodules:

- :mod:`pairip_audit.nativelibs` -- pure mapping of ``lib/<abi>/*.so`` zip
  entries (works on plain entry-name lists / synthetic zips).
- :mod:`pairip_audit.assets` -- pure detection of PairIP VM bytecode assets.
- :mod:`pairip_audit.stubs` -- pure instruction-level stub heuristic; operates
  on anything that quacks like androguard instructions (mockable).
- :mod:`pairip_audit.dexscan` -- pure dex traversal over androguard-shaped
  class/method objects (mockable).
- :mod:`pairip_audit.apksource` -- thin androguard adapter (the only module
  that touches the real APK file).
- :mod:`pairip_audit.census` -- pure census assembly + orchestration.
"""

__version__ = "1.0.0"

HEURISTIC_DOC = (
    "A method outside com.pairip.* is counted as a PairIP VM stub when its "
    "Dalvik bytecode contains an invoke instruction targeting "
    "Lcom/pairip/VMRunner;->invoke or ->executeVM."
)
