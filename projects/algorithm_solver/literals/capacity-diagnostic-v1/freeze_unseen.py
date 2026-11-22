#!/usr/bin/env python3
"""Freeze unseen-instances.json from pinned 59ff0441 Git blobs and constructed decision corpora.

Does NOT run diagnostic.py or print any alphabet/rank/bound statistics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"

REAL_PY_PATHS = [
    "tests/test_seal_fx2_cmix21_lstm200_disjoint.py",
    "tests/latent_handoff/test_experiment_config.py",
    "tests/test_seal_fx2_cmix21_source_package_accounting.py",
    "tests/test_seal_fx2_cmix21_lstm200_source_frontier.py",
    "tests/latent_handoff/test_no_replay_route.py",
    "tests/test_seal_cmix21_lstm200_fx2lite428_10m_codec_failure.py",
    "tests/latent_handoff/test_rope_roundtrip.py",
    "tests/test_mind_meld.py",
    "tests/test_seal_cmix21_lstm200_fx2lite428_ram_recovery.py",
    "tests/test_seal_wrt_static_boundary_swap_geometry_title_proxy.py",
    "tests/test_run_fx2_cmix21_wrapper_proof.py",
    "tests/test_wikiir_materialize.py",
]

REAL_YAML_PATHS = [
    "configs/latent_handoff/qwen3_0_6b_to_1_7b.yaml",
    "configs/latent_handoff/qwen3_1_7b_to_0_6b.yaml",
]


def git_cat(repo: Path, rev_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), "cat-file", "blob", rev_path]
    )


def main() -> None:
    here = Path(__file__).resolve().parent
    repo = here.parents[3]

    py_progs, py_meta = [], []
    for p in REAL_PY_PATHS:
        raw = git_cat(repo, f"{PIN}:{p}")
        py_progs.append(raw.decode("utf-8"))
        py_meta.append({"path": p, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

    yaml_progs, yaml_meta = [], []
    for p in REAL_YAML_PATHS:
        raw = git_cat(repo, f"{PIN}:{p}")
        yaml_progs.append(raw.decode("utf-8"))
        yaml_meta.append({"path": p, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

    # 66 distinct printable ASCII chars: 62 base chars + 2 pairs (c62,c63) and (c64,c65)
    pool = [chr(c) for c in range(33, 33 + 66)]
    base62 = pool[:62]
    p1_a, p1_b, p2_a, p2_b = pool[62], pool[63], pool[64], pool[65]
    pair1, pair2 = p1_a + p1_b, p2_a + p2_b
    pairable_66 = [
        "".join(base62[:15]) + pair1 + "".join(base62[15:31]) + pair2,
        "".join(base62[31:46]) + pair1 + "".join(base62[46:62]) + pair2,
    ]
    doomed_66 = [
        "".join(base62[:15]) + pair1 + "".join(base62[15:31]) + pair2,
        "".join(base62[31:46]) + (p1_b + p1_a + p1_b) + "".join(base62[46:62]) + (p2_b + p2_a + p2_b),
    ]

    # Unresolved case: overlap motif {abcd, abce, fbcd} (6 chars) + 20 extra disjoint chars with shared bigrams
    extra20 = [chr(ord("g") + i) for i in range(20)]
    tail_a = "".join(extra20[:10])
    tail_b = "".join(extra20[10:20])
    unresolved_26 = [
        "abcd",
        "abce",
        "fbcd",
        tail_a + "gh" + tail_b[:5],
        tail_b + "gh" + tail_a[:5],
    ]

    payload = {
        "schema": "capacity-diagnostic-unseen-instances/v1",
        "pin": PIN,
        "corpora": {
            "unseen_real_py_tests_12": {"source": "git-blobs-59ff0441", "files": py_meta, "programs": py_progs},
            "unseen_real_yaml_pair": {"source": "git-blobs-59ff0441", "files": yaml_meta, "programs": yaml_progs},
            "decision_66char_pairable": {"source": "encoding-decision-pair-A", "programs": pairable_66},
            "decision_66char_doomed": {"source": "encoding-decision-pair-B", "programs": doomed_66},
            "unseen_3comp_mixed": {
                "source": "fresh-3-component-mixed",
                "programs": ["cde", "cdf", "gdf", "hjkl", "klhj", "hlkj", "kjhl", "wxy", "wxwx"],
            },
            "unseen_forced_block_split": {
                "source": "fresh-forced-block-split",
                "programs": ["ijk", "ljk", "ijmnop", "opmn", "mpon", "onmp"],
            },
            "unseen_u_span_obstruction": {
                "source": "fresh-u-span-obstruction",
                "programs": ["uvwz", "wzuv", "uzwv", "wvuz"],
            },
            "unseen_unresolved_interval": {
                "source": "fresh-natural-unresolved",
                "programs": unresolved_26,
            },
        },
    }
    out = here / "unseen-instances.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Froze {len(payload['corpora'])} unseen corpora to {out.name} (zero diagnostics run).")


if __name__ == "__main__":
    main()
