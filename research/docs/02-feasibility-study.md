# Feasibility Study — PairIP Protection of Current Grindr (26.21.0) and Client-Side Modding

**Date:** 2026-10-22
**Deliverable:** `docs/02` of the PairIP/GrindrPlus research program (charter in repo README; ROE in `ROE.md`).
**Question answered:** Is the current public Grindr build (versionName 26.21.0, versionCode 189896) protected by PairIP, how heavily is it virtualized, and what does that mean for client-side modding (GrindrPlus-style hook clients and static repackaging)?
**Method:** static census of the distributed artifact with `tools/pairip-audit` (read-only; no bypass produced — ROE §1), cross-referenced against `docs/01-pairip-dossier.md`. Every claim below is either **[measured]** — produced this run by a command or file read recorded here — or **[sourced]** — cited to the dossier, which carries its own provenance grades.

**Path convention:** commands and code references are given relative to the workspace root (the parent of `pairip-research/`); the census JSON's own `apk` fields use the same convention. Code refs into the analyzer are `pairip-research/tools/pairip-audit/...`.

---

## 1. Artifacts under test

| Artifact | Size (bytes) | SHA-256 | Acquired |
|---|---|---|---|
| `pairip-research/samples/apk/grindr-current.apk` | 114,511,937 | `22c7743951b49a0cf6d11f7f05b517c1bdd8c8e6339441dccdc06a5a46ae751c` | APKMirror, 2026-10-22 (per task record; file mtime 2026-10-22 07:51) |
| `pairip-research/samples/apk/grindr-current-base.apk` | 72,037,281 | `4b73c916b9b85c672070caebe859cda010c90f0df9e098e542cc3c1113b8ed63` | extracted from the container (see §3.3); file mtime 2026-10-22 07:52 |

Both census outputs live in `pairip-research/samples/out/` (`census.json`, mtime 07:53; `census-base.json`, mtime 08:02). `samples/` is gitignored (ROE §4 hygiene; `.gitignore` line 1), so these artifacts are local-only by policy — confirmed by `git log --oneline --all -- samples/out/` returning nothing.

**Container metadata [measured]** — `info.json` inside `grindr-current.apk` (read this run via Python `zipfile`): APKMirror bundle format `apkm_version: 5`; `app_name` "Grindr - Gay Dating & Chat"; `release_version` "26.21.0"; `versioncode` "189896"; `pname` `com.grindrapp.android`; `post_date` "2026-10-15 23:11:41" (APKMirror's release-posting date; acquisition was 2026-10-22); `arches` `["arm64-v8a","x86","x86_64"]`; `dpis` `["480"]`; 16 language configs; `min_api` "26".

---

## 2. Measured on the artifact

Everything in this section was produced or re-produced in this session on this machine (Python 3.14.6, androguard 4.1.4). The analyzer is `pairip-research/tools/pairip-audit/run_audit.py` (CLI documented at `pairip-research/tools/pairip-audit/README.md:13-17`).

### 2.1 The exact commands

Census production (from the workspace root; the `--out` targets are the files now on disk):

```bash
python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/grindr-current.apk \
    --out pairip-research/samples/out/census.json

python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/grindr-current-base.apk \
    --out pairip-research/samples/out/census-base.json
```

**Reproduction this run.** I re-ran both commands verbatim (only `--out` redirected to temp files) at 2026-10-22 12:41–12:42 local. Result, per a key-by-key JSON comparison I executed:

- `grindr-current-base.apk`: reproduced census **identical in every key** to `samples/out/census-base.json` (46 classes, 422,621 methods, 20 stubs, 110 entry points, version 26.21.0/189896).
- `grindr-current.apk`: reproduced census **identical in every key** to `samples/out/census.json` (all-empty, `pairipDetected=false`).
- CLI summary lines printed: `pairipDetected=True pairipClasses=46 stubs=20/422621 (0.0%)` and, for the container, the empty-census equivalent.

**Analyzer suite verification.** `python -m pytest pairip-research/tools/pairip-audit/tests -q` (run this session from the workspace root) → **81 passed in 3.04s**. The suite uses faked androguard objects and synthetic zips, no real APK (`README.md:121-125`).

### 2.2 Census of the base split — `census-base.json`

Read from `pairip-research/samples/out/census-base.json` (every number below also re-counted programmatically this run):

| Fact | Value | Where in file |
|---|---|---|
| Target | `pairip-research/samples/apk/grindr-current-base.apk` | `apk` (line 2) |
| versionName / versionCode | **26.21.0 / 189896** | lines 3–4 |
| `pairipDetected` | **true** | line 5 |
| `com.pairip.*` classes | **46** (lines 9–54; recounted = 46) | `pairipClasses` |
| Native libs in this split | `{}` — **none** | `nativeLibs` / `pairipNativeLibs` (lines 6–7) |
| dex files scanned | **11** (classes.dex, classes2–11.dex) | `dexStats.perDex` |
| total method entries | **422,621** (per-dex sum re-verified = 422,621; 76,167 class entries) | lines 56–127 |
| VM-stub methods | **20** → `stubPct` **0.0** (two-decimal rounding; exact = 20/422,621 = **0.00473 %**) | lines 57–59 |
| integrity entry points | **110** = 1 `manifest-application` + 1 `load-pairipcore` + 108 `pairip-call` | lines 129–1112 |

The 46 classes split into: 11 in `com.pairip.*` proper — `InitContextProvider`, `SignatureCheck`(+`SignatureTamperedException`), `StartupLauncher`, `Utils`(+`Utils$1`), `VMRunner`(+`VMRunner$1`,+`VMRunnerException`), `VmDecryptor`, `application.Application` — and 35 in `com.pairip.licensecheck.*` (`LicenseClient` + 21 inner classes/lambdas, `LicenseActivity` + 6, `LicenseResponseHelper`, `LicenseContentProvider`, `TrialClient`, `ILicenseV2ResultListener`(+Stub), `LicenseCheckException`, `RepeatedCheckMetadata`).

Per-dex stub distribution (0 in classes.dex, classes3, classes4, classes8): classes10: 5, classes5: 4, classes9: 4, classes6: 3, classes2: 2, classes11: 1, classes7: 1 → 20.

**Structural highlights from `integrityEntryPoints`** (all read from the file):

- **Manifest application is a PairIP class:** the `<application android:name>` resolves to `com.pairip.application.Application` (kind `manifest-application`, lines 130–134). The analyzer only records this when the manifest attribute is a `com.pairip.*` name (`census.py:84-89`) — i.e., the app's manifest entry point is the PairIP wrapper, not an application class of Grindr's own.
- **Startup chain wraps the earliest framework hooks:** `android.app.AppComponentFactory.<clinit>` (lines 136–142) and `androidx.core.app.CoreComponentFactory.<clinit>` (lines 143–150) each invoke `Lcom/pairip/StartupLauncher;->launch`; an obfuscated app class `qai.<clinit>` does the same (lines 1104–1111). Entry-point wrapping reaches into the `androidx` namespace, not just `com.grindrapp.*`.
- **Signature + license + VM context wired at `attachBaseContext`:** `com.pairip.application.Application.attachBaseContext` invokes `SignatureCheck.verifyIntegrity`, `VMRunner.setContext`, `super.attachBaseContext`, and `LicenseClient.checkLicense` (lines 260–269). Independently, `com.pairip.licensecheck.LicenseContentProvider.onCreate` invokes `LicenseClient.checkLicense` (lines 1032–1039) — the licensing layer also self-starts via a ContentProvider.
- **Native-library request present, library absent from this split:** `com.pairip.VMRunner.<clinit>` is the sole `load-pairipcore` entry (`const-string "pairipcore"` + `System.loadLibrary/load`; kind `load-pairipcore`, lines 176–181). The base split itself contains **zero** `lib/<abi>/*.so` entries (census `nativeLibs` = `{}`, confirmed by my own zip listing: 0 `.so` files, no `lib/` dirs).
- **This build's `VMRunner` variant differs from the published description:** the recorded call graph shows `invoke` → `getVmByteCode` → `VmDecryptor.<init>`/`VmDecryptor.decrypt` (lines 209–217), plus `openBaseApk` → `getApkFromContextPath`/`getApkPathFromResource` (lines 231–240). No method's recorded targets include `VMRunner.executeVM`. This is a measured observation about this build's wiring only; §5 notes what public research describes, and the two need not match (per-build variation is documented there).
- **No `assets/*.vmcode` entries:** the analyzer would have appended a "VM bytecode assets" note had any matched (`census.py:53-57`); `census-base.json`'s `notes` contain no such note, and my own name-level zip scan found no `assets/*vmcode*` or `assets/*.iap` entries in the base split.
- **Complete coverage, zero scan errors:** the census appends notes for undecodable methods, skipped dex files, and capped entry points (`census.py:94-108`). None are present — all 11 dex parsed, all 422,621 method entries decoded and inspected, and the 110 entry points are uncapped (cap is 500, `dexscan.py:17`).

### 2.3 Census of the APKMirror download — `census.json`

`samples/out/census.json` (read in full; 23 lines): `pairipDetected` **false**, `pairipClasses` **[]**, `dexStats.totalMethods` **0**, `perDex` **[]**, `integrityEntryPoints` **[]**, `versionName`/`versionCode` **empty**. Reproduced identically this run (§2.1).

**Why it is empty — measured, not conjectured.** I listed the zip structure of both files with Python `zipfile` this run:

- `grindr-current.apk` has **27 entries**, and its root holds **no** `classes*.dex`, **no** `AndroidManifest.xml`, **no** `lib/` tree. Its root files are `base.apk`, 20 `split_config.*.apk` files (16 languages `ar de es fr hi in it ja ko ms pl pt ru th vi zh`, 3 ABIs `arm64_v8a`/`x86`/`x86_64`, 1 density `xxhdpi`), plus APKMirror metadata (`info.json`, `icon.png`, `APKM_installer.url`) and `META-INF`.
- The analyzer enumerates only root-level `classes\d*\.dex` (`pairip_audit/apksource.py:25,84`) and reads versions from the APK manifest (`apksource.py:41-52`); a container with no root dex and no root manifest therefore yields exactly the empty census observed. The exit code was still 0 because an APK without PairIP markers is a successful audit (`run_audit.py:9-11`).
- **`grindr-current-base.apk` is the container's inner `base.apk`, byte-identical**: SHA-256 of the extracted file = SHA-256 of `base.apk` read from inside the container = `4b73c916…b8ed63` (both computed this run).

**These two census files do not contradict each other.** `census.json` is the analyzer correctly reporting that a **multi-APK bundle container** (APKMirror's `.apkm` format, `apkm_version: 5` per `info.json`) is not itself an installable APK: it is a distribution zip *around* 21 APKs. `census-base.json` is the analyzer correctly reporting the **base split** extracted from that same container. Same download, two different objects; the PairIP facts live in the base split (and, for native libraries, potentially in the ABI splits — §7).

### 2.4 What was NOT measured (in this study)

- The **ABI split APKs** (`split_config.arm64_v8a.apk`, `split_config.x86.apk`, `split_config.x86_64.apk`) were **not analyzed**. Their contents — including whether `libpairipcore.so` ships in any of them — are **unmeasured** and are not asserted either way in this document (§7, Limitations).
- The **identities of the 20 stub methods** are not recoverable from the census output: `dexStats` records counts only (`dexscan.py:90-107`), and a pure VM stub (one whose only PairIP reference is to `VMRunner.invoke`/`executeVM`) does not appear in `integrityEntryPoints`, whose targets come from non-VM `com.pairip.*` references (`dexscan.py:45-60`, `stubs.py:20-24`).
- No runtime observation of any kind was performed (ROE §1: static analysis of the distributed artifact only).

---

## 3. From public research (cited)

All items in this section are cited to `docs/01-pairip-dossier.md` (rev. 3, 2026-10-22), which carries per-claim provenance grades and its own source list (§9 there). Nothing here was re-measured in this study.

- **What PairIP is.** The community name for Google Play's opt-in, partner-gated "automatic integrity protection," injected at Play-signing time; Google's documentation never uses the name (dossier §1). Its distinguishing mechanism is native-level code virtualization: selected method bodies replaced by `VMRunner.invoke(...)` calls executing per-method bytecode inside `libpairipcore.so`'s interpreter (dossier §1, §2.1).
- **Layered defense.** (1) Java `SignatureCheck.verifyIntegrity` at the earliest startup point, crashing on signature mismatch; (2) native `protections_main` with anti-debugging (raw AArch64 syscalls), `/proc/self/maps`+`status` scanning, frida-server detection, system-property sweeps; (3) `com.pairip.licensecheck` with Play-redirect and silent `System.exit(0)` paths (dossier §1, §3.2–§3.4). Google documents tamper response as stopping the app "predominantly by crashing the app" (dossier §3.1).
- **Per-build opcode randomization** defeats portable VM decoding; no complete public devirtualizer exists; public tooling stalled at ≈86 % *format* coverage on one target binary and semantics for 14 of ~99 opcodes in the shipped table (dossier §2.4, §2.7, §6). Tampering with VM bytecode redirects down a fallback path (FNV-family hash chain) rather than crashing cleanly (dossier §2.6).
- **Vendor tiers:** installer check, anti-tamper, partner-gated device check; a select-partner EAP offers *custom method protection* of developer-selected methods (`@PlayAutomaticIntegrityProtection`), i.e., the vendor documents method-level protection but not virtualization — the VM mechanism is third-party-established (dossier §3.1, §3.5).
- **Grindr chronology.** Hookable at 25.20.0 (Nov 2025); GrindrPlus announced probable EOL 2026-03-21 attributing it to "advanced native-backed VMProtect-esque protections … no bypass publicly available"; EOL commit authored 2026-04-04, pushed at archival 2026-05-18; server-side cutoff of 25.20.0 ~2026-05-07; latest Grindr 26.21.0 listed on APKMirror 2026-10-16. The exact first protected version was, before this study, **unmeasured** (dossier §4).
- **Why GrindrPlus died — the dossier's adjudicated position.** Best-supported explanation is loss of hookable Java surface (virtualization), consistent with the maintainer's attribution — but *not demonstrated method-by-method*, and Java hooking demonstrably still works on the non-virtualized `com.pairip` license classes (`ahmedmani/pairipfix` LSPosed module defeats exactly the license dialog; dossier §4, §5 Tier 1).
- **Bypass landscape (descriptive only).** Tier 1 license/integrity bypasses keep being re-published (partial); Tier 2 VM analysis stalled 2025; Tier 3 (2026, most active) neutralizes `VMRunner` entry points and restores extracted methods per-app — an approach that produces unprotected builds but *cannot revive a hook client*, since it destroys rather than exercises the Java surface (dossier §5).
- **Open questions carried over** that this study partially answers: which Grindr versions ship PairIP and how heavily (dossier §8.1.9 — answered for 26.21.0 base split in §2.2); ABI coverage of `libpairipcore.so` (dossier §8.1.8 — **still open**, §7).

---

## 4. Hookability verdict — client-side modding of Grindr 26.21.0

**Bottom line: the current build carries the full PairIP integrity/licensing wrapper but — in the base split — virtually no method virtualization. Runtime hooking (a GrindrPlus-style module on an unmodified, Play-installed APK) is structurally plausible again; static repackaging remains protected; the decisive unknown is the native layer, which this census could not see.**

Weighing both facts, as measured:

**Fact A — PairIP is structurally present [measured, §2.2].** The manifest application is the PairIP wrapper; `SignatureCheck.verifyIntegrity` and `LicenseClient.checkLicense` are wired into `attachBaseContext`; the licensing layer also self-starts from `LicenseContentProvider.onCreate`; `StartupLauncher.launch` is invoked from the `<clinit>` of both framework component factories and an obfuscated app class; `VMRunner`/`VmDecryptor` are present with a `System.loadLibrary("pairipcore")` request in `VMRunner.<clinit>`.

**Fact B — the virtualization footprint in the base split is ~0 % [measured, §2.2].** 20 of 422,621 method entries (0.00473 %) outside `com.pairip.*` delegate to the VM runner. The 46 PairIP classes are themselves ordinary Java with concrete call graphs — i.e., the protection runtime is present but not self-virtualized, exactly as the analyzer's design expects (`stubs.py:194-204`).

Consequences by modding approach (verdict, then its basis):

1. **Static repackaging / re-signing: not feasible without defeating the integrity layer.** Any modified, re-signed APK changes the signature digest that `SignatureCheck` computes; public research documents the response as an uncaught `SignatureTamperedException` crash (dossier §3.2), and the wrapper owns the manifest application entry [measured] so it cannot be simply skipped past. This is the same wall the Tier-1/Tier-3 public tools work around by patching the checks themselves (dossier §5) — an arms race this study, per ROE, does not extend.
2. **Runtime hooking on an unmodified APK (the GrindrPlus model): structurally plausible on this build — with three explicit caveats.** The measured ~0 % stub rate means the app's Java logic overwhelmingly retains real bodies for Xposed/LSPosed-style hooks to intercept; that is the same property that made ≤25.20.0 hookable, and it is *measured present* in 26.21.0's base split. Public evidence already shows the Java-side license layer is hookable (pairipfix; dossier §5). Caveats, in order of severity:
   - **The native layer is unmeasured.** `protections_main`-style environment checks (anti-debug, frida detection, `/proc` scanning — dossier §3.3) live in `libpairipcore.so`, which is **not in the base split** [measured] and whose presence in the ABI splits was **not analyzed** (§7). A hook client runs in exactly the environment those checks probe; nothing in this census can rule that risk in or out. Note the tension this creates and leave it unresolved: `VMRunner.<clinit>` requests a library [measured] that this split does not ship [measured], and where it ships — if anywhere — is unmeasured.
   - **The 20 stubs' identities are unknown.** If the specific methods a mod needs (e.g., feature gating, update enforcement) are among the 20, those hooks die exactly as the GrindrPlus maintainer described; the census counts them but does not name them (§2.4). Identifying them is the highest-value next measurement (§8).
   - **The heuristic has documented blind spots** — renamed PairIP classes, reflection-based delegation, and native-only virtualization are undetected, and "a low stubPct does not prove absence of virtualization" (quoted in full in §7).
3. **Interpretation for the program's central historical question.** The maintainer's attribution — virtualization killed GrindrPlus (dossier §4) — was formed against 26.3/26.4-era builds and without an APK census (the dossier's own biggest verification gap, §1 there). This study's measurement **rules out blanket virtualization of the 26.21.0 base split**. What remains consistent with both the historical record and this measurement is *targeted* virtualization (20 methods may be exactly the ones that mattered), the integrity/licensing wrapper's presence, native-layer pressure, and maintenance economics. Distinguishing among these is possible but requires the §8 follow-ups; this study does not adjudicate it.

**Confidence:** HIGH that the structural facts and the 20/422,621 count describe the base split (reproduced identically this run, complete coverage, zero scan errors); MEDIUM on the hookability verdict itself, because it extrapolates from a static, base-split-only view past one unexamined native layer and one unnamed set of 20 methods.

---

## 5. Reconciliation note: this build's `VMRunner` vs. the published chain

Public research describes `invoke()` → `readByteCode()` (assets blob) → native `executeVM` (dossier §2.1). The measured call graph of this build instead shows `invoke` → `getVmByteCode` → `VmDecryptor.decrypt`, with APK-path sourcing (`openBaseApk`, `getApkPathFromResource`), and no recorded `executeVM` target (§2.2) — and no `assets/*.vmcode` entries in the base split (§2.2). The dossier already documents that VM internals vary per build (opcode randomization, dossier §2.4) and that per-team samples are unattributed to apps (dossier §8.1.11), so the difference is recorded here as a per-build observation. It is **not** evidence about where this build's VM bytecode lives (unmeasured) nor about protection strength.

---

## 6. What the two census files are — one-line resolution

`census-base.json` = PairIP census of the **installable base APK** (extracted from the bundle; byte-identical to the container's `base.apk`). `census.json` = the same tool correctly reporting that APKMirror's 114 MB download is a **bundle container** (`.apkm` v5 zip of 21 APKs + metadata), which has no root dex and no manifest of its own — an object type the analyzer, by design, reads as "no PairIP markers at zip root." Neither file is wrong; they describe different objects, and only the base split carries the protection facts.

---

## 7. Limitations

1. **Static analysis only.** No APK was installed, run, hooked, or dynamically observed; every finding is from reading bytes on disk (ROE §1). All statements about *behavior* (crash on tamper, license prompts, anti-frida activity) are [sourced] to public research, not observed here.
2. **The ABI split APKs were NOT analyzed.** `split_config.arm64_v8a.apk`, `split_config.x86.apk`, and `split_config.x86_64.apk` were never opened. **Whether `libpairipcore.so` is present in any ABI split is unmeasured and must not be asserted either way.** The only related measurements are: the base split contains no native libraries at all (`nativeLibs` = `{}`), and `VMRunner.<clinit>` requests the library. The container's *entry names* show three ABI splits exist (§2.3); that is metadata, not content.
3. **The stub heuristic is best-effort, with the tool's own documented limits.** Quoted verbatim from `census-base.json` `notes[3]` (identical text at `census.py:42-49`): *"Heuristic limits (best effort): (1) a method is only inspected when androguard's linear-sweep disassembler can decode its code item -- undecodable methods are counted as scan errors, not as non-stubs; (2) renamed/repackaged com.pairip classes, reflection-based delegation, or native-only virtualization are NOT detected; (3) a low stubPct does not prove absence of virtualization; (4) stubPct counts all defined method entries (including abstract/native) in totalMethods."* Point (3) is the load-bearing caveat for this study's Fact B. This run reported **zero** scan errors and zero skipped dex files (no such notes appended, §2.2), so within the heuristic's coverage the count is complete — but coverage ≠ correctness against its blind spots.
4. **The bundle container is not itself an installable APK.** `census.json`'s empty result describes the container, not Grindr; treating it as "Grindr 26.21.0 has no PairIP" would be a category error (§2.3, §6). Conversely, the base-split census alone does not describe what a user's device receives from Play: a real install composes base + device-matching splits.
5. **Stub identities are not recorded** by the census output format (§2.4), so the verdict's "which 20 methods" question is open.
6. **Version skew and provenance.** The census describes exactly one build (26.21.0 / 189896) from one mirror acquisition (APKMirror, 2026-10-22; mirror posting dated 2026-10-15). APKMirror is a third-party mirror, not Google Play; whether the mirrored bundle is byte-identical to what Play serves is unverifiable from here. No claim is made about any other Grindr version (the onset question — which versions between 25.20.0 and 26.21.0 first carried PairIP — remains open per dossier §4).
7. **The reproduction environment differs from the original run** in nothing material that was recorded (same tool commit lineage, same androguard 4.1.4), but the original production commands were reconstructed from the README's documented form plus the `apk` paths recorded inside the census JSONs; the JSONs do not embed the full command line. My identical re-runs (§2.1) are the evidence the reconstruction is faithful.

---

## 8. Highest-value next measurements

1. **Name the 20 stubs** — a small extension to `dexscan.py` recording stub class/method identities would answer whether the methods mods historically needed are virtualized; that single fact would harden the §4 verdict from MEDIUM toward either direction.
2. **Census the ABI splits** — run the same tool over `split_config.arm64_v8a.apk` etc. to measure `libpairipcore.so` presence and size per ABI (closing dossier §8.1.8 for this build).
3. **Version sweep** — the same census across 25.20.0 (known hookable), 26.0–26.4 (onset bracket), and later 26.x would pin the first protected version and whether the stub count has trended (dossier §4, §8.1.9).

These stay within ROE §1 (static analysis of publicly distributed artifacts); none produces bypass capability.

---

## Sources

- **Measured artifacts (this study):** `pairip-research/samples/apk/grindr-current.apk` (APKMirror bundle container, 114,511,937 bytes, SHA-256 `22c7743951b49a0cf6d11f7f05b517c1bdd8c8e6339441dccdc06a5a46ae751c`) and `pairip-research/samples/apk/grindr-current-base.apk` (base split extracted from that container, 72,037,281 bytes, SHA-256 `4b73c916b9b85c672070caebe859cda010c90f0df9e098e542cc3c1113b8ed63`), both acquired from APKMirror on 2026-10-22; container metadata from its `info.json` (read via Python `zipfile`).
- **Analyzer and its output:** `tools/pairip-audit/run_audit.py` (pure Python; Python 3.14.6, androguard 4.1.4), producing `samples/out/census-base.json` and `samples/out/census.json` — both reproduced identically this run (§2.1). Analyzer test suite: `python -m pytest pairip-research/tools/pairip-audit/tests -q` → 81 passed (this session).
- **Public-research context:** `docs/01-pairip-dossier.md` (2026-10-22) — every [sourced] claim in §3 traces to a named dossier section; the dossier carries per-claim provenance grades and its own numbered source list (§9 there).
- **Release chronology / acquisition channel:** APKMirror Grindr listing (release 26.21.0 posted 2026-10-15, listed through 2026-10-16; dossier source 29) — used as the APK source only. Third-party mirror, not Google Play; Play-identity of the bytes is unverifiable from here (§7.6).

---

*Evidence chain: `samples/out/census-base.json`, `samples/out/census.json` (both reproduced identically this run); zip-level and hash checks executed this session with Python 3.14.6 `zipfile`/`hashlib`; analyzer code at `tools/pairip-audit/` (repo-relative); public-research context from `docs/01-pairip-dossier.md` rev. 3. Analyzer suite: 81/81 tests passed this session.*
