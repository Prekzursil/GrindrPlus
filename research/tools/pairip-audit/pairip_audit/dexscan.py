"""Traversal of androguard-shaped DEX objects: census counters + stub findings.

Pure logic over objects that quack like androguard's ``DEX`` (``get_classes``
-> ``ClassDefItem.get_name()/get_methods()`` -> ``EncodedMethod``), so tests
drive it with fakes rather than real dex bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .stubs import is_pairip_class_name, is_stub, scan_method

#: Hard cap on collected integrity entry points per APK (keeps the census
#: bounded for huge multidex apps).
MAX_ENTRY_POINTS = 500


@dataclass
class DexScan:
    """Census result for one dex file."""

    name: str
    classes: int = 0
    methods: int = 0
    stub_methods: int = 0
    scan_errors: int = 0
    #: Dotted names (``com.pairip.VMRunner``) of classes under com.pairip.*.
    pairip_classes: List[str] = field(default_factory=list)
    #: Integrity/licensing call sites discovered in this dex.
    entry_points: List[Dict] = field(default_factory=list)
    #: Number of entry points dropped because of MAX_ENTRY_POINTS.
    dropped_entry_points: int = 0


def to_dotted(class_ref: str) -> str:
    """Convert a Dalvik descriptor ``Lcom/pairip/VMRunner;`` to
    ``com.pairip.VMRunner``.  Non-class descriptors pass through unchanged."""
    if class_ref.startswith("L") and class_ref.endswith(";"):
        return class_ref[1:-1].replace("/", ".")
    return class_ref


def _entry_point(class_name_ref: str, method_name: str, findings) -> Optional[Dict]:
    """Build an integrity entry-point record, or None when uninteresting."""
    targets = sorted(set(findings.pairip_refs))
    if not targets and not findings.loads_pairipcore:
        return None
    entry: Dict = {
        "class": to_dotted(class_name_ref),
        "method": method_name,
        "kind": "pairip-call",
    }
    if targets:
        entry["targets"] = targets
    if findings.loads_pairipcore:
        entry["kind"] = "load-pairipcore"
        entry["library"] = "pairipcore"
    return entry


def scan_dex(dex, name: str) -> DexScan:
    """Scan one DEX-shaped object (``dex.get_classes()`` iterable)."""
    result = DexScan(name=name)
    for cls in dex.get_classes():
        class_ref = cls.get_name() or ""
        result.classes += 1
        if is_pairip_class_name(class_ref):
            result.pairip_classes.append(to_dotted(class_ref))
        for method in cls.get_methods():
            result.methods += 1
            findings, error = scan_method(method)
            if error is not None:
                result.scan_errors += 1
                continue
            if findings is None:  # abstract / native: no code item
                continue
            if is_stub(class_ref, findings):
                result.stub_methods += 1
            entry = _entry_point(class_ref, method.get_name() or "", findings)
            if entry is not None:
                if len(result.entry_points) < MAX_ENTRY_POINTS:
                    result.entry_points.append(entry)
                else:
                    result.dropped_entry_points += 1
    return result


def combine(scans: List[DexScan]) -> Dict:
    """Merge per-dex scans into the ``dexStats`` census block."""
    total_methods = sum(s.methods for s in scans)
    stub_methods = sum(s.stub_methods for s in scans)
    return {
        "totalMethods": total_methods,
        "stubMethods": stub_methods,
        "stubPct": round(stub_methods * 100.0 / total_methods, 2) if total_methods else 0.0,
        "perDex": [
            {
                "dex": s.name,
                "classes": s.classes,
                "methods": s.methods,
                "stubMethods": s.stub_methods,
            }
            for s in scans
        ],
    }
