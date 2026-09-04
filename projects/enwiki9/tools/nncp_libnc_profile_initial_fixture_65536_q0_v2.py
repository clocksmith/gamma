#!/usr/bin/env python3
"""Standalone registration of the pre-forward block-zero NNCP fixture."""

from pathlib import Path

import nncp_libnc_profile_initial_fixture_65536_q0 as base


CANDIDATE_ID = "nncp_libnc_profile_initial_fixture_65536_q0_v2"
base.CANDIDATE_ID = CANDIDATE_ID


def source_package(path: Path, experiment: dict[str, object]) -> None:
    members = sorted(
        {
            *base.local_source_closure((Path(__file__),)),
            base.OBJECTIVE_CONTRACT.resolve(),
        },
        key=lambda item: item.relative_to(base.ROOT).as_posix(),
    )
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(base.ROOT).as_posix()
        record = declared.get(relative, {})
        if record != base.reference(member, record.get("id")):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with base.tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(base.ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    with path.open("xb") as output:
        output.write(
            base.lzma.compress(
                tar_path.read_bytes(), preset=9 | base.lzma.PRESET_EXTREME
            )
        )
    tar_path.unlink()
    if path.stat().st_size > base.SOURCE_CEILING:
        raise ValueError("source closure exceeds the frozen package ceiling")


base.source_package = source_package


if __name__ == "__main__":
    raise SystemExit(base.main())
