#!/usr/bin/env python3
"""Retry the production update fixture with corrected external identities."""

from pathlib import Path

import nncp_libnc_profile_update_fixture_64_q0 as base


CANDIDATE_ID = "nncp_libnc_profile_update_fixture_64_q1_v1"
base.CANDIDATE_ID = CANDIDATE_ID
base.EXPECTED = {
    base.LIBNC_ROOT / "nncp.c": "9a44757c4837607b0be9abc0bb2780dbe006b381728549481eedc339599a138a",
    base.LIBNC_ROOT / "libnc.so": "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e",
    base.PREPROCESSED: "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    base.DICTIONARY: "950683b44e6c7696f6daa896296365eb54bce8cc05ae15fff7acb5715936a0a1",
}


def source_package(path: Path, experiment: dict[str, object]) -> None:
    members = [*base.local_source_closure((Path(__file__),)), base.HOOK.resolve()]
    members = sorted(
        set(members), key=lambda item: item.relative_to(base.ROOT).as_posix()
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
    path.write_bytes(
        base.lzma.compress(
            tar_path.read_bytes(), preset=9 | base.lzma.PRESET_EXTREME
        )
    )
    tar_path.unlink()
    if path.stat().st_size > experiment["budget"]["maximumAddedPackageBytes"]:
        raise ValueError("source closure exceeds the frozen package budget")


base.source_package = source_package


if __name__ == "__main__":
    raise SystemExit(base.main())
