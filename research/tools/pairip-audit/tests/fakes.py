"""Fake androguard-shaped objects and synthetic-zip builders for the tests.

No real APK is needed anywhere: dex contents are described as blueprints and
instantiated as fakes; the APK side reads a synthetic zip built with stdlib
``zipfile``.
"""

from __future__ import annotations

import zipfile
from typing import Iterable, List, Optional


# --- instruction / method / class / dex fakes -------------------------------


class FakeInsn:
    """Quacks like androguard's Instruction (get_name/get_output)."""

    def __init__(self, name: str, output: str):
        self._name = name
        self._output = output

    def get_name(self) -> str:
        return self._name

    def get_output(self) -> str:
        return self._output


class BrokenInsn:
    """An instruction whose accessors raise (must be skipped, not fatal)."""

    def get_name(self):
        raise RuntimeError("boom-name")

    def get_output(self):
        raise RuntimeError("boom-output")


class RaisingIterator:
    """Iterator that yields one instruction, then raises (broken disassembly)."""

    def __init__(self, first):
        self._first = first
        self._done = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self._done:
            self._done = True
            return self._first
        raise ValueError("disassembly failed mid-stream")


class FakeBC:
    def __init__(self, instructions: Optional[Iterable]):
        self._instructions = instructions

    def get_instructions(self):
        if self._instructions is None:
            return []
        if isinstance(self._instructions, (list, tuple)):
            return list(self._instructions)
        return self._instructions  # generator-like: pass through


class FakeCode:
    def __init__(self, instructions: Optional[Iterable]):
        self._instructions = instructions

    def get_bc(self) -> FakeBC:
        return FakeBC(self._instructions)


class FakeMethod:
    """Quacks like androguard's EncodedMethod."""

    def __init__(
        self,
        name: str,
        class_name: str,
        instructions: Optional[Iterable] = None,
        descriptor: str = "()V",
        access_flags: int = 0x0009,  # public static
        code_error: Optional[Exception] = None,
    ):
        self._name = name
        self._class_name = class_name
        self._descriptor = descriptor
        self._access_flags = access_flags
        self._code = None if code_error is not None else (
            None if instructions is _NO_CODE else FakeCode(instructions)
        )
        self._code_error = code_error

    def get_name(self) -> str:
        return self._name

    def get_class_name(self) -> str:
        return self._class_name

    def get_descriptor(self) -> str:
        return self._descriptor

    def get_access_flags(self) -> int:
        return self._access_flags

    def get_code(self):
        if self._code_error is not None:
            raise self._code_error
        return self._code


class _NoCode:
    """Sentinel: a method whose code item is absent (abstract/native)."""


_NO_CODE = _NoCode()


def abstract_method(name: str, class_name: str) -> FakeMethod:
    return FakeMethod(name, class_name, instructions=_NO_CODE)


class FakeClass:
    """Quacks like androguard's ClassDefItem."""

    def __init__(self, name: str, methods: List[FakeMethod]):
        self._name = name
        self._methods = methods

    def get_name(self) -> str:
        return self._name

    def get_methods(self):
        return list(self._methods)


class FakeDEX:
    """Quacks like androguard's DEX."""

    def __init__(self, classes: List[FakeClass]):
        self._classes = classes

    def get_classes(self):
        return list(self._classes)


# --- canonical instruction snippets -----------------------------------------

VM_INVOKE_OUTPUT = (
    "v0, v1, Lcom/pairip/VMRunner;->invoke"
    "(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/Object;"
)
VM_EXECUTE_OUTPUT = (
    "v0, v1, Lcom/pairip/VMRunner;->executeVM"
    "([B[Ljava/lang/Object;)Ljava/lang/Object;"
)
VERIFY_INVOKE_OUTPUT = (
    "v0, Lcom/pairip/SignatureCheck;->verifyIntegrity"
    "(Landroid/content/Context;)V"
)
LOADLIBRARY_OUTPUT = (
    "v0, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V"
)


def insn(name: str, output: str) -> FakeInsn:
    return FakeInsn(name, output)


def vm_stub_insns() -> List[FakeInsn]:
    """A minimal PairIP stub body: load bytecode name, delegate to VMRunner."""
    return [
        FakeInsn("const-string", 'v0, "b4f5k.vmcode"'),
        FakeInsn("invoke-static", VM_INVOKE_OUTPUT),
        FakeInsn("move-result-object", "v0"),
        FakeInsn("return-object", "v0"),
    ]


# --- dex blueprints ----------------------------------------------------------


def pairip_dex_blueprint() -> List[FakeClass]:
    """A PairIP-shaped dex modeled on the sample repositories.

    Mirrors samples/pairipcore/README.md: VMRunner (invoke + native executeVM
    + <clinit> loading "pairipcore"), SignatureCheck.verifyIntegrity, the
    com.pairip.application.Application attachBaseContext hook, plus app
    classes with one virtualized stub and one plain method.
    """
    return [
        FakeClass(
            "Lcom/pairip/VMRunner;",
            [
                FakeMethod(
                    "<clinit>",
                    "Lcom/pairip/VMRunner;",
                    [
                        FakeInsn("const-string", 'v0, "pairipcore"'),
                        FakeInsn("invoke-static", LOADLIBRARY_OUTPUT),
                        FakeInsn("return-void", ""),
                    ],
                ),
                FakeMethod(
                    "invoke",
                    "Lcom/pairip/VMRunner;",
                    [
                        FakeInsn("invoke-static", VM_EXECUTE_OUTPUT),
                        FakeInsn("return-object", "v0"),
                    ],
                ),
                abstract_method("executeVM", "Lcom/pairip/VMRunner;"),
                FakeMethod(
                    "setContext",
                    "Lcom/pairip/VMRunner;",
                    [FakeInsn("return-void", "")],
                ),
            ],
        ),
        FakeClass(
            "Lcom/pairip/SignatureCheck;",
            [
                FakeMethod(
                    "verifyIntegrity",
                    "Lcom/pairip/SignatureCheck;",
                    [FakeInsn("return-void", "")],
                ),
            ],
        ),
        FakeClass(
            "Lcom/pairip/application/Application;",
            [
                FakeMethod(
                    "attachBaseContext",
                    "Lcom/pairip/application/Application;",
                    [
                        FakeInsn("invoke-static", VERIFY_INVOKE_OUTPUT),
                        FakeInsn("invoke-super", "v0, v1"),
                        FakeInsn("return-void", ""),
                    ],
                ),
            ],
        ),
        FakeClass(
            "Lcom/example/game/GameLogic;",
            [
                FakeMethod(
                    "virtualizedSecret",
                    "Lcom/example/game/GameLogic;",
                    vm_stub_insns(),
                ),
                FakeMethod(
                    "plainJava",
                    "Lcom/example/game/GameLogic;",
                    [FakeInsn("const/4", "v0, 1"), FakeInsn("return-void", "")],
                ),
                abstract_method("onAbstract", "Lcom/example/game/GameLogic;"),
            ],
        ),
        FakeClass(
            "Lcom/example/other/Helper;",
            [
                FakeMethod(
                    "callExecuteVMDirectly",
                    "Lcom/example/other/Helper;",
                    [
                        FakeInsn("invoke-static", VM_EXECUTE_OUTPUT),
                        FakeInsn("return-object", "v0"),
                    ],
                ),
            ],
        ),
    ]


def plain_dex_blueprint() -> List[FakeClass]:
    """A dex with no PairIP markers at all."""
    return [
        FakeClass(
            "Lcom/example/app/Main;",
            [
                FakeMethod(
                    "onCreate",
                    "Lcom/example/app/Main;",
                    [FakeInsn("invoke-super", "v0, v1"), FakeInsn("return-void", "")],
                ),
            ],
        ),
    ]


class FakeAPK:
    """Quacks like the subset of androguard's APK used by ApkSource.

    Reads real zip entries from a synthetic APK built by
    :func:`build_synthetic_apk`, so the pure entry-name logic downstream sees
    genuine zip contents.  Manifest facts and dex payloads are canned.
    """

    def __init__(
        self,
        path: str,
        version_name: str = "25.21.1",
        version_code: str = "250211",
        app_class: str = "com.pairip.application.Application",
        dex_blueprints: Optional[List[List[FakeClass]]] = None,
        open_error: bool = False,
    ):
        self.path = path
        self._version_name = version_name
        self._version_code = version_code
        self._app_class = app_class
        self._blueprints = dex_blueprints
        if open_error:
            raise zipfile.BadZipFile("file is not a zip file")
        with zipfile.ZipFile(path) as zf:
            self._files = sorted(zf.namelist())

    # manifest facts
    def get_androidversion_name(self) -> str:
        return self._version_name

    def get_androidversion_code(self) -> str:
        return self._version_code

    def get_attribute_value(self, tag_name: str, attribute: str, **_):
        if tag_name == "application" and attribute == "name":
            return self._app_class
        return None

    # zip facts
    def get_files(self) -> List[str]:
        return list(self._files)

    def get_all_dex(self):
        if self._blueprints is not None:
            blobs = [b"fake-dex-bytes" for _ in self._blueprints]
        else:
            blobs = [b"fake-dex-bytes"]
        yield from blobs


class FakeDEXFactory:
    """Builds FakeDEX objects from blueprints, one per get_all_dex blob."""

    def __init__(self, blueprints: List[List[FakeClass]]):
        self._blueprints = blueprints
        self._index = 0

    def __call__(self, blob: bytes) -> FakeDEX:
        # advance through blueprints regardless of blob count; recycle last
        idx = min(self._index, len(self._blueprints) - 1)
        self._index += 1
        return FakeDEX(self._blueprints[idx])


# --- synthetic APK builder ----------------------------------------------------


def build_synthetic_apk(
    path,
    *,
    with_pairip_libs: bool = True,
    with_vmcode_assets: bool = True,
) -> str:
    """Write a synthetic zip with the entry names a PairIP APK would carry.

    The dex bytes are placeholders -- dex *contents* come from FakeDEX
    blueprints, so no real dex file is needed.
    """
    entries = {
        "AndroidManifest.xml": b"<binary-xml-placeholder/>",
        "classes.dex": b"\x00\x01placeholder-dex",
        "res/layout/activity_main.xml": b"<xml/>",
        "META-INF/MANIFEST.MF": b"Manifest-Version: 1.0\n",
        "lib/arm64-v8a/libother.so": b"\x7fELF-placeholder",
        "lib/armeabi-v7a/libother.so": b"\x7fELF-placeholder",
    }
    if with_pairip_libs:
        entries["lib/arm64-v8a/libpairipcore.so"] = b"\x7fELF-pairipcore"
        entries["lib/armeabi-v7a/libpairipcore.so"] = b"\x7fELF-pairipcore"
    if with_vmcode_assets:
        entries["assets/b4f5k.vmcode"] = b"\x00\x01\x02pairip-vm-bytecode"
        entries["assets/other.vmcode"] = b"\x00\x01\x02pairip-vm-bytecode"
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return str(path)
