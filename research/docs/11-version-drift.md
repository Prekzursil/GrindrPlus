# Version Drift — the PairIP Footprint Across the Grindr Lineage (25.19.0 → 26.21.0)

**Date:** 2026-10-24
**Deliverable:** `docs/11` of the PairIP/GrindrPlus research program (charter in repo `README.md`; ROE in `ROE.md`). Extends `docs/05` (splits census of one build) backwards and forwards in time along the release lineage.
**Question answered:** Is the PairIP footprint in Grindr growing, flat, or shrinking across the lineage — and did anything structural change (classes, entry points, native libraries) between 25.19.0, 25.21.1 (the version the GrindrPlus module last claimed to support), 26.8.2, and the current 26.21.0?
**Method:** live census runs this session of the repo analyzer `tools/pairip-audit/run_audit.py` (androguard 4.1.4) against the three historical base APKs in `samples/apk/versions/`, plus one stdlib `zipfile`+`hashlib` pass over all three `.apkm` bundles for native-library presence and hashes. The 26.21.0 column reads `samples/out/census-base.json` / `census-base-named.json` (same APK, both runs identical on every shared field) with native hashes as already published in `docs/05`/`docs/10`. Every claim is **[measured]** (command recorded in §7), **[sourced]** (cited to a file read this session), or **[interpretation]**.

---

## 0. Provenance of this run — the track's failed censuses were re-run, successfully

The task record supplied to this doc listed three census runs — 25.21.1, 25.19.0, 26.8.2 — each with `exitCode: 1`, and an empty acquisition-failure list. The exit-1 meaning per the analyzer CLI is "the APK could not be opened or read" (`tools/pairip-audit/run_audit.py:11`). Yet all three artifacts were already on disk and zip-valid (`samples/apk/versions/`, validated in the acquisition run per `samples/apk/versions/SOURCES.txt:16-19`), so the failures were **analyzer-run failures, not acquisition failures** — the missing-cells set the task feared is empty.

This session re-ran the same analyzer on the same on-disk artifacts (§7): **all three exited 0** in ~2 minutes each (`samples/out/census-25.19.0.log`, `census-25.21.1.log`, `census-26.8.2.log`). The original exit-1 cause is not recoverable from the record — the only candidate artifact, repo-root `err.log`, is truncated androguard DEBUG noise from 07:26:17 with no traceback — and it did not reproduce. Everything below comes from the live re-runs.

## 1. The version-ordered table **[measured]**

Grindr lineage only; every row is a base APK census. Native libraries never live in the base APK (`nativeLibs: {}` in all four censuses — they ship in the ABI splits), so the native column reads the bundles: the `.apkm` files for 25.19.0/25.21.1/26.8.2 (this session, §7b), the already-published split hashes for 26.21.0 (`docs/05-splits-census.md:41-43`, byte-verified in `docs/10 §1`).

| Version | versionCode | pairipDetected | `com.pairip` classes | Total methods | VM stubs (unrounded %) | Integrity entry points | `libpairipcore.so` in bundle |
|---|---|---|---|---|---|---|---|
| 25.19.0 | 146528 | **false** | 0 | 485,564 | 0 (0%) | 0 | none — absent from all 4 ABI splits |
| 25.21.1 | 148541 | **false** | 0 | 527,880 | 0 (0%) | 0 | none — absent from all 4 ABI splits |
| 26.8.2 | 162647 | **true** | 40 (11 core + 29 licensecheck) | 539,087 | 20 (0.0037%) | 92 (90 pairip-call, 1 manifest-app, 1 load-pairipcore) | **4 ABIs** — hashes §4 |
| 26.21.0 | 189896 | **true** | 46 (11 core + 35 licensecheck) | 422,621 | 20 (0.0047%) | 110 (108 pairip-call, 1 manifest-app, 1 load-pairipcore) | **3 ABIs** — hashes `docs/05:41-43` |

Sources per cell (identical layout in both 25.x files): `census-25.19.0.json` and `census-25.21.1.json` at `:3-5` (version, versionCode, pairipDetected), `:9` (empty `pairipClasses`), `:11-12` (totalMethods/stubMethods), `:79` (empty `integrityEntryPoints`); `census-26.8.2.json:3-8,52-53,124,227` (92 `"kind"` lines); `census-base-named.json:3-8,58-59,130,233` (110 `"kind"` lines). `vmcodeAssets: []` in all four — the no-`.vmcode`-assets deployment drift noted in `docs/10 §4.2` holds across the entire protected era, not just the current build.

## 2. The 25.21.1 → 26.21.0 span explicitly

**25.21.1 — the version the GrindrPlus module pinned and last supported — carries zero PairIP markers of any kind [measured]:** no `com.pairip.*` class in any of its 10 dex files, zero stub methods, zero integrity entry points, no `.vmcode` asset, and no `libpairipcore.so` in any of the four ABI splits of its `.apkm` (§7b). **[sourced nuance]** per the corpus doc the module's *compile-time* pin was 26.0.1/149389, with 25.21.1 (148541) being the update-spoof value in `version.json` (`README.md:80`, `docs/06 §7`); either way, every version the module ever targeted at or below its final spoof is PairIP-free, and the compile pin itself sits *inside* the introduction bracket below, unmeasured.

**26.21.0 — the current build — carries the full kit [measured]:** 46 classes, 20 stubs, 110 entry points, the manifest `<application>` bound to `com.pairip.application.Application` (`census-base.json:129-134`), and `libpairipcore.so` in every ABI the app still ships.

Net: **the entire observable PairIP footprint postdates the module's last supported version.** Any revival of the module targeting anything ≥ the 26.x cutover faces a protection stack its 25.x-era hooks were never written against.

**The introduction bracket narrows [measured + sourced].** `docs/06 §8` closed with "which build first shipped PairIP remains bracketed, not identified" — bracketed then only by maintainer statements (announcement 2026-03-21 postdating a 26.4.2 sighting, `README.md:101`, `docs/06 §2.1`). Static measurement now bounds it: first protected build is somewhere in **versionCode (148541, 162647]** — after 25.21.1 (bot-tracked 2025-12-26, `docs/06 §2.1`), by 26.8.2. The 2026-03-21 "advanced native-backed VMProtect-esque protections … probably the end" announcement (msg 197, `docs/06 §4`) falls inside that window, consistent with a 26.4.x–26.5.x-era landing, but only the code-order bracket is asserted here. A single further census of 26.0.1 (the module's compile pin) would cut the bracket roughly in half; that APK was not fetched.

## 3. Trajectory: step-function introduction, then licensing-surface growth

**[interpretation from measured cells]** The footprint's history is: **flat zero → step to the complete kit → modest, licensing-driven growth** — against an app that is simultaneously *shrinking*.

- **25.19.0 → 25.21.1: flat at zero.** Two clean builds, 12 and 10 dex respectively, no marker in any category.
- **25.21.1 → 26.8.2: step introduction — the kit arrived whole.** Between the two bracketing builds — versionCode 148541 → 162647, a wide span with every intermediate release unmeasured, so only the step's completeness by 26.8.2 is measured, not its temporal sharpness — the footprint goes 0 → 40 classes, and not a partial core: all 11 non-licensecheck classes of the current build (`InitContextProvider`, `SignatureCheck`(+exception), `StartupLauncher`, `Utils`(+inner), `VMRunner`(+2 inners), `VmDecryptor`, `application.Application`) are already present, as is a 29-class licensecheck family, 20 stubs, and 4-ABI native coverage. The bootstrap chain is already in its current shape: manifest application = `com.pairip.application.Application`; `VMRunner.<clinit>` → `loadLibrary("pairipcore")`; `<clinit>` hooks on `android.app.AppComponentFactory`, `androidx.core.app.CoreComponentFactory` **and one obfuscated holder class** calling `StartupLauncher.launch` (`census-26.8.2.json` `integrityEntryPoints`; the same three-hook shape is present in both 26.x builds per the §7 item-3 entry-point set-diff — framework hooks unchanged, holder renamed, §5).
- **26.8.2 → 26.21.0: growing, but only on the licensing surface.** Core kit unchanged (same 11 classes). The +6 classes are all licensecheck: `TrialClient` (new) and `LicenseClient$$ExternalSyntheticLambda10–14` (5 new lambdas); licensecheck grows 29 → 35. Entry points 92 → 110; all 18 added/lost entries are licensecheck-or-bootstrap bookkeeping (§5). The stub count holds at exactly 20 while total methods collapse 539,087 → 422,621 (−21.6%), so stub *density* rises 0.0037% → 0.0047%.
- **Native ABI coverage shrinks for app reasons:** 26.8.2 ships `libpairipcore.so` for 4 ABIs; 26.21.0 for 3 — because the app dropped `armeabi-v7a` entirely between the builds (no such split exists in the 26.21.0 bundle, §7b), while both 25.x bundles still shipped one.

**Verdict:** growing — but the growth since introduction is confined to the Play licensing layer (`TrialClient`, trial-stop machinery `stopTrial`/`handleTrialEnd`, extra lambdas, and a `connectToLicensingService` → `bindToLicensingService` rename). The protection core (VM runner, decryptor, signature check, bootstrap) has been structurally frozen since at least 26.8.2.

## 4. Native library drift — seven distinct binaries, sizes all growing **[measured]**

SHA-256 of every `libpairipcore.so` shipped across the lineage (25.x rows: absent; §7b for 26.8.2, `docs/05:41-43` for 26.21.0):

| ABI | 26.8.2 size / SHA-256 | 26.21.0 size / SHA-256 | Δ size |
|---|---|---|---|
| arm64-v8a | 576,664 / `a020759ff9dec2a56dc060ae4e35aa064f3eff6c2f138f9eefef926532ab6543` | 608,896 / `b20ee5bca05328b794744ab082c758ec2e0d298c5447e1a6415094ecc6987589` | +5.6% |
| armeabi-v7a | 566,640 / `d60cab41dded58a7ed0debc2387fcb0a5e9514eb1bf8f6214e32f898e0e66c6b` | *(ABI dropped from app)* | — |
| x86 | 599,316 / `bf8f1dad70dfec1a0f5caee2308ef1a96a6c30a544406a27a52f2d7147188f7f` | 697,616 / `46b814fb40c6e8b036c0a66eda72d6cac164434f40520e7a42c2a2c06bee76cc` | +16.4% |
| x86_64 | 607,808 / `68abcb16053b6756feab3d5a6197eb638624cf567ca7a7f41de3e139397b0257` | 624,184 / `a9c54f7a2e2a92d385354415bd46b2935904fb9235226a62864db6ea418fbba6` | +2.7% |

Seven distinct hashes for seven shipped binaries. **[interpretation]** That is consistent with the dossier's per-build randomized opcode mapping (`docs/01:61`, via `docs/05 §3.3`) — and equally consistent with ordinary code evolution between the two protected builds measured here (n = 2: 26.8.2 and 26.21.0); the hashes establish that each measured binary is individually built, not that every protected release ships a freshly rebuilt VM. All three common ABIs grew between 26.8.2 and 26.21.0.

## 5. What actually changed inside the protection, 26.8.2 → 26.21.0 **[measured]**

- **Stub set churns 60% while the count stays 20.** Only 8 of 20 stubs persist; 12 leave and 12 arrive. Stable: the two Agora `BTHeadsetBroadcastReceiver`s, `mbridge LoadingActivity$1`, `facebook AuthenticationTokenManager$…Receiver`, `fyber storepromo.ui.b`, both `gms.ads…util.zzcf/zzp`, `gms OfflinePingSender.doWork`. Gone in 26.21.0 (12): mostly `gms.internal.ads`/`ironsource`/`bidmachine`/`play-core` receivers plus two `androidx.work` entries. New in 26.21.0 (12): braze/applovin/inmobi/pubnative/agora-utility receivers and three R8-short names (`nua0.doInBackground`, `obd0/seq.onReceive`). Every stub in both builds is the same family — `onReceive`/`doWork`/`doInBackground` in ad/network SDK classes — matching `docs/09`'s characterization of the 26.21.0 set (one stub per class, uniform 11–12-instruction body, per-method VM token). **[interpretation]** the transformer re-selects targets per release; the *selection policy* (broadcast receivers and workers) is the stable trait, not the targets.
- **Licensing machinery grew** (§3): `TrialClient` + trial-stop path (`stopTrial`, `handleTrialEnd`, `lambda$stopTrial$0`) exist only in 26.21.0; `connectToLicensingService` (26.8.2) is renamed `bindToLicensingService` (26.21.0).
- **Bootstrap holder renamed:** the obfuscated `<clinit>`→`StartupLauncher.launch` hook moved from `ta.o0` (26.8.2) to `qai` (26.21.0); the two framework hooks (`android.app.AppComponentFactory`, `androidx.core.app.CoreComponentFactory` `<clinit>`) are unchanged. **[interpretation]** R8 re-minification churn, not a redesign — the same three-hook shape survives.

## 6. Census corpus read for this doc, and out-of-lineage files

Every `samples/out/census-*.json` was read: the four lineage rows above; `census-split-{arm64_v8a,x86,x86_64,xxhdpi}.json` (26.21.0 splits, already covered by `docs/05`); `census.json` (the whole-bundle misparse of `grindr-current.apk` — empty version, `pairipDetected: false`; superseded by `census-base.json`, excluded); and the concurrent baseline-track files `census-app-{efteling-latest,paseo-0.7.2,paseo-latest,vpnify-2.1.8}.json` (other apps, out of lineage). One lineage-relevant aside from the baselines **[measured]**: `vpnify-2.1.8` ships a **9-class PairIP config** — the core kit without `InitContextProvider`, `VmDecryptor`, and the entire licensecheck family — yet still 20 stubs and a `load-pairipcore` entry point. The licensecheck layer Grindr grew between 26.8.2 and 26.21.0 is a per-app option, not part of the mandatory core.

## 7. Run record (this session; commands from `pairip-research/`)

1. **Census re-runs (§0, §1)** —
   `python tools/pairip-audit/run_audit.py samples/apk/versions/25.21.1-base.apk --out samples/out/census-25.21.1.json` → exit 0, stdout `pairipDetected=False pairipClasses=0 stubs=0/527880`;
   same for `25.19.0-base.apk` → exit 0, `pairipDetected=False pairipClasses=0 stubs=0/485564`;
   same for `26.8.2-base.apk` → exit 0, `pairipDetected=True pairipClasses=40 stubs=20/539087` (logs: `samples/out/census-<v>.log`).
2. **Bundle native scan + hashes (§1, §4)** — one Python `zipfile`+`hashlib` pass over `25.19.0.apkm`, `25.21.1.apkm`, `26.8.2.apkm` (every split APK's `lib/` entries; `libpairipcore.so` hashed where present) and over `grindr-current.apk`'s 21 split APKs (armeabi-v7a absence in 26.21.0).
3. **Cross-version diffs (§5)** — `json.load` set-diffs of `pairipClasses`, `stubMethodsList`, `integrityEntryPoints` between `census-26.8.2.json` and `census-base-named.json`; kind census via line count of `"kind"` (92 / 110).

**Limitations.** Detection is name-based (analyzer notes, `census-25.21.1.json:84`): a renamed/repackaged PairIP in the 25.x builds would not be seen — though absence of any `libpairipcore.so` in any split of either bundle corroborates the DEX-side zero. The 26.8.2 `.so` files were hashed, not analyzed (no symbol/section inventory as `docs/10` did for 26.21.0). 26.0.1 was not fetched, so the introduction bracket is a code range, not a build identity. The original track exit-1s remain unexplained (§0).
