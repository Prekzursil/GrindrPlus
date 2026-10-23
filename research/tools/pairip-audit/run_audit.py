#!/usr/bin/env python3
"""pairip-audit CLI: static PairIP census of an APK.

Usage (from the workspace root, or any directory -- paths are resolved
relative to the current working directory):

    python pairip-research/tools/pairip-audit/run_audit.py <apk_path> --out <json_path>

Exit codes:
    0  success (includes APKs without PairIP -- ``pairipDetected`` is false)
    1  the APK could not be opened or read (bad zip, missing file, ...)
    2  usage error (argparse)

Read-only: the tool never writes to the APK and produces no bypass or
patching capability -- only a structural census JSON.
"""

from __future__ import annotations

import argparse
import os
import sys

# Make the package importable no matter the current working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from pairip_audit.apksource import ApkError  # noqa: E402
from pairip_audit.census import audit_apk, write_census  # noqa: E402
from pairip_audit import __version__  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pairip-audit",
        description="Read-only static census of PairIP protection markers in an APK.",
    )
    parser.add_argument("apk", help="path to the APK to audit")
    parser.add_argument(
        "--out",
        required=True,
        help="path of the census JSON to write",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not os.path.isfile(args.apk):
        print(f"error: no such file: {args.apk}", file=sys.stderr)
        return 1

    try:
        census = audit_apk(args.apk)
    except ApkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        write_census(census, args.out)
    except OSError as exc:
        print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
        return 1

    stats = census["dexStats"]
    print(
        f"{census['apk']}: pairipDetected={census['pairipDetected']} "
        f"pairipClasses={len(census['pairipClasses'])} "
        f"stubs={stats['stubMethods']}/{stats['totalMethods']} "
        f"({stats['stubPct']}%) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
