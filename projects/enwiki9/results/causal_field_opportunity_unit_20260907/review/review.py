"""Independent synthetic observer review; no corpus or arithmetic-code inputs."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import causal_field_opportunity_v1 as subject
import test_causal_field_opportunity_v1 as author

PINS = {
    'tools/causal_field_opportunity_v1.py': 'be6d722771a4426d74d46acf8e9fefe8a6d207b44580fe775f8f64253e259c3d',
    'tests/test_causal_field_opportunity_v1.py': 'c68530bb29f6113fbeabea9f4bd557992d8e969003b149461861cb4826952513',
    'tools/causal_field_wrt_adapter_v1.py': '649acd80af3ac10e8c2273bde3c2007e07d677bd2941c939494bd0ab76f7c89a',
    'tools/causal_field_dependency_v1.py': 'f34a42054ba151219c67060cf3420e06fb1e1aff8ea9f01aa408e116b495ec0a',
    'tools/wrt_exact.py': 'ae08246ee8b4708904f78aa5f694111834d6420deece34957c61d6fea3a9797a',
}
EVIDENCE = []
CODE = subject.base.wrt.wrt_byte_transform


def literal(raw):
    codes = bytearray()
    for value in raw:
        if value >= 128 or value in (subject.base.wrt.END_UPPER, subject.base.wrt.UPPERCASE,
                                    subject.base.wrt.CAPITALIZED, subject.base.wrt.ESCAPE):
            codes.append(CODE(subject.base.wrt.ESCAPE))
        codes.append(CODE(value))
    return bytes(codes)


class IndependentTests(unittest.TestCase):
    def parity(self, raw, modeled, words):
        self.assertLessEqual(len(raw), 8192)
        all_rows = {}
        for arm in 'PKTRS':
            frozen = subject.base.Adapter(words, arm, len(raw))
            observer = subject.Adapter(words, arm, len(raw), first_event_limit=128)
            output = bytearray()
            chain = hashlib.sha256()
            for offset, value in enumerate(modeled):
                left = frozen.feed(value)
                right = observer.feed(value)
                self.assertEqual(left, right, (arm, offset))
                self.assertEqual(frozen.state_digest(), observer.state_digest(), (arm, offset))
                self.assertEqual(frozen.donor, observer.donor, (arm, offset))
                self.assertEqual(frozen.activation_id, observer.activation_id, (arm, offset))
                output.extend(right)
                chain.update(bytes.fromhex(observer.state_digest()))
            self.assertEqual(bytes(output), raw)
            self.assertEqual(frozen.finish(), observer.finish())
            diagnostic = observer.diagnostics()
            for event in diagnostic['first_events']:
                if event['kind'] != 'value_start' or event['eligibility'] != 'eligible':
                    continue
                field, hit = {'K': ('conditional', 'exact_compatible_hit'),
                              'T': ('conditional', 'exact_compatible_hit'),
                              'R': ('recency', 'compatible_route_hit'),
                              'S': ('rotated', 'compatible_rotated_hit')}[arm]
                self.assertEqual(event['inherited_donor_selected'], event[field] == hit)
                self.assertEqual(raw[event['context']['raw_offset']], ord('='))
            all_rows[arm] = {'diagnostics': diagnostic, 'state_chain_sha256': chain.hexdigest(),
                             'terminal_state_sha256': observer.state_digest()}
        EVIDENCE.append({'test': self.id(), 'raw_hex': raw.hex(), 'modeled_hex': modeled.hex(),
                         'raw_bytes': len(raw), 'modeled_bytes': len(modeled),
                         'dictionary_sha256': observer.dictionary_digest,
                         'parity_boundaries': len(modeled) * 5, 'arms': all_rows})
        return all_rows

    def test_multibyte_token_partition_and_emission_parity(self):
        # Independently assembled WRT codewords exercise indices 80 and 3920.
        words = [b'x'] * 3921
        words[0] = b'v=alpha'
        words[80] = b'{{t|s=A|v=alpha}}'
        words[3920] = b'alpha'
        two = bytes(map(CODE, (0xD0, 0x80)))
        three = bytes(map(CODE, (0xF0, 0xD0, 0x80)))
        one = bytes([CODE(0x80)])
        rec = lambda s: b'{{t|s=' + s + b'|v=alpha}}'
        modeled = (b'\7' + literal(b'{{t|s=A|v=') + three + literal(b'}}')
                   + literal(rec(b'B')) + two
                   + literal(b'{{t|s=A|') + one + literal(b'}}')
                   + literal(rec(b'A')))
        raw = rec(b'A') + rec(b'B') + rec(b'A') + rec(b'A') + rec(b'A')
        rows = self.parity(raw, modeled, words)
        self.assertEqual(rows['T']['diagnostics']['conditional']['exact_compatible_hit'], 1)
        self.assertEqual(rows['R']['diagnostics']['inherited_selected_starts'], 2)
        self.assertEqual(rows['S']['diagnostics']['inherited_selected_starts'], 1)
        self.assertGreater(rows['T']['diagnostics']['eligibility']['unaligned_entry'], 0)

    def test_first_invalidation_offsets_with_whole_event_and_literal_segmentations(self):
        cases = [
            (b'{{|s=A|v=x}}', 2),
            (b'{{t|s=A|v=x|s=duplicate}}', len(b'{{t|s=A|v=x|s')),
            (b'{{t|s=A|v={{nested}}}}', len(b'{{t|s=A|v=')),
            (b'{{t|s=A|v=' + b'x' * 65 + b'}}', len(b'{{t|s=A|v=') + 64),
            (b'{{t|s=A|v=x}q}}', len(b'{{t|s=A|v=x}')),
        ]
        for raw, offset in cases:
            for modeled, words in ((b'\7' + literal(raw), []), (b'\7' + bytes([CODE(0x80)]), [raw])):
                with self.subTest(raw=raw, whole_event=bool(words)):
                    rows = self.parity(raw, modeled, words)
                    for arm in 'KTRS':
                        events = [e for e in rows[arm]['diagnostics']['first_events']
                                  if e['kind'] == 'parser_invalidation']
                        self.assertEqual(len(events), 1)
                        self.assertEqual(events[0]['context']['raw_offset'], offset)
                        self.assertNotEqual(events[0]['context']['mode'], 'invalid')
                        self.assertEqual(rows[arm]['diagnostics']['parser_invalidation_transitions'], 1)


def main():
    assert os.sched_getaffinity(0) == {3}
    for name, expected in PINS.items():
        data = (ROOT / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, name
        target = OUT / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(author),
                               unittest.defaultTestLoader.loadTestsFromTestCase(IndependentTests)])
    start, cpu_start = time.monotonic(), time.process_time()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    elapsed, cpu = time.monotonic() - start, time.process_time() - cpu_start
    for name, expected in PINS.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    (OUT / 'independent-synthetic-evidence.json').write_text(json.dumps(EVIDENCE, indent=2) + '\n')
    (OUT / 'author-synthetic-evidence.json').write_text(json.dumps(author.SYNTHETIC_EVIDENCE, indent=2) + '\n')
    receipt = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'passed': result.wasSuccessful(), 'author_tests': 14, 'independent_tests': 2,
               'wall_seconds': elapsed, 'cpu_seconds': cpu,
               'max_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'source_sha256': PINS, 'source_unchanged_after': True,
               'author_recorded_per_byte_checks': sum(r['every_modeled_byte_parity_checks'] for r in author.SYNTHETIC_EVIDENCE),
               'independent_per_byte_checks': sum(r['parity_boundaries'] for r in EVIDENCE),
               'no_corpus_reads': True, 'no_codec_runs': True,
               'scope': 'Synthetic equality and diagnostic attribution only; no compression or qualification credit.'}
    (OUT / 'review-execution.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
