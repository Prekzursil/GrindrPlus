# PairIP / GrindrPlus Research Program — Master Index

An evidence-graded research project studying **PairIP** (Google Play's VM-based app
integrity protection, shipped via `libpairipcore.so` / `com.pairip.*`) and its
deployment in the Grindr Android app, plus an engineering post-mortem of the
archived [GrindrPlus](https://github.com/R0rt1z2/GrindrPlus) Xposed module.

This README is the master index: the Charter defines the deliverables
(`docs/00`–`docs/04`), **Findings at a glance** summarizes what each concluded,
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

Measured numbers below were produced (or reproduced) on 2026-10-22 by the
commands in **Reproduction**; each bullet links to the doc section that carries
its evidence.

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

**`docs/02` — Feasibility study (measured on Grindr 26.21.0 / 189896, base split)**

- PairIP is **structurally present**: **46 `com.pairip.*` classes**; the manifest application is the PairIP wrapper (`com.pairip.application.Application`), `SignatureCheck` + `LicenseClient` are wired at `attachBaseContext`, `StartupLauncher` wraps framework factories, and `VMRunner.<clinit>` requests `System.loadLibrary("pairipcore")`.
- Virtualization footprint ≈ 0%: **20 VM-stub markers out of 422,621 method entries** (0.00473%) across 11 dex files, 110 integrity entry points, zero scan errors, complete coverage.
- Verdict: runtime hooking of an unmodified APK (the GrindrPlus model) is **structurally plausible again**; static repackaging/re-signing remains blocked by the signature check.
- Open caveats: the **ABI splits are unmeasured** (whether `libpairipcore.so` ships in any of the three ABI splits was never analyzed — the base split ships no native libs at all); the identities of the 20 stub methods are not recorded; the stub heuristic has documented blind spots.
- Both censuses (`samples/out/census.json`, `census-base.json`) were reproduced identically by re-run this session; the analyzer's 81-test suite passes.

**`docs/03` — Legacy combo audit (GrindrPlus v4.7.2-lineage × pinned Grindr)**

- 20 of 29 hooks (69%) target R8-reassigned short names (`vn.a`, `fo.k`, `sk.g`) and re-break on essentially every re-minified Grindr release — upstream release v4.4.0 existed solely to "add support" for one new Grindr version.
- Only 4 hooks (14%) are high-confidence survivors of a Grindr update (AllowScreenshots, SSLUnpinning, TimberLogging, StatusDialog — all OS/bundled-library API).
- The snapshot's compile-time pin is Grindr 26.0.1/149389 (the 25.21.1 in `version.json` is the update-spoof tracker, not the build pin); upstream is archived (2026-05-18) and the pinned build is ~9 months old.
- The binding constraint is the **server gate**, not the hooks: upstream's own record shows Grindr moving features server-side (v4.6.0) and version-gating login; verdict — the combo is at or past end-of-life.

**`docs/04` — Forkability review (GrindrPlus snapshot at `EOL` commit `aa497a0`)**

- Restarting from the snapshot is cheap (days — toolchain vendored in-tree); sustaining it is not (a days-to-weeks reverse-engineering sprint per Grindr release across ~26 obfuscated class pins + ~27 method pins, guided by 64 breadcrumb comments; zero automated tests).
- The post-PairIP verdict is downgraded to *attributed-but-not-demonstrated*: the 26.21.0 census (20/422,621 stubs) shows runtime hooking is structurally plausible, but with the native layer unmeasured it remains a research bet, not a fork.
- GPL-3.0 obligations are real and partly unmet by the snapshot itself: no per-file headers, attribution only in (absent) git history, and the `old_base` branch is unlicensed — a contamination hazard that must never be folded into a fork.
- Verdict: not worth forking as a living mod for current Grindr; marginal as frozen-version maintenance; genuinely valuable as reference architecture (hook framework, LSPatch pipeline) for targets that don't ship PairIP.

## Reproduction

All commands run from this repo root (`pairip-research/`); the in-repo
`pairip-research` symlink makes the `pairip-research/...` paths resolve. All
three were verified this session (2026-10-22):

```bash
pip install -r tools/pairip-audit/requirements.txt   # androguard 4.1.4 + pytest 8.4.2
python -m pytest pairip-research/tools/pairip-audit/tests -q   # 81 passed (synthetic fixtures; no real APK)
python pairip-research/tools/pairip-audit/run_audit.py <apk> --out census.json
```

For `<apk>` use a real APK or extracted split (e.g. the base split of an
APKMirror bundle); the recorded census for Grindr 26.21.0's base split
(`samples/out/census-base.json`, gitignored) was reproduced identically by
re-running the third command this session:
`pairipDetected=True pairipClasses=46 stubs=20/422621 (0.0%)`.
The unit suite uses faked androguard objects and synthetic zips — it needs no
APK and no network. Docs cite census facts as `docs/02` §2.

## Limitations

- **Static analysis only** (ROE §1). No APK was installed, run, hooked, or
  otherwise dynamically observed anywhere in this program; every behavioral
  claim (crash on tamper, license prompts, anti-frida activity) is sourced to
  public research via the dossier, not observed here (`docs/02` §7.1).
- **ABI splits unmeasured.** The three ABI split APKs of the 26.21.0 bundle were
  never opened; whether `libpairipcore.so` ships in any of them is unmeasured
  and asserted neither way. The base split contains no native libraries at all,
  and stub-method identities are not recorded by the census format
  (`docs/02` §7.2, §7.5; `docs/01` §8.1.8).
- **Policy verification runs against HackerOne's GraphQL API, not the rendered
  page.** The public policy pages are JS-rendered and return no content to plain
  fetches; quotes were verified against the GraphQL endpoint the page itself
  loads (42 of 59 fragments byte-exact, 17 matching at formatting level — none
  failed content-level verification; `docs/00` method section).
- Additional documented limits live in each deliverable (dossier provenance
  grades in `docs/01` §10; version-skew and mirror-provenance caveats in
  `docs/02` §7; single-snapshot scope of `docs/03`–`04`).

## Layout

```
docs/     numbered research deliverables (00–04)
tools/    pairip-audit analyzer package (src + tests + CI)
samples/  gitignored: cloned repos, downloaded APKs, analyzer output
ROE.md    rules of engagement and evidence rules
```

License: MIT for original code in `tools/`; documents are CC BY 4.0.
Third-party material in `samples/` keeps its upstream license (GrindrPlus is GPL-3.0).
