"""Build the C engine into the extension alteruphono._native.

The C core and merkmal's C sources are compiled straight into the extension,
as merkmal and regulae do, so nothing is located at run time. merkmal is taken
from AP_MERKMAL_SOURCE_DIR (default: ../merkmal, branch
claude/alteruphono-support until merged), with its `cc-by` data profile:
alteruphono needs only merkmal's `descriptive` system (CC-BY-4.0), and the
full profile would put P-base (CC-BY-NC-SA) and PHOIBLE (CC-BY-SA) in an MIT
package.
"""

from __future__ import annotations

import glob
import os

from setuptools import Extension, setup

HERE = os.path.dirname(os.path.abspath(__file__))
MERKMAL = os.environ.get("AP_MERKMAL_SOURCE_DIR", os.path.join(HERE, "..", "merkmal"))
if not os.path.exists(os.path.join(MERKMAL, "include", "merkmal.h")):
    raise SystemExit(f"alteruphono: merkmal sources not found at {MERKMAL}; set AP_MERKMAL_SOURCE_DIR")


def rel(path: str) -> str:
    return os.path.relpath(path, HERE)


merkmal_full_data = os.path.join(MERKMAL, "src", "generated", "builtin_data.c")
SOURCES = (
    ["python/_native.c"]
    + sorted(rel(p) for p in glob.glob(os.path.join(HERE, "src", "*.c")))
    + ["src/generated/compat1x.c"]
    + sorted(
        rel(p)
        for pattern in ("src/*.c", "src/generated/*.c")
        for p in glob.glob(os.path.join(MERKMAL, pattern))
        if os.path.abspath(p) != os.path.abspath(merkmal_full_data)
    )
    + [rel(os.path.join(MERKMAL, "src", "generated", "cc-by", "builtin_data.c"))]
)

SANITIZE = os.environ.get("AP_SANITIZE", "")
SANITIZE_FLAGS = [f"-fsanitize={SANITIZE}", "-fno-omit-frame-pointer", "-g"] if SANITIZE else []

setup(
    options={"bdist_wheel": {"py_limited_api": "cp312"}},
    ext_modules=[
        Extension(
            "alteruphono._native",
            sources=SOURCES,
            include_dirs=["include", "src", rel(os.path.join(MERKMAL, "include")), rel(os.path.join(MERKMAL, "src"))],
            define_macros=[("Py_LIMITED_API", "0x030C0000")],
            py_limited_api=True,
            extra_compile_args=["-std=c99", "-O2", "-Wall", "-Wextra", *SANITIZE_FLAGS],
            extra_link_args=[*SANITIZE_FLAGS],
        )
    ],
)
