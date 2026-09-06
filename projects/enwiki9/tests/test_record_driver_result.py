"""Recorder protocol tests in isolated roots; no corpus work or real writes.

Existing reflection identity/receipt-reference checks and ledger-row contracts run
unchanged. Full scientific reflection and guard schema validation are delegated
and mocked here; rejection from that validator is tested explicitly.
"""

from __future__ import annotations

from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import record_driver_result as recorder


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        for module, values in (
            (recorder, {"ROOT": self.root, "REPO_ROOT": self.root,
                        "PROGRAMS": self.root / "programs", "RESULTS": self.root / "results"}),
            (recorder.reflections, {"ROOT": self.root, "ADAPTIVE": self.root / "operations/adaptive",
                                    "REFLECTIONS": self.root / "operations/adaptive/reflections"}),
            (recorder.research_contracts, {"PROJECT_ROOT": self.root}),
        ):
            for name, value in values.items():
                self.stack.enter_context(patch.object(module, name, value))
        self.validator = self.stack.enter_context(patch.object(
            recorder.research_contracts, "validate_artifact", return_value={}))
        self.index = self.make_job("job1")
        self.ledger = self.root / "results/run_ledger.jsonl"
        self.ledger.write_bytes(b"")

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")
        return path

    def reference(self, path):
        return {"path": str(path.relative_to(self.root)),
                "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}

    def make_job(self, job_id, candidate="fixture"):
        self.candidate = candidate
        guard_path = self.write(f"results/{job_id}/guard.json",
                                {"status": "complete", "returncode": 0, "label": job_id,
                                 "command": ["fixture"],
                                 "command_sha256": hashlib.sha256(b"fixture").hexdigest()})
        job = {"schema": "gamma.enwiki9.adaptive-job.v3", "job_id": job_id,
               "candidate_id": candidate, "state": "completed", "returncode": 0,
               "finished_at": "2026-09-06T00:00:00+00:00",
               "execution_resources": {"cleanup_complete": True, "guard_path":
                                       str(guard_path.relative_to(self.root))}}
        job_path = self.write(f"operations/adaptive/completed/000_{job_id}.json", job)
        revision = {"candidateId": candidate, "candidateTreeSha256": "sha256:" + "a" * 64,
                    "receipt": {"path": "revision.json", "sha256": "sha256:" + "b" * 64}}
        arms = []
        for arm in ("P", "K"):
            artifacts = {}
            for name in ("archive", "restored", "repeat"):
                path = self.root / f"results/{job_id}/{arm}.{name}"
                path.write_bytes(b"fixture")
                artifacts[name] = self.reference(path)
            digest = hashlib.sha256(b"fixture").hexdigest()
            result = {"program_id": candidate, "arm": arm, "candidate_revision": revision,
                      "timestamp": "2026-09-06T00:00:00+00:00",
                      "run_source": str(job_path.relative_to(self.root)),
                      "data_size": 7, "data_sha256": digest,
                      "compressed_size": 7, "compressed_sha256": digest,
                      "roundtrip_ok": True, "determinism": {"single_host_byte_equal": True},
                      "run_purpose": "diagnostic", "missing_diagnostics": ["optional telemetry unavailable"]}
            path = self.write(f"results/{job_id}/{arm}.json", result)
            arms.append({"arm": arm, "result": self.reference(path), "artifacts": artifacts})
        index_path = self.write(f"results/{job_id}/terminal-index.json",
                                {"schema": "gamma.enwiki9.terminal-result-index.v1",
                                 "job": self.reference(job_path), "guard": self.reference(guard_path),
                                 "arms": arms, "evidence": []})
        reflection_path = self.write(f"operations/adaptive/reflections/{job_id}.json",
                                     {"candidateId": candidate, "candidateRevision": revision,
                                      "job": self.reference(job_path), "evidence": [self.reference(index_path)]})
        meta_path = self.root / f"programs/{candidate}/meta.json"
        metadata = json.loads(meta_path.read_text()) if meta_path.exists() else {
            "status": "measured_negative", "verdict": "retained scientific conclusion",
            "measured": {"reflections": {}}}
        metadata["measured"]["reflections"][job_id] = self.reference(reflection_path)
        self.write(str(meta_path.relative_to(self.root)), metadata)
        return index_path

    def refresh_bindings(self, *, job_changed=False):
        index = json.loads(self.index.read_text())
        job_path = self.root / index["job"]["path"]
        job_id = json.loads(job_path.read_text())["job_id"]
        if job_changed:
            index["job"] = self.reference(job_path)
        self.write(str(self.index.relative_to(self.root)), index)
        reflection_path = self.root / f"operations/adaptive/reflections/{job_id}.json"
        reflection = json.loads(reflection_path.read_text())
        reflection["job"] = self.reference(job_path)
        reflection["evidence"] = [self.reference(self.index)]
        self.write(str(reflection_path.relative_to(self.root)), reflection)
        meta_path = self.root / f"programs/{self.candidate}/meta.json"
        metadata = json.loads(meta_path.read_text())
        metadata["measured"]["reflections"][job_id] = self.reference(reflection_path)
        self.write(str(meta_path.relative_to(self.root)), metadata)

    def record(self, **kwargs):
        return recorder.record_terminal(self.candidate, self.index, **kwargs)

    def rows(self):
        return [json.loads(line) for line in self.ledger.read_text().splitlines()]

    def test_distinct_identical_archive_arms_and_idempotent_retry(self):
        outcome = self.record()
        self.assertEqual(outcome["appended_rows"], 2)
        self.assertEqual({row["run_id"] for row in self.rows()}, {"fixture__job1__P", "fixture__job1__K"})
        before = self.ledger.read_bytes()
        meta_path = self.root / "programs/fixture/meta.json"
        metadata = json.loads(meta_path.read_text())
        self.assertEqual(metadata["status"], "measured_negative")
        self.assertEqual(metadata["verdict"], "retained scientific conclusion")
        os.utime(self.root / "results/job1/P.json", (1, 1))
        self.assertEqual(self.record()["appended_rows"], 0)
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertTrue(self.validator.called)
        self.assertEqual(json.loads((self.root / "results/job1/P.json").read_text())["missing_diagnostics"],
                         ["optional telemetry unavailable"])

    def test_check_is_read_only(self):
        inputs = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        before = (self.root / "programs/fixture/meta.json").read_bytes()
        outcome = self.record(check_only=True)
        self.assertEqual(outcome["missing_rows"], 2)
        self.assertEqual(outcome["local_process_check"], "missing-boot-terminal-evidence-only")
        self.assertEqual(self.ledger.read_bytes(), b"")
        self.assertEqual((self.root / "programs/fixture/meta.json").read_bytes(), before)
        self.assertEqual({path: path.read_bytes() for path in inputs}, inputs)

    def test_guard_command_and_job_identity_rejected(self):
        path = self.root / "results/job1/guard.json"
        original = json.loads(path.read_text())
        for field, value, reason in (("label", "another-job", "guard label"),
                                     ("command_sha256", "0" * 64, "guard command digest")):
            guard = dict(original)
            guard[field] = value
            self.write(str(path.relative_to(self.root)), guard)
            index = json.loads(self.index.read_text())
            index["guard"] = self.reference(path)
            self.write(str(self.index.relative_to(self.root)), index)
            self.refresh_bindings()
            with self.assertRaisesRegex(ValueError, reason):
                self.record()

    def test_running_or_duplicate_live_claim_rejected(self):
        terminal = self.root / "operations/adaptive/completed/000_job1.json"
        self.write("operations/adaptive/running/000_job1.json", json.loads(terminal.read_text()))
        with self.assertRaisesRegex(ValueError, "live queue claim"):
            self.record()
        terminal.unlink()
        with self.assertRaises(FileNotFoundError):
            self.record()
        self.assertEqual(self.rows(), [])

    def test_missing_cleanup_and_running_guard_rejected(self):
        path = self.root / "operations/adaptive/completed/000_job1.json"
        job = json.loads(path.read_text())
        job["execution_resources"]["cleanup_complete"] = False
        self.write(str(path.relative_to(self.root)), job)
        self.refresh_bindings(job_changed=True)
        with self.assertRaisesRegex(ValueError, "cleanup"):
            self.record()
        job["execution_resources"]["cleanup_complete"] = True
        self.write(str(path.relative_to(self.root)), job)
        guard = self.root / "results/job1/guard.json"
        value = json.loads(guard.read_text())
        value.update(status="running", returncode=None)
        self.write(str(guard.relative_to(self.root)), value)
        index = json.loads(self.index.read_text())
        index["guard"] = self.reference(guard)
        self.write(str(self.index.relative_to(self.root)), index)
        self.refresh_bindings(job_changed=True)
        with self.assertRaisesRegex(ValueError, "guard is not closed"):
            self.record()

    def test_live_terminal_worker_rejected_and_zombie_is_not_live(self):
        path = self.root / "operations/adaptive/completed/000_job1.json"
        job = json.loads(path.read_text())
        job["worker_pid"] = os.getpid()
        job["worker_proc_start_ticks"] = int(Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()[19])
        job["execution_resources"]["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        self.write(str(path.relative_to(self.root)), job)
        self.refresh_bindings(job_changed=True)
        with self.assertRaisesRegex(ValueError, "remains live"):
            self.record()
        with patch.object(Path, "read_text", return_value="123 (process) Z " + "0 " * 18 + "42"):
            self.assertFalse(recorder._process_active(123, 42))
        self.assertFalse(recorder._process_active(999999999))

    def test_missing_or_replaced_artifact_rejected_before_writes(self):
        path = self.root / "results/job1/K.repeat"
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "identity differs"):
            self.record()
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.record()
        self.assertEqual(self.rows(), [])

    def test_missing_claim_evidence_and_alias_repeat_rejected(self):
        index = json.loads(self.index.read_text())
        index["arms"][0]["artifacts"].pop("repeat")
        self.write(str(self.index.relative_to(self.root)), index)
        self.refresh_bindings()
        with self.assertRaisesRegex(ValueError, "missing repeat evidence"):
            self.record()
        index["arms"][0]["artifacts"]["repeat"] = index["arms"][0]["artifacts"]["archive"]
        self.write(str(self.index.relative_to(self.root)), index)
        self.refresh_bindings()
        with self.assertRaisesRegex(ValueError, "separately retained"):
            self.record()

    def test_replaced_result_reflection_and_validator_rejection(self):
        reflection = self.root / "operations/adaptive/reflections/job1.json"
        old = reflection.read_bytes()
        reflection.write_bytes(old + b" ")
        with self.assertRaisesRegex(ValueError, "reflection digest differs"):
            self.record()
        reflection.write_bytes(old)
        self.validator.side_effect = ValueError("scientific contract failed")
        with self.assertRaisesRegex(ValueError, "scientific contract failed"):
            self.record()
        self.validator.side_effect = None
        result = self.root / "results/job1/P.json"
        result.write_bytes(result.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "identity differs"):
            self.record()
        self.assertEqual(self.rows(), [])

    def test_interruption_after_ledger_append_retries_metadata(self):
        with patch.object(recorder, "write_json", side_effect=InterruptedError("fixture interruption")):
            with self.assertRaises(InterruptedError):
                self.record()
        self.assertEqual(len(self.rows()), 2)
        outcome = self.record()
        self.assertEqual(outcome["appended_rows"], 0)
        self.assertTrue(outcome["metadata_updated"])

    def test_completed_prefix_is_resumable_but_torn_line_preserved(self):
        self.record()
        first = self.ledger.read_bytes().splitlines(keepends=True)[0]
        self.ledger.write_bytes(first)
        self.assertEqual(self.record()["appended_rows"], 1)
        torn = self.ledger.read_bytes() + b'{"run_id":'
        self.ledger.write_bytes(torn)
        with self.assertRaisesRegex(ValueError, "incomplete line"):
            self.record()
        self.assertEqual(self.ledger.read_bytes(), torn)

    def test_duplicate_claim_and_replaced_index_after_recording_rejected(self):
        self.record()
        before = self.ledger.read_bytes()
        with self.ledger.open("ab") as stream:
            stream.write(before.splitlines(keepends=True)[0])
        with self.assertRaisesRegex(ValueError, "duplicated ledger claim"):
            self.record()
        self.ledger.write_bytes(before)
        index = json.loads(self.index.read_text())
        index["note"] = "changed index"
        self.write(str(self.index.relative_to(self.root)), index)
        self.refresh_bindings()
        with self.assertRaisesRegex(ValueError, "existing projection"):
            self.record()

    def test_concurrent_distinct_and_duplicate_recording(self):
        second = self.make_job("job2")
        context = multiprocessing.get_context("fork")
        queue = context.Queue()
        start = context.Event()

        def run(index):
            start.wait()
            try:
                queue.put(recorder.record_terminal("fixture", index))
            except Exception as exc:
                queue.put({"error": repr(exc)})

        children = [context.Process(target=run, args=(index,)) for index in (self.index, self.index, second)]
        for child in children:
            child.start()
        start.set()
        outcomes = [queue.get(timeout=30) for _ in children]
        for child in children:
            child.join(timeout=30)
            self.assertEqual(child.exitcode, 0)
        self.assertFalse([outcome for outcome in outcomes if "error" in outcome], outcomes)
        self.assertEqual(sum(outcome["appended_rows"] for outcome in outcomes), 4)
        self.assertEqual(len({row["run_id"] for row in self.rows()}), 4)
        metadata = json.loads((self.root / "programs/fixture/meta.json").read_text())
        self.assertEqual(set(metadata["measured"]["terminal_results"]), {"job1", "job2"})

    def test_evidence_replaced_during_append_is_not_projected(self):
        original = recorder._missing_rows
        count = 0

        def replace_after_append(existing, proposed):
            nonlocal count
            count += 1
            result = original(existing, proposed)
            if count == 2:
                (self.root / "results/job1/P.archive").write_bytes(b"changed")
            return result

        with patch.object(recorder, "_missing_rows", side_effect=replace_after_append):
            with self.assertRaisesRegex(ValueError, "changed after ledger append"):
                self.record()
        metadata = json.loads((self.root / "programs/fixture/meta.json").read_text())
        self.assertNotIn("terminal_results", metadata["measured"])
        with self.assertRaisesRegex(ValueError, "identity differs"):
            self.record()

    def test_failed_arm_can_preserve_missing_archive_without_inventing_claims(self):
        index = json.loads(self.index.read_text())
        for arm in index["arms"]:
            path = self.root / arm["result"]["path"]
            value = json.loads(path.read_text())
            value.update(compressed_size=None, compressed_sha256=None, roundtrip_ok=False,
                         determinism=None, failure_class="implementation-failure")
            self.write(str(path.relative_to(self.root)), value)
            arm["result"] = self.reference(path)
            arm["artifacts"] = {}
        self.write(str(self.index.relative_to(self.root)), index)
        self.refresh_bindings()
        self.assertEqual(self.record()["appended_rows"], 2)
        self.assertTrue(all(row["compressed_size"] is None and row["roundtrip_ok"] is False for row in self.rows()))

    def test_changed_entire_arm_set_cannot_replace_interrupted_claim(self):
        with patch.object(recorder, "write_json", side_effect=InterruptedError("fixture interruption")):
            with self.assertRaises(InterruptedError):
                self.record()
        index = json.loads(self.index.read_text())
        for entry in index["arms"]:
            path = self.root / entry["result"]["path"]
            result = json.loads(path.read_text())
            result["arm"] += "2"
            path = self.write(f"results/job1/{result['arm']}.json", result)
            entry["arm"] = result["arm"]
            entry["result"] = self.reference(path)
        self.write(str(self.index.relative_to(self.root)), index)
        self.refresh_bindings()
        before = self.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, "different index or reflection"):
            self.record()
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_reserved_source_tags_cannot_bypass_interrupted_job_identity(self):
        with patch.object(recorder, "write_json", side_effect=InterruptedError("fixture interruption")):
            with self.assertRaises(InterruptedError):
                self.record()
        before = self.ledger.read_bytes()
        index = json.loads(self.index.read_text())
        for entry in index["arms"]:
            source = self.root / entry["result"]["path"]
            result = json.loads(source.read_text())
            result["arm"] += "2"
            path = self.write(f"results/job1/{result['arm']}.json", result)
            entry["arm"], entry["result"] = result["arm"], self.reference(path)
        for prefix in ("terminal-job:", "terminal-index:", "terminal-reflection:"):
            with self.subTest(prefix=prefix):
                path = self.root / index["arms"][0]["result"]["path"]
                result = json.loads(path.read_text())
                result["run_tags"] = [prefix + "carryover0"]
                self.write(str(path.relative_to(self.root)), result)
                index["arms"][0]["result"] = self.reference(path)
                self.write(str(self.index.relative_to(self.root)), index)
                self.refresh_bindings()
                with self.assertRaisesRegex(ValueError, "reserved terminal recorder identity tags"):
                    self.record()
                self.assertEqual(self.ledger.read_bytes(), before)

    def test_check_rejects_conflicting_metadata_projection(self):
        self.record()
        path = self.root / "programs/fixture/meta.json"
        meta = json.loads(path.read_text())
        meta["measured"]["terminal_results"]["job1"]["arms"]["P"]["compressed_size"] += 1
        self.write(str(path.relative_to(self.root)), meta)
        with self.assertRaisesRegex(ValueError, "existing projection"):
            self.record(check_only=True)

    def test_legacy_result_cli_preserved(self):
        arguments = ["record_driver_result.py", "fixture", "--result", str(self.root / "results/job1/P.json"),
                     "--label", "legacy-fixture", "--note", "retained"]
        with patch.object(sys, "argv", arguments), redirect_stdout(io.StringIO()):
            self.assertEqual(recorder.main(), 0)
        metadata = json.loads((self.root / "programs/fixture/meta.json").read_text())
        self.assertEqual(metadata["measured"]["legacy-fixture"]["notes"], ["retained"])
        self.assertEqual(self.ledger.read_bytes(), b"")

    def test_retry_after_boot_change_preserves_recorded_bytes(self):
        path = self.root / "operations/adaptive/completed/000_job1.json"
        job = json.loads(path.read_text())
        boot_path = Path("/proc/sys/kernel/random/boot_id")
        job["execution_resources"]["boot_id"] = boot_path.read_text().strip()
        self.write(str(path.relative_to(self.root)), job)
        self.refresh_bindings(job_changed=True)
        self.assertEqual(self.record()["local_process_check"], "same-boot-identities-checked")
        meta_path = self.root / "programs/fixture/meta.json"
        before = (self.ledger.read_bytes(), meta_path.read_bytes())
        original = Path.read_text

        def foreign_boot(path, *args, **kwargs):
            return "another-boot\n" if path == boot_path else original(path, *args, **kwargs)

        with patch.object(Path, "read_text", foreign_boot):
            outcome = self.record()
        self.assertEqual(outcome["local_process_check"], "foreign-boot-terminal-evidence-only")
        self.assertEqual(outcome["appended_rows"], 0)
        self.assertEqual((self.ledger.read_bytes(), meta_path.read_bytes()), before)

    def test_check_rejects_evidence_replacement_after_ledger_read(self):
        original = recorder._missing_rows

        def replace(existing, proposed):
            result = original(existing, proposed)
            (self.root / "results/job1/P.archive").write_bytes(b"changed")
            return result

        with patch.object(recorder, "_missing_rows", side_effect=replace):
            with self.assertRaisesRegex(ValueError, "changed during check"):
                self.record(check_only=True)
        self.assertEqual(self.ledger.read_bytes(), b"")


class RecordedEvidenceIntegrationTests(unittest.TestCase):
    def test_real_reflection_guard_and_results_validate_without_canonical_writes(self):
        """A disposable projection binds retained records through full validators."""
        candidate = "dualstream_grammar_development250k_q0_v1"
        job_id = "20260906T174841Z_181d2f2c47"
        original_reflection = PROJECT / f"operations/adaptive/reflections/{job_id}.json"
        if not original_reflection.exists():
            self.skipTest("retained closed grammar evidence is unavailable")
        value = json.loads(original_reflection.read_text())
        job_path = PROJECT / value["job"]["path"]
        job = json.loads(job_path.read_text())
        guard_path = PROJECT / job["execution_resources"]["guard_path"]
        if not guard_path.exists():
            self.skipTest("host-local closed guard is unavailable")
        metadata_path = PROJECT / f"programs/{candidate}/meta.json"
        canonical = [original_reflection, job_path, metadata_path, guard_path,
                     PROJECT / "results/run_ledger.jsonl"]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in canonical}
        with tempfile.TemporaryDirectory(prefix="recorder-integration-", dir=PROJECT / "results") as directory:
            scratch = Path(directory)
            arms = []
            for arm in ("P", "S"):
                path = PROJECT / f"operations/evidence/{candidate}_normalized/{arm}.json"
                result = json.loads(path.read_text())
                artifacts = {name: recorder.reflections.reference(Path(ref["path"]))
                             for name, ref in result["artifacts"].items()}
                arms.append({"arm": arm, "result": recorder.reflections.reference(path),
                             "artifacts": artifacts})
            index_path = scratch / "terminal-index.json"
            index_path.write_text(json.dumps({"schema": "gamma.enwiki9.terminal-result-index.v1",
                "job": value["job"], "guard": recorder.reflections.reference(guard_path),
                "arms": arms, "evidence": []}))
            value["evidence"].append(recorder.reflections.reference(index_path))
            reflection_path = scratch / "reflection-fixture.json"
            reflection_path.write_text(json.dumps(value))
            metadata = json.loads(metadata_path.read_text())
            metadata["measured"]["reflections"][job_id] = recorder.reflections.reference(reflection_path)
            local_meta = scratch / f"programs/{candidate}/meta.json"
            local_meta.parent.mkdir(parents=True)
            local_meta.write_text(json.dumps(metadata))
            (scratch / "run_ledger.jsonl").write_bytes(b"")
            inputs = {path: path.read_bytes() for path in scratch.rglob("*") if path.is_file()}
            with patch.object(recorder, "PROGRAMS", scratch / "programs"), patch.object(recorder, "RESULTS", scratch):
                outcome = recorder.record_terminal(candidate, index_path, check_only=True)
            self.assertEqual(outcome["arms"], 2)
            self.assertEqual(outcome["missing_rows"], 2)
            self.assertEqual({path: path.read_bytes() for path in inputs}, inputs)
            guard = json.loads(guard_path.read_text())
            self.assertEqual(recorder._validate_guard_receipt(guard_path, job, guard), "discovery-budget-schema")
            wrong = json.loads(json.dumps(job))
            wrong["execution_resources"]["groups"][0]["memory_bytes"] += 4096
            with self.assertRaisesRegex(ValueError, "allocation exceeds|requested memory differs"):
                recorder._validate_guard_receipt(guard_path, wrong, guard)
            qualification = {**job, "execution_mode": "qualification"}
            with self.assertRaises(recorder.research_contracts.jsonschema.ValidationError):
                recorder._validate_guard_receipt(guard_path, qualification, guard)
        self.assertEqual({path: hashlib.sha256(path.read_bytes()).hexdigest() for path in canonical}, before)


if __name__ == "__main__":
    unittest.main()
