# 06 — The GrindrPlus Public Corpus (R0rt1z2/GrindrPlus)

**Retrieval date for all API pulls: 2026-10-24** (single session; every `gh api` command named below was run that day).
**Subject:** the complete public record of [R0rt1z2/GrindrPlus](https://github.com/R0rt1z2/GrindrPlus) — an Xposed module that unlocked/modified the Grindr Android app — as it stood at archival. The ask dates the archive to **2026-05-18**; corroborated this session by `gh api repos/R0rt1z2/GrindrPlus` → `archived: true`, `pushed_at: "2026-05-18T08:31:33Z"` (the repo object exposes no `archived_at` timestamp; it returned `null` — the archive date rests on the ask, `pushed_at`, and the archive notice previously captured on the releases page in `docs/03` §5).

**Sources mined:**

- (a) GitHub REST/GraphQL API via `gh api` against `R0rt1z2/GrindrPlus`: releases, "issues", PRs, commits, branches, tags. Raw dumps preserved in `out/grindrplus-corpus/` of the draft workspace (`releases_flat.json`, `all_release_notes.txt`, `commits_p1.txt`, `versionjson_commits.txt`, `probe_all.txt`, `probe_refs.txt`).
- (b) The local snapshot at `pairip-research/samples/GrindrPlus` — a **depth-1 clone** (verified: `git rev-list --count HEAD` → `1`; the single commit is `aa497a0` "EOL", 2026-04-04). Every git-history fact below therefore comes from the GitHub API, not the clone. Local file claims cite `samples/GrindrPlus/<path>:<line>`.

---

## 1. Repository identity card

All fields from `gh api repos/R0rt1z2/GrindrPlus` (run 2026-10-24):

| Field | Value |
|---|---|
| Description | "Xposed Module that unlocks and adds unique features to the Grindr app" |
| Created | 2023-09-11T23:00:08Z |
| Last push / archival window | 2026-05-18T08:31:33Z (`pushed_at`); `archived: true` |
| Stars | 547 (snapshot 2026-10-24; `docs/01` §10 recorded 546 at its own retrieval — star drift, not a contradiction) |
| Default branch | `master` (546 commits, 2024-04-24 → 2026-04-04) |
| Branches (10) | `antiblock-feature`, `backup`, `l10n_master`, `l10n_master3`, `manager`, `maps-api-key`, `master`, `new-notifs`, `old_base`, `roger` (`gh api repos/R0rt1z2/GrindrPlus/branches`) |
| Issues | **disabled** — `has_issues: false` (see §3) |
| Discussions | disabled — `hasDiscussionsEnabled: false`, GraphQL `discussions.totalCount: 0` |
| License | GPL-3.0 (`samples/GrindrPlus/LICENSE`; README §License notes the `old_base` branch is unlicensed — README.md:286) |

**Lineage.** The repo's own history begins at commit `b7361ce2` "GrindrPlus: Initial commit" (2024-04-24T18:32:26Z) — the day release v3.0.0 shipped, whose notes say "Rebased the entire source code". Everything before that (releases v1.2.6 → v2.1.4, Sep 2023 – Apr 2024) was published from history that no longer exists on `master`; the pre-rebase code lives on branch `old_base` (tip commit 2024-04-15T23:05:24Z, "Make drop down triangle white" — `gh api repos/R0rt1z2/GrindrPlus/branches/old_base`). README.md:24 states the repo is "a completely rewritten version of ElJaviLuki's original mod", and the very first release note (v1.2.6-9.16.1, 2023-09-12) links to `ElJaviLuki/GrindrPlus/pull/51` ("Add support for latest version (9.16.1)", 2023-09-12) — so day one of this repo re-publishes the tail of ElJaviLuki's line. The original [ElJaviLuki/GrindrPlus](https://github.com/ElJaviLuki/GrindrPlus) still exists as a separate, non-archived repo (`pushed_at` 2024-09-18, `has_issues: false`, 16 PRs reachable via `gh api repos/ElJaviLuki/GrindrPlus/pulls?state=all`); its PR numbers top out at #72, so the R0rt1z2 #1–#300 numbering is entirely its own.

---

## 2. Deliverable 1 — Module-release ↔ Grindr-version timeline (all 44 releases)

Fetched via `gh api repos/R0rt1z2/GrindrPlus/releases --paginate` (44 objects; flattened into `out/grindrplus-corpus/releases_flat.json`; full note bodies in `out/grindrplus-corpus/all_release_notes.txt`). Version codes shown where the tag/notes state them. "±" = Grindr versionName only. Every row's canonical URL is `https://github.com/R0rt1z2/GrindrPlus/releases/tag/<tag>`.

| # | Module release | Grindr target | Published (UTC) | Note-worthy (from the release body) |
|---|---|---|---|---|
| 1 | v1.2.6 | 9.16.1 | 2023-09-12 | First release of this repo; body defers to ElJaviLuki PR #51 |
| 2 | v1.3.1 | 9.17.4 | 2023-12-15 | (empty body) |
| 3 | v1.3.2 | 9.18.0 | 2023-12-20 | Chat terminal; "You've been blocked/unblocked" notifications fix |
| 4 | v1.3.3 | 9.18.0 | 2023-12-21 | **Profile redesign disabled** ("random crashes when trying to open certain profiles") |
| 5 | v1.3.4 | 9.18.1 | 2023-12-24 | Redesign restored; "Reworked and refactored the whole mod (internally)" |
| 6 | v1.3.5 | 9.18.1 | 2023-12-28 | Messages deleted on block, chat-markers leaking — both fixed |
| 7 | v1.3.6 | 9.18.1 | 2023-12-29 | Analytics / profile-view recording fixes |
| 8 | v1.3.7 | 9.18.2 | 2024-01-05 | Unsend-any-message hook; teleport feature introduced |
| 9 | v1.3.8 | 9.18.2 | 2024-01-16 | App-updates hook fixed (APKPure dependency dropped); album cache manager for the 7th-album limit |
| 10 | v1.4.0 | 9.18.5 | 2024-02-05 | Precise distance |
| 11 | v2.1.0 | 24.0.8 | 2024-03-15 | **Grindr's year-based versioning begins (9.x → 24.x).** WARNING: "Due to recent updates by Grindr regarding the messaging system, certain features of the mod are not stable at all"; blocked/unblocked detection dead |
| 12 | v2.1.1 | 24.1.0 | 2024-03-17 | "Completely removed the unlimited albums feature (it was broken)" |
| 13 | v2.1.2 | 24.2.0 | 2024-04-01 | Commands reworked to dialogs/toasts |
| 14 | v2.1.3 | 24.2.0 | 2024-04-03 | Profile-delay workaround: "swiping between profiles will no longer work" (explicit trade-off) |
| 15 | v2.1.4 | 24.3.0 | 2024-04-14 | Swipe feature back; LSPatch perf regressions fixed |
| 16 | v3.0.0 | 24.3.1 | 2024-04-24 | **Full rebase** (matches the new "Initial commit"); Mod Settings UI |
| 17 | v3.1.0 | 24.4.0 | 2024-04-27 | Unlimited expiring photos fixed |
| 18 | v3.1.1 | 24.4.0 | 2024-05-01 | "Huge refactor"; hide-views fix; BMI crash fix |
| 19 | v3.1.2 | 24.4.1 | 2024-05-01 | `/open` crash fix |
| 20 | v3.1.3 | 24.7.0 | 2024-06-11 | Google Login fix under LSPatch |
| 21 | v3.1.4 | 24.8.0 | 2024-07-19 | "Signatures have changed" (reinstall required); AdAway/cookielaw whitelist note |
| 22 | v3.1.5 | 24.9.0 | 2024-08-06 | "more strict updates blocker" |
| 23 | v3.2.0 | 24.12.0 | 2024-09-11 | "**EVEN MORE** strict updates blocker" |
| 24 | v3.2.1 | 24.12.0 | 2024-09-12 | applovin startup-crash fix; JingMatrix-LSPatch compat |
| 25 | v3.2.3 | 24.14.0 | 2024-10-08 | Unlimited albums fixed (again) |
| 26 | v3.2.5 | 24.17.1 (131488) | 2024-11-17 | **TWO BUILDS caution** (only the Nov-15 build works); "Swiping through cascade profiles **IS BROKEN** (again)"; telemetry-disable "got broken a few releases ago" — fixed |
| 27 | v3.2.7 | 24.19.0 | 2024-12-23 | Persistent-incognito hook disabled ("causing issues"); cascade swipe **BROKEN** |
| 28 | v3.2.8 | 24.19.0 | 2025-01-07 | Swipe fixed; `DisableShuffle`, `ReverseRadarTabs` hooks; command prefix |
| 29 | v3.3.0 | 25.0.0 (133286/133352) | 2025-01-23 | "works with both" 25.0.0 variants |
| 30 | v3.5.1 | 25.3.0 | 2025-03-05 | Feature-granting hook "target[s] the new flags system" |
| 31 | v3.5.3 | 25.3.0 (135731) | 2025-03-18 | Gender filter restored |
| 32 | v4.0.0 | 25.5.0 | 2025-04-06 | **GrindrPlus Manager public beta** — "eliminating the need for LSPatch or Shizuku" |
| 33 | v4.1.2 | 25.6.0 (137100) | 2025-04-21 | **Two 25.6.0 builds** (Play 137249 vs APKMirror 137100 — module needs the latter); ban-details hook ("including the actual ban reason"); Room DB unification |
| 34 | v4.1.3 | 25.6.0 | 2025-04-27 | Maps-API-key + cloning fixes |
| 35 | v4.2.0 | 25.8.0 (138406) | 2025-06-02 | Foreground bridge service; background tasks (experimental "Always Online") |
| 36 | v4.2.1 | 25.8.0 | 2025-06-03 | Hide-views fix; gender filter back |
| 37 | v4.3.0 | 25.10.2 (140001) | 2025-07-03 | "Should fix Facebook Login" |
| 38 | v4.3.1 | 25.10.2 | 2025-07-04 | "Now SHOULD forcefully bypass the new UK 18+ ID verification system" (later reversed — §6, news msg 166) |
| 39 | v4.3.2 | 25.10.2 | 2025-07-22 | **[EXPERIMENTAL] UA spoof** — see §5; "IT COULD GET YOU BANNED!" |
| 40 | v4.4.0 | 25.12.1 (140963) | 2025-07-23 | Support-only release |
| 41 | v4.5.0 | 25.12.1 | 2025-07-26 | QuickBlock + AntiBlock restored ("disabled because they don't work", per news msg 164) |
| 42 | v4.6.0 | 25.15.0 (144041) | 2025-09-18 | News section; **chat filters moved server-side** — see §5 |
| 43 | v4.7.1 | 25.20.0 (147239) | 2025-12-27 | **WIP release; hooks listed broken** — see §5 |
| 44 | v4.7.2 | 25.20.0 | 2026-01-28 | Final release; fixes mostly by "ASDF Biker" (community) |

**Cadence summary (computed from `releases_flat.json` this session):** 44 module releases across 868 days (2023-09-12 → 2026-01-28) — one release every ~19.7 days — tracking **29 distinct Grindr builds**. 22 of the 44 note bodies contain fix/restore items for things a previous Grindr update broke. Module version numbering has gaps (no v2.0.0, v3.4.x, v4.1.0/4.1.1, v4.7.0 — the "v4.7.0" update lived in PRs #201/#202, closed unmerged).

### 2.1 The Grindr release cadence as seen by the repo's own bot

`version.json` was updated by a scheduled workflow (`.github/workflows/fetch_version.yml`, removed at EOL — §8). Commit list: `gh api "repos/R0rt1z2/GrindrPlus/commits?path=version.json&per_page=100"` (50 commits, `out/grindrplus-corpus/versionjson_commits.txt`); values read at each ref via the contents API. Selected points (date = bot commit):

| Bot commit date | version.json → | Evidence |
|---|---|---|
| 2025-09-17 | 25.15.0 | `669aefe3` |
| 2025-11-13 | 25.19.0 | `78b32989` |
| 2025-11-21 | **25.20.0** (last version a release supports) | `7a1c0cdf` |
| 2025-12-18 | 25.21.0 | `ed65ed16` |
| 2025-12-26 | 25.21.1 | `4f787764` |
| 2026-01-22 | 26.0.1 | `859d3d1f` |
| 2026-01-29 | 26.1.0 | `60c90bef` |
| 2026-03-01 | 26.2.0 | `05f4aeb5` |
| 2026-03-13 | 26.4.0 | `c607c7fb` |
| 2026-03-18 | 26.4.1 | `f52d21a1` |
| 2026-03-19 | 26.4.2 | `5e54c9f9` |
| 2026-03-31 | **26.5.0** (last value the bot recorded) | `d326a6b7` |
| 2026-04-04 | **pin-back to 25.21.1** (manual) | `8b9d23af` "Spoof an older version" — §7 |

So at the moment of the PairIP announcement (2026-03-21, §6) the tracker stood at 26.4.x — corroborating `docs/01` §4's "current at announcement time" framing.

---

## 3. Deliverable 4 (first half) — Issues: an empty shelf, verified

The ask requests "issues (titles, numbers, state; note ban-related reports without quoting personal details)". **There is no issue corpus to mine.** Evidence trail, all run 2026-10-24:

1. `gh api repos/R0rt1z2/GrindrPlus` → `"has_issues": false`, `open_issues_count: 0`.
2. `gh api "repos/R0rt1z2/GrindrPlus/issues?state=all&per_page=100"` → `[]` (same for `state=open` and `state=closed`).
3. `gh api "search/issues?q=repo:R0rt1z2/GrindrPlus+type:issue"` → `total_count: 0` (also 0 for `type:pr` — the search index has nothing for this repo).
4. GraphQL `{ repository(...) { issues { totalCount } } }` → `0`.
5. Exhaustive number probe: because listing endpoints are empty but the shared issue/PR counter demonstrably reached ≥ #260 (PR #260, 2026-03-04), I probed **every number 1–360** via GraphQL `issueOrPullRequest(number: N)` in batched alias queries (`out/grindrplus-corpus/probe_all.txt` + follow-ups). Result: **103 numbers resolve, every single one a PullRequest; zero Issues.** Numbers 1–300 resolve; 301–360 resolve nothing. The ~197 unresolvable numbers within 1–300 are deleted items or never-issued numbers — the two are indistinguishable through the API.
6. A bug-report template exists on disk (`samples/GrindrPlus/.github/ISSUE_TEMPLATE/bug_report.yml`, added with the dev docs in PR #203, 2025-12) and its text tells users to "search existing issues" — but issues are disabled at the repo level, and README.md:270's "submit an issue … Discussions section also available!" points at features that are off. **No user-filed issue, ban-related or otherwise, is publicly retrievable from this repository.**

The maintainer intentionally kept user support off GitHub: README.md:117-118 — "Before reporting a new bug, please check our [Discord](https://discord.gg/invite/SPb6Kc7S4C) or [Telegram](https://t.me/GrindrPlus) channels to see if it's already known." The nearest public artefact of that Telegram traffic is `news.json` (§6): maintainer-authored advisories that respond to, and describe, user-side breakage waves. Those, plus PR titles and release-note acknowledgements, are the issue-derived signal this corpus can actually provide (§5.3).

**Ban-related reports specifically:** none exist in the minable record. The only ban statements are maintainer-authored (v4.3.2's ban warning, the README FAQ's "no reported cases of bans" answer, and the BanManagement hook lineage: v4.1.2 "display ban details … including the actual ban reason"; v4.7.2 "Fixed Ban Management crashes"; PR #269 "Fix Ban Management wrong Android_ID lenght"). No personal details are quoted anywhere in this document.

### 3.1 Pull-request census (substitute signal)

103 PRs resolve (titles/states/dates in `out/grindrplus-corpus/probe_all.txt`). Notable, beyond those merged:

- **Community takeover of maintenance, Dec 2025 – Mar 2026:** #193 "Bug workaround: DisableUpdates: use static version info" (closed), #194/#195/#196 (the 25.20.0 update wave that became v4.7.1), #201/#202 "Update to Grindr 25.20.0 (v4.7.0)" (closed), #207-#210/#218 (fixes shipped in v4.7.2), #231-#233 (teleport UI + the fixes v4.7.2 credits to ASDF Biker), #259/#260 "Remove unnecessary DexClassLoader…" / "drop RootBeer dependency" (2026-03-04, the last merges).
- **Post-EOL continuation attempt, ~#263–#299** (all CLOSED, none merged after archival window): #277 "Pressie albums V26", #281-#299 a wave of automated quality/test PRs ("Claude/refactor text setting", "bootstrap unit tests", "cover the PCHIP interpolation algorithm", "authorise bind attempts"…). A `samples/GrindrPlus-fork` directory also exists in this workspace (adjacent sample, **not** mined for this document).
- **Spam pressure visible in the record:** #107/#108 "SPAM", #113 "Delete .gitignore", #114 "Create iml", #205 "Create moe", #217 "Friend" — all closed.

---

## 4. Commit activity timeline

`gh api "repos/R0rt1z2/GrindrPlus/commits?per_page=100"` pages 1–7 → **546 commits** on `master`, `b7361ce2` (2024-04-24 "Initial commit") → `aa497a04` (2026-04-04 "EOL"). Raw list: `out/grindrplus-corpus/commits_p1.txt`.

**Monthly histogram** (computed from that list):

```
2024-04 14   2024-10  4   2025-03 70   2025-09 17
2024-05  7   2024-11 28   2025-04 117  2025-10  3
2024-06  7   2024-12 23   2025-05 21   2025-11  4
2024-07  5   2025-01 48   2025-06 19   2025-12 35
2024-08  7   2025-02  3   2025-07 40   2026-01 16
2024-09 32                 2025-08  4   2026-02  9
                                       2026-03  9
                                       2026-04  4
```

Peaks align with the two biggest pushes: 2025-03/04 (the Manager build-out before v4.0.0) and 2025-12/2026-01 (the community 25.20.0 rescue that produced v4.7.1/v4.7.2). The long gaps (2025-02: 3, 2025-08: 4, 2025-10: 3, 2025-11: 4) match news msg 184 (2025-12-04): "The main developer is currently taking a break from the project."

**Top authors** (commit counts, same list): R0rt1z2 370, github-actions[bot] 45, Truffle2143 27, Giovanni Mazzone 16, Roger Ortiz 12, Poundr 12, asdf biker 11, r0rt1z2 11, ASDF Biker 9, Rattly 8 (remainder: ~28 others). The 45 bot commits are the two scheduled workflows' output ("Fetch latest Grindr version" / "Fetch latest news from Telegram").

**EOL-day sequence** (2026-04-04, from the API):

| Time (UTC) | SHA | Commit |
|---|---|---|
| 16:16:56 | `1836dd29` | "Nuke CIs" — removes `.github/workflows/fetch_version.yml` and `news.yml` (verified via commit files API; `build_apk.yml`/`extract_base.yml` survive to HEAD in the local clone) |
| 16:17:40 | `8b9d23af` | "Spoof an older version" — version.json 26.5.0→25.21.1 (§7) |
| 16:22:50 | `aa497a04` | "EOL" — adds the README PairIP banner (the only commit in the file's API history, `commits?path=README.md`, to touch README after 2026-01-28) |

After 2026-04-04 there are no further commits; `pushed_at` 2026-05-18 marks the archival push. (Commit-author dates vs push date discrepancy noted and explained in `docs/01` §4; consistent with what I see.)

---

## 5. Deliverable 2 — Documented breakage events (release-note corpus)

Everything in this section is quoted or paraphrased from `out/grindrplus-corpus/all_release_notes.txt` (full bodies; each release cited as `releases/tag/<tag>`).

### 5.1 Grindr-side changes that broke or reshaped the module

| When | Grindr version | Event (verbatim fragments) | Source |
|---|---|---|---|
| 2024-03-15 | 24.0.8 | Messaging-system update: "Due to recent updates by Grindr regarding the messaging system, certain features of the mod are not stable at all"; the blocked/unblocked detector "doesn't work anymore" | v2.1.0-24.0.8 |
| 2024-11-17 | 24.17.1 | Two APK builds shipped; module works only with one ("this **ONLY WORKS** with the LATEST ONE"). Cascade-profile swiping broken by the new unlimited-profiles hook | v3.2.5-24.17.1 |
| 2025-03-05 | 25.3.0 | Feature granting re-targeted: "Updated the feature-granting hook to target the new flags system" | v3.5.1-25.3.0 |
| 2025-04-21 | 25.6.0 | Two builds again (Play 137249 vs APKMirror 137100); LSPosed users must use the APKMirror build | v4.1.2-25.6.0 |
| 2025-07-04 | 25.10.2 | UK 18+ ID verification appears; module ships a bypass ("Now SHOULD forcefully bypass…") — then reverses it 20 days later (news msg 166, §6) | v4.3.1-25.10.2 |
| 2025-09-18 | 25.15.0 | **Server-side chat filters:** "Chat filters are limited. Looks like everything related to this feature has been moved server-side. The API now returns both `full_chats` and `partial_chats`, so they won't work at all." | v4.6.0-25.15.0 (NOTES block) |
| 2025-09-18 | 25.12.1 | **Server-side version discontinuation:** "Grindr has recently discontinued version v25.12.1, which means the current mod is no longer functional." | news msg 177 (2025-09-18, §6) — the same day v4.6.0 shipped for 25.15.0 |
| 2025-12-27 | 25.20.0 | Hooks listed broken at update: "Antiblock / Reverse Radar Tabs / Signature Spoofer (Facebook login has been reported broken, but unverified) / Keep Alive Websocket … It's possible that other hooks have issues at the moment too, but most of the core ones should work." | v4.7.1-25.20.0 (Notes) |
| (at 25.20.0) | 25.20.0 | Online-indicator moved server-side: "this version uses `onlineUntil` field in the profile (computed on the server) instead of `lastSeen` … behind a feature flag, but the old behaviour will most likely be removed" | `samples/GrindrPlus/docs/patches/online_indicator.md:8-11` |
| 2026-03-13 | 26.4-era | Grid anomaly: "a weird issue affecting the main grid … looks like some sort of A/B testing on Grindr's side" | news msg 196 (§6) |
| 2026-04-04 | 26.x | Grid paywall server-side checks tied to claimed version: "Latest versions have the main grid paywalled through server side checks and this is being reflected in the mod since we spoof the latest version against the API." | commit `8b9d23af` message (§7) |
| 2026-05-18 (archival) | 26.5+ | PairIP wall — §6/§7 | README banner, news msgs 197/198 |

### 5.2 Module-side breakage admitted in notes (selection)

- Unlimited Albums: removed entirely in v2.1.1 ("it was broken"), re-added and re-fixed repeatedly (v3.2.3, v3.1.5 "might still be buggy", v4.1.2 "still unstable"), crash-fixed in v4.7.2.
- Cascade swiping: broken in v3.2.5, still broken in v3.2.7, fixed in v3.2.8.
- Persistent-incognito hook: disabled in v3.2.7 ("causing issues"); README.md:109 still lists Incognito Mode as unreliable at EOL.
- Startup crashes (applovin) v3.2.1; settings-crashes v4.2.0; race condition resetting settings v4.1.2.
- README "Bugs" section at EOL (README.md:103-115) is a curated list of permanent losses: "Viewed Me" ("a server-side feature that cannot be modified"), Google-login workaround needed on LSPatch, Maps needing a user-supplied API key, LSPatch instability.

### 5.3 User-reported signal (the issue substitute)

- v4.7.1 note: "Facebook login has been reported broken, but unverified" — a user report absorbed into release notes (releases/tag/v4.7.1-25.20.0).
- v4.6.0 note credits `@gustarmartins` for the Install-section network fix; v4.6.0/v4.5.0 rely on user-reported OnePlus/OPPO/Realme ColorOS failures (also news msgs 173/183, 2025-09-18 and 2025-11-23, the latter linking `https://t.me/GrindrPlus/38490` for "OxygenOS, ColorOS OnePlus, Oppo, RealMe users (unrooted) having issues with recent Android security updates").
- news msg 171 (2025-07-30): mass "connection issues or profiles not loading" → published workaround: disable the `Disable Updates` hook, force-close both apps. This is the strongest dated user-complaint wave in the corpus (Telegram-sourced, maintainer-relayed).
- news msgs 181/182/194/195 (2025-10-08, 2025-11-18, 2026-01-29, 2026-02-10): repeated "Grindr is down" advisories — the maintainer explicitly triaging user complaints as server outages/Cloudflare incidents, not module faults ("Please DO NOT spam the chat with messages like 'My app doesn't work'").

---

## 6. Deliverable 3 — Maintainer statements, verbatim, with URLs

**(a) The PairIP discontinuation statement — README banner, verbatim** (`samples/GrindrPlus/README.md:1-4`; introduced by the EOL commit `aa497a04`, 2026-04-04 — verified via `gh api "repos/R0rt1z2/GrindrPlus/commits?path=README.md"`; canonical URL https://github.com/R0rt1z2/GrindrPlus#readme):

> [!WARNING]
> Grindr has started using PairIP for their latest versions of the app. **This effectively marks the end of this module, and no further updates will be released**.
>
> Enjoy it while it lasts, as you'll eventually be required to update to the latest version.

**(b) PairIP arrival announcement — Telegram channel message mirrored into the repo, verbatim** (news.json message_id 197, Unix 1774135930 = **2026-03-21 23:32 UTC**, converted this session; file `samples/GrindrPlus/news.json:108-111`; channel https://t.me/GrindrPlus):

> Hello everyone, sad news today.
>
> Grindr has implemented Google's new PairIP protection.
> This system implements advanced native-backed VMProtect-esque protections to Android apps.
>
> There is no bypass publicly available online right now, and we don't have the time nor the expertise required to implement one.
>
> The current releases are *probably* the last ones we will be able to publish, at least until someone develops a new bypass. But this is probably the end.
>
> It's been a wild ride.

**(c) Wind-down announcement — verbatim excerpts** (news.json message_id 198, Unix 1775125106 = **2026-04-02 10:18 UTC**; `samples/GrindrPlus/news.json:113-115`):

> Unfortunately the monthly cost for the download server utilized by the manager is now exceeding our financial ability to support. […] However, because Grindr has made the continued maintenance and development of this project unfeasible with the recent introduction of PairIP DRM, we're now going to use this as a cue to start winding down GrindrPlus operations.
>
> The first thing to go will be the auto-download functionality of the manager. […] I would estimate this to take effect sometime in the third week of this month.
>
> The next thing to happen will likely be Grindr enforcing updates past versions where GrindrPlus is able to support. When this happens, the repository will be archived and no new code submissions will be accepted.

**(d) Ban-risk statements** (no user reports quoted — none exist; §3):

- FAQ, verbatim (README.md:234-237, "Can I get banned with this?"): "- [Obviously](https://www.grindr.com/terms-of-service), however, the risk is very low, and there have been no reported cases of bans related to using this mod."
- v4.3.2 release caution, verbatim (releases/tag/v4.3.2-25.10.2): "**This is a TEMPORARY fix for Grindr version 25.10.2 and is HIGHLY EXPERIMENTAL. IT COULD GET YOU BANNED!**" and "I've tested it with my account, and so far it seems to keep 25.10.2 working and I haven't been banned yet. **That said, this method could lead to a ban, so use it at your own risk.**"

**(e) The UA-spoof mechanism statement** (v4.3.2, same URL): "It works by spoofing the user-agent's version code and name to trick the app into thinking it's on a supported version."

**(f) UK age-verification policy reversal** (news msg 166, 2025-07-24, `samples/GrindrPlus/news.json:13-16`): "**GrindrPlus will NOT help you get around this verification by any means** … any code that interferes with age verification has been completely removed because this project will not help anyone break the law" — reversing the v4.3.1 (2025-07-04) "SHOULD forcefully bypass" stance.

**(g) Server-side discontinuation notice** (news msg 177, 2025-09-18, `samples/GrindrPlus/news.json:48-51`): "Grindr has recently discontinued version v25.12.1, which means the current mod is no longer functional. We're aware of this and are already working on an update."

---

## 7. How the module pinned Grindr versions (mechanism, from the clone)

Four cooperating pieces — this is the machinery behind column 2 of the §2 table:

1. **Compile-time pin.** `samples/GrindrPlus/app/build.gradle.kts:16-17` — `grindrVersionName = listOf(<name>)`, `grindrVersionCode = listOf(<code>)`; injected as `TARGET_GRINDR_VERSION_NAMES/CODES` build-config fields (build.gradle.kts:32-42). Verified at release tags via the contents API: v4.7.2 → `25.20.0`/`147239`; v4.6.0 → `25.15.0`/`144041`; v4.3.2 → `25.10.2`/`140001` (i.e., **each module release hard-pins exactly one Grindr build**). At HEAD the pin is `26.0.1`/`149389` with self-version `4.8.0` (build.gradle.kts:16-17,24) — an unreleased lineage.
2. **Runtime gate.** `XposedLoader.kt:33-38` passes the pins into `GrindrPlus.init(...)`; `GrindrPlus.kt:415-436` (`checkVersionCodes`) compares installed Grindr `versionName`/`longVersionCode` and, on mismatch, disables the module with a "Version Mismatch" dialog (GrindrPlus.kt:438-468). Rationale (README.md:215): "Grindr has lots of obfuscated symbols that change in each app update" — the pins exist because hooks reference obfuscated single-letter names that rot every release (e.g. GrindrPlus.kt:108-116: `as.r` for the UA class, `nz.e` for the location provider, each with a "search for '<string constant>'" comment for re-finding it after updates).
3. **Update-spoof feed.** `hooks/DisableUpdates.kt:24-25` fetches `https://raw.githubusercontent.com/R0rt1z2/GrindrPlus/master/version.json` at runtime; `updateVersionInfo()` (DisableUpdates.kt:94-118) blocks Play-core update checks and, **if the fetched version is newer than the installed one, rewrites the app's user-agent field** (any `String` field starting `grindr3/` on the `as.r` UA object → `grindr3/$versionName.$versionCode;$versionCode;`) and `AppConfiguration` field `d`. This is the productionized descendant of v4.3.2's experimental spoof. `version.json` itself is written by `fetch_version.py`, which scrapes **APKMirror's Grindr listing** (fetch_version.py:23-75: selector `.appRowTitle > a`, then the variants table) and saves `{versionName, versionCode}` (fetch_version.py:78-95) — a scheduled GitHub Action did this until the bots were removed at EOL (§4).
4. **Manager download feed.** `manifest.json` maps module releases to a self-hosted APK pair (Grindr APK + module APK) at `gplusapks.airdns.org:32734` — at HEAD only v4.7.1/v4.7.2, both against Grindr `25.20.0-147239` (manifest.json:2-9). This is the "auto-download functionality" news msg 198 says was wound down in April 2026.

**The final act of that machinery** — commit `8b9d23af` (2026-04-04, "GrindrPlus: Spoof an older version"; diff retrieved via the commit API): version.json `26.5.0 (154546)` → `25.21.1 (148541)`, with the message: "Latest versions have the main grid paywalled through server side checks and this is being reflected in the mod since we spoof the latest version against the API." I.e., the spoof itself had become a liability: claiming the latest version invited the newest server-side gates, so the maintainer pinned the *claimed* version back under the 26.x line as a last life-extension for the 25.x population.

---

## 8. Dating the PairIP wall — what this corpus establishes

Synthesis (every element cited above):

| Date (UTC) | Event | Evidence |
|---|---|---|
| ≤ 2025-11-21 | Grindr 25.20.0 current; still fully hookable (later supported by v4.7.1/v4.7.2) | bot commit `7a1c0cdf`; §2 rows 43-44 |
| 2025-12-27 / 2026-01-28 | Last two releases (v4.7.1 WIP, v4.7.2 community-fixed) | §2 |
| 2026-01-22 → 03-19 | Grindr rolls 26.0.1 → 26.4.2; **no module release follows past 25.20.0** | §2.1 bot table |
| 2026-03-13 | Grid anomaly first flagged (A/B-testing theory) | news msg 196 |
| **2026-03-21** | **PairIP announced to users: "advanced native-backed VMProtect-esque protections … no bypass publicly available … probably the end"** | news msg 197 (verbatim §6b) |
| 2026-03-31 | Bot's last version track (26.5.0) | `d326a6b7` |
| 2026-04-02 | Wind-down: auto-download server being cut "third week of this month"; archive predicted "once Grindr enforces updates past" supported versions | news msg 198 (§6c) |
| 2026-04-04 | CIs nuked → spoof pinned back to 25.21.1 → "EOL" commit with README banner | §4 EOL table |
| 2026-05-18 | Repo archived (ask; `pushed_at`; `archived: true`) | §1 |

What this corpus does **not** establish: which Grindr build first shipped PairIP code (the announcement postdates the 26.4.2 sighting by an unknown lag; no APK census here — that gap is `docs/01` §1's MEDIUM grading and `docs/02`'s measured follow-up), and whether any individual user was banned (§3).

---

## 9. Deliverable 5 — How this corpus feeds docs/00–04

| Doc | What it already uses from GrindrPlus | What doc 06 adds / tightens |
|---|---|---|
| **00 — Scope verification** (HackerOne policy) | Nothing — grep shows zero GrindrPlus references in `00-scope-verification.md` (verified this session) | Context only: a fully-public 3-year record (releases, commits, PRs, README/news statements) of client-side modding of the in-scope Grindr app — the activity class whose treatment under the policy 00 verifies. No load-bearing fact flows into 00. |
| **01 — PairIP dossier** | GrindrPlus death chronology §4 (README banner, msgs 197/198, `aa497a0`, archived 2026-05-18, "VMProtect-esque" phrasing, update-block survival mechanism); sources list items 3/25/26; provenance §10 items 7/10/20 | (1) The complete 44-release table with full notes (dossier relied on the release record via `docs/03` §4's 10-release fetch); (2) independent re-verification of every date it cites (§8 matches its chronology); (3) the §2.1 bot table bracketing 26.4.2-at-announcement; (4) the issues-absence proof (§3) closing out its "no user reports" implications; (5) the `8b9d23af` diff + message evidencing server-side grid gating tied to the claimed client version. |
| **02 — Feasibility study** (26.21.0 census) | Chronology bullets ("Hookable at 25.20.0 (Nov 2025); … announced probable EOL 2026-03-21 … EOL commit authored 2026-04-04, pushed at archival 2026-05-18") and the maintainer-attribution caveat | The dated version ladder the bullets summarize (§2 + §2.1), letting 02's "targeted virtualization vs economics" question be posed against the exact release/breakage history (§5) rather than a 10-release window. |
| **03 — Legacy combo audit** (v4.7.2 × 25.21.1) | §4 cross-checked only the 10 most recent releases (v4.2.0→v4.7.2, WebFetch page 1); §1 pinning facts from `build.gradle.kts`/`version.json`/`manifest.json` | All 44 release notes incl. the pre-4.2.0 era; per-release breakage ledger (§5) for hook-tier history; tag-level verification of the compile-time pin at four tags (§7.1) confirming one-release/one-build pinning across eras; confirmation its "external source" limitation ("earlier releases were not fetched") is now lifted. |
| **04 — Forkability review** | §3 "The version-mapping treadmill" (qualitative); §6 verdict; cites release notes via 03 §4 | Quantified treadmill: 44 releases / 29 Grindr builds / 868 days, 22 of 44 notes repair-dominated (§2); the pins-and-spoof machinery as a fork-inheritance risk (§7 — incl. the runtime dependency on `raw.githubusercontent.com` version.json the fork cannot control, mirroring 04's spline.json finding); post-EOL continuation evidence (28+ closed PRs, §3.1) as a direct datum for "can it be resurrected". |

---

## 10. Gaps and non-findings (stated plainly)

1. **GitHub Issues are not minable** — disabled and verifiably absent (§3, six independent checks). Any "issue-derived signal" claim in our docs must cite news.json/PRs/release notes instead.
2. **Why the PR list endpoints fail is unexplained by GitHub**: REST `/pulls` returns 404 and GraphQL `pullRequests` returns 0 even though individual PRs (e.g. #203, #260) resolve on the same repo. I report the behaviour as observed; the census (§3.1) rests on per-number probes, which are exhaustive over 1–360.
3. **Deleted vs never-used numbers** (≈197 of 1–300) cannot be distinguished via the API.
4. **Telegram/Discord content beyond news.json is out of reach** of this session (news.json holds 23 messages, ids 164–198; the channel has thousands of posts — `t.me/GrindrPlus/38490` is referenced but not fetched).
5. **The first PairIP-protected Grindr build is not identified here** — only bracketed (26.4.2 current at announcement; 25.20.0 last-hookable). APK-level measurement belongs to `docs/02`.
6. **`samples/GrindrPlus-fork` was not mined** (adjacent sample, outside this ask's scope).
7. The local clone is depth-1; all git-history facts come from the GitHub API as stated.
