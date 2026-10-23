"""Focused checks for roles-v1: role rules, exact decoding in both modes, literal equivalence, incremental parse, accounting."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure, binding
joint, ALPHABET = measure.joint, measure.ALPHABET

A = ('function solve(a,b){let total=0;let queue=[a];let out=[];for(let index=0;index<b;index++){total+=index;}'
     'while(queue.length){let node=queue.shift();out.push(node);if(node>1)queue.push(node-1);}let o={total};return out;}')
B = ('function solve(a){let queue=[a];let total=0;for(let index=0;index<a;index++){total+=a[index];queue.push(index);'
     'queue.pop();}return total;}')
IFACE = {'entry': 'solve', 'names': ['solve']}


def recs(*texts):
    got = binding.classify({str(i): (t, IFACE) for i, t in enumerate(texts)})
    return {t: got[str(i)] for i, t in enumerate(texts)}


class Roles(unittest.TestCase):
    def test_role_rules_and_exclusions(self):
        r = recs(A)[A]
        roles = {n['name']: (n['role'], n['ordinal']) for n in r['names']}
        self.assertEqual(roles['a'], ('input', 0)); self.assertEqual(roles['b'], ('input', 1))
        self.assertEqual(roles['out'], ('output', 0)); self.assertEqual(roles['index'], ('index', 0))
        self.assertEqual(roles['queue'], ('queue', 0)); self.assertEqual(roles['node'], ('other', 0))
        self.assertEqual(r['excluded']['interface'], ['solve'])
        self.assertEqual(r['excluded']['shorthand'], ['total'])  # `{total}`: renaming would change the key
        self.assertNotIn('total', roles)
        spans = [A[s:e] for n in r['names'] if n['name'] == 'queue' for s, e in n['spans']]
        self.assertEqual(spans, ['queue'] * 4)  # `queue.length` property `length` is not a span

    def test_member_property_is_not_a_reference(self):
        t = 'function solve(a){let length=a.length;return length;}'
        r = recs(t)[t]
        n = next(n for n in r['names'] if n['name'] == 'length')
        self.assertEqual(len(n['spans']), 2)


class Codec(unittest.TestCase):
    def setUp(self):
        self.records = recs(A, B)
        self.sources = {1: {'s': A}, 2: {'s': B}}

    def slots(self, *names):
        out = []
        for t in (A, B):
            out += [n['slot'] for n in self.records[t]['names'] if n['name'] in names]
        return sorted(set(out))

    def roundtrip(self, mode, vocab):
        binding.install(joint, mode, self.records)
        st = joint.evaluate(self.sources, vocab, 8)
        with tempfile.TemporaryDirectory() as d:
            man = binding.save_and_verify(Path(d) / 'x', self.sources, st, 8)  # asserts decoder.mjs hashes
            decoded = {i: (Path(d) / 'x' / 'decoded' / f'{i}.js').read_text() for i in (1, 2)}
        return st, man, decoded

    def test_bind_decodes_to_source(self):
        vocab = list(ALPHABET) + [binding.END] + self.slots('queue', 'index', 'out') + ['.push(']
        st, man, decoded = self.roundtrip('B', vocab)
        self.assertEqual(decoded, {1: A, 2: B})
        for row in man['programs']:
            self.assertEqual(sum(row['actions'].values()), row['selections'] + 1)
            self.assertEqual(row['actions']['binding'], row['bound_names'])

    def test_rename_decodes_to_canonical_program(self):
        vocab = list(ALPHABET) + self.slots('queue', 'index')
        st, man, decoded = self.roundtrip('N', vocab)
        self.assertIn('$$p0.shift()', decoded[1]); self.assertIn('for(let $$i0=0;', decoded[2])
        self.assertNotIn('queue', decoded[1])

    def test_bind_without_end_is_literal(self):
        binding.install(joint, 'L', {})
        lit = joint.evaluate(self.sources, list(ALPHABET) + ['.push('], 8)
        binding.install(joint, 'B', self.records)
        b = joint.evaluate(self.sources, list(ALPHABET) + ['.push('] + self.slots('queue'), 8)  # no END: slots inactive
        self.assertEqual(b['selections'], lit['selections'])
        n0 = joint.evaluate(self.sources, list(ALPHABET) + ['.push('], 8)
        self.assertEqual(n0['parsed'], lit['parsed'])

    def test_declarations_are_charged(self):
        binding.install(joint, 'B', self.records)
        q = self.slots('queue')
        st = joint.evaluate({1: {'s': A}}, list(ALPHABET) + [binding.END] + q, 8)
        body = st['bodies'][(1, 's')]
        self.assertEqual(st['selections'], len(body) + len('queue') + 1)  # every body char, the name once, END

    def test_incremental_matches_full(self):
        binding.install(joint, 'B', self.records)
        v0 = list(ALPHABET) + [binding.END]
        s0 = joint.evaluate(self.sources, v0, 8)
        for change in (self.slots('queue'), self.slots('index', 'queue') + ['++'], ['total+=']):
            s1 = joint.evaluate(self.sources, set(s0['vocab']) | set(change), 8, s0)
            full = joint.evaluate(self.sources, set(s0['vocab']) | set(change), 8)
            self.assertEqual(s1['parsed'], full['parsed'])
            back = joint.evaluate(self.sources, set(s0['vocab']), 8, s1)
            self.assertEqual(back['parsed'], s0['parsed'])
            s0 = s1

    def test_prune_keeps_slots_and_end(self):
        binding.install(joint, 'B', self.records)
        unused = binding.PLACE('queue', 5)
        st = joint.evaluate(self.sources, list(ALPHABET) + [binding.END, unused, 'zzz'], 8)
        pruned, removed = joint.prune(self.sources, st, 8)
        self.assertEqual(removed, ['zzz'])
        self.assertIn(unused, pruned['vocab']); self.assertIn(binding.END, pruned['vocab'])

    def test_mode_n_rejects_end(self):
        binding.install(joint, 'N', self.records)
        with self.assertRaises(ValueError):
            joint.evaluate(self.sources, list(ALPHABET) + [binding.END], 8)


if __name__ == '__main__':
    unittest.main()
