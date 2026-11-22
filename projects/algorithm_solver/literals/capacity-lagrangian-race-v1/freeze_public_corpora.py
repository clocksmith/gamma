#!/usr/bin/env python3
"""Freeze 12 independently selected EXTERNAL public open-source corpora (P01..P12) with exact UTF-8
bytes and SHA-256 hashes (no private local paths stored in the frozen JSON).

Selected by isolated read-only subagent 368a4433-8fc7-4918-9162-3895c1b0b4cc from upstream
C headers (GGML, FFmpeg, Cairo, Brotli), CPython 3.14.2 stdlib, and npm packages (semver,
postcss, protobufjs, undici). Runs zero capacity, rank, or solver calculations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

SELECTIONS = [
    {
        "id": "P01",
        "name": "ggml_backends_alloc_headers",
        "upstreamProject": "ggml",
        "language": "C",
        "files": [
            ("include/ggml-alloc.h", "/opt/homebrew/include/ggml-alloc.h"),
            ("include/ggml-blas.h", "/opt/homebrew/include/ggml-blas.h"),
            ("include/ggml-cpp.h", "/opt/homebrew/include/ggml-cpp.h"),
            ("include/ggml-zendnn.h", "/opt/homebrew/include/ggml-zendnn.h"),
        ],
        "description": "GGML tensor allocator, C++ helper, and BLAS/ZenDNN backend public headers.",
    },
    {
        "id": "P02",
        "name": "ffmpeg_libavutil_hwcontext_headers",
        "upstreamProject": "FFmpeg",
        "language": "C",
        "files": [
            ("libavutil/hwcontext_cuda.h", "/opt/homebrew/include/libavutil/hwcontext_cuda.h"),
            ("libavutil/hwcontext_vdpau.h", "/opt/homebrew/include/libavutil/hwcontext_vdpau.h"),
            ("libavutil/hwcontext_videotoolbox.h", "/opt/homebrew/include/libavutil/hwcontext_videotoolbox.h"),
        ],
        "description": "FFmpeg libavutil hardware acceleration context headers for CUDA, VDPAU, and VideoToolbox.",
    },
    {
        "id": "P03",
        "name": "cairo_xlib_script_headers",
        "upstreamProject": "cairo",
        "language": "C",
        "files": [
            ("cairo/cairo-script.h", "/opt/homebrew/include/cairo/cairo-script.h"),
            ("cairo/cairo-xlib.h", "/opt/homebrew/include/cairo/cairo-xlib.h"),
            ("cairo/cairo-xlib-xrender.h", "/opt/homebrew/include/cairo/cairo-xlib-xrender.h"),
        ],
        "description": "Cairo 2D graphics library public headers for script surface and Xlib/XRender backends.",
    },
    {
        "id": "P04",
        "name": "brotli_decoder_core_headers",
        "upstreamProject": "brotli",
        "language": "C",
        "files": [
            ("brotli/decode.h", "/opt/homebrew/include/brotli/decode.h"),
            ("brotli/port.h", "/opt/homebrew/include/brotli/port.h"),
            ("brotli/shared_dictionary.h", "/opt/homebrew/include/brotli/shared_dictionary.h"),
            ("brotli/types.h", "/opt/homebrew/include/brotli/types.h"),
        ],
        "description": "Brotli compression library public headers defining decoder APIs, shared dictionaries, and core types.",
    },
    {
        "id": "P05",
        "name": "cpython_asyncio_task_helpers",
        "upstreamProject": "CPython 3.14.2",
        "language": "Python",
        "files": [
            ("Lib/asyncio/base_tasks.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/base_tasks.py"),
            ("Lib/asyncio/exceptions.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/exceptions.py"),
            ("Lib/asyncio/mixins.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/mixins.py"),
        ],
        "description": "CPython 3.14.2 asyncio subpackage modules for task inspection, exceptions, and loop-binding mixins.",
    },
    {
        "id": "P06",
        "name": "cpython_multiprocessing_posix_popen",
        "upstreamProject": "CPython 3.14.2",
        "language": "Python",
        "files": [
            ("Lib/multiprocessing/popen_fork.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/multiprocessing/popen_fork.py"),
            ("Lib/multiprocessing/popen_forkserver.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/multiprocessing/popen_forkserver.py"),
            ("Lib/multiprocessing/popen_spawn_posix.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/multiprocessing/popen_spawn_posix.py"),
        ],
        "description": "CPython 3.14.2 multiprocessing POSIX process-spawning backends for fork, forkserver, and spawn.",
    },
    {
        "id": "P07",
        "name": "cpython_sqlite3_interface",
        "upstreamProject": "CPython 3.14.2",
        "language": "Python",
        "files": [
            ("Lib/sqlite3/__init__.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/sqlite3/__init__.py"),
            ("Lib/sqlite3/dbapi2.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/sqlite3/dbapi2.py"),
            ("Lib/sqlite3/dump.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/sqlite3/dump.py"),
        ],
        "description": "CPython 3.14.2 sqlite3 stdlib modules implementing DB-API 2.0 wrapper and SQL dump iterator.",
    },
    {
        "id": "P08",
        "name": "cpython_unittest_execution_core",
        "upstreamProject": "CPython 3.14.2",
        "language": "Python",
        "files": [
            ("Lib/unittest/__main__.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/__main__.py"),
            ("Lib/unittest/_log.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/_log.py"),
            ("Lib/unittest/result.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/result.py"),
            ("Lib/unittest/signals.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/signals.py"),
            ("Lib/unittest/suite.py", "/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/suite.py"),
        ],
        "description": "CPython 3.14.2 unittest execution modules covering TestSuite, TestResult, signals, log capture, and CLI.",
    },
    {
        "id": "P09",
        "name": "semver_range_utilities",
        "upstreamProject": "semver",
        "language": "JavaScript",
        "files": [
            ("semver/ranges/max-satisfying.js", "../../../../../../reploid/node_modules/semver/ranges/max-satisfying.js"),
            ("semver/ranges/min-satisfying.js", "../../../../../../reploid/node_modules/semver/ranges/min-satisfying.js"),
            ("semver/ranges/min-version.js", "../../../../../../reploid/node_modules/semver/ranges/min-version.js"),
            ("semver/ranges/simplify.js", "../../../../../../reploid/node_modules/semver/ranges/simplify.js"),
        ],
        "description": "node-semver range evaluation helpers for computing minimal, maximal, and simplified version bounds.",
    },
    {
        "id": "P10",
        "name": "postcss_ast_nodes_results",
        "upstreamProject": "postcss",
        "language": "JavaScript",
        "files": [
            ("postcss/lib/at-rule.js", "../../../../../../reploid/node_modules/postcss/lib/at-rule.js"),
            ("postcss/lib/document.js", "../../../../../../reploid/node_modules/postcss/lib/document.js"),
            ("postcss/lib/no-work-result.js", "../../../../../../reploid/node_modules/postcss/lib/no-work-result.js"),
            ("postcss/lib/result.js", "../../../../../../reploid/node_modules/postcss/lib/result.js"),
            ("postcss/lib/root.js", "../../../../../../reploid/node_modules/postcss/lib/root.js"),
        ],
        "description": "PostCSS core JS classes representing AtRule, Document, and Root CSS AST nodes alongside Result objects.",
    },
    {
        "id": "P11",
        "name": "protobufjs_reflection_primitives",
        "upstreamProject": "protobufjs",
        "language": "JavaScript",
        "files": [
            ("protobufjs/src/method.js", "../../../../../../reploid/node_modules/protobufjs/src/method.js"),
            ("protobufjs/src/oneof.js", "../../../../../../reploid/node_modules/protobufjs/src/oneof.js"),
            ("protobufjs/src/roots.js", "../../../../../../reploid/node_modules/protobufjs/src/roots.js"),
        ],
        "description": "protobuf.js hand-written reflection modules for RPC Method, OneOf field groups, and root registries.",
    },
    {
        "id": "P12",
        "name": "undici_http_client_apis",
        "upstreamProject": "undici",
        "language": "JavaScript",
        "files": [
            ("undici/lib/api/api-connect.js", "../../../../../../reploid/node_modules/undici/lib/api/api-connect.js"),
            ("undici/lib/api/api-pipeline.js", "../../../../../../reploid/node_modules/undici/lib/api/api-pipeline.js"),
            ("undici/lib/api/api-request.js", "../../../../../../reploid/node_modules/undici/lib/api/api-request.js"),
            ("undici/lib/api/api-stream.js", "../../../../../../reploid/node_modules/undici/lib/api/api-stream.js"),
            ("undici/lib/api/api-upgrade.js", "../../../../../../reploid/node_modules/undici/lib/api/api-upgrade.js"),
        ],
        "description": "Undici HTTP/1.1 client API handlers implementing request, stream, pipeline, connect, and upgrade.",
    },
]


def main() -> None:
    corpora = {}
    queries = []
    for spec in SELECTIONS:
        programs = []
        file_meta = []
        for canonical_rel, src in spec["files"]:
            p = Path(src) if Path(src).is_absolute() else (HERE / src).resolve()
            raw = p.read_bytes()
            text = raw.decode("utf-8")
            programs.append(text)
            file_meta.append({
                "upstreamPath": canonical_rel,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            })
        alpha_size = len(set("".join(programs)))
        total_bytes = sum(f["bytes"] for f in file_meta)
        corpora[spec["id"]] = {
            "id": spec["id"],
            "name": spec["name"],
            "upstreamProject": spec["upstreamProject"],
            "language": spec["language"],
            "description": spec["description"],
            "alphabetSize": alpha_size,
            "totalBytes": total_bytes,
            "files": file_meta,
            "programs": programs,
        }
        queries.append({"corpusId": spec["id"], "rule": "W2", "budget": 64, "kind": "64-slot-cliff"})
        below_k = alpha_size - 1 if alpha_size <= 64 else alpha_size - 2
        if below_k != 64:
            queries.append({"corpusId": spec["id"], "rule": "W2", "budget": below_k, "kind": "below-alphabet"})

    payload = {
        "schema": "bits-public-repo-lagrangian-instances/v1",
        "selectorSubagentId": "368a4433-8fc7-4918-9162-3895c1b0b4cc",
        "rule": "W2",
        "maxBytes": 160,
        "wholeProgramExcluded": True,
        "corpora": corpora,
        "queries": queries,
    }
    out = HERE / "public-instances.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(corpora)} external OSS corpora, {len(queries)} unique queries)")
    for cid, c in corpora.items():
        print(f"  {cid} ({c['upstreamProject']:14s} / {c['language']:10s}) |S|={c['alphabetSize']:2d} bytes={c['totalBytes']:5d}")


if __name__ == "__main__":
    main()
