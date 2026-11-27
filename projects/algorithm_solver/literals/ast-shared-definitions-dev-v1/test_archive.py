"""Checks for the two distinct types of sharing in SDA1."""
import unittest

import archive
import independent_decode as decode


def expr(tag, *children, atoms=()):
    return ("NODE", "EXPR", tag, atoms, children)


def call(index, *args):
    return ("CALL", "EXPR", index, 0, args)


class ArchiveTests(unittest.TestCase):
    def test_compound_header_applies_an_earlier_definition_and_forwards_a_hole(self):
        left = ("HOLE", "EXPR", "EXPR_BIN_L")
        right = ("HOLE", "EXPR", "EXPR_BIN_R")
        def scan(a, b):
            return expr("UnrolledScan", expr("Guard", expr("Combine", a, b), atoms=("iteration-count",)))
        update = expr("Update", atoms=("index",))
        definitions = (scan(left, right), scan(update, right))
        stats = archive.library_stats(definitions, "dag")
        self.assertGreater(stats["earlier_template_calls"], 0)
        self.assertGreater(stats["concrete_arguments"], 0)
        self.assertGreater(stats["forwarded_holes"], 0)
        flat = archive.encode_library(definitions, "flat")
        dag = archive.encode_library(definitions, "dag")
        self.assertLess(len(dag), len(flat))
        self.assertEqual(decode.decode_library(flat), definitions)
        self.assertEqual(decode.decode_library(dag), definitions)

    def test_header_and_dispatch_change_independently(self):
        pair = expr("Pair", ("HOLE","EXPR","EXPR_BIN_L"), ("HOLE","EXPR","EXPR_BIN_R"))
        definitions = (pair,)
        a, b = expr("Left", atoms=(True,)), expr("Right", atoms=(1,))
        docs = [tuple(call(0, a, b) for _ in range(256)), b"\xffraw"]
        expanded = [tuple(expr("Pair", a, b) for _ in range(256)), docs[1]]
        sizes = {}
        for prior in ("general","hole"):
            model = archive.fit_prior(docs, definitions, prior)
            payload = archive.encode_payload(docs, definitions, model)
            for fmt in ("flat","dag"):
                data, cost = archive.encode_archive(docs, definitions, fmt, model)
                sections = decode.Reader(data[4:-4])
                self.assertEqual(sections.block(), archive.encode_library(definitions, fmt))
                self.assertEqual(sections.block(), model.blob)
                self.assertEqual(sections.block(), payload)
                sections.finish()
                self.assertEqual(len(data), sum(cost[k] for k in ("library_bytes","model_bytes","framing_bytes","payload_bytes")))
                result = decode.decode_archive(data)
                self.assertEqual(result["calls"], docs)
                self.assertEqual(result["documents"], expanded)
            sizes[prior] = len(payload)
        self.assertLess(sizes["hole"], sizes["general"])

    def test_general_backoff_and_literal_escape_for_unseen_labels(self):
        fit = [(expr("Seen"),)]
        docs = [(expr("Unseen", ("NODE","UnknownGroup","Untyped",("é", None, -9),())),), tuple(), b""]
        sizes = []
        for prior in ("general", "hole"):
            model = archive.fit_prior(fit, (), prior)
            data, _ = archive.encode_archive(docs, (), "dag", model)
            sizes.append(len(data))
            self.assertEqual(decode.decode_archive(data)["documents"], docs)
        self.assertEqual(sizes[0], sizes[1])

    def test_node_atom_types_survive_sharing(self):
        defs = (expr("Same", atoms=(True,)), expr("Same", atoms=(1,)))
        for fmt in ("flat","dag"):
            both = decode.decode_library(archive.encode_library(defs, fmt))
            self.assertIs(type(both[0][3][0]), bool)
            self.assertIs(type(both[1][3][0]), int)

    def test_corrupt_archive_and_illegal_header_reference_are_rejected(self):
        model = archive.fit_prior([], (), "general")
        data, _ = archive.encode_archive([], (), "flat", model)
        corrupt = bytearray(data)
        corrupt[-1] ^= 1
        with self.assertRaises(ValueError):
            decode.decode_archive(bytes(corrupt))
        # One definition attempts to apply itself; its ID is not yet available.
        with self.assertRaisesRegex(ValueError, "forward"):
            decode.decode_library(b"SL1\x01\x01\x00\x03\x00")


if __name__ == "__main__":
    unittest.main()
