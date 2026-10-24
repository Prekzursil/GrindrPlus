# Native Inventory — `libpairipcore.so` Across the Three ABI Splits (Grindr 26.21.0)

**Date:** 2026-10-24
**Deliverable:** `docs/10` of the PairIP/GrindrPlus research program (charter in repo `README.md`; ROE in `ROE.md`). Extends the `docs/00`–`docs/08` series; opens the native-binary side that `docs/05` deliberately left at hashes-and-sizes.
**Question answered:** What does the shipped PairIP VM runtime (`libpairipcore.so`, all three ABIs) look like structurally (size, ELF identity, symbol surface, sections, telltale strings), what is its cross-ABI stable surface, and has the shipped VM drifted from the two public research baselines in `samples/pairipcore` and `samples/pairipcore-vm` (entry points, JNI exports, handler structure)?
**Method:** live runs this session of the pyelftools inventory script `samples/tools/so_inventory.py` against the three `.so` files in `samples/out/so/`, plus one supplementary pyelftools pass (full import-name diff) and one raw-bytes pass (DEX string scan, `.text` string localization). Research comparison is a close read of `samples/pairipcore/README.md`, `samples/pairipcore-vm/README.md` and `samples/pairipcore-vm/docs/source/{introduction,cfg,instructions}.md`, cited by line. Every claim is **[measured]** (produced by a command recorded in §6 this session) or **[sourced]** (cited to a repo file read this session).

---

## 1. Artifacts under test

The three native libraries extracted to `samples/out/so/`, byte-verified this session against their APK members (Python `zipfile` + `hashlib`; all three reported `MATCH`):

| File | Size (bytes) | SHA-256 | Source APK member |
|---|---|---|---|
| `samples/out/so/libpairipcore-arm64_v8a.so` | 608,896 | `b20ee5bca05328b794744ab082c758ec2e0d298c5447e1a6415094ecc6987589` | `split_config.arm64_v8a.apk!lib/arm64-v8a/libpairipcore.so` |
| `samples/out/so/libpairipcore-x86_64.so` | 624,184 | `a9c54f7a2e2a92d385354415bd46b2935904fb9235226a62864db6ea418fbba6` | `split_config.x86_64.apk!lib/x86_64/libpairipcore.so` |
| `samples/out/so/libpairipcore-x86.so` | 697,616 | `46b814fb40c6e8b036c0a66eda72d6cac164434f40520e7a42c2a2c06bee76cc` | `split_config.x86.apk!lib/x86/libpairipcore.so` |

**[measured]** The hashes match `docs/05-splits-census.md:41-43` exactly, so this doc analyzes the same binaries that census recorded.

> Provenance note: an earlier harness record of the same three inventory runs was supplied with this task; its JSON shows `exitCode: 0` and field-for-field identical values to the live runs below. Per instruction, everything in this doc comes from the **live** re-runs recorded in §6, not from that record.

## 2. Per-ABI inventory **[measured]**

All values from `samples/out/so/inventory-<abi>.json`, written by the §6 commands.

| Property | arm64_v8a | x86_64 | x86 |
|---|---|---|---|
| File size | 608,896 B | 624,184 B | 697,616 B |
| ELF class / data | ELFCLASS64 / LSB | ELFCLASS64 / LSB | ELFCLASS32 / LSB |
| Machine | EM_AARCH64 | EM_X86_64 | EM_386 |
| **Soname** | `libpairipcore.so` | `libpairipcore.so` | `libpairipcore.so` |
| Dynsym exported | 3 | 3 | 3 |
| Dynsym imported | 71 | 69 | 70 |
| Dynsym unnamed | 1 | 1 | 1 |
| Exported, non-std prefix | `ExecuteProgram`, `JNI_OnLoad`, `JNI_OnUnload` | same | same |
| Sections | 25 | 25 | 25 |
| `.text` size | 485,864 | 496,930 | 610,586 |
| `.rodata` size | 18,056 | 22,880 | 22,564 |
| `.init_array` size | 56 | 40 | 20 |
| Relocations | `.rela.dyn` 42,600 + `.rela.plt` 1,656 | `.rela.dyn` 39,360 + `.rela.plt` 1,608 | `.rel.dyn` 13,432 + `.rel.plt` 544 (REL, 32-bit) |
| Keyword-string matches | 9 | 10 | 10 |

Notes: `.init_array` 56/40/20 bytes at pointer widths 8/8/4 works out to 7/5/5 constructors respectively (arithmetic on measured section sizes, not a disassembly). All three carry a custom section `__lcxx_override` (200/156/237 B) — a section name that appears nowhere in either research repo (grep over `samples/pairipcore*` returned nothing).

## 3. Cross-ABI comparison — the stable surface **[measured]**

**Exports are identical on all three ABIs** — the entire exported surface is three symbols: `ExecuteProgram`, `JNI_OnLoad`, `JNI_OnUnload`. No `Java_*` symbol is exported on any ABI.

**Imports: 69 symbols common to all three** (supplementary pass, §6b, output `samples/out/so/imports-by-abi.json`). Per-ABI extras:

| ABI | Extra imports beyond the common 69 |
|---|---|
| arm64_v8a | `__system_property_get`, `strncmp` |
| x86_64 | — (exactly the common set) |
| x86 | `ceilf` |

The common import set includes `dlopen`/`dlsym`/`dlclose`/`dlerror`/`dl_iterate_phdr`, a bare `syscall`, `__system_property_read`/`__system_property_foreach`, `opendir`/`readdir`/`closedir`, `android_set_abort_message`, `getauxval`, full pthread set, and libc++abi machinery (`__cxa_atexit`, `__cxa_finalize`, `__register_atfork`). Notably **absent** as imports: `prctl`, `ptrace`, `openat`, `read`, `lseek` — the syscall surface those imply is reached some other way (see §4 drift discussion).

**String-level drift (keyword matches, `/pairip|VM|license|integrity|dex|apk/i`):** the nine common matches on every ABI are the soname, five `out/llvm-project/libcxxabi/src/...` paths (`private_typeinfo.cpp`, `demangle/Utility.h`, `demangle/ItaniumDemangle.h`, `fallback_malloc.cpp`, `cxa_demangle.cpp`), the libunwind diagnostic `DW_OP_pick index out of bounds`, and two Itanium-demangler type names (`N12_GLOBAL__N_1...`) — 1+5+1+2 = 9, matching the §2 per-ABI counts of 9/10/10; the tenth match on each x86-family ABI is the `APK`-matching fragment discussed below. Together with `__lcxx_override` these indicate a statically linked LLVM libc++abi/unwind payload — no pairip-specific strings beyond the soname survive in plain ASCII. The two x86-family-only matches are `APK Sig H9` (x86_64) and `APK 1` (x86); a localization pass (§6c) places both **inside `.text`**, not `.rodata`, and both are ≤8 printable bytes — consistent with coincidental immediate bytes inside instruction streams rather than stored string constants. Reported as measured; interpretation is that caveat only. No `license`/`integrity`/`pairip` keyword matches beyond the soname on any ABI.

## 4. Drift vs the public research baselines

### 4.1 What the two research repos document

**Baseline A — `samples/pairipcore/README.md` (Solaree, 2024):**
- Java side: `VMRunner` declares `public static native Object executeVM(byte[] vmCode, Object[] args);` and loads the library via `System.loadLibrary("pairipcore")` (`samples/pairipcore/README.md:98-102`, `:136-146`).
- The native library's **symbols are stripped** — `executeVM` has no export; it is located by hooking `RegisterNatives` at runtime, resolving to `libpairipcore.so!0x560c8` in that era (`README.md:147`, Frida script `:148-194`, output `:196`).
- The library "fixes up functions and changes offset in runtime (probably code decryption too)" (`README.md:209`).
- Handler structure: `protections_main` — a giant switch over ~78 opcode ids (0–137) whose cases are security checks and obfuscated stubs: anti-debugger (case 49), `openat`/`read`/`lseek`/`fstat`/`fstatfs` handlers, `dlopen_libc`/`dlsym`/`dlclose` cases, `getdents64`, `clock_gettime`, `unknown_syscall` (`README.md:219-528`).
- Anti-debug via raw syscalls `prctl`/`clone`/`waitpid`/`ptrace` (`README.md:542-616`); device-property sweep via `dlopen`-resolved `__system_property_read_callback` plus `access`/`opendir`/`readdir`/`__system_property_read` (`README.md:626-656`); a frida-server check (`README.md:658`); `dlopen`/`dlsym`/`dlclose` and `syscall`/`SVC 0` named as core techniques (`README.md:14`).

**Baseline B — `samples/pairipcore-vm` (Matrixeditor, 2025):**
- Same Java-side declaration (`docs/source/introduction.md:8-18`).
- "By examining the exports of the native library, we observe that no native function starting with `Java_` is defined … linked statically via `JNIEnv->RegisterNatives`" (`introduction.md:44-47`); registration happens at the end of **`JNI_OnLoad`** with exactly **one** `JNINativeMethod` (name, signature, `fnPtr`), `RegisterNatives(..., &local_80, 1)` (`introduction.md:49-63`).
- Handler structure: `executeVM` delegates to a main dispatcher (FDE loop) over a `VMContext {ptrTable, vmCode, vmCodeLength, pc}` (`docs/source/cfg.md:20-32` and the component list at `cfg.md:1-19`); opcodes are obfuscated (`pairipcore/opcode.py:1-23`, `decode_opcode_v0/v1`) and the **opcode→handler mapping is randomized at every library compile**, so handlers are keyed by stable *format IDs* instead (`docs/source/instructions.md:170-190`, table builder `pairipcore/cfg.py:268-278`).
- Deployment: VM bytecode as `assets/data.vmcode`-style files with a per-file XOR key and 30 format IDs (`samples/pairipcore-vm/README.md:17-47`); "Google designed the VM to be custom for every release of an application" (`README.md:8-10`).

### 4.2 Shipped 26.21.0 vs those baselines

| Documented surface | Baseline says | Shipped (measured) | Verdict |
|---|---|---|---|
| `executeVM` Java native method | Both repos (`pairipcore/README.md:98`; `introduction.md:16`) | Still present DEX-side: `executeVM` byte-string found in `classes2.dex` (only dex of 13 containing it, §6d); census records `com.pairip.VMRunner` + 20 stub methods invoking `VMRunner;->invoke or ->executeVM` (`samples/out/census-base-named.json`, `dexStats.stubMethods=20`, `notes[0]`) | **Unchanged** |
| No `Java_*` dynsym exports | `introduction.md:44-47` | No `Java_*` export on any ABI (§3) | **Unchanged** |
| `JNI_OnLoad` registers the VM entry | `introduction.md:49-63` | `JNI_OnLoad` is exported on all three ABIs | **Consistent** (export presence matches its documented role) |
| `JNI_OnUnload` | Documented by **neither** repo | Exported on all three ABIs | **Added export** (undocumented lifecycle hook) |
| Named non-JNI entry export (`ExecuteProgram`) | Neither repo documents any named VM entry; Baseline A stresses symbols are stripped and the entry must be found dynamically (`pairipcore/README.md:147,209`) | `ExecuteProgram` exported by name on **all three** ABIs | **Added export — headline drift** (see below) |
| `assets/*.vmcode` bytecode files | Baseline B's core artifact (`pairipcore-vm/README.md:17-47`) | Census measures `vmcodeAssets: []` for the base APK (`census-base-named.json`); bundle-wide, no `.vmcode`-named asset in the base or any split — base 647 `assets/` entries / zero `.vmcode`, splits no assets at all (`docs/05:175`); a `com.pairip.VmDecryptor` class exists in the DEX (`pairipClasses`) | **Deployment drift** (bytecode carried some other way) |
| `dlopen`/`dlsym`/`dlclose`/`syscall` runtime imports | `pairipcore/README.md:14,626-627` | Imported on all three ABIs (§3) | **Corroborated** |
| Anti-debug via raw `prctl`/`ptrace` syscalls, not PLT | `pairipcore/README.md:15,542-616` | `prctl`/`ptrace`/`openat`/`read` absent from imports while bare `syscall` is imported (§3) | **Consistent, not corroborated** — import absence is non-contradiction: it leaves the documented raw-syscall style possible (syscall-number dispatch, no PLT entries), but does not verify that the shipped library actually performs anti-debug that way (no disassembly or dynamic evidence at inventory depth) |
| Property sweep functions | `__system_property_read_callback` via dlsym (`README.md:627,632`) | `__system_property_read` + `__system_property_foreach` imported on all ABIs; `__system_property_get` **arm64-only** | **Minor drift** (different property API mix; one ABI-specific addition) |
| Randomized opcode→handler mapping per release | `instructions.md:176-181`; `pairipcore-vm/README.md:8-10` | Not statically decidable at inventory depth (needs the disassembly stage Baseline B describes) | **Open** (§5) |

**Drift verdict.** Nothing documented is *missing*: the documented entry chain (Java `executeVM` → `RegisterNatives` inside `JNI_OnLoad` → stripped internal dispatcher) still has all its observable parts in place, and the import profile corroborates the documented runtime architecture. The drift is **additive on the export surface**: the shipped library exports two symbols the research does not document — `JNI_OnUnload` and, more significantly, **`ExecuteProgram`**, a *named* VM-family entry point on every ABI. In the 2024 baseline the equivalent function had to be recovered dynamically precisely because no such name existed (`pairipcore/README.md:147`). Statically, this inventory cannot prove what `ExecuteProgram` is (the renamed current `executeVM` implementation, a second entry, or an unrelated routine) — dynsym gives the name, not the body; resolving that needs the disassembly/CFG stage Baseline B used (`cfg.md:20-32`) or a `RegisterNatives` observation like Baseline A's (`README.md:148-196`), both out of scope here and recorded as open questions.

## 5. What the native layer could theoretically host that the DEX census cannot see

Descriptive scope only (what a DEX-level census is structurally blind to; no bypass is discussed):

- **The VM interpreter itself.** The census sees *that* 20 methods invoke `VMRunner;->invoke or ->executeVM` (`census-base-named.json: dexStats.stubMethods`); the executed logic — dispatcher, obfuscated opcode decode (`pairipcore/opcode.py:1-23`), per-release randomized handler table (`instructions.md:176-181`) — is ~0.5 MB of `.text` per ABI (§2) that never appears as Dalvik bytecode.
- **Environment and integrity probes.** Baseline A documents `/proc/self/maps`+`status` scanning, device-property sweeps, directory checks and a frida-server check implemented over raw `syscall` numbers (`pairipcore/README.md:15-18,542-658`). The shipped import profile (bare `syscall`, no `prctl`/`ptrace`/`openat` PLT entries, §3) leaves exactly that style possible; none of it is visible in DEX.
- **Self-modifying / self-decrypting code.** Baseline A describes runtime fixups and probable code decryption (`README.md:209`); a DEX census reads declared code, not runtime-mutated native images.
- **Native-resident secrets and keys.** Baseline B shows per-file XOR keys inside `data.vmcode` (`pairipcore-vm/README.md:23-47`); key material or native-only constants in `.data`/`.rodata` (or generated at runtime) are invisible to DEX tooling. Related: the shipped bundle carries no `.vmcode` assets at all (§4.2), so whatever carries the bytecode now, the DEX census's `vmcodeAssets` probe measures `[]` — the carrying mechanism itself is a native-side question.
- **Anti-tamper reactions.** `android_set_abort_message` and `abort` in the import set (§3) are consistent with native-side terminate-on-check-failure paths; the census can only see a crash afterwards, not the check.

## 6. Run record (this session; commands run from `pairip-research/samples/`)

1. **Byte verification** — Python `zipfile`+`hashlib` compare of each on-disk `.so` against its APK member: all three `MATCH` (hashes in §1).
2. **Inventory runs (the doc's primary data)** —
   `python tools/so_inventory.py out/so/libpairipcore-arm64_v8a.so > out/so/inventory-arm64_v8a.json` (exit 0),
   same for `-x86_64.so` → `inventory-x86_64.json` (exit 0),
   same for `-x86.so` → `inventory-x86.json` (exit 0). All three stderr streams empty; JSON parses in all three cases. Values transcribed in §2.
3. **Supplementary import diff** — pyelftools pass over the three files dumping all UNDEF dynsym names → `out/so/imports-by-abi.json` (§3); `dlopen`-family/prctl-absence table from the same file.
4. **String localization + DEX scan** — raw-byte search for `APK Sig`/`APK 1` with offset→section mapping via section headers (`x86_64: .text @ file-off 202373`; `x86: .text @ 197602`; arm64: none); `zipfile` scan of the 13 dex files in `grindr-current-base.apk` for `executeVM` → `classes2.dex` only.

**Limitations.** No disassembly, decompilation, or dynamic execution was performed — symbol-level and byte-level facts only; §4's open cell (what `ExecuteProgram` is; whether the handler table follows Baseline B's format-ID scheme in this build) requires the deeper stages cited there. The `.text`-resident `APK`-matching fragments are reported with the coincidence caveat stated in §3. `docs/09` does not exist at writing time; this doc is numbered `10` per its tasking.
