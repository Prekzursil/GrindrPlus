# Cross-App PairIP Baseline — Grindr's Footprint vs Five Other Play Apps

**Date:** 2026-10-24
**Deliverable:** `docs/12` of the PairIP/GrindrPlus research program (charter in repo README; ROE in `ROE.md`). Extends the `docs/00`–`docs/10`, `docs/14` series. Takes the single-app measurements of `docs/05` (Grindr's splits) and `docs/09` (Grindr's 20 stubs) and places them against a five-app baseline census.
**Question answered:** Is Grindr's PairIP footprint — 20 stub methods out of 422,621 (0.0047 %) — *typical*, *light*, or *heavy* compared with other PairIP-protected Play apps? Does any baseline app ship `assets/*.vmcode` VM bytecode (Grindr recorded none)?
**Method:** this doc's author executed the tested analyzer (`tools/pairip-audit/run_audit.py`, androguard 4.1.4, Python 3.14.6) over each of the five baseline base APKs plus one config split — **six runs, all exit code 0** (§7 run record) — then read every output JSON in full. Complementary stdlib `zipfile` passes (this session) enumerated `lib/` entries in every config split of every XAPK and counted random-named top-level assets. Every claim below is **[measured]** (produced this session; command in §7), **[sourced]** (cited to a census JSON or an earlier doc), or **[interpretation]** (labeled as such).

**Provenance note on the task record [measured]:** the census list this doc was handed recorded `exitCode: 1` for all five apps, and no `census-app-*.json` existed in `samples/out/` at session start (verified by `find` — only `census-base*.json`, `census-split-*.json`, `census.json` were present). Per `run_audit.py`'s contract (`run_audit.py:9-12`), exit 1 means *"the APK could not be opened or read"* — e.g. running against an un-extracted `.xapk`. Those recorded runs produced no output; this doc re-ran every census against the already-extracted base APKs (all succeeded, exit 0), and those runs are the sole source of the baseline columns below.

**Path convention:** paths relative to the workspace root; `samples/` is gitignored (local-only by policy), matching `docs/05`/`docs/09`.

---

## 1. Inputs **[measured + sourced]**

| App | package / versionCode | Artifact censused | Census output |
|---|---|---|---|
| Grindr 26.21.0 | `com.grindrapp.dating` / 189896 | `samples/apk/grindr-current-base.apk` | `samples/out/census-base-named.json` (pre-existing run, re-read this session; identical `dexStats`/`pairipClasses` to legacy `census-base.json`) |
| VPNify 2.1.8 | `com.vpn.free.hotspot.secure.vpnify` / 218000 | `samples/apk/baseline/vpnify-2.1.8-base.apk` | `samples/out/census-app-vpnify-2.1.8.json` (this session) |
| Efteling 5.27.0 | `nl.efteling.android` / 10026426 | `samples/apk/baseline/efteling-latest-base.apk` | `samples/out/census-app-efteling-latest.json` (this session) |
| Paseo 0.12.0 | `sh.paseo` / 12000 | `samples/apk/baseline/paseo-latest-base.apk` | `samples/out/census-app-paseo-latest.json` (this session) |
| Paseo 0.7.2 | `sh.paseo` / 7002 | `samples/apk/baseline/paseo-0.7.2-base.apk` | `samples/out/census-app-paseo-0.7.2.json` (this session) |
| VPNify 2.3.0 (**negative control**) | `com.vpn.free.hotspot.secure.vpnify` / 2300002 | `samples/apk/baseline/vpnify-latest-base.apk` | `samples/out/census-app-vpnify-latest.json` (this session) |
| VPNify 2.1.8 — ABI split | same | `samples/apk/baseline/vpnify-218-extract/config.armeabi_v7a.apk` | `samples/out/census-app-vpnify-2.1.8-config-armeabi_v7a.json` (this session) |

App roles (VPNify 2.1.8 "FULL PairIP VM layer"; Efteling/Paseo "PairIP license layer"; Paseo 0.7.2 the exact Play version in getpaseo/paseo issue #4417's logcat; VPNify 2.3.0 negative control) come from the task record, not from independent verification this session. VPNify 2.1.8's VM role is independently corroborated by the measurements below (VMRunner classes, stubs, `libpairipcore.so`).

## 2. The census table **[measured]**

All cells read from the census JSONs named in §1 (fields `versionName`, `versionCode`, `pairipDetected`, `pairipClasses`, `dexStats.totalMethods`, `dexStats.stubMethods`, `dexStats.stubPct`, `vmcodeAssets`; "dex classes" = sum of `dexStats.perDex[].classes`, recomputed this session — the census has no total-classes field).

| App | version | pairipDetected | pairip classes | dex classes | totalMethods | stubs | stubPct (census / exact) | vmcode assets |
|---|---|---|---|---|---|---|---|---|
| **Grindr** | 26.21.0 (189896) | **true** | 46 | 76,167 | 422,621 | **20** | 0.0 / **0.00473 %** | `[]` |
| VPNify 2.1.8 | 2.1.8 (218000) | true | 9 | 25,650 | 124,227 | **20** | 0.02 / **0.01610 %** | `[]` |
| Efteling 5.27.0 | 5.27.0 (10026426) | true | 36 | 40,600 | 228,443 | 0 | 0.0 / 0 % | `[]` |
| Paseo 0.12.0 | 0.12.0 (12000) | true | 36 | 43,636 | 271,107 | 0 | 0.0 / 0 % | `[]` |
| Paseo 0.7.2 | 0.7.2 (7002) | true | 35 | 42,916 | 265,937 | 0 | 0.0 / 0 % | `[]` |
| VPNify 2.3.0 *(neg. control)* | 2.3.0 (2300002) | **false** | 0 | 25,812 | 119,275 | 0 | 0.0 / 0 % | `[]` |

Supporting rows: VPNify 2.1.8 `config.armeabi_v7a.apk` — `pairipDetected: true` with **0 dex, 0 methods**, detection carried entirely by `pairipNativeLibs: {"armeabi-v7a": ["libpairipcore.so"]}`. Grindr's own `census-base-named.json:6-7` records `nativeLibs: {}` / `pairipNativeLibs: {}` for the *base* split; its `libpairipcore.so` ships in all three ABI splits (`docs/05:37-43`).

No census in this table reported scan errors, unreadable DEX, or a truncated stub list (no non-boilerplate `notes` entries in any output — checked this session), so the stub counts are complete under the heuristic, not cap-limited.

## 3. What the baseline shows beyond the table **[measured]**

**Three integration profiles, not one.** Composition of `pairipClasses` per app (recomputed this session):

| Profile | Apps | Java-side layer | VM stubs | `libpairipcore.so` |
|---|---|---|---|---|
| License-only | Efteling 5.27.0, Paseo 0.12.0 & 0.7.2 | `com.pairip.licensecheck.*` (34–35 classes) + `application.Application`; **no** VMRunner/SignatureCheck/VmDecryptor | 0 | **none** — absent from base *and* every config split (42 / 33 / 31 lib entries enumerated, zero pairip) |
| Integrity+VM (no license client) | VPNify 2.1.8 | 9 classes: SignatureCheck×2, StartupLauncher, Utils×2, **VMRunner×3**, application.Application; zero `licensecheck` | 20 | **yes** — `lib/armeabi-v7a/libpairipcore.so` in its config split |
| License + integrity + VM | Grindr 26.21.0 | 35 `licensecheck` + 11 (VPNify's 9 minus nothing, plus `InitContextProvider`, `VmDecryptor`) | 20 | yes — all three ABI splits (`docs/05:37`) |

Grindr's non-license 11 classes are exactly VPNify 2.1.8's 9 **plus** `InitContextProvider` and `VmDecryptor` — the same Java-side VM/integrity kit, one generation apart. The two Paseo versions are near-identical despite the version-number jump (0.7.2 → 0.12.0; 35 → 36 classes; no release date was established for either version this session, so only version-order separation is claimed), so the license-only profile is stable across releases for at least one vendor.

**The negative control is clean on both base and split [measured].** VPNify 2.3.0 (`pairipDetected: false`, 0 pairip classes) also has no pairip entry in its `config.arm64_v8a.apk` (7 lib entries enumerated) — and no random-named assets (below). Same publisher dropped PairIP entirely between 2.1.8 and 2.3.0.

**VM stubs: same count, same shape, same kind of victim code [measured].** VPNify 2.1.8's 20 stubs (read in full from `census-app-vpnify-2.1.8.json` `stubMethodsList`) are, like Grindr's 20 (`docs/09:212`), all third-party ad/analytics SDK event callbacks — 13 `onReceive` / 4 `doInBackground` / 3 `doWork` across Google Mobile Ads, Yandex Ads, AppMetrica, Facebook SDK, and `androidx.work` — versus Grindr's 18/1/1 across ≥10 SDKs. Two stubs are *exact* class#method matches in both apps (`com.facebook.AuthenticationTokenManager$CurrentAuthenticationTokenChangedBroadcastReceiver.onReceive`; `com.google.android.gms.ads.internal.offline.buffering.OfflinePingSender.doWork`), with near-matches elsewhere (`…util.zzcl`/`zzcf`, `zzq`/`zzp`). **[interpretation]** An unrelated app from the public pairipcore-research era showing the *identical* stub count (20), the identical callback-only selection, and overlapping victim methods is strong cross-app corroboration of `docs/09:140`'s reading: the virtualized set is an **automatic batch transform applied to SDK entry callbacks**, not a curated per-app protection list — and the count 20 in both apps hints at a batch-size cap in the transform, though n=2 cannot establish that.

**VM bytecode assets: none by filename anywhere — but blobs exactly where the VM ships [measured + interpretation].** `vmcodeAssets` is `[]` for all six censuses; the tool's marker is any `assets/*` entry ending in `.vmcode` (`tools/pairip-audit/pairip_audit/assets.py:24-26`). A stdlib `zipfile` pass this session over all six base APKs, counting top-level assets named `assets/[A-Za-z0-9]{16}`:

| App | random-16 asset blobs | size range | first-16-bytes header (sample) |
|---|---|---|---|
| Grindr | **30** | 176,202–480,140 B | `004941500200000008079a4767c779b5` (`assets/2BesmkLN1gZiFJr6`) |
| VPNify 2.1.8 | **22** | 30,723–113,614 B | `4409ca60ba914f9bd01b4cb4f0d4ab28` (`assets/1MkX5lQE8Ugk9emS`) |
| Efteling / Paseo ×2 / VPNify 2.3.0 | **0** each | — | — |

The blobs appear **only** in the two apps that ship the full VM stack (VMRunner + stubs + `libpairipcore.so`), never in license-only or unprotected apps. **[interpretation]** This is consistent with — but does not prove — those blobs being the renamed/encrypted VM bytecode payload; `docs/05:175` already concluded for Grindr that "the VM payload is present but not statically enumerable by filename" because `VMRunner.getVmByteCode` reads and `VmDecryptor` decrypts at call time. Neither app uses the default `assets/data.vmcode` name the heuristic (and the public pairipcore-vm tooling, `samples/pairipcore-vm/README.md:28`) expects. No decryption was attempted this session, so blob identity remains unconfirmed.

## 4. The comparison: typical, light, or heavy? **[measured + interpretation]**

- **Against the only other VM-stack app measured (VPNify 2.1.8), Grindr is typical in absolute terms and lightest in relative terms.** Absolute stub count is *identical* (20 vs 20); Grindr's percentage is ~3.4× lower (0.00473 % vs 0.01610 %) purely because its method count is ~3.4× larger (422,621 vs 124,227). The percentage difference is a denominator effect, not a lighter deployment.
- **Against the license-only apps (3 of 5 baseline entries), Grindr is heavier by every Java-side measure**: +11 VM/integrity classes and +20 stubs over their zero, plus `libpairipcore.so` shipped in three ABI splits where they ship none anywhere. But this is a *different integration profile* (§3's license-only vs integrity+VM vs license+integrity+VM), not a different intensity of the same one — whether those profiles correspond to different commercial purchase tiers is not established by anything measured here; license-only apps carry no VM to invoke at all.
- **Net verdict:** within the population that actually ships the VM, **20 stubs / 0.005 % is the typical footprint — sparse invocation of a fully shipped VM, exactly the "integrity-first" deployment `docs/02`/`docs/05`/`docs/09` established for Grindr alone**. Grindr is neither an outlier nor a heavy user of Java-visible virtualization; it is the *largest* app carrying the *smallest observed* relative (and tied-smallest absolute) stub load. There is no baseline app where PairIP virtualizes a large share of app code — among the apps that actually ship the VM (n = 2: Grindr, VPNify 2.1.8) the observed stub count is a tied 20 (0.005–0.016 %, the spread being a denominator effect), a single observed value rather than a range; the 0-stub apps ship no VM at all and sit outside that population.
- **vmcode assets:** no app in the sample — Grindr included — has `assets/*.vmcode` by filename; the only filename-dodging candidates (the random-16 blobs) again occur only in the two VM-stack apps. So "Grindr had none recorded" is *typical*, not anomalous: the default `.vmcode` name appears to be unused in production Play builds, and the census field is effectively a negative marker everywhere it matters.

## 5. Caveats — why this baseline cannot carry distributional claims

1. **n = 5 baseline apps (+1 split), 4 distinct packages.** Every percentage above is a point observation; nothing here licenses "X % of PairIP apps…" phrasing. The two Paseo versions are one app at two times, not independent samples.
2. **Selection bias toward small apps and known PairIP users.** All five were chosen *because* PairIP use was documented or suspected (VPNify via the public pairipcore research; Paseo 0.7.2 chosen to match the issue-#4417 logcat), and all are small-to-mid apps (119k–271k methods) next to Grindr's 422k. No AAA game, no banking app, no other top-100 app is in the sample; heavy virtualization, if it exists in the wild, is most plausibly there — unmeasured.
3. **Heuristic limits (from the census's own notes, present verbatim in every output).** The stub heuristic only sees invokes of `VMRunner.invoke`/`executeVM` in disassemblable code; renamed/repackaged `com.pairip` classes, reflection-based delegation, and **native-only virtualization are not detected**; a low `stubPct` does not prove absence of virtualization; `totalMethods` includes abstract/native entries. The `vmcodeAssets` marker misses any non-`.vmcode` filename — which, per §3, is every production app measured. The license-only apps' "0 stubs" therefore means "no Java-visible VM invocation," trivially true since they do not ship VMRunner at all.
4. **Single-version snapshots.** VPNify dropped PairIP entirely between 2.1.8 and 2.3.0 — proof that a vendor's tier changes between releases; a one-version-per-app baseline freezes that variation out.
5. **Base-split scope.** Base APKs were censused per the task; config splits were checked only for pairip native libs and random assets (§3), not fully censused. DEX never ships in config splits in this sample set (0 methods in the censused split), so stub counts are unlikely to be affected, but asset/lib placement across splits is only spot-verified.

## 6. What a larger baseline would need

1. **Scale and stratification:** n ≥ 30–50 apps sampled *randomly within strata* (category × app size × popularity), not by known-PairIP reputation, before any "typical footprint" claim becomes distributional. Include at least a few top-download and game titles, where a heavy-VM tier would most plausibly appear.
2. **Longitudinal sampling:** 2–3 versions per app (as Paseo already has here) so tier changes like VPNify's 2.1.8→2.3.0 drop are measured, not frozen.
3. **A split-aware, XAPK-aware pipeline:** the failed runs this doc replaced (exit 1, § provenance note) came from pointing the analyzer at container artifacts; the harness should extract XAPKs, census base *and* every config split, and merge per-app results (Java census from base; `libpairipcore.so` presence/ABI from splits) into one record.
4. **Census-tool extensions:** flag random-named top-level asset blobs (the §3 count) and per-ABI native-lib correlation as first-class fields, since `vmcodeAssets` is a universal negative in production builds; keep the exact stub-token extraction so cross-app batch-transform comparisons (§3) are mechanical.
5. **Payload ground truth:** decrypt or runtime-trace one app's random-named blobs (via the `VmDecryptor` path, under the program's ROE) to convert "blob count" into "confirmed VM bytecode count," turning the §3 [interpretation] into [measured].
6. **Per-category negative controls** (as VPNify 2.3.0 is here) so detection-rate claims have a false-positive floor.

## 7. Run record — every command executed this session **[measured]**

All runs from the workspace root; tool `pairip-research/tools/pairip-audit/run_audit.py`; environment Python 3.14.6, androguard 4.1.4. Stdout summary lines quoted verbatim; all exits 0.

```
python pairip-research/tools/pairip-audit/run_audit.py pairip-research/samples/apk/baseline/vpnify-2.1.8-base.apk --out pairip-research/samples/out/census-app-vpnify-2.1.8.json
  -> "pairipDetected=True pairipClasses=9 stubs=20/124227 (0.02%)"            EXIT=0
python pairip-research/tools/pairip-audit/run_audit.py pairip-research/samples/apk/baseline/efteling-latest-base.apk --out pairip-research/samples/out/census-app-efteling-latest.json
  -> "pairipDetected=True pairipClasses=36 stubs=0/228443 (0.0%)"             EXIT=0
python pairip-research/tools/pairip-audit/run_audit.py pairip-research/samples/apk/baseline/paseo-latest-base.apk --out pairip-research/samples/out/census-app-paseo-latest.json
  -> "pairipDetected=True pairipClasses=36 stubs=0/271107 (0.0%)"             EXIT=0
python pairip-research/tools/pairip-audit/run_audit.py pairip-research/samples/apk/baseline/paseo-0.7.2-base.apk --out pairip-research/samples/out/census-app-paseo-0.7.2.json
  -> "pairipDetected=True pairipClasses=35 stubs=0/265937 (0.0%)"             EXIT=0
python pairip-research/tools/pairip-audit/run_audit.py pairip-research/samples/apk/baseline/vpnify-latest-base.apk --out pairip-research/samples/out/census-app-vpnify-latest.json
  -> "pairipDetected=False pairipClasses=0 stubs=0/119275 (0.0%)"             EXIT=0
python pairip-research/tools/pairip-audit/run_audit.py pairip-research/samples/apk/baseline/vpnify-218-extract/config.armeabi_v7a.apk --out pairip-research/samples/out/census-app-vpnify-2.1.8-config-armeabi_v7a.json
  -> "pairipDetected=True pairipClasses=0 stubs=0/0 (0.0%)"                   EXIT=0
```

Supporting passes (stdlib `zipfile`, inline Python, this session): (a) per-census field extraction incl. exact `stubs/totalMethods×100` and perDex class sums — source of every §2 cell; (b) `unzip -l` + `zipfile` enumeration of every config split in `vpnify-xapk-extract`, `efteling-xapk-extract`, `paseo-xapk-extract`, `paseo-072-extract` for pairip/`.vmcode`/`lib/` entries — source of §3 native-lib rows (Grindr's arm64 split read as `samples/apk/splits/split_config.arm64_v8a.apk`, agreeing with `docs/05:41`); (c) random-16 asset count + first-16-byte headers across all six base APKs — source of the §3 blob table; (d) `stubMethodsList` reads and class-composition/prefix counts for all apps; (e) `find` confirming no `census-app-*.json` pre-existed. File reads: all seven census JSONs named in §1 (in full for stub lists and classes), `tools/pairip-audit/run_audit.py`, `pairip_audit/{census.py,assets.py}`, `docs/05`, `docs/09` (grep-verified citations), `samples/pairipcore/README.md:202`, `samples/pairipcore-vm/README.md:28`.

**Not done this session (and therefore not claimed):** decryption or content analysis of the random-named asset blobs; any runtime/dynamic analysis of baseline apps; download provenance verification for the XAPKs (files consumed as found; identities cross-checked only via embedded `versionName`/`versionCode`, which matched the task record for all five).
