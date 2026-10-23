# pairip-audit

Read-only static census of **PairIP** (Google Play Integrity Protect,
`com.pairip.*` / `libpairipcore.so`) markers in an Android APK.
The tool **only reads** an APK and reports structure — it has no patching,
repacking, or bypass capability (see the repository `ROE.md`).

Implemented in pure Python on the standard library plus
[androguard](https://github.com/androguard/androguard) 4.1.4.

## Usage

From the workspace root (the parent of `pairip-research/`):

```bash
python pairip-research/tools/pairip-audit/run_audit.py <apk_path> --out <json_path>
```

Exit code `0` on success — including for an APK with no PairIP
(`pairipDetected: false`). Non-zero (`1`) when the artifact cannot be
opened/read, `2` on usage errors.

Example output (`census.json`, abbreviated):

```json
{
  "apk": "app.apk",
  "versionName": "25.21.1",
  "versionCode": 250211,
  "pairipDetected": true,
  "nativeLibs": { "arm64-v8a": ["libother.so", "libpairipcore.so"] },
  "pairipNativeLibs": { "arm64-v8a": ["libpairipcore.so"] },
  "pairipClasses": ["com.pairip.SignatureCheck", "com.pairip.VMRunner", "..."],
  "dexStats": {
    "totalMethods": 10,
    "stubMethods": 2,
    "stubPct": 20.0,
    "perDex": [{ "dex": "classes.dex", "classes": 5, "methods": 10, "stubMethods": 2 }]
  },
  "integrityEntryPoints": [
    { "class": "com.pairip.application.Application", "method": null, "kind": "manifest-application" },
    { "class": "com.pairip.application.Application", "method": "attachBaseContext",
      "kind": "pairip-call", "targets": ["Lcom/pairip/SignatureCheck;->verifyIntegrity"] },
    { "class": "com.pairip.VMRunner", "method": "<clinit>", "kind": "load-pairipcore", "library": "pairipcore" }
  ],
  "notes": ["Stub heuristic: ...", "..."]
}
```

### Census keys

| key | meaning |
| --- | --- |
| `apk` | APK path as passed on the command line |
| `versionName` / `versionCode` | manifest version facts (`versionCode` numeric when possible) |
| `pairipDetected` | `com.pairip.*` classes **or** pairip native lib **or** `assets/*.vmcode` present |
| `nativeLibs` | ABI → `.so` name list, from `lib/<abi>/*.so` entries |
| `pairipNativeLibs` | subset of `nativeLibs` whose name contains `pairip` (e.g. `libpairipcore.so`) |
| `pairipClasses` | dotted `com.pairip.*` class list found across all dex files |
| `dexStats` | `totalMethods`, `stubMethods`, `stubPct`, `perDex` breakdown |
| `integrityEntryPoints` | manifest application class, `SignatureCheck`-style call sites, `System.loadLibrary("pairipcore")` sites |
| `notes` | heuristic documentation + limits + runtime caveats (scan errors, skipped dex files) |

## The stub / virtualized-method heuristic

Grounded in the two public research repositories vendored under
`pairip-research/samples/`, read before implementing:

1. **`samples/pairipcore-vm/docs/source/introduction.md`** — *"some classes
   invoke `VMRunner.executeVM` instead of executing regular Java code"*:
   PairIP virtualizes selected methods; the original body is replaced by a
   stub that delegates to the PairIP VM.
2. **`samples/pairipcore/README.md`** — `com.pairip.VMRunner` exposes
   `public static Object invoke(String vmByteCodeFile, Object[] args)`
   (reads VM bytecode from the APK `assets/` folder) which calls
   `public static native Object executeVM(byte[] vmCode, Object[] args)`;
   its static initializer runs `System.loadLibrary("pairipcore")`.
   The host application class (`com.pairip.application.Application`) calls
   `SignatureCheck.verifyIntegrity(context)` from `attachBaseContext`.
3. **`samples/pairipcore-vm/README.md`** — VM bytecode files live in
   `assets/` (e.g. `./assets/data.vmcode`).

**Implemented marker:** a method outside `com.pairip.*` is counted as a
PairIP VM **stub** when its Dalvik bytecode contains an invoke instruction
targeting `Lcom/pairip/VMRunner;->invoke` or `->executeVM` (resolved through
androguard's instruction disassembly). `stubPct` is `stubMethods /
totalMethods` across all dex files.

Secondary findings (reported, not counted as stubs):

- invokes of *other* `com.pairip.*` classes → `integrityEntryPoints`
  entries of kind `pairip-call` (e.g. `SignatureCheck.verifyIntegrity`);
- `const-string "pairipcore"` combined with an invoke of
  `System.loadLibrary/load` → kind `load-pairipcore`;
- the manifest `<application android:name>` when it is a `com.pairip.*`
  class → kind `manifest-application`.

### Known limits (best effort — also recorded in every census `notes`)

- Methods declared inside `com.pairip.*` are never counted as stubs — the VM
  runtime itself lives there (`VMRunner.invoke` calls `executeVM`).
- A method is only inspected when androguard's linear-sweep disassembler can
  decode its code item; undecodable methods are counted as scan errors
  (reported in `notes`), not as non-stubs.
- Renamed/repackaged `com.pairip` classes, reflection-based delegation, or
  native-only virtualization are **not** detected.
- A low `stubPct` does not prove absence of virtualization.
- `totalMethods` counts all defined method entries (including
  abstract/native).

## Development

```bash
pip install -r pairip-research/tools/pairip-audit/requirements.txt

# from the workspace root:
python -m pytest pairip-research/tools/pairip-audit/tests -q
# (from the pairip-research repo root, as CI does:)
python -m pytest tools/pairip-audit/tests -q
```

The suite needs **no real APK**: androguard objects are faked
(`tests/fakes.py`) and APK zip entry names come from synthetic zips built
with the stdlib `zipfile` (`tests/conftest.py` puts the package on
`sys.path`).

### Layout

```
pairip_audit/           the package
  nativelibs.py         lib/<abi>/*.so mapping (pure)
  assets.py             assets/*.vmcode detection (pure)
  stubs.py              instruction-level stub heuristic (pure)
  dexscan.py            dex traversal + counters (pure, mock-friendly)
  apksource.py          thin androguard adapter (only module touching the APK)
  census.py             census assembly (pure) + audit orchestration
run_audit.py            CLI entry point
tests/                  pytest suite (fakes + synthetic zips)
```

CI: `.github/workflows/ci.yml` (repo root) runs the same pytest suite on
every push.
