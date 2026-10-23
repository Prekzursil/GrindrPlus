# 03 — Legacy Combo Audit: GrindrPlus (v4.7.2 lineage) × Grindr 25.21.1

**Date:** 2026-10-22
**Scope:** All 29 Xposed hook files in the pinned module snapshot (`samples/GrindrPlus/app/src/main/java/com/grindrplus/hooks/`, 29 `.kt` files verified present this session), audited as 29 hook-audit rows supplied with this ask (all `File.kt:line` references below come from those rows unless marked otherwise).
**External source:** GrindrPlus upstream release notes, fetched this session from <https://github.com/R0rt1z2/GrindrPlus/releases> (page 1: the 10 most recent releases, v4.2.0 → v4.7.2).

---

## 0. TL;DR

- **20 of 29 hooks (69%) target at least one R8-reassigned short name** (`vn.a`, `fo.k`, `sk.g`, single-letter fields). These re-break on essentially **every** re-minified Grindr release — upstream release v4.4.0 existed solely to "add support" for one new Grindr version.
- **Only 4 hooks (14%) are high-confidence survivors** of a Grindr app update: `AllowScreenshots`, `SSLUnpinning`, `TimberLogging`, `StatusDialog` — all hook OS / bundled-library public API, none hook Grindr code.
- Upstream's own release notes name **at least 9 of these 29 hooks as broken at some point** in v4.2.0→v4.7.2, and document Grindr **moving chat filters server-side in v4.6.0** — proof the server can kill client-hooked features with no client-side counter.
- The upstream repo is **archived (read-only) since 2026-05-18**; its last release (v4.7.2, 2026-01-28) targeted Grindr **25.20.0**, while this snapshot's compile-time pin is Grindr **26.0.1 / 149389** (`app/build.gradle.kts:16-17`; the **25.21.1**/148541 in `version.json` is the update-spoof tracker, not the build pin — §1, corrected 2026-10-22). As of 2026-10-22 the pinned Grindr build (26.0.1, released 2026-01-21) is ~9 months old: the combo must be treated as **at or past end-of-life**, gated or one server config-flip away from login refusal.
- Best case for a *newer* Grindr: the 4 framework hooks keep working mechanically, plus degraded fragments of ~6 mixed/SDK hooks — **but only while the old client can still authenticate**, which is the binding constraint, not the hooks.

---

## 1. Pinning facts (what exactly is pinned)

| Fact | Value | Source |
|---|---|---|
| Compile-time build pin (the actual target) | **`26.0.1` / versionCode `149389`** | `samples/GrindrPlus/app/build.gradle.kts:16-17` (read this session; flows into `TARGET_GRINDR_VERSION_*`) |
| `version.json` value (update-spoof tracker, **not** wired into Gradle) | `25.21.1` / versionCode `148541` | `samples/GrindrPlus/version.json` (read this session; adjudicated in `docs/01` §4/§10.4 and `docs/04` §3.3) |
| Snapshot's own version string | `4.8.0-...` (unreleased lineage) | `samples/GrindrPlus/app/build.gradle.kts:24` |
| Build pins Grindr version at compile time | `26.0.1` / `149389` via `TARGET_GRINDR_VERSION_NAMES` / `TARGET_GRINDR_VERSION_CODES` build-config fields | `app/build.gradle.kts:16-17,34,40` |
| Last upstream release | **v4.7.2-25.20.0** (2026-01-28), shipped against Grindr **25.20.0 (147239)** | release notes (WebFetch) + `samples/GrindrPlus/manifest.json` (both APK URLs pinned to `25.20.0-147239`) |
| Upstream repo status | **Archived 2026-05-18, read-only** — no future releases | release notes (WebFetch) |

**Version-skew note (important, corrected 2026-10-22):** the ask names the combo "module v4.7.2 + Grindr 25.21.1", but upstream v4.7.2 was built for Grindr 25.20.0, and the audited tree — the v4.7.2 code lineage, self-versioned 4.8.0 — is **re-pinned at compile time to Grindr 26.0.1 / 149389** (`app/build.gradle.kts:16-17`), past 25.21.0/25.21.1 and 26.0.0 to the first 26.x release. The `25.21.1`/`148541` figure from `version.json` is the update-spoof tracker — the latest-version value scraped from APKMirror and fed to the `DisableUpdates` hook — not a build pin and not wired into Gradle (adjudicated in `docs/01` §4/§10.4 and `docs/04` §3.3; this doc previously repeated the conflation and now applies the correction). In other words, this snapshot was *already* past the last upstream-supported Grindr version on the day it was pinned, and the upstream repair loop that historically fixed it (§4) ended when the repo was archived.

---

## 2. Full per-hook table (29 rows)

Kind and versionProof are from the ask's audit rows; target/line refs are from those rows. Spot-checks this session confirmed the files and their build-specific "search for" comments exist (e.g. `fo.k` at `hooks/ChatTerminal.kt:15`, `vn.a` at `hooks/ChatIndicators.kt:14` and `hooks/LocalSavedPhrases.kt:26`, `to.p1` at `hooks/EmptyCalls.kt:11`, `tk.a` at `hooks/UnlimitedAlbums.kt:40`).

| # | Hook | Kind | Proof | Primary hook targets (audit-row refs) | Survival driver / break trigger |
|---|------|------|-------|----------------------------------------|--------------------------------|
| 1 | AllowScreenshots.kt | framework | **high** | `android.view.Window.setFlags`, `Activity.registerScreenCaptureCallback` (API 34+), `ContentResolver.registerContentObserver` media-host cancel (:18–36) | OS classes only — survives any Grindr update. Breaks only via Android-level change; note it blocks ALL media content-observer registrations process-wide, not just Grindr's |
| 2 | ChatIndicators.kt | mixed | low | `retrofit2.Retrofit.create` AFTER → blacklist proxy for obfuscated Grindr class `vn.a` / `v4/chatstatus/typing` (:14, 22–36) | Hook *site* stable, but blacklist is built from the R8 name `vn.a`; after re-minification `mapNotNull` yields an empty blacklist and the proxy **silently blocks nothing** |
| 3 | DisableShuffle.kt | grindr-internal | low | `ui.browse.v$g` / `v$j` obfuscated UI-state ctors, fields `a`–`j` (:16–31) | Both targets R8 inner classes (found by string search per repo comments); regenerated every re-minified release |
| 4 | ExpiringMedia.kt | grindr-internal | medium | 5 `com.grindrapp.*` chat-model getters forced to `MAX_VALUE`; `getUrl` AFTER → saved file (:36–84) | Full un-minified names (likely keep rules) but Grindr-owned model shape; also reflects `mediaId`/`url` fields (:83–84) |
| 5 | NotificationAlerts.kt | grindr-internal | low | `cy.g.a` BEFORE → null (:11, 14–17) | Two-char R8 name, located via build-specific string `'notification_reminder_time'` |
| 6 | QuickBlock.kt | grindr-internal | low | `profileV2.g.y` AFTER (menu inject), `gc0.b.R` BEFORE (profileId scan); reflects fields `b`/`p` (:21–45) | Obfuscated classes + single-letter fields; upstream history shows this hook breaking and being restored twice (§4: v4.3.1, v4.5.0) |
| 7 | TimberLogging.kt | framework | **high** | `Timber$Forest.v/d/i/w/e/wtf` (3 overloads each), `Timber$Tree.log` (:22–146) | Bundled 3rd-party lib, public API stable for years; fails only if Grindr drops Timber. No-op unless module `BuildConfig.DEBUG` (:17–19); reads impl field `explicitTag` |
| 8 | WebSocketAlive.kt | grindr-internal | low | SafeDK internals, `WebSocketClientImpl.disconnect/d/onClosed/onFailure`, `Ab.p.a`; reflects fields `g`/`c`, method `b(String)` (:29–202) | All targets inside the APK incl. obfuscated factory + private letters; upstream itself listed "Keep Alive Websocket" as **nonfunctional at v4.7.1** (§4) |
| 9 | AntiBlock.kt | grindr-internal | low | `ConversationDeleteNotification.<init>`, `vb0.w.T`, `yx.c.b`, `tn.c.b` (:33–99) | 3 R8 short names + single-letter methods; file's own comments (:26–28) give the smali search strings needed per build. Broken at v4.7.1, fixed in v4.7.2 (§4) |
| 10 | ChatTerminal.kt | grindr-internal | low | `fo.k.l` BEFORE + reflective chat-model field chain (:15–23) | Maximally build-pinned: one R8 class + one single-letter method |
| 11 | DisableUpdates.kt | mixed | low | Play Core `AppUpdateInfo.updateAvailability/isUpdateTypeAllowed` + `zzm.zza`; Grindr `rz.v.b`, `AppConfiguration.<init>`+field `d`, `as.r.<init>` **user-agent rewrite** (:30–114) | Play Core public API durable; `zzm.zza`/Grindr pins are per-build. The `as.r` UA rewrite is the anti-force-update lever analyzed in §5 |
| 12 | FeatureGranting.kt | mixed | low | `q30.f.a` flag gate, `Feature.isGranted`, `distance.a$e.<init>`, `UpsellsV8`/`Inserts`/`Tap` models; androidx `AlertDialog$Builder.show` + obfuscated field `P` (:35–98) | One genuine androidx hook, but it reads obfuscated field `P` ⇒ effectively build-pinned too |
| 13 | OnlineIndicator.kt | grindr-internal | low | `nf0.u1.a`, `q30.f.a`, `ProfileUtilsV2.b` (:21–40) | Two R8 names + single-letter method; upstream **fixed this hook in v4.7.2**, i.e. it broke on the prior Grindr bump |
| 14 | SSLUnpinning.kt | framework | **high** | `OkHttpClient$Builder.<init>` trust-all, `certificatePinner` DO_NOTHING, conscrypt `TrustManagerImpl.verifyChain` (:22–68) | Stable public API across OkHttp 3/4/5 (bundled un-renamed) + OS-level conscrypt; unaffected by Grindr app updates |
| 15 | UnlimitedAlbums.kt | grindr-internal | low | `tk.a` service via 6 album endpoints; `Album`/`SpankBankAlbum` ctors; reflective `AlbumsList` (:53–545) | R8 service name + REST path scheme; upstream fixed its crashes in v4.7.2 (§4) |
| 16 | AntiDetection.kt | framework | medium | 6 public SDK `isEmulator`/`isRooted` methods + 2 Crashlytics `AutoValue_*` ctors mutating `setArg(2)`/`setArg(5)` (:12–79) | SDK publics durable; the 2 ctor arg indices are pinned to the bundled Crashlytics model and break if fields reorder |
| 17 | DisableAnalytics.kt | mixed | medium | Braze / Firebase Analytics / Crashlytics / IronSource / Vungle / Unity publics + obfuscated Fyber `i.a` (:13–54) | 6/7 stable documented SDK APIs; Fyber piece re-breaks per obfuscation → feature **degrades partially, not totally** |
| 18 | EmptyCalls.kt | grindr-internal | low | `to.p1.P` = `IndividualChatNavViewModel.isTalkBefore` → true (:11–17) | R8 class + method; comment maps it via build-specific search |
| 19 | LocalSavedPhrases.kt | mixed | low | `Retrofit.create` AFTER; proxies `sk.j` / `vn.a` / `g10.a$b`; intercepts 4 phrase endpoints (:24–152) | `findClass` on obfuscated names — if any shifts, hook init dies wholesale |
| 20 | ProfileDetails.kt | grindr-internal | low | `ServerDrivenCascadeCacheState.getItems`, `ze0.n`, `vb0.m0$c`, `ProfileBarView.setProfile`, `DistanceUtils.c`, `ProfileViewState.getWeight` (:38–218) | 3/6 targets obfuscated + reflected letters `a`/`o`/`b`/`c`; corresponds to upstream's "exposed hidden profile details" (v4.3.1, §4) |
| 21 | SignatureSpoofer.kt | mixed | medium | 3× Firebase `getFingerprintHashForPackage` forced-hash; `ly.img.android.c.d`; FB `KatanaProxyLoginMethodHandler.tryAuthorize`; `ContextWrapper.getPackageName`; FCM `Metadata` (:11–97) | Named Firebase/FB SDK classes durable; the `ly.img` piece is obfuscated and re-breaks. Upstream: "Signature Spoofer" FB login **reportedly broken at v4.7.1** (§4) |
| 22 | UnlimitedProfiles.kt | grindr-internal | low | `getItems`, `ProfileTagCascadeFragment.R`, `getUpsellType`, `ProfileRepo.getProfilesWithPhotosFlow`, `browse.e0.invokeSuspend` (:21–122) | 2 obfuscated targets + reflective `Flow`/`Function2` plumbing; breaks on rebuild |
| 23 | BanManagement.kt | grindr-internal | low | `sk.g` (all methods), `w80.m.h`, `xk.a` ctor, `BannedFragment.onViewCreated` (:35–104) | 3 R8 names; upstream fixed "Ban Management crashes" in v4.7.2 (§4) |
| 24 | DisableBoosting.kt | grindr-internal | low | `sc0.j$a` / `r50.a$a` ctors (letters `a,e,f,c,i,j,t,v`), `FabUiModel`, `RightNowMicrosFab`, bottom-nav filter, `cd0.j2` (:27–83) | All-Grindr targets, 3 obfuscated; the file's own TODO (:78, "find the showTapsAndViewedMePopup in 25.20.0") documents drift **already observed** across builds |
| 25 | EnableUnlimited.kt | mixed | low | `usersession.b.W/.D`, `mo.b1$a.emit`, `TabLayout.addTab`, 5 named `invoke` hooks, `nb.d.a`, `Profile.isBlockable`, `x90.e.d`, `isChatPaywalled` (:28–154) | Only the Material `TabLayout.addTab` hook and resource-ID hiding are update-resilient; the paywall payload is obfuscated |
| 26 | LocationSpoofer.kt | mixed | medium | `android.location.Location.isMock/isFromMockProvider/getLatitude/getLongitude`; `ChatBottomToolbar` ctor (Teleport button) (:60–102) | Core spoof = pure framework (survives updates); UI button = named Grindr class + app drawables — a refactor breaks only the button, not the spoof |
| 27 | ProfileViews.kt | mixed | medium | `Retrofit.create` AFTER → blocking proxy for `ProfileRestService` POST `v5/views/{profileId}` (:14–36) | Hook site survives; an endpoint-version bump (v5→v6) or interface rename silently empties the blacklist (feature loss without crash) |
| 28 | StatusDialog.kt | framework | **high** | Material `TabLayout$TabView` ctor AFTER (long-press at position 0) (:25–43) | Stable bundled-library API; only a Material major swap affects it; assumes a tab exists at position 0 |
| 29 | UnlockExplorer.kt | grindr-internal | low | `ProfileViewState.getShouldLockQuickbar` → false (:12–19) | Semantic names, but `profileV2` is versioned and the file's own comments (:17–19) list two alternate method names — evidence this gating API already churned. Feature shipped upstream in v4.7.2 (§4) |

---

## 3. Summary statistics

**By kind** (29 total):

| Kind | Count | Share | Hooks |
|------|-------|-------|-------|
| framework | 5 | 17.2% | AllowScreenshots, TimberLogging, SSLUnpinning, AntiDetection, StatusDialog |
| grindr-internal | 15 | 51.7% | DisableShuffle, ExpiringMedia, NotificationAlerts, QuickBlock, WebSocketAlive, AntiBlock, ChatTerminal, OnlineIndicator, UnlimitedAlbums, EmptyCalls, ProfileDetails, UnlimitedProfiles, BanManagement, DisableBoosting, UnlockExplorer |
| mixed | 9 | 31.0% | ChatIndicators, DisableUpdates, FeatureGranting, DisableAnalytics, LocalSavedPhrases, SignatureSpoofer, EnableUnlimited, LocationSpoofer, ProfileViews |

**By update-survival confidence (versionProof):**

| Confidence | Count | Share | Hooks |
|------------|-------|-------|-------|
| high | 4 | 13.8% | AllowScreenshots, TimberLogging, SSLUnpinning, StatusDialog |
| medium | 6 | 20.7% | ExpiringMedia, AntiDetection, DisableAnalytics, SignatureSpoofer, LocationSpoofer, ProfileViews |
| low | 19 | 65.5% | the remaining 19 (all grindr-internal except ChatIndicators, DisableUpdates, FeatureGranting, LocalSavedPhrases, EnableUnlimited) |

**Cross-tab:** framework = 4 high + 1 medium; mixed = 4 medium + 5 low; grindr-internal = 1 medium + 14 low.

**The binding statistic:** **20/29 rows (69%) hook at least one R8-reassigned short name or single-letter field** (rows 2, 3, 5, 6, 8–13, 15, 17–25, i.e. every low row except none — all 19 low rows plus SignatureSpoofer's `ly.img` piece and DisableAnalytics' Fyber `i.a` piece). R8 re-randomizes these on each release build, so ~two-thirds of the module is pinned to one Grindr APK by construction.

---

## 4. Cross-check against upstream GrindrPlus release notes

Fetched this session from <https://github.com/R0rt1z2/GrindrPlus/releases> (page 1; the 10 releases below are everything shown — earlier releases were not fetched). Quotes are verbatim from the notes.

| Release (date) | Grindr target | What the notes say (verbatim where it matters) | Hooks in this audit affected |
|---|---|---|---|
| v4.2.0 (02 Jun 2025) | 25.8.0 | Added "Timber hook"; "hid Right Now and Boost buttons"; teleport geohash fix; "renamed Unlimited Expiring Photos to Unlimited Expiring Media (videos too)" | **TimberLogging, DisableBoosting, LocationSpoofer, ExpiringMedia** — the notes document when these features entered/reworked |
| v4.2.1 (03 Jun 2025) | 25.8.0 | "should fix hide-my-views and restore the gender filter" | **ProfileViews** — had broken on 25.8.0 |
| v4.3.0 (03 Jul 2025) | 25.10.2 | "should fix Facebook Login" | **SignatureSpoofer** (its FB `tryAuthorize` hook) — broken on the prior bump |
| v4.3.1 (04 Jul 2025) | 25.10.2 | "fixed Quick Block"; "exposed hidden profile details (copyable)"; UK 18+ verification bypass | **QuickBlock** (2nd break/fix cycle), **ProfileDetails** |
| v4.3.2 (22 Jul 2025) | 25.10.2 | EXPERIMENTAL user-agent version-code/name spoof — "IT COULD GET YOU BANNED!", logout/login required | **DisableUpdates** (`as.r` UA rewrite is this technique, now permanent in code) — direct evidence Grindr's **server** enforces client version at login |
| v4.4.0 (23 Jul 2025) | 25.12.1 | "sole change is adding support for that version" | **All 29** — a bare Grindr version bump is enough to require a module release; this is the R8-churn fingerprint matching §3's 20 obfuscated rows |
| v4.5.0 (26 Jul 2025) | 25.12.1 | "restored QuickBlock (auto-disables on failure)"; "reinstated AntiBlock"; "should fix inbox/chat filters" | **QuickBlock** (3rd cycle), **AntiBlock** — both previously broken/disabled |
| v4.6.0 (18 Sep 2025) | 25.15.0 | **"Chat filters are limited. Looks like everything related to this feature has been moved server-side."** (API now returns `full_chats`/`partial_chats`) | No direct row among the 29 (chat filters live outside this hook set), but this is the maintainers' own documented proof that **Grindr migrates features/enforcement server-side, beyond any client hook's reach** |
| v4.7.1 (27 Dec 2025) | 25.20.0 | "Not all functionality is working 100% at the moment": **AntiBlock**, Reverse Radar Tabs, **Signature Spoofer** ("Facebook login reportedly broken"), **Keep Alive Websocket** "may be nonfunctional" | **AntiBlock, SignatureSpoofer, WebSocketAlive** — three of this audit's rows explicitly named broken on the 25.20.0 bump |
| v4.7.2 (28 Jan 2026) | 25.20.0 | "unlock all Explorer profiles; fixed Online Indicator hook, AntiBlock hook, Unlimited Albums crashes, Ban Management crashes" | **UnlockExplorer** (feature shipped here), **OnlineIndicator, AntiBlock, UnlimitedAlbums, BanManagement** — four more rows that had broken and were repaired by re-mining names |

**Pattern confirmed by the maintainers' own history:** every Grindr bump in the v4.2.0→v4.7.2 window (25.8.0 → 25.10.2 → 25.12.1 → 25.15.0 → 25.20.0, five bumps in ~7 months) broke between one and five+ of these 29 hooks, and repair always meant re-locating re-minified classes (exactly the "search for '...'" comments preserved in the audited source). Also visible: **DisableUpdates' UA spoof descends from a release the maintainer himself stamped "IT COULD GET YOU BANNED!"**, and the v4.6.0 chat-filters note is the standing precedent that Grindr can withdraw a feature server-side at will.

---

## 5. Longevity estimate for the pinned combo (module v4.7.2-lineage + Grindr 25.21.1)

**Inputs (all sourced above):**

1. **Grindr release cadence:** 5 breaking Grindr versions in ~30 weeks (Jun 2025 → Dec 2025, per §4) ≈ **one re-minifying release every ~4–8 weeks**, each invalidating the ~20 obfuscated-name rows (v4.4.0 precedent: support-add was the *only* change needed).
2. **Server-side force-update:** demonstrated by v4.3.2 — old clients hit a login-level version gate within weeks of a Grindr release, and the emergency counter was a UA spoof the maintainer labeled ban-risky. Today that spoof lives permanently in `DisableUpdates.kt:105-114` (`as.r.<init>` rewriting the `grindr3/` user-agent, per audit row) — it can *mask* the client version but does not fix protocol/API drift, and it carries the same ban risk the maintainer warned about.
3. **Server-side feature withdrawal:** v4.6.0 chat filters — a whole feature category killed server-side with no client-side remedy possible.
4. **Upstream is dead:** repo archived 2026-05-18 (read-only); last release v4.7.2-25.20.0 (2026-01-28). The historical repair loop (§4) **no longer exists**. The snapshot under audit is already past upstream's last supported target — its compile pin 26.0.1 sits two minor version lines beyond 25.20.0 (§1, corrected).
5. **Today is 2026-10-22:** the compile-pinned Grindr 26.0.1 (released 2026-01-21) is ~9 months old; Grindr has shipped roughly **30 further 26.x releases** since the module's death — the APKMirror listing shows 26.21.0 current as of 2026-10-16 (mirror-derived count per `docs/01` §4; corrected 2026-10-22 — this doc's earlier "roughly 5–8 newer versions" was a cadence extrapolation written before that listing was consulted and understated the gap several-fold).

**Estimate:**

- **Hook-level, on the next Grindr version after 25.21.1:** 19/29 low rows silently no-op or trip their try/catch guards (WebSocketAlive's hook groups are individually try/caught, `WebSocketAlive.kt:30,72,78,118,129` per audit row; QuickBlock "auto-disables on failure" per v4.5.0 notes); 6 medium rows partially degrade (e.g. DisableAnalytics leaks Digital Turbine calls, LocationSpoofer loses only the Teleport button, ProfileViews' blacklist silently empties); **4 high rows keep working**.
- **Combo-level, full function:** from a fresh pin, history says the full 29-hook experience lasts **one Grindr release cycle ≈ 4–8 weeks** before re-minification breaks two-thirds of it.
- **Combo-level, any function (login ceiling):** the binding constraint is the server gate, not the hooks. Login viability for an old client historically decays over **weeks-to-a-few-months** post-release (v4.3.2 precedent). For a 9-month-old client in Oct 2026 with the upstream project archived, the honest estimate is: **the combo is most likely already login-gated, and at best is one server config-flip from total death**. If it still authenticates today, it is running on borrowed time via the UA spoof (ban risk) — not stability.
- **Residual after the gate closes:** none for practical purposes — if 25.21.1 cannot authenticate, even the 4 framework hooks are moot, because they run inside an app that can't log in. Framework-hook longevity (§6) only matters on a *newer* Grindr APK carrying the module forward, which requires exactly the re-pinning/re-mining work upstream no longer performs.

**Verdict: treat the v4.7.2-lineage × 25.21.1 combo as end-of-life.** Expected remaining full-function window: ~0 (already past the historical 4–8-week window many times over). Probability the full combo still works on 2026-10-22: very low. Probability the framework subset works *if* login still succeeds: high (that subset is version-independent by construction).

---

## 6. Hooks that keep working on NEWER Grindr versions (framework tier)

These survive a Grindr app update **by construction** — they hook OS classes or bundled third-party libraries with stable public API, never Grindr-owned code:

| Hook | Why it survives | Residual conditions |
|---|---|---|
| **AllowScreenshots.kt** (high) | Targets `android.view.*` / `android.app.*` / `ContentResolver` — OS classes a Grindr update cannot rename | `registerScreenCaptureCallback` needs API 34+; the ContentResolver hook keeps blocking *all* media content-observer registrations process-wide (blast-radius caveat, audit row) |
| **SSLUnpinning.kt** (high) | OkHttp `Builder` ctor / `certificatePinner` / `hostnameVerifier` names stable across OkHttp 3/4/5, bundled un-renamed; conscrypt `TrustManagerImpl.verifyChain` is OS-level | Breaks only if Grindr drops/renames OkHttp or Android changes `verifyChain`'s signature — Android-version-dependent, not Grindr-version-dependent |
| **TimberLogging.kt** (high) | `Timber$Forest`/`Timber$Tree` public API stable for years | Only if Grindr stops bundling Timber; also a **no-op in release builds** (module `BuildConfig.DEBUG` gate, :17–19) |
| **StatusDialog.kt** (high) | Material `TabLayout$TabView` ctor — bundled androidx-family library | Only a Material major-version swap; assumes Grindr still renders a tab at position 0 |
| **AntiDetection.kt** (medium) | 6 public SDK methods (AppLovin, PubNative, Facebook, Firebase Crashlytics, Sift) — stable SDK API surface | The 2 Crashlytics `AutoValue_*` ctor hooks mutate positional args (`setArg(2)`, `setArg(5)`) pinned to the bundled Crashlytics model; those two break if Grindr bumps Crashlytics |

**Partial survivors from the mixed tier** (hook site attaches on newer Grindr; feature payload may not):

- **LocationSpoofer** — the actual spoof (`android.location.Location`) is pure framework and survives; only the Teleport UI button (Grindr class + drawables) breaks.
- **SignatureSpoofer** — the named Firebase/Facebook SDK classes survive; the obfuscated `ly.img.android.c.d` piece re-breaks (upstream already reported its FB-login path broken at v4.7.1).
- **DisableAnalytics** — 6/7 targets are stable public SDK APIs and keep working; the Fyber `i.a` obfuscated target re-breaks, so the feature degrades, not dies.
- **Retrofit-based hooks (ChatIndicators, LocalSavedPhrases, ProfileViews)** — `retrofit2.Retrofit.create` (constant verified at `utils/RetrofitUtils.kt:15` per audit rows) keeps attaching on any Grindr that bundles Retrofit, but each feature's payload depends on obfuscated service classes and endpoint paths, so they **attach yet no-op** after re-minification.
- **EnableUnlimited / FeatureGranting** — the Material `TabLayout.addTab` and androidx `AlertDialog$Builder.show` hook sites survive, but both payloads read obfuscated Grindr fields (`'Store'` filtering needs Grindr routes; `Builder` field `P`), making them effectively build-pinned.

**Hard floor:** everything in this section still presumes the process runs — i.e., a Grindr version that still authenticates for the user's account. The server gate (§5) dominates all hook-level survival.

---

## 7. Sources & verification log

**Read/run this session:**

- Workspace layout: `find` over the draft workspace; confirmed `pairip-research/docs/` exists (empty — this is its first document) and `samples/GrindrPlus/` is the module snapshot.
- `samples/GrindrPlus/version.json` → `25.21.1` / `148541`; `manifest.json` → v4.7.2/v4.7.1 APK URLs pinned to Grindr `25.20.0-147239`; `app/build.gradle.kts:23-24,34,40` → self-version `4.8.0`, `TARGET_GRINDR_VERSION_*` build-config pins.
- Hook inventory: `find app -name "*.kt" -path "*hook*"` → exactly **29 files**, matching the 29 audit rows one-for-one.
- Spot-check of audit-row claims: `grep` confirmed `fo.k` (`ChatTerminal.kt:15`), `vn.a` (`ChatIndicators.kt:14`, `LocalSavedPhrases.kt:26`), `to.p1` (`EmptyCalls.kt:11`), `tk.a` (`UnlimitedAlbums.kt:40`) with the build-specific "search for" comments exactly as the audit rows describe.
- Release notes: WebFetch of `https://github.com/R0rt1z2/GrindrPlus/releases` — public page, no login wall; returned the 10 most recent releases (v4.2.0→v4.7.2) with dates, Grindr targets, and note bodies, plus the archive notice (2026-05-18).

**Not done / limitations (stated plainly):**

- Release-notes cross-check covers **page 1 only** (v4.2.0 onward). Releases before v4.2.0 (v4.0.x–v4.1.x era) were not fetched; breakage history older than Jun 2025 is therefore not in §4.
- Per-hook file:line citations for targets come from the **29 audit rows supplied with this ask**; I spot-checked five obfuscated-name claims against the source (above) but did not re-derive all 29 rows line-by-line this session.
- No runtime testing was performed (no device/emulator, no Grindr APK installed — `samples/apk/` and `samples/out/` were empty **at this document's authoring**; later the same day, 2026-10-22, the `docs/02` census session populated them with two Grindr APKs (`grindr-current.apk`, `grindr-current-base.apk`) and two census outputs (`census.json`, `census-base.json`), so a reader inspecting the repo now will find them non-empty — that material postdates and does not feed this audit). All survival judgments are static analysis + upstream release-note evidence; "already login-gated" in §5 is an inference from the v4.3.2 precedent and the 9-month age of the pinned client, not a measured login attempt.
- Grindr version-code semantics (YY.WW) is inferred from the observed sequence (25.8 → 25.10 → 25.12 → 25.15 → 25.20); current-store Grindr version as of 2026-10-22 was not checked.
