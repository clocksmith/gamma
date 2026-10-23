"""Focused checks for the typed-component codec (typed.py, matcher.mjs, decoder.mjs)."""
import importlib.util, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(HERE))
import typed

spec = importlib.util.spec_from_file_location('style150_v2_measure', LIT / 'style150-v2/measure.py')
m2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m2)
joint = m2.joint
ORIGINAL = joint.evaluate
ALPHABET = list(joint.base.ALPHABET)

TEXTS = {
    1: 'function solve(a){let M=new Map();for(let x of a){M.set(x,(M.get(x)||0)+1);}return M;}',
    2: 'function solve(a,b){let e=[];let q=[b];while(q.length>0){let u=q.pop();for(let v of a[u]){if(!e[v]){e[v]=true;q.push(v);}}}return e;}',
    3: 'function F(a){if(a===null){return 0;}return 1+Math.max(F(a.left),F(a.right));}function solve(a){let p=a;let s=0;while(p!==null){s+=p.val;p=p.next;}return s+F(a);}',
    4: 'function solve(a){let cnt=new Map();for(let x of a){cnt.set(x,(cnt.get(x)||0)+1);}return cnt;}',
}
SOURCES = {pid: {'s': t} for pid, t in TEXTS.items()}
COMPS = [typed.code(c) for c in typed.COMPONENTS]


def setUpModule():
    rows = typed.find_matches({str(k): v for k, v in TEXTS.items()})
    typed.install(joint, {TEXTS[int(k)]: r['matches'] for k, r in rows.items()})


def tearDownModule():
    joint.evaluate = ORIGINAL


class Typed(unittest.TestCase):
    def test_without_components_delegates_to_the_literal_codec(self):
        vocab = ALPHABET + ['function solve(a', 'return ']
        a, b = typed.evaluate(SOURCES, vocab, 8), ORIGINAL(SOURCES, vocab, 8)
        self.assertEqual((a['selections'], a['package_bytes'], a['parsed']), (b['selections'], b['package_bytes'], b['parsed']))

    def test_map_increment_is_charged_code_operands_and_end_once_per_hole(self):
        plain = ORIGINAL({1: SOURCES[1]}, ALPHABET, 8)['selections']
        st = typed.evaluate({1: SOURCES[1]}, ALPHABET + [typed.code('C1'), typed.END], 8)
        span = len('M.set(x,(M.get(x)||0)+1);')
        self.assertEqual(st['selections'], plain - span + 4)  # C1, M, x, END: M and x repeat but are charged once
        self.assertEqual(st['parsed'][1, 's'].count(typed.code('C1')), 1)

    def test_id_operand_needs_an_identifier_entry(self):
        base = ORIGINAL({4: SOURCES[4]}, ALPHABET, 8)['selections']
        without = typed.evaluate({4: SOURCES[4]}, ALPHABET + [typed.code('C1'), typed.END], 8)['selections']
        self.assertEqual(without, base)
        with_name = typed.evaluate({4: SOURCES[4]}, ALPHABET + ['cnt', typed.code('C1'), typed.END], 8)
        self.assertIn(typed.code('C1'), with_name['parsed'][4, 's'])

    def test_end_removal_disables_only_end_closed_components(self):
        st = typed.evaluate({3: SOURCES[3]}, ALPHABET + [typed.code('T2'), typed.code('T7')], 8)
        codes = st['parsed'][3, 's']
        self.assertIn(typed.code('T2'), codes)        # id-only holes
        self.assertNotIn(typed.code('T7'), codes)     # needs END for its body

    def test_nesting_and_roundtrip_through_the_independent_decoder(self):
        vocab = ALPHABET + COMPS + [typed.END, 'function solve(a', 'return ']
        st = typed.evaluate(SOURCES, vocab, 8)
        codes = st['parsed'][2, 's']
        self.assertTrue({typed.code('Q1'), typed.code('G2'), typed.code('G3')} <= set(codes))
        with tempfile.TemporaryDirectory() as d:
            m = typed.save_and_verify(Path(d) / 'arm', SOURCES, st, 8)
        self.assertEqual(m['verified'], 4)
        self.assertEqual(sum(r['selections'] for r in m['programs']), st['selections'])

    def test_depth_limit_blocks_components(self):
        old = typed.DEPTH
        try:
            typed.DEPTH = 0
            st = typed.evaluate(SOURCES, ALPHABET + COMPS + [typed.END], 8)
            self.assertFalse(any(typed.is_code(s) for k in st['parsed'] for s in st['parsed'][k]))
        finally:
            typed.DEPTH = old

    def test_near_whole_match_is_not_admissible(self):
        text = 'while(q.length>0){let u=q.pop();}'
        m = {'c': 'Q1', 's': 0, 'e': len(text), 'holes': {'Q': [6, 7], 'U': [22, 23], 'B': [32, 32]}}
        self.assertFalse(typed.admissible(m, text))
        self.assertTrue(typed.admissible(m, TEXTS[2] + text))

    def test_whole_program_literal_rejected(self):
        with self.assertRaises(ValueError):
            typed.evaluate(SOURCES, ALPHABET + [typed.code('C1'), TEXTS[1]], 8)

    def test_proposals_stay_inside_contiguous_source_text(self):
        st = typed.evaluate(SOURCES, ALPHABET + COMPS + [typed.END], 8)
        props = typed.proposals(SOURCES, st, 500, allowed=list(typed.COMPONENTS))
        texts = list(TEXTS.values())
        for p in props:
            if not typed.is_code(p):
                self.assertTrue(sum(p in t for t in texts) >= 2, p)


if __name__ == '__main__':
    unittest.main()
