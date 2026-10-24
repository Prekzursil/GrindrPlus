# Tamper-Response Characterization — Probe Set P1/P2/P3 (ROE §5.2)

**Date:** 2026-10-24 (probes built and attempted this date; the one surviving probe log covers 10-24 06:40:24.375 → 06:40:54.490)
**Deliverable:** `docs/14` of the PairIP/GrindrPlus research program (charter in repo README; ROE in `ROE.md`). Authorized by `ROE.md` §5.2 (added 2026-10-24, user-approved "all 3 tiers").
**Question answered:** When copies of the acquired Grindr base APK are modified and/or re-signed locally and installed on the local emulator, what does the protection actually do — reject the install, crash at runtime, or behave silently?
**Method / evidence markers:** **[record]** marks a field of the probe-outcome record handed to this task verbatim. **[log L###]** marks a verbatim line of `pairip-research/samples/out/probe-P2.log` at that line number. **[verified]** marks a fact I established this session by running a command against local files (commands in §7). **[wf]** marks the workflow harness code that drove the probes (quoted from `.zcode/workflow-runs/dwfrun-eba7c598-195a-44cd-b6bc-bcdbc7581852.mjs`, Track F). **[inferred]** marks reasoning beyond what any artifact states. I had no device access this session; every runtime fact comes from the record or the pulled log.

---

## 0. Framing — verbatim from ROE §5.2

> **5.2 Tamper-response characterization (local, characterization-only).** On the local emulator only: modify copies of the acquired APK, test-sign them with a locally generated debug key, install, and *observe and record* what the protection does (installer rejection, runtime crash, silent behavior). Hard limits: no attempt is made to make a tampered build pass its checks or run past a failed check (no defeat development); tampered artifacts never leave `samples/`; nothing is distributed; no live Grindr infrastructure is contacted by these probes beyond the app's own normal startup traffic.

(`ROE.md` lines 62–68, quoted verbatim.) This doc is **characterization-only**: the tampered builds were observed failing, never assisted past a check; all probes remain local under `samples/` (gitignored — `.gitignore` line 2: `samples/`). No defeat development occurred at any step documented below.

---

## 1. The probe set — what was built, verified locally

Per the harness instructions **[wf]**, all three probes derive from `samples/apk/grindr-current-base.apk` (the pristine base APK of Grindr 26.21.0, versionCode 189896 — the same bundle statically characterized in `docs/02` and observed clean in `docs/07`):

| Probe | Definition (**[wf]**, verbatim) | Local verification **[verified]** |
|---|---|---|
| **P1 "unsigned-modified"** | "change one byte of a non-critical asset (e.g. append a byte to a small res file) and rezip; leave unsigned" — implemented by `samples/tools/build_probe_p1.py`, which appends `0x0A` after the IEND trailer of `res/drawable-hdpi-v4/mbridge_cm_tail.png` | `samples/apk/probes/P1.apk`: 73,384,788 B, 3,743 entries, **no** `META-INF/*.SF|RSA|EC|DSA` files → unsigned (v1 absent; the rezip necessarily drops the APK Signing Block, per the script's docstring — so v2/v3 absent too). Target PNG in P1 = 98 B ending `82 0a` vs. base 97 B ending `60 82` (byte `0a` after the IEND trailer, exactly as scripted) |
| **P2 "resigned-unmodified"** | "the untouched base.apk re-signed with a fresh local debug keystore" (uber-apk-signer; keystore `samples/tools/probe-debug.keystore`) | `samples/apk/probes/P2.apk`: 72,303,651 B, 3,745 entries = base + `META-INF/DEBUG.SF` + `META-INF/DEBUG.RSA` — i.e., content-identical to base plus a debug signature |
| **P3 "resigned-modified"** | "the P1 modification re-signed the same way" | `samples/apk/probes/P3.apk`: 73,704,483 B, 3,745 entries = P1's modified content + `DEBUG.SF`/`DEBUG.RSA` |

**Size anomaly, stated rather than explained [inferred]:** the one-byte content change cannot itself account for the ~1.0–1.7 MB of archive growth in the table — P1 = base +1,347,507 B; P3 = P1 +319,695 B; P2 = base +266,370 B (arithmetic on the sizes above). The growth is presumably repackaging overhead: `build_probe_p1.py`'s rezip evidently does not reproduce the original archive's compression/alignment (P1's +1.35 MB over base), and the uber-apk-signer re-sign pass adds a further ~0.27–0.32 MB (P2 over base; P3 over P1). Inferred from the deltas only — no re-packing experiment isolated the cause; the absolute sizes reflect build tooling, not probe semantics (the entry counts and signature-file inventory are the load-bearing verification columns).

Bundle-composition facts that matter for everything below **[verified]**:

- `samples/apk/grindr-current-base.apk` (72,037,281 B, identical size to `samples/apk/splits/base.apk` from the clean-run bundle) contains **zero entries under `lib/`** — no native libraries at all.
- `libpairipcore.so` exists **only** in the ABI splits of the distributed bundle: `lib/x86/libpairipcore.so` (697,616 B) in `split_config.x86.apk`, `lib/x86_64/libpairipcore.so` (624,184 B) in `split_config.x86_64.apk`, `lib/arm64-v8a/libpairipcore.so` (608,896 B) in `split_config.arm64_v8a.apk`.
- The harness installed each probe **base-APK-only**: the install command in the harness code is `adb -s 127.0.0.1:5555 install -r pairip-research/samples/apk/probes/${p}.apk` — no splits, no `install-multiple` **[wf]**. The clean baseline run of `docs/07` §1, by contrast, installed base **plus four splits**, and its DexPathList enumerated all five APKs with `nativeLibraryDirectories=[.../lib/x86, ...]` populated from the x86 split (`docs/07` [log L741]).

---

## 2. Recorded outcomes of this run's probe wave — none of the three probes reached a device

The outcome record handed to this task, verbatim **[record]**:

```json
[
  {"probe":"P1","installOk":false,"installTail":"adb.exe: device '127.0.0.1:5555' not found\r\n","processAlive":false,"logPulled":false,"note":""},
  {"probe":"P2","installOk":false,"installTail":"adb.exe: device '127.0.0.1:5555' not found\r\n","processAlive":false,"logPulled":false,"note":""},
  {"probe":"P3","installOk":false,"installTail":"adb.exe: device '127.0.0.1:5555' not found\r\n","processAlive":false,"logPulled":false,"note":""}
]
```

What this is, precisely: every install failed at the **adb transport layer** — `adb.exe: device '127.0.0.1:5555' not found` means adb had no connection to the emulator at that serial (the BlueStacks instance used for `docs/07` and the earlier probe wave was no longer attached). The command never reached a device, so **PackageManager was never asked to verify or reject any of the three probes in this wave** — the failure signature is an adb client error, not an installer verdict. Because the harness only launches, waits, and pulls a log after a successful install **[wf]**, there was also: no launch, no process to check (`processAlive: false` by construction), and **no log pulled for any probe in this wave** (`logPulled: false`, all three).

**P1 and P3: no logs exist, anywhere.** `find . -name "probe-*.log"` over the whole repo (`.git` pruned) returns exactly one file — `samples/out/probe-P2.log` **[verified]**. There is no `probe-P1.log` and no `probe-P3.log`. Nothing more can be recorded for P1 and P3 than: *never installed in this wave (device not found), no log artifact exists from any wave.*

---

## 3. The one surviving probe artifact — `samples/out/probe-P2.log`

### 3.1 Provenance and a discrepancy, stated plainly

The record says P2's log was not pulled (`logPulled: false`), yet `samples/out/probe-P2.log` exists on disk (84,701 B, 643 lines). The filesystem timeline explains it **[verified]**:

| Artifact | Host mtime |
|---|---|
| `samples/tools/build_probe_p1.py` | 06:21:40 |
| `samples/out/probe-P2.log` (content spans 06:40:24 → 06:40:54, emulator clock) | 06:40:40 |
| earlier workflow run `dwfrun-41c6536d-…mjs` (same probe definitions and procedure in its Track F) | 06:50:07 |
| current run `dwfrun-eba7c598-…mjs` | 06:54:39 |
| `samples/apk/probes/P1.apk` / `P2.apk` / `P3.apk` (rebuilt by this run's prep step) | 07:11:41 / 07:12:30 / 07:12:32 |

So the log was produced by an **earlier wave of the same automated probe loop, ~31 minutes before the current on-disk probe APKs were rebuilt**; the emulator was still up at 06:40 and gone by this wave. The earlier wave's P2.apk was overwritten at 07:12:30, so **the exact bytes that produced this log cannot be verified against the current `P2.apk`** — that provenance link is lost, and this doc does not claim it. What ties the log to a P2-type probe nonetheless — with the attribution's basis stated precisely: the quoted log lines establish a **base-only install of Grindr 26.21.0 (versionCode 189896)** and nothing further about the artifact (`source: user`, base-only DexPathList); they do **not** establish the signing key or an unmodified content state — a P3-type (modified + re-signed) install would produce identical lines. The debug-signed, otherwise-unmodified characterization therefore rests on the artifact filename and harness chronology (the file is `probe-P2.log` from the earlier wave of the same probe loop, whose P2 definition is quoted in §1), not on log content; and the log's internal timing matches the harness procedure (logcat cleared just before install; monkey launch at 06:40:28.642; final line at 06:40:54.490 ≈ launch + 25 s sleep + pull, per the harness's `time.sleep(25)` and `logcat -d -v time` pull **[wf]**). The run also occurred on a **different emulator boot** than `docs/07` (system_server pid 2147 here vs 2215 there; zygote 1910/1911 vs 1904).

### 3.2 The run, quoted verbatim

**Install (base-only, fresh).**

```text
L50: 10-24 06:40:26.368 D/BstCommandProcessor-PackageIntentReceiver( 2514): pkg is: com.grindrapp.android event is android.intent.action.PACKAGE_ADDED
L67: 10-24 06:40:26.801 D/BstCommandProcessor-CommandHandler( 2514): calling native onAppInstalled function, pkgName: com.grindrapp.android activity: com.grindrapp.android.HomeActivityOriginal appLabel: Grindr, versionCode: 189896, versionName: 26.21.0 iconFileName: com.grindrapp.android.png, source: user, isUpdate: false, isHomeApp: false, orientation:
L71: 10-24 06:40:26.813 I/HCALL   ( 2147): hcallOnAppInstalledRpc({"pkg":"com.grindrapp.android",...,"versionCode":189896,"versionName":"26.21.0",...,"source":"user","isUpdate":false,...})
```

**Launch via monkey (uid 2000), one process, pid 7063.**

```text
L284: 10-24 06:40:28.642 W/Monkey  ( 6969): args: [-p, com.grindrapp.android, -c, android.intent.category.LAUNCHER, 1]
L309: 10-24 06:40:28.831 I/ActivityManager( 2147): START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.grindrapp.android/.HomeActivityOriginal} from uid 2000
L349: 10-24 06:40:29.418 I/ActivityManager( 2147): Start proc 7063:com.grindrapp.android/u0a80 for activity com.grindrapp.android/.HomeActivityOriginal
```

**The failure — immediate FATAL, full stack, ~0.85 s after process start.** (The crash-buffer marker `--------- beginning of crash` is at L383.)

```text
L384: 10-24 06:40:30.271 E/AndroidRuntime( 7063): FATAL EXCEPTION: main
L385: 10-24 06:40:30.271 E/AndroidRuntime( 7063): Process: com.grindrapp.android, PID: 7063
L386: 10-24 06:40:30.271 E/AndroidRuntime( 7063): java.lang.UnsatisfiedLinkError: dalvik.system.PathClassLoader[DexPathList[[zip file "/system/framework/org.apache.http.legacy.boot.jar", zip file "/data/app/com.grindrapp.android--voKbRP_yn2bmMW8zQV-Qw==/base.apk"],nativeLibraryDirectories=[/data/app/com.grindrapp.android--voKbRP_yn2bmMW8zQV-Qw==/lib/x86_64, /system/lib64, /system/vendor/lib64]]] couldn't find "libpairipcore.so"
L387: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at java.lang.Runtime.loadLibrary0(Runtime.java:1032)
L388: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at java.lang.System.loadLibrary(System.java:1669)
L389: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at com.pairip.VMRunner.<clinit>(VMRunner.java:33)
L390: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at com.pairip.VMRunner.invoke(VMRunner.java:56)
L391: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at com.pairip.StartupLauncher.launch(StartupLauncher.java:14)
L392: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at androidx.core.app.CoreComponentFactory.<clinit>(Unknown Source:0)
L393: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at java.lang.Class.newInstance(Native Method)
L394: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.LoadedApk.createAppFactory(LoadedApk.java:227)
L395: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.LoadedApk.createOrUpdateClassLoaderLocked(LoadedApk.java:731)
L396: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.LoadedApk.getClassLoader(LoadedApk.java:810)
L397: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.LoadedApk.getResources(LoadedApk.java:1032)
L398: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.ContextImpl.createAppContext(ContextImpl.java:2354)
L399: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.ActivityThread.handleBindApplication(ActivityThread.java:5850)
L400: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.ActivityThread.access$1100(ActivityThread.java:204)
L401: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.ActivityThread$H.handleMessage(ActivityThread.java:1717)
L402: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.os.Handler.dispatchMessage(Handler.java:106)
L403: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.os.Looper.loop(Looper.java:193)
L404: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at android.app.ActivityThread.main(ActivityThread.java:6846)
L405: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at java.lang.reflect.Method.invoke(Native Method)
L406: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:518)
L407: 10-24 06:40:30.271 E/AndroidRuntime( 7063): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:858)
```

*(Correction record: an earlier draft of this section mis-transcribed L393's pid as `7066`; re-checked against the file (`sed -n '393p'` → `E/AndroidRuntime( 7063)`), all 24 lines of the block print pid 7063. Caught and fixed during final verification.)*

**Aftermath — system tears the launch down.**

```text
L412: 10-24 06:40:30.281 W/WindowManager( 2147): Force clearing freeze: AppWindowToken{d265ba token=Token{24586e5 ActivityRecord{63715dc u0 com.grindrapp.android/.HomeActivityOriginal t514}}}
L420: 10-24 06:40:30.390 W/ActivityManager( 2147):   Force finishing activity com.grindrapp.android/.HomeActivityOriginal
L440: 10-24 06:40:30.897 W/ActivityManager( 2147): Activity pause timeout for ActivityRecord{63715dc u0 com.grindrapp.android/.HomeActivityOriginal t514 f}
L465: 10-24 06:40:31.388 E/BufferQueueProducer( 1935): [Splash Screen com.grindrapp.android#0] queueBuffer: BufferQueue has been abandoned
```

**Negative results, all [verified] by grep over the full 643-line log:**

- `SignatureCheck` → **0 lines.** `licens*` (any case) → **0 lines.** `integrity` → **0 lines.** `VMRunner` → 2 lines (L389–L390, inside the FATAL stack). `pairip` → 4 lines (L386, L389, L390, L391 — all inside the FATAL stack). `FATAL` → 1.
- Exactly **one** `com.grindrapp.android` process ever started (L349); no second `Start proc` for the package anywhere in the window — no service restarts, no retry cycle.
- No explicit "Process … has died" line for pid 7063 was captured (the only `exited due to signal` lines in the log are unrelated pids 3130/3098/4280/6134 of other apps); the death path is instead shown by the FATAL dump itself plus L420/L440.

### 3.3 Did the process survive, and what would the user see?

- **Survived: no.** FATAL on the main thread at 06:40:30.271, 0.853 s after `Start proc` (L349 → L384). Nothing from the package appears in the log after 06:40:31.4. The harness's post-sleep `pidof` (~06:40:53) would necessarily have returned empty — the process had been gone for ~23 s.
- **User-visible result [inferred from the quoted system lines]:** tapping the app icon shows at most the splash-screen window (L465 shows a splash-surface that is immediately abandoned), then the launch is force-finished (L420) — on this Android 9-era build the standard manifestation of a main-thread FATAL during bind is the system crash dialog ("Unfortunately, Grindr has stopped" / "App keeps stopping" style) and return to the launcher. The dialog text itself is not printed in logcat; its occurrence is inferred from the FATAL + force-finish lines, not observed verbatim.

---

## 4. What the P2 crash is — and what it is not

**Attribution, carefully bounded:**

- **Fact [log]:** the crash site is the earliest possible app entry point — `com.pairip.StartupLauncher.launch` → `com.pairip.VMRunner.invoke` → `VMRunner.<clinit>` line 33, a `System.loadLibrary("pairipcore")` that fails because the classloader's native-library search path (the app's own `lib/x86_64` dir plus system/vendor dirs, L386) does not contain `libpairipcore.so`. The stack runs through `androidx.core.app.CoreComponentFactory.<clinit>` during `ActivityThread.handleBindApplication` — i.e., **before the Application class is created, before any Activity, before any Java-level PairIP gate can run.**
- **Fact [log L386 + verified]:** the DexPathList contains **only** `base.apk` — no splits — and §1 established that the base APK ships **zero** native libraries while `libpairipcore.so` lives exclusively in the ABI splits. The probe harness installed base-only by design **[wf]**.
- **Therefore [inferred]:** this FATAL is **fully explained by the probe bundle's composition** — the native library PairIP's Java bootstrap hard-requires was never placed on the device — and must **not** be read as the protection detecting the re-sign and killing the app. The re-sign-sensitive and tamper-sensitive layers characterized in `docs/01` and observed in `docs/07` (the `SignatureCheck` tag; `com.pairip.licensecheck`) all sit *later* in startup than this crash; they were never reached, which is exactly what the zero SignatureCheck/license/integrity lines show.
- **Limit [stated, not papered over]:** the clean control for this claim — installing the *untouched, correctly-signed* base.apk alone, without splits, and observing the same crash — was **not run** (the emulator was gone by the time this doc was written). "A pristine base-only install would crash identically" is composition-based inference (same loader, same missing library, same entry point), not an observed run. What is observed-and-verified stands regardless: on this probe, the failure was a missing-library crash, not a protection response.

---

## 5. Comparison against the clean first-run baseline (`docs/07`)

| Aspect | Clean run (`docs/07`, base + 4 splits) | Probe P2 run (earlier wave, base-only; P2-type attribution per §3.1 — filename + harness chronology, not log content) |
|---|---|---|
| Installed bundle | base.apk + 4 splits; DexPathList enumerates all five APKs; native libs from x86 split (`docs/07` [log L741]) | base.apk only; DexPathList = single base.apk entry [log L386] |
| Launcher | `HomeActivityOriginal` via monkey (`docs/07` [log L412]) | Same activity, same launch path [log L309] |
| First PairIP-attributable event | `com.pairip.licensecheck.LicenseActivity` started at ~8.4 s after process start (`docs/07` [log L1026]); `com.pairip.application.Application` observed as the running Application class (`docs/07` [log L1946]) | `java.lang.UnsatisfiedLinkError … couldn't find "libpairipcore.so"` at `com.pairip.VMRunner.<clinit>(VMRunner.java:33)` at **0.85 s** after process start [log L386, L389] — before Application creation |
| `SignatureCheck` | `Signature check ok`, once per process, ~0.3–0.4 s after `Start proc` (`docs/07` [log L1171, L2127]) | **0 lines** — the gate was never reached (crash precedes it) |
| Licensing flow | Full `LicenseClient` connect→send rounds; LicenseActivity foregrounded then finished (`docs/07` §3.4, [log L810–L936]) | **0 licens\* lines of any kind** |
| Play Integrity | One token request round-trip; 8× GMS-side token-generation failures (`docs/07` §3.5) | **0 integrity lines** |
| Process end | Deliberate `System.exit called, status: 0`, clean Zygote exits, **no FATAL anywhere** (`docs/07` §4) | `FATAL EXCEPTION: main`, hard crash, activity force-finished [log L384, L420] |
| User-visible | LoginActivity frame → PairIP LicenseActivity → Play Store paywall surface; app cycles start→license-round→exit (`docs/07` §6.5) | Splash at most, then immediate crash-death at every launch (§3.3) |

The two runs share nothing beyond the package name and launcher entry: the clean bundle's protection stack ran to its silent-exit licensing path; the base-only probe died in the classloader before any of that stack executed.

---

## 6. What this track did — and did not — establish

**Established (observed/verified):**

1. All three probes of the final wave failed **before reaching any device** — adb transport error, verbatim in §2. P1 and P3 have no logs from any wave; nothing about their on-device behavior is known.
2. One completed probe run exists (earlier wave; log content establishes a base-only install of Grindr 26.21.0, versionCode 189896 [log L67, L386]; its P2-type — debug-signed, unmodified — attribution rests on the artifact filename and harness chronology, not on log content, §3.1): it **installed cleanly** (no installer rejection — `isUpdate: false`, `source: user` [log L67]) and then **crashed immediately and fatally at every launch** with the missing-`libpairipcore.so` signature quoted in §3.2.
3. The observed crash is a **packaging-composition artifact** (base APK carries no native libs; the harness installed base-only), not an observed defensive response to the re-sign — the tamper-sensitive gates were never reached (§4).

**NOT established — no observation exists for any of these:**

- **P1's installer verdict.** An unsigned APK would predictably be rejected by PackageManager (no signatures to verify), but that is expectation, not observation: in the final wave P1 never reached a device, and the earlier wave left no `probe-P1.log` (its P1 outcome — installed-and-logged or rejected-at-install — is unknown). No PackageManager/installer rejection line was ever captured for any probe.
- **P3's behavior** — never observed at all.
- **Any `SignatureCheck` failure verdict, `SignatureTamperedException`, license-check response, or integrity-verdict response to a modified or re-signed build.** The only PairIP behavior actually observed across this program's probes is the startup hard-dependency on `libpairipcore.so` from the splits — a structural fact, not a defense response.
- **Byte-identity of the logged run's APK with the current `P2.apk`** (probes were rebuilt ~31 min after the log; §3.1).

---

## 7. Commands run this session (all against local files; no device access)

Working directory: `pairip-research/`. Every **[verified]** fact above comes from one of these.

1. `ls`/`find` over `samples/`, `samples/apk/probes/`, `samples/apk/baseline/`, `samples/out/`, `docs/`, `.zcode/workflow-runs/`; `find . -path ./.git -prune -o -name "probe-*.log" -print` → exactly one hit, `samples/out/probe-P2.log`.
2. `wc -l samples/out/probe-P2.log` → 643; `head -5`/`tail -5` → span `10-24 06:40:24.375` … `10-24 06:40:54.490`.
3. `grep -c -i` over the log for `SignatureCheck` → 0, `licens` → 0, `license` → 0, `integrity` → 0, `VMRunner` → 2, `pairip` → 4, `FATAL` → 1; `grep -n "beginning of crash"` → L383.
4. `grep -n` for `grindr|PACKAGE_ADDED|onAppInstalled|versionCode|Start proc|Force|pidof|has died|died:|exited|killed` → the lifecycle lines quoted in §3.2 (one `Start proc` for the package; none of the `exited` lines belong to pid 7063).
5. `sed -n '375,412p'` and `sed -n '418,422p;463,467p'` → the verbatim FATAL block and aftermath lines.
6. `unzip -l` over `samples/apk/grindr-current-base.apk`, `samples/apk/splits/*.apk`, `samples/apk/probes/P{1,2,3}.apk`, plus `grep -c "lib/"` on base → 0; `libpairipcore.so` located only in the three ABI splits (sizes in §1).
7. Python/zipfile entry counts and signature-file inventories for base and P1/P2/P3; byte check of `res/drawable-hdpi-v4/mbridge_cm_tail.png` in P1 (98 B, ends `82 0a`) vs base (97 B, ends `60 82`).
8. `stat` of `probe-P2.log`, `P1/P2/P3.apk`, `build_probe_p1.py`, and the workflow-run scripts → the §3.1 timeline; `cmp` of the earlier vs current run script → differ in bytes, but both contain the identical probe definitions and the identical per-probe adb loop (verified by grep of both files).
9. `grep -n -A7 "5.2" ROE.md` → the verbatim §0 quote; `cat .gitignore` → `samples/` ignored (line 2).

---

*Evidence boundary: every runtime quotation is a verbatim line of `pairip-research/samples/out/probe-P2.log` (local-only, gitignored per ROE §4) cited by line number; the final wave's outcomes are the [record] fields supplied with this task; every local claim was verified by the §7 commands. Nothing in this doc assisted a tampered build past any check: the one observed probe failed on its own, and the other two never reached a device. All probe artifacts remain under `samples/`.*
