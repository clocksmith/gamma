#!/usr/bin/env python3
"""WIKIBACK v2: enforce normalized-title separation in Cblind."""

from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
from dataclasses import dataclass, field
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import Any

import wikiback_incoming_anchor_context_qh0 as impl


CANDIDATE_ID = "wikiback_incoming_anchor_context_cblind_keyguard_qh0_v2"
DECISION_SCHEMA = "wikiback_incoming_anchor_context_qh0_decision_v2"
BASE_BOUND_SOURCE_FILES = tuple(impl.BOUND_SOURCE_FILES)
BASE_FROZEN_CONFIG = dict(impl.FROZEN_CONFIG)
CONFIGURED = False


@dataclass
class CausalBacklinkMachineV2(impl.CausalBacklinkMachine):
    completed_snapshots: list[tuple[int, bytes, impl.Snapshot]] = field(
        default_factory=list
    )
    blind_same_key_exclusions: int = 0
    blind_selected_sources: int = 0
    blind_selected_source_key_violations: int = 0
    blind_query_digest: Any = field(default_factory=hashlib.sha256)
    blind_selection_digest: Any = field(default_factory=hashlib.sha256)

    def _blind_snapshot(
        self, current_title_key: bytes, reference: impl.Snapshot
    ) -> impl.Snapshot | None:
        excluded = [
            row
            for row in self.completed_snapshots
            if row[1] == current_title_key
        ]
        distinct_key_rows = [
            row
            for row in self.completed_snapshots
            if row[1] != current_title_key
        ]
        capacity_rows = [
            row
            for row in distinct_key_rows
            if len(row[2].codes) >= len(reference.codes)
        ]
        self.blind_same_key_exclusions += len(excluded)
        self.blind_query_digest.update(len(current_title_key).to_bytes(4, "little"))
        self.blind_query_digest.update(current_title_key)
        self.blind_query_digest.update(len(reference.codes).to_bytes(8, "little"))
        self.blind_query_digest.update(reference.total.to_bytes(8, "little"))
        self.blind_query_digest.update(
            len(self.completed_snapshots).to_bytes(8, "little")
        )
        self.blind_query_digest.update(len(capacity_rows).to_bytes(8, "little"))
        self.blind_query_digest.update(len(excluded).to_bytes(8, "little"))
        for source_ordinal, source_title_key, _ in excluded:
            self.blind_query_digest.update(source_ordinal.to_bytes(8, "little"))
            self.blind_query_digest.update(
                len(source_title_key).to_bytes(4, "little")
            )
            self.blind_query_digest.update(source_title_key)
        if reference.total <= 0:
            return impl.Snapshot.empty()
        if not capacity_rows:
            self.missing_blind_sources += 1
            self.blind_unique_shortfalls += 1
            return None
        target_bin = len(reference.codes).bit_length()
        source_ordinal, source_title_key, source = min(
            capacity_rows,
            key=lambda row: (
                abs(len(row[2].codes).bit_length() - target_bin),
                row[0],
            ),
        )
        if source_title_key == current_title_key:
            self.blind_selected_source_key_violations += 1
            raise ValueError("Cblind selected the current normalized title key")
        self.blind_selected_sources += 1
        self.blind_selection_digest.update(len(current_title_key).to_bytes(4, "little"))
        self.blind_selection_digest.update(current_title_key)
        self.blind_selection_digest.update(source_ordinal.to_bytes(8, "little"))
        self.blind_selection_digest.update(len(source_title_key).to_bytes(4, "little"))
        self.blind_selection_digest.update(source_title_key)
        if len(source.codes).bit_length() == target_bin:
            self.exact_bin_matches += 1
        else:
            self.nearest_bin_matches += 1
        return impl.injective_weight_match(source.counter(), reference)

    def _freeze_snapshots(self, title_key: bytes) -> None:
        full_counter = self.full_index.get(title_key, Counter())
        target_counter = self.target_index.get(title_key, Counter())
        full = impl.Snapshot.from_counter(full_counter)
        target = impl.Snapshot.from_counter(target_counter)
        blind = self._blind_snapshot(title_key, full)
        prior = impl.injective_weight_match(self.previous_page_tokens, full)
        if full.total and prior is None:
            self.missing_prior_sources += 1
            self.prior_unique_shortfalls += 1
        if full.total and (blind is None or prior is None):
            self.all_variant_deactivations += 1
            self.snapshots = {
                name: impl.Snapshot.empty() for name in impl.VARIANTS
            }
        else:
            self.snapshots = {
                "Cblind": blind if blind is not None else impl.Snapshot.empty(),
                "Cprior": prior if prior is not None else impl.Snapshot.empty(),
                "Ctarget": target,
                "Wfull": full,
            }
        self.snapshot_queries += 1
        if full.total:
            self.nonempty_queries += 1
        if self.page is None:
            raise ValueError("title snapshot completed outside a page")
        self.page.wfull_snapshot = full

    def _commit_page(self) -> None:
        if self.page is None:
            raise ValueError("cannot commit an absent page")
        stage = self.page
        if stage.ordinal >= self.page_count:
            raise ValueError("WIKIBACK complete-page limit would be exceeded")
        for target_key, full, target in stage.backlink_counters():
            self.full_index[target_key].update(full)
            self.target_index[target_key].update(target)
            self.completed_links += 1
        self.previous_page_tokens = stage.all_token_counter()
        if stage.wfull_snapshot is not None and stage.wfull_snapshot.total:
            self.completed_snapshots.append(
                (stage.ordinal, stage.title_key, stage.wfull_snapshot)
            )
        self.discarded_boundaries += stage.discarded_boundaries
        if stage.ordinal != self.committed_pages:
            raise ValueError("nonchronological WIKIBACK page commit")
        self.committed_pages += 1
        self.page_commits_after_close += 1
        self.page = None
        self.snapshots = {
            name: impl.Snapshot.empty() for name in impl.VARIANTS
        }

    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.committed_pages.to_bytes(8, "little"))
        digest.update(self.completed_links.to_bytes(8, "little"))
        digest.update(int(self.trailing_partial_page_open).to_bytes(1, "little"))
        digest.update(self.trailing_partial_events.to_bytes(8, "little"))
        for key in sorted(self.full_index):
            impl.update_digest_with_counter(digest, b"F" + key, self.full_index[key])
        for key in sorted(self.target_index):
            impl.update_digest_with_counter(digest, b"T" + key, self.target_index[key])
        impl.update_digest_with_counter(digest, b"P", self.previous_page_tokens)
        for ordinal, source_title_key, snapshot in self.completed_snapshots:
            digest.update(ordinal.to_bytes(8, "little"))
            digest.update(len(source_title_key).to_bytes(4, "little"))
            digest.update(source_title_key)
            impl.update_digest_with_counter(digest, b"S", snapshot.counter())
        digest.update(self.blind_same_key_exclusions.to_bytes(8, "little"))
        digest.update(self.blind_selected_sources.to_bytes(8, "little"))
        digest.update(self.blind_selected_source_key_violations.to_bytes(8, "little"))
        digest.update(self.blind_query_digest.digest())
        digest.update(self.blind_selection_digest.digest())
        return digest.hexdigest()

    def receipt(self) -> dict[str, int | str]:
        receipt = super().receipt()
        receipt.update(
            {
                "blind_same_key_exclusions": self.blind_same_key_exclusions,
                "blind_selected_sources": self.blind_selected_sources,
                "blind_selected_source_key_violations": (
                    self.blind_selected_source_key_violations
                ),
                "blind_query_sha256": self.blind_query_digest.hexdigest(),
                "blind_selection_sha256": self.blind_selection_digest.hexdigest(),
            }
        )
        return receipt


def configure_v2() -> None:
    global CONFIGURED
    if CONFIGURED:
        return
    donor_files = tuple(
        path
        for path in BASE_BOUND_SOURCE_FILES
        if path
        not in {
            "projects/enwiki9/docs/wikiback_incoming_anchor_context_qh0_plan.md",
            "projects/enwiki9/tools/wikiback_incoming_anchor_context_qh0.py",
        }
    )
    impl.CANDIDATE_ID = CANDIDATE_ID
    impl.FRAME_MAGIC = b"WIKIBK2\0"
    impl.CausalBacklinkMachine = CausalBacklinkMachineV2
    impl.BOUND_SOURCE_FILES = (
        "projects/enwiki9/docs/wikiback_incoming_anchor_context_cblind_keyguard_qh0_v2_plan.md",
        "projects/enwiki9/docs/wikiback_incoming_anchor_context_qh0_plan.md",
        "projects/enwiki9/tools/wikiback_incoming_anchor_context_cblind_keyguard_qh0_v2.py",
        "projects/enwiki9/tools/wikiback_incoming_anchor_context_qh0.py",
        *donor_files,
    )
    impl.FROZEN_CONFIG = {
        **BASE_FROZEN_CONFIG,
        "schema": "wikiback_incoming_anchor_context_config_v2",
        "candidate_id": CANDIDATE_ID,
        "matched_control": (
            "causal completed-page source with a normalized title key distinct "
            "from the current title and enough identities; nearest unique-count "
            "bit-length and earliest ordinal ties; injective identities receive "
            "Wfull's exact weight multiset"
        ),
        "blind_title_key_guard": (
            "exclude source_title_key == current_title_key before support matching; "
            "bind source/current keys and selections into machine receipts"
        ),
    }
    impl.CONFIG_BYTES = json.dumps(
        impl.FROZEN_CONFIG, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    impl.CONFIG_SHA256 = hashlib.sha256(impl.CONFIG_BYTES).digest()
    CONFIGURED = True


def output_dir_from_argv() -> Path:
    if "--output-dir" not in sys.argv:
        raise ValueError("WIKIBACK v2 requires --output-dir")
    index = sys.argv.index("--output-dir")
    if index + 1 >= len(sys.argv):
        raise ValueError("--output-dir has no value")
    return Path(sys.argv[index + 1]).resolve()


def strengthen_decision(output_dir: Path) -> None:
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    causal_replays = decision.get("causal_replays", {})
    receipts: list[dict[str, Any]] = []
    for key in ("first_machine", "second_machine"):
        value = causal_replays.get(key)
        if isinstance(value, dict):
            receipts.append(value)
    decoders = causal_replays.get("decoders", {})
    if isinstance(decoders, dict):
        for value in decoders.values():
            if isinstance(value, dict) and isinstance(value.get("machine"), dict):
                receipts.append(value["machine"])

    def valid_sha256(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 64:
            return False
        try:
            bytes.fromhex(value)
        except ValueError:
            return False
        return True

    expected_receipts = 2 + len(impl.VARIANTS)
    query_digests = {
        receipt.get("blind_query_sha256") for receipt in receipts
    }
    selection_digests = {
        receipt.get("blind_selection_sha256") for receipt in receipts
    }
    keyguard_exact = len(receipts) == expected_receipts and all(
        receipt.get("blind_selected_sources", 0) > 0
        and receipt.get("blind_selected_source_key_violations") == 0
        and valid_sha256(receipt.get("blind_query_sha256"))
        and valid_sha256(receipt.get("blind_selection_sha256"))
        for receipt in receipts
    ) and len(query_digests) == 1 and len(selection_digests) == 1
    if not keyguard_exact:
        decision["schema"] = DECISION_SCHEMA
        decision["cblind_keyguard"] = {
            "receipt_count": len(receipts),
            "expected_receipt_count": expected_receipts,
            "all_selected_source_keys_distinct": False,
            "query_digests": sorted(str(value) for value in query_digests),
            "selection_digests": sorted(
                str(value) for value in selection_digests
            ),
        }
        decision["exactness"]["Cblind_title_key_guard_replayed"] = False
        decision["causality"]["Cblind_source_title_key_distinct"] = False
        conditions = decision["gates"]["conditions"]
        conditions["Cblind_title_key_guard"] = False
        conditions["exactness_pass"] = False
        conditions["causality_pass"] = False
        decision["gates"]["failed_conditions"] = [
            "MALFORMED_CBLIND_KEYGUARD_EVIDENCE"
        ]
        decision["decision"] = {
            "verdict": "MALFORMED_EVIDENCE",
            "scientific_verdict": None,
            "distant_replay_authorized": False,
            "native_integration_authorized": False,
            "forecast_change_authorized": False,
            "full_1g_authorized": False,
            "next_action": (
                "Repair the malformed keyguard execution and rerun the identical "
                "frozen candidate as an explicit infrastructure retry."
            ),
        }
        temporary = decision_path.with_suffix(".json.v2.tmp")
        temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
        temporary.replace(decision_path)
        raise ValueError(
            "malformed Cblind keyguard evidence: expected complete, exercised, "
            "byte-identical encoder/decoder query and selection receipts"
        )
    decision["schema"] = DECISION_SCHEMA
    decision["cblind_keyguard"] = {
        "receipt_count": len(receipts),
        "expected_receipt_count": expected_receipts,
        "all_selected_source_keys_distinct": keyguard_exact,
        "query_sha256": next(iter(query_digests)),
        "selection_sha256": next(iter(selection_digests)),
        "first_machine_same_key_exclusions": (
            receipts[0].get("blind_same_key_exclusions") if receipts else None
        ),
        "first_machine_selected_sources": (
            receipts[0].get("blind_selected_sources") if receipts else None
        ),
        "first_machine_selected_source_key_violations": (
            receipts[0].get("blind_selected_source_key_violations")
            if receipts
            else None
        ),
    }
    decision["exactness"]["Cblind_title_key_guard_replayed"] = keyguard_exact
    decision["causality"]["Cblind_source_title_key_distinct"] = keyguard_exact
    conditions = decision["gates"]["conditions"]
    conditions["Cblind_title_key_guard"] = keyguard_exact
    conditions["exactness_pass"] = all(decision["exactness"].values())
    conditions["causality_pass"] = all(
        value
        for key, value in decision["causality"].items()
        if key != "native_parent_state_hash_proved"
    )
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    decision["gates"]["failed_conditions"] = failed
    decision["decision"]["verdict"] = (
        "AUTHORIZED_DISTANT_REPLAY" if authorized else "REJECT"
    )
    decision["decision"]["distant_replay_authorized"] = authorized
    decision["decision"]["next_action"] = (
        "Run only the frozen distant replay and native parent-state proof."
        if authorized
        else (
            "Retire this exact incoming-link source, +/-16 event context, "
            "title-key-guarded snapshot rule, KT coder, and matched controls "
            "without rescue sweeps."
        )
    )
    temporary = decision_path.with_suffix(".json.v2.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)


def main() -> int:
    configure_v2()
    output_dir = output_dir_from_argv()
    base_stdout = io.StringIO()
    with redirect_stdout(base_stdout):
        returncode = impl.main()
    if returncode != 0:
        sys.stdout.write(base_stdout.getvalue())
        return returncode
    strengthen_decision(output_dir)
    final = json.loads((output_dir / "decision.json").read_text())
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "decision": final["decision"]["verdict"],
                "decision_path": str(output_dir / "decision.json"),
                "Cblind_title_key_guard": final["gates"]["conditions"][
                    "Cblind_title_key_guard"
                ],
                "score_credit_bytes": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
