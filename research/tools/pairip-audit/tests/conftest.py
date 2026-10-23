"""Test bootstrap: put the pairip_audit package (and the tests dir, for the
``fakes`` helper module) on sys.path so the suite runs from any rootdir via
``python -m pytest pairip-research/tools/pairip-audit/tests -q``.
"""

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]  # .../tools/pairip-audit
TESTS_DIR = Path(__file__).resolve().parent

for _path in (str(TOOLS_DIR), str(TESTS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)
