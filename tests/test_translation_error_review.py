"""End-to-end tests for blinded diagnostic translation review custody."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import jsonschema


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "pipeline"
PROMOTION_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "promotion"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_LEDGER = _load_module(
    "translation_error_review_ledger_builder",
    PIPELINE_ROOT / "build_translation_error_ledger.py",
)
_PACKAGE = _load_module(
    "translation_error_review_package_builder",
    PIPELINE_ROOT / "build_translation_error_review_package.py",
)
_MERGE = _load_module(
    "translation_error_review_merger",
    PIPELINE_ROOT / "merge_translation_error_review.py",
)


def _receipt(core: dict) -> dict:
    payload = json.dumps(
        core,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {**core, "receiptHash": hashlib.sha256(payload).hexdigest()}


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class TranslationErrorReviewTests(unittest.TestCase):
    def test_two_reviews_and_distinct_adjudication_merge_by_custodied_mapping(self) -> None:
        population = {
            "pair": "en-es",
            "source": "Keep number 12",
            "target_pos": "Conserva el número 12",
            "tgt_lang": "es",
        }
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            population_path = root / "population.jsonl"
            alpha_path = root / "alpha.jsonl"
            beta_path = root / "beta.jsonl"
            ledger_path = root / "ledger.json"
            worklist_path = root / "worklist.json"
            mapping_path = root / "mapping.json"
            reviewer_one_path = root / "reviewer-one.json"
            reviewer_two_path = root / "reviewer-two.json"
            adjudicator_path = root / "adjudicator.json"
            population_path.write_text(json.dumps(population) + "\n", encoding="utf-8")
            alpha_path.write_text(
                json.dumps({**population, "pred": "Conserva el número 12"}) + "\n",
                encoding="utf-8",
            )
            beta_path.write_text(
                json.dumps({**population, "pred": "Conserva el número"}) + "\n",
                encoding="utf-8",
            )
            ledger = _LEDGER.build_error_ledger(
                population_path,
                [("system-alpha", alpha_path), ("system-beta", beta_path)],
                ledger_id="test-ledger",
            )
            _write_json(ledger_path, ledger)
            worklist, mapping = _PACKAGE.build_review_package(
                ledger_path,
                b"fixed-test-key-material-32-bytes!!",
                worklist_id="blinded-review-v1",
            )
            _write_json(worklist_path, worklist)
            _write_json(mapping_path, mapping)

            reviewer_one = self._submission(worklist, role="reviewer", actor_id="reviewer-one")
            reviewer_two = self._submission(worklist, role="reviewer", actor_id="reviewer-two")
            _write_json(reviewer_one_path, reviewer_one)
            _write_json(reviewer_two_path, reviewer_two)
            reviewer_hashes = sorted(
                hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (reviewer_one_path, reviewer_two_path)
            )
            adjudicator = self._submission(
                worklist,
                role="adjudicator",
                actor_id="adjudicator-one",
                reviewer_hashes=reviewer_hashes,
            )
            _write_json(adjudicator_path, adjudicator)

            merged = _MERGE.merge_reviews(
                ledger_path,
                worklist_path,
                mapping_path,
                [reviewer_one_path, reviewer_two_path],
                adjudicator_path,
            )

            schema = json.loads((PROMOTION_ROOT / "error-ledger.schema.json").read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema).validate(merged)
            final = merged["rows"][0]["adjudication"]
            self.assertEqual(final["status"], "complete")
            self.assertEqual(final["reviewerIds"], ["reviewer-one", "reviewer-two"])
            self.assertEqual(final["adjudicatorId"], "adjudicator-one")
            self.assertEqual(set(final["systemAssessments"]), {"system-alpha", "system-beta"})
            self.assertTrue(
                all(assessment["status"] == "complete" for assessment in final["systemAssessments"].values())
            )
            self.assertEqual(final["reviewerSubmissionSha256s"], reviewer_hashes)

    @staticmethod
    def _submission(
        worklist: dict,
        *,
        role: str,
        actor_id: str,
        reviewer_hashes: list[str] | None = None,
    ) -> dict:
        rows = []
        for row in worklist["rows"]:
            rows.append(
                {
                    "rowId": row["rowId"],
                    "inputAssessment": {"status": "usable", "notes": ""},
                    "outputs": [
                        {"outputLabel": output["outputLabel"], "errors": [], "notes": ""}
                        for output in row["outputs"]
                    ],
                    "notes": "",
                }
            )
        core = {
            "schemaVersion": 1,
            "submissionId": f"{worklist['worklistId']}.{actor_id}",
            "worklistId": worklist["worklistId"],
            "worklistReceiptHash": worklist["receiptHash"],
            "role": role,
            "actorId": actor_id,
            "qualificationReceiptSha256": "a" * 64,
            "rows": rows,
        }
        if role == "adjudicator":
            core["reviewerSubmissionSha256s"] = reviewer_hashes or []
        return _receipt(core)


if __name__ == "__main__":
    unittest.main()
