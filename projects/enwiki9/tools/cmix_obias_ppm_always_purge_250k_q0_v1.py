#!/usr/bin/env python3
"""Build and run the frozen 250KB exact PPM residency diagnostic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cmix_obias_bithead_delta_midas512_q0_v2 as monitor
import cmix_obias_source_1m_roundtrip_qm2 as qualified


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_ppm_always_purge_250k_q0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM = ROOT / "programs" / "cmix_obias_ppm_always_purge_q0_v1"
BUILD_CONTRACT = PROGRAM / "build_contract.json"
RAW_SCOPE = 250_000
OPENING_SHA256 = "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"
MAX_PROGRAM_BYTES = 557_019


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    monitor.refuse_concurrent_cmix()
    contract = json.loads(BUILD_CONTRACT.read_text())
    qm1 = qualified.parent
    qm0 = qm1.parent
    original_command = qm1.command

    def command(
        command_args: list[str],
        *,
        cwd: Path,
        environment: dict[str, str] | None = None,
    ) -> dict[str, object]:
        adjusted = list(command_args)
        if adjusted[:2] == ["make", "prof_use"]:
            adjusted[1] = "cmix"
        executable = Path(adjusted[0]).name if adjusted else ""
        if executable in {"cmix", "cmix_orig", "archive9"}:
            return monitor.monitored_command(
                adjusted,
                cwd=cwd,
                environment=environment,
                failure_directory=RESULT,
            )
        return original_command(adjusted, cwd=cwd, environment=environment)

    qualified.CANDIDATE_ID = CANDIDATE_ID
    qualified.RESULT = RESULT
    qm1.command = command
    qm0.RAW_SCOPE = RAW_SCOPE
    qm0.MAX_PROGRAM_BYTES = MAX_PROGRAM_BYTES
    qm0.EXPECTED["opening"] = OPENING_SHA256
    qm0.DEFINES = (
        "-DSEED=923 -DUPDATE_LIMIT=3000 -DLSTM_NUM_CELLS=256 "
        "-DKH_BITLSTM32 -DKH_OBIAS -DKH_OBIAS_CONST_GATE=0.15f "
        + str(contract["compileDefine"])
    )
    returncode = qualified.main()
    if returncode != 0:
        return returncode

    decision_path = RESULT / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision.update(
        {
            "schema": "gamma.enwiki9.cmix-obias-ppm-always-purge-250k-q0-v1",
            "candidate_id": CANDIDATE_ID,
            "status": "TERMINAL_250KB_INFRASTRUCTURE_DIAGNOSTIC",
            "score_credit_bytes": 0,
            "claim_boundary": (
                "Opening-250KB page-residency diagnostic only; payload identity "
                "against its matched clean control and larger-scope RSS transfer "
                "remain required."
            ),
            "memory_policy": {
                "build_contract_path": str(BUILD_CONTRACT.relative_to(ROOT)),
                "build_contract_sha256": sha256(BUILD_CONTRACT),
                "compile_define": contract["compileDefine"],
                "check_interval_input_bytes": contract["checkIntervalInputBytes"],
                "probability_change": False,
            },
            "population": {"raw_bytes": RAW_SCOPE, "sha256": OPENING_SHA256},
            "decision": {
                "promotion_authorized": False,
                "reason": "Matched clean payload comparison and joint memory decision required.",
                "target_bytes": 105_000_000,
            },
        }
    )
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(json.dumps({"event": "ppm_memory_diagnostic_terminal"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
