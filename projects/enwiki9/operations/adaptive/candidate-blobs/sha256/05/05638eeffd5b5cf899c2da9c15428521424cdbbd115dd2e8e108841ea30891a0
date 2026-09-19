"""Synthetic argument-binding controls; no corpus or objective-score evidence.

Recipe: 64 eight-letter words derived from SHA-256; Random(9183) selects
16 words for each of 32 values. Each value occurs twice in one XML page.
The 10,560 raw bytes hash to RAW_SHA256 below. Shared and unshared programs
retain identical output, literal spellings, root order, and frame partition.
Only argument arity, argument references, and supplied bindings change.
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as legacy
from tools import dualstream_grammar_argtokens_v2 as argtokens

RAW_SHA256 = "de785feaabefd6bab78995553ec7fe6782925cf2338fa0af6b5a31a0aaa9c4f0"
ACCOUNTING_KEYS = (
    "literal_definition_bytes", "structure_bytes", "content_bytes",
    "argument_reference_bytes", "exception_bytes", "framing_bytes",
)


def synthetic_raw():
    rng = random.Random(9183)
    vocabulary = tuple(
        bytes(97 + value % 26 for value in hashlib.sha256(str(i).encode()).digest()[:8])
        for i in range(64)
    )
    values = tuple(b" ".join(rng.choices(vocabulary, k=16)) for _ in range(32))
    return b"".join(
        b"<page><field>" + value + b"</field><field>" + value
        + b"</field></page>\n" for value in values
    )


def matched_models(codec, raw):
    """Construct module-native nodes, preserving its Ref/Arg class identity."""
    chunks = codec.records(raw)
    template, uses = next(
        (template, uses)
        for template, uses in codec.template_proposals(chunks)
        if template[0] == 1
        and sum(isinstance(node, codec.Arg) for node in template[1]) == 2
    )
    shared = codec.model_for(
        chunks, [(index, (0, values)) for index, values in uses], [template]
    )
    independent_indices = iter(range(2))
    unshared = replace(
        shared,
        arguments=tuple(value for value in shared.arguments for _ in range(2)),
        templates=((2, tuple(
            codec.Arg(next(independent_indices)) if isinstance(node, codec.Arg) else node
            for node in template[1]
        )),),
    )
    return shared, unshared


def complete_archive(codec, raw, model):
    frame, report = codec.frame_bytes(raw, "parameter", model)
    header = codec.HEADER.pack(codec.MAGIC, codec.MAX_FRAME, 1, len(raw))
    return header + frame, report


def synthetic_measurements():
    """Emit reproducible synthetic costs for the parent diagnostic receipt."""
    raw = synthetic_raw()
    result = {
        "evidence_class": "synthetic_diagnostic",
        "recipe": "sha256_64_words_random9183_32_values_16_words_two_fields",
        "raw_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "frame_size": legacy.MAX_FRAME,
        "frames": 1,
        "python_version": sys.version.split()[0],
        "zlib_runtime_version": legacy.zlib.ZLIB_RUNTIME_VERSION,
        "package_bytes": None,
        "full_corpus_score_bytes": None,
        "arms": {},
    }
    for name, codec in (("v1", legacy), ("v2", argtokens)):
        arms = {}
        for label, model in zip(("shared", "unshared"), matched_models(codec, raw)):
            archive, report = complete_archive(codec, raw, model)
            repeated, repeated_report = complete_archive(codec, raw, model)
            accounting = {key: report[key] for key in ACCOUNTING_KEYS}
            accounting["framing_bytes"] += codec.HEADER.size
            arms[label] = {
                "complete_archive_bytes": len(archive),
                "archive_sha256": hashlib.sha256(archive).hexdigest(),
                "accounting": accounting,
                "exact_inverse": codec.decode(archive) == raw,
                "fixed_program_repeat": (archive, report) == (repeated, repeated_report),
                "supplied_arguments": len(model.arguments),
                "template_arity": model.templates[0][0],
                "template_argument_uses": sum(
                    isinstance(node, codec.Arg) for node in model.templates[0][1]
                ),
            }
        auto, report = codec.encode(raw, mode="auto")
        repeated, repeated_report = codec.encode(raw, mode="auto")
        frame = report["frames"][0]
        arms["auto"] = {
            "complete_archive_bytes": len(auto),
            "archive_sha256": hashlib.sha256(auto).hexdigest(),
            "exact_inverse": codec.decode(auto) == raw,
            "raw_encoder_repeat": (auto, report) == (repeated, repeated_report),
            "selected_mode": frame["mode"],
            "templates": frame["templates"],
            "supplied_arguments": frame["supplied_arguments"],
            "repeated_argument_references": frame["repeated_argument_references"],
        }
        arms["shared_binding_bytes_saved"] = (
            arms["unshared"]["complete_archive_bytes"]
            - arms["shared"]["complete_archive_bytes"]
        )
        result["arms"][name] = arms
    result["plain_complete_archive_bytes"] = len(legacy.encode(raw, mode="plain")[0])
    return result


class SyntheticSelectionDiagnosticTest(unittest.TestCase):
    def test_matched_shared_binding_pays_complete_archive_cost(self):
        raw = synthetic_raw()
        self.assertEqual(len(raw), 10560)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), RAW_SHA256)
        for codec in (legacy, argtokens):
            with self.subTest(codec=codec.__name__):
                shared, unshared = matched_models(codec, raw)
                self.assertEqual(len(shared.arguments), 32)
                self.assertEqual(len(unshared.arguments), 64)
                for field in ("structure", "content", "phrases", "structure_rules"):
                    self.assertEqual(getattr(shared, field), getattr(unshared, field))
                self.assertEqual(shared.arguments, unshared.arguments[::2])
                self.assertEqual(shared.arguments, unshared.arguments[1::2])
                shared_sections = codec.packed_sections(shared)
                unshared_sections = codec.packed_sections(unshared)
                for index in (0, 2, 3):
                    self.assertEqual(shared_sections[index], unshared_sections[index])
                archives = []
                for model in (shared, unshared):
                    archive, report = complete_archive(codec, raw, model)
                    self.assertEqual(codec.decode(archive), raw)
                    self.assertEqual(complete_archive(codec, raw, model), (archive, report))
                    self.assertEqual(
                        report["complete_archive_bytes"] + codec.HEADER.size, len(archive)
                    )
                    self.assertEqual(
                        sum(report[key] for key in ACCOUNTING_KEYS) + codec.HEADER.size,
                        len(archive),
                    )
                    archives.append(archive)
                self.assertLess(len(archives[0]), len(archives[1]))

    def test_v2_auto_discovers_the_shared_binding_and_it_pays(self):
        raw = synthetic_raw()
        archive, report = argtokens.encode(raw, mode="auto")
        self.assertEqual(argtokens.decode(archive), raw)
        self.assertEqual(argtokens.encode(raw, mode="auto"), (archive, report))
        self.assertEqual(report["complete_archive_bytes"], len(archive))
        self.assertEqual(sum(report[key] for key in ACCOUNTING_KEYS), len(archive))
        frame = report["frames"][0]
        self.assertEqual(frame["mode"], "parameter")
        self.assertEqual(frame["templates"], 1)
        self.assertEqual(frame["supplied_arguments"], 32)
        self.assertEqual(frame["repeated_argument_references"], 32)
        shared, unshared = matched_models(argtokens, raw)
        self.assertEqual(archive, complete_archive(argtokens, raw, shared)[0])
        self.assertLess(len(archive), len(complete_archive(argtokens, raw, unshared)[0]))
        self.assertLess(len(archive), len(argtokens.encode(raw, mode="plain")[0]))
        self.assertLess(len(archive), len(argtokens.encode(raw, mode="grammar")[0]))


if __name__ == "__main__":
    unittest.main()
