"""Synthetic scan and canonical-main admission tests; external authority is mocked."""
from contextlib import contextmanager, ExitStack
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_field_opportunity_gate_v2 as gate
import causal_field_opportunity_v1 as observer
import enwiki9_python_source_closure as closure
import jsonschema

MAIN_EVIDENCE = []


def fixture():
    raw = b"{{place|name=A|text=alpha}}{{place|name=B|text=beta}}{{place|name=A|text=alpha}}"
    modeled = b"\7" + bytes(observer.base.wrt.wrt_byte_transform(byte) for byte in raw)
    return raw, modeled


def ref(root, name):
    data = (root / name).read_bytes()
    return {"path": name, "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def schema(name):
    return json.loads((ROOT / "contracts/research/v1" / name).read_bytes())


@contextmanager
def main_fixture():
    source_paths = {str(path.relative_to(ROOT)) for path in closure.local_source_closure(
        [ROOT / gate.SELF, ROOT / gate.LAB, ROOT / gate.GUARD])} | gate.MANDATORY_SOURCES
    with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
        root = Path(directory)
        for name in source_paths:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        raw, modeled = fixture()
        words, dictionary = [b"alpha", b"beta"], b"alpha\nbeta\n"
        pop = {"modeled_path": "fixtures/modeled.bin", "dictionary_path": "fixtures/dictionary.bin",
               "terminal_result_path": "fixtures/T-result.json", "raw_bytes": len(raw),
               "raw_sha256": hashlib.sha256(raw).hexdigest()}
        (root / "fixtures").mkdir()
        (root / pop["modeled_path"]).write_bytes(modeled)
        (root / pop["dictionary_path"]).write_bytes(dictionary)
        original = observer.base.Adapter(words, "T", len(raw))
        for byte in modeled:
            original.feed(byte)
        original.finish()
        write_json(root / pop["terminal_result_path"], {"program_stats": {"phase": {"adapter": original.stats()}}})
        runtime = Path(sys.executable).resolve()
        runtime_data = runtime.read_bytes()
        plan = {"candidate_id": gate.ID, "bounds": gate.CAPS, "population": pop,
                "runtime": {"path": str(runtime), "bytes": len(runtime_data),
                            "sha256": hashlib.sha256(runtime_data).hexdigest()},
                "source_paths": sorted(source_paths)}
        write_json(root / gate.PLAN, plan)
        names = sorted(source_paths | set(pop[name] for name in ("modeled_path", "dictionary_path", "terminal_result_path")) | {gate.PLAN})
        contract = {
            "schema": "gamma.enwiki9.adaptive-experiment-contract.v1",
            "objective": {"objectiveId": "synthetic", "objectiveDigest": "sha256:" + "0" * 64,
                          "objectivePath": "contracts/objective.json", "targetScoreBytes": 99000000,
                          "corpusBytes": 1000000000, "corpusSha256": "0" * 64},
            "experimentId": gate.ID, "proposalId": gate.ID, "status": "frozen",
            "registrationTiming": "prospective", "evidenceClass": "diagnostic", "objectiveCreditBytes": 0,
            "parent": None, "hypothesis": {"claim": "State parity", "falsification": "Any divergence"},
            "changedMechanism": "Observations only", "invariants": ["No predictor changes"],
            "controls": [{"id": "T", "role": "comparator", "definition": "Frozen adapter"}],
            "population": {"unit": "bytes", "scopeBytes": len(raw), "scopeSymbols": len(modeled),
                           "selection": "Synthetic", "coordinate": "WRT modeled bytes"},
            "causalBoundary": {"availableInformation": ["Decoded prefix"], "forbiddenInformation": ["Future bytes"]},
            "inputs": [{"id": "input-" + str(i), **ref(root, name)} for i, name in enumerate(names)],
            "budget": {"expectedGrossSavingsBytes": 0, "maximumAddedPackageBytes": 0, "expectedNetSavingsBytes": 0},
            "search": {"expectedTransferRetention": 0, "expectedRuntimeRatio": 1, "expectedMemoryRatio": 1,
                       "uncertaintyRisk": 1, "interactionRisk": 1},
            "measurements": [{"id": "agreement", "definition": "All states agree", "unit": "boolean"}],
            "promotionPredicates": [{"id": "no-promotion", "measurement": "agreement", "operator": "eq", "threshold": False}],
            "killPredicates": [{"id": "no-science-rejection", "measurement": "agreement", "operator": "eq", "threshold": False}],
            "outputs": ["results/" + gate.ID + "/report.json"], "generatedUtc": "2026-09-07T00:00:00Z"}
        contract_name = "operations/adaptive/experiments/" + gate.ID + ".json"
        write_json(root / contract_name, contract)
        revision_name = "operations/adaptive/candidate-revisions/" + gate.ID + "/synthetic.json"
        revision = {"schema": "gamma.enwiki9.candidate-revision.v1", "candidateId": gate.ID,
                    "candidateTreeSha256": "sha256:" + "a" * 64}
        write_json(root / revision_name, revision)
        job_id, worker, inode = "synthetic-job", 123456789, 4455
        group = Path("/sys/fs/cgroup/synthetic/gamma-enwiki9-" + job_id)
        budget = {**gate.CAPS, "cgroup_parent": str(group.parent)}
        marker = root / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl")
        marker.parent.mkdir(parents=True)
        marker.write_bytes(b"")
        job = {"schema": "gamma.enwiki9.adaptive-job.v3", "job_id": job_id, "candidate_id": gate.ID,
               "candidate_revision": ref(root, revision_name), "candidate_tree_sha256": revision["candidateTreeSha256"],
               "experiment": ref(root, contract_name), "proposal": {"path": "proposal.json", "sha256": "sha256:" + "b" * 64},
               "proposal_id": gate.ID, "runner": ref(root, gate.SELF), "execution_guard": ref(root, gate.GUARD),
               "gate_size": len(raw), "priority": 100, "purpose": "diagnostic", "state": "running",
               "tags": ["synthetic"], "submitted_at": "2026-09-07T00:00:00Z", "execution_mode": "discovery",
               "resource_budget": budget, "worker_pid": worker, "worker_proc_start_ticks": 1234,
               "execution_resources": {"budget": budget, "cgroup_path": str(group), "cgroup_inode": inode,
                   "guard_path": str((marker.parent / "guard.json").relative_to(root))}}
        job_path = root / "operations/adaptive/running/000_synthetic-job.json"
        write_json(job_path, job)
        candidate = {"candidateId": gate.ID, "candidateTreeSha256": job["candidate_tree_sha256"],
                     "receipt": job["candidate_revision"]}
        result = root / "results" / gate.ID
        result.mkdir(parents=True)
        environ = {"GAMMA_ENWIKI9_EXPERIMENT_JSON": json.dumps(job["experiment"]),
                   "GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON": json.dumps(candidate),
                   "GAMMA_RESOURCE_PHASE_MARKERS": str(marker)}
        stack.enter_context(patch.dict(os.environ, environ))
        stack.enter_context(patch.object(gate, "ROOT", root))
        stack.enter_context(patch.object(gate.os, "getppid", return_value=worker))
        stack.enter_context(patch.object(gate.os, "sched_getaffinity", return_value={2}))
        timer = stack.enter_context(patch.object(gate.signal, "setitimer"))
        stack.enter_context(patch.object(gate.signal, "signal"))
        stack.enter_context(patch.object(gate.resource, "setrlimit"))
        lab = SimpleNamespace(__file__=str(root / gate.LAB), ROOT=root,
                              worker_pid_matches_job=Mock(return_value=True))
        stack.enter_context(patch.dict(sys.modules, {"enwiki9_lab": lab}))
        import_call = stack.enter_context(patch.object(gate, "import_lab", wraps=gate.import_lab))
        reads, real_bound_read = [], gate.bound_read
        def tracking_read(root, reference, *args, **kwargs):
            reads.append(reference["path"])
            return real_bound_read(root, reference, *args, **kwargs)
        stack.enter_context(patch.object(gate, "bound_read", side_effect=tracking_read))
        path_read, path_stat = Path.read_text, Path.stat
        pseudo = {Path("/proc/self/cgroup"): "0::/synthetic/" + group.name + "\n",
                  group / "memory.max": str(gate.CAPS["memory_bytes"]), group / "memory.swap.max": "0"}
        def read_text(path, *args, **kwargs):
            return pseudo[path] if path in pseudo else path_read(path, *args, **kwargs)
        def file_stat(path, *args, **kwargs):
            return SimpleNamespace(st_ino=inode) if path == group else path_stat(path, *args, **kwargs)
        stack.enter_context(patch.object(Path, "read_text", read_text))
        stack.enter_context(patch.object(Path, "stat", file_stat))
        def refresh():
            write_json(root / gate.PLAN, plan)
            for reference in contract["inputs"]:
                if reference["path"] == gate.PLAN:
                    reference.update(ref(root, gate.PLAN))
            write_json(root / contract_name, contract)
            job["experiment"] = ref(root, contract_name)
            write_json(job_path, job)
            os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"] = json.dumps(job["experiment"])
        yield SimpleNamespace(root=root, plan=plan, contract=contract, candidate=candidate, job=job,
                              job_path=job_path, result=result, marker=marker, group=group, pseudo=pseudo,
                              pop=pop, lab=lab, import_call=import_call, reads=reads, timer=timer, refresh=refresh,
                              contract_name=contract_name, revision_name=revision_name)


class ScanTests(unittest.TestCase):
    def test_scan_binds_complete_reconstructed_identity_and_original_state(self):
        raw, modeled = fixture()
        expected = observer.base.Adapter([], "T", len(raw))
        for byte in modeled:
            expected.feed(byte)
        expected.finish()
        report = gate.scan(observer, modeled, [], len(raw), hashlib.sha256(raw).hexdigest(), expected.stats())
        self.assertTrue(report["retained_terminal_state_agreement"])
        self.assertEqual(report["diagnostics"]["inherited_selected_starts"], 1)
        self.assertEqual(report["diagnostics"]["conditional"]["exact_compatible_hit"], 1)
        again = gate.scan(observer, modeled, [], len(raw), hashlib.sha256(raw).hexdigest(), expected.stats())
        self.assertEqual(report, again)
        self.assertIsNone(report["archive_bytes"])
        self.assertEqual(report["objective_credit_bytes"], 0)

    def test_wrong_raw_hash_and_terminal_expectation_fail(self):
        raw, modeled = fixture()
        with self.assertRaisesRegex(ValueError, "raw identity mismatch"):
            gate.scan(observer, modeled, [], len(raw), "0" * 64)
        with self.assertRaisesRegex(ValueError, "retained corpus adapter"):
            gate.scan(observer, modeled, [], len(raw), hashlib.sha256(raw).hexdigest(), {})

    def test_first_intermediate_state_divergence_fails_even_if_terminal_would_agree(self):
        class Broken(observer.Adapter):
            def state_digest(self):
                return "0" * 64 if self.modeled_count == 9 else super().state_digest()
        raw, modeled = fixture()
        with self.assertRaisesRegex(ValueError, "state divergence at modeled byte 8"):
            gate.scan(SimpleNamespace(base=observer.base, Adapter=Broken), modeled, [], len(raw), hashlib.sha256(raw).hexdigest())

    def test_first_emission_divergence_fails(self):
        class Broken(observer.Adapter):
            def feed(self, byte):
                output = super().feed(byte)
                return output + b"!" if self.modeled_count == 9 else output
        raw, modeled = fixture()
        with self.assertRaisesRegex(ValueError, "raw emission divergence at modeled byte 8"):
            gate.scan(SimpleNamespace(base=observer.base, Adapter=Broken), modeled, [], len(raw), hashlib.sha256(raw).hexdigest())

    def test_malformed_or_overbound_population_fails(self):
        with self.assertRaises(ValueError):
            gate.scan(observer, b"\7\0", [], 250001, "0" * 64)
        with self.assertRaisesRegex(ValueError, "modeled bound"):
            gate.scan(observer, b"\7" * 4097, [], 0, "0" * 64)
        with self.assertRaises(ValueError):
            gate.scan(observer, b"", [], 0, hashlib.sha256(b"").hexdigest())


class BindingTests(unittest.TestCase):
    def test_digest_bounds_aliases_and_nonregular_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").write_bytes(b"abc")
            reference = ref(root, "data")
            self.assertEqual(gate.bound_read(root, reference, 3), b"abc")
            for changed, maximum in ((reference, 2), ({**reference, "sha256": "0" * 64}, 3),
                                     ({**reference, "bytes": 4}, 3)):
                with self.assertRaises(ValueError):
                    gate.bound_read(root, changed, maximum)
            (root / "alias").symlink_to(root / "data")
            os.mkfifo(root / "fifo")
            for name in ("alias", "../data", "fifo", "."):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    gate.bound_read(root, {**reference, "path": name})

    def test_same_content_replacement_during_read_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "data"
            target.write_bytes(b"abc")
            reference = ref(root, "data")
            real = Path.lstat
            calls = 0
            def changed(path, *args, **kwargs):
                nonlocal calls
                if path == target:
                    calls += 1
                    if calls == 2:
                        other = root / "other"
                        other.write_bytes(b"abc")
                        other.replace(target)
                return real(path, *args, **kwargs)
            with patch.object(Path, "lstat", changed), self.assertRaisesRegex(ValueError, "input replaced"):
                gate.bound_read(root, reference)

    def test_FIFO_swap_at_open_is_nonblocking_and_rejected_by_fstat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "data"
            target.write_bytes(b"abc")
            reference = ref(root, "data")
            real = os.open
            def changed(path, flags, *args, **kwargs):
                if Path(path) == target:
                    self.assertTrue(flags & os.O_NONBLOCK)
                    self.assertTrue(flags & os.O_NOFOLLOW)
                    target.unlink()
                    os.mkfifo(target)
                return real(path, flags, *args, **kwargs)
            with patch.object(os, "open", changed), self.assertRaisesRegex(ValueError, "not a regular file"):
                gate.bound_read(root, reference)


class MainTests(unittest.TestCase):
    def test_schema_valid_canonical_shape_runs_exact_synthetic_main(self):
        with main_fixture() as f:
            jsonschema.Draft202012Validator(schema("adaptive-experiment-contract.schema.json")).validate(f.contract)
            jsonschema.Draft202012Validator(schema("adaptive-job.schema.json")).validate(f.job)
            self.assertIn("cgroup_parent", f.job["resource_budget"])
            report = gate.main()
            f.timer.assert_called_once_with(signal.ITIMER_REAL, 120)
            self.assertEqual(f.lab.worker_pid_matches_job.call_count, 2)
            self.assertTrue(report["every_byte_state_agreement"])
            self.assertTrue(report["retained_terminal_state_agreement"])
            self.assertEqual(report["diagnostics"]["inherited_selected_starts"], 1)
            self.assertEqual(report["runtime"], f.plan["runtime"])
            self.assertEqual(report["candidate_revision"], f.candidate)
            self.assertEqual(report["continuous_guard_decision"], "await outer closure")
            self.assertEqual(sorted(p.name for p in f.result.iterdir()), ["report.json"])
            self.assertEqual(json.loads((f.result / "report.json").read_bytes()), report)
            self.assertEqual([json.loads(line)["event"] for line in f.marker.read_text().splitlines()],
                             ["opportunity_scan_start", "opportunity_scan_complete"])
            MAIN_EVIDENCE.append({"kind": "schema-valid-mocked-main", "contract": f.contract,
                                  "execution_plan": f.plan, "job": f.job, "report": report,
                                  "mocked_external_authority": ["lab worker identity", "PPID", "CPU affinity", "cgroup proc/files"],
                                  "real_source_closure_authenticated": True, "real_runtime_authenticated": True})

    def test_metadata_failures_reject_before_population_read(self):
        cases = ("runtime_hash", "runtime_bytes", "runtime_path", "revision_env", "revision_file",
                 "guard_reference", "guard_identity", "job_identity", "budget", "guard_budget",
                 "source_drift", "missing_source", "missing_transitive_source", "plan_missing",
                 "population_in_sources", "cgroup_inode", "cgroup_memory", "guard_parent", "foreign_lab")
        early = {"runtime_hash", "runtime_bytes", "runtime_path", "revision_env", "revision_file",
                 "guard_reference", "job_identity", "budget", "source_drift", "missing_source",
                 "missing_transitive_source", "plan_missing", "population_in_sources"}
        for case in cases:
            with self.subTest(case=case), main_fixture() as f:
                if case == "runtime_hash": f.plan["runtime"]["sha256"] = "0" * 64
                elif case == "runtime_bytes": f.plan["runtime"]["bytes"] += 1
                elif case == "runtime_path": f.plan["runtime"]["path"] = "/bin/false"
                elif case == "revision_env":
                    os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"] = json.dumps({**f.candidate, "candidateId": "other"})
                elif case == "revision_file": (f.root / f.revision_name).write_bytes(b"changed")
                elif case == "guard_reference": f.job["execution_guard"]["sha256"] = "sha256:" + "0" * 64
                elif case == "guard_identity": f.lab.worker_pid_matches_job.return_value = False
                elif case == "job_identity": f.job["job_id"] = "other"
                elif case == "budget":
                    f.job["resource_budget"] = {**f.job["resource_budget"], "scratch_bytes": 1}
                elif case == "guard_budget":
                    f.job["execution_resources"]["budget"] = {**f.job["resource_budget"], "scratch_bytes": 1}
                elif case == "source_drift":
                    path = f.root / gate.LAB
                    path.write_bytes(path.read_bytes() + b"\n")
                elif case == "missing_source": f.plan["source_paths"].remove(gate.LAB)
                elif case == "missing_transitive_source": f.plan["source_paths"].remove("tools/enwiki9_worker_identity.py")
                elif case == "plan_missing":
                    f.contract["inputs"] = [r for r in f.contract["inputs"] if r["path"] != gate.PLAN]
                elif case == "population_in_sources": f.plan["source_paths"].append(f.pop["modeled_path"])
                elif case == "cgroup_inode": f.job["execution_resources"]["cgroup_inode"] += 1
                elif case == "cgroup_memory": f.pseudo[f.group / "memory.max"] = "max"
                elif case == "guard_parent": f.job["worker_pid"] += 1
                elif case == "foreign_lab": f.lab.__file__ = str(f.root / "foreign.py")
                f.refresh()
                with self.assertRaises((ValueError, OSError)):
                    gate.main()
                self.assertFalse((f.result / "report.json").exists())
                self.assertNotIn(f.pop["modeled_path"], f.reads)
                self.assertNotIn(f.pop["dictionary_path"], f.reads)
                if case in early:
                    f.import_call.assert_not_called()
                MAIN_EVIDENCE.append({"kind": "rejected-metadata", "case": case,
                                      "population_read": False, "report_published": False})

    def test_post_scan_input_or_job_change_never_publishes(self):
        for case in ("source", "job"):
            with self.subTest(case=case), main_fixture() as f:
                original = gate.scan
                def change(*args, **kwargs):
                    report = original(*args, **kwargs)
                    path = f.root / gate.OBSERVER if case == "source" else f.job_path
                    path.write_bytes(path.read_bytes() + b"\n")
                    return report
                with patch.object(gate, "scan", side_effect=change), self.assertRaises(ValueError):
                    gate.main()
                self.assertFalse((f.result / "report.json").exists())

    def test_marker_or_final_rename_failure_leaves_no_published_report(self):
        for case in ("marker", "rename"):
            with self.subTest(case=case), main_fixture() as f:
                with ExitStack() as stack:
                    if case == "marker":
                        real = gate.append_marker
                        def fail(marker, event):
                            if event.endswith("complete"):
                                raise OSError("synthetic completion marker failure")
                            return real(marker, event)
                        stack.enter_context(patch.object(gate, "append_marker", side_effect=fail))
                    else:
                        real = Path.replace
                        def fail(path, target):
                            if path.name == "report.tmp":
                                raise OSError("synthetic final rename failure")
                            return real(path, target)
                        stack.enter_context(patch.object(Path, "replace", fail))
                    with self.assertRaises(OSError):
                        gate.main()
                self.assertFalse((f.result / "report.json").exists())
                if case == "rename":
                    self.assertTrue((f.result / "report.tmp").is_file())

    def test_retained_terminal_stats_mismatch_fails_main(self):
        with main_fixture() as f:
            path = f.root / f.pop["terminal_result_path"]
            value = json.loads(path.read_bytes())
            value["program_stats"]["phase"]["adapter"]["selected_values"] += 1
            write_json(path, value)
            for row in f.contract["inputs"]:
                if row["path"] == f.pop["terminal_result_path"]:
                    row.update(ref(f.root, row["path"]))
            f.refresh()
            with self.assertRaisesRegex(ValueError, "retained corpus adapter"):
                gate.main()
            self.assertFalse((f.result / "report.json").exists())

    def test_existing_output_is_preserved_and_prevents_population_read(self):
        with main_fixture() as f:
            path = f.result / "report.json"
            path.write_bytes(b"previous report")
            with self.assertRaisesRegex(ValueError, "output is not empty"):
                gate.main()
            self.assertEqual(path.read_bytes(), b"previous report")
            self.assertNotIn(f.pop["modeled_path"], f.reads)

    def test_wall_alarm_interrupts_blocked_process(self):
        command = [sys.executable, "-B", "-c",
                   "import sys,time,signal;signal.signal(signal.SIGALRM,signal.SIG_IGN);"
                   "sys.path.insert(0,sys.argv[1]);"
                   "import causal_field_opportunity_gate_v2 as g;"
                   "g.arm_wall_deadline(0.05);time.sleep(10)", str(ROOT / "tools")]
        result = subprocess.run(command, capture_output=True, timeout=3)
        self.assertEqual(result.returncode, -signal.SIGALRM)
        MAIN_EVIDENCE.append({"kind": "independent-wall-alarm", "command": command,
                              "returncode": result.returncode, "new_codec_runs": 0})


if __name__ == "__main__":
    unittest.main()
