"""Census assembly (pure) + audit orchestration over :class:`ApkSource`.

The JSON census contract (keys, in order):

``apk, versionName, versionCode, pairipDetected, nativeLibs, pairipNativeLibs,
pairipClasses, dexStats, integrityEntryPoints, notes``
"""

from __future__ import annotations

import json
from typing import Dict, List

from . import HEURISTIC_DOC
from .apksource import ApkError, ApkSource
from .assets import find_vmcode_assets
from .dexscan import MAX_ENTRY_POINTS, scan_dex, DexScan, combine
from .nativelibs import filter_pairip_libs, map_native_libs

#: Dotted prefix used for the manifest-application cross-check.
PAIRIP_DOTTED = "com.pairip."


def coerce_version_code(value) -> object:
    """androguard returns versionCode as a string; keep numeric ones numeric."""
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def base_notes(vmcode_assets: List[str]) -> List[str]:
    """Static documentation of the stub heuristic and its limits."""
    notes = [
        "Stub heuristic: " + HEURISTIC_DOC,
        "Marker grounding: pairipcore-vm research notes that virtualized "
        "classes 'invoke VMRunner.executeVM instead of executing regular Java "
        "code' (samples/pairipcore-vm/docs/source/introduction.md), and "
        "VMRunner.invoke/executeVM are the documented Java-side/native VM "
        "entries (samples/pairipcore/README.md).",
        "Methods declared inside com.pairip.* are never counted as stubs: the "
        "VM runtime itself (e.g. VMRunner.invoke -> executeVM) lives there.",
        "Heuristic limits (best effort): (1) a method is only inspected when "
        "androguard's linear-sweep disassembler can decode its code item -- "
        "undecodable methods are counted as scan errors, not as non-stubs; "
        "(2) renamed/repackaged com.pairip classes, reflection-based "
        "delegation, or native-only virtualization are NOT detected; (3) a "
        "low stubPct does not prove absence of virtualization; (4) stubPct "
        "counts all defined method entries (including abstract/native) in "
        "totalMethods.",
        "pairipDetected = com.pairip.* classes present OR pairip native "
        "library present OR assets/*.vmcode present.",
    ]
    if vmcode_assets:
        notes.append(
            "VM bytecode assets (per samples/pairipcore-vm: './assets/"
            "data.vmcode'): " + ", ".join(vmcode_assets)
        )
    return notes


def build_census(
    *,
    apk: str,
    version_name: str,
    version_code,
    entry_names: List[str],
    dex_scans: List[DexScan],
    unreadable_dex: List[str],
    manifest_app: str = "",
) -> Dict:
    """Assemble the census dict from collected facts (pure function)."""
    native_libs = map_native_libs(entry_names)
    pairip_native_libs = filter_pairip_libs(native_libs)
    vmcode_assets = find_vmcode_assets(entry_names)

    pairip_class_set = {
        name for scan in dex_scans for name in scan.pairip_classes
    }
    pairip_classes = sorted(pairip_class_set)

    entry_points: List[Dict] = []
    for scan in dex_scans:
        entry_points.extend(scan.entry_points)
    if manifest_app and (
        manifest_app.startswith(PAIRIP_DOTTED) or manifest_app in pairip_class_set
    ):
        entry_points.insert(
            0, {"class": manifest_app, "method": None, "kind": "manifest-application"}
        )
    total_dropped = sum(s.dropped_entry_points for s in dex_scans)

    notes = base_notes(vmcode_assets)
    scan_errors = sum(s.scan_errors for s in dex_scans)
    if scan_errors:
        notes.append(
            f"{scan_errors} method(s) could not be disassembled and were "
            "excluded from the stub count."
        )
    if unreadable_dex:
        notes.append(
            "Dex file(s) that failed to parse and were skipped: "
            + ", ".join(unreadable_dex)
        )
    if total_dropped:
        notes.append(
            f"{total_dropped} integrity entry point(s) omitted beyond the "
            f"per-APK cap ({MAX_ENTRY_POINTS})."
        )

    pairip_detected = bool(
        pairip_classes or any(pairip_native_libs.values()) or vmcode_assets
    )

    return {
        "apk": apk,
        "versionName": version_name,
        "versionCode": coerce_version_code(version_code),
        "pairipDetected": pairip_detected,
        "nativeLibs": native_libs,
        "pairipNativeLibs": pairip_native_libs,
        "pairipClasses": pairip_classes,
        "dexStats": combine(dex_scans),
        "integrityEntryPoints": entry_points,
        "notes": notes,
    }


def audit_apk(apk_path: str) -> Dict:
    """Orchestrate a full read-only audit; returns the census dict.

    Raises :class:`ApkError` when the artifact cannot be opened/read.
    """
    source = ApkSource(apk_path)
    entry_names = source.entry_names()

    dex_scans: List[DexScan] = []
    unreadable: List[str] = []
    for name, dex in source.dex_units():
        if dex is None:
            unreadable.append(name)
            continue
        dex_scans.append(scan_dex(dex, name))

    return build_census(
        apk=source.path,
        version_name=source.version_name,
        version_code=source.version_code,
        entry_names=entry_names,
        dex_scans=dex_scans,
        unreadable_dex=unreadable,
        manifest_app=source.application_class,
    )


def write_census(census: Dict, out_path: str) -> None:
    """Serialize the census to ``out_path`` as pretty JSON (utf-8)."""
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(census, handle, indent=2)
        handle.write("\n")
