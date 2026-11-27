"""Scope and argument regressions on hand-predicted lexical relationships."""

import unittest

import archive
from independent_decode import decode_archive
import patterns
from sources import named_ast, normalize, verify_documents


def program(source):
    return normalize([{"id": "case", "lineage": "fixture"}], [source])[0]


def walk(tree):
    yield tree
    for child in tree[4]:
        yield from walk(child)


class LexicalPatternsTest(unittest.TestCase):
    def test_block_shadowing_restores_outer_binding(self):
        doc = program("function f(x){let keep=x;{let x=keep; use(x,keep);}use(x,keep);}")
        body = named_ast(doc.tree)["body"][0]["body"]["body"]
        inner_call = body[1]["body"][1]["expr"]
        outer_call = body[2]["expr"]
        self.assertEqual(["v2", "v1"], [a["name"] for a in inner_call["args"]])
        self.assertEqual(["v0", "v1"], [a["name"] for a in outer_call["args"]])
        inside, outside = (n for n in walk(doc.tree[0]) if n[2] == "Call")
        self.assertIsNone(patterns.match(inside, outside))
        self.assertEqual([doc.normalized], verify_documents([doc], [doc.tree]))

    def test_nested_function_can_capture_its_outer_parameter(self):
        doc = program("function f(x){return function(y){return y+x;};}")
        target = named_ast(doc.tree)["body"][0]
        outer_name = target["params"][0]["name"]
        inner = target["body"]["body"][0]["arg"]
        inner_name = inner["params"][0]["name"]
        add = inner["body"]["body"][0]["arg"]
        self.assertNotEqual(outer_name, inner_name)
        self.assertEqual((inner_name, outer_name), (add["left"]["name"], add["right"]["name"]))

    def test_far_registers_free_names_and_property_keys_are_literal(self):
        doc = program("function f(a,b,c,d,e,g,h,i,j){return [a,j,lib.x];}")
        array = next(n for n in walk(doc.tree[0]) if n[2] == "ArrayExpr")
        far, near, prop = array[4]
        self.assertEqual(("RegFar", (8,)), far[2:4])
        self.assertEqual(("Reg8", (0,)), near[2:4])
        self.assertIsNone(patterns.match(far, near))
        self.assertIsNone(patterns.match(near, far))
        self.assertIsNone(patterns.match(far, (*far[:3], (16,), ())))
        self.assertIsNone(patterns.match(prop, (*prop[:3], (False, "y"), prop[4])))
        self.assertIsNone(patterns.match(prop[4][0], near))
        self.assertEqual([doc.normalized], verify_documents([doc], [doc.tree]))
        wrong_array = (*array[:4], (near, near, prop))
        top, = doc.tree
        old_return = top[4][-1]
        changed = (*top[:4], (*top[4][:-1], (*old_return[:4], (wrong_array,))))
        with self.assertRaisesRegex(ValueError, "named AST differs"):
            verify_documents([doc], [(changed,)])

    def test_positional_typed_holes_and_shift(self):
        doc = program("function f(a,b){return a+(b+a);}")
        outer, inner = (n for n in walk(doc.tree[0]) if n[2] == "Binary")
        reg0 = ("NODE", "EXPR", "Reg8", (0,), ())
        right = ("HOLE", "EXPR", "EXPR_BIN_R")
        tpl = (*outer[:4], (reg0, right))
        self.assertEqual((1, (inner,)), patterns.match(tpl, outer))
        self.assertEqual((0, (inner[4][1],)), patterns.match(tpl, inner))
        for bad in [("HOLE", "EXPR", "EXPR_BIN_L"), ("HOLE", "STMT", "EXPR_BIN_R")]:
            self.assertIsNone(patterns.match((*tpl[:4], (reg0, bad)), outer))
        self.assertTrue(all(patterns.match(t, outer) is not None for t in patterns.templates(outer)))

    def test_nested_calls_keep_arguments_in_their_original_scope(self):
        doc = program("function f(a,b){return a+(b+a);}")
        top, = doc.tree
        ret = top[4][-1]
        outer, = ret[4]
        reg0 = ("NODE", "EXPR", "Reg8", (0,), ())
        template = (*outer[:4], (reg0, ("HOLE", "EXPR", "EXPR_BIN_R")))
        shift, (inner,) = patterns.match(template, outer)
        subshift, args = patterns.match(template, inner)
        nested = ("CALL", "EXPR", 0, subshift, args)
        call = ("CALL", "EXPR", 0, shift, (nested,))
        covered = (*top[:4], (*top[4][:-1], (*ret[:4], (call,))))
        fixed_calls = [(covered,)]
        for prior in ("general", "hole"):
            model = archive.fit_prior(fixed_calls, (template,), prior)
            for header in ("flat", "dag"):
                with self.subTest(prior=prior, header=header):
                    blob, _ = archive.encode_archive(fixed_calls, (template,), header, model)
                    decoded = decode_archive(blob)
                    self.assertEqual(fixed_calls, decoded["calls"])
                    self.assertEqual([doc.normalized], verify_documents([doc], decoded["documents"]))

    def test_out_of_scope_reference_fails_independent_decoder(self):
        tree = (("NODE", "STMT", "Return", (True,), (("NODE", "EXPR", "Reg8", (7,), ()),)),)
        with self.assertRaisesRegex(Exception, "illegal register index"):
            named_ast(tree)


if __name__ == "__main__":
    unittest.main()
