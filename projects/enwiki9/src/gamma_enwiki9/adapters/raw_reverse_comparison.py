"""The known P/K/D comparison through explicit execution and evidence services."""
from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
import sys

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.types import EvidenceReport, ScientificDecision


def commands(codec: Path, population: Path, output: Path, arm: str, *, python=sys.executable, block_size=250000):
    archive, raw, repeat = (output / (arm + suffix) for suffix in (".rbz", ".raw", ".repeat.rbz"))
    options = ["--mode", arm, "--block-size", str(block_size)]
    return [("encode", [python, str(codec), "encode", str(population), str(archive), *options]),
            ("decode", [python, str(codec), "decode", str(archive), str(raw)]),
            ("repeat", [python, str(codec), "encode", str(raw), str(repeat), *options])]


def run(executor: CommandExecutor, *, codec: Path, population: Path,
        population_sha256: str, limits: PhaseLimits) -> dict:
    output = executor.context.workspace
    identity = fingerprint(population, population.parent)
    if identity["sha256"] != population_sha256 or identity["bytes"] > 1000000:
        raise ValueError("comparison population differs or exceeds fixture scope")
    command_rows, archives, reports = [], {}, {}
    failed = None
    evidence_errors = []
    try:
        for arm in ("P", "K", "D"):
            for phase, argv in commands(codec, population, output, arm):
                outcome, row = executor.run(arm + "-" + phase, argv, limits)
                command_rows.append(row)
                if outcome.classification != "completed":
                    failed = outcome
                    break
                reports[(arm, phase)] = json.loads((output / (arm + "-" + phase + ".stdout")).read_bytes())
            if failed:
                break
            archive = (output / (arm + ".rbz")).read_bytes()
            if (output / (arm + ".raw")).read_bytes() != population.read_bytes():
                raise ValueError("independent inverse differs")
            if (output / (arm + ".repeat.rbz")).read_bytes() != archive:
                raise ValueError("raw encoder repeat differs")
            encoded, decoded, repeated = (reports[(arm, p)] for p in ("encode", "decode", "repeat"))
            common = {k: v for k, v in encoded.items() if k != "requested_mode"}
            if encoded != repeated or common != decoded:
                raise ValueError("encoder/decoder common witness differs")
            if sum(encoded["costs"].values()) != len(archive):
                raise ValueError("complete archive accounting differs")
            archives[arm] = archive
        if not failed and archives["P"] != archives["K"]:
            raise ValueError("P/K archive identity differs")
        if fingerprint(population, population.parent) != identity:
            raise ValueError("population changed during comparison")
    except (ValueError, OSError) as error:
        evidence_errors.append(str(error))
    if failed or evidence_errors:
        evidence = EvidenceReport(False, missing=tuple(evidence_errors) + ((failed.classification,) if failed else ()))
        decision = ScientificDecision("D archive is smaller than P", "inconclusive", evidence)
    else:
        evidence = EvidenceReport(True, identities=(population_sha256,),
            comparisons=("independent inverses", "raw repeats", "P/K identity", "complete archive accounting"),
            coverage=("common_encoder_decoder_projection",))
        decision = ScientificDecision("D archive is smaller than P",
            "supported" if len(archives["D"]) < len(archives["P"]) else "rejected", evidence)
    result = {"schema": "gamma.enwiki9.comparison-migration.v1", "commands": command_rows,
        "execution": asdict(failed) if failed else {"classification": "completed", "cleanup_complete": True},
        "evidence": asdict(evidence), "decision": asdict(decision),
        "archive_bytes": {k: len(v) for k, v in archives.items()},
        "objective_credit_bytes": 0, "resource_qualified": False}
    publish_immutable_artifact(output / "comparison.json", canonical_bytes(result) + b"\n")
    return result
