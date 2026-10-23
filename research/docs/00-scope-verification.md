# 00 — Scope Verification: Grindr Bug Bounty Policy vs. Client-Side / Anti-Tamper Research

**Retrieval date for all quotes: 2026-10-22.**
**Program: Grindr, HackerOne handle `grindr` (https://hackerone.com/grindr).**
**Current policy version: id 3713946, effective 2024-03-11T16:16:05Z (`last_policy_change_at` = `2024-03-11T16:16:05.850Z`, confirmed via HackerOne GraphQL). The live policy text is identical to version 3713946 in content but — corrected 2026-10-22 — **not** strictly byte-identical: a diff shows the only difference is a single trailing newline (the version record carries one byte more than the live text, 15,652 vs 15,651 chars; re-measured this session). The earlier "byte-identical … only a trailing newline differed" phrasing was self-contradictory and is withdrawn.**

## How this was retrieved (method + limitations)

Both `https://hackerone.com/grindr` and `https://hackerone.com/grindr/policy_versions` are JavaScript-rendered single-page apps: a plain HTTP fetch of either returns only the word "HackerOne". Content was therefore obtained from three primary, unauthenticated sources, all fetched 2026-10-22:

1. **Policy text + structured scope** — `POST https://hackerone.com/graphql` with query `{ team(handle: "grindr") { policy structured_scopes(first: 50) { edges { node { asset_identifier asset_type eligible_for_bounty eligible_for_submission instruction } } } } }`. This is the same API the rendered page loads; returns the full markdown policy (15,651 chars) and 34 scope assets. Cross-checked against a JS-rendering fetch (webReader) of `https://hackerone.com/grindr` — policy text matched.
2. **Policy version history** — `GET https://hackerone.com/grindr/policy_versions.json` (the JSON backing the `/policy_versions` page): 6 versions, 2023-02-23 → 2024-03-11.
3. **Wayback Machine** — checked as a fallback: snapshot of `/policy_versions` (2023-02-24) captured only the JS shell (no version table); main-page snapshot exists (2026-09-05) but was not needed.

**Limitations (stated plainly):**

- The rendered `/policy_versions` HTML page could not be read directly (JS-rendered); its JSON backing endpoint was used instead. The version list is therefore complete (6 entries), not sampled.
- `https://www.grindr.com/.well-known/security.txt` and `https://grindr.com/.well-known/security.txt` return `Invalid .well-known request` (no security.txt published) — no independent cross-reference available from Grindr's own domain. Checked 2026-10-22.
- Scope table is from the GraphQL `structured_scopes` connection (34 nodes, `first: 50` — no pagination truncation at 34 < 50).
- Version history only reaches back to 2023-02-23; if the program changed policy before that, those versions are not exposed by this endpoint.

## Verbatim quoted clauses (policy text)

All quotes below are from the Grindr policy as served for https://hackerone.com/grindr, retrieved 2026-10-22 via the GraphQL API above — the undocumented, unauthenticated endpoint the rendered page itself loads. Verification method, stated precisely (corrected 2026-10-22): the *policy text as a whole* was cross-checked once against a JS-rendering fetch (webReader) of the rendered page and matched (method item 1 above); the individual quotes were **not** each re-checked against the rendered page, which returns only the word "HackerOne" to a plain fetch. A scripted re-check of all 59 quoted fragments against a fresh GraphQL fetch of the same policy (run 2026-10-22) found 42 byte-exact matches and 17 that match only at formatting level: the live markdown uses double spaces after sentence periods and curly apostrophes/quotes where this document transcribes single spaces and straight quotes; two Treasure Map rows are quoted with a severity label ("Critical", "Low") that the live table leaves as an empty continuation cell; and the disclosure-guidelines bullet renders as an inline markdown link where this document prints the URL parenthetically. No quoted fragment failed content-level verification, but the earlier per-quote claim "cross-checked against the rendered page" was an overstatement and is withdrawn. Quotes are otherwise unmodified except ellipses where noted.

### Program purpose

> "Grindr is excited to be working with the HackerOne security community to help find security vulnerabilities. We are happy to work together to keep Grindr and our users safe. Please report security issues or concerns you find and note the \"Out of Scope Vulnerabilities\" and \"Bounties and Rewards\" sections to understand how we reward findings."

> "Please note that this service is only for the submission of technical security issues. If you need help with a support issue (account, billing, safety, privacy etc.), please reach out to our help center…"

### Test Plan (the client-side research charter)

> "* Grindr is taking a black-box testing approach.
> * Issues with the higher severity and higher bounties as described in the \"Treasure Map\" involve finding vulnerabilities in the mobile app and how it uses the backend API's. Focus on defeating the certificate pinning used in the mobile app to find these higher severity issues.
> * You may create your own Grindr accounts for testing purposes provided you are at least 18 years of age or the age of majority in your jurisdiction.
> * When using test accounts you should only be able to see personal information that other Grindr users have allowed you to see via their account configuration. Avoid interacting with real users and instead please setup multiple test accounts when you try and identify if it is possible to access too much information from another test user's account or identify issues with features like chatting.
> * We encourage you to also perform penetration testing on administrative systems that are not part of the core app, provided they are not excluded subdomains of grindr.com, grindr.io, grindr.mobi, and grindr.work, and not those of any of Grindr's third party service providers."

### Bounty "Treasure Map" — the client-side rows

> "| Critical | Ability to inject arbitrary code into the Grindr mobile application or to hijack, tamper, or reverse engineer the Grindr mobile application in a way that causes another user's account to be taken over or significantly abused or that causes sensitive or personal data to be revealed without expected access control. |"

> "| High | API Disclosure of sensitive or personal information without expected access control or failure to protect such sensitive or personal information with reasonable encryption and key management. |"

> "| Medium | Passing untrusted inputs to backend API's or method calls made within the Grindr mobile application code or tampering with the mobile application in ways that significantly enable fraud. For example exploits that make creating large numbers of fake users possible or spamming users with fake chat messages significantly easier than doing it manually or with bot automation simulating users. |"

> "| Low | Improper Platform Usage: Misuse or failure to use cloud, mobile or web browser application platform security controls that does not affect access control or sensitive/personal data. |"

> "| Low | Any usage of dependencies that does not affect access control or sensitive/personal data. |"

### Out of Scope — the client-side-relevant exclusions (verbatim bullets)

> "* Attacks on other Grindr users requiring MITM or physical access of another user's device."
> "* Mobile client issues requiring a rooted device and/or outdated OS version. This includes ways to bypass the Grindr PIN on mobile devices if you have access to root."
> "* Third-party API Keys/Secrets embedded in mobile applications, without a clear impact, as many third-parties require this for their own client attribution purposes."
> "* Lack of certificate pinning or HSTS."
> "* Attacks that only affect the user hacking their own use or accounts associated with the same email or mobile number."
> "* Previously known vulnerable libraries without a working Proof of Concept."
> "* Any activity that could lead to the disruption of our service (DoS)."
> "* Ability to access user data that is intentionally exposed in Grindr API responses."
> "* Do not publicly disclose vulnerabilities without our explicit consent." *(from Program Rules)*
> "* Most GPS spoofing related issues."

### Program Rules (submission rules, verbatim excerpts)

> "Please provide detailed reports with reproducible steps. If the report is not detailed enough to reproduce the issue, the issue will not be eligible for a bounty."
> "* Submit one clear vulnerability per report, unless you need to chain vulnerabilities to provide impact. Include attachments such as screenshots, videos and proof of concept code as necessary.
> * When duplicates occur, we only award the first report that was received (provided that it can be fully reproduced).
> * If multiple vulnerabilities are caused by one underlying issue, only the first reported that meets our submission requirements will be accepted.
> * Social engineering (e.g. phishing, vishing, smishing or physical attacks against our employees, users or infrastructure) is prohibited.
> * Make a good faith effort to avoid privacy violations, unauthorized destruction of data, and/or interruption or degradation of our service.
> * Only interact with accounts you own or with the explicit permission of the account holder. …
> * Please do not interact with real users during your testing.
> * Do not leak, manipulate, or destroy any user data. …
> * Do not attempt to elevate privileges, or explore a system beyond the minimum necessary to prove access or attempt to pivot in any way. This will disqualify you from receiving a bounty.
> * Do not leave any system in a more vulnerable state than you found it.
> * If you encounter unanticipated access or viewing of user personal information, cease further testing and make your Submission immediately.
> * Do not mass create accounts to perform testing against our applications and services. Creating a few accounts for testing is not a problem.
> * Do not publicly disclose vulnerabilities without our explicit consent. …
> * Do not extort us."

### Confidentiality (constrains research artifacts)

> "Any information you receive, collect or otherwise obtain about us, our services, our affiliates or any of our users, employees, or agents in connection with our Security Vulnerability Reporting Program (whether after or before you joined the Security Vulnerability Reporting Program, notably as a result of you finding and/or investigating a security bug in our in-scope applications or infrastructure) (\"Confidential Information\") must be kept confidential, only used in connection with the Security Vulnerability Reporting Program, and not disclosed to any third party. You may not use, disclose or distribute any such Confidential Information, including without limitation any information regarding your participation in our Security Vulnerability Reporting Program and any Submission."

> "Once a Submission is made, Grindr reserves the right to request from you, and you already accept to abide by this request, to securely and irreversibly delete any data related to such Submission…"

### Disclosure & Safe Harbor

> "* Follow HackerOne's disclosure guidelines." (linking https://www.hackerone.com/disclosure-guidelines)

> "Any activities conducted in a manner consistent with this policy will be considered authorized conduct, and we will not initiate legal action against you. If legal action is initiated by a third party against you in connection with activities conducted under this policy, we will take steps to make it known that your actions were conducted in compliance with this policy."

### License grant on submissions

> "As a condition of participation in our Security Vulnerability Reporting Program, you hereby grant Grindr and its affiliates a perpetual, irrevocable, worldwide, royalty-free, transferrable, sublicensable, and exclusive license to use, reproduce, adapt, modify, publish, distribute, publicly perform, create derivative work from, make, use, sell, offer for sale, and import the Submission, as well as any materials submitted to Grindr in connection therewith, for any purpose."

### Structured-scope instructions for the mobile app assets (verbatim)

Both app assets carry this instruction (source: `structured_scopes` via GraphQL for https://hackerone.com/grindr, retrieved 2026-10-22):

> "Vulnerabilities that require physical, jailbroken, or device root OS access of another user's device will typically be considered out-of-scope."

Note the tension with the policy body's broader exclusion ("Mobile client issues requiring a rooted device and/or outdated OS version…" — unqualified): the asset-level note limits the exclusion to *another user's device*; the policy bullet reads as excluding root-dependent findings generally. Both are quoted; the narrower asset note does not override the broader policy bullet.

## In-scope / exclusions table

From `structured_scopes` (34 assets) for https://hackerone.com/grindr, retrieved 2026-10-22. "Bounty" = `eligible_for_bounty`; "Submit" = `eligible_for_submission`.

### Bounty-eligible, submission-eligible (core scope)

| Asset | Type | Notes (verbatim where quoted) |
|---|---|---|
| `com.grindrapp.android` | Google Play app ID | Android client. "Vulnerabilities that require physical, jailbroken, or device root OS access of another user's device will typically be considered out-of-scope." |
| `319881193` | Apple App Store app ID | iOS client. Same instruction as above. |
| `*.grindr.mobi` | WILDCARD | "This domain is used for backend API's." |
| `*.grindr.com` | WILDCARD | Website, chat server (chat.grindr.com, chat-internal.grindr.com), presence server, CDN (cdns.grindr.com), gaymoji index, captcha, admin webapp, law-enforcement reporting webapp |
| `*.grindr.io` | WILDCARD | "This domain is used for development purposes." |
| `*.grindr.work` | WILDCARD | (no instruction) |
| `web.grindr.com` | URL | "This is the Web version of the Grindr app. Only paid subscriptions have access to Grindr Web." |
| `admin.grindr.com` | URL | Admin webapp (also listed with bounty eligibility as standalone asset) |
| `reporting-portal.grindr.com` | URL | Law-enforcement reporting webapp |
| `hue.dsci.grindr.io`, `jupyter.dsci.grindr.io`, `superset.dsci.grindr.io`, `spammer-monitor.dsci.grindr.io`, `airflow-beta-master.dsci.grindr.io` | URL | Data-science internal tooling |
| `vpn.preprod.dev.grindr.io` | URL | Preprod VPN endpoint |

### Submission-eligible but NOT bounty-eligible

| Asset | Notes |
|---|---|
| `*.dev.grindr.io`, `*.dev2.grindr.io`, `preprod1.grindr.com` | "development and test systems; feel free to evaluate them, but severity levels will be reduced because we do not host customer data in these environments." |

### Out of scope (submission not accepted) — mostly third-party-hosted

| Asset | Stated reason (verbatim excerpt) |
|---|---|
| `*.intomore.com` | "Any databases, Wordpress instances, web infrastructure related to INTO is out of scope" |
| `*.grindrads.com`, `selfservice.grindr.com` | "hosted by a third-party, Bucksense… contact security@bucksense.com" |
| `go.grindr.com` | "hosted by a third-party, GoLinks" |
| `grindr.atlassian.net`, `status.grindr.com` | "hosted by a third-party, Atlassian" |
| `blog.grindr.com` | "hosted by a third-party, webflow" |
| `help.grindr.com` | "Zendesk-hosted. Do not test (ticket creation impacts support)" |
| `grindrbloop.com` | "hosted by a third-party, Squarespace" |
| `shop.grindrbloop.com`, `shop.grindr.com`, `grindrtogo.grindr.com` | "hosted by a third-party, Shopify" |
| `kindr.grindr.com` | "hosted by a third-party, Wix" |
| `investors.grindr.com` | "hosted by a third-party, Q4 inc." |
| `https://github.com/grindrlabs` | (no instruction; not bounty/submission eligible) |
| `github.com/thesokrin/vfd` | SOURCE_CODE — "Known issue; this repo describes staging systems that are no longer in use. Please do not submit reports unless you are able to demonstrate a connection between this code and live infrastructure." |

### Policy-level exclusions that bite client-side research (from the "Out of Scope Vulnerabilities" list)

- Rooted-device / outdated-OS mobile client findings (including Grindr-PIN bypass with root).
- MITM / physical-access attacks on other users.
- Attacks affecting only the researcher's own account ("the user hacking their own use").
- "Lack of certificate pinning or HSTS" (the *absence* of pinning is not a bug; *defeating* it to reach API bugs is explicitly the intended path).
- Third-party API keys/secrets embedded in the app without demonstrated impact.
- Vulnerable libraries without a working PoC; dependency takeovers without demonstrated impact on Grindr.
- DoS / service disruption of any kind.

## Policy version history (retrieved 2026-10-22 from https://hackerone.com/grindr/policy_versions.json)

| Version id | Timestamp (UTC) | Size (chars) | Client-relevant changes |
|---|---|---|---|
| 3683986 | 2023-02-23T15:12:35Z | 15,336 | (baseline) |
| 3683988 | 2023-02-23T15:17:02Z | 26,034 | Directory-page variant (adds anonymous-directory wording); no change to client clauses |
| 3687405 | 2023-05-09T21:44:06Z | 15,314 | no change to client clauses |
| 3704584 | 2023-10-06T01:01:06Z | 15,504 | no change to client clauses |
| 3713945 | 2024-03-11T16:15:08Z | 15,657 | no change to client clauses |
| 3713946 | 2024-03-11T16:16:05Z | 15,652 | **current**; only punctuation fixes vs 3713945 ("Lack of certificate pinning, or HSTS." → "Lack of certificate pinning or HSTS.") |

Verified by scripted line-diff of all six versions: every anti-tamper-relevant clause (cert-pinning test-plan bullet, the Critical "hijack, tamper, or reverse engineer" row, the Medium "tampering … enable fraud" row, the rooted-device and MITM exclusions, the embedded-keys exclusion) is textually identical across all six versions, 2023-02-23 → 2024-03-11. The program has not touched its client-side research terms in any exposed version.

## What this means for this research program

This program studies client-side protection / anti-tamper mechanisms in the Grindr Android client (PairIP / Play Integrity family). Measured against the policy retrieved 2026-10-22:

**What the policy affirmatively covers (encouraged or bounty-eligible):**

1. **Studying the Grindr Android client is in scope as an asset.** `com.grindrapp.android` is a bounty- and submission-eligible scope item. Black-box analysis of the distributed app is the program's stated method: "Grindr is taking a black-box testing approach."
2. **Defeating client-side protections to reach API-level bugs is explicitly invited**: "Focus on defeating the certificate pinning used in the mobile app to find these higher severity issues." Certificate-pinning bypass (an anti-tamper-adjacent control) is a sanctioned technique, not a violation — when used to find API/vulnerability impact.
3. **Reverse engineering and tampering research can earn Critical bounties — but only with cross-user impact**: "…hijack, tamper, or reverse engineer the Grindr mobile application in a way that causes another user's account to be taken over or significantly abused or that causes sensitive or personal data to be revealed without expected access control." Fraud-enabling tampering is Medium. "Improper Platform Usage" (platform security controls misused, no access-control/data impact) is Low. In other words: **client-integrity findings are ranked by what they let you do to other users or to fraud, not by how strong the bypass is.**
4. **Tracing untrusted input flows from client code to backend APIs** is a named Medium target — static/dynamic analysis of how the client calls APIs is squarely in-scope research material.
5. **Safe Harbor**: research "conducted in a manner consistent with this policy" is "authorized conduct" and Grindr "will not initiate legal action against you." Studying your own copy of the app, on your own devices, with your own test accounts, without touching real users or degrading the service, fits inside this clause. (The policy cannot bind third parties or immunize against non-Grindr claims — DMCA/anti-circumvention and app-store ToS exposure lie outside what a bug bounty can authorize.)

**What the policy does NOT cover — and in places affirmatively excludes:**

1. **Anti-tamper research for its own sake is not a bounty category.** The words "PairIP", "Play Integrity", "anti-tamper", "obfuscation", "RASP", and "client-side protection" appear nowhere in the policy or any of its six versions. There is no reward for "I bypassed the integrity check" without one of the enumerated impacts (account takeover / sensitive-data exposure / significant fraud enablement). A pure protection-mechanism bypass demonstrated only on the researcher's own account matches the exclusion "Attacks that only affect the user hacking their own use" — out of scope for bounty.
2. **Rooted-device findings are excluded.** "Mobile client issues requiring a rooted device and/or outdated OS version" are out of scope. This is the single most important constraint for this program: PairIP/Play-Integrity bypass work is normally demonstrated on rooted devices or emulators, and a bypass that only manifests under root will not be rewarded. The asset-level note ("…of another user's device") is narrower, but the policy bullet is unqualified; assume root-dependent results are non-bountyable.
3. **MITM and physical-access attack chains against other users are excluded** — cert-pinning defeat is sanctioned as an analysis technique on your own traffic, not as an attack on other users.
4. **Embedded third-party keys/secrets without demonstrated impact are excluded** — a common byproduct of static client analysis; do not expect credit for these.
5. **Confidentiality chills publication.** Everything learned about Grindr's services while investigating an in-scope bug is "Confidential Information" that must not be disclosed to third parties, and public disclosure of vulnerabilities requires Grindr's explicit consent. Any write-up of Grindr-client internals produced under this program's research cannot be published without Grindr's consent, and Grindr may demand deletion of submission-related data. This is a real constraint on disseminating PairIP-research artifacts that include Grindr client specifics.
6. **Submission mechanics to respect if findings are ever reported**: one vulnerability per report with reproducible steps (no repro → no bounty), first-report-wins on duplicates, no public disclosure pre-consent, exclusive perpetual license granted to Grindr on everything submitted, SLAs (first response 5 business days / triage 10 / bounty 15), and the prohibition on privilege escalation or exploring "beyond the minimum necessary to prove access."

**Bottom line.** The policy sanctions studying and defeating the Grindr client's protections *as a means* to demonstrate user-impacting vulnerabilities, and its Safe Harbor protects policy-consistent research conduct. It does **not** sanction, reward, or address protection-mechanism research *as an end in itself*: root-dependent bypasses, own-account-only tampering, embedded-key finds, and any publication of client internals are either expressly out of scope or contractually restricted. This program's PairIP/client-integrity work is authorized *ground* (own device, own accounts, black-box method) but is bounty-relevant **only** at the point a chain reaches another user's account/data or enables significant fraud on un-rooted, current-OS configurations.

## Sources

All primary material was retrieved 2026-10-22; the retrieval method and its limitations are detailed in "How this was retrieved (method + limitations)" above. Consolidated list:

1. **Live policy text + structured scope** — `POST https://hackerone.com/graphql` (unauthenticated, undocumented endpoint; the same API the rendered page loads), query `{ team(handle: "grindr") { policy structured_scopes(first: 50) { edges { node { asset_identifier asset_type eligible_for_bounty eligible_for_submission instruction } } } } }` → full markdown policy (15,651 chars) + 34 scope assets. Cross-checked in full, once, against a JS-rendering fetch (webReader) of `https://hackerone.com/grindr` — matched.
2. **Policy version history** — `GET https://hackerone.com/grindr/policy_versions.json` (the JSON backing the JS-rendered `/policy_versions` page): 6 versions, 2023-02-23 → 2024-03-11; current = id 3713946 (effective 2024-03-11T16:16:05Z).
3. **Wayback Machine** (fallback checks only; not load-bearing) — snapshot of `/policy_versions` (2023-02-24) captured only the JS shell; main-page snapshot (2026-09-05) exists but was not needed.
4. **Negative checks** — `https://www.grindr.com/.well-known/security.txt` and `https://grindr.com/.well-known/security.txt` both return `Invalid .well-known request` (no security.txt published; checked 2026-10-22) — no independent cross-reference from Grindr's own domain.

Program page: https://hackerone.com/grindr (handle `grindr`).
