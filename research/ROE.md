# Rules of Engagement (ROE)

Adapted from the engagement-discipline rules of the local security toolchain
(exact allowlist, recorded scope, stop conditions) — applied to a research-only
program.

## 1. Boundary: research, measurement, disclosure

**Allowed:**
- Reading and synthesizing public research (papers, blogs, repos, write-ups).
- Static analysis of publicly distributed APK artifacts (unpacking, census,
  counting, mapping) for characterization.
- Verbatim policy extraction from Grindr's public HackerOne program.
- Building/testing **analysis** tooling (the `pairip-audit` census tool).
- Drafting a vulnerability **report** for anything confirmed in bounty scope.

**Not allowed (no exceptions in this project):**
- Producing, hosting, or linking working bypass code: integrity-check defeat,
  devirtualization-to-patch pipelines, repacked/modified APKs, Xposed/Frida
  hook packs that alter app behavior, signature spoofing, ban evasion.
- Any active testing against Grindr's production infrastructure (servers,
  APIs, endpoints). Client-side static analysis of the distributed artifact
  only.
- Automated interaction with the live Grindr service.

## 2. Scope record

| Item | Value |
| --- | --- |
| Engagement type | Independent security research (desk + static lab) |
| Target artifacts | Publicly distributed Grindr APK; public PairIP research; archived GrindrPlus repo |
| Authorization basis | Static analysis of publicly distributed artifacts + public research synthesis; bounty-policy scope verified in `docs/00` before any disclosure step |
| Lab | Local workstation; BlueStacks reserved for optional *observational* follow-up (logcat), not part of automated runs |
| Stop conditions | Any task that would produce a bypass artifact, target live infrastructure, or exceed the verified bounty scope → stop and record in the run's `notCovered` |

## 3. Evidence rules (deep-research discipline)

- Every load-bearing claim carries a citation (URL + retrieval date) and a
  confidence grade: `high` (primary source: repo code, vendor doc, verified
  quote), `medium` (reputable secondary), `low` (single uncorroborated source).
- Claims confirmed by a second independent pass are marked `verified`; failed
  confirmations are kept and marked `unconfirmed` — never silently dropped.
- Measured-on-artifact results are labeled separately from
  sourced-from-research results in every deliverable.
- No unsourced assertions; gaps are stated as "insufficient data found".

## 4. Hygiene

- `samples/` is gitignored; nothing downloaded enters history.
- Conventional commits; docs updated in the same commit as the code they describe.
- Tests: 100% coverage target on pure-logic modules; CI runs lint + pytest.
