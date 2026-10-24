# Virtualized Methods — Identity and Characterization of the 20 VM Stubs in the Current Grindr Base Split (26.21.0)

**Date:** 2026-10-24
**Deliverable:** `docs/09` of the PairIP/GrindrPlus research program (charter in repo README; ROE in `ROE.md`). Extends the `docs/00`–`docs/08` series. Closes the identity gap that `docs/02` left open — *"The **identities of the 20 stub methods** are not recoverable from the census output"* (`docs/02-feasibility-study.md:96`) — using the named census produced after `docs/05` was written.
**Question answered:** What did the vendor actually choose to virtualize in this build, class-by-class and method-by-method? How many of the virtualized methods are integrity/licensing glue vs feature logic? What does the answer imply for the integrity-first verdict of `docs/02`/`docs/05`? And does the APK ship `assets/*.vmcode` VM bytecode (`vmcodeAssets` present or absent)?
**Method:** three passes, all executed this session. **(a)** Read the analyzer census `samples/out/census-base-named.json` in full (4,225 lines; analyzer run exit code 0 per the task record; file read this session) and list every `stubMethodsList` entry. **(b)** Independent inspection of **each** named method with androguard 4.1.4 from this session's shell against `pairip-research/samples/apk/grindr-current-base.apk`: the method's declaring class (superclass, interfaces, fields, sibling methods), string constants, the full stub disassembly, and — for the three R8-obfuscated entries — the surrounding class cluster. **(c)** Independent stdlib `zipfile` pass over the APK for `vmcode` assets, plus an `APK.get_receivers()` manifest read to establish how each stub receiver is registered. Every claim below is either **[measured]** — produced this session by a command or file read recorded in §7 — or **[sourced]** — cited to `docs/01`/`docs/02`/`docs/05`/the census file, which carry their own provenance — or explicitly labeled **[interpretation]**. Measurement and interpretation are kept separate throughout (§2–§4 measurement; §5 interpretation).

**Path convention:** commands and paths are relative to the workspace root (the parent of `pairip-research/`), matching `docs/02`/`docs/05`. `samples/` is gitignored (local-only by policy).

---

## 1. Inputs and headline numbers **[measured]**

| Input | Value |
|---|---|
| Census file | `pairip-research/samples/out/census-base-named.json` (read in full, 4,225 lines) |
| Target APK | `pairip-research/samples/apk/grindr-current-base.apk` (`census-base-named.json:2`) |
| versionName / versionCode | 26.21.0 / 189896 (`census-base-named.json:3-4`) |
| `pairipDetected` | `true` (`census-base-named.json:5`) |
| Total method entries / stub methods | 422,621 / 20 (`census-base-named.json:58-59`; `stubPct` field rounds to `0.0` at `:60`; `docs/05:175` computes the unrounded 0.00473 %) |
| `stubMethodsList` | 20 entries, `stubMethodsListTruncated: false` (`census-base-named.json:130-232`; recount via `json.load` this session: len 20) |
| **`vmcodeAssets`** | **`[]` — ABSENT** (`census-base-named.json:8`); independently confirmed absent this session (§6) |

The census's stub heuristic (quoted from its own notes, `census-base-named.json:1218-1221`): a method **outside** `com.pairip.*` counts as a PairIP VM stub when its Dalvik bytecode contains an invoke targeting `Lcom/pairip/VMRunner;->invoke` or `->executeVM`; methods declared inside `com.pairip.*` are never counted because the VM runtime itself lives there.

---

## 2. The shared stub shape — what every one of the 20 looks like **[measured]**

All 20 entries were disassembled this session (commands §7b). Every one of them is the *same 11–12-instruction body*, differing only in argument-array size and token string. Canonical example — `com.braze.push.BrazePushReceiver.onReceive` (`classes5.dex`):

```dalvik
const          | v0, 3
new-array      | v2, v0, [Ljava/lang/Object;
const          | v0, 0
aput-object    | v5, v2, v0        # [0] = this
const          | v0, 1
aput-object    | v6, v2, v0        # [1] = Context arg
const          | v0, 2
aput-object    | v7, v2, v0        # [2] = Intent arg
const-string/jumbo | v1, KgYFNRlK79JZ8psX
invoke-static  | v1, v2, Lcom/pairip/VMRunner;->invoke(Ljava/lang/String; [Ljava/lang/Object;)Ljava/lang/Object;
move-result-object | v1
return-void    |
```

**What the VM stub passes** — measured across all 20:

- **One opaque token string** (first argument), e.g. `KgYFNRlK79JZ8psX`. All 20 tokens are distinct, all 16 chars, alphanumeric mixed case. Per census `integrityEntryPoints` (`census-base-named.json:311-321`) the bytecode is fetched at call time by `VMRunner.getVmByteCode` → `readByteCode` → `openBaseApk`/`readFullByteArrayFromStream` and decrypted via `VmDecryptor.<init>`/`decrypt` — there is no static per-token file (§6).
- **One `Object[]` holding exactly `this` plus the method's declared parameters**: 3 elements for the 18 instance `onReceive(Context, Intent)` stubs; 2 elements for `nua0.doInBackground([Object)Object` (`this` + the varargs array); 1 element (`this` alone) for `com.google.android.gms…OfflinePingSender.doWork()Lken;`, which takes no parameters. The stub preserves the original method signature exactly — same name, same descriptor, same return handling (`return-void`, or `check-cast` + `return-object` for the two value-returning stubs).
- **Invoke target:** all 20 call `VMRunner.invoke(String, Object[])`; none calls `executeVM`.

**Rewriter artifacts in the declaring classes [measured].** 15 of the 20 declaring classes carry one or more synthetic accessor methods with the non-standard suffix `$00N` — `getClass$001`, `getClass$002` (a one-instruction `Object.getClass()` wrapper, disassembled this session), `getAction$001`, `equals$002`, `goAsync$003`, `submit$003`, `finish$001`, `zzd$001`, `onNetworkChange$002`, `updateOrientationManual$003`, `notifyVolumeChange$003`, `getRingerMode$003`, `b$004`, `a$002`, `c$001`, `get$001`. (The 5 without any accessor are the two Agora `BTHeadsetBroadcastReceiver` variants, `zzp`, `nua0`, and `obd0` — the latter three being minimal classes whose stub needs no private-member bridge.) What is measured here is the accessors' existence/shape above (disassembled this session). The `$00N` suffix is not a Java/R8 naming convention — that statement is background naming knowledge, not something any §7 command establishes, and is not claimed as measured. Who adds the suffix and why is **[interpretation]**: it is plausibly produced by the same build-time transform that created the stubs (presumed to be the PairIP transformer), presumably so code executing outside the JVM — e.g. the VM-executed body — can reach the class's private members; the stub bodies were not decoded (§6), so neither the transformer attribution nor the caller of these accessors was observed. These accessors persist even where **only one** method of the class was virtualized — e.g. `BrazePushReceiver` (5 methods total, one stub) still carries `getClass$001/002`.

**One stub per class, rest of the class left intact [measured].** In each of the 20 classes exactly one method contains a `VMRunner` invoke — the method named by the census; no class has a second. Every other non-abstract method of those classes remains ordinary Dalvik (e.g. AppLovin `j` keeps a 31-instruction plain-Java `onReceive(Intent, Map)` overload beside the stubbed `onReceive(Context, Intent)`; ironSource `obd0` keeps its plain-Java constructor and connectivity logic).

---

## 3. The complete `stubMethodsList` — all 20 entries, with per-method characterization

Table fields: the census entry (class, method, dex — verbatim from `census-base-named.json:130-231`), the VM token measured in the stub this session, and the characterization (evidence in §3.1–§3.4). "Direct" = vendor identity established by the class's own literal package name or a direct in-class reference; "Inferred" = identity/role established from indirect evidence (surrounding cluster, external naming convention, or structural similarity to another row), flagged per row.

| # | Class (census `:130-231`) | Method | DEX | VM token **[measured]** | Vendor (evidence grade) | What the virtualized method is | Category |
|---|---|---|---|---|---|---|---|
| 1 | `io.agora.base.internal.voiceengine.WebRtcAudioManager$VolumeChangeReceiver` | `onReceive` | classes10 | `PhIfFXjaqxk96ofB` | Agora (direct) | System-volume-change receiver feeding a WebRTC audio manager | Feature — call audio |
| 2 | `io.agora.rtc2.internal.AudioDeviceInventoryLowerThanM$BTHeadsetBroadcastReceiver` | `onReceive` | classes10 | `R9buNjsb6WhBzLkb` | Agora (direct) | BT-headset plug/unplug → audio-device routing (pre-Android-M inventory) | Feature — call audio |
| 3 | `io.agora.rtc2.internal.AudioDeviceInventoryMocker$BTHeadsetBroadcastReceiver` | `onReceive` | classes10 | `s51yWnQigL5UAaoQ` | Agora (direct) | Same, "Mocker" inventory variant | Feature — call audio |
| 4 | `io.agora.utils2.internal.CommonUtility$14` | `onReceive` | classes10 | `QmLTxpiv03knUKqU` | Agora (direct) | Anonymous receiver; accessors `updateOrientationManual$003`/`getAction$001` → in-call orientation/proximity handling | Feature — call audio |
| 5 | `io.agora.utils2.internal.ConnectionChangeBroadcastReceiver` | `onReceive` | classes10 | `gDZWaagHvLwOLWP8` | Agora (direct) | Network-change receiver; accessor `onNetworkChange$002` | Feature — call audio |
| 6 | `net.pubnative.lite.sdk.receiver.VolumeChangedActionReceiver` | `onReceive` | classes11 | `kpRzDC4RmylXGWi0` | PubNative/Verve (direct) | Volume-changed singleton receiver; strings `android.media.VOLUME_CHANGED_ACTION`, `notifyVolumeChange` | Feature — ads |
| 7 | `com.applovin.impl.sdk.j` | `onReceive` | classes2 | `qdPD2AAtL4j2hdln` | AppLovin (direct) | Ringer/volume + app-pause/resume observer; strings `android.media.RINGER_MODE_CHANGED`, `com.applovin.application_paused/resumed`, `Observing ringer mode...` | Feature — ads |
| 8 | `com.fyber.inneractive.sdk.flow.storepromo.ui.b` | `onReceive` | classes5 | `u87aL1cDWST6AwHo` | Fyber Inneractive (direct) | Store-promo UI receiver (WeakReference to promo controller `c`) | Feature — ads |
| 9 | `com.fyber.inneractive.sdk.util.y` | `onReceive` | classes5 | `aWnOk37EZYn8twkS` | Fyber Inneractive (direct) | Util-layer receiver (callback field `b0`) | Feature — ads |
| 10 | `com.google.android.gms.ads.internal.util.zzcf` | `onReceive` | classes6 | `olXmke9EyYKWR8ba` | Google Mobile Ads (direct) | Ads-internal util receiver (callback `zzcg`; accessor `zzd$001`) | Feature — ads |
| 11 | `com.google.android.gms.ads.internal.util.zzp` | `onReceive` | classes6 | `6rTehwDbQM1jfJgM` | Google Mobile Ads (direct) | Ads-internal util receiver (ctor takes `zzs`, `byte[]`) | Feature — ads |
| 12 | `nua0` | `doInBackground` | classes6 | `DAt3coOv6J3viODD` | GMS-ads cluster (**inferred**, §3.2) | Obfuscated `AsyncTask` background body in the Play-Services ads/mediation blob | Feature — ads |
| 13 | `com.google.android.gms.ads.internal.offline.buffering.OfflinePingSender` | `doWork` | classes9 | `aUJyWEc0WjIDV2sb` | Google Mobile Ads (direct) | WorkManager `Worker` ping for offline ad buffering | Feature — ads |
| 14 | `com.inmobi.media.ik` | `onReceive` | classes9 | `ptKsg85PuPboQur5` | InMobi (direct) | Ads receiver; accessors `submit$003` (executor) + `getClass$001/002` | Feature — ads |
| 15 | `com.mbridge.msdk.out.LoadingActivity$1` | `onReceive` | classes9 | `3ct4LWxNaqrwClJf` | Mintegral/MBridge (direct) | Inner receiver of ad LoadingActivity; accessor `finish$001` | Feature — ads |
| 16 | `obd0` | `onReceive` | classes9 | `QUvrFewfIRe6RZnm` | ironSource AdQuality (direct ref, §3.2) | StringFog-obfuscated connectivity receiver; `c()` checks `ConnectivityManager` state | Feature — ads |
| 17 | `bo.app.i4` | `onReceive` | classes2 | `VDwVJJTI1AZUTJUm` | Braze (**inferred**, §3.1) | Braze-internal receiver by inference — no literal vendor name or in-class Braze reference; attribution from the external `bo.app`-is-Braze's-obfuscation-root convention plus the `getClass$001/002` accessor pair matching #18; accessor `goAsync$003` | Feature — push/engagement |
| 18 | `com.braze.push.BrazePushReceiver` | `onReceive` | classes5 | `KgYFNRlK79JZ8psX` | Braze (direct) | Braze push entry-point receiver (manifest-registered, §3.4) | Feature — push/engagement |
| 19 | `com.facebook.AuthenticationTokenManager$CurrentAuthenticationTokenChangedBroadcastReceiver` | `onReceive` | classes5 | `qYpac9jPewHi3L2X` | Facebook SDK (direct) | Auth-token-change invalidation receiver (manifest-registered, §3.4) | Feature — identity |
| 20 | `seq` | `onReceive` | classes7 | `E434BqDVkzKSgnEi` | Obfuscated (**inferred**, §3.2) | Kotlin `callbackFlow`-created broadcast receiver in a location-monitoring module | Feature — location |

**Not one of the 20 is licensing/integrity glue.** Zero stubs sit in `com.pairip.*` (excluded by the heuristic by construction, `census-base-named.json:1220` — and the pairip classes' own call graph is fully enumerated as plain `pairip-call` entries in `integrityEntryPoints`, `census-base-named.json:233-1215`, none of them stubs). Zero stubs sit in Grindr first-party code (`com.grindrapp.*` — absent from the list). Zero stubs touch signature verification, licensing, or the VM entry chain.

### 3.1 Direct-evidence groups (17 of 20; #17's inference noted in place)

Measured facts per group, from this session's class dumps (§7b):

- **Agora real-time communications — 5 stubs (#1–#5).** All five declare `io.agora.*` package names (Agora RTC/WebRTC SDK, the video-call stack Grindr ships). Receiver roles are legible from surviving members: `WebRtcAudioManager$VolumeChangeReceiver` keeps `mWebRtcAudioManager:WeakReference` + accessor `get$001`; both `AudioDeviceInventory*` receivers keep an `isRegistered` flag and `this$0` pointing at their inventory class (Bluetooth-headset audio routing for pre-M and mocked Android audio stacks); `CommonUtility$14` keeps accessors `getAction$001`/`updateOrientationManual$003` (in-call orientation/proximity); `ConnectionChangeBroadcastReceiver` keeps `TAG` + `mCommonUtility:WeakReference` + `onNetworkChange$002`. Every one is an event callback in call handling. None carries any security, licensing, or integrity vocabulary.
- **Ad networks — 9 direct stubs (#6–#11, #13–#15) + 1 direct-reference (#16).** Self-identifying strings measured in the declaring classes: PubNative's `android.media.VOLUME_CHANGED_ACTION` / `VolumeChangedActionReceiver`; AppLovin's `android.media.RINGER_MODE_CHANGED`, `com.applovin.application_paused`, `com.applovin.application_resumed`, `Observing ringer mode...`, `Unable to collect device volume` (mute/volume telemetry for ads — note the class's *other* overload `onReceive(Intent, Map)` is intact Java); GMS-ads `zzcf`/`zzp`/`OfflinePingSender` under `com.google.android.gms.ads.internal.*`; InMobi `ik`; Mintegral `LoadingActivity$1` with `finish$001`.
- **Push/engagement & identity — 2 direct stubs (#18–#19) + 1 inferred (#17).** #18 `com.braze.push.BrazePushReceiver` and #19 (the Facebook SDK's auth-token invalidation receiver) are direct — literal package names. #17 `bo.app.i4` carries no literal vendor name and no in-class Braze reference; its Braze attribution is an **inference** resting on the externally documented convention that `bo.app` is Braze's obfuscation root (an assertion from outside this APK, with no in-class evidence cited) plus circumstantial similarity — the same `getClass$001/002` accessor pair as #18 — so it is graded Inferred, not Direct; its `goAsync$003` accessor marks async broadcast processing.

### 3.2 The three obfuscated entries — evidence and confidence

- **`obd0` (classes9) — ironSource AdQuality, direct reference [measured].** The *intact* methods of the class call `Lcom/ironsource/adqualitysdk/sdk/StringFog;->decrypt(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;` repeatedly; `<init>` registers the receiver with a StringFog-decrypted action and logs through `Lnwc0;->b/h`; `c(obd0, Context)` fetches the (decrypted-named) connectivity service, calls `ConnectivityManager.getActiveNetworkInfo()/isConnected()`. The encrypted-string blobs seen in the class are StringFog ciphertext. Identity: established by the direct in-class call to the ironSource AdQuality decryptor.
- **`nua0` (classes6) — GMS-ads cluster, inferred [measured cluster evidence; identity not proven].** `nua0 extends mua0 extends android.os.AsyncTask` (both measured). The cluster's enclosing type `uu00` (constructor parameter of `mua0`) implements `Lcom/google/android/gms/common/api/internal/RemoteCall;` and `Lcom/google/android/gms/tasks/OnCompleteListener;` and has a constructor taking `Lcom/google/android/gms/internal/ads/zzcbk;`. A sibling task in the same cluster, `oua0` (also extends `mua0`), carries the string `setNativeViewHierarchy` — Google Mobile Ads native-ad view-hierarchy vocabulary. `nua0` itself contains no self-identifying string (only its token), so the attribution to the GMS ads/mediation blob is an inference from its cluster, not a direct identification.
- **`seq` (classes7) — Kotlin-flow location receiver, role measured; owner unresolved.** `seq` extends `BroadcastReceiver` with fields `$$this$callbackFlow:Llss;` and `this$0:Lueq;`. The field name `$$this$callbackFlow` is the Kotlin compiler's synthetic marker for a receiver created inside a `callbackFlow{…}` builder; the referenced coroutine machinery is real (`ah7` in classes4 has a constructor taking `Lkotlin/coroutines/CoroutineContext;` — measured). The `this$0` class `ueq` implements `req` and its `b()` compares provider names `location`, `network`, `gps` (LocationManager provider checks — measured strings). So the virtualized method is a broadcast callback inside a coroutine-flow location-availability monitor. Whether that module is Grindr first-party or a location SDK cannot be resolved from the minified names — stated as unresolved.

### 3.3 Selection shape across the 20 **[measured]**

- 18 of 20 are `onReceive(Context, Intent)` — Android `BroadcastReceiver` callbacks; 1 is `AsyncTask.doInBackground`; 1 is `WorkManager Worker.doWork`. All are **event entry points**, none is a business computation returning app state.
- Vendors span 10 distinct third-party SDK origins (Agora, Google Mobile Ads, Fyber, AppLovin, PubNative, InMobi, Mintegral, ironSource AdQuality, Braze, Facebook), each with at least one directly-attributed stub; the two inferred rows extend already-listed origins (`nua0` → GMS ads, `bo.app.i4` → Braze), and #20's owner is unresolved.
- Manifest wiring (measured, `APK.get_receivers()`, §7c): 19 manifest receivers total; of the stub classes only **2** are manifest-registered — `com.braze.push.BrazePushReceiver` and `com.facebook.AuthenticationTokenManager$CurrentAuthenticationTokenChangedBroadcastReceiver`. The other 18 are dynamically registered receivers/workers (consistent with their `registerReceiver` code surviving in-class, e.g. PubNative `register`, ironSource `obd0.<init>`).

### 3.4 Count table — integrity vs feature **[measured categorization of measured stubs]**

| Category | Count | Entries |
|---|---|---|
| **Licensing / integrity glue** (`com.pairip.*`, signature, license, VM chain) | **0** | — |
| **Grindr first-party** (`com.grindrapp.*`) | **0** | — |
| Feature — 3rd-party call stack (Agora audio/proximity/connectivity) | 5 | #1–#5 |
| Feature — 3rd-party advertising (GMS ads ×3, Fyber ×2, AppLovin, PubNative, InMobi, Mintegral, ironSource AdQuality, `nua0` GMS-cluster) | 11 | #6–#16 |
| Feature — 3rd-party push/engagement & identity (Braze ×2 — #18 direct, #17 inferred; Facebook) | 3 | #17–#19 |
| Feature — location flow (owner unresolved) | 1 | #20 |
| **Total** | **20** | |

Evidence-grade split: 17 direct (literal package or in-class reference), 3 inferred (`nua0`, `bo.app.i4` — §3.1 — and `seq` — §3.2).

---

## 4. `vmcodeAssets` — absent **[measured twice]**

- Census: `"vmcodeAssets": []` (`census-base-named.json:8`).
- Independent check this session (stdlib `zipfile`, §7c): the APK contains **647** `assets/` entries and **zero** entries whose name contains `vmcode` (case-insensitive) or ends in `.vmcode`.
- Consistent with `docs/05` (§ quoted at `docs/05:175`): no plaintext `assets/*.vmcode` anywhere in the bundle (base: 647 assets/0 `.vmcode`; splits: no assets at all).

**[sourced context]** Where the VM payload actually lives: the census `integrityEntryPoints` chain (`census-base-named.json:311-321`) shows `VMRunner.getVmByteCode` → `readByteCode` → `openBaseApk`/`readFullByteArrayFromStream` with `VmDecryptor.<init>`/`decrypt` — bytecode is read out of the installed APK and decrypted at call time, keyed by the per-method token measured in §2. So the tokens are present and enumerable (this doc lists all 20), but their bytecode blobs are not statically enumerable by filename.

---

## 5. What this implies — for the integrity-first verdict of docs/02 and docs/05

This section is **[interpretation]**, built only on §2–§4 measurements and cited priors.

1. **The integrity-first verdict survives its sharpest test and is sharpened by it.** `docs/02`'s bottom line (`docs/02:118`) and `docs/05:175` describe a deployment that is "integrity-first": the always-on protection is the signature/license wrapper at process entry, with the VM shipped everywhere (all three ABI splits, `docs/05` §2) but sparsely invoked. The strongest remaining way that picture could have broken was if the 20 stubs turned out to be protection of Grindr's security or business chokepoints. They are not: **0 of 20 touch integrity or licensing; 0 of 20 are Grindr code**. All 20 are third-party SDK event plumbing. The Java-visible integrity stack itself (`SignatureCheck`, `LicenseClient`, `VMRunner` entry chain — 110 entry points, `census-base-named.json:233-1215`) is *not* stub-virtualized at all; its protection is placement at process entry plus the native layer, not Java-level virtualization.
2. **`docs/02:133`'s "targeted virtualization may be exactly the ones that mattered" hypothesis is substantially weakened — for this build.** `docs/02` left open that the 20 virtualized methods "may be exactly the ones that mattered" to the GrindrPlus kill. Now that they are named: virtualizing PubNative's volume-changed callback or Mintegral's screen-off receiver does not protect Grindr intellectual property, matching logic, paywall, or anti-tamper. The hypothesis retains force only insofar as the 20 are a *floor* (census notes: native-only virtualization, reflection-based delegation, and renamed runtimes are invisible to the heuristic, `census-base-named.json:1221`) and insofar as this is the 26.21.0 build — the GrindrPlus-era attribution concerned 26.3/26.4-era builds (`docs/02:133`), which this doc does not measure.
3. **The selection pattern reads as an automatic batch transform, not a curated protection list [interpretation].** All 20 are structurally identical small event entry points (18 `onReceive`, 1 `doInBackground`, 1 `doWork`) scattered across ≥10 third-party SDKs, with the same rewriter artifacts (`name$00N` accessors) in 15 of the 20 declaring classes. A partner that hand-picked methods worth protecting (the select-partner EAP of `@PlayAutomaticIntegrityProtection`, `docs/02:108`) would be expected to pick its own code; nothing in the list is Grindr code. The observed shape is what an automatic protector applying a uniform transform to SDK entry callbacks produces. This doc cannot determine which vendor tier Grindr is enrolled in — no assertion either way.
4. **Practical consequence for the program's feasibility question:** nothing in the Java stub set obstructs a runtime-hooking (GrindrPlus-style) module on this build — the stubs live in ad/engagement SDK callbacks, not in the app's matching/UI/subscription paths, and the integrity defenses remain the ones `docs/02` already catalogued (wrapper at `attachBaseContext`, native layer). Static repackaging remains a different matter (`docs/02:128`).

---

## 6. Limitations

- **The 20 are a floor, not a ceiling** — the census heuristic sees only Java-visible `VMRunner.invoke`/`executeVM` stubs; native-only virtualization, reflection-based delegation, and renamed/repackaged pairip runtimes are undetectable by it (`census-base-named.json:1221`). A low count does not prove absence of further protection.
- **Stub contents were not decoded.** This doc characterizes each method by its declaring class and surviving members; the VM bytecode behind each token was not decrypted or executed, so statements are about *what kind of method* was virtualized, not about the hidden body's exact behavior.
- **Three identifications are inferences** (`nua0` from its GMS-ads cluster; `bo.app.i4` from the external `bo.app`-is-Braze's-root convention plus accessor-pair similarity to #18; `seq`'s owner unresolved) — flagged in §3.1/§3.2; nothing above depends on those three being correct beyond their category (3rd-party/obfuscated event plumbing).
- **Single build.** All measurements are against 26.21.0 (versionCode 189896) only.
- **Census provenance.** The analyzer run itself predates this session (exit 0 per the task record; output read from disk this session); every headline number used here was re-derived independently (§7d recount) and every stub re-verified in the APK by hand.

---

## 7. Commands used (reproduction)

Environment: Windows/Git Bash, **Python 3.14.6**, **androguard 4.1.4** (both printed this session). All commands run from the workspace root; paths inside scripts relative to `pairip-research/`.

**(a) Census read.** `pairip-research/samples/out/census-base-named.json` read in full (this doc's §1 table). Headline recount run this session:

```bash
python -c "import json; d=json.load(open('pairip-research/samples/out/census-base-named.json')); \
print(len(d['stubMethodsList']), d['stubMethodsListTruncated'], d['vmcodeAssets'], \
d['dexStats']['stubMethods'], d['dexStats']['totalMethods'])"
# -> 20 False [] 20 422621
```

**(b) Androguard inspection of all 20 stubs + clusters — run by this doc's author this session** (androguard DEBUG logging disabled via `logging.disable(logging.CRITICAL)`; produces §2, §3.1–§3.3). Shape (full transcripts in session log):

```python
import logging; logging.disable(logging.CRITICAL)
import zipfile
from androguard.core.dex import DEX

z = zipfile.ZipFile("pairip-research/samples/apk/grindr-current-base.apk")
# For each of the 20 (dex, "L<class>;") pairs from census stubMethodsList:
d = DEX(z.read(dex_name))
for c in d.get_classes():
    if c.get_name() == target_class:
        # print superclass, interfaces, fields, every method's name/descriptor/
        # instruction count, flag any method whose instructions contain "VMRunner";
        # disassemble the census-named method in full; collect const-string values
        # across the class (the basis of every "strings" quote in §3).
        ...
# Cluster follow-ups (same API, named classes):
#   classes6: Lmua0; Lnua0; Loua0; Lpua0; Lkua0; Luu00;   -> §3.2 nua0
#   classes7: Lueq;  classes4 (located by scan): Llss; Lah7; -> §3.2 seq
#   classes9: Lobd0; disassembly of <init>/c/a/b          -> §3.2 obd0
#   classes2: Lbo/app/i4;
#   classes5: Lcom/braze/push/BrazePushReceiver; (getClass$001 body)
```

**(c) vmcode + manifest pass — run this session** (produces §3.3 manifest facts and §4):

```python
import logging; logging.disable(logging.CRITICAL)
import zipfile
z = zipfile.ZipFile("pairip-research/samples/apk/grindr-current-base.apk")
names = z.namelist()
print(len([n for n in names if n.startswith("assets/")]))   # -> 647
print([n for n in names if "vmcode" in n.lower()])          # -> []

from androguard.core.apk import APK
a = APK("pairip-research/samples/apk/grindr-current-base.apk")
print(a.get_receivers())  # -> 19 receivers, incl. the 2 stub classes of §3.3
```

**(d) Supporting reads this session.** `docs/02-feasibility-study.md` (lines 96, 108, 118, 128, 133), `docs/05-splits-census.md` (§2, line 175, §5 style), `samples/out/census-base-named.json` (all lines cited inline), `samples/out/census-base.json` (cross-reference), `docs/` directory listing.

---

**Bottom line [measured + interpretation]:** the 20 virtualized methods of the 26.21.0 base split are named, disassembled, and characterized: every one is a third-party SDK event callback (5 Agora call-audio, 11 advertising, 3 push/identity, 1 location-flow) — **0 integrity/licensing, 0 Grindr first-party** — each replaced by the same `VMRunner.invoke(token, {this, args…})` stub with a unique 16-char token, `vmcodeAssets` absent, bytecode fetched and decrypted at call time. The integrity-first verdict of `docs/02`/`docs/05` is thereby strengthened: what virtualization is **visible at the Java-stub level measured here** is scatter-shot SDK plumbing, consistent with an automatic batch transform, not protection of Grindr's or the integrity stack's chokepoints — a claim about the 20 Java-visible stubs only; they are a floor, not a ceiling (§6), and native-only virtualization, reflection-based delegation, and renamed runtimes remain unmeasured.
