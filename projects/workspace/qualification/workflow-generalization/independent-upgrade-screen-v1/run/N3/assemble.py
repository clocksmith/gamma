#!/usr/bin/env python3
"""Derive the disposition of one case mechanically from the raw repeats and write results/<case>.json.

  SCREEN_OUT_DIR=<dir holding repeat-1.json .. repeat-3.json> ./assemble.py

The table applied is the one in ../../README.md. The sealed list is only read.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screenlib as lib  # noqa: E402
import case_meta  # noqa: E402  (per-case constants: CASE, CONDITIONS, DEVIATIONS, FLAGS)

SCREEN = os.path.normpath(os.path.join(HERE, "..", ".."))


def classify_b(gate):
    if not gate["reported_success"]:
        return "rejected"
    return "accepted-right-value" if gate["stored_is_right"] else "accepted-wrong-value"


def disposition(repeats):
    """Returns (disposition, reason, gate A right per repeat, gate B class per repeat, gate C right per repeat)."""
    a_ok = [r["gate_A"]["reported_success"] and r["gate_A"]["stored_is_right"] for r in repeats]
    b = [classify_b(r["gate_B"]) for r in repeats]
    c_ok = [r["gate_C"]["stored_is_right"] for r in repeats]
    if len(repeats) < 3:
        return "not-run", f"only {len(repeats)} valid repeat(s)", a_ok, b, c_ok
    if not all(a_ok):
        return "setup-block", "the old workflow did not store the right value on the from-version 3 of 3", a_ok, b, c_ok
    if all(x == "rejected" for x in b):
        return "loud-failure", "the to-version rejected the old steps 3 of 3", a_ok, b, c_ok
    if all(x == "accepted-right-value" for x in b):
        return "self-healing", "the to-version accepted the old steps and stored the right value 3 of 3", a_ok, b, c_ok
    if all(x == "accepted-wrong-value" for x in b):
        if all(c_ok):
            return ("silent-wrong-write",
                    "old steps reported success and stored a value other than the right one 3 of 3; "
                    "the correct path stored the right value 3 of 3", a_ok, b, c_ok)
        return ("mixed", "old steps accepted with a wrong value 3 of 3, but the correct path did not store the "
                "right value 3 of 3", a_ok, b, c_ok)
    return "mixed", "gate B differed across the three repeats", a_ok, b, c_ok


def gate_summary(repeats, a_ok, b, c_ok):
    def rows(gate):
        return [{"repeat": r["repeat"], "status": r[gate]["workflow_response_status"],
                 "stored": r[gate]["stored"], "right": r[gate]["right"]} for r in repeats]
    return {
        "A_old_workflow_on_from_version_right": f"{sum(a_ok)} of {len(a_ok)}",
        "B_old_workflow_on_to_version": b,
        "C_correct_path_on_to_version_right": f"{sum(c_ok)} of {len(c_ok)}",
        "A_observations": rows("gate_A"), "B_observations": rows("gate_B"), "C_observations": rows("gate_C"),
    }


def main():
    out_dir = os.environ["SCREEN_OUT_DIR"]
    repeats = []
    for n in (1, 2, 3):
        path = os.path.join(out_dir, f"repeat-{n}.json")
        if os.path.exists(path):
            repeats.append(json.load(open(path)))
    sealed = next(c for c in json.load(open(os.path.join(SCREEN, "screen-list.json")))["candidates"]
                  if c["id"] == case_meta.CASE)
    verdict, reason, a_ok, b, c_ok = disposition(repeats)
    as_sealed = None
    if repeats and all("corrected" in r for r in repeats):
        # The sealed steps did not work as written; the repeats also hold the smallest correction. The case's
        # disposition is that of the corrected steps, flagged; the sealed steps keep their own verdict beside it.
        as_sealed = {"disposition": verdict, "disposition_reason": reason,
                     "gate_summary": gate_summary(repeats, a_ok, b, c_ok)}
        corrected = [{**r["corrected"], "repeat": r["repeat"]} for r in repeats]
        verdict, reason, a_ok, b, c_ok = disposition(corrected)
        summary = gate_summary(corrected, a_ok, b, c_ok)
    else:
        summary = gate_summary(repeats, a_ok, b, c_ok)
    sealed_digests = {i["ref"]: i["platforms"] for i in sealed["images"]}
    ran = repeats[0]["images"] if repeats else {}
    comparison = {}
    for ref, pin in ran.items():
        sealed_digest = sealed_digests.get(ref, {}).get(pin.get("architecture"), {}).get("digest")
        comparison[ref] = {"platform_ran": f"{pin.get('os')}/{pin.get('architecture')}",
                           "sealed_digest_for_that_platform": sealed_digest,
                           "ran_platform_manifest_digest": pin.get("platform_manifest_digest"),
                           "same": sealed_digest is not None and sealed_digest == pin.get("platform_manifest_digest")}
    result = {
        "schema": "gammatron-real-upgrade-screen-result/v1",
        "case": case_meta.CASE,
        "app": sealed["app"], "from_version": sealed["from_version"], "to_version": sealed["to_version"],
        "assembled_utc": lib.utc_now(),
        "disposition": verdict, "disposition_reason": reason,
        "flags": case_meta.FLAGS,
        "gate_summary": summary,
        "steps_exactly_as_sealed": as_sealed,
        "sealed_prediction": {"predicted_disposition": sealed["predicted_disposition"],
                              "prediction_detail": sealed["prediction_detail"],
                              "predicted_stored_on_to_version":
                                  sealed["database_outcome"]["predicted_stored_on_to_version"]},
        "prediction_right": verdict == sealed["predicted_disposition"],
        "prediction_right_means": "the mechanical disposition equals the sealed predicted disposition; see "
                                  "prediction_notes for the stored values and for any flag that qualifies it",
        "prediction_notes": case_meta.PREDICTION_NOTES,
        "conditions": case_meta.CONDITIONS,
        "deviations": case_meta.DEVIATIONS,
        "images": {"sealed_digests_by_platform": sealed_digests,
                   "ran": ran,
                   "same_in_every_repeat": all(r["images"] == ran for r in repeats) if repeats else None,
                   "digest_comparison": comparison,
                   "digest_notes": case_meta.DIGEST_NOTES},
        "voided_attempts": case_meta.VOIDED_ATTEMPTS,
        "repeats": repeats,
    }
    target = os.path.join(SCREEN, "results", f"{case_meta.CASE}.json")
    lib.write_json(target, result)
    print(case_meta.CASE, verdict, "|", reason, "| prediction", "right" if result["prediction_right"] else "wrong")
    print("A", a_ok, "B", b, "C", c_ok)
    if as_sealed:
        print("exactly as sealed:", as_sealed["disposition"], "|", as_sealed["disposition_reason"])


if __name__ == "__main__":
    main()
