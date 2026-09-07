#!/usr/bin/env python3
"""Synthetic-only adapter-factory parity and native-framed replay integration."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import causal_field_preceding_adapter250k_v1 as frontend
import fx2_causal_field_preceding_replay_v1 as codec
import fx2_causal_field_replay_v1 as old
from causal_field_parent_coder_v1 import Encoder
from wrt_exact import wrt_byte_transform, parse_store_bytes

RETAIN = Path(os.environ["GAMMA_PRECEDING_INTEGRATION_RETAIN"]) if os.environ.get("GAMMA_PRECEDING_INTEGRATION_RETAIN") else None
EXTRA = {"adapter_policy_id", "adapter_constructor_arm", "decoder_arm_option_bytes"}
VOLATILE = {"operation", "cpu_seconds", "wall_seconds", "peak_rss_kib", "pid"}
RAW = (b"{{t|anchor=fixed|decoy=x|kind=p|v=aaaaaaaa}}"
       b"{{t|anchor=fixed|decoy=x|kind=q|v=bbbbbbbb}}"
       b"{{t|anchor=fixed|decoy=y|kind=p|v=aaaaaaaa}}")
SOURCE_PATHS = ["tools/causal_field_preceding_adapter250k_v1.py",
    "tools/fx2_causal_field_preceding_replay_v1.py", "tests/test_fx2_causal_field_preceding_replay_v1.py",
    "tools/causal_field_preceding_selector_v1.py", "tools/causal_field_wrt_adapter_v1.py",
    "tools/causal_field_dependency_v1.py", "tools/wrt_exact.py",
    "tools/causal_field_parent_coder_v1.py", "tools/fx2_causal_field_replay_v1.py"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def code(*values):
    return bytes(wrt_byte_transform(value) for value in values)


def literals(raw):
    return b"".join(code(12, byte) if byte >= 128 or byte in (6, 7, 12, 64) else code(byte) for byte in raw)


def fixture(raw, *, modeled=None, words=()):
    assert len(raw) <= 8192, "synthetic fixture raw bound"
    modeled = b"\7" + literals(raw) if modeled is None else modeled
    prefix = b"GFV1\7" + len(raw).to_bytes(4, "big") + ((1 << 39) + len(modeled)).to_bytes(5, "big") + b"\xff" * 32
    # Declared by index alone; no raw truth or future symbol enters this parent.
    q16 = b"".join(struct.pack("<H", 16000 + (index * 19) % 30000) for index in range(len(modeled) * 8))
    stored = b"\x80\0\0\0\0\7" + len(raw).to_bytes(4, "big") + modeled
    assert parse_store_bytes(stored, list(words)).decoded == raw
    return modeled, dict(q16=q16, prefix=prefix, words=list(words), raw_bytes=len(raw), raw_sha256=sha(raw))


def source_rows():
    return [{"path": path, "bytes": (ROOT / path).stat().st_size,
             "sha256": sha((ROOT / path).read_bytes())} for path in SOURCE_PATHS]


def retain_sources(directory):
    directory.mkdir(parents=True, exist_ok=False)
    rows = source_rows()
    for row in rows:
        target = directory / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / row["path"]).read_bytes())
    (directory / "inventory.json").write_bytes(canonical(rows))
    return rows


def retain_fixture(name, raw, modeled, options):
    if RETAIN is None:
        return None
    path = RETAIN / name
    path.mkdir(exist_ok=False)
    (path / "raw.bin").write_bytes(raw)
    (path / "modeled.bin").write_bytes(modeled)
    (path / "q16.bin").write_bytes(options["q16"])
    (path / "prefix.bin").write_bytes(options["prefix"])
    (path / "dictionary.json").write_bytes(canonical([word.hex() for word in options["words"]]))
    (path / "fixture.json").write_bytes(canonical({"raw_bytes": len(raw), "raw_sha256": sha(raw),
        "modeled_bytes": len(modeled), "modeled_sha256": sha(modeled),
        "q16_recipe": "little-endian Q16=16000+(bit_index*19)%30000; independent of truth",
        "corpus_bytes": 0, "parent_probability_dependency": True}))
    return path


def retained_replay(directory, name, module, operation, body, options, arm, **extra):
    if directory is not None:
        destination = directory / name
        destination.mkdir()
        retain_sources(destination / "source")
        (destination / "input.bin").write_bytes(body)
        (destination / "invocation.json").write_bytes(canonical({"module": module.__name__,
            "operation": operation, "arm": arm, "factory": "legacy" if extra else "default",
            "body_sha256": sha(body), "raw_bytes": options["raw_bytes"], "raw_sha256": options["raw_sha256"],
            "q16_sha256": sha(options["q16"]), "prefix_hex": options["prefix"].hex()}))
    output, sync, report = module.replay(operation, body, arm=arm, **options, **extra)
    if directory is not None:
        (destination / "output.bin").write_bytes(output)
        (destination / "state-chain.bin").write_bytes(sync)
        (destination / "report.json").write_bytes(canonical(report))
    return output, sync, report


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proofs = {"legacy_factory_arms": [], "main_arms": {}, "cli_phases": [], "future_prefix_boundaries": 0}

    def setUp(self):
        if RETAIN is not None:
            retain_sources(RETAIN / "before-tests" / self._testMethodName)

    @classmethod
    def tearDownClass(cls):
        if RETAIN is not None:
            (RETAIN / "proofs.json").write_bytes(canonical(cls.proofs))

    def test_01_wrapper_bound_identity_and_factory_routes(self):
        self.assertEqual(frontend.SELECTOR_SHA256, sha((ROOT / "tools/causal_field_preceding_selector_v1.py").read_bytes()))
        self.assertEqual(frontend.Adapter.start_value, frontend.selector.Adapter.start_value)
        self.assertEqual(frontend.Adapter.commit, frontend.selector.Adapter.commit)
        for arm in "PKTORS":
            adapter = frontend.make_adapter([], arm=arm, raw_limit=250000)
            self.assertEqual(adapter.raw_limit, 250000)
            self.assertEqual(adapter.arm, "T" if arm == "O" else arm)
            self.assertEqual(type(adapter), frontend.original.Adapter if arm in "PO" else frontend.Adapter)
        for invalid in (-1, 250001, True, 1.0):
            with self.assertRaises(ValueError):
                frontend.Adapter([], raw_limit=invalid)
        with self.assertRaises(ValueError):
            frontend.selector.Adapter([], raw_limit=8193)
        for arm in ("P", "O", "X", "TR", None):
            with self.assertRaises(ValueError):
                frontend.Adapter([], arm=arm)
        self.assertNotEqual(frontend.POLICY, frontend.selector.POLICY)

    def test_02_replay_loop_is_old_loop_with_explicit_factory_and_O_only(self):
        def function(path):
            return next(node for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == "replay")
        actual = function(ROOT / "tools/fx2_causal_field_preceding_replay_v1.py")
        expected = function(ROOT / "tools/fx2_causal_field_replay_v1.py")
        actual.args.kwonlyargs, actual.args.kw_defaults = [], []
        class Normalize(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id == "adapter_factory":
                    node.id = "Adapter"
                return node
            def visit_Constant(self, node):
                if node.value == "TORS":
                    node.value = "TRS"
                return node
            def visit_Dict(self, node):
                self.generic_visit(node)
                retained = [(key, value) for key, value in zip(node.keys, node.values)
                            if not isinstance(key, ast.Constant) or key.value not in EXTRA]
                node.keys, node.values = [key for key, _ in retained], [value for _, value in retained]
                return node
        self.assertEqual(ast.dump(Normalize().visit(actual)), ast.dump(expected))

    def test_03_legacy_factory_all_five_arms_exact_old_replay(self):
        raw = b"{{t|a=x|v=aaaa}}{{t|a=y|v=bbbb}}{{t|a=x|v=aaaa}}"
        modeled, options = fixture(raw)
        directory = retain_fixture("legacy-factory", raw, modeled, options)
        global_adapter = old.Adapter
        for arm in "PKTRS":
            original = retained_replay(directory, arm + "-old", old, "encode", modeled, options, arm)
            new = retained_replay(directory, arm + "-factory", codec, "encode", modeled, options, arm,
                                  adapter_factory=old.Adapter)
            self.assertEqual(original[:2], new[:2])
            self.assertEqual(original[2], {key: value for key, value in new[2].items() if key not in EXTRA})
            inverse, decoded_sync, decoded = codec.replay("decode", new[0], arm=arm, **options, adapter_factory=old.Adapter)
            self.assertEqual((inverse, decoded_sync, decoded), (raw, new[1], new[2]))
            self.proofs["legacy_factory_arms"].append({"arm": arm, "boundaries": len(modeled),
                "archive_sha256": sha(new[0]), "probability_digest": new[2]["probability_digest"],
                "synchronization_file_sha256": sha(new[1])})
        self.assertIs(old.Adapter, global_adapter)

    def test_04_default_P_and_O_are_exact_original_P_and_T(self):
        modeled, options = fixture(RAW)
        directory = retain_fixture("original-P-O", RAW, modeled, options)
        for arm, parent_arm in (("P", "P"), ("O", "T")):
            actual = retained_replay(directory, arm + "-new", codec, "encode", modeled, options, arm)
            expected = retained_replay(directory, arm + "-old", old, "encode", modeled, options, parent_arm)
            self.assertEqual(actual[:2], expected[:2])
            normalized = {key: value for key, value in actual[2].items() if key not in EXTRA}
            normalized["arm"] = parent_arm
            self.assertEqual(normalized, expected[2])
            self.assertEqual(actual[2]["adapter_constructor_arm"], parent_arm)
            self.assertEqual(actual[2]["adapter_policy_id"], frontend.ORIGINAL_POLICY)
        self.assertGreater(actual[2]["changed_probability_bits"], 0)
        self.proofs["original_O_active_and_exact_previous_T"] = True

    def test_05_six_arm_framed_inverse_repeat_probability_and_state(self):
        modeled, options = fixture(RAW)
        directory = retain_fixture("six-arm", RAW, modeled, options)
        results = {}
        for arm in "PKTORS":
            archive, sync, report = retained_replay(directory, arm + "-encode", codec, "encode", modeled, options, arm)
            raw, decoded_sync, decoded = retained_replay(directory, arm + "-decode", codec, "decode", archive, options, arm)
            repeat = retained_replay(directory, arm + "-repeat", codec, "repeat", modeled, options, arm)
            self.assertEqual(raw, RAW)
            self.assertEqual((archive, sync, report), repeat)
            self.assertEqual((sync, report), (decoded_sync, decoded))
            self.assertEqual(len(sync), 32 * len(modeled))
            self.assertEqual(sync[-32:].hex(), report["synchronization_digest"])
            self.assertEqual(archive[:46], options["prefix"])
            self.assertEqual(len(archive), 46 + report["payload_bytes"])
            self.assertEqual(report["decoder_arm_option_bytes"], 1)
            self.assertFalse(report["standalone_decoder"])
            self.assertIsNone(report["complete_package_bytes"])
            results[arm] = (archive, report)
            self.proofs["main_arms"][arm] = report
        self.assertEqual(results["P"][0], results["K"][0])
        self.assertEqual(results["P"][1]["probability_digest"], results["K"][1]["probability_digest"])
        self.assertEqual(codec.replay("decode", results["K"][0], arm="P", **options)[0], RAW)
        for arm in "TORS":
            self.assertGreater(results[arm][1]["changed_probability_bits"], 0)
        self.assertNotEqual(results["T"][1]["probability_digest"], results["O"][1]["probability_digest"])

    def test_06_two_field_probability_archive_equivalence_and_explicit_policy(self):
        raw = b"{{t|kind=x|v=aaaa}}{{t|kind=y|v=bbbb}}{{t|kind=x|v=aaaa}}"
        modeled, options = fixture(raw)
        for arm in "KTRS":
            archive, _, report = codec.replay("encode", modeled, arm=arm, **options)
            parent, _, previous = old.replay("encode", modeled, arm=arm, **options)
            self.assertEqual(archive, parent)
            self.assertEqual(report["probability_digest"], previous["probability_digest"])
            self.assertNotEqual(report["adapter_state_digest"], previous["adapter_state_digest"])
            self.assertEqual(report["adapter_policy_id"], frontend.POLICY)

    def test_07_future_suffix_does_not_change_common_boundary_state(self):
        common = RAW[:-10]
        raw_variants = [common + b"aaaaaaaa}}", common + b"bbbbbbbb}}", common + b"{{u|v=x}}}"]
        self.assertEqual(len({len(raw) for raw in raw_variants}), 1)
        for arm in "PKTORS":
            baseline = None
            for raw in raw_variants:
                modeled, options = fixture(raw)
                _, sync, _ = codec.replay("encode", modeled, arm=arm, **options)
                prefix_sync = sync[:(len(literals(common)) + 1) * 32]
                if baseline is None:
                    baseline = prefix_sync
                self.assertEqual(prefix_sync, baseline)
                self.proofs["future_prefix_boundaries"] += len(prefix_sync) // 32

    def test_08_native_finite_parent_payload_equals_direct_encoder(self):
        raw = b"{{t|kind=x|v=abc}}"
        modeled, options = fixture(raw)
        for probabilities in (options["q16"], b"\1\0\xff\xff" * (len(modeled) * 4)):
            options["q16"] = probabilities
            encoder = Encoder(max_bits=len(modeled) * 8)
            for index, (q,) in enumerate(struct.iter_unpack("<H", probabilities)):
                encoder.encode((modeled[index // 8] >> (7 - index % 8)) & 1, q)
            archive, sync, report = codec.replay("encode", modeled, arm="P", **options)
            self.assertEqual(archive, options["prefix"] + encoder.finish())
            self.assertEqual(codec.replay("decode", archive, arm="P", **options), (raw, sync, report))

    def test_09_nonempty_dictionary_controls_and_token_boundaries(self):
        words = [b"alpha", b"beta"]
        first = literals(b"{{t|id=A|kind=x|v=") + code(64, 128, 6) + literals(b"}}")
        second = literals(b"{{t|id=B|kind=y|v=") + code(129) + literals(b"}}")
        third = literals(b"{{t|id=C|kind=x|v=") + code(64, 128, 6) + literals(b"}}")
        raw = b"{{t|id=A|kind=x|v=Alpha}}{{t|id=B|kind=y|v=beta}}{{t|id=C|kind=x|v=Alpha}}"
        modeled, options = fixture(raw, modeled=b"\7" + first + second + third, words=words)
        directory = retain_fixture("nonempty-dictionary", raw, modeled, options)
        for arm in "PKTORS":
            archive, sync, report = retained_replay(directory, arm + "-encode", codec, "encode", modeled, options, arm)
            self.assertEqual(retained_replay(directory, arm + "-decode", codec, "decode", archive, options, arm),
                             (raw, sync, report))

    def test_10_malformed_archive_and_population_bounds_reject(self):
        modeled, options = fixture(RAW)
        archive, _, _ = codec.replay("encode", modeled, arm="T", **options)
        for bad in (archive[:-1], archive + b"\0", archive[:46] + bytes([archive[46] ^ 128]) + archive[47:],
                    archive[:45], b"\0" + archive[1:]):
            with self.assertRaises(ValueError):
                codec.replay("decode", bad, arm="T", **options)
        for changes in ({"raw_sha256": "0" * 64}, {"raw_bytes": 250001}, {"raw_bytes": True},
                        {"q16": options["q16"][:-2]}, {"q16": b"\0\0" + options["q16"][2:]},
                        {"prefix": options["prefix"][:14] + b"\0" * 32}):
            with self.assertRaises(ValueError):
                codec.replay("encode", modeled, arm="T", **{**options, **changes})
        for arm in ("", "TO", "X"):
            with self.assertRaises(ValueError):
                codec.replay("encode", modeled, arm=arm, **options)

    def test_11_all_raw_bytes_and_invalid_invocations_roundtrip(self):
        raw = bytes(range(256)) + b"{{t|id=A|kind=x|v=mmm|id=duplicate}}{{t|id=A|kind=x|v={{u|v=q}}}}"
        modeled, options = fixture(raw)
        for arm in "PKTORS":
            archive, sync, report = codec.replay("encode", modeled, arm=arm, **options)
            self.assertEqual(codec.replay("decode", archive, arm=arm, **options), (raw, sync, report))
            self.assertEqual(report["adapter"]["associations_committed"], 0)

    def test_12_factory_is_called_explicitly_without_mutating_old_globals(self):
        modeled, options = fixture(b"abc")
        seen = []
        original = old.Adapter
        def factory(words, *, arm, raw_limit):
            seen.append((words, arm, raw_limit))
            return old.Adapter(words, arm=arm, raw_limit=raw_limit)
        codec.replay("encode", modeled, arm="P", adapter_factory=factory, **options)
        self.assertEqual(seen, [([], "P", 3)])
        self.assertIs(old.Adapter, original)

    def test_13_eighteen_independent_cli_phases_and_legacy_O_process(self):
        if RETAIN is None:
            self.skipTest("durable evidence path required for independent CLI phases")
        modeled, options = fixture(RAW)
        tree = retain_fixture("cli", RAW, modeled, options)
        dictionary = tree / "dictionary.bin"
        dictionary.write_bytes(b"")
        cli = ROOT / "tools/fx2_causal_field_preceding_replay_v1.py"
        reports = {}
        for arm in "PKTORS":
            arm_root = tree / arm
            arm_root.mkdir()
            projections = []
            for operation in ("encode", "decode", "repeat"):
                snapshots = retain_sources(arm_root / (operation + "-source"))
                body = arm_root / "encode.bin" if operation == "decode" else tree / "modeled.bin"
                output, sync = arm_root / (operation + ".bin"), arm_root / (operation + ".sync")
                command = [sys.executable, "-B", str(cli), operation, str(body), str(output), "--sync", str(sync),
                    "--q16", str(tree / "q16.bin"), "--dictionary", str(dictionary), "--arm", arm,
                    "--prefix", options["prefix"].hex(), "--raw-bytes", str(len(RAW)), "--raw-sha256", sha(RAW)]
                receipt = {"command": command, "sources_before": snapshots, "input": str(body),
                    "input_bytes": body.stat().st_size, "input_sha256": sha(body.read_bytes()),
                    "q16_sha256": sha(options["q16"]), "dictionary_sha256": sha(b""),
                    "decoder_inputs": [str(body), str(tree / "q16.bin"), str(dictionary)] if operation == "decode" else None,
                    "scope": "synthetic-only", "corpus_bytes": 0}
                (arm_root / (operation + "-command.json")).write_bytes(canonical(receipt))
                started = time.monotonic()
                with (arm_root / (operation + ".stdout")).open("wb") as stdout, (arm_root / (operation + ".stderr")).open("wb") as stderr:
                    process = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=120,
                                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                receipt.update({"returncode": process.returncode, "wall_seconds": time.monotonic() - started,
                                "sources_after": source_rows()})
                (arm_root / (operation + "-execution.json")).write_bytes(canonical(receipt))
                self.assertEqual(process.returncode, 0)
                self.assertEqual(receipt["sources_before"], receipt["sources_after"])
                report = json.loads((arm_root / (operation + ".stdout")).read_bytes())
                self.assertEqual(report["cpu_affinity"], [4])
                self.assertEqual(report["source_sha256"], sha(cli.read_bytes()))
                projections.append({key: value for key, value in report.items() if key not in VOLATILE})
                self.proofs["cli_phases"].append({"arm": arm, "operation": operation,
                    "cpu_seconds": report["cpu_seconds"], "wall_seconds": report["wall_seconds"],
                    "process_wall_seconds": receipt["wall_seconds"], "peak_rss_kib": report["peak_rss_kib"],
                    "pid": report["pid"], "archive_bytes": report["archive_bytes"],
                    "probability_digest": report["probability_digest"], "state_chain_sha256": sha(sync.read_bytes())})
            self.assertEqual(projections[0], projections[1])
            self.assertEqual(projections[0], projections[2])
            self.assertEqual((arm_root / "encode.bin").read_bytes(), (arm_root / "repeat.bin").read_bytes())
            self.assertEqual((arm_root / "decode.bin").read_bytes(), RAW)
            self.assertEqual((arm_root / "encode.sync").read_bytes(), (arm_root / "decode.sync").read_bytes())
            self.assertEqual((arm_root / "encode.sync").read_bytes(), (arm_root / "repeat.sync").read_bytes())
            reports[arm] = projections[0]
        self.assertEqual((tree / "P/encode.bin").read_bytes(), (tree / "K/encode.bin").read_bytes())
        # An additional original CLI process proves O parity beyond shared imports.
        legacy = tree / "legacy-T"
        legacy.mkdir()
        retain_sources(legacy / "source")
        command = [sys.executable, "-B", str(ROOT / "tools/fx2_causal_field_replay_v1.py"), "encode",
            str(tree / "modeled.bin"), str(legacy / "archive.bin"), "--sync", str(legacy / "state.sync"),
            "--q16", str(tree / "q16.bin"), "--dictionary", str(dictionary), "--arm", "T",
            "--prefix", options["prefix"].hex(), "--raw-bytes", str(len(RAW)), "--raw-sha256", sha(RAW)]
        (legacy / "command.json").write_bytes(canonical(command))
        started = time.monotonic()
        with (legacy / "stdout").open("wb") as stdout, (legacy / "stderr").open("wb") as stderr:
            process = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=120)
        (legacy / "execution.json").write_bytes(canonical({"returncode": process.returncode,
            "wall_seconds": time.monotonic() - started, "command": command, "sources_after": source_rows()}))
        self.assertEqual(process.returncode, 0)
        report = json.loads((legacy / "stdout").read_bytes())
        self.assertEqual((legacy / "archive.bin").read_bytes(), (tree / "O/encode.bin").read_bytes())
        self.assertEqual((legacy / "state.sync").read_bytes(), (tree / "O/encode.sync").read_bytes())
        self.assertEqual(report["probability_digest"], reports["O"]["probability_digest"])
        self.assertEqual(report["adapter_state_digest"], reports["O"]["adapter_state_digest"])
        self.proofs["original_T_cli"] = {key: report[key] for key in
            ("cpu_seconds", "wall_seconds", "peak_rss_kib", "archive_bytes", "archive_sha256",
             "probability_digest", "synchronization_digest", "adapter_state_digest")}


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=True)
