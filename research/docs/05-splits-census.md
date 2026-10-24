# ABI-Split Census — PairIP Native-Library Coverage of Current Grindr (26.21.0)

**Date:** 2026-10-23
**Deliverable:** `docs/05` of the PairIP/GrindrPlus research program (charter in repo README; ROE in `ROE.md`). Extends the `docs/00`–`docs/04` series; closes the measurement gap that `docs/02` §7 left open (dossier open-question list, item 8 — `docs/01-pairip-dossier.md:267`).
**Question answered:** Does `libpairipcore.so` — the PairIP native VM runtime whose load the base split requests but does not ship (`docs/02` §2.2) — ship in the ABI split APKs of the current Grindr bundle (versionName 26.21.0, versionCode 189896), at what size per ABI, and what does the complete split picture say about how the protection is deployed?
**Method:** two passes over the same four artifacts. **(a)** The tested analyzer `tools/pairip-audit` was executed over each split this run — four executions, all exit code `0` (run record in §5); this doc reads the four JSON outputs those runs wrote to `samples/out/`. **(b)** An independent, stdlib-only verification pass (Python `zipfile` + `hashlib`), executed by this doc's author in this session: every `lib/` entry of each split listed by name and compressed size, and `libpairipcore.so` hashed per ABI. The two passes agree entry-for-entry (§3.2). Every claim below is either **[measured]** — produced this session or this run by a command or file read recorded here — or **[sourced]** — cited to `docs/01`/`docs/02`, which carry their own provenance grades.

**Path convention:** commands and paths are relative to the workspace root (the parent of `pairip-research/`), matching `docs/02`. `samples/` is gitignored (local-only by policy, `docs/02` §1).

---

## 1. Artifacts under test

All four config splits of the distributed bundle, as extracted to `pairip-research/samples/apk/splits/`. **[measured]** Each on-disk file is byte-identical to its entry inside the APKMirror container `grindr-current.apk` — verified this session by SHA-256-comparing the container entry bytes against the on-disk file bytes (script in §5c; all four reported `MATCHES container entry`).

| Artifact | Size (bytes) | SHA-256 | Contents (measured, §3) |
|---|---|---|---|
| `pairip-research/samples/apk/splits/split_config.arm64_v8a.apk` | 24,962,889 | `e5d2424aac2034fc517400b8ed12dfc879a3395f39c79398952582e9c70dc3ed` | 21 native libs (arm64-v8a) |
| `pairip-research/samples/apk/splits/split_config.x86_64.apk` | 23,225,978 | `f7ec894492845a94d014684bf98c54d1a53a5ab07887979c1c7c366a38fd0403` | 19 native libs (x86_64) |
| `pairip-research/samples/apk/splits/split_config.x86.apk` | 22,599,233 | `c8527a8318d3385edba3e7c6cab86ad6773e1d80c6515bd2dc9b9480342d2919` | 19 native libs (x86) |
| `pairip-research/samples/apk/splits/split_config.xxhdpi.apk` | 10,147,126 | `5637fb9cb72048727a657c0b24bab455b81014af17ccc9955c372042e12685fa` | resources only — 0 libs |

The base split (`grindr-current-base.apk`, 72,037,281 bytes, SHA-256 `4b73c916…b8ed63`) is not re-censused here; its census (`samples/out/census-base.json`, read this session) is the counterpart this doc reconciles against (§4). **[sourced for the base hash]** `docs/02` §1. **[measured this session]** the container additionally holds 16 language config splits (`split_config.ar.apk` … `split_config.zh.apk`, container `namelist()`); they were **not** opened by this census (§6).

---

## 2. The question `docs/02` left open — now answered

What the program previously recorded:

> "The **ABI split APKs** (`split_config.arm64_v8a.apk`, `split_config.x86.apk`, `split_config.x86_64.apk`) were **not analyzed**. Their contents — including whether `libpairipcore.so` ships in any of them — are **unmeasured** and are not asserted either way in this document (§7, Limitations)." — `docs/02-feasibility-study.md:95`

> "**Whether `libpairipcore.so` is present in any ABI split is unmeasured and must not be asserted either way.**" — `docs/02-feasibility-study.md:154`

The dossier had the same hole on the vendor side: "Which ABIs `libpairipcore.so` actually ships … was **not recorded by any source read**" (`docs/01:117`; open-question item 8, `docs/01:267`). `docs/02:166` named this census as the closing step.

**Answer [measured]:** `libpairipcore.so` **is present in all three ABI splits — arm64-v8a, x86_64, and x86 — and in no other split.** The xxhdpi split carries no native libraries at all (§3.3). Per-ABI entry path, size, and SHA-256:

| ABI | Entry | Size (bytes) | SHA-256 |
|---|---|---|---|
| arm64-v8a | `lib/arm64-v8a/libpairipcore.so` | 608,896 | `b20ee5bca05328b794744ab082c758ec2e0d298c5447e1a6415094ecc6987589` |
| x86_64 | `lib/x86_64/libpairipcore.so` | 624,184 | `a9c54f7a2e2a92d385354415bd46b2935904fb9235226a62864db6ea418fbba6` |
| x86 | `lib/x86/libpairipcore.so` | 697,616 | `46b814fb40c6e8b036c0a66eda72d6cac164434f40520e7a42c2a2c06bee76cc` |

Three different hashes and three different sizes: three distinct per-ABI builds, not one library stamped three times. **[sourced context]** the dossier records that the VM's opcode-to-handler mapping is re-randomized each time the library is built (`docs/01:61`); three distinct binaries are *consistent with* that, but this census did no binary analysis, so whether the three differ beyond target architecture is unmeasured (§6).

This also resolves the tension `docs/02:130` flagged — "`VMRunner.<clinit>` requests a library [measured] that this split does not ship [measured]": the library ships in every ABI split, which Android installs alongside the base on-device (runtime corroboration, §4.3).

---

## 3. Per-split census

### 3.1 Summary

**[measured]** — analyzer JSONs (`samples/out/census-split-*.json`, read this session) plus this session's independent `zipfile` pass (§5b). The two passes' native-lib inventories agree entry-for-entry: 21 / 19 / 19 / 0.

| Split APK | ZIP entries | Native libs (`lib/<abi>/*.so`) | PairIP native lib | Size (bytes) | SHA-256 |
|---|---|---|---|---|---|
| `split_config.arm64_v8a.apk` | 23 = 21 `lib/` + 2 root | 21 (arm64-v8a) | `lib/arm64-v8a/libpairipcore.so` | 608,896 | `b20ee5bc…987589` (§2) |
| `split_config.x86_64.apk` | 21 = 19 `lib/` + 2 root | 19 (x86_64) | `lib/x86_64/libpairipcore.so` | 624,184 | `a9c54f7a…8fbba6` (§2) |
| `split_config.x86.apk` | 21 = 19 `lib/` + 2 root | 19 (x86) | `lib/x86/libpairipcore.so` | 697,616 | `46b814fb…bee76cc` (§2) |
| `split_config.xxhdpi.apk` — **control** | 182 = 179 `res/` + 3 root | **0** | — none | — | — |

Supporting facts, all **[measured]** this session:

- **Root entries.** Each ABI split: `AndroidManifest.xml` + `stamp-cert-sha256` (the Play signing-stamp file) — nothing else. The xxhdpi split: `AndroidManifest.xml` + `resources.arsc` + `stamp-cert-sha256`.
- **No DEX, no assets in any split.** No split contains a `classes*.dex` or any `assets/` entry (analyzer `dexStats.totalMethods = 0` with empty `perDex` for all four; confirmed by the zipfile pass). Every DEX byte of this app lives in the base split.
- **Split manifests.** `versionCode` **189896** in all four splits — matching the base's 189896 (`census-base.json`) — with empty `versionName` (typical for config splits).
- **Analyzer verdicts.** `pairipDetected: true` for the three ABI splits (detection via `pairipNativeLibs`); `pairipDetected: false` for xxhdpi (`census-split-xxhdpi.json:5`).
- **Packaging.** Every `.so` in all three ABI splits is ZIP-**STORED** (`compress_type` 0; compressed size = uncompressed size for all 59 entries) — the uncompressed-native-lib layout Android bundles use so libs can be mmap'd directly from the APK. Sizes in §3.2 are therefore both the compressed and the on-disk size.
- **ABI-set note.** The 19 library names in the x86_64 and x86 splits are identical sets; the arm64-v8a split carries those same 19 **plus two arm64-only libraries** (`libPhoenixAndroid.so`, `libafb3.so`). The bundle has no armeabi-v7a split at all (container entry list, §1) — three ABIs shipped, `libpairipcore.so` in each. **[sourced context]** the vendor's protection tier is described as requiring "all four ABIs" (`docs/01:105`); this census measures presence only and does not adjudicate tier compliance.

### 3.2 Complete native-lib inventory (independent `zipfile` pass)

Every `lib/` entry of each split, as listed by this session's stdlib pass (§5b) — name and size in bytes (stored; see §3.1). The PairIP runtime is bolded. Analyzer agreement: each list matches the corresponding `nativeLibs` array in `census-split-<abi>.json` exactly.

**`split_config.arm64_v8a.apk` — 21 entries under `lib/arm64-v8a/`:**

| Library | Size (bytes) |
|---|---|
| `libPhoenixAndroid.so` | 1,925,269 |
| `libafb3.so` | 1,544,008 |
| `libagora-rtc-sdk.so` | 13,489,584 |
| `libagora-soundtouch.so` | 67,344 |
| `libagora_ffmpeg.so` | 804,784 |
| `libandroidx.graphics.path.so` | 10,096 |
| `libaosl.so` | 544,792 |
| `libapplovin-native-crash-reporter.so` | 843,152 |
| `libcrashlytics-common.so` | 864,800 |
| `libcrashlytics-handler.so` | 222,248 |
| `libcrashlytics-trampoline.so` | 9,408 |
| `libcrashlytics.so` | 232,152 |
| `libdatastore_shared_counter.so` | 10,360 |
| `libimage_processing_util_jni.so` | 32,528 |
| `libnative-jpeg.so` | 271,840 |
| **`libpairipcore.so`** | **608,896** |
| `libpl_droidsonroids_gif.so` | 42,416 |
| `librenderscript-toolkit.so` | 514,720 |
| `libsqliteJni.so` | 1,345,696 |
| `libsurface_util_jni.so` | 4,896 |
| `libvideo_dec.so` | 1,312,816 |

**`split_config.x86_64.apk` — 19 entries under `lib/x86_64/`:**

| Library | Size (bytes) |
|---|---|
| `libagora-rtc-sdk.so` | 14,855,120 |
| `libagora-soundtouch.so` | 67,344 |
| `libagora_ffmpeg.so` | 870,384 |
| `libandroidx.graphics.path.so` | 10,760 |
| `libaosl.so` | 528,688 |
| `libapplovin-native-crash-reporter.so` | 873,464 |
| `libcrashlytics-common.so` | 860,424 |
| `libcrashlytics-handler.so` | 210,208 |
| `libcrashlytics-trampoline.so` | 8,944 |
| `libcrashlytics.so` | 219,856 |
| `libdatastore_shared_counter.so` | 9,424 |
| `libimage_processing_util_jni.so` | 49,416 |
| `libnative-jpeg.so` | 260,144 |
| **`libpairipcore.so`** | **624,184** |
| `libpl_droidsonroids_gif.so` | 41,408 |
| `librenderscript-toolkit.so` | 439,304 |
| `libsqliteJni.so` | 1,247,392 |
| `libsurface_util_jni.so` | 4,912 |
| `libvideo_dec.so` | 1,804,336 |

**`split_config.x86.apk` — 19 entries under `lib/x86/`:**

| Library | Size (bytes) |
|---|---|
| `libagora-rtc-sdk.so` | 14,541,344 |
| `libagora-soundtouch.so` | 54,456 |
| `libagora_ffmpeg.so` | 767,348 |
| `libandroidx.graphics.path.so` | 9,284 |
| `libaosl.so` | 563,956 |
| `libapplovin-native-crash-reporter.so` | 835,288 |
| `libcrashlytics-common.so` | 863,884 |
| `libcrashlytics-handler.so` | 198,492 |
| `libcrashlytics-trampoline.so` | 6,952 |
| `libcrashlytics.so` | 208,864 |
| `libdatastore_shared_counter.so` | 7,976 |
| `libimage_processing_util_jni.so` | 41,276 |
| `libnative-jpeg.so` | 241,028 |
| **`libpairipcore.so`** | **697,616** |
| `libpl_droidsonroids_gif.so` | 40,660 |
| `librenderscript-toolkit.so` | 420,272 |
| `libsqliteJni.so` | 1,164,584 |
| `libsurface_util_jni.so` | 3,812 |
| `libvideo_dec.so` | 1,717,480 |

### 3.3 The xxhdpi control row

**[measured]** `split_config.xxhdpi.apk` contains 182 entries: 179 under `res/` plus `AndroidManifest.xml`, `resources.arsc`, and `stamp-cert-sha256`. Zero `lib/` entries, zero DEX, zero assets — a pure resource/density split. The analyzer's verdict matches: `pairipDetected: false`, `nativeLibs: {}`, `pairipNativeLibs: {}` (`census-split-xxhdpi.json:5-7`). It functions as the census' negative control: PairIP's native footprint appears exactly where Android's bundle format requires native code to live — the ABI splits — and nowhere in the density split.

---

## 4. Reconciliation with the base-split census (`docs/02`)

### 4.1 What each split type carries of the PairIP stack

**[measured]** from `census-base.json` (read this session; produced by the run recorded in `docs/02` §2.1) and this census:

| Layer | Base split | ABI splits | xxhdpi split |
|---|---|---|---|
| `com.pairip.*` classes | **46** (incl. `VMRunner`, `VmDecryptor`, `SignatureCheck`, `StartupLauncher`, `licensecheck.*`) | 0 (no DEX) | 0 (no DEX) |
| Manifest application | `com.pairip.application.Application` (PairIP wrapper) | — | — |
| Integrity wrapper | `SignatureCheck.verifyIntegrity` + `LicenseClient.checkLicense` wired at `attachBaseContext`; 110 integrity entry points (1 manifest-application + 108 pairip-call + 1 load-pairipcore, counted this session) | — | — |
| Entry wrapping | `StartupLauncher.launch` injected into `<clinit>` of `android.app.AppComponentFactory`, `androidx.core.app.CoreComponentFactory`, and the app's `qai` factory | — | — |
| VM load request | `VMRunner.<clinit>` → `System.loadLibrary("pairipcore")` | — | — |
| Native VM runtime | **none** (`nativeLibs: {}`) | **`libpairipcore.so` in every ABI** (§2) | none |
| VM-stub invocation | **20 stub methods / 422,621** (0.00473%) across 11 DEX | 0 (no DEX) | 0 (no DEX) |

### 4.2 The reconciliation

The two censuses together show the **full PairIP stack deployed across the bundle**: the native VM runtime (`libpairipcore.so`, 0.6–0.7 MB) ships in **every** ABI split — three distinct per-ABI builds (§2) — while the base split carries the **entire Java-side layer**: the integrity wrapper (`SignatureCheck.verifyIntegrity` and `LicenseClient.checkLicense`, both invoked from the PairIP application wrapper's `attachBaseContext` — the earliest startup hook), entry wrapping (the manifest application replaced by `com.pairip.application.Application`, and `StartupLauncher.launch` spliced into the static initializers of both framework component factories and the app's own `qai` factory), and `VMRunner` with its `System.loadLibrary("pairipcore")` request. Because Android installs the base together with the device-matching ABI split, the base's load request resolves on any device the app can run on; the "requests a library it does not ship" tension in `docs/02:130` was an artifact of analyzing the base split in isolation, and is closed by this census. What remains sparse is **invocation**: the VM-stub measurement from `census-base.json` still stands at **20 stub methods out of 422,621 method entries (0.00473%)** across the base's 11 DEX files (stub distribution: classes10 → 5, classes5 → 4, classes6 → 3, classes2 → 2, classes11 → 1, classes7 → 1, classes9 → 4) — unchanged by this census, since no split adds DEX. The deployment is therefore **integrity-first**: the always-on, every-launch protection is the signature/integrity/license wrapper at process entry, while the code-virtualization VM is fully shipped (all three ABIs) but sparsely invoked from the base split. Two boundaries keep that reading honest: (1) the 20-stub figure is a *floor on Java-visible stub markers*, not a ceiling on protection — the heuristic cannot see native-only virtualization, reflection-based delegation, or renamed runtimes (census notes, quoted verbatim at `docs/02:155` §7; `docs/02:132` §4); (2) no VM bytecode ships as plaintext `assets/*.vmcode` anywhere in the bundle (base: 647 `assets/` entries, zero `.vmcode` — counted this session; splits: no assets at all) — instead the base's `VMRunner.getVmByteCode` path reads bytecode out of the APK and decrypts it at runtime via `VmDecryptor` (`census-base.json` `integrityEntryPoints`: `getVmByteCode` → `readByteCode` → `openBaseApk`/`readFullByteArrayFromStream` + `VmDecryptor.decrypt`), so the VM payload is present but not statically enumerable by filename.

### 4.3 Runtime corroboration

**[measured]** `pairip-research/samples/out/gp-first-run.log` (logcat captured by this run's environment; file mtime 2026-10-23 20:31, one minute after the census JSONs were written — this doc's author read the file but did not capture it) shows the installed package's classloader with all splits coexisting: the `DexPathList` of `com.grindrapp.android` = `base.apk` + `split_config.arm64_v8a.apk` + `split_config.x86.apk` + `split_config.x86_64.apk` + `split_config.xxhdpi.apk`, with `nativeLibraryDirectories` including the split APKs' lib dirs (line 741; the surrounding `ClassNotFoundException` stacktrace for an unrelated ad-SDK class is the vehicle that exposed the loader path, not a finding). That is the on-device shape §4.2 relies on: base + ABI split(s) in one loader, so `loadLibrary("pairipcore")` resolves into an ABI split's `lib/` directory. (This run's test environment installed *all* splits; a store delivery to a real device installs base + the matching ABI split + the density split.)

---

## 5. Commands used (reproduction)

Environment: Windows/Git Bash, **Python 3.14.6**, **androguard 4.1.4** (both printed this session: `python --version`; `python -c "import androguard; print(androguard.__version__)"`). The (b)/(c) passes need only the Python standard library.

**(a) Analyzer runs — four executions this run, all exit code 0.** Run record (from the task record for this deliverable): arm64_v8a completed 2026-10-23 20:30:09, x86_64 20:30:13, x86 20:30:25, xxhdpi 20:30:29 (each tail: `androguard.core.apk:_apk_analysis:420 - Starting analysis on AndroidManifest.xml`); JSON outputs on disk at `samples/out/census-split-*.json` (mtimes 2026-10-23 20:30). The command form (CLI contract at `tools/pairip-audit/run_audit.py:7`; exit 0 includes `pairipDetected: false` results):

```bash
python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/splits/split_config.arm64_v8a.apk \
    --out pairip-research/samples/out/census-split-arm64_v8a.json

python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/splits/split_config.x86_64.apk \
    --out pairip-research/samples/out/census-split-x86_64.json

python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/splits/split_config.x86.apk \
    --out pairip-research/samples/out/census-split-x86.json

python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/splits/split_config.xxhdpi.apk \
    --out pairip-research/samples/out/census-split-xxhdpi.json
```

**(b) Independent native-lib enumeration + `libpairipcore.so` hashing — run by this doc's author this session** (produces §3.2 and the §2 hash table):

```python
import zipfile, hashlib

for apk in ["pairip-research/samples/apk/splits/split_config.arm64_v8a.apk",
            "pairip-research/samples/apk/splits/split_config.x86_64.apk",
            "pairip-research/samples/apk/splits/split_config.x86.apk",
            "pairip-research/samples/apk/splits/split_config.xxhdpi.apk"]:
    with zipfile.ZipFile(apk) as z:
        for i in sorted(z.infolist(), key=lambda x: x.filename):
            if i.filename.startswith("lib/"):
                print(i.filename, i.compress_size, "compress_type", i.compress_type)
                if i.filename.endswith("libpairipcore.so"):
                    print("  sha256:", hashlib.sha256(z.read(i.filename)).hexdigest())
```

**(c) Split↔container provenance check — run this session** (all four printed `MATCHES container entry`):

```python
import zipfile, hashlib, os

with zipfile.ZipFile("pairip-research/samples/apk/grindr-current.apk") as z:
    container_hashes = {n: hashlib.sha256(z.read(n)).hexdigest()
                        for n in z.namelist() if n.endswith(".apk")}

for p in ["pairip-research/samples/apk/splits/split_config.arm64_v8a.apk",
          "pairip-research/samples/apk/splits/split_config.x86_64.apk",
          "pairip-research/samples/apk/splits/split_config.x86.apk",
          "pairip-research/samples/apk/splits/split_config.xxhdpi.apk"]:
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    print(os.path.basename(p),
          "MATCHES container entry" if container_hashes.get(os.path.basename(p)) == h else "MISMATCH")
```

**(d) Supporting reads this session** (facts cited above): `zipfile` listing of root entries / DEX / assets per split and of the base APK (`grindr-current-base.apk`: 647 assets, 0 `.vmcode`, 0 `lib/`, 13 `.dex` entries = 11 root-level `classes*.dex` matching `census-base.json` `perDex` + 2 under `assets/audience_network/`); JSON reads of `census-base.json`, `census.json`, and the four `census-split-*.json`; text reads of `docs/02` (lines 95, 112, 130, 154, 166), `docs/01` (lines 61, 105, 117, 267), `samples/out/gp-first-run.log` (line 741ff), and `tools/pairip-audit/{run_audit.py,README.md}`.

---

## 6. Limitations

- **Provenance of the analyzer pass.** The four analyzer executions were performed by this run (record in §5a, given to this doc's author as the task record); the author read their JSON outputs and independently re-verified the native-lib inventory with the §5b pass. The author did not re-execute the analyzer. Every §3 number, however, is reproduced by the author-run §5b/§5c scripts, which need only the stdlib.
- **No binary analysis of `libpairipcore.so`.** The three `.so` files were hashed and sized, not disassembled. "Three distinct builds" (§2) is a hash observation; architecture-only vs. opcode-table divergence (`docs/01:61`) is unmeasured. Environment checks inside the library (`docs/01` §3.3, via `docs/02:130`) remain unmeasured and relevant to any hook-client work.
- **Coverage boundary.** Only the four config splits shipped to this workspace were censused. The 16 language splits in the container (§1) were not opened; nothing is asserted about their contents. Within the base split, 2 DEX files embedded as assets (`assets/audience_network/classes*.dex`, 57,076 and 5,237,600 bytes — measured this session) sit outside the analyzer's `classes*.dex` scan and outside `docs/02`'s 422,621-method denominator; their contents were not censused.
- **Static census only.** Nothing was executed against these splits by this doc; §4.3's runtime picture is read from a log this run's environment captured, not from an experiment designed here.
- **Heuristic limits carry over** (verbatim from every census JSON's notes): a low `stubPct` does not prove absence of virtualization; renamed/repackaged `com.pairip` classes, reflection-based delegation, and native-only virtualization are not detected; undecodable methods count as scan errors, not non-stubs.
- `samples/` is gitignored (local-only, ROE §4): the split APKs and census JSONs cited here are not in version control; the hashes in §1–§2 are the durable record.
