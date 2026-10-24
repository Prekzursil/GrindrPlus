# PairIP / GrindrPlus Research Program — Master Index

An evidence-graded research project studying **PairIP** (Google Play's VM-based app
integrity protection, shipped via `libpairipcore.so` / `com.pairip.*`) and its
deployment in the Grindr Android app, plus an engineering post-mortem of the
archived [GrindrPlus](https://github.com/R0rt1z2/GrindrPlus) Xposed module.

This README is the master index: the Charter defines the deliverables
(`docs/00`–`docs/04`; later runs extended the series through `docs/14`),
**Findings at a glance** summarizes what each concluded, **Reproduction**
rebuilds the measured numbers, and **Limitations** states the evidence
boundary. Evidence rules live in `ROE.md`; every claim in every doc cites
what was read or run. The tier-3 provisions added to `ROE.md` §5 (2026-10-24,
user-approved) authorize the two newest tracks: passive in-scope recon
(`docs/13`) and local, characterization-only tamper probes (`docs/14`).

## Charter

This project produces **research, measurement, and disclosure artifacts only**:

1. `docs/00-scope-verification.md` — what Grindr's HackerOne bounty policy actually
   covers (verbatim quotes retrieved from the live policy via HackerOne's GraphQL
   API; per-quote re-verification ran against that channel, not the JS-only
   rendered page — see the doc's method-and-limitations section).
2. `docs/01-pairip-dossier.md` — deep technical dossier on PairIP from public
   research (VM architecture, integrity/licensing layer, published bypass classes,
   tooling), with per-claim provenance and confidence grades.
3. `docs/02-feasibility-study.md` — static attack-surface measurement of the
   current Grindr APK using `tools/pairip-audit`: what fraction of methods are
   virtualized vs. plain Java, and a hookability verdict.
4. `docs/03-legacy-combo-audit.md` — hook-by-hook audit of GrindrPlus v4.7.x
   against its pinned Grindr (compile-time pin 26.0.1/149389; the 25.21.1 in
   `version.json` is the update-spoof tracker, not the build pin — see docs/03 §1),
   with a longevity estimate.
5. `docs/04-forkability-review.md` — engineering review of the GrindrPlus
   codebase: architecture, hook infrastructure, resumption cost, GPL-3.0 duties.

`tools/pairip-audit` is a tested, CI'd static analyzer (pure Python) that produces
the protection census for deliverable 3.

## Out of scope (hard boundary — see ROE.md)

No bypass artifacts are produced or hosted here: no integrity-check defeat code,
no patched/repackaged APKs, no Xposed/Frida hook packs restoring paid features,
no ban-evasion tooling, and no testing against live Grindr infrastructure. If
in-scope vulnerability classes are confirmed under the bounty policy, the output
is a HackerOne report draft — not tooling.

## Findings at a glance

Measured numbers below were produced (or reproduced) on 2026-10-22 through
2026-10-24 by the commands in **Reproduction** and, for the corpus/runtime/
provenance/recon/probe docs, by the API pulls, log reads, and probe artifacts
cited inside each doc; each bullet points to the doc section that carries its
evidence.

**`docs/00` — Scope verification** (policy retrieved 2026-10-22 via HackerOne's GraphQL API; current version id 3713946, effective 2024-03-11; 34 structured-scope assets)

- `com.grindrapp.android` is a bounty- and submission-eligible asset; black-box testing of the app is the program's stated method, and *defeating certificate pinning* is explicitly invited to reach higher-severity API issues.
- Client-integrity findings are ranked by cross-user impact, not bypass strength: Critical = tamper/reverse the app into another user's account takeover or data exposure; Medium = fraud-enabling tampering; a bypass demonstrated only on your own account is expressly excluded.
- Rooted-device / outdated-OS mobile findings are excluded outright; MITM/physical-access chains against other users are excluded; publication of client internals requires Grindr's explicit consent (confidentiality clause).
- All six exposed policy versions (2023-02-23 → 2024-03-11) are textually identical on every anti-tamper-relevant clause — the program has never touched its client-side research terms.

**`docs/01` — PairIP dossier** (33 sources read in full; 71 graded findings; 21 confirmation checks)

- PairIP is the community name for Google Play's opt-in, partner-gated "automatic integrity protection"; Google's documentation never uses the name, so everything public about the VM comes from third-party reverse engineering. Confidence HIGH on VM architecture (three converging RE efforts), MEDIUM on Grindr chronology, LOW–MEDIUM on bypass working statuses.
- Mechanism: selected method bodies are replaced with `VMRunner.invoke(...)` calls executing per-method bytecode in a native interpreter inside `libpairipcore.so`; the opcode-to-handler mapping is randomized on every library build, so no portable public decoder exists (best public tooling: ≈86% *format* coverage on one target binary; semantics for 14 of ~99 opcodes).
- Layered defense: Java `SignatureCheck` at the earliest startup point (crash on mismatch), native `protections_main` (raw-syscall anti-debug, `/proc` scanning, frida-server detection), and a `com.pairip.licensecheck` licensing layer (Play redirect or silent exit).
- Grindr chronology: hookable at 25.20.0 (Nov 2025) → GrindrPlus probable-EOL announcement 2026-03-21 blaming "advanced native-backed VMProtect-esque protections" → repo archived 2026-05-18, eleven days after the server-side cutoff of the last supported version. The first protected Grindr version is bracketed, not measured.

**`docs/02` — Feasibility study (measured on Grindr 26.21.0 / 189896, base split; its open native-layer question is now answered: `libpairipcore.so` is present in the arm64-v8a, x86_64, and x86 splits — `docs/05`)**

- PairIP is **structurally present**: **46 `com.pairip.*` classes**; the manifest application is the PairIP wrapper (`com.pairip.application.Application`), `SignatureCheck` + `LicenseClient` are wired at `attachBaseContext`, `StartupLauncher` wraps framework factories, and `VMRunner.<clinit>` requests `System.loadLibrary("pairipcore")`.
- Virtualization footprint ≈ 0%: **20 VM-stub markers out of 422,621 method entries** (0.00473%) across 11 dex files, 110 integrity entry points, zero scan errors, complete coverage.
- Verdict: runtime hooking of an unmodified APK (the GrindrPlus model) is **structurally plausible again**; static repackaging/re-signing remains blocked by the signature check.
- Residual caveats: the stub heuristic has documented blind spots. (Two caveats this bullet originally carried are now closed: the stub-identity gap by `docs/09` — all 20 stubs are named, disassembled, and characterized — and the ABI-split gap by `docs/05` — `libpairipcore.so` ships in all three ABI splits, while the base split itself still ships no native libs.)
- Both censuses (`samples/out/census.json`, `census-base.json`) were reproduced identically by re-run this session; the analyzer's 81-test suite passes.

**`docs/03` — Legacy combo audit (GrindrPlus v4.7.2-lineage × pinned Grindr)**

- 20 of 29 hooks (69%) target R8-reassigned short names (`vn.a`, `fo.k`, `sk.g`) and re-break on essentially every re-minified Grindr release — upstream release v4.4.0 existed solely to "add support" for one new Grindr version.
- Only 4 hooks (14%) are high-confidence survivors of a Grindr update (AllowScreenshots, SSLUnpinning, TimberLogging, StatusDialog — all OS/bundled-library API).
- The snapshot's compile-time pin is Grindr 26.0.1/149389 (the 25.21.1 in `version.json` is the update-spoof tracker, not the build pin); upstream is archived (2026-05-18) and the pinned build is ~9 months old.
- The binding constraint is the **server gate**, not the hooks: upstream's own record shows Grindr moving features server-side (v4.6.0) and version-gating login; verdict — the combo is at or past end-of-life.

**`docs/04` — Forkability review (GrindrPlus snapshot at `EOL` commit `aa497a0`)**

- Restarting from the snapshot is cheap (days — toolchain vendored in-tree); sustaining it is not (a days-to-weeks reverse-engineering sprint per Grindr release across ~26 obfuscated class pins + ~27 method pins, guided by 64 breadcrumb comments; zero automated tests).
- The post-PairIP verdict is downgraded to *attributed-but-not-demonstrated*: the 26.21.0 census (20/422,621 stubs) shows runtime hooking is structurally plausible, but with the native layer examined short of disassembly (`docs/05`: `libpairipcore.so` hashed and sized in all three ABIs; `docs/10`: symbol/section-level inventory — still no disassembly) it remains a research bet, not a fork.
- GPL-3.0 obligations are real and partly unmet by the snapshot itself: no per-file headers, attribution only in (absent) git history, and the `old_base` branch is unlicensed — a contamination hazard that must never be folded into a fork.
- Verdict: not worth forking as a living mod for current Grindr; marginal as frozen-version maintenance; genuinely valuable as reference architecture (hook framework, LSPatch pipeline) for targets that don't ship PairIP.

**`docs/05` — ABI-split census (four config splits of the 26.21.0 bundle, measured 2026-10-23)**

- `libpairipcore.so` ships in **all three ABI splits** — arm64-v8a (608,896 B), x86_64 (624,184 B), x86 (697,616 B) — and in no other split; three distinct SHA-256s mean three distinct per-ABI builds, not one library stamped three times. The xxhdpi density split, as control, contains zero native libraries.
- No split carries DEX or assets: every `com.pairip.*` class and all 422,621 method entries live in the base split; the ABI splits hold only ZIP-STORED `lib/<abi>/*.so` plus manifest and Play signing stamp.
- Reconciliation with `docs/02`: the bundle deploys the **full PairIP stack** — base split = the entire Java layer (integrity wrapper, entry wrapping, `VMRunner`), ABI splits = the native VM runtime — so the base's `loadLibrary("pairipcore")` resolves on any installable device; `docs/02`'s "requests a library it does not ship" tension was an artifact of analyzing the base split in isolation.
- Reading: the deployment is **integrity-first** — the always-on, every-launch protection is the signature/license wrapper at process entry, while the VM is fully shipped but sparsely invoked (the 20-stub figure stands). The `.so` files were hashed and sized only, **not disassembled** (`docs/05` §2–§4, §6; `docs/10` later added symbol-level inventory — disassembly remains undone).

**`docs/06` — GrindrPlus public corpus (GitHub API mining, 2026-10-24)**

- Full release ledger: **44 module releases over 868 days** (2023-09-12 → 2026-01-28, one per ~19.7 days) tracking **29 distinct Grindr builds**; 22 of 44 release notes are dominated by repairing what a Grindr update broke — the version-mapping treadmill `docs/04` described qualitatively, now quantified (`docs/06` §2).
- The issue shelf is **verifiably empty**: issues are disabled at repo level and an exhaustive probe of numbers 1–360 resolves 103 items — every one a PullRequest, zero Issues — so no user-filed ban report exists in the public record; the maintainer's Telegram mirrors (`news.json`, 23 messages) are the substitute signal (`docs/06` §3).
- Verbatim maintainer statements with URLs: the PairIP announcement (news msg 197, 2026-03-21 — "advanced native-backed VMProtect-esque protections … probably the end"), the wind-down (msg 198, 2026-04-02), and the EOL-day commit sequence (2026-04-04: "Nuke CIs" → spoof pinned 26.5.0→25.21.1 → "EOL" README banner) (`docs/06` §4, §6).
- The version-pinning machinery is documented end-to-end — compile-time pin in `build.gradle.kts` (one release = one pinned Grindr build, verified at four release tags), runtime version gate, APKMirror-scraping `version.json` spoof feed, self-hosted manager APK feed — including the final act: the spoof itself invited server-side grid gating, so the maintainer pinned the *claimed* version back under 26.x (`docs/06` §7).
- Dating the wall: 25.20.0 (bot-tracked 2025-11-21) is the last Grindr version a module release supports; the PairIP announcement postdates a 26.4.2 sighting; **which build first shipped PairIP remains bracketed, not identified** (`docs/06` §8).

**`docs/07` — Runtime observation (observational first-run on BlueStacks, log captured 2026-10-23)**

- One stock, unmodified first run of 26.21.0 observed via adb logcat (42.4 s window): `SignatureCheck` printed "Signature check ok" at each process start, `com.pairip.licensecheck.LicenseActivity` foregrounded and finished, full `LicenseClient` rounds ran, and the app requested a Play Integrity token (GMS separately logged eight emulator-pattern token-generation failures) (`docs/07` §3).
- **No crash anywhere in the log**: both app-process exits were deliberate `System.exit(0)` clean self-terminations — a firsthand corroboration of the dossier's silent-exit licensing path on a sideloaded copy; the attribution is sequencing-based inference, as the log prints no reason (`docs/07` §4, §6.1).
- The running Application class is directly observed as `com.pairip.application.Application`; the VM itself stayed dark (zero `VMRunner` lines), consistent with the dossier's account (`docs/07` §3.1, §3.3).
- The first-run funnel never reached account creation: the only Grindr frame drawn was LoginActivity, then the PairIP LicenseActivity, then the Play Store's own Play-Pass paywall — after which no Grindr UI existed; the app process cycles start → license round → exit (`docs/07` §5–§6.5).

**`docs/08` — Provenance map & execution post-mortem (2026-10-24)**

- One-table provenance map for `docs/00`–`04`: where each doc's evidence lives, how it was verified, and which claims were ask-sourced vs re-measured, with each doc's residual caveats preserved (`docs/08` §1).
- Run-chain post-mortem: the main run settled 64/65 steps over 7.5 h then died mid-writer on a driver-internal crash; amending it reproduced the identical crash 1 s after launch (a journal containing an in-flight step is poison); recovery came from a fresh minimal workflow that consumed the on-disk artifacts and re-ran only the missing tail (`docs/08` §2).
- General lessons: recover from artifacts, not journals, when a run dies mid-step; keep writer steps cheap and last; superseded-at-launch runs cost nothing (`docs/08` §2.3).
- Fork record: the program lands in `github.com/Prekzursil/GrindrPlus` under `research/`, licensed GPL-3.0 to match the fork, upstream's 546-commit history untouched; the push was pending at writing time, not done (`docs/08` §3).

**`docs/09` — Virtualized-method identities (the 20 stubs of 26.21.0 named, disassembled, characterized; 2026-10-24)**

- All 20 stubs are identified: every one is a **third-party SDK event callback** — 5 Agora call-audio receivers, 11 advertising (GMS Ads ×3, Fyber ×2, AppLovin, PubNative, InMobi, Mintegral, ironSource AdQuality, one GMS-cluster inference), 3 push/identity (Braze ×2, one inferred; Facebook), 1 location-flow receiver with unresolved owner. **0 touch integrity/licensing; 0 are Grindr first-party code**; 17 identifications direct, 3 inferred (`docs/09` §3, §3.4).
- Every stub is the same 11–12-instruction `VMRunner.invoke(token, {this, args…})` body with a unique 16-char token (18 `onReceive`, 1 `doInBackground`, 1 `doWork`); 15 of 20 declaring classes carry `$00N`-suffixed synthetic accessors; only 2 of the 20 stub classes are manifest-registered (Braze, Facebook); `vmcodeAssets` is `[]`, confirmed twice — bytecode is fetched from the installed APK and decrypted at call time via `VmDecryptor` (`docs/09` §2–§4).
- Reading: `docs/02`'s "the 20 may be exactly the ones that mattered" hypothesis is substantially weakened *for this build* — the set reads as an automatic batch transform over SDK entry callbacks, and the integrity-first verdict of `docs/02`/`docs/05` is strengthened; the stubs remain a floor, not a ceiling, and were not decoded (`docs/09` §5–§6).

**`docs/10` — Native inventory & research drift (`libpairipcore.so`, three ABIs, pyelftools; 2026-10-24)**

- Byte-verified against `docs/05`'s hashes, then inventoried: the exported surface is identical on all three ABIs and is exactly three symbols — `ExecuteProgram`, `JNI_OnLoad`, `JNI_OnUnload`; no `Java_*` export anywhere. Imports: 69 symbols common to all three (incl. `dlopen`/`dlsym`/`dlclose`/`dl_iterate_phdr`, a bare `syscall`, `__system_property_read/foreach`, `android_set_abort_message`) with `prctl`/`ptrace`/`openat`/`read`/`lseek` notably absent from the PLT. The binaries are statically linked LLVM libc++abi/unwind payloads (custom `__lcxx_override` section; no pairip-specific strings beyond the soname) (`docs/10` §1–§3).
- Drift vs the two public research baselines is **additive, not subtractive**: `ExecuteProgram` — a *named* VM-family entry on every ABI — and `JNI_OnUnload` are exports neither the 2024 nor the 2025 research documents (the 2024 baseline had to recover the entry dynamically because symbols were stripped); the documented entry chain (DEX `executeVM` → `RegisterNatives` inside `JNI_OnLoad`) is unchanged; and the baselines' `assets/*.vmcode` deployment is gone (deployment drift — bytecode carried some other way) (`docs/10` §4).
- Boundary: symbol- and byte-level facts only — no disassembly, decompilation, or dynamic execution; what `ExecuteProgram` actually is (renamed `executeVM`, second entry, or unrelated) remains open (`docs/10` §4.2, §6).

**`docs/11` — Version timeline (25.19.0 / 25.21.1 / 26.8.2 / 26.21.0 censuses; the track's failed exit-1 runs re-run successfully, 2026-10-24)**

- 25.19.0 and 25.21.1 carry **zero PairIP markers of any kind** (no classes, stubs, entry points, `.vmcode` asset, or `libpairipcore.so` in any split); 26.8.2 already ships the complete kit (40 classes, 20 stubs, 92 entry points, `.so` in 4 ABIs). The entire observable PairIP footprint postdates the module's last supported version (`docs/11` §1–§2).
- The introduction bracket narrows to **versionCode (148541, 162647]** — after 25.21.1, by 26.8.2 — inside which the maintainer's 2026-03-21 "VMProtect-esque" announcement falls. 26.0.1 (the module's compile pin) was never fetched, so this is a code range, not a build identity (`docs/11` §2).
- Trajectory: flat zero → step introduction of the whole kit (all 11 core classes + licensecheck family already present at 26.8.2) → growth confined to the **licensing surface** (licensecheck 29→35 classes incl. new `TrialClient`/trial-stop path; entry points 92→110, all licensing bookkeeping) while the app itself shrank 21.6% (539,087→422,621 methods). The protection core has been structurally frozen since at least 26.8.2 (`docs/11` §3).
- The stub set churns 60% between 26.8.2 and 26.21.0 (8 persist, 12 leave, 12 arrive) while the count holds at exactly 20 — the selection *policy* (receivers/workers) is the stable trait, not the targets. Seven distinct `.so` hashes across the lineage; all three common-ABI libraries grew in size; the app dropped armeabi-v7a entirely, cutting native coverage 4 ABIs → 3 (`docs/11` §4–§5).

**`docs/12` — Cross-app baseline (five Play apps + one config split censused; six runs, all exit 0; 2026-10-24)**

- Three integration profiles exist, not one intensity: **license-only** (Efteling 5.27.0, Paseo 0.12.0 & 0.7.2 — 34–36 licensecheck classes, no VMRunner/SignatureCheck, 0 stubs, no native lib in base *or* any split), **integrity+VM without license client** (VPNify 2.1.8 — 9 classes, 20 stubs, `libpairipcore.so` in its config split), and **full stack** (Grindr = VPNify's kit plus `InitContextProvider`, `VmDecryptor`, and the 35-class licensecheck family) (`docs/12` §2–§3).
- The only other VM-stack app measured, VPNify 2.1.8, shows the **identical stub count (20)** with the identical callback-only selection across ad/analytics SDKs — including two *exact* class#method matches with Grindr (the Facebook auth-token receiver; GMS `OfflinePingSender.doWork`) — cross-app corroboration of the automatic-batch-transform reading (`docs/12` §3).
- `vmcodeAssets` is `[]` for every app; random-16-char top-level asset blobs appear **only** in the two VM-stack apps (Grindr 30, 176–480 KB; VPNify 2.1.8 22, 31–114 KB; zero in the other four) — consistent with, but not proof of, a renamed/encrypted VM-bytecode payload; no decryption attempted. VPNify 2.3.0 is a clean negative control on both base and split: same publisher, PairIP dropped entirely (`docs/12` §3).
- Verdict: within the population that actually ships the VM, **20 stubs / ~0.005% is the typical footprint** — Grindr is the largest app carrying the smallest relative (and tied-smallest absolute) stub load; no app in the sample virtualizes a large share of code. The sample is n = 5 apps / 4 packages, so nothing distributional is claimed (`docs/12` §4–§5).

**`docs/13` — Bounty recon outcome (ROE §5.1; three passive passes, ~60 unauthenticated requests, in-scope-only; 2026-10-24)**

- One confirmed, drafted finding: **`admin.grindr.com` serves a TLS certificate expired ~18.6 months** (`notAfter` 2025-04-05, `CN=*.grindr.com`; re-served identically by a fresh handshake in the doc's verification pass); accepting it reaches only a CloudFront→S3 403; proposed **Low**. Exactly one HackerOne draft exists and it is **unpublished** (`samples/h1-drafts/admin-grindr-com-expired-tls-certificate.md`) (`docs/13` §3 C1, §5).
- Observed but held below reporting threshold: `web.grindr.com`'s security.txt `Expires: 2024-01-01` (≈22 months stale), `reporting-portal.grindr.com` with no public A record, and CSP third-party allowances. One candidate was **eliminated by verification** (exposed sourcemaps — the `.map` URLs return the 4.6 KB SPA shell byte-identically); the secrets scan of the Grindr-Web bundles is negative (0 AWS/Sentry/Mapbox keys; only a public reCAPTCHA sitekey) (`docs/13` §3 C2–C6).
- The LicenseActivity "crash" of `docs/07` is formally assessed: **there is no crash** — it is the deliberate silent `System.exit(0)` licensing self-exit on the researcher's own sideloaded copy, squarely inside the policy's own-use exclusion; no report drafted from it (`docs/13` §4).

**`docs/14` — Tamper-response probes (ROE §5.2; P1 unsigned-modified / P2 resigned-unmodified / P3 resigned-modified; 2026-10-24)**

- The final probe wave **never reached a device**: all three installs failed at the adb transport layer (`device '127.0.0.1:5555' not found`) — PackageManager was never asked for a verdict on P1 or P3, and no logs exist for either from any wave (`docs/14` §2).
- One completed run survives (`samples/out/probe-P2.log`, earlier wave): a base-only install of 26.21.0 **installed cleanly**, then died **FATAL `UnsatisfiedLinkError … libpairipcore.so` at `VMRunner.<clinit>` 0.85 s after process start** — before the Application class, before any Java-level gate (0 `SignatureCheck`/licens*/integrity lines in the whole log; exactly one process start, no retries) (`docs/14` §3).
- Attribution, bounded: the crash is a **packaging-composition artifact** — the base APK ships zero native libraries and the harness installed base-only, so the library the Java bootstrap hard-requires was never on the device; it is *not* an observed defensive response to the re-sign, and the clean base-only control was never run. No `SignatureCheck` failure verdict, license response, or P1/P3 behavior was ever observed anywhere in the program (`docs/14` §4, §6).

## Reproduction

All commands run from this repo root (`pairip-research/`); the in-repo
`pairip-research` symlink makes the `pairip-research/...` paths resolve. All
three were verified this session (2026-10-22):

```bash
pip install -r tools/pairip-audit/requirements.txt   # androguard 4.1.4 + pytest 8.4.2
python -m pytest pairip-research/tools/pairip-audit/tests -q   # 81 passed (synthetic fixtures; no real APK)
python pairip-research/tools/pairip-audit/run_audit.py <apk> --out census.json

# split census (docs/05) — one run per split; all four exit 0 (2026-10-23)
python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/splits/split_config.arm64_v8a.apk \
    --out pairip-research/samples/out/census-split-arm64_v8a.json
# …same form for split_config.x86_64.apk / split_config.x86.apk / split_config.xxhdpi.apk

# named census (docs/09–12 input) — same 26.21.0 base APK, stub identities included
python pairip-research/tools/pairip-audit/run_audit.py \
    pairip-research/samples/apk/grindr-current-base.apk \
    --out pairip-research/samples/out/census-base-named.json
# version-lineage censuses (docs/11) — all three exit 0 (2026-10-24)
#   samples/apk/versions/{25.19.0,25.21.1,26.8.2}-base.apk → samples/out/census-<v>.json
# cross-app baseline censuses (docs/12) — six runs, all exit 0 (2026-10-24)
#   samples/apk/baseline/*-base.apk (plus one config split) → samples/out/census-app-*.json

# native inventory (docs/10) — pyelftools; run from pairip-research/samples/
python tools/so_inventory.py out/so/libpairipcore-arm64_v8a.so > out/so/inventory-arm64_v8a.json
# …same form for -x86_64.so / -x86.so
```

For `<apk>` use a real APK or extracted split (e.g. the base split of an
APKMirror bundle); the recorded census for Grindr 26.21.0's base split
(`samples/out/census-base.json`, gitignored) was reproduced identically by
re-running the third command this session:
`pairipDetected=True pairipClasses=46 stubs=20/422621 (0.0%)`.
The unit suite uses faked androguard objects and synthetic zips — it needs no
APK and no network. Docs cite census facts as `docs/02` §2. The four split
censuses (`samples/out/census-split-{arm64_v8a,x86_64,x86,xxhdpi}.json`,
gitignored) were produced 2026-10-23 by the escalation run and re-verified
entry-for-entry by an independent stdlib `zipfile`/`hashlib` pass — verdict:
`libpairipcore.so` present in the three ABI splits, absent from xxhdpi
(`docs/05` §3, §5).

The later-track outputs (all gitignored, local-only per ROE §4) were produced
2026-10-24 by their respective doc sessions, each of which quotes its exact
commands, stdout lines, and exit codes in its own run record:
`samples/out/census-base-named.json` is the identity-carrying 26.21.0 census
consumed by `docs/09`–`docs/12` (`docs/09` §7 re-derived its headline fields
and re-verified every stub against the APK by hand); the three version
censuses and their `.log` stdout files back `docs/11` (§7 quotes all three
exit-0 lines); the six baseline censuses back `docs/12` (§7 quotes each
stdout line); the pyelftools inventories under `samples/out/so/` back
`docs/10` (§6). The `docs/13` recon artifacts (`samples/out/recon-20261024/`
and `samples/out/recon-pass2/`, plus the single unpublished draft under
`samples/h1-drafts/`) and the `docs/14` probe set (`samples/apk/probes/
P{1,2,3}.apk`, built by `samples/tools/build_probe_p1.py` + the vendored
uber-apk-signer, and the one surviving log `samples/out/probe-P2.log`) are
**not** re-runnable from this repo alone — they record one external vantage's
passive passes and one earlier emulator wave respectively; `docs/13` §7 and
`docs/14` §7 list every verification command that was run against them.

## Limitations

- **Static-analysis-first, with three bounded dynamic exceptions** (ROE §1–§2,
  §5). Nothing in this program was ever hooked, instrumented,
  debugger-attached, or network-intercepted. The only dynamic activities are:
  `docs/07`'s stock first-run (adb install + one launch + logcat read — next
  bullet); `docs/13`'s passive, unauthenticated, in-scope-only recon (ROE
  §5.1); and `docs/14`'s local, characterization-only tamper probes (ROE
  §5.2), of which the final wave never reached a device and the one surviving
  earlier run observed a stock base-only install crash (last two bullets).
  Every other behavioral claim (crash on tamper, anti-frida activity) is
  sourced to public research via the dossier, not observed here (`docs/02`
  §7.1; `docs/07` §0; `docs/14` §6).
- **Observational first-run only, no instrumentation.** `docs/07` is a single
  42.4 s logcat capture of one launch of the unmodified app on one confounded
  BlueStacks instance (emulator, permissive SELinux, LSPosed present on the
  image, Play account logged in); no Frida, no Xposed acting on the app, no
  debugger attach, no network interception, no re-launch, no second device;
  licensing/integrity verdict payloads are invisible in logcat, so the
  silent-exit attribution is sequencing-based inference (`docs/07` §0, §6, §7).
- **Native layer measured to symbol level; never disassembled.** `docs/10`
  took the three ABI `.so` files past `docs/05`'s hashes-and-sizes (ELF
  sections, dynsym imports/exports, string localization), but no
  disassembly, decompilation, or execution was performed: what the new
  `ExecuteProgram` export is, whether the shipped handler table follows the
  documented format-ID scheme, environment checks inside the library, and
  opcode-table divergence across the three builds all remain open
  (`docs/10` §4.2, §6). The stub-identity gap `docs/02` carried is closed
  for 26.21.0 (`docs/09`), but the census heuristic remains a floor —
  native-only virtualization, reflection-based delegation, and renamed/
  repackaged pairip runtimes are invisible to it (`docs/09` §6; `docs/12`
  §5.3).
- **Cross-app baseline is a point sample, not a distribution.** n = 5 apps
  (+1 split), 4 distinct packages, every one selected by known or suspected
  PairIP reputation, and all small-to-mid (119k–271k methods) next to
  Grindr's 422k; no top-download, game, or banking app was measured, so a
  heavy-VM tier, if it exists in the wild, is unmeasured. One version per
  app freezes tier changes (VPNify's 2.1.8→2.3.0 total drop is the one
  measured flip); config splits were spot-checked for libs/assets only. The
  random-16 asset blobs' identity as VM bytecode is interpretation, not
  confirmed — no decryption was attempted (`docs/12` §3, §5).
- **Version lineage bracketed, not continuous.** Four builds measured across
  the lineage; every intermediate release is unmeasured, and 26.0.1 (the
  module's compile pin) was never fetched, so the first protected build is a
  code range — versionCode (148541, 162647] — not an identity. The 26.8.2
  `.so` files were hashed, not symbol-inventoried as `docs/10` did for
  26.21.0; the original exit-1 analyzer failures were re-run successfully
  but their cause is unexplained (`docs/11` §0, §2, §7 Limitations).
- **Policy verification runs against HackerOne's GraphQL API, not the rendered
  page.** The public policy pages are JS-rendered and return no content to plain
  fetches; quotes were verified against the GraphQL endpoint the page itself
  loads (42 of 59 fragments byte-exact, 17 matching at formatting level — none
  failed content-level verification; `docs/00` method section).
- **Recon is passive, single-vantage, and its draft is undelivered.** One
  external vantage (Istanbul egress), three passes, ~60 unauthenticated
  requests; no CNAME/other RR-type DNS queries were made for the
  no-A-record finding, so deliberate split-horizon placement cannot be
  distinguished from misconfiguration or decommissioning; bot-detection
  variance appeared between passes (`grindr.mobi` 404→403); two of the
  draft's sub-checks have no saved artifacts and its pass-timeline wording
  differs from artifact times — all stated in the doc. The single HackerOne
  draft is unpublished; no triage outcome exists (`docs/13` §0, §3 C1/C5,
  §5, §7).
- **Tamper probes produced no device verdict.** The final probe wave failed
  at the adb transport layer before PackageManager was ever consulted; P1
  (unsigned-modified) and P3 (resigned-modified) were never observed on any
  device and have no logs from any wave. The one surviving log's P2-type
  attribution rests on filename + harness chronology (log content cannot
  distinguish P2 from P3), and its bytes cannot be verified against the
  rebuilt `P2.apk`. Its crash is a base-only packaging artifact — the clean
  base-only control was never run — so no `SignatureCheck` failure, license
  response, or integrity verdict to any tampered build has been observed
  anywhere in this program (`docs/14` §3.1, §4, §6).
- Additional documented limits live in each deliverable (dossier provenance
  grades in `docs/01` §10; version-skew and mirror-provenance caveats in
  `docs/02` §7; single-snapshot scope of `docs/03`–`04`; `docs/05` §6,
  `docs/06` §10, `docs/07` §7, `docs/08` §4, `docs/09` §6, `docs/10` §6,
  `docs/11` §7, `docs/12` §5, `docs/13` §0/§5/§7, and `docs/14` §6 carry
  the later series' own limits).

## Layout

```
docs/     numbered research deliverables (00–14)
tools/    pairip-audit analyzer package (src + tests + CI)
samples/  gitignored: cloned repos, downloaded APKs, analyzer output
ROE.md    rules of engagement and evidence rules
```

License: MIT for original code in `tools/`; documents are CC BY 4.0.
Third-party material in `samples/` keeps its upstream license (GrindrPlus is GPL-3.0).
