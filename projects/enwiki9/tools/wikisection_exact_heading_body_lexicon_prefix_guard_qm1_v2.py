#!/usr/bin/env python3
"""Run WIKISECTION QM1 with the exact causal heading-prefix guard."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import wikisection_exact_heading_body_lexicon_qm1 as base


CANDIDATE_ID = "wikisection_exact_heading_body_lexicon_prefix_guard_qm1_v2"


def heading_remains_possible(prefix: bytes) -> bool:
    """Whether completed line bytes can still begin a frozen exact heading."""
    if not prefix or prefix[0] != ord("="):
        return False
    opening = 0
    while opening < len(prefix) and prefix[opening] == ord("="):
        opening += 1
    if opening > 6:
        return False
    if opening == 1 and len(prefix) > 1:
        return False
    return True


class PrefixGuardSectionMachine(base.SectionMachine):
    def _score_pre_event(self, index: int, event: base.WrtEvent) -> None:
        if self.page is not None and heading_remains_possible(bytes(self.page.line)):
            return
        super()._score_pre_event(index, event)


def main() -> int:
    base.CANDIDATE_ID = CANDIDATE_ID
    base.SectionMachine = PrefixGuardSectionMachine
    base.BOUND_SOURCE_FILES = (
        "projects/enwiki9/docs/wikisection_exact_heading_body_lexicon_qm1_plan.md",
        "projects/enwiki9/docs/wikisection_exact_heading_body_lexicon_prefix_guard_qm1_v2_plan.md",
        "projects/enwiki9/tools/wikisection_exact_heading_body_lexicon_qm1.py",
        "projects/enwiki9/tools/wikisection_exact_heading_body_lexicon_prefix_guard_qm1_v2.py",
        "projects/enwiki9/tools/build_heading_state_map.py",
        "projects/enwiki9/tools/causal_state_screen.py",
        "projects/enwiki9/tools/mobius2_tessera_self_annotation_graph.py",
        "projects/enwiki9/tools/mobius2_tessera_typed_fiber_ceiling.py",
        "projects/enwiki9/tools/sibyl_page_prompt_oracle.py",
        "projects/enwiki9/tools/wrt_exact.py",
    )
    result = base.main()
    if result == 0 and "--output-dir" in sys.argv:
        output = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve() / "decision.json"
        decision = json.loads(output.read_text())
        decision["schema"] = "wikisection_exact_heading_body_lexicon_qm1_decision_v2"
        decision["causal_prefix_guard"] = {
            "parent_job": "20260803T002023Z_f2913f8b93",
            "parent_failure": "accepted_heading_scheduled_dictionary_token_opportunity",
            "rule": "suppress while the completed line prefix can still begin a 2-to-6-equals exact heading",
            "truth_or_event_kind_visible": False,
        }
        output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
