# PairIP Dossier — Google Play Automatic Integrity Protection (`com.pairip.*` / `libpairipcore.so`)

**Date:** 2026-10-22 (rev. 2 — reviewer-gap pass)
**Basis:** 7 research lenses · 71 graded findings · 21 confirmation checks, all held with caveats (each check enumerated in §10.1) · **33 numbered sources read in full: 3 local git clones, 3 Google vendor pages, 5 independent write-ups (two of them JEB posts), 14 GitHub repos/issues/releases records (one of which — item 23 — is GitLab-hosted), 3 community records (1 Telegram channel + 2 forum threads), 2 app-mirror listings, 3 academic references** (3+3+5+14+3+2+3 = 33, matching the §9 numbering) — plus ~10 snippet-level or unreachable items explicitly **not** counted as read (§9 items 34–38).

**Derived overall confidence:**
- **HIGH — VM architecture & integrity mechanism, with the corroboration base stated precisely.** Three *public* RE efforts converge on every load-bearing structural claim — Solaree (2024) and ByteriaLab (2025), genuinely independent of each other (JEB/PNF 2023 independently confirms the RegisterNatives binding), plus MatrixEditor (2024–25), which explicitly builds on Solaree ("the groundwork," §6) and is therefore *corroborating but not independent*; local artifact checks were also run this cycle (`\0IAP` magic via `xxd`; opcode-table counts via `grep`). **Anchoring caveat:** which app each team's `libpairipcore.so`/vmcode sample came from is not recorded in the material available to this dossier (the only sample attribution in the corpus is TU Graz's `com.openai.chatgpt` example — §6), so per-build-variation claims (§2.4) cannot be anchored to sample identity (§8.1.11). [high.corrob.2026 — dependency structure as stated]
- **MEDIUM — Grindr deployment chronology.** Primary-source and dated (GrindrPlus README/news.json/git metadata/Telegram), but the exact first protected Grindr version is unmeasured — no APK was available for census (`samples/apk` empty). The underlying records are primary and high-confidence; the *overall* grade is MEDIUM because the onset is bracketed, not measured (tag grade and section confidence are different axes — see tag scheme below). [high.primary.2026]
- **LOW–MEDIUM — bypass working statuses.** Self-reported by tool authors; nothing was executed or tested against a live build in this program (ROE). [low.unverified.2026]

**Provenance tag scheme (inline):** `[high.local.2026]` verified on a local clone/artifact this cycle · `[high.corrob.2026]` ≥2 independent sources agree · `[high.vendor.2026]` Google documentation · `[high.primary.2026]` first-party project record · `[med.web.2026]` single reputable web source · `[med.snippet.2026]` search-snippet level only · `[low.unverified.2026]` content unreachable or uncorroborated · `[low.spec.2026]` the source itself hedges or speculates.
**Tag granularity:** a tag grades the *claim it follows*. Where a paragraph carries a single trailing tag, it applies to every claim in that paragraph **unless** a sentence carries its own tag; paragraphs mixing source strengths use sentence-level tags. A high tag on a *source* (e.g. a vendor page quoted verbatim) does not grade the evidentiary weight of a *number the source asserts* — such cases are hedged explicitly in the text.

---

## 1. Executive summary

**PairIP is the community name for Google Play's "automatic integrity protection"** — an opt-in, partner-gated service that rewrites an app's bundle at Play-signing time. Google's own documentation never uses the name "PairIP"; it describes only "an anti-tamper code protection service" adding "runtime checks … hard to remove with advanced obfuscation and anti-reverse engineering techniques" [high.vendor.2026]. Everything **publicly** known about the `com.pairip.*` Java classes and `libpairipcore.so` comes from third-party reverse engineering (an absolute about *all* knowledge — including any private/undisclosed knowledge — would be unverifiable). [high.corrob.2026] The name decodes as **P**l**A**y**I**nteg**RI**ty**P**rotect (pairipcore-vm README). [high.local.2026]

**Its distinguishing mechanism is code virtualization at the native level.** Selected Java/Kotlin method bodies are replaced with calls to `com.pairip.VMRunner.invoke(...)`, which loads per-method bytecode blobs from the APK's assets and executes them inside a custom interpreter in `libpairipcore.so` — a second VM layered on top of the Dalvik/ART VM. [high.corrob.2026] The interpreter's opcode-to-handler mapping is **randomized on every library build** [high.corrob.2026] — this alone is why opcode tables do not transfer between releases (§2.4). Separately, every instruction's control flow is **hash-chained with an FNV-family hash — documented as FNV-1, with an unadjudicated FNV-1a variant in the same research codebase (§2.6, §10.3.12) — with a fallback address**, so bytecode tampering silently redirects execution down a fallback path rather than producing a clean, debuggable crash (what that fallback then does is itself undocumented — §8.1); the hash chain contributes tamper-redirection, not table non-transfer. [high.corrob.2026]

**The protection is layered.** (1) A Java-side `SignatureCheck` runs at the earliest possible startup point and crashes the app on signature mismatch [high.local.2026]; (2) a native `protections_main` dispatcher performs anti-debugging (raw `prctl`/`clone`/`waitpid`/`ptrace` syscalls), `/proc/self/maps`+`status` scanning, full frida-server detection, and system-property sweeps [high.corrob.2026]; (3) a licensing layer (`com.pairip.licensecheck`) prompts "get this app from Google Play" or silently exits [med.web.2026]. Google documents the tamper response as stopping the app "predominantly by crashing the app." [high.vendor.2026]

**Grindr adopted it; GrindrPlus shut down, attributing its death to it.** The module's own records date PairIP arrival between Grindr 25.20.0 (Nov 2025, still hookable) and the 26.3/26.4 era (current at announcement time, per the APKPure listing — mirror-derived, not APK-verified). GrindrPlus announced probable end-of-life on 2026-03-21 ("advanced native-backed VMProtect-esque protections … no bypass publicly available"), declared the introduction of "PairIP DRM" unfeasible-to-support on 2026-04-02, **authored** the "EOL" commit on 2026-04-04 (pushed/commit-dated 2026-05-18 at archival — §4 explains the split), and was archived 2026-05-18 — eleven days after Grindr server-side-cut the last supported version (~2026-05-07). [high.primary.2026] The maintainer's own attribution of the death is loss of hookable Java surface (virtualization); this is the best-supported explanation and consistent with the architecture, but it is **not demonstrated method-by-method** — see §4 for what is and is not established. [med.web.2026]

**The public bypass landscape has not *decoded* the VM — with "defeat" defined.** Under this dossier's bar (defeat = portable decoding of the bytecode), no tool qualifies; per-build opcode randomization stalled generalizable VM analysis in 2025 (best public tooling: ≈86% format coverage **on its target binary** — 134/155, §2.7; semantics for 14 of ~99 opcodes; decompiler "WIP"). A weaker, **per-app** bar is being met: restoration/dump pipelines produce working unprotected builds per-app (§5) — the attacker mission of running a modified app is achievable per-app, which is a different and lower bar than portable decoding. What remains active in 2026 is bytecode-level *restoration* (Morphe-ecosystem patches that neutralize `VMRunner` entry points and restore extracted methods) plus per-app runtime dumpers — approaches that sidestep the VM rather than decode it. Descriptive only; see §5. [high.corrob.2026]

**Biggest verification gap:** no Grindr APK was available in this workspace, so which Grindr versions ship `com.pairip.*`/`libpairipcore.so`, how many methods are virtualized, and which layers current builds carry are **unmeasured** (insufficient data — deferred to the APK-census deliverable, `docs/02`). *(Chronology note, added 2026-10-22: this statement and the other "empty `samples/apk`" statements in this dossier describe its own earlier authoring session and were true then. Later the same day, the `docs/02` census session fetched two Grindr APKs into `samples/apk/` and produced `samples/out/census.json` + `census-base.json`, so those directories are no longer empty; the gap was closed for exactly one build — Grindr 26.21.0/189896, whose base split measured 20 VM-stub methods of 422,621 (`docs/02` §2.2, §4). The version-onset question remains open (`docs/02` §7.6).)*

---

## 2. How the VM works

### 2.1 The virtualization marker and execution pipeline

A virtualized DEX method is recognizable by its Java/Kotlin body being replaced with a call to `com.pairip.VMRunner.invoke(String vmByteCodeFile, Object[] args)`. The decompiled `VMRunner` in Solaree's write-up shows the chain: `invoke()` → `readByteCode(vmByteCodeFile)` (reads a blob from the APK's `assets/`) → `executeVM(byte[] vmCode, Object[] args)` — a `static native` method loaded via `System.loadLibrary("pairipcore")` (`samples/pairipcore/README.md:91–145`, hook output at `:196–202`). MatrixEditor's docs concur: protected classes "invoke `VMRunner.executeVM` instead of executing regular Java code," with bytecode "stored within the assets directory" (`samples/pairipcore-vm/docs/source/introduction.md:21–31`). [high.local.2026]

```
Java/Kotlin method body (removed by Play at bundle protection time)
   └─> VMRunner.invoke(String vmByteCodeFile, Object[] args)      [Java, com.pairip]
         ├─ readByteCode(vmByteCodeFile)  → assets/<name> blob     ("\0IAP" file)
         └─ executeVM(byte[] vmCode, Object[] args)                [JNI, no Java_* export]
               └─ libpairipcore.so: JNI_OnLoad → RegisterNatives → vm_dispatch_{0,1,2}
                     VMContext { void** ptrTable; char* vmCode; uint vmCodeLength; uint pc; }
```

A ByteriaLab quote used by one lens ("the parameters we see in the invoke() call … correspond to the names of the bytecode files in the assets/ folder") could **not** be located in the named source and is carried as **unverified** — its substance is independently established by the verified `vmByteCodeFile → readByteCode` chain above. [med.web.2026]

### 2.2 Native binding: RegisterNatives, not Java_* exports

`libpairipcore.so` exports no `Java_` symbols. `executeVM` is bound at load time from the tail of `JNI_OnLoad` via `JNIEnv->RegisterNatives` (`introduction.md:44–65`, registering `Java_com_pairip_VMRunner_executeVM`), with signature `([B[Ljava/lang/Object;)Ljava/lang/Object;` (Solaree hook output, README.md:196). [high.local.2026] JEB's independent recovery: "libpairipcore.so registered one method for com.pairip.VMRunner.executeVM, and mapped it to a routine at 0x5F180." [med.web.2026] The library also fixes up offsets at runtime ("changes offset in runtime, probably code decryption too" — Solaree's own hedged guess, README.md:209 [low.spec.2026]); **on that basis Solaree *recommends* dumping the process at runtime before static analysis — a recommendation, not a demonstrated necessity.** Indeed, MatrixEditor's automated Ghidra analysis of the dispatcher switches (§2.7, §6) shows static analysis of the binary is at least partially possible; whether that pipeline's input was a runtime-dumped image or the shipped `.so` is **not recorded in the sources read** (§8.1.10 context; open question §8.1). [high.local.2026 for the quote; med.web.2026 for the conclusion]

### 2.3 The interpreter: three dispatchers, one context

Instruction dispatch is split across three native functions over a `VMContext { void** ptrTable; char* vmCode; uint vmCodeLength; uint pc; }`: `vm_dispatch_0` and `vm_dispatch_2` are large switch statements; `vm_dispatch_1` is a heavily control-flow-obfuscated function of roughly **16,000 lines** of decompiled C (`docs/source/automation.md:6–8,76–78,140–147,173`; struct verbatim at `docs/source/cfg.md:24–31`). What *distinguishes* the three — which instruction classes each dispatcher handles, and why the interpreter splits across three functions at all — is not described in the sources read (§8.1.10); that gap matters for anyone targeting tooling at a specific dispatcher. [high.local.2026]

### 2.4 Per-build opcode randomization — the load-bearing structural fact

MatrixEditor: "Google has introduced a feature that randomizes the opcode handler mapping each time the library is compiled" (`instructions.md:176–180`) and "the VM is custom for every release of an application" (`README.md:7–10`). Two already-divergent raw-opcode decoders coexist in that codebase (`decode_opcode_v0` vs `v1`, `pairipcore/opcode.py:7–20`). ByteriaLab independently: "since opcodes change during each compilation, there is no way to decode them as a fixed opcode." This is the structural reason **no complete, portable public opcode table exists**. [high.corrob.2026]

**Scope of the randomization (open, §8.1.14):** the sources say "each time the library is compiled" (MatrixEditor, `instructions.md:176–180`) and "custom for every release *of an application*" (MatrixEditor README) / "during each compilation" (ByteriaLab) — phrasing that fixes variation **per app-release** but is silent on whether two **different apps** protected in the same period share an opcode mapping. That distinction decides whether per-build tooling generalizes across apps or only across releases of one app; no source read answers it. [med.web.2026 — for the absence]

### 2.5 Bytecode file format

Measured locally this cycle: `xxd samples/pairipcore-vm/assets/data.vmcode` shows magic `0049 4150` (`"\0IAP"`) at offset 0 — a **4-byte** magic. Format otherwise per MatrixEditor: an encoded u32 at `+0x04` from which the entry point is derived (`context.py:67–77`); addresses encoded as `((enc ^ ~code_length) & 0xFFFFFFFF) % code_length` (`context.py:50–61`); encoded 16-bit opcodes; per-instruction layouts described by "format IDs" (e.g. `20a` = `<stack-vars><extra-vars><store-var>`) (`instructions.md:56–77,186–201`). [high.local.2026]

**Flagged layout tension (unadjudicated — §10.3.15):** ByteriaLab describes the library as skipping "the first 8 bytes," in phrasing tied to the `.IAP` magic. A 4-byte magic plus the 4-byte encoded u32 at `+0x04` makes an 8-byte header, so the two descriptions are compatible **only if** ByteriaLab's "8 bytes" denotes the whole header (magic + entry-point u32) rather than the magic alone; whether executed code literally resumes at `+0x08`, or the `+0x04` u32 participates past the skip, was not adjudicated here. Both sources are quoted as-is; the tension is recorded, not resolved.

### 2.6 Hash-chained control flow (tamper → fallback path)

Every instruction embeds an `insn_info_t` header — XOR value (+0x0), 64-bit FNV hash (+0x4), hash-data address (+0xc), hash-data length (+0x10), **next address (+0x12)**, **fallback address (+0x16)**. Execution verifies the instruction hash (offset basis `0xCBF29CE484222325`) over the instruction data and picks between the two candidate continuations; tampering redirects execution down the fallback path rather than producing a usable modification (`instructions.md:83–123`; `verify_fnv` at `context.py:31–44`; ByteriaLab: "If an external modification is made to the opcode, the FNV-1 hash verification will always redirect execution to the fail address"). [high.corrob.2026]

- **Variant caveat:** the docs and Python implementation say FNV-1 (multiply-then-XOR, `context.py:23–28`); the Rust `src/fnv.rs` in the same repo implements FNV-1a (XOR-then-multiply). Which variant production `libpairipcore.so` uses was **not adjudicated** (§10.3.12); this dossier says "FNV-family / documented FNV-1" wherever the distinction matters.
- **Open detail:** what the fallback path then *does* — terminate, decoy, or execute alternate logic — is not described in any source read (§8.1).

### 2.7 What is actually known about opcode semantics — and reconciling the denominators

The shipped public table (`pairipcore/insn.py:348–444`) registers **99 opcodes, of which only 14 have identified semantics** (names like `Add_Int_30c`, `CastToInt_22d`); 85 are format-only placeholders `"_"` (grep-measured this cycle). MatrixEditor's automated Ghidra+tree-sitter pipeline recovered format IDs for ~90/159 opcodes from dispatcher switches — **134/155 (~86%)** including the obfuscated dispatcher — and "0x98 total / 0 missing" for one specific binary (`automation.md:141–143,267–268,356–359). The repo itself marks the table "TODO: scheduled for removal" and the decompiler/disassembler "WIP." [high.local.2026]

**Denominator reconciliation (as far as the sources allow):** these numbers do **not** measure the same thing, and there is no single canonical opcode count. 99 is the size of the *shipped Python table* (the format set captured for the specific build that research targeted). 159 and 155 are *per-binary totals of handler slots* observed in the dispatcher switches of the particular binaries the automated pipeline analyzed; 134/155 is that pipeline's format-ID recovery on its target binary, and 0x98 (=152, "total") with "0 missing" is the post-recovery count for one named binary. Because the opcode mapping is randomized per build (§2.4), different binaries legitimately expose different totals. **No public source states the size of the "complete" instruction set for an arbitrary build, and the relationship between these particular totals was not re-measured in this cycle** — the honest reading is "on the order of ~100–160 handler slots per build, of which public semantics exist for 14." [med.web.2026]

**No public tool that decodes PairIP bytecode generally was found in this corpus** — an unbounded absence claim cannot be proven, so this carries the same hedge as §10.3.4: no counter-example surfaced in the searches conducted. [high.corrob.2026]

### 2.8 String protection

Strings are XOR-encrypted inside the vmcode assets with a single 256-byte key **reused across all bytecode files of an app** ("Surprisingly, the decoding key remains consistent across all files!", `docs/source/strings.md:51–53`), with the source's length formula `length = 2 + (u16@key ^ u16@data)` (`strings.md:13–22`). The exact offsets of the two u16 values within the key material and the ciphertext are **not restated in the material available to this dossier** — the formula is quoted as the source gives it, and `strings.md` is cited for the layout rather than paraphrased into specifics we cannot verify. The key is recoverable by brute-force heuristics (Rust `find_key_loc`). Separately, JEB documents that string constants are removed from the DEX itself and restored at runtime through `libpairipcore.so`. [high.corrob.2026]

### 2.9 Academic framing

No peer-reviewed paper studies PairIP itself. Zhao et al. 2020 (*Computers & Security* 94:101821, prototype Dex2VM on LLVM) published — **three to four years before the earliest public PairIP analyses in this corpus** (JEB's PairIP-specific post: Apr 2023; PlatinMods licensecheck tutorial: Jul 2023; Solaree: Apr 2024) — "a novel approach to transfer code virtualization from DEX level to native level" (quote verified via the whiterose eprints abstract): the same *family* of design — compile-time lifting of DEX method execution into a native-level interpreter — that PairIP later shipped in production form. A causal connection between the prototype and PairIP is neither claimed nor claimable from this corpus; "family resemblance," not identity. Blázquez & Tapiador 2025 (*ACM CSUR* 58(2) Art. 36; ~2.45M apps surveyed, **~4% with any detectable protection — protection-in-general, not PairIP specifically**) characterize code virtualization as "an architecture that exists only for this specific protected build" — the academic framing of per-build VMs. **Both quotes are second-hand, taken via the authors' Quarkslab summary blog (source 32); the CSUR paper itself was not read.** [med.web.2026]

### 2.10 Relation to prior protectors (bounded by what this corpus actually supports)

- **DexGuard-style Java p-code VMs (Java-side):** PNF/JEB's 2020 work shows such DEX-level VMs (5 parallel stacks, two large switches) were automatically devirtualizable in JEB since v3.22 via concolic execution, CFG unflattening, and stack analysis. PairIP moves the interpreter **native** and randomizes opcodes per build — precisely the two properties that remove that playbook. An automated-devirtualization asymmetry therefore exists: tooling that worked on Java-side VMs does not transfer. [med.web.2026]
- **Promon SHIELD:** appears in this corpus only as Solaree's comparison point for frida-server checking ("not only default port, like Promon Shield does") — one aside, not a systematic comparison. [high.local.2026]
- **"VMProtect-esque":** GrindrPlus's own phrase for the native-VM character (news msg 197) — a characterization, not an analysis. [high.primary.2026]
- **What is supported as distinctive here:** native-side interpreter over Play-selected DEX methods + per-build opcode randomization + injection at Play-signing time. A systematic comparison against commercial native-VM protectors (VMProtect, Themida, etc.) was **not undertaken** and would be needed to judge true novelty. [high.corrob.2026]

---

## 3. Integrity and licensing layers

### 3.1 What Google actually documents

- Play Console Help (art. 10183279): "Google Play's automatic protection" is opt-in, in three tiers — **installer check** (runs "at runtime when your app is opened"; failure → "users will be prompted to get your app on Google Play"), **anti-tamper protection** (failure → Play prompt "or the app will not run"; "the runtime check will stop your app from running, predominantly by crashing the app"), and a partner-gated **device check** that "makes it harder for attackers to run your app in unknown and emulated environments." The service "replaces the need to use the Play Licensing library," works offline, requires Play App Signing + App Bundles + min API 24 and all four ABIs, is partner-gated (e.g. ≥US$25k/mo consumer spend or 1M+ MAU sensitive category), and the page never uses "PairIP." Vendor docs mention **no** root, debugger, or instrumentation detection, and caution "Anti-tamper protection cannot guarantee prevention of all modification and redistribution." [high.vendor.2026]
- developer.android.com automatic-protection page (updated 2026-02-26, marked confidential/select-partner yet publicly fetchable): "Google Play adds runtime checks to your app's code … hard to remove with advanced anti-tamper protection." It further claims **"on average ~80% lower unauthorized usage"** — *Google's self-reported figure from unspecified "internal analysis" with no published methodology; the [high.vendor] tag above grades the page's authenticity, not this number's evidentiary weight, and it should not be cited as an independent measurement.* The page describes a select-partner EAP "**custom method protection**" that obfuscates developer-selected method bodies via a `@PlayAutomaticIntegrityProtection` annotation that "will be removed automatically from the dex code of your bundle at the time when Google Play protects your bundle," with per-call overhead "of many milliseconds" and explicit diff-based-attack warnings against turning protection off post-publication. **Note the vendor's own verb is "obfuscates (hides)" — the page documents method-level protection, not virtualization or any interpreter; the VM mechanism is established only by third-party RE (§2).** [high.vendor.2026]
- developer.android.com fraud-prevention/environment page: protection is "an anti-tamper code protection service … adds checks to your app's code and makes them hard to remove," offline, zero developer work, select Play partners. [high.vendor.2026]

### 3.2 Java-side signature check (earliest startup)

`com.pairip.SignatureCheck.verifyIntegrity(context)` is called from `Application.attachBaseContext` **before** `super.attachBaseContext(context)` — the earliest possible startup point. It computes `Base64(SHA-256(PackageInfo.signatures[0]))` and, when the digest satisfies none of three comparisons — `verifySignatureMatches(str)` (against `expectedSignature`), `expectedTestSignature`, and `ALLOWLISTED_SIG` (`README.md:74–75`) — throws `SignatureTamperedException("Apk signature is invalid.")` — an uncaught `RuntimeException`, i.e., a crash (`samples/pairipcore/README.md:38–86`). Per Solaree's decompile of its (single, unnamed-app) sample: `expectedSignature = expectedLegacyUpgradedSignature = expectedTestSignature = "ag4imYhJd4ISc+m2klK8n1Oq2WId2REza1aYcssrVwc="` and `ALLOWLISTED_SIG = "Vn3kj4pUblROi2S+QfRRL9nhsaO2uoHQg6+dpEtxdTE="` (`:56–60`). **Whether the expected-signature value is the protected app's own Play signature (per-app, injected per bundle) or a Google-global constant cannot be determined from one app's sample — this decides whether the Java check is per-app-configured or universal, and it is open (§8.1.12).** [high.local.2026 for the decompile; the generalization question is open]

### 3.3 Native `protections_main` (the integrity layer around the VM)

Adjacent to the VM dispatcher, `libpairipcore.so` runs a second obfuscated switch (Solaree's decompile, README.md:219–528 — **98 case labels** by grep; one lens's "~80" and another's "~70" were corrected during confirmation). It mixes: dynamic libc imports (`dlopen`/`dlsym`/`dlclose`); raw-syscall anti-debugging (`prctl` 167, `clone` 220, **wait4 260** — Solaree writes "waitpid," which exists only as a libc wrapper over the `wait4` syscall; correction logged in §10.4 — `ptrace` 117, `kill` 129, `exit` 93; traced at README.md:609–616); `/proc/self/maps` and `/proc/self/status` scanning executed by a cloned child that "crashes, if it finds injected Frida in own process" (:619); system-property enumeration via `__system_property_read_callback` ("it checks all your device properties to make sure it's real device and not some kind of emulator," :626–655 — author's characterization); and "Full frida-server check (not only default port, like Promon Shield does)" (:18), with the author explicitly guessing the mechanism at :658. [high.local.2026]

**ABI note:** the syscall numbers cited above are **AArch64** syscall IDs. Which ABIs `libpairipcore.so` actually ships (arm64-v8a only, or also armeabi-v7a/x86_64/x86) was **not recorded by any source read**; the vendor's "all four ABIs" prerequisite constrains the *app bundle*, not which ABI slices carry the protector. This matters for emulator/ABI analysis planning and is left open (§8.1). [med.web.2026 — for the absence]

Independent corroboration of the check family: frida-interception-and-unpinning issue #124 (HoffiF, 2024-12-04, app nl.efteling.android) reports pairipcore "prevents repacking, tampering, code injection, and the usage of tools such as frida-server," scans "for frida-server on various ports," uses "prctl, clone, waitpid, and ptrace," and scans `/proc/self/maps` + `/proc/self/status`. [high.corrob.2026]

### 3.4 Licensing layer (`com.pairip.licensecheck`)

- **Play-redirect path:** ge0.dev's RE of `LicenseClient.initializeLicenseCheck()` shows dispatch on `licenseCheckState` between a local path (`localCheckEnabled` → background executor) and `connectToLicensingService()`, with `LicenseResponseHelper.validateResponse(Bundle, String)` verifying the server response and `retryOrThrow()`/`handleError(LicenseCheckException)` error paths producing a "get this app from Google Play" screen for failing sideloaded copies. [med.web.2026]
- **Silent-exit path:** getpaseo/paseo issue #4417 (firsthand logcat, Play-installed app, Samsung S24/Android 16): `LicenseCheckException: Licensing service unexpectedly disconnected` at `LicenseClient.onServiceDisconnected(LicenseClient.java:413)` followed by `System.exit(0)` — no crash dialog, tombstone, or Play crash report. (The issue's automated reproduction bot reported "cannot reproduce": per the bot-repro record in the issue thread — the lens record of the full issue — it ran against a sideloaded **0.11.0** build in which no PairIP code was present. This is *consistent with* PairIP being injected after upload to Play, **on the premise** that the bot's APK came from a non-Play-injected channel — paseo is open-source, so a repo-built APK is the likely source; the repro result alone does not prove the injection point. Issue open, triaged p2.) The failure response therefore includes silent self-termination, not only crashes. [med.web.2026]
- **Corroborating hints (snippet-level, not read):** Stack Overflow 79347596 / 79759688 (crashes via `retryOrThrow` / `startErrorDialogActivity`, LicenseClient.java:115) and Google Issue Tracker 497588848 (`handleError`, LicenseClient.java:492) — see §10.3. [med.snippet.2026]
- APKiD issue #495 (Apr 2026): the licensing check can be present and auto-run at launch (observed from `contentprovider.onCreate()`) **even without** `libpairipcore.so`; "Only the license check is always present, the other two are only for select developers." PlatinMods (Jul 2023) documents the same Play-redirect family (`LicenseClientV3`). [med.web.2026]

**Evidence gap, stated:** the local clones ship no `licensecheck` source (grep for "license" across both clones + GrindrPlus: zero matches), so all licensing internals rest on web sources; the paseo logcat is the strongest of them.

**Unexplored tension (open question, §8.1):** the vendor documentation says automatic protection "works offline" (§3.1), yet the licensing layer's *primary* path is a bound service with server-response validation, and the observed silent-exit fired on service *disconnect*. A local path exists (`localCheckEnabled`), so the layers are evidently not uniformly network-dependent — but which tiers function without network, and what offline failure looks like, is **not established by the sources read**.

**Reliability / false-positive surface (open, §8.1.15):** the paseo case above is a Play-installed, *untampered* app silently exiting on a licensing-service disconnect — and no source read addresses how often the integrity layers misfire on legitimate users (rooted-but-legitimate devices, custom ROMs, work profiles, connectivity flaps). This bears directly on defender deployment decisions and on the credibility of Google's self-reported ~80% figure (§3.1).

### 3.5 Vendor tier ↔ RE-observed layer mapping (explicitly inferential)

Google documents *tiers*, not implementations; no vendor statement ties any tier to specific code. The following alignment is inference from observed behavior and should be read as such:

| Vendor tier (documented, §3.1) | RE-observed candidate implementation | Status of the alignment |
|---|---|---|
| Installer check | `com.pairip.licensecheck` installer/licensing paths ("get this app from Play") | Inferential — consistent naming/behavior; no vendor statement |
| Anti-tamper protection | Java `SignatureCheck` (§3.2) + native `protections_main` (§3.3) + FNV VM-internal integrity (§2.6) | Inferential — composite guess; which parts implement the vendor's "checks" is unstated |
| Device check (partner-gated) | System-property sweep characterized as emulator detection (§3.3) | The **one** alignment the sources themselves suggest (Solaree's characterization ↔ vendor's "unknown and emulated environments"); still an RE characterization, not a mapping |

[med.web.2026 for the mapping as a whole; the tiers themselves are high.vendor.2026]

---

## 4. Deployment in Grindr (and the death of GrindrPlus)

All dates below are from primary project records unless tagged otherwise.

| Date | Event | Source |
|---|---|---|
| 2025-11-22 | Grindr 25.20.0 released (APKPure) — later shown still hookable | [med.web.2026] |
| 2025-12-17 / 12-25 | 25.21.0 / 25.21.1 released; no module release for either | [med.web.2026] |
| 2026-01-18 / 01-21 | 26.0.0 / 26.0.1 released; no module release | [med.web.2026] |
| 2026-01-28 | Last module release **v4.7.2-25.20.0** (Grindr 25.20.0 / build 147239) | [high.primary.2026] |
| 2026-02-11 | Unreleased WIP: "Partial update to 26.0.1" (build.gradle pins 26.0.1/149389) | [high.primary.2026] |
| 2026-03-06 / 03-12 | Grindr 26.3.1 / 26.4.0 current at announcement time (APKPure listing — this is the onset bracket's upper endpoint; mirror-derived, not APK-verified) | [med.web.2026] |
| 2026-03-21 | news.json msg 197: PairIP adoption announced; "VMProtect-esque … no bypass publicly available online right now … probably the end"; "Last G+ version works as of today" (Telegram corroborates verbatim) | [high.primary.2026] |
| 2026-04-02 | news.json msg 198: wind-down "unfeasible with the recent introduction of PairIP DRM"; predicts archival when Grindr enforces updates past supported versions | [high.primary.2026] |
| 2026-04-04 | EOL commit `aa497a0` **authored** (AuthorDate; README warning added) — README: "Grindr has started using PairIP for their latest versions of the app. **This effectively marks the end of this module, and no further updates will be released**" | [high.primary.2026] |
| ~2026-05-07 | Grindr 25.20.0 stops refreshing/sending messages (server-side enforcement; XDA user reports, confirmed by a second user) | [med.web.2026] |
| 2026-05-18 | EOL commit **commit-dated and pushed** (CommitDate 2026-05-18; GitHub `pushed_at` 2026-05-18T08:31:33Z matches), and repo archived same day (`archived:true`) | [high.primary.2026] |
| 2026-10-16 | Latest Grindr 26.21.0 on APKMirror — roughly 30 further 26.x releases since the module's death (whether each carries PairIP is **unverified** — see below) | [med.web.2026] |

**On the AuthorDate/CommitDate split:** the EOL commit carries AuthorDate 2026-04-04 and CommitDate 2026-05-18, with the repo's `pushed_at` equal to the CommitDate — consistent with the maintainer preparing the EOL commit in April and pushing it at archival time in May. The dossier therefore says "**authored** 2026-04-04, **pushed/archived** 2026-05-18" and avoids the ambiguous bare "committed on <date>." [high.local.2026]

**Onset bracket — insufficient data:** no public source read names the exact first Grindr version shipping `libpairipcore.so`/`com.pairip.*`, and `samples/apk` was empty at this dossier's authoring, so no APK-level check was possible *(chronology: later the same day — 2026-10-22 — the `docs/02` census session populated `samples/apk/` with the 26.21.0 bundle and base APK and censused the base split; the bracket below nonetheless remains open because only that one build was measured, `docs/02` §7.6)*. PairIP onset is bracketed **25.20.0 (2025-11-22, hookable) → 26.3.1/26.4.0 (current at announcement, per the APKPure listing — the 2026-03-06/03-12 table row)**. Versions 26.1.x/26.2.x are **not enumerated in the sources read** (the APKPure listing was consulted for specific dates only); on the observed ≈2–4-week cadence they presumably shipped inside the 2026-01-21 → 2026-03-06 gap and therefore inside the bracket. The ambiguous window is accordingly stated as **25.21.0 (Dec 2025) through 26.2.x**: the team never released support past 25.20.0 but left an unreleased WIP pinning 26.0.1 — it is unknown whether 26.0.1 predated PairIP or was an abandoned attempt against it. A definitive answer needs APK diffing (`tools/pairip-audit` exists for this once an APK is fetched). [med.web.2026]

**Two version numbers, two meanings (correction to the program README):** at the EOL commit, `app/build.gradle.kts:16–24` pins the *build target* at Grindr **26.0.1 / 149389** (module versionName 4.8.0-…), while `version.json`'s **25.21.1 / 148541** is merely the latest-version value fetched from APKMirror and fed to the update-spoofing hook (`hooks/DisableUpdates.kt:21,68–102`). The root README's phrase "pinned Grindr 25.21.1" conflates the two. [high.local.2026]

**Why the module died — what is and is not established.** The *documented* chain: the pre-PairIP survival mechanism was the module's own update-block hook ("Disable forced app updates (extend mod lifespan)", README.md:67), which let the 25.20.0 population survive until Grindr's server-side cutoff completed the predicted wind-down. The *attributed* cause of hooking death is virtualization: protected methods' Java bodies are gone, executed as native-VM bytecode, so Xposed method hooks have no Java body to intercept — this is the maintainer's own attribution ("advanced native-backed VMProtect-esque protections," "no bypass publicly available") and is architecturally consistent. **It is not demonstrated method-by-method:** this dossier does not establish which specific methods GrindrPlus hooked, nor that those specific methods were virtualized in Grindr's protected builds (no APK was available); and Tier-1 evidence (§5, pairipfix) shows Java hooking *still works* on the non-virtualized `com.pairip` license classes via LSPosed. The claim is therefore "best-supported explanation, consistent with maintainer statements and the architecture," not a proven per-method causal chain. **No public source documents an explicit Xposed/LSPosed detector inside PairIP** (closest: SReverse's hedged note that "the guard knows common hook frameworks" via GOT/PLT rewrites — a lead, not a proven check [low.spec.2026]). An XDA user's distinction (Apr 2026) matches the evidence: PairIP *License* check workaroundable, PairIP *Core* "impossible for now" due to encrypted native code. The developer's farewell (May 8, 2026, XDA post #3200): "This is indeed the end of the mod … Please don't message me … about trying pairip fixes." [med.web.2026]

**Presence of PairIP in current 26.x builds:** inferred from the project records above; **not APK-verified** — stated as unmeasured, which is why the 2026-10-16 table row says "further 26.x releases" rather than asserting protection per release. [low.unverified.2026]

---

## 5. Public bypass landscape — **descriptive only**

> ROE note (per `ROE.md` §1 and the lenses' rules of engagement): this section *describes* what exists, in the sources' own words, at the what-it-outputs level. No bypass code, payloads, chaining instructions, or step-by-step defeat procedures are reproduced. Solaree's repo embeds working payloads (a RegisterNatives Frida hook, a SIGKILL-to-child trick, PADumper usage); they are referenced by existence only. Nothing below was executed or tested against a live build; all "working" statuses are self-reported by their authors.

The landscape splits into three tiers with different survival rates:

**Tier 1 — integrity/license-check bypasses (trivially reproducible, perpetually re-published):**
- `ahmedmani/pairipfix` (LSPosed module, 691★, pushed 2026-04-20) defeats exactly one layer — the install-source/license dialog — by hooking the check in the target app; its own README enumerates what it does *not* defeat (signature validation, Frida/debugger detection) and warns blocking the VM code "would simply crash the app"; reported partial ("detected on some devices, while it works flawlessly on others"). Notably, this repo is also evidence that **Java-side hooking of `com.pairip` classes remains possible** — the license classes are not virtualized. [med.web.2026]
- `SafaSafari/bypass_libpairipcore` (78★, single commit 2025-04-21) — static tamper/signature bypass: re-points the manifest Application entry away from the PairIP wrapper and repairs APK CRC32s so the patched build passes `libpairipcore`'s validation; untouched since April 2025. [med.web.2026]
- `Anon4You/PKiller` (33★, 2025-12-12) — Termux "Pairip Licence Check Remover"; no versioning or compatibility claims. [low.unverified.2026]
- petruknisme, "Bypassing PairIP Integrity Checks" (Medium, announced on X 2025-12-02, snowflake-decoded in-session): existence and date verified; **content unreachable (403/500) — technique and current status unverified.** [low.unverified.2026]

**Tier 2 — VM-layer analysis (stalled 2025 at analysis tooling):** MatrixEditor (analysis to the opcode boundary, workaround "WIP!"), Solaree (integrity-layer bypasses characterized as "easily bypassable" — e.g., killing the anti-debug child after `waitpid` — but no VM defeat), ByteriaLab (working *analysis* techniques: Frida Stalker to locate `executeVM` via RegisterNatives, runtime dumping of the self-modifying library; explicitly no bypass of either layer). Per-build opcode randomization defeats generalization — every published "defeat" of the VM neutralizes or dumps it **per-app** rather than decoding it. [high.corrob.2026]

**Tier 3 — the most active 2026 line: bytecode restoration inside the Morphe Patcher ecosystem:**
- `sjshb57/pairip-patches` (v1.11.0, pushed 2026-10-11 — the most recently pushed **PairIP-dedicated** repo in the landscape; the MorpheApp *platform* repos themselves were pushed later, 2026-10-22, but are not PairIP-specific): four DEX-bytecode-level patches for Morphe Patcher (on-device, no root) — deobfuscate strings back to `const-string` form, replace `VMRunner`-invoking method bodies with minimal returns, delete `com/pairip/*` classes, restore method bodies extracted into `<class>$c<n>` reflection-helper classes, and inline `$<n>` synthetic call wrappers. I.e., it defeats the **method-extraction obfuscation** and neutralizes **VM entry points** — it neither defeats the license check nor decodes VM bytecode; its README carries no "broken on latest PairIP" caveat. [high.corrob.2026]
- Morphe itself (`morphe-manager` 9,192★, `morphe-patches` 4,182★, both pushed 2026-10-22) ships no PairIP-named patch officially (code search: no `pairip` files) — only adjacent universal patches ("Change installer source", "Spoof signature"); PairIP-specific patches live in third-party repos (sjshb57's; a "Disable PairIP license check" patch in mentalblank/Messenger-Revanced builds). [med.web.2026]
- Runtime dumpers filling the same niche: `ispointer/RePairip` (153★, v1.6.30 2026-09-07, pushed 2026-09-20; "dump all VMRunner snapshots and fully repack … removing protection layers completely"), `TechnoIndian/PairipJNI` (root-free runtime string/method dumper to `pairip.json`, method kept closed-source), `TechnoIndian/RKPairip` (77★; APKEditor string-restoration repack), TU Graz `mobilesecpairip` toolkit (dumper + patch + sign pipeline reusing the TechnoIndian components; also ships a reconstructed `libpairipcore.c` and the `.so`). All self-reported status. [med.web.2026]

**Synthesis:** the only actively maintained line of work (Tier 3) **sidesteps** the VM by neutralizing `VMRunner` and restoring extracted methods — precisely the approach that cannot revive GrindrPlus as a *hook client*, since the hookable Java surface is what was destroyed; its maintainer chose EOL over shipping per-version restoration patches. Commercial/gray offerings are advertised inside these repos (pwn.me alpha per Solaree's README; `mawo95/pairip`, 84★, paid full removal via Discord) — noted, unverified. [med.web.2026]

---

## 6. Analysis tooling (public state of the art)

**No complete public PairIP devirtualizer was found as of 2026-10-22** — unbounded absence claim, hedged the same way as §10.3.4: no counter-example surfaced in the searches conducted. The gap is filled by four other tool classes:

1. **Bytecode-level analysis (one repo, dormant):** MatrixEditor/pairipcore-vm — a Python disassembler/decompiler framework (**~3,597 LOC: 1,868 Python package + 1,005 tools + 724 Rust, as line-counted by the tooling lens; the counting command was not preserved in the lens record and was not re-run in this pass** — figure carried with that attribution): FDE loop at `pairipcore/__init__.py:35–65`, address/entry decoders at `context.py:50–77`, format model at `insn.py`; plus a Rust CLI (`pairip find-key` prints format-ID count and XOR-key offset/material; `pairip strings` prints decoded strings) plus a 770-line Ghidra headless automation (`tools/gvm_ghidra_x86_64.py` — line count verified by the lens) mining opcode handlers from dispatcher switches. Maturity: decompiler emits "// Stopped at unknown opcode" and exits; README: "Decompiler and Disassembler are WIP!"; 0 releases; 1 unanswered issue since 2025-05-06; 218★; last push 2025-01-26 (dormant ~21 months). It is the only public repo found that actually parses PairIP VM bytecode artifacts (superlative not independently provable — see §10.3.4). [high.local.2026]
2. **Write-ups, not tools:** Solaree/pairipcore is a README-only manual-analysis record (686 lines per one lens; `wc -l` = 685 — see §10.4), the groundwork pairipcore-vm cites. [high.local.2026]
3. **Runtime dumpers:** RePairip (snapshot dumper + repacker, above), PairipJNI (string/method dictionary), PADumper (463★, general-purpose process memory dumper — the tool Solaree recommends for the runtime-fixed `libpairipcore.so`; BlackDex issue #112 independently documents BlackDex failing on PairIP-protected apps — runtime dumping is the fallback because symbols are stripped and RegisterNatives binds only at load time). [high.corrob.2026]
4. **Dump-and-patch pipelines / hooking modules:** RK family, TU-Graz toolkit, Morphe patches; LSPosed/Zygisk skip-analysis modules (`pairipfix` family, `ymuuuu/pairipfix-zygisk` 13★, `wizzwuz/pairip-disabler` 6★, `Kitsuri-Studios/unpaircore` 15★ "fake lib … for research purposes"). [med.web.2026]

Methodological references for anyone extending this: Tim Blazytko's "Writing Disassemblers for VM-based Obfuscators" (symbolic execution of dispatcher/handler structure) is the canonical methodology and the explicit reference recommended by pairipcore-vm's own docs (`cfg.md:4`); SReverse gives a practitioner workflow (apktool/jadx/llvm-nm/strings on the target APK, tracing `com.pairip.application.Application` and `licensecheck` callers) and the caution that "A successful launch does not establish that later request code is available or unchanged." [med.web.2026]

*Repo-metadata provenance for every ★/push/release figure quoted in §5–§6: see §10.2.*

---

## 7. Detection surface

**Vendor-documented (only these are Google-confirmed):**

| Check | Trigger/failure behavior | Grade |
|---|---|---|
| Installer check | At app open; fail → Play Store prompt | [high.vendor.2026] |
| Anti-tamper | Fail → Play prompt "or the app will not run" (docs: "predominantly by crashing the app") | [high.vendor.2026] |
| Device check (partner-gated) | "Harder … to run your app in unknown and emulated environments" — the only vendor-confirmed emulator-related check | [high.vendor.2026] |

Vendor docs mention **no** root, debugger, or instrumentation detection, and explicitly disclaim completeness ("cannot guarantee prevention of all modification and redistribution"). [high.vendor.2026]

**RE-attributed native checks (well corroborated, two+ independent sources each):**
- **Anti-debugging** via raw AArch64 syscalls (`prctl`/`clone`/`wait4` — Solaree: "waitpid," §10.4 — /`ptrace`; ABI caveat in §3.3), incl. a cloned watchdog child — Solaree decompile + frida issue #124. Response attributed: process crash ("crashes, if it finds injected Frida"). [high.corrob.2026]
- **`/proc/self/maps` + `/proc/self/status` scanning** by the child — Solaree + #124 + SReverse lead list. [high.corrob.2026]
- **frida-server detection beyond the default port** ("not only default port, like Promon Shield does") — Solaree + #124 ("various ports"); exact mechanism (port vs messaging probe) is the author's explicit guess [low.spec.2026 for the mechanism; high.corrob.2026 for the check's existence].
- **System-property sweep** (dlopen libc → `__system_property_read_callback` → "VERY big iteration" over properties) characterized by Solaree as an emulator check; aligns with the vendor's "device check" (§3.5). Characterization is the author's. [med.web.2026]
- **Hook-framework indicators:** SReverse notes GOT/PLT rewrite checks ("the guard knows common hook frameworks") — hedged as a lead, not a proven check. [low.spec.2026]
- **VM-internal tamper check:** per-instruction hash verification with fail-address redirection (§2.6) — an integrity check on virtualized bytecode, not an environment probe. [high.corrob.2026]

**Thin, optional, or undocumented:**
- **Root detection:** only ever reported as optional or explicitly speculative — Solaree: "Optionally … prevent usage of the app for rooted users" (README.md:8) and "I guess pairipcore does root check too" (:658, unfinished analysis); SReverse: "A root or Magisk check **may** exist … A string match does not prove a check runs." Treat as per-app configuration, not a documented universal. [low.spec.2026]
- **Xposed/LSPosed detection:** no public source documents an explicit detector. The GrindrPlus post-mortem attributes failure to virtualization + integrity/licensing layers (with the §4 caveat on causal strength). [high.corrob.2026 — for the evidence base of the absence claim]
- **Failure responses are per-build, not uniform:** SReverse frames outcomes as build-dependent — app exit after launch, Play prompt, API 403, or divergence under a debugger — "Failure handling depends on the protected build"; licensing additionally has the silent `System.exit(0)` path (§3.4). [med.web.2026]
- **Detection timing (snippet-level):** farimarwat (Medium, fetch-blocked) reports "Spawning injects frida too early and gets detected" — consistent with checks running inside `JNI_OnLoad`/startup paths, but snippet-grade only. [med.snippet.2026]
- **Uncorroborated pillar claims:** the System Weakness "Deobfuscating PairIP" write-up claims RC4-with-permutation-table encryption, NEON-accelerated decryption, a second JIT-decryption VM, and a hidden encrypted DEX inside the `.iap` payload — none corroborated by the three repo/lab analyses; graded low and cited descriptively only. [low.unverified.2026]

---

## 8. Key takeaways

1. **Mechanism is settled science; semantics are not.** The pipeline (`VMRunner.invoke` → assets blob → RegisterNatives-bound `executeVM` → three-dispatcher interpreter over `VMContext`), the `\0IAP` format, FNV-family hash-chained dual-address control flow, and single-key XOR strings are corroborated by three public RE teams — Solaree↔ByteriaLab genuinely independent of each other, MatrixEditor building on Solaree (§6) — and partially verified on local artifacts. Opcode *semantics* remain 14-of-99 known publicly against per-binary handler totals on the order of ~100–160 (§2.7), and **per-build opcode randomization makes any fixed table obsolete on the next release** — the design's structural anti-generalization property.
2. **Defense in depth, deliberately layered:** earliest-startup Java signature check → native anti-debug//proc/frida/property checks wrapped around the VM → licensing with Play-redirect *and* silent-exit paths. No single layer is the protection.
3. **Google never names PairIP and documents none of the RE-attributed checks.** The vendor surface (installer/anti-tamper/device tiers) is a strict subset of what third parties found in the binary; the tier-to-code mapping (§3.5) is inferential. The custom-method-protection EAP is vendor-side confirmation that **method-level protection exists** (bodies "obfuscated," annotation stripped at protection time, per-call millisecond overhead) — the *virtualization/interpreter mechanism itself* is established only by third-party RE, not by the vendor page.
4. **Grindr's adoption is precisely dated in its consequences, not its onset:** hookable at 25.20.0 (Nov 2025) → announced 2026-03-21 → EOL commit authored 2026-04-04, pushed at archival 2026-05-18 → server-side cutoff ~2026-05-07 → archived 2026-05-18. First protected version: **insufficient data** (no APK census possible this cycle).
5. **GrindrPlus died of lost hookable Java surface (best-supported explanation), not detection:** virtualization removes the Java bodies Xposed hooks need — the maintainer's attribution, architecturally consistent — but the causal chain is not demonstrated per-method, no Xposed detector is documented, and Java hooking demonstrably still works on non-virtualized `com.pairip` classes (pairipfix). The update-block hook extended life until server-side enforcement; the kill was economic/architectural, and the maintainer explicitly refused "pairip fixes."
6. **The bypass economy mirrors the architecture:** license/integrity bypasses keep being re-published (cheap, partial); VM analysis stalled in 2025; the only active 2026 line (Morphe-ecosystem restoration + runtime dumpers) *sidesteps* the VM per-app. None of this revives a general hook client.
7. **The evidence hierarchy to keep in mind:** local artifacts > three-team corroboration > single reputable write-up > vendor docs (for *intent*) > snippets. Several circulating claims (System Weakness's RC4/NEON/hidden-DEX, the Medium bypasses, Google's self-reported ~80% figure) fail that bar for *content* weight and are hedged or quarantined accordingly.

### 8.1 Open questions this dossier does not answer

Collected here so no section silently implies an answer:

1. **Fallback-path behavior on tamper** — what executing the fail address actually does (terminate / decoy / alternate logic) is described by no source read (§2.6).
2. **FNV-1 vs FNV-1a in production** — unadjudicated repo-internal discrepancy (§2.6, §10.3.12).
3. **Header size tension** — 4-byte magic + u32@+0x04 vs ByteriaLab's "skip the first 8 bytes" (§2.5, §10.3.15).
4. **Method-selection criteria in the default (non-EAP) flow** — which methods Play chooses to virtualize absent the partner annotation, and what fraction of an app's methods typically get virtualized, is publicly undocumented; APKiD #495's per-app layer variation hints at configuration but does not characterize it. Needs the APK census (`docs/02`).
5. **PairIP prevalence** — no public estimate of how many Play apps ship PairIP was found; the ~4% figure (§2.9) is protection-in-general, not PairIP.
6. **General wild timeline** — the earliest public PairIP-era records in this corpus are JEB Apr 2023 and PlatinMods Jul 2023, implying deployment predates the 2024–25 RE wave this dossier leans on; PairIP's actual first appearance is not established.
7. **Offline behavior per tier** — vendor says "works offline"; licensing's primary path is network-bound and the observed silent-exit fired on disconnect; which tiers function without network, and what offline failure looks like, is unestablished (§3.4).
8. **ABI coverage of `libpairipcore.so`** — arm64-only vs multi-ABI is unrecorded by any source read (§3.3).
9. **Which Grindr versions ship PairIP, and how heavily** — the central unmeasured fact; needs `tools/pairip-audit` on fetched APKs (§4).
10. **Dispatcher roles** — which instruction classes `vm_dispatch_0/1/2` each handle, and why the interpreter splits across three functions; unrecorded by the sources read, and needed by anyone targeting tooling at one dispatcher (§2.3). Related: whether MatrixEditor's Ghidra pipeline consumed a runtime-dumped image or the shipped `.so` (§2.2).
11. **Sample identity per analysis** — which app each team's `libpairipcore.so`/vmcode sample came from; only TU Graz's `com.openai.chatgpt` example is attributed in the corpus, so per-build-variation claims cannot be anchored to sample identity (header, §6).
12. **SignatureCheck generality** — whether the expected-signature constant is per-app (injected per bundle) or Google-global; decides whether the Java check is per-app-configured or universal (§3.2).
13. **Detection telemetry** — whether detection events (frida found, tamper detected, emulator suspected) are reported to Google via network indicators or silent logging: no source read addresses it, and the vendor's "works offline" claim implies local responses but does not preclude telemetry. Also unexplored: whether the partner-gated device check integrates Play Integrity verdicts — the fraud-prevention page (source 6) is cited only for the service description (§3).
14. **Scope of opcode randomization** — per-app-release vs cross-app: whether two different apps protected in the same period share an opcode mapping decides whether per-build tooling generalizes across apps or only across releases of one app (§2.4).
15. **False-positive / reliability rate** of the integrity layers on legitimate users (rooted-but-legitimate devices, custom ROMs, work profiles, connectivity flaps) — unaddressed; bears on deployment decisions and on the credibility of Google's self-reported ~80% figure (§3.4).

---

## 9. Sources

Numbered in rough order of evidentiary weight. Retrieval/window: all fetched or cloned 2026-10-22 (UTC) unless a source date is given. Items 34–38 are the unreachable/snippet-level set, listed for completeness and **not** counted as read sources. The count below (1–33) matches the header arithmetic: 3 local clones (1–3) + 3 vendor pages (4–6) + 5 write-ups (7–11) + 14 repo/issue/release records (12–25) + 3 community records (26–28) + 2 app mirrors (29–30) + 3 academic references (31–33).

**Local clones (read directly this cycle):**
1. Solaree/pairipcore — https://github.com/Solaree/pairipcore (local: `samples/pairipcore`; README.md, 685 lines by `wc -l`)
2. MatrixEditor/pairipcore-vm — https://github.com/MatrixEditor/pairipcore-vm (local: `samples/pairipcore-vm`; README + `docs/source/{introduction,cfg,instructions,strings,automation}.md` + `pairipcore/{insn,context,opcode,__init__}.py` + `assets/data.vmcode`; docs mirrored at https://matrixeditor.github.io/pairipcore-vm/)
3. R0rt1z2/GrindrPlus — https://github.com/R0rt1z2/GrindrPlus (local: `samples/GrindrPlus`; README.md, news.json, version.json, manifest.json, app/build.gradle.kts, hooks/DisableUpdates.kt, git metadata)

**Google vendor documentation:**
4. Play Console Help — "About Google Play's automatic protection" (art. 10183279) — https://support.google.com/googleplay/android-developer/answer/10183279
5. Android Developers — "Automatic Protection: Customizable anti-tamper protection (EAP)" (updated 2026-02-26) — https://developer.android.com/google/play/integrity/automatic-protection
6. Android Developers — "Secure the environment" (fraud prevention) — https://developer.android.com/security/fraud-prevention/environment

**Independent reverse-engineering write-ups:**
7. ByteriaLab (A. Gültekin) — "Reversing Google's New VM-Based Integrity Protection (PairIP)", 2025-03-03 — https://blog.byterialab.com/reversing-googles-new-vm-based-integrity-protection-pairip
8. PNF Software (JEB) — "Recovering JNI Registered Natives", Apr 2023 — https://www.pnfsoftware.com/blog/recovering-jni-registered-natives
9. PNF Software (JEB) — "Reversing an Android App Protector — Part 3: Virtualization", 2020-07-08 — https://www.pnfsoftware.com/blog/reversing-android-protector-virtualization
10. ge0.dev — "Get this app from play: LicenseClient (com.pairip.licensecheck) reverse engineering" — https://www.ge0.dev/tech/get-this-app-from-play
11. SimpaLabs SReverse — "Understanding libpairipcore.so" (updated 2026-10-17) — https://sreverse.simpalabs.com/research/pairip-libpairipcore

**Repo / issue / release records (metadata provenance in §10.2):**
12. getpaseo/paseo issue #4417 — silent-exit licensing failure (firsthand logcat; automated-repro caveat noted in §3.4) — https://github.com/getpaseo/paseo/issues/4417
13. httptoolkit/frida-interception-and-unpinning issue #124 (HoffiF, 2024-12-04) — https://github.com/httptoolkit/frida-interception-and-unpinning/issues/124
14. sjshb57/pairip-patches (a.k.a. Pairip-Patches) — https://github.com/sjshb57/pairip-patches
15. MorpheApp/morphe-manager + morphe-patches — https://github.com/MorpheApp/morphe-manager
16. ahmedmani/pairipfix — https://github.com/ahmedmani/pairipfix
17. SafaSafari/bypass_libpairipcore — https://github.com/SafaSafari/bypass_libpairipcore
18. Anon4You/PKiller — https://github.com/Anon4You/PKiller
19. TechnoIndian/PairipJNI — https://github.com/TechnoIndian/PairipJNI
20. TechnoIndian/RKPairip (+ wrapper jyotidwi/RK_Pairip) — https://github.com/TechnoIndian/RKPairip
21. ispointer/RePairip — https://github.com/ispointer/RePairip
22. PADumper — https://github.com/CodingGay/PADumper (**citation-audit note:** widely cited under the owner name "BryanGIG/PADumper"; the URL resolves under CodingGay. A repo transfer/rename is the likely explanation but was **not verified** this cycle — both names are recorded here deliberately.)
23. Gamper, M. / mobilesecpairip — TU Graz **GitLab** (filed in this block for numbering continuity; it is not GitHub) — https://gitlab.tugraz.at/D6944BBA33F2F49C/mobilesecpairip
24. rednaga/APKiD issue #495 (Myshtea, Apr 2026) — https://github.com/rednaga/APKiD/issues/495
25. GrindrPlus Releases (v4.7.2-25.20.0, 2026-01-28; release page of source 3) — https://github.com/R0rt1z2/GrindrPlus/releases
    *Minor mentions (metadata only, not counted):* mawo95/pairip, ymuuuu/pairipfix-zygisk, wizzwuz/pairip-disabler, Kitsuri-Studios/unpaircore, haxymad/Pairip-Deobfuscating, mentalblank/Messenger-Revanced, revdex.re / t.me/RevDex tutorials, pwn.me (advertised), BlackDex issue #112 (via source 22's lens).

**Community records:**
26. Telegram — GrindrPlusCI channel (in-app news mirrored verbatim) — https://t.me/s/GrindrPlusCI
27. XDA Forums — "[CLOSED][MOD][LS/POSED/PATCH] Grindr Plus" thread, page 160 — https://xdaforums.com/t/closed-mod-ls-posed-patch-grindr-plus.4461857/page-160
28. PlatinMods — "PairipCore Kill Tutorial" (Jul 2023, replies through Jan 2026) — https://platinmods.com/threads/pairipcore-kill-tutorial.191553

**App mirrors (release chronology):**
29. APKMirror — Grindr listing (through 26.21.0, 2026-10-16) — https://www.apkmirror.com/apk/grindr-llc/grindr-gay-chat-meet-date/
30. APKPure — Grindr version history (25.x/26.0.x dates; source of the 2026-03-06/03-12 bracket endpoint; used because APKMirror per-release pages 403'd) — https://apkpure.com/grindr-gay-chat-app/com.grindrapp.android/versions

**Academic:**
31. Zhao et al., "Compile-time Code Virtualization for Android Applications," *Computers & Security* 94:101821 (2020) — https://www.sciencedirect.com/science/article/abs/pii/S0167404820300936 (abstract verified via eprints.whiterose.ac.uk)
32. Blázquez & Tapiador, "Practical Android Software Protection in the Wild," *ACM Computing Surveys* 58(2) Art. 36 (2025) — https://dl.acm.org/doi/10.1145/3757735 (quotes via the authors' Quarkslab summary)
33. T. Blazytko, "Writing Disassemblers for VM-based Obfuscators," Synthesis, 2021-10-21 — https://www.synthesis.to/2021/10/21/vm_based_obfuscation.html

**Reachable only at snippet/summary level — NOT counted as read:**
34. petruknisme — "Bypassing PairIP Integrity Checks" (Medium, 2025-12-02; 403/500 to both fetchers; X announcement date snowflake-decoded) — https://petruknisme.medium.com/bypassing-pairip-integrity-checks-21d7bdd4a052
35. farimarwat — "Bypassing Pairip VM Protection on Android" (Medium; fetch-blocked; one timing quote at snippet level) — https://medium.com/@farimarwat/bypassing-pairip-vm-protection-on-android-a684c1559b39
36. System Weakness — "Deobfuscating PairIP" (403 to WebFetch; claims via z.ai webReader summary; graded low) — https://systemweakness.com/deobfuscating-pairip-reverse-engineering-vm-protector-af8e18ea49ab
37. Stack Overflow 79347596 & 79759688 (403; snippets only); Google Issue Tracker 497588848 (sign-in wall; snippet only)
38. Vargas 2025, "Assessing the Security Coverage of the Google Play Integrity API" (SBC OpenLib; PDF downloaded but text extraction failed on embedded-font encodings — whether it mentions PairIP is unknown)

---

## 10. Methodology

### 10.1 Lenses covered (7/7) and the 21 confirmation checks, enumerated

| Lens | Focus | Findings | Checks (all held) |
|---|---|---|---|
| vm-internals | VM architecture, bytecode format, opcodes | 12 | 3 |
| integrity-layer | Vendor tiers, SignatureCheck, licensing, native protections | 9 | 3 |
| bypass-landscape | Published bypass classes and working status | 11 | 3 |
| grindr-deployment | Grindr version chronology, GrindrPlus EOL forensics | 11 | 3 |
| formal-analyses | Academic literature, long-form technical analyses | 11 | 3 |
| tooling-landscape | Public analysis/dump/patch tooling state | 7 | 3 |
| detection-surface | Attributed checks and failure behaviors | 10 | 3 |

**The 21 checks, as claim → what it was checked against** (each held; corrections and unverified sub-elements are logged in §10.3–§10.4 rather than silently dropped):

1. VMRunner marker chain (`invoke`→`readByteCode`→`executeVM`) → local `samples/pairipcore/README.md:91–145` decompile + `introduction.md:21–31`; the ByteriaLab sub-quote itself was not locatable (→ §10.3.1).
2. RegisterNatives binding + JNI signature + 0x5F180 mapping → `introduction.md:44–65`, Solaree README:196, live JEB blog (quote matched verbatim).
3. Three dispatchers + `VMContext` struct + ~16,000-line figure → verbatim `automation.md`/`cfg.md` passages in the local clone.
4. Play Help tiers / "predominantly by crashing" / never-named-PairIP → live fetch, verbatim quotes.
5. EAP page: annotation stripping, ~80% claim, footer date 2026-02-26 → live fetch, verbatim quotes.
6. SignatureCheck mechanics (attachBaseContext ordering, Base64-SHA-256, exception text) → local README:38–86 quotes.
7. GrindrPlus EOL (README wording, `aa497a0`, archived, 546★ — star figure is a same-session `gh api` snapshot within the §10.2 provenance scope as extended below) → raw README fetch + `gh api` commit + repo record.
8. "No universal devirtualizer" → local `pairipcore-vm/README.md:7–10` + live GitHub cross-check.
9. sjshb57 patch set (exactly 4 patches, v1.11.0, 2026-10-11) → `gh api` release/repo + README contents.
10. GrindrPlus README EOL statement + README commit history (warning added only in `aa497a0`) → local clone + GitHub commits API (local clone is depth-1).
11. Archival date + EOL commit AuthorDate/CommitDate split → repo HTML banner + `git log -1 --format=fuller` on the local clone.
12. news.json msg 197 (epoch 1774135930 = 2026-03-21T23:32:10Z) → local JSON parse + Telegram verbatim match.
13. MatrixEditor VM architecture summary → GitHub Pages mirror quotes (instructions/strings/automation/cfg pages).
14. Solaree write-up contents (SignatureCheck constants, hook, protections_main, syscalls) → line-level quote check on the local README ("first public" sub-claim logged → §10.3.2).
15. ByteriaLab corroboration (RegisterNatives, FNV-1 dual addresses, .IAP skip, per-build opcodes) → live fetch, verbatim quotes.
16. MatrixEditor repo stats (218★, 0 releases, 1 issue, 770-line script, FDE-loop/context line refs, WIP markers) → `gh api` + local file checks.
17. Solaree writeup-only status (`git ls-files` = README.md) → local git + `gh api` (line/case-count corrections logged → §10.4).
18. RePairip metadata + description quote → `gh api` + fetched page.
19. Vendor detection-surface wording (tiers, prompts, no root/debugger mention, disclaimer) → live fetch, verbatim.
20. GrindrPlus PairIP attribution (README + news.json msgs 197/198 + archived/EOL) → local files + `gh api`.
21. Solaree native-check attribution (anti-debug, /proc, frida-server, property sweep) → line-level verbatim check on local README (98-case correction logged → §10.4).

### 10.2 Checks actually run this cycle (vs. sourced) — and metadata provenance

**Run locally:** `xxd` on `samples/pairipcore-vm/assets/data.vmcode` (`\0IAP` magic at offset 0); grep counts on `pairipcore/insn.py` (99 `O()` registrations, 85 `O("_")` placeholders, 14 semantic); `.git/config` + `git log -1 --format=fuller` + reflog on all three clones (upstream remotes and HEAD commit dates verified; GrindrPlus clone is depth-1, so README history was checked against GitHub's API instead); grep case-label count in Solaree's dispatcher block (98); epoch decoding of news.json dates 197/198; `gh api` metadata pulls; tweet snowflake decoding for the petruknisme announcement date.

**NOT run (stated per ROE and harness rules):** the Python pairipcore tools and Rust binaries were **not executed** — all behavioral claims about decoders come from reading code and docs. The **~3,597 LOC figure** for pairipcore-vm was line-counted by the tooling lens (1,868 + 1,005 + 724); the counting command was not preserved in the lens record and was **not re-run in this pass** — the figure is carried with that attribution, not as a fresh measurement. No bypass was executed, no APK patched, no live Grindr infrastructure touched. No APK census: `samples/apk` and `samples/out` are **empty**, so no Grindr-version measurement of any kind was possible in this cycle.

**Repo-metadata provenance (stars / push dates / releases / archived status wherever they appear — §5–§6 and the §10.1 check list):** all such figures are **point-in-time snapshots recorded by the lens passes on 2026-10-22**, from two retrieval channels: (a) authenticated `gh api` — the tooling-landscape lens reports using it for *all* metadata it cites (MatrixEditor, Solaree, RePairip, Pairip-Patches, PairipJNI, RKPairip, pairipfix, PADumper), and the bypass-landscape lens reports 8 `gh api` repo records; (b) fetched repo pages/READMEs in the same sessions for the remainder (e.g., the MorpheApp figures, `mawo95/pairip` 84★, and the 13★/6★/15★ minor modules). **The exact per-figure channel mapping was not preserved in the records handed to this synthesis, and no metadata was re-pulled during this writing pass** — treat every ★/push figure as a session snapshot of that date, not an independently re-verified number.

### 10.3 Claims and cited evidence that FAILED or could not complete confirmation — kept and labelled

No top-level lens claim failed its confirmation pass, but the following sub-claims, superlatives, and citations **could not be confirmed** and are carried as unverified throughout this dossier:

1. **ByteriaLab invoke()-parameters quote** (vm-internals): "the parameters we see in the invoke() call … correspond to the names of the bytecode files in the assets/ folder" — not found in the named source or workspace by grep. **Unverified quote**; the underlying mechanism is independently verified via Solaree's decompile.
2. **"Solaree = the first public long-form RE write-up"** (formal-analyses): priority label is not asserted by the source; only consistency-supported by its April 2024 date. **Unconfirmed superlative.**
3. **"RePairip = the most active dedicated PairIP unpacker"** (tooling-landscape): unverifiable from the single source. **Unconfirmed superlative.**
4. **"MatrixEditor = the only public repo that parses PairIP VM bytecode"** (tooling-landscape): not establishable from that source alone. **Unconfirmed superlative** (no counter-example was found either).
5. **petruknisme Medium article content** (bypass-landscape, integrity-layer): HTTP 403/500 to WebFetch, stackprinter, and webReader; freedium mirror returned unrelated content. **Existence and date verified; technique and working status unverified.**
6. **farimarwat Medium article** (detection-surface, formal-analyses): fetch-blocked; one timing quote at search-snippet level only. **Snippet-grade.**
7. **System Weakness "Deobfuscating PairIP" pillar claims** (formal-analyses): RC4 permutation-table encryption, NEON-accelerated decryption, second JIT-decryption VM, hidden encrypted DEX in `.iap` — obtained via a webReader summary of a 403 page; uncorroborated by the three repo/lab analyses. **Low, quarantined.**
8. **Stack Overflow 79347596 / 79759688** (integrity-layer): 403; used only as corroborating *hints* (LicenseClient crash line numbers). **Not read.**
9. **Google Issue Tracker 497588848** (integrity-layer): sign-in wall; snippet only. **Not read.**
10. **Vargas 2025 (SBC OpenLib) PDF**: downloaded but text extraction failed (embedded-font encodings; ~8.5KB of garbled glyphs; no pdftotext available). **Whether it mentions PairIP is unknown.**
11. **Exact first Grindr version shipping PairIP**: no public source names it; `samples/apk` empty. **Insufficient data**; onset bracketed 25.20.0 (2025-11-22) → 26.3.1/26.4.0 (current at announcement per APKPure — itself mirror-derived, not APK-verified); 25.21.x/26.0.x window ambiguous.
12. **FNV-1 vs FNV-1a** (vm-internals): `context.py` implements FNV-1; `src/fnv.rs` implements FNV-1a, in the same repo. **Which matches production `libpairipcore.so` was not adjudicated** — the exec summary and takeaways therefore say "FNV-family / documented FNV-1," never asserting the variant as settled.
13. **haxymad/Pairip-Deobfuscating README**: decodes to binary garbage; characterized by metadata only. **Uncharacterized.**
14. **PairIP presence in current Grindr 26.x builds**: inferred from project records; **not APK-verified** (and §4's "further 26.x releases" phrasing deliberately avoids asserting it per release).
15. **Bytecode header size (new in rev. 2):** the 4-byte `\0IAP` magic (xxd-verified) + encoded u32 at `+0x04` (MatrixEditor) vs ByteriaLab's "skipping the first 8 bytes" — compatible only if "8 bytes" means the whole header. **Unadjudicated; both sources quoted as-is (§2.5).**

### 10.4 Corrections made during confirmation (discrepancies, not failures)

- Solaree README is **685** lines by `wc -l` (one lens said 686).
- The `protections_main` switch has **98 case labels** by grep (lens estimates of "~80" and "~70" corrected).
- GrindrPlus `version.json` **25.21.1 is the update-spoof tracker**, not the build pin (build pin at HEAD: 26.0.1/149389). The program root README's "pinned Grindr 25.21.1" phrase conflates the two (flagged for `docs/03`).
- Mirror date conflict: APKMirror dates 26.8.2 as 2026-05-15, APKPure as 2026-05-18; APKPure was used for 25.x/26.0.x chronology because APKMirror per-release pages 403'd and its pagination would not advance.
- JEB's 2020 "p-code VM un-virtualization" posts concern an anonymous third-party protector, **not** PairIP; deliberately excluded despite search-snippet conflation. The only PairIP-specific JEB claim used is the April 2023 RegisterNatives/string-constants post.
- TU Graz GitLab commit dates are only relative ("~4 months ago", page metadata 2026-06-05) — hence medium confidence on that finding.
- AArch64 syscall naming (rev. 3): Solaree's "waitpid 260" corrected to **wait4 260** — waitpid exists only as a libc wrapper over the wait4 syscall; the other five IDs (93/117/129/167/220) are correct as printed (§3.3).
- Recency qualifier (rev. 2): sjshb57/pairip-patches is "most recently pushed **PairIP-dedicated** repo" — the MorpheApp platform repos (pushed 2026-10-22) are more recent but not PairIP-specific.

### 10.5 Source-access failures encountered (environmental, reported not padded)

Medium (403 to WebFetch and rate-limit/500 to webReader), Stack Overflow (403; stackprinter "server too busy"), Google Issue Tracker (sign-in wall), APKMirror per-release pages (403 bot protection; pagination stuck), systemweakness.com (403), gitlab.tugraz.at (ECONNRESET to WebFetch; retrieved via alternate reader), unauthenticated GitHub REST (403 rate-limited; retried authenticated via `gh api`).

### 10.6 Deliberate exclusions under ROE

The two Medium bypass tutorials (petruknisme, farimarwat) are noted by existence only — ROE forbids reproducing bypass content. Solaree's embedded payloads (RegisterNatives hook, SIGKILL-to-child, PADumper recipe) are referenced descriptively, never reproduced. No bypass artifacts were produced, hosted, or tested in this program.

---

*Rev. 2 changelog (2026-10-22, reviewer-gap pass): reconciled header/§9 source arithmetic; enumerated the 21 confirmation checks; stated repo-metadata provenance; FNV wording neutralized to "FNV-family/documented FNV-1" at summary level; added the 2026-03-06/03-12 bracket-endpoint table row and citation; softened EAP claim to "method-level protection," kill-mechanism claim to "best-supported explanation," and "~80%" to a hedged self-reported figure; added "PairIP-dedicated" recency qualifier; reconciled opcode denominators; corrected "four years" to "three to four years"; flagged the 4-vs-8-byte header tension; explained the AuthorDate/CommitDate split and the paseo bot repro; added ABI note, offline-licensing tension, vendor-tier↔RE-layer mapping (§3.5), prior-protector comparison (§2.10), and the consolidated open-questions list (§8.1); added PADumper owner/URL note, u16-formula and LOC attributions, sentence-level tags on mixed-strength paragraphs, and phrasing fixes ("publicly known", fallback-path wording, tag-vs-confidence note).*

*Rev. 3 changelog (2026-10-22, second reviewer pass): corroboration base stated precisely — MatrixEditor flagged as building on Solaree, so only Solaree↔ByteriaLab (plus JEB for RegisterNatives) are independent, with the sample-identity caveat (only TU Graz's com.openai.chatgpt is attributed); "static analysis requires a process dump" downgraded to Solaree's recommendation, with the Ghidra-pipeline-input question flagged; SignatureCheck constants fully quoted and the per-app-vs-global question opened; 26.1.x/26.2.x non-enumeration stated and the ambiguous window widened to 25.21.0→26.2.x; detection-telemetry/Play-Integrity-linkage and false-positive-reliability angles added as open questions; opcode-randomization scope (cross-app vs per-app-release) opened; both flat absence claims re-hedged per §10.3.4; exec-summary causal bundling split (randomization→non-transfer, hash-chain→tamper-redirection) and ~86% re-qualified as per-binary; "waitpid 260" corrected to wait4; Zhao "exactly" softened to family resemblance with no causal claim; "not defeated the VM" reframed with the defeat=decoding definition and the per-app bar acknowledged; paseo bot-repro parenthetical re-based to the issue's bot-repro record with its premise stated; Blázquez quotes flagged second-hand at point of use; dispatcher-role question added to §8.1; §4 headline downgraded to attributed causation; §10.2 provenance scope extended to the §10.1 check list (546★ annotated).*
