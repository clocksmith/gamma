#!/usr/bin/env python3
"""Run the production final-RMSNorm order gate with declared probes."""

from __future__ import annotations

import lzma
from pathlib import Path
import tarfile

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_final_rmsnorm_order_64_q0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_order_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROBE_SOURCE = PROGRAM / "final_rmsnorm_probe.inc.c"
EVALUATOR_SOURCE = PROGRAM / "final_rmsnorm_order.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_final_rmsnorm_order_64_q0_retry_v1_materializer.py"
)
RUNNER = Path(__file__).resolve()
_PARENT_PATCH_TEACHER = parent.patch_teacher
DECLARATIONS = """static void gamma_final_rms_set_block(int block_idx);
static void gamma_final_rms_dump(
    const char *kind, int state, NCTensor *tensor);

"""


def patch_teacher(source: str) -> str:
    patched = _PARENT_PATCH_TEACHER(source)
    return parent.replace_once(
        patched,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        EVALUATOR_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        parent.FIXTURE_HOOK.resolve(),
    ]
    members = sorted(
        set(members), key=lambda item: item.relative_to(ROOT).as_posix()
    )
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(
        lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    tar_path.unlink()
    if path.stat().st_size > parent.SOURCE_CEILING:
        raise ValueError("final RMSNorm order source closure exceeds ceiling")


def configure() -> None:
    bindings = {
        "CANDIDATE_ID": CANDIDATE_ID,
        "PROGRAM": PROGRAM,
        "RESULT": RESULT,
        "WORK": WORK,
        "PROBE_SOURCE": PROBE_SOURCE,
        "EVALUATOR_SOURCE": EVALUATOR_SOURCE,
        "PROGRAM_DESCRIPTOR": PROGRAM_DESCRIPTOR,
        "MATERIALIZER": MATERIALIZER,
    }
    for name, value in bindings.items():
        setattr(parent, name, value)
    parent.patch_teacher = patch_teacher
    parent.source_package = source_package


def main() -> int:
    configure()
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
