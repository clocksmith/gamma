"""Invented source and inputs only. No private population or case access."""
import ast
import json
import unittest
import render


def execute(text,*args):
    namespace={}
    exec(compile(text,'candidate.py','exec'),namespace)
    return namespace['solve'](*args)


class RenderTests(unittest.TestCase):
    def same(self,text,inputs):
        result=render.menu(text)
        self.assertIsNone(result['unsupported'])
        self.assertEqual(result['candidates']['original'],text)
        self.assertLessEqual(len(result['candidates']),6)
        self.assertGreater(len(result['candidates']),1)
        expected=[execute(text,*a) for a in inputs]
        for source in result['candidates'].values():
            self.assertTrue(render.validate(text,source))
            self.assertEqual(render.literal_profile(text),render.literal_profile(source))
            self.assertTrue(set(source)<=render.ALPHABET)
            self.assertEqual([execute(source,*a) for a in inputs],expected)
        return result

    def test_nested_indentation_comments_comprehensions_and_operators(self):
        text='''# unrelated comment

def solve(values):
    result = []
    for x in values:
        if x is not None and x not in (0, 1):
            result.append(- -x + 1)
        else:
            result.append(0)
    return [x ** 2 for x in result if x >= 0]
'''
        r=self.same(text,[([None,0,1,2,-3],),([],),([7,8],)])
        self.assertIn('compact_original_indent1',r['candidates'])
        self.assertIn('compact_original_indent2',r['candidates'])

    def test_number_string_spelling_and_debug_fstring_labels(self):
        text='''def solve(x):
    value = 0x0_F + 1_000 + 1.00e+02
    raw = r"\\n\\x61"
    escaped = "\\u0061\\x62"
    return value, raw, escaped, f"{ x = }/{x!r:>4}"
'''
        r=self.same(text,[(3,),(-12,),('z',)])
        self.assertIn('unparse',r['candidates'])
        for source in r['candidates'].values():
            self.assertIn('f"{ x = }/{x!r:>4}"',source)
            self.assertIn('0x0_F',source)
            self.assertIn('"\\u0061\\x62"',source)

    def test_multiline_and_adjacent_strings_keep_literal_bytes(self):
        text='''def solve(x):
    """a docstring
       whose indentation is data
    """
    a = ('first'
         # internal concatenation comment
         'second')
    b = """line1
        line2
"""
    return a, b, x
'''
        self.same(text,[(3,),('x',)])

    def test_nested_formatted_strings_and_lambda(self):
        text='''def solve(x):
    fn = lambda v: v + 1
    return f"outer {f'{fn(x)=}'}", fn(x)
'''
        self.same(text,[(0,),(4,)])

    def test_token_collision_boundaries_and_numeric_attribute(self):
        text='''def solve(x):
    a = 1 .real
    return (a + +x, x - -2, x is not None, x not in [3], 1e3 / 2)
'''
        self.same(text,[(0,),(3,),(4,)])
        for left,right in [('not','in'),('a','b'),('1','e3'),('1','.')]:
            self.assertTrue(render.needs_space(left,right),(left,right))

    def test_reflection_source_and_frame_observability_retain_original(self):
        sources=[
            'import inspect as look\ndef solve(x):return look.getsource(solve)\n',
            'from traceback import extract_stack as s\ndef solve(x):return s()\n',
            'def solve(x):return solve.__code__.co_firstlineno\n',
            'def solve(x):return getattr(solve,"__code__")\n',
            'def solve(x):return eval(x)\n',
            'def solve(x):return exec(x)\n',
            'def solve(x):return compile(x,"p","exec")\n',
            'def solve(x):return x.tb_frame.f_code\n',
            'def solve(x):return open("candidate.py").read()\n',
            'def solve(x):\n try:return x()\n except Exception as e:return str(e)\n',
            'from __future__ import annotations\ndef solve(x: list [ int ]):return x\n',
            'def solve(x):\n y=x # type: int\n return y\n',
            'def solve(x):return x # type: ignore[attr-defined]\n',
            '@dec\ndef solve(x):return x\n',
            'async def solve(x):return x\n',
        ]
        for text in sources:
            with self.subTest(text=text):
                result=render.menu(text)
                self.assertIsNotNone(result['unsupported'])
                self.assertEqual(result['candidates'],{'original':text})

    def test_alphabet_and_literal_changes_rejected(self):
        text='def solve(x): return "\\u03bb", 0x10, "\\u0061", x\n'
        result=self.same(text,[(4,)])
        self.assertIn('unparse',result['candidates'])
        with self.assertRaises(ValueError):render.validate(text,'def solve(x):return "λ",x\n')
        with self.assertRaises(ValueError):render.validate(text,'def solve(x):return "\\u03bb",x+1\n')
        for source in ('def solve(x):return "λ",x\n','def solve(x):\n\treturn x\n'):
            result=render.menu(source)
            self.assertEqual(result['unsupported'],'outside_literal_alphabet')
            self.assertEqual(result['candidates'],{'original':source})
            self.assertTrue(render.validate(source,source))

    def test_ast_equal_literal_respell_is_still_rejected(self):
        a="def solve(x):return 'a',0x10,x\n"
        b='def solve(x):return "a",16,x\n'
        self.assertEqual(render.fingerprint(ast.parse(a)),render.fingerprint(ast.parse(b)))
        with self.assertRaises(ValueError):render.validate(a,b)

    def test_format_field_reflection_retains_original(self):
        sources=['\n\n\ndef solve(x):\n    return "{0.__code__.co_firstlineno}".format(solve)\n',
                 'from string import Formatter as F\ndef solve(x):return F().format("{0.__code__}",solve)\n',
                 'def solve(x):return "{f.__code__}".format_map({"f":solve})\n']
        for source in sources:
            result=render.menu(source)
            self.assertIsNotNone(result['unsupported'])
            self.assertEqual(result['candidates'],{'original':source})
        self.assertEqual(execute(sources[0],0),'4')

    def test_typing_evaluation_and_string_annotations_retain_original(self):
        source='from typing import get_type_hints\n\ndef target() -> "solve.__code__.co_firstlineno":\n    pass\n\n\ndef solve(x):\n    return get_type_hints(target)["return"]\n'
        self.assertEqual(execute(source,0),7)
        sources=[source,'from typing import get_type_hints as gh\ndef solve(x):return gh(x)\n',
                 'import typing as t\ndef solve(x):return t.evaluate_forward_ref(x)\n',
                 'from typing import ForwardRef as F\ndef solve(x):return F(x)\n',
                 'from typing import List\ndef solve(x: List["Node"]):return x\n']
        for text in sources:
            self.assertEqual(render.menu(text)['candidates'],{'original':text})
        self.same('from typing import List, Optional\ndef solve(x: List[int]) -> Optional[int]:\n    return len(x)\n',[([1,2],)])

    def test_public_summary_never_includes_private_rejection_or_source(self):
        source='def solve(x): return "PRIVATE_EXAMPLE", x\n'
        result=render.menu(source)
        result['rejected']['unparse']='SyntaxError'
        result['_private_rejections']['unparse']='PRIVATE_ERROR_SOURCE_FRAGMENT'
        summary=render.public_summary(result)
        encoded=json.dumps(summary)
        self.assertNotIn('PRIVATE_EXAMPLE',encoded)
        self.assertNotIn('PRIVATE_ERROR_SOURCE_FRAGMENT',encoded)
        self.assertEqual(summary['rejection_types']['unparse'],'SyntaxError')
        self.assertTrue(all(len(value)==64 for value in summary['candidate_sha256'].values()))


if __name__=='__main__':unittest.main()
