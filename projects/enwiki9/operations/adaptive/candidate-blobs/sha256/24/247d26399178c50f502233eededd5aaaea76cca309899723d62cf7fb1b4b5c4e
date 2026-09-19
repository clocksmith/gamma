"""Fixed programs cross explicit format/class boundaries without rediscovery."""
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_reserialize_v1 as diag


class ReserializeTests(unittest.TestCase):
    def test_cross_formats_keep_exact_arbitrary_bytes_and_frames(self):
        rng = random.Random(81)
        for raw in (b"", rng.randbytes(97), b"<page>x\xff\r\n&amp;X</page>\n" * 4):
            for source in diag.VERSIONS:
                for mode in ("plain", "split", "grammar", "parameter"):
                    codec = diag.VERSIONS[source]
                    parent, _ = codec.encode(raw, mode=mode, frame_size=41, config=codec.Config(4, 4, 1, 4))
                    for storage in diag.VERSIONS:
                        with self.subTest(size=len(raw), source=source, mode=mode, storage=storage):
                            archive, report = diag.reserialize(parent, storage)
                            self.assertEqual(diag.VERSIONS[storage].decode(archive), raw)
                            self.assertEqual(diag.reserialize(parent, storage), (archive, report))
                            self.assertEqual(diag.reserialize(archive, source)[0], parent)
                            self.assertEqual(report["complete_archive_bytes"], len(archive))
                            self.assertFalse(report["raw_encoder_repeat_proved"])

    def test_private_class_adapter_retains_backward_rules_and_shared_arguments(self):
        old = diag.old
        model = old.Model(structure=(old.Ref(0),), content=(old.Ref(0),),
                          arguments=(b"name\x00 \xff",), phrases=((b"a", b"b"),),
                          templates=((1, (old.Arg(0), b"/", old.Arg(0))),),
                          structure_rules=((("content", 2), ("call", 0)),))
        raw = b"abname\x00 \xff/name\x00 \xff"
        body, _ = old.frame_bytes(raw, "parameter", model)
        parent = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(raw)) + body
        archive, report = diag.reserialize(parent, "new")
        self.assertEqual(diag.new.decode(archive), raw)
        self.assertEqual(diag.reserialize(archive, "old")[0], parent)
        self.assertEqual(report["frames"][0]["model_sha256"], diag.fingerprint(model))
        self.assertEqual(report["frames"][0]["repeated_argument_references"], 1)
        self.assertIsInstance(diag.convert(model, diag.new).content[0], diag.new.Ref)
        self.assertEqual(diag.graph(diag.convert(model, diag.new)), diag.graph(model))

    def test_corruption_and_output_bounds_reject(self):
        parent, _ = diag.old.encode(b"exact\xff\n", mode="split")
        for bad in (parent[:-1], parent + b"x", b"invalid!"):
            with self.assertRaises(ValueError):
                diag.reserialize(bad, "old")
        from unittest.mock import patch
        with patch.object(diag.old, "MAX_ARCHIVE", len(parent) - 1):
            with self.assertRaisesRegex(ValueError, "bound"):
                diag.reserialize(parent, "new")

    def test_unused_declared_rules_are_preserved(self):
        old = diag.old
        model = old.Model(structure=(("literal", b"xx"),), phrases=((b"a", b"b"),),
                          templates=((1, (old.Arg(0),)),))
        body, _ = old.frame_bytes(b"xx", "parameter", model)
        parent = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, 2) + body
        cross, report = diag.reserialize(parent, "new")
        self.assertEqual(report["frames"][0]["templates"], 1)
        self.assertEqual(report["frames"][0]["model_sha256"], diag.fingerprint(model))
        self.assertEqual(diag.reserialize(cross, "old")[0], parent)


if __name__ == "__main__":
    unittest.main()
