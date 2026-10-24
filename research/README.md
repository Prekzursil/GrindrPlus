# PairIP / GrindrPlus Research Program — Master Index

An evidence-graded research project studying **PairIP** (Google Play's VM-based app
integrity protection, shipped via `libpairipcore.so` / `com.pairip.*`) and its
deployment in the Grindr Android app, plus an engineering post-mortem of the
archived [GrindrPlus](https://github.com/R0rt1z2/GrindrPlus) Xposed module.

This README is the master index: the Charter defines the deliverables
(`docs/00`–`docs/04`; the escalation run extended the series with
`docs/05`–`docs/08`), **Findings at a glance** summarizes what each concluded,
**Reproduction** rebuilds the measured numbers, and **Limitations** states the
evidence boundary. Evidence rules live in `ROE.md`; every claim in every doc
cites what was read or run.

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
provenance docs, by the API pulls and log reads cited inside each doc; each
bullet points to the doc section that carries its evidence.

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
- Residual caveats: the identities of the 20 stub methods are not recorded; the stub heuristic has documented blind spots. (The ABI-split caveat this bullet originally carried — splits unmeasured — is closed by `docs/05`: `libpairipcore.so` ships in all three ABI splits; the base split itself still ships no native libs.)
- Both censuses (`samples/out/census.json`, `census-base.json`) were reproduced identically by re-run this session; the analyzer's 81-test suite passes.

**`docs/03` — Legacy combo audit (GrindrPlus v4.7.2-lineage × pinned Grindr)**

- 20 of 29 hooks (69%) target R8-reassigned short names (`vn.a`, `fo.k`, `sk.g`) and re-break on essentially every re-minified Grindr release — upstream release v4.4.0 existed solely to "add support" for one new Grindr version.
- Only 4 hooks (14%) are high-confidence survivors of a Grindr update (AllowScreenshots, SSLUnpinning, TimberLogging, StatusDialog — all OS/bundled-library API).
- The snapshot's compile-time pin is Grindr 26.0.1/149389 (the 25.21.1 in `version.json` is the update-spoof tracker, not the build pin); upstream is archived (2026-05-18) and the pinned build is ~9 months old.
- The binding constraint is the **server gate**, not the hooks: upstream's own record shows Grindr moving features server-side (v4.6.0) and version-gating login; verdict — the combo is at or past end-of-life.

**`docs/04` — Forkability review (GrindrPlus snapshot at `EOL` commit `aa497a0`)**

- Restarting from the snapshot is cheap (days — toolchain vendored in-tree); sustaining it is not (a days-to-weeks reverse-engineering sprint per Grindr release across ~26 obfuscated class pins + ~27 method pins, guided by 64 breadcrumb comments; zero automated tests).
- The post-PairIP verdict is downgraded to *attributed-but-not-demonstrated*: the 26.21.0 census (20/422,621 stubs) shows runtime hooking is structurally plausible, but with the native layer examined only for presence (`docs/05`: `libpairipcore.so` hashed and sized in all three ABIs, never disassembled) it remains a research bet, not a fork.
- GPL-3.0 obligations are real and partly unmet by the snapshot itself: no per-file headers, attribution only in (absent) git history, and the `old_base` branch is unlicensed — a contamination hazard that must never be folded into a fork.
- Verdict: not worth forking as a living mod for current Grindr; marginal as frozen-version maintenance; genuinely valuable as reference architecture (hook framework, LSPatch pipeline) for targets that don't ship PairIP.

**`docs/05` — ABI-split census (four config splits of the 26.21.0 bundle, measured 2026-10-23)**

- `libpairipcore.so` ships in **all three ABI splits** — arm64-v8a (608,896 B), x86_64 (624,184 B), x86 (697,616 B) — and in no other split; three distinct SHA-256s mean three distinct per-ABI builds, not one library stamped three times. The xxhdpi density split, as control, contains zero native libraries.
- No split carries DEX or assets: every `com.pairip.*` class and all 422,621 method entries live in the base split; the ABI splits hold only ZIP-STORED `lib/<abi>/*.so` plus manifest and Play signing stamp.
- Reconciliation with `docs/02`: the bundle deploys the **full PairIP stack** — base split = the entire Java layer (integrity wrapper, entry wrapping, `VMRunner`), ABI splits = the native VM runtime — so the base's `loadLibrary("pairipcore")` resolves on any installable device; `docs/02`'s "requests a library it does not ship" tension was an artifact of analyzing the base split in isolation.
- Reading: the deployment is **integrity-first** — the always-on, every-launch protection is the signature/license wrapper at process entry, while the VM is fully shipped but sparsely invoked (the 20-stub figure stands). The `.so` files were hashed and sized only, **not disassembled** (`docs/05` §2–§4, §6).

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

## Limitations

- **Static analysis everywhere except one observational first-run** (ROE §1–§2).
  Nothing was hooked, modified, or instrumented anywhere in this program. The
  sole dynamic activity is `docs/07`'s stock first-run (adb install + one
  launch + logcat read — next bullet); every other behavioral claim (crash on
  tamper, anti-frida activity) is sourced to public research via the dossier,
  not observed here (`docs/02` §7.1; `docs/07` §0).
- **Observational first-run only, no instrumentation.** `docs/07` is a single
  42.4 s logcat capture of one launch of the unmodified app on one confounded
  BlueStacks instance (emulator, permissive SELinux, LSPosed present on the
  image, Play account logged in); no Frida, no Xposed acting on the app, no
  debugger attach, no network interception, no re-launch, no second device;
  licensing/integrity verdict payloads are invisible in logcat, so the
  silent-exit attribution is sequencing-based inference (`docs/07` §0, §6, §7).
- **ABI-split presence measured; library interiors not.** `docs/05` closed the
  gap this section previously carried ("ABI splits unmeasured" —
  `libpairipcore.so` is now measured present in arm64-v8a, x86_64, and x86),
  but the `.so` files were hashed and sized only, never disassembled:
  environment checks inside the library and opcode-table divergence across the
  three builds remain unmeasured. The base split ships no native libraries,
  and stub-method identities are still not recorded by the census format
  (`docs/05` §6; `docs/02` §7.5).
- **Policy verification runs against HackerOne's GraphQL API, not the rendered
  page.** The public policy pages are JS-rendered and return no content to plain
  fetches; quotes were verified against the GraphQL endpoint the page itself
  loads (42 of 59 fragments byte-exact, 17 matching at formatting level — none
  failed content-level verification; `docs/00` method section).
- Additional documented limits live in each deliverable (dossier provenance
  grades in `docs/01` §10; version-skew and mirror-provenance caveats in
  `docs/02` §7; single-snapshot scope of `docs/03`–`04`; `docs/05` §6, `docs/06`
  §10, `docs/07` §7, and `docs/08` §4 carry the later series' own limits).

## Layout

```
docs/     numbered research deliverables (00–08)
tools/    pairip-audit analyzer package (src + tests + CI)
samples/  gitignored: cloned repos, downloaded APKs, analyzer output
ROE.md    rules of engagement and evidence rules
```

License: MIT for original code in `tools/`; documents are CC BY 4.0.
Third-party material in `samples/` keeps its upstream license (GrindrPlus is GPL-3.0).
