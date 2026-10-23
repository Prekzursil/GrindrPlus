# 04 — Forkability Review: Can GrindrPlus Be Resurrected?

**Date:** 2026-10-22
**Subject:** The archived [GrindrPlus](https://github.com/R0rt1z2/GrindrPlus) Xposed module, snapshotted in this repo at `samples/GrindrPlus/` (single `EOL` commit `aa497a0`, verified via `git log` this session).

**Provenance:** This document merges two independent code reviews supplied with this ask (cited below as **review A** and **review B**). All load-bearing claims were re-verified against the snapshot this session; the verification commands are listed in §7. Line references without an explicit "(review)" tag were read directly this session. Where the two reviews measured the same thing with different methodology, both numbers are reported and labeled.

---

## 0. TL;DR

- **Restarting from this snapshot is cheap; sustaining it is not.** A competent maintainer can reproduce a working APK for the pinned pre-PairIP Grindr **in days** — the toolchain is vendored (12 MB `lspatch.jar` + four `liblspatch.so` in-tree), deps are on public mavens, and the frozen target keeps the whole obfuscation map valid (review A).
- **Every Grindr release afterward is a manual reverse-engineering sprint**: ~26 obfuscated class pins + ~27 obfuscated method pins (review B's count of pin sites; review A counts 82 references to 68 unique `com.grindrapp.android.*` names plus ~14 two-letter packages) must be re-derived by a human with JADX, guided by 64 `// search for` breadcrumb comments — historically a days-to-weeks cycle per release (review A).
- **Zero automated tests.** `app/src` contains only `main/` (verified: `ls app/src`). CI is packaging automation on manual dispatch, not a quality gate. Every change is validated by smoke-testing a live Grindr account whose ban risk the upstream README itself documents (review A).
- **Post-PairIP Grindr is likely out of reach for this codebase — a verdict downgraded (2026-10-22) from categorical to attributed-but-not-demonstrated.** The maintainer's own EOL statement (news.json msg 197, full text read this session) says Grindr shipped Google PairIP VM protection, no public bypass exists, and the team lacked "the time nor expertise" to build one; the dossier grades that attribution "best-supported explanation… not demonstrated method-by-method" and records that Java hooking demonstrably still works on the non-virtualized `com.pairip` license classes (`docs/01-pairip-dossier.md` §4, §5 Tier 1). The same-day APK census of Grindr 26.21.0 measured only 20 VM-stub methods out of 422,621 in the base split and concluded runtime hooking is "structurally plausible again," with named caveats — the unmeasured native layer, the 20 unidentified stubs, and the heuristic's blind spots (`docs/02-feasibility-study.md` §4). A forker targeting current Grindr therefore does not face a *proven* wall before hook #1 fires, but an unsolved and unmeasured devirtualization risk of unknown width.
- **GPL-3.0 obligations are real and partly unmet by the snapshot itself**: redistributed APKs carry corresponding-source duties; the sources carry no per-file copyright headers; the `old_base` branch is explicitly unlicensed and must never be folded into a fork; the README's "don't kang this" request cannot override GPL-3.0 §10.
- **Verdict:** as a living mod for current Grindr — **not worth forking** (blocked by PairIP). As a frozen-version maintenance project — viable for a part-time reverse-engineer who accepts an unbounded, event-driven treadmill that Grindr's servers can end at any moment (they have already discontinued old versions server-side, news.json msg 177). As a reference implementation of Xposed-module architecture and the LSPatch packaging pipeline — genuinely valuable, and that value transfers to targets that don't ship PairIP.

---

## 1. Architecture assessment

### 1.1 What the codebase is

One Gradle module (`:app` only, `samples/GrindrPlus/settings.gradle`) ships **three artifacts from one APK** (review A):

1. a Compose **manager app** (launcher UI, installer pipeline, settings);
2. an **LSPosed module** (AndroidManifest `xposedmodule` meta-data + `assets/xposed_init`);
3. an **LSPatch-embeddable mod** for no-root installation, using the vendored JingMatrix/LSPatch nightly.

Scale (review B, consistent with this session's file survey): 124 Kotlin files, ~20,051 LOC, comprising the injected Xposed runtime, the Compose manager UI (~4,300 lines including a 1,002-line `SettingsScreen`), a Room persistence layer, an AIDL socket bridge (`bridge/BridgeService.kt` at 519 lines + `bridge/BridgeClient.kt` at 617 lines, both verified this session), and the LSPatch patcher pipeline.

### 1.2 Strengths

- **Clean layering for an Xposed mod.** `XposedLoader.kt` (39 lines, read this session) is a thin entry — package gate, signature spoof, one `Application.attach` hook — delegating to the `GrindrPlus` orchestrator object (`GrindrPlus.kt:128-233`, review A), which drives a small framework (`Hook`/`Hooker`/`HookAdapter`/`HookManager` in `utils/`) that feature hooks plug into. Hooks are self-contained one-file features: **29 files, 4,174 lines** under `hooks/` (verified this session by per-file `wc -l`).
- **Runtime-configurable with per-clone namespacing.** `HookManager.kt` initializes only hooks enabled in `Config` (verified: the `hooks.values.forEach { … hook.init() }` loop at `utils/HookManager.kt:80-88`); `Config.kt:32-61` (review A) carries a one-time migration to a multi-clone JSON layout so multiple patched Grindr clones keep independent settings.
- **Dual distribution from one codebase**, with a composable installer step pipeline — storage check → downloads → extract → patch/clone/sign → install — with progress printing, telemetry events, and cleanup-on-failure (`manager/installation/Installation.kt:42-54, 144-153`, review A).
- **Defensive runtime engineering**: uncaught-exception crash logging (`GrindrPlus.kt:647-673`, read this session), a hard version-mismatch gate that disables the module with an explanatory dialog instead of crashing obscurely (`checkVersionCodes` at `GrindrPlus.kt:415-436`, read this session), a bridge watchdog with auto-reconnect (`BridgeClient.kt:66-97`, review A), and an `InstanceManager` that captures obfuscated singletons via constructor hooks rather than repeated reflection walks (review A).
- **Authenticated API access without touching credentials**: the injected module reproduces Grindr's HTTP stack by intercepting its own OkHttp client with the live `userSession`/`deviceInfo` instances (`GrindrPlus.kt:322-331` and `core/http/Interceptor.kt:22-62`, review A; `Interceptor.kt`'s auth-header assembly read this session).
- **Honest project hygiene**: GPL-3.0 `LICENSE` (verified: full text, "GNU GENERAL PUBLIC LICENSE, Version 3"), upstream credits in the README, an age-verification **compliance** dialog that refuses to bypass (`GrindrPlus.kt:502-538`, read this session; removal of the old bypass code documented in news.json msg 166), and a public EOL statement rather than silent abandonment.

### 1.3 Weaknesses

- **Single-module monolith.** Manager UI, APK patcher, AIDL bridge, and injected runtime are fused into one artifact — every manager-side tweak forces re-signing and re-shipping the Xposed module, and the module cannot be built or tested independently of the Compose app (review A).
- **God-object global state.** The `GrindrPlus` object (673 lines, verified) holds ~15 mutable globals (`myProfileId`, `shouldTriggerAntiblock`, `isImportingSomething`, a `currentActivity` weak reference, a 19-point PCHIP spline at `GrindrPlus.kt:82-103` per review A) that hooks read/write cross-module — hard to reason about, untestable in isolation. A remote `spline.json` is fetched from the upstream repo at runtime (`GrindrPlus.kt:122-123`, read this session: `raw.githubusercontent.com/R0rt1z2/GrindrPlus/refs/heads/master/spline.json`), a dependency outside any fork's control.
- **Persistence split-brain.** Mod config is a JSON file in the *manager's* storage (`Config.kt:95-115`, `BridgeService.kt:34`, review A), while feature data lives in a Room DB created inside the *Grindr* process: `GPDatabase` at database v5, `exportSchema=false`, `fallbackToDestructiveMigration(false)` — no migrations exist, so any schema bump crashes on open unless the user flips the manual `reset_database` flag (`GrindrPlus.kt:344-350`, read this session). `DatabaseHelper.kt:12-14` (read this session) additionally locates Grindr's own SQLite by filename prefix `"grindr_user"` — fragile to Grindr renaming its DB.
- **No error isolation between hooks.** `hook.init()` is called bare inside `runBlocking` (`HookManager.kt:81-88`); only 11 of 29 hook files contain any `try`/`runCatching`, and none wraps `init()` from the start (review A, grep sweep). One renamed class in one enabled hook throws up to the single catch in `GrindrPlus.initializeCore` (`GrindrPlus.kt:223-232`, read this session) and kills the **entire module**, not just that feature.
- **Minor but real** (review A, spot-verified): release builds ship unminified (`isMinifyEnabled = false` at `app/build.gradle.kts:53`) despite proguard rules; the LSPatch signing keystore password is hardcoded (`"password"`/`"alias"` at `manager/installation/steps/PatchApkStep.kt:133-139`, read this session); `app/build.gradle.kts:1` imports AGP-internal `BaseVariantOutputImpl` (verified); `WebSocketAlive` sits commented out mid-list at `HookManager.kt:68` (verified) rather than removed.

---

## 2. Hook-infrastructure quality

The hook framework itself is the best part of this codebase, and both reviews agree on it independently.

- **Uniform hook abstraction.** An abstract `Hook` base class (name/description, `init`/`cleanup`, per-hook enable persisted via `Config`) with a central `HookManager` registry — all 29 hooks follow one pattern (`utils/Hook.kt`, 37 lines; `utils/HookManager.kt`, 103 lines — both verified this session). Adding or disabling a hook is a small, well-bounded edit (review B).
- **`Hooker.kt` is a genuinely good ergonomic layer over raw Xposed** (review A): BEFORE/AFTER stages with filters (`Hooker.kt:14-31`, spot-read this session), `hookAllMethods`/`hookAllConstructors` wrappers, self-unhooking ephemeral hooks for one-shot interception (`Hooker.kt:100-138`), and Kotlin extensions on `Class`/`Member` (`Hooker.kt:141-180`; file is 179 lines, verified) that make hook bodies read declaratively.
- **`HookAdapter.kt`** (119 lines, verified) is a typed facade over `XC_MethodHook.MethodHookParam`: argument casting with reflective conversion and primitive-default fallback (lines 24-39, 94-119), `setArg`/`setResult`/`setThrowable`, and `invokeOriginalSafe` (lines 74-84) — removing most of the boilerplate and `ClassCastException` hazards that plague raw Xposed code (review A).
- **Fails loud instead of silently breaking.** `checkVersionCodes()` compares the installed Grindr `versionName`/`versionCode` against `BuildConfig.TARGET_GRINDR_*` and disables the module with an explicit Version Mismatch dialog rather than letting stale obfuscated hooks crash the app (`GrindrPlus.kt:415-436`, read this session; review B). This is the right safety design for an obfuscation-coupled mod — but note it interacts badly with the missing hook isolation (§1.3): a mismatch that slips past the gate takes down all 29 hooks at once.
- **The breadcrumb convention is the project's single most valuable maintenance asset.** `docs/README.md` codifies it (review B): *"When targeting an obfuscated class/method, leave a comment with some sensible code snippet used to search for the class in newer versions of the G app."* The code carries **64 `// search for …` comments across 21 files** (verified this session: `grep -rn "search for" app/src/main/java` → 64 matches in 21 files). This turns each Grindr update from archaeology into a guided JADX grep — when the breadcrumb exists and is current.

**The framework's blind spot:** the abstraction makes hooks *easy to write*, which is exactly why the codebase accumulated 29 hooks' worth of obfuscated pins with no automated way to re-derive them. The framework does not, and cannot, protect against the treadmill in §3 — `Hooker` will happily hook `"W"` on the wrong class after a re-minification rename.

---

## 3. The version-mapping treadmill

This is the project's structural liability, and it is measured, not hypothetical.

### 3.1 The scale of the coupling

Two complementary measurements from the two reviews (different units, both plausible against this session's spot checks):

| Measurement | Count | Source |
|---|---|---|
| References to unique `com.grindrapp.android.*` names | 82 refs / **68 unique** | review A (grep across `app/src/main/java`) |
| Fully-qualified `com.grindrapp.android…` strings, unique | **71** (my recount this session, `grep -hon … \| sort -u` — same order of magnitude, methodology differs) | this session |
| Two-letter obfuscated *package* names (`x90.e`, `nb.d`, `mo.b1$a`, `as.r`, `ek.y`, `nz.e`, `q30.f`, `vn.a`, `fo.k`, `nf0.u1` …) | **~14** pinned declarations | review A |
| Obfuscated **class-name pins** | **26** | review B |
| Obfuscated **method-name pins** (single letters: `hook("W")`, `invokeMethodSafe(userSession, "w")` …) | **27** | review B |
| `// search for …` breadcrumbs guiding re-derivation | **64 across 21 files** | both reviews; verified this session |
| Per-hook patch documentation | **2 of 29** (`docs/patches/anti_block.md`, `online_indicator.md` only — verified: `ls docs/patches/`) | both reviews |

### 3.2 Concrete examples (read this session)

- `hooks/EnableUnlimited.kt` pins `paywallUtils = "x90.e"` (breadcrumb: `app_restart_required`), `persistentAdBannerContainer = "nb.d"` (breadcrumb: a `ViewBindings.findChildViewById` snippet), `subscribeToInterstitialsList = ["mo.b1$a"]`, and hides UI via `com.grindrapp.android.ui.tagsearch.ProfileTagCascadeFragment$b` / `…ui.browse.CascadeFragment$b` resource-name lists. It then hooks **one-letter methods** on `userSession`: `"W"` (fakes the roles list) and `"D"` (prevents the faked roles leaking into HTTP headers).
- `core/http/Interceptor.kt:30-60` re-derives Grindr's auth headers by reflecting `userSession` methods `"w"` (auth-token StateFlow), `"D"` (roles string) and a `deviceInfo` lazy field `"d"` — each with a `search for` breadcrumb. If any of these letters shift, the module's HTTP client silently sends empty/wrong headers.
- `hooks/FeatureGranting.kt:20` pins `isFeatureFlagEnabled = "q30.f"` with the breadcrumb `implements IsFeatureFlagEnabled {` — the canonical example (review B) of a pin that a guided JADX grep can re-find in minutes.

Every one of these names changes on each R8 re-minification (i.e., each Grindr release), and every one must be manually re-found by decompiling. There is **no automated mapping resolver, no smali-diff pipeline, no string-constant search tooling** in-repo (review B); the README itself warns "Each Grindr Plus release supports only a specific Grindr app version" (review B).

### 3.3 The treadmill has a history, and it ended

- news.json msg 177 (read this session): *"Grindr has recently discontinued version v25.12.1, which means the current mod is no longer functional."* — proof that even **frozen** clients break when Grindr's servers change behavior; the code carries the scars (server-computed `onlineUntil` replacing `lastSeen`, `docs/patches/online_indicator.md`; a server-enforced paywall dialog at `EnableUnlimited.kt:129-152` per review A).
- news.json msg 184: the main developer taking a break. msg 197 (read this session): Grindr shipped Google PairIP protection; *"There is no bypass publicly available online right now, and we don't have the time nor the expertise required to implement one… this is probably the end."* The treadmill's terminal failure mode — hook targets that may no longer exist as hookable Java at all — has already happened upstream.
- Version-pin drift at the final commit (verified this session): `app/build.gradle.kts:16-17` pins Grindr **26.0.1 / 149389** into `BuildConfig` (via the `buildConfigField` blocks at lines 32-43), while root `version.json` still says **25.21.1 / 148541** and `manifest.json` serves **25.20.0-147239** APK URLs. Three files, three versions, one stale — `version.json` is not wired into Gradle at all, and the update workflow is `fetch_version.py` scraping APKMirror HTML (lines 33-77, review A; brittle to layout changes) followed by hand-editing `build.gradle.kts`. A forker cannot tell which pin is authoritative without rebuilding.

---

## 4. Engineering effort estimate to resume on pre-PairIP versions

Merging both reviews' resumption-cost analyses:

### 4.1 One-time restart: days

The clone is complete and self-contained — the 12 MB `lspatch.jar` and four `liblspatch.so` files are vendored in-tree (`app/libs/`, `app/src/main/assets/lspatch/so/`), dependencies are on public mavens, and CI is a plain GitHub Actions script (review A). Because the target Grindr build is frozen, the entire obfuscation map stays valid — no reverse engineering needed to reproduce a working APK for the pinned 26.0.1 (149389). Immediate to-dos: re-establish CI keystore/Telegram secrets a fork won't inherit; decide which version pin (§3.3) is authoritative.

### 4.2 Recurring, per Grindr release: a days-to-weeks reverse-engineering sprint

Per release (both reviews): fetch the new APK (`fetch_version.py`, APKMirror only) → decompile with JADX (`docs/env_setup.md`) → manually re-derive the pin set (§3.1) across the 29 hooks, guided by the 64 breadcrumbs and 2 patch docs → bump `app/build.gradle.kts:16-17` and reconcile the drifted `version.json` → smoke-test all 29 hooks **by hand** on LSPosed/LSPatch hardware. With zero automated tests and CI that triggers on `workflow_dispatch` only (no push/PR builds, no test or lint step — review B), every regression is caught on-device or by users. The upstream release cadence in news.json shows this cycle repeating roughly per Grindr release, historically days-to-weeks each time (review A).

### 4.3 Continuous, on frozen clients: event-driven firefighting

Even pinned forever, the mod decays (review A): server-side discontinuation of old versions (msg 177), server-enforced behavior changes, dead auto-download infrastructure (msg 198: the download server is being shut down for cost — `manifest.json`'s `gplusapks.airdns.org` URLs and the version selector are dead weight that must be replaced with the manual install-custom flow or new hosting). A resumer inherits a live-account smoke-test loop whose ban risk the upstream README documents — or must first build a test harness the project never had.

### 4.4 Toolchain rot

`setupLSPatch` (`app/build.gradle.kts:130-166`, read this session) regex-scrapes a **nightly.link preview page** for an *unpinned* JingMatrix/LSPatch nightly at build time, using `mkdir`/`wget`/`unzip`/`mv`/`zip` — Unix-only commands, no hash pinning (review B). Historical builds are not reproducible; the upstream artifact can vanish or change silently (partially mitigated by the vendored jar/`.so` files — but the "Update LSPatch" CI step depends on the scrape). Android SDK/AGP rot accumulates silently on top (`BaseVariantOutputImpl` import is already a build-rot flag).

### 4.5 Net estimate (review A, concurred by B)

- **Restart:** ≈ days for a competent maintainer.
- **Sustained maintenance:** ≈ a part-time reverse-engineer plus release engineer, with **unbounded per-incident cost** whenever Grindr's servers change behavior for old clients.
- **Anything post-PairIP:** an unsolved devirtualization research problem that the original author explicitly declined — not an effort estimate but a research bet with no public solution (news.json msg 197).

---

## 5. GPL-3.0 obligations for forkers

The `LICENSE` file is the full GPL-3.0 text (verified this session). What that means for anyone picking this up (review B, confirmed against files read this session):

1. **The whole fork stays GPL-3.0**; relicensing is not permitted. The README's request not to "copy it and release it as your own (kanging)" (`README.md:288`) is a courtesy ask that **cannot override GPL-3.0 §10** (no further restrictions) — compliant forking and redistribution are permitted; what's prohibited is relicensing and removing attribution.
2. **Corresponding source accompanies every binary distribution.** CI-built APKs posted to Telegram *are* distributions; the source-disclosure duty lands on the forker for each APK shipped (GPL-3.0 §4-§6).
3. **Attribution is currently only in git history — and this clone doesn't have it.** The Kotlin sources carry no per-file copyright headers (review B), and this snapshot is a single `EOL` commit (`aa497a0`, verified via `git log`) that does not preserve contributor history. A forker must **fetch full history from the (archived) upstream** to satisfy notice-retention duties (§5-§6).
4. **The `old_base` branch is a contamination hazard.** `README.md:286` (read this session): the `old_base` branch contains the original author's code and is *"not subjected to any license"*. Unlicensed code must **never** be folded into a GPL fork.
5. **Vendored binaries ship without a license inventory.** `app/libs/LSPosed-api-*.jar`, `lspatch.jar`, and `assets/lspatch/so/*/liblspatch.so` are bundled with no in-repo NOTICE file documenting their licenses (review B). A distributor is shipping these binaries and should inventory them before redistributing.
6. **Trademark is a separate axis of risk**: the "Grindr" name and the app's redistribution itself carry risk independent of copyright, and the mod's ToS/ban exposure is documented by upstream itself (README FAQ, review A).

---

## 6. Verdict: is forking worthwhile?

**Split by goal — because the answer flips completely depending on which goal you mean.**

### 6.1 As a living mod targeting *current* Grindr: **No — but on attributed, not measured, grounds.**

Likely blocked in practice; "blocked before it starts" (this doc's earlier wording) overstated what the corpus shows. PairIP VM protection (news.json msg 197) means the plain-Java hook targets this module's entire approach depends on *may* no longer exist — that is the maintainer's attribution, graded "best-supported explanation, not demonstrated per-method" by `docs/01-pairip-dossier.md` §4, which also records that Java hooking demonstrably still works on the non-virtualized `com.pairip` license classes (pairipfix, LSPosed; `docs/01` §5 Tier 1). The same-day census measured the Grindr 26.21.0 base split at 20 VM stubs / 422,621 methods and called runtime hooking "structurally plausible again," with the caveats that the native layer is unmeasured and the 20 stubs are unidentified (`docs/02-feasibility-study.md` §4). What a forker actually faces is therefore not a demonstrated wall but a research bet: no published general devirtualization/bypass capability exists (news.json msg 197; `docs/01` §5–§6), and whether it blocks *this* module's hooks is unmeasured. This is a research bet, not a fork.

### 6.2 As a frozen-version maintenance project (pre-PairIP 26.0.1): **Marginal — only for the right person.**

The economics (§4): days to restart, then a recurring per-release RE sprint plus event-driven firefighting against a backend that has already demonstrated it will kill old clients server-side (msg 177). The binding constraint is not effort but **server-side login refusal for old clients** — no amount of client hooking fixes that (see sibling doc `docs/03-legacy-combo-audit.md`, which concludes authentication is the terminal risk for the pinned combo). Fork only if all of these hold: (a) scope is explicitly "maintain the frozen pre-PairIP combo," (b) you have R8/JADX reverse-engineering skill and accept an unbounded treadmill, (c) you operate GPL compliance properly (§5), and (d) you treat the whole thing as disposable the day Grindr enforces client upgrades.

### 6.3 As reference material: **Yes — this is where the real value is.**

The parts that are *not* coupled to Grindr's obfuscation are genuinely reusable: the `Hooker`/`HookAdapter`/`HookManager` framework (§2), the version-mismatch safety gate, the breadcrumb documentation convention, the multi-clone config layout, the LSPatch packaging/signing pipeline, and the dual LSPosed/LSPatch distribution design. All of that transfers to Xposed targets that don't ship PairIP. Harvest the patterns; don't inherit the treadmill.

### 6.4 First tasks if you do fork (from both reviews + this session's findings)

1. Resolve the version-pin drift: make one source of truth (build.gradle vs `version.json` vs `manifest.json` disagree — §3.3).
2. Replace the dead auto-download path (msg 198) with the manual install-custom flow or your own hosting.
3. Re-establish CI secrets; hash-pin LSPatch or freeze on the vendored jar; make `setupLSPatch` non-Unix-only or drop it.
4. Remove the hardcoded keystore credentials (`PatchApkStep.kt:133-139`).
5. Add error isolation around `hook.init()` (`HookManager.kt:80-88`) so one stale pin doesn't kill all 29 hooks.
6. Fetch full upstream git history for GPL attribution; add a NOTICE for the vendored binaries; never merge `old_base`.
7. As you re-derive pins per release, write the missing 27 patch docs — the convention exists (`docs/README.md`); it was just never followed.

---

## 7. Sources & verification log

**Sources:**

- **Review A and Review B** — the two independent code reviews of `samples/GrindrPlus/` supplied with this ask (provenance stated in the header above; where they measured the same thing differently, both numbers are reported and labeled). All load-bearing claims were re-verified against the snapshot this session — commands below.
- **The snapshot itself** — `samples/GrindrPlus/` at the single `EOL` commit `aa497a0` (verified via `git log`). Files read directly this session include `README.md`, `LICENSE`, `news.json` (msgs 166, 177, 184, 197, 198 extracted in full), `version.json`, `manifest.json`, `settings.gradle`, `app/build.gradle.kts`, the hook corpus (`app/src/main/java/com/grindrplus/hooks/`, 29 files), `PatchApkStep.kt`, `GrindrPlus.kt`, `HookManager.kt`, `Hooker.kt`, `HookAdapter.kt`, `Hook.kt`, `Config.kt`, `XposedLoader.kt`, `BridgeService.kt`, `BridgeClient.kt`, and `docs/patches/`.
- **Upstream (archived) project** — https://github.com/R0rt1z2/GrindrPlus (archived 2026-05-18), as the review subject; its release-notes record is cited via `docs/03-legacy-combo-audit.md` §4.
- **Sibling deliverables cross-cited** — `docs/01-pairip-dossier.md` (§4 attribution grade; §5 Tier-1 pairipfix evidence), `docs/02-feasibility-study.md` (§4 census verdict on 26.21.0), `docs/03-legacy-combo-audit.md` (authentication-is-the-binding-constraint conclusion).

**Verification log (commands run this session — all against `samples/GrindrPlus/` unless noted; working tree at the single EOL commit):**

| Claim | Command | Result |
|---|---|---|
| No test source sets | `ls app/src` | only `main/` |
| Version drift | `cat version.json`; `sed -n '1,30p' app/build.gradle.kts` | version.json 25.21.1/148541 vs build.gradle.kts:16-17 → 26.0.1/149389 |
| Hook corpus | per-file `wc -l` loop over `hooks/*.kt` | 29 files, 4,174 lines |
| Breadcrumb count | `grep -rn "search for" app/src/main/java` | 64 matches across 21 files |
| Unique obfuscated names | `grep -hon "com\.grindrapp\.android[A-Za-z0-9_.$]*" … \| sort -u \| wc -l` | 71 unique strings (cf. review A's 68 — different regex/methodology) |
| news.json content | python parse of `news.json` | 23 messages; full text extracted for msgs 166, 177, 184, 197, 198 |
| EOL commit | `git log --oneline -3` | single commit `aa497a0 EOL` |
| Key file sizes | `wc -l` on GrindrPlus.kt, HookManager.kt, Hooker.kt, HookAdapter.kt, Hook.kt, Config.kt, XposedLoader.kt, BridgeService.kt, BridgeClient.kt | 673 / 103 / 179 / 119 / 37 / 266 / 39 / 519 / 617 |
| Obfuscated pins | `sed -n` reads of `EnableUnlimited.kt`, `Interceptor.kt`, `FeatureGranting.kt` | `x90.e`, `nb.d`, `mo.b1$a`, method pins `W`/`D`/`w`/`d`, `q30.f` + breadcrumbs — all present at cited locations |
| Hardcoded keystore | `sed -n '130,140p' …/PatchApkStep.kt` | `"password"`, `"alias"`, `"password"` literals |
| Patch docs coverage | `ls docs/patches/` | README + anti_block.md + online_indicator.md only (2 of 29) |
| Quality-gate absence | `find . -name "*Test*.kt" -o -name "detekt*" -o -name ".editorconfig" -o -name "CONTRIBUTING*" -o -name "CHANGELOG*"` | no hits (outside `.git`) |
| License | `head -3 LICENSE`; `grep -n "old_base\|kanging\|GPL" README.md` | GPL-3.0; README:286 `old_base` unlicensed; README:288 kanging request |
| Dead download URLs | `head -20 manifest.json` | `gplusapks.airdns.org` URLs for 25.20.0-147239 |
| Spline remote | `sed -n '122,126p' GrindrPlus.kt` | raw.githubusercontent.com/R0rt1z2/GrindrPlus master spline.json |

**Not run / not possible this session:** no Gradle build was attempted (would require the Unix-only `setupLSPatch` path and network fetches; out of scope for a doc-merge ask). No APK was patched or smoke-tested; all runtime-behavior claims trace to the two supplied reviews and upstream's own news.json statements.

*Cross-references:* `docs/00-scope-verification.md` (program scope), `docs/03-legacy-combo-audit.md` (per-hook survival analysis of the pinned combo; records upstream archive date 2026-05-18 and the authentication-is-the-binding-constraint conclusion referenced in §6.2).
