# Runtime Observation — First Run of Current Grindr (26.21.0) on BlueStacks, via adb logcat

**Date:** 2026-10-23 (log captured this date; doc written same day from the pulled log)
**Deliverable:** `docs/07` of the PairIP/GrindrPlus research program (charter in repo README; ROE in `ROE.md`). This is the *optional observational follow-up* that `ROE.md` §2 pre-authorized: "Lab: Local workstation; BlueStacks reserved for optional *observational* follow-up (logcat), not part of automated runs."
**Question answered:** What does a stock, unmodified first run of the current PairIP-protected Grindr build (versionName 26.21.0, versionCode 189896) actually do at startup on an emulator — which PairIP components appear in logcat, in what order, and does the app crash or continue?
**Method:** The runtime run (device check, install, launch, 35 s wait, logcat pull) was executed once on BlueStacks via adb; this session's work is reading and quoting the pulled log. **[run]** marks a fact from the run record handed to this task: `{"deviceOk":true,"installOk":true,"logPulled":true,"note":"process after 35s: 8445; log pull ok"}`. **[log L###]** marks a verbatim line of `pairip-research/samples/out/gp-first-run.log` at that line number (quoted exactly, no paraphrase). **[inferred]** marks reasoning that goes beyond what any log line states. Commands I ran this session are listed in §8; I did not touch the device this session.

---

## 0. Protocol — what this run was and was not

**This was OBSERVATIONAL ONLY.**

- **No Frida.** No frida-server, no injection, no scripting of the process. (Corroborated negatively: the log contains zero `frida` matches — §8, command 5.)
- **No Xposed usage.** No module was loaded, configured, or invoked for this observation. (The BlueStacks image itself carries an LSPosed status notification — an environment fact disclosed in §2.3; it was not part of the observation and no evidence in the log shows any module acting on Grindr.)
- **No instrumentation of any kind.** No debugger attach, no ptrace, no sysprop toggles, no `setprop debug.*` (the log's only mention of that flag is Firebase suggesting it — [log L812](#) `To enable faster debug mode event logging run:` / `adb shell setprop debug.firebase.analytics.app com.grindrapp.android`, which is an SDK hint printed by the app, not an action taken). The app was installed with the stock `adb install` of the unmodified distributed bundle, launched once via `monkey` (the stock launcher path — [log L402]), and observed by reading `logcat -d` output.
- **No account created.** The observed flow never reached an account-creation screen (see §5 for what UI was actually reached); no credentials were entered anywhere.
- **Observation stopped at the first-run UI.** One launch, ~35 s of logcat, pull, stop.
- **Any network traffic observed is the app's own normal client behavior.** The log shows first-run SDK traffic (AppsFlyer, Facebook SDK, Firebase, Braze, Google Play licensing/integrity) — all initiated by the unmodified app itself; nothing was intercepted, redirected, or MITM'd.

This stays inside `ROE.md` §1: no bypass artifacts, no modified APK, no active testing against Grindr infrastructure. The APK installed is the distributed artifact characterized statically in `docs/02`.

---

## 1. Run record and artifacts

| Item | Value | Source |
|---|---|---|
| Device up | `deviceOk: true` | **[run]** |
| Install OK | `installOk: true` | **[run]** |
| Log pulled | `logPulled: true`, note `process after 35s: 8445; log pull ok` | **[run]** |
| App / version | `com.grindrapp.android`, versionCode 189896, versionName 26.21.0, `isUpdate: false` (fresh install) | **[log L230, L232]** (BlueStacks `onAppInstalled` host call) |
| Installed bundle | `base.apk` (72,037,281 B) + `split_config.arm64_v8a.apk` (24,962,889 B) + `split_config.x86.apk` (22,599,233 B) + `split_config.x86_64.apk` (23,225,978 B) + `split_config.xxhdpi.apk` (10,147,126 B) | directory listing of `pairip-research/samples/apk/splits/` this session; on-device install of exactly these five APKs is log-shown — [log L741] DexPathList enumerates `base.apk`, `split_config.arm64_v8a.apk`, `split_config.x86.apk`, `split_config.x86_64.apk`, `split_config.xxhdpi.apk` under `/data/app/com.grindrapp.android-5CvRpwTmQmI5G413DAckZg==/` |
| Log artifact | `pairip-research/samples/out/gp-first-run.log` — 338,052 bytes, 2,426 lines, starts `--------- beginning of main`, covers **10-23 20:31:08.065 → 20:31:50.434** (42.4 s) | `wc -l` + `head`/`tail` this session (§8, command 1) |
| Launcher activity | `com.grindrapp.android.HomeActivityOriginal` | **[log L230, L412]** |

`samples/` is gitignored (ROE §4 hygiene), so the log is local-only, like the APKs.

**Process inventory of the run (all log-shown):** three `com.grindrapp.android` processes existed in the window — pid **7955** (started 20:31:12.704 for the launcher activity, exited 20:31:23.714), pid **8280** (started 20:31:24.748 for a restarted chat service, exited 20:31:28.197), pid **8445** (started 20:31:48.487 for a Firebase DataTransport job, still alive at the log's last line). The run note `process after 35s: 8445` is corroborated by the log: 8445's start at 20:31:48.487 is ~35.8 s after the first app process started at 20:31:12.704, and the final log lines (L2420–L2426) are LicenseClient traffic from pid 8445.

---

## 2. Environment facts visible in the log

These frame every interpretation below. All are **[log]**-shown.

### 2.1 BlueStacks, x86, SELinux permissive

- BlueStacks identity: `BlueStacks Virtual Touch` input device [log L479, L524]; `BstCommandProcessor` / `BstCommandProcessor-Application` / `BstCommandProcessor-CommandHandler` tags (pid 2500); `HCALL`/`VMSG` host-call service (system_server); `bstsensor_*` tags; `bstSpecialAppKeyboardHandlingEnabled` suffix on TopActivityInfo lines.
- SELinux is permissive on the instance: every app Zygote spawn prints `seccomp disabled by setenforce 0` [log L446 for 7955, L1152 for 8280, L2121 for 8445].
- CPU/ABI: processes print `Unexpected CPU variant for X86 using defaults: x86_64` [log L1153 for 8280], and the app's classloader lists `nativeLibraryDirectories=[.../lib/x86, ...]` [log L741] — the **x86** native libraries of the bundle are what got loaded on this instance. **[inferred]** from those two lines: the running ABI is x86 (the BlueStacks VM), not arm64; the log does not directly print "ABI = x86".

### 2.2 Google Play services / Play Store present, with an account

- GMS 26.36.63 (from dynamite suffix `@263663017@26.36.63` throughout), Finsky (Play Store, pid 3522) active.
- A Play account exists on the instance: `com.grindrapp.android: Account determined from library ownership - [FEKsdAsRCKzGIfaJRcF4GS9EYXDQZUaCa1XiWjUVnvs]` [log L818, L824] and `Billing preferred account via installer for com.grindrapp.android` [log L819-area, L1937, L1939].
- WebView provider is Chrome: the app's WebView use spawned `com.android.chrome:sandboxed_process0` (pid 8213) [log L906], and the app logged a caught `ClassNotFoundException: Didn't find class "android.webkit.PacProcessor"` against Chrome's APK path [log L741-area].

### 2.3 LSPosed present on the image (not used by this run)

The BlueStacks image itself carries LSPosed, visible as system noise:

```
490: 10-23 20:31:13.537 D/NotificationService( 2215): notification record before applyZenModeLocked NotificationRecord(... pkg=android ... key=0|android|2000|null|1000 ... (channel=lsposed_status ...))
578: 10-23 20:31:14.827 W/Notification( 2536): warning: pkg android attempting to substitute app name 'LSPosed' without holding perm android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME
```

This is an **environment fact**, disclosed for honesty and because it is a plausible confounder for Play Integrity verdicts on this instance (§3.5, §6.3). Nothing in the log shows any LSPosed module interacting with Grindr; the observation used no Xposed capability (§0). Also visible in the same window: unrelated third-party apps on the instance (e.g. an Instagram process [log L~470-area `uid=10067(com.instagram.android)`], a dual-space/clone-app notification [log L244-area]) — the instance is a working multi-app BlueStacks, not a clean-room device.

### 2.4 logd rate limiting (chatty) hid most app-side lines

Android's `chatty` collapsed the app's own logging: at process start logd recorded `identical 184 lines` [log L447] and dozens of `expire N lines` entries across all three app pids, and re-tagged surviving app-origin lines with the truncated process name (`I/indrapp.androi`). Consequence (stated as a limit, not a finding): **the app's own first-party log output is mostly not visible in this capture**; what is quotable is system-server, Play-services, and the minority of app/SDK lines that survived rate limiting.

---

## 3. Every PairIP/keyword-matching log line, verbatim

The ask defines the quote set as tags/components containing `pairip`, `VMRunner`, `SignatureCheck`, `license`, `integrity`. Command 2 in §8 (`grep -n -i -E "pairip|VMRunner|SignatureCheck|licens|integrity"`) matches **exactly 44 lines**; all 44 are quoted below, grouped by who authored them. Attribution labels are careful: (a) lines that literally name `com.pairip.*` are PairIP-component lines by name; (b) `SignatureCheck` is a tag whose PairIP identity rests on `docs/01` §3.2, not on the log; (c) `LicenseClient`/`PlayCore`/`Finsky`/`AsyncOperation` lines are Google Play code running *for* the app — the log alone cannot prove which caller (PairIP licensing layer vs. Grindr's own integration) drove them (§6.2); (d) `IMGLY` lines match the keyword "license" but belong to the IMG.LY editor SDK, not PairIP.

### 3.1 Lines naming `com.pairip.*` components — 7 lines (all system-side observations of PairIP components)

```text
L1026: 10-23 20:31:21.102 I/ActivityManager( 2215): START u0 {flg=0x10010000 cmp=com.grindrapp.android/com.pairip.licensecheck.LicenseActivity (has extras)} from uid 10080
L1027: 10-23 20:31:21.106 D/ActivityManager( 2215): TopActivityInfo, pkgName: com.grindrapp.android activityName: com.pairip.licensecheck.LicenseActivity callingPackage: com.grindrapp.android  bstSpecialAppKeyboardHandlingEnabled = false
L1060: 10-23 20:31:21.667 D/ActivityManager( 2215): TopActivityInfo, pkgName: com.grindrapp.android activityName: com.grindrapp.android/com.pairip.licensecheck.LicenseActivity callingPackage:   bstSpecialAppKeyboardHandlingEnabled = false
L1095: 10-23 20:31:23.101 E/FA      ( 7955): Throwable caught in onActivityCreated: java.lang.RuntimeException: Parcelable encountered ClassNotFoundException reading a Serializable object (name = com.pairip.licensecheck.LicenseActivity$ActivityType): m7.tc.a(:com.google.android.gms.dynamite_measurementdynamite@263663017@26.36.63 (100800-0):42)
L1102: 10-23 20:31:23.493 W/ActivityManager( 2215): Duplicate finish request for ActivityRecord{9644e22 u0 com.grindrapp.android/com.pairip.licensecheck.LicenseActivity t510 f}
L1122: 10-23 20:31:24.413 W/SurfaceFlinger( 1927): Attempting to destroy on removed layer: AppWindowToken{a849670 token=Token{fcfd0b3 ActivityRecord{9644e22 u0 com.grindrapp.android/com.pairip.licensecheck.LicenseActivity t510}}}#0
L1946: 10-23 20:31:27.712 D/TelephonyManager( 8280): creating subscriptionInfo Record, context : com.pairip.application.Application@e8ca5a8
```

Reading of these seven (facts, then one inference):
- **Fact:** a `com.pairip.licensecheck.LicenseActivity` was started by the app itself (uid 10080) at 20:31:21.102 with extras, became top activity, and was finished by 20:31:23.493.
- **Fact:** the app's `Application` subclass is `com.pairip.application.Application` — the TelephonyManager line names the live context object's class [log L1946]. This is the PairIP-injected application wrapper (dossier §2/§4 describe `com.pairip.application.Application` as the PairIP entry point; here it is directly observed as the running Application class).
- **Fact:** Firebase Analytics hit a *caught* `RuntimeException` while parcel-reading the LicenseActivity's intent extras — the nested `com.pairip.licensecheck.LicenseActivity$ActivityType` class could not be loaded by GMS's measurement dynamite classloader [log L1095]. Logged at E level by `FA`, explicitly "Throwable caught" — **not** a crash (§4).
- **[inferred]:** the FA error is a benign integration seam (GMS's dynamite classloader doesn't see the app's `ActivityType` Serializable); it did not stop the flow — the LicenseActivity was finished normally 0.4 s later.

### 3.2 `SignatureCheck` tag — 2 lines

```text
L1171: 10-23 20:31:25.129 I/SignatureCheck( 8280): Signature check ok
L2127: 10-23 20:31:48.818 I/SignatureCheck( 8445): Signature check ok
```

- **Fact:** a component tagged `SignatureCheck` inside the Grindr process printed `Signature check ok` twice — once per process start (8280: ~0.4 s after `Start proc`; 8445: ~0.33 s after `Start proc`), each time *before* Firebase initialization lines (see §5 ordering).
- **Attribution [inferred, from docs/01 §3.2, grade high.local.2026]:** this is the PairIP Java-side signature gate (`com.pairip.SignatureCheck`, executed around `Application.attachBaseContext` per the dossier). The log alone shows only the tag name and the verdict "ok". Notably the check **passed** — the APK's signature verified — so the subsequent app exits (§4) were not signature-gate crashes.
- **Fact:** no `SignatureCheck` line is visible from pid 7955 (the first, UI-bearing process). **[inferred]:** it very likely ran there too but was among the chatty-collapsed lines (§2.4); absence of the line is not evidence the check didn't run.

### 3.3 `VMRunner` tag — 0 lines

`grep -c -i "vmrunner"` returned **0** (§8, command 4). No VMRunner-tagged line exists anywhere in the 42-second window. Consistent with the dossier's account of the VM (its bytecode interpreter does not log to logcat by design); nothing more can be said from this log.

### 3.4 Play licensing lines from inside the app processes (`LicenseClient`) — 11 lines

```text
L810:  10-23 20:31:18.637 D/LicenseClient( 7955): Connecting to the main licensing service...
L928:  10-23 20:31:20.659 D/LicenseClient( 7955): Connected to the licensing service.
L935:  10-23 20:31:20.727 D/LicenseClient( 7955): Sending request to licensing service...
L936:  10-23 20:31:20.743 D/LicenseClient( 7955): Request to licensing service sent.
L1928: 10-23 20:31:27.449 D/LicenseClient( 8280): Connecting to the main licensing service...
L1943: 10-23 20:31:27.615 D/LicenseClient( 8280): Connected to the licensing service.
L1945: 10-23 20:31:27.710 D/LicenseClient( 8280): Sending request to licensing service...
L1947: 10-23 20:31:27.717 D/LicenseClient( 8280): Request to licensing service sent.
L2420: 10-23 20:31:50.198 D/LicenseClient( 8445): Connecting to the main licensing service...
L2424: 10-23 20:31:50.392 D/LicenseClient( 8445): Connected to the licensing service.
L2426: 10-23 20:31:50.434 D/LicenseClient( 8445): Sending request to licensing service...
```

- **Fact:** each of the three app processes ran a full `LicenseClient` connect→send round (7955: 18.637→20.743, overlapping the LicenseActivity flow; 8280: 27.449→27.717; 8445: 50.198→50.434, request still in flight at log end).
- **Attribution [inferred, from docs/01 §3.4, grade med.web.2026]:** the dossier documents a `LicenseClient` class inside `com.pairip.licensecheck` with `connectToLicensingService()`. The tag name and timing (immediately around the PairIP LicenseActivity) match; the log cannot by itself prove the caller is PairIP code rather than Grindr's own Play-licensing integration.

### 3.5 Play Integrity lines — 20 lines (PlayCore/Finsky from app+store; AsyncOperation/BoundBrokerSvc from GMS)

From the app's process (PlayCore) and the Play Store (Finsky):

```text
L828:  10-23 20:31:19.020 I/PlayCore( 7955): UID: [10080]  PID: [7955] IntegrityService : requestIntegrityToken(IntegrityTokenRequest{nonce=NGQyYTE3N2I5MzZiMGRlY2MxMjlmOTc4NDZlMWNjY2Q5OTFmZDljOTdkNzk4OTI2OGE0N2IyMTRhNzZlN2IwNg==, cloudProjectNumber=676451317595, network=null})
L842:  10-23 20:31:19.104 I/PlayCore( 7955): UID: [10080]  PID: [7955] IntegrityService : Initiate binding to the service.
L929:  10-23 20:31:20.698 I/PlayCore( 7955): UID: [10080]  PID: [7955] IntegrityService : ServiceConnectionImpl.onServiceConnected(ComponentInfo{com.android.vending/com.google.android.finsky.integrityservice.IntegrityService})
L933:  10-23 20:31:20.709 I/PlayCore( 7955): UID: [10080]  PID: [7955] IntegrityService : linkToDeath
L1084: 10-23 20:31:22.349 I/Finsky  ( 3522): [134] requestIntegrityToken() finished for com.grindrapp.android.
L1085: 10-23 20:31:22.355 I/PlayCore( 7955): UID: [10080]  PID: [7955] OnRequestIntegrityTokenCallback : onRequestIntegrityToken
L1086: 10-23 20:31:22.355 I/PlayCore( 7955): UID: [10080]  PID: [7955] IntegrityService : Unbind from service.
```

From Google Play services (pid 2793) — service binds and **eight identical token-generation failures**:

```text
L972:  10-23 20:31:20.893 D/BoundBrokerSvc( 2793): onBind: Intent { act=com.google.android.gms.play.integrity.api.service.IntegrityApiDisplayListenerApiService.START dat=chimera-action: cmp=com.google.android.gms/.chimera.PersistentApiServiceNoInstantApps }
L975:  10-23 20:31:20.896 D/BoundBrokerSvc( 2793): Loading bound service for intent: Intent { act=com.google.android.gms.play.integrity.api.service.IntegrityApiDisplayListenerApiService.START dat=chimera-action: cmp=com.google.android.gms/.chimera.PersistentApiServiceNoInstantApps }
L1973: 10-23 20:31:28.313 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L1987: 10-23 20:31:28.375 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2000: 10-23 20:31:28.382 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2013: 10-23 20:31:28.395 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2027: 10-23 20:31:28.518 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2042: 10-23 20:31:28.534 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2056: 10-23 20:31:28.562 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2069: 10-23 20:31:28.586 W/AsyncOperation( 2793): OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]
L2111: 10-23 20:31:35.666 D/BoundBrokerSvc( 2793): onBind: Intent { act=com.google.android.gms.potokens.service.IntegrityTokenRefreshTaskService.ACTION_TASK_READY dat=chimera-action: cmp=com.google.android.gms/.chimera.GmsInternalBoundBrokerService }
L2112: 10-23 20:31:35.666 D/BoundBrokerSvc( 2793): Loading bound service for intent: Intent { act=com.google.android.gms.potokens.service.IntegrityTokenRefreshTaskService.ACTION_TASK_READY dat=chimera-action: cmp=com.google.android.gms/.chimera.GmsInternalBoundBrokerService }
L2114: 10-23 20:31:35.677 D/BoundBrokerSvc( 2793): onUnbind: Intent { act=com.google.android.gms.potokens.service.IntegrityTokenRefreshTaskService.ACTION_TASK_READY dat=chimera-action: cmp=com.google.android.gms/.chimera.GmsInternalBoundBrokerService }
```

*(All eight `AsyncOperation` lines are byte-identical apart from their timestamps — re-verified against the file this session, §8, command 9.)*

- **Fact:** the app requested one Play Integrity token (nonce + `cloudProjectNumber=676451317595`); Finsky reported the request "finished" at 22.349 and PlayCore received its callback at 22.355 — the log does **not** show the verdict payload. Separately, GMS logged eight `Unable to generate a new integrity token.` failures at 28.3–28.6 (after both app processes had exited).
- **[inferred]:** the 8× AsyncOperation failures are GMS-side token-refresh failures — the classic emulator/Play-Integrity-refuses-emulators pattern; the log gives no reason code. Whether the app's single requestIntegrityToken round-trip (22.349 "finished") returned a usable token is **not determinable** from these lines.

### 3.6 `license`-keyword lines that are NOT PairIP — IMG.LY SDK, 4 lines

```text
L1819: 10-23 20:31:25.901 V/IMGLY   ( 8280): Read PhotoEditor SDK license file
L1820: 10-23 20:31:25.911 V/IMGLY   ( 8280): Read VideoEditor SDK license file
L2403: 10-23 20:31:49.380 V/IMGLY   ( 8445): Read PhotoEditor SDK license file
L2404: 10-23 20:31:49.395 V/IMGLY   ( 8445): Read VideoEditor SDK license file
```

These are the IMG.LY photo/video editor SDK reading its own commercial license files from app assets. They match the keyword "license" and are quoted for completeness; they have **no relation to PairIP**.

### 3.7 Inventory check

7 (§3.1) + 2 (§3.2) + 0 (§3.3) + 11 (§3.4) + 20 (§3.5) + 4 (§3.6) = **44 lines = the full grep result**. No keyword-matching line is omitted.

---

## 4. Crashes — none; both exits were deliberate `System.exit(0)` self-terminations

**There is no FATAL exception and no AndroidRuntime crash dump anywhere in the log.** Verified this session (§8, command 3): `grep -c "FATAL"` → `0`; `grep -c "FATAL EXCEPTION"` → `0`. The only `AndroidRuntime` lines are the monkey tool's own startup/exit and the app processes' clean VM-exit notices.

What actually happened to the first two processes — quoted exactly:

```text
L1103: 10-23 20:31:23.502 I/indrapp.androi( 7955): System.exit called, status: 0
L1104: 10-23 20:31:23.502 I/AndroidRuntime( 7955): VM exiting with result code 0, cleanup skipped.
L1111: 10-23 20:31:23.714 I/Zygote  ( 1904): Process 7955 exited cleanly (0)
L1113: 10-23 20:31:23.716 I/ActivityManager( 2215): Process com.grindrapp.android (pid 7955) has died: fore TOP 
L1117: 10-23 20:31:23.727 W/ActivityManager( 2215): Scheduling restart of crashed service com.grindrapp.android/.chat.service.ChatMessageSenderService in 1000ms
...
L1959: 10-23 20:31:28.105 I/indrapp.androi( 8280): System.exit called, status: 0
L1960: 10-23 20:31:28.106 I/AndroidRuntime( 8280): VM exiting with result code 0, cleanup skipped.
L1966: 10-23 20:31:28.197 I/Zygote  ( 1904): Process 8280 exited cleanly (0)
L1962: 10-23 20:31:28.190 I/ActivityManager( 2215): Process com.grindrapp.android (pid 8280) has died: cch  CEM 
```

- **Fact:** both app processes ended via an explicit `System.exit called, status: 0` logged from inside the app (`indrapp.androi` is logd's process-name retag of the app's own tag, §2.4), with Zygote confirming `exited cleanly (0)` — no tombstone, no crash dialog, no `AndroidRuntime` FATAL block.
- **Fact:** ActivityManager's `Scheduling restart of crashed service ...` [log L1117] is boilerplate wording that fires when a process dies while a started service is bound; the same log's Zygote lines show the death was a clean exit, so "crashed" there is the system's phrasing, not a Java crash.
- **Fact (complete list of non-fatal exceptions visible in the window, for the record):** (1) the caught FA `RuntimeException` on `com.pairip.licensecheck.LicenseActivity$ActivityType` [L1095, quoted §3.1]; (2) the app's caught `ClassNotFoundException: android.webkit.PacProcessor` at I level [L741-area]; (3) the app's caught `NoClassDefFoundError: com.appsflyer.lvl.AppsFlyerLVL$resultListener` [L730, L741] — AppsFlyer's optional License-Verification-Library helper class is absent from the APK, so that helper fails to initialize (caught, non-fatal); (4) GMS-internal `ijwn` "ManagedChannel allocation site" RuntimeExceptions from pid 2793 [L192–L217 area] — Google Play services noise, unrelated to the app.
- **[inferred]:** the `System.exit(0)` calls are the app terminating itself. No log line states the reason. The sequencing (§5) is what supports the licensing interpretation in §6.1.

---

## 5. Startup timeline — what initialized, in what order (log-shown only)

All entries below are **[log]** facts; the one-sentence readings after each block only name the actor. Timestamps are as printed.

**Install completes (pre-launch).**

```text
L188  10-23 20:31:09.842 D/BstCommandProcessor-PackageIntentReceiver( 2500): pkg is: com.grindrapp.android event is android.intent.action.PACKAGE_ADDED
L230  10-23 20:31:09.995 D/BstCommandProcessor-CommandHandler( 2500): calling native onAppInstalled function, pkgName: com.grindrapp.android activity: com.grindrapp.android.HomeActivityOriginal appLabel: Grindr, versionCode: 189896, versionName: 26.21.0 iconFileName: com.grindrapp.android.png, source: user, isUpdate: false, isHomeApp: false, orientation:
```

Play Store/GMS react to the new package (Finsky invalidates its app-info cache [L221]; GCM/NetworkScheduler forward the PACKAGE_ADDED [L251, L269]).

**Launch via monkey (uid 2000), first app process 7955.**

```text
L402  10-23 20:31:12.307 W/Monkey  ( 7942): args: [-p, com.grindrapp.android, -c, android.intent.category.LAUNCHER, 1]
L412  10-23 20:31:12.396 I/ActivityManager( 2215): START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.grindrapp.android/.HomeActivityOriginal} from uid 2000
L439  10-23 20:31:12.704 I/ActivityManager( 2215): Start proc 7955:com.grindrapp.android/u0a80 for activity com.grindrapp.android/.HomeActivityOriginal
L446  10-23 20:31:12.781 I/Zygote  ( 7955): seccomp disabled by setenforce 0
L447  10-23 20:31:12.787 I/chatty  ( 7955): uid=10080(com.grindrapp.android) identical 184 lines
```

HomeActivityOriginal never drew a frame (no `onWindowsDrawn` for it anywhere in the log; the only two `onWindowsDrawn` lines in the file are quoted below). The app's own dex2oat children (pids 8042/8051, uid 10080) compiled during startup [L591, L596, L626 chatty lines].

**App routes itself to the login activity and starts Play licensing + integrity.**

```text
L628  10-23 20:31:17.579 I/ActivityManager( 2215): START u0 {flg=0x14008000 cmp=com.grindrapp.android/.ui.login.LoginActivity (has extras)} from uid 10080
L810  10-23 20:31:18.637 D/LicenseClient( 7955): Connecting to the main licensing service...
L814  10-23 20:31:18.694 I/Choreographer( 7955): Skipped 237 frames!  The application may be doing too much work on its main thread.
L818  10-23 20:31:18.844 I/Finsky  ( 3522): [139] com.grindrapp.android: Account determined from library ownership - [FEKsdAsRCKzGIfaJRcF4GS9EYXDQZUaCa1XiWjUVnvs]
L828  10-23 20:31:19.020 I/PlayCore( 7955): ... IntegrityService : requestIntegrityToken(IntegrityTokenRequest{nonce=NGQyYTE3...wNg==, cloudProjectNumber=676451317595, network=null})
```

Concurrently the app's SDKs initialize (all caught in the log): AppsFlyer 6.18.1 config/referrer activity [L844, L845, L932 — install referrer retrieval failed with "Binder invocation to an incorrect interface"], Facebook SDK not-yet-initialized notices [L~813 `GraphRequest can't be used when Facebook SDK isn't fully initialized`], GMS measurement dynamite [L847-area FlagStore SecurityException showing the app's signing-cert SHA-256 as computed by GMS: `6e21a5f966a7252628cd8f5982d93086a0fcf76c09edb9d7731964bb1c842897`], maps dynamite version [L718], Google Analytics socket connections [L965, L1051].

**Licensing service round-trip, then the PairIP LicenseActivity takes over the UI.**

```text
L928  10-23 20:31:20.659 D/LicenseClient( 7955): Connected to the licensing service.
L935  10-23 20:31:20.727 D/LicenseClient( 7955): Sending request to licensing service...
L936  10-23 20:31:20.743 D/LicenseClient( 7955): Request to licensing service sent.
L1026 10-23 20:31:21.102 I/ActivityManager( 2215): START u0 {flg=0x10010000 cmp=com.grindrapp.android/com.pairip.licensecheck.LicenseActivity (has extras)} from uid 10080
L1084 10-23 20:31:22.349 I/Finsky  ( 3522): [134] requestIntegrityToken() finished for com.grindrapp.android.
L1088 10-23 20:31:23.067 D/ActivityManager( 2215): onWindowsDrawn: packageName = com.grindrapp.android, name = com.grindrapp.android.ui.login.LoginActivity, mCallingPackage = com.grindrapp.android
L1095 10-23 20:31:23.101 E/FA ( 7955): Throwable caught ... com.pairip.licensecheck.LicenseActivity$ActivityType ...
L1096 10-23 20:31:23.138 I/ActivityManager( 2215): START u0 {act=com.google.android.finsky.LAUNCH_PLAY_PASS_PAYWALL_PAGE dat=playPassPaywall:/com.grindrapp.android pkg=com.android.vending cmp=com.android.vending/com.google.android.finsky.activities.MainActivityPrivate (has extras)} from uid 10012
L1102 10-23 20:31:23.493 W/ActivityManager( 2215): Duplicate finish request for ActivityRecord{9644e22 u0 com.grindrapp.android/com.pairip.licensecheck.LicenseActivity t510 f}
L1103 10-23 20:31:23.502 I/indrapp.androi( 7955): System.exit called, status: 0
L1111 10-23 20:31:23.714 I/Zygote  ( 1904): Process 7955 exited cleanly (0)
```

Ordering facts within this block: LoginActivity drew its first frame at 23.067 (the only Grindr UI frame ever drawn), the caught FA exception fired at 23.101, the **Play Store itself** (uid 10012) launched a Play Pass paywall page targeting `playPassPaywall:/com.grindrapp.android` at 23.138, the LicenseActivity was finished by 23.493, and the app self-exited at 23.502.

**Second process 8280 — system restarts the chat service; full SDK stack initializes; SignatureCheck visible; second self-exit.**

```text
L1117 10-23 20:31:23.727 W/ActivityManager( 2215): Scheduling restart of crashed service com.grindrapp.android/.chat.service.ChatMessageSenderService in 1000ms
L1150 10-23 20:31:24.748 I/ActivityManager( 2215): Start proc 8280:com.grindrapp.android/u0a80 for service com.grindrapp.android/.chat.service.ChatMessageSenderService
L1154 10-23 20:31:24.885 W/ActivityManager( 2215): Stopping service due to app idle: u0a80 -5s294ms com.grindrapp.android/.chat.service.ChatMessageSenderService
L1171 10-23 20:31:25.129 I/SignatureCheck( 8280): Signature check ok
L1172 10-23 20:31:25.226 I/FirebaseApp( 8280): Device unlocked: initializing all Firebase APIs for app [DEFAULT]
L1173 10-23 20:31:25.250 I/FirebaseCrashlytics( 8280): Initializing Firebase Crashlytics 20.1.1 for com.grindrapp.android
L1491 10-23 20:31:25.414 D/libcrashlytics( 8280): Initializing libcrashlytics version 3.2.0
L1512 10-23 20:31:25.553 D/libcrashlytics( 8280): Initializing native crash handling successful.
L1527 10-23 20:31:25.668 I/FirebaseInitProvider( 8280): FirebaseApp initialization successful
L1819 10-23 20:31:25.901 V/IMGLY ( 8280): Read PhotoEditor SDK license file
L1899 10-23 20:31:26.631 I/Braze v42.2.0 .Braze( 8280): Braze.configure() called with configuration: Builder(apiKey=3fe66e8b-..., customEndpoint=gaspra.iad-03.braze.com, ...)
L1928 10-23 20:31:27.449 D/LicenseClient( 8280): Connecting to the main licensing service...
L1946 10-23 20:31:27.712 D/TelephonyManager( 8280): creating subscriptionInfo Record, context : com.pairip.application.Application@e8ca5a8
L1950 10-23 20:31:27.744 I/ActivityManager( 2215): Fully drawn com.android.vending/com.google.android.finsky.activities.MainActivityPrivate: +3s303ms (total +15s125ms)
L1959 10-23 20:31:28.105 I/indrapp.androi( 8280): System.exit called, status: 0
```

Meanwhile the foreground UI was the **Play Store's** paywall page (fully drawn 27.744), not any Grindr surface. After 8280's exit, GMS logged its 8× integrity-token failures (§3.5, 28.3–28.6).

**Third process 8445 — system-started Firebase job, still alive at window end.**

```text
L2120 10-23 20:31:48.487 I/ActivityManager( 2215): Start proc 8445:com.grindrapp.android/u0a80 for service com.grindrapp.android/com.google.android.datatransport.runtime.scheduling.jobscheduling.JobInfoSchedulerService
L2127 10-23 20:31:48.818 I/SignatureCheck( 8445): Signature check ok
L2128 10-23 20:31:48.919 I/FirebaseApp( 8445): Device unlocked: initializing all Firebase APIs for app [DEFAULT]
L2143 10-23 20:31:49.160 I/FirebaseInitProvider( 8445): FirebaseApp initialization successful
L2403 10-23 20:31:49.380 V/IMGLY ( 8445): Read PhotoEditor SDK license file
L2420 10-23 20:31:50.198 D/LicenseClient( 8445): Connecting to the main licensing service...
L2426 10-23 20:31:50.434 D/LicenseClient( 8445): Sending request to licensing service...   ← last line of the log
```

**Initialization order, condensed (per process, as visible):** Zygote spawn (seccomp/permissive notice) → classloader/JIT lines → **`SignatureCheck` … ok** → FirebaseApp/Crashlytics/libcrashlytics → NetworkSecurityConfig (`debugBuild: false`) → IMGLY licenses → Braze configure → `LicenseClient` licensing round → (7955 only: UI flow with LicenseActivity) → `System.exit(0)`. In 7955 the SignatureCheck line is not visible (chatty, §3.2), but the licensing round preceded the LicenseActivity by ~2.5 s.

---

## 6. Interpretation — explicitly inference, cross-referenced

Nothing in this section is a log line; each item is **[inferred]** and says so.

**6.1 The licensing layer engaged on this sideloaded copy and the app self-terminated — a firsthand corroboration of the dossier's "silent-exit path."** The dossier (`docs/01` §3.4, grade med.web.2026, sourced from the paseo issue #4417 logcat) documents that PairIP's `com.pairip.licensecheck` failure mode includes `LicenseCheckException` → `System.exit(0)` with **no crash dialog, tombstone, or Play crash report**. This run reproduces exactly that signature on a different app (Grindr 26.21.0), different channel (BlueStacks sideload), with the log showing: LicenseClient round-trip → `com.pairip.licensecheck.LicenseActivity` foregrounded → Play Store Play-Pass paywall launched *by Finsky* → LicenseActivity finished → `System.exit called, status: 0` → clean process exit. The second process repeated LicenseClient → `System.exit(0)`. The log never prints a reason for either exit, so "the license check failed and the app deliberately quit" is inference from sequencing — but it is the sequencing the dossier predicts for an unlicensed (adb-installed, `source: user`) copy. This upgrades the silent-exit claim from "one secondhand-reported instance" to "independently observed first- and second-hand in this program's own log," within the limits of one emulator run.

**6.2 Which caller drove LicenseClient/PlayCore is not provable from the log.** The `LicenseClient` tag matches `com.pairip.licensecheck.LicenseClient` (dossier §3.4) and the timing brackets the PairIP LicenseActivity, but Grindr also ships its own Play integrations. The attribution is probable, not log-proven. Same for the Play Integrity request: it is issued from the app's uid, but whether PairIP code or Grindr code issued it cannot be distinguished from logcat.

**6.3 The Play Integrity environment verdicts were negative or unusable on this instance.** GMS's eight `Unable to generate a new integrity token.` failures [L1973–L2069] match the well-known Play-Integrity-on-emulator pattern. Contributing environment factors visible in the log: the instance is an emulator (BlueStacks markers, §2.1), SELinux is permissive [L446], and LSPosed is present on the image (§2.3). Which factor(s) caused the failures is not determinable from the log — and none of them were introduced *by this run* (§0).

**6.4 The signature gate passed.** `Signature check ok` twice, and no `SignatureTamperedException`/crash anywhere — consistent with the APK being the untouched, correctly-signed distributed artifact (the GMS FlagStore line independently shows the signing-cert SHA-256 `6e21…897`, §5). Whatever ended the processes, it was not the signature gate.

**6.5 What the user-visible "first-run UI" actually was.** Per the log, the screens reached were: launcher activity (no frame drawn) → LoginActivity first frame (23.067) → PairIP LicenseActivity (21.102–23.493) → Play Store Play-Pass paywall (foreground from 23.138, fully drawn 27.744). After 23.716 no Grindr UI existed at all; the later processes were background service/job restarts. **[inferred]:** on this device state, the app's first-run funnel terminates in the Play licensing/paywall surface, and the app process cycles (start → license round → exit) whenever anything re-launches it — which is exactly where observation was stopped per protocol. No Grindr account-creation UI was ever reached, and no account was created.

---

## 7. What this observation does NOT establish (limits)

1. **No verdict values.** The log shows licensing/integrity *round-trips*, not their payloads — the license response content, the integrity token verdict, and any `licenseCheckState` value are all invisible in logcat. §6.1's reading is sequencing-based inference.
2. **No VMRunner visibility.** Zero VMRunner lines (§3.3); the native VM's behavior (whether it ran, what it verified) is entirely dark in this capture — consistent with the dossier's description of the VM, but not evidence about it.
3. **chatty collapse.** Most app-origin lines were rate-limited away (§2.4), including — evidently — any SignatureCheck line from pid 7955 and any app-level license-error text. A longer or differently-filtered capture (e.g., `logcat -b all`, or per-buffer pulls) might retain more; that was not done in this run.
4. **42 seconds, one launch, one device state.** No re-launch after the Play-surface state, no licensed-account comparison run, no second device. Single-sample.
5. **Confounded environment, disclosed not controlled.** BlueStacks + permissive SELinux + LSPosed-on-image + Play account present (§2). This is what the pre-authorized observational follow-up had available; findings here should be read as "behavior on this BlueStacks instance," not "behavior on a stock licensed phone."
6. **I did not verify the device side this session.** Device interaction facts (deviceOk/installOk/logPulled, the 35 s wait, the pull command) come from the run record **[run]**; my session work was limited to reading `gp-first-run.log` and the local sample tree. The log's internal consistency (PACKAGE_ADDED → install → launch → three pids; final pid 8445 matching the run note) corroborates the record, but I ran no adb command myself.

---

## 8. Commands run this session (all against the pulled log; no device access)

Working directory: `pairip-research/`. Every count quoted above comes from these.

1. `wc -l samples/out/gp-first-run.log` → `2426`; `head -5` / `tail -5` → span `10-23 20:31:08.065` … `10-23 20:31:50.434` (first content line / last line `D/LicenseClient( 8445): Sending request to licensing service...`).
2. `grep -n -i -E "pairip|VMRunner|SignatureCheck|licens|integrity" samples/out/gp-first-run.log` → **44 lines** (line numbers L810…L2426; all quoted in §3).
3. `grep -c "FATAL" …` → `0`; `grep -c "FATAL EXCEPTION" …` → `0`.
4. `grep -c -i "vmrunner" …` → `0`; `grep -c -i "pairip" …` → `7`.
5. `grep -n -i -E "lsposed|xposed|magisk|substrate|frida" …` → 7 lines, all LSPosed-status notification noise from the system (L490, L491, L578, L579, L581, L583, L585); **no frida/xposed-acting-on-app lines**.
6. Process-lifecycle greps: `grep -n -E "Start proc|…died|System.exit called|exited cleanly|onWindowsDrawn" …` → the full pid 7955/8280/8445 timeline quoted in §4–§5, and exactly two `onWindowsDrawn` lines in the whole log (Grindr LoginActivity L1088; Play Store MainActivityPrivate L1823).
7. Directory listings: `samples/apk/splits/` (five APKs, §1) and `samples/out/` (log + census files), `ls -la` this session.
8. Cross-reference greps in `docs/01-pairip-dossier.md` (`SignatureCheck` → §3.2 at dossier line 111; `licensecheck`/`LicenseActivity`/silent-exit → §3.4 at dossier lines 121–128) for the attributions marked [inferred] in §3.2/§3.4/§6.1.
9. `sed -n '2027p;1973p' samples/out/gp-first-run.log | cat -A` → both lines byte-identical (`OperationException[Status{statusCode=Unable to generate a new integrity token., resolution=null}]`). *Correction record: an earlier draft of §3.5 mis-transcribed L2027 with a dropped `Status{` and carried a note falsely claiming the drop was in the source; caught and fixed during final verification. The eight lines are in fact identical apart from timestamps.*

---

*Evidence boundary: every quotation in this doc is a verbatim line of `pairip-research/samples/out/gp-first-run.log` (gitignored, local-only per ROE §4), cited by line number; every conclusion beyond a quotation is labeled [inferred]. The runtime facts (deviceOk/installOk/logPulled/process-8445) are from the run record supplied with the task. This doc produces no bypass artifact and initiates no interaction with Grindr infrastructure (ROE §1).*
