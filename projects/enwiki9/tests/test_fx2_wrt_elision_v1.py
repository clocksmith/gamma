import hashlib
import json
import os
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lib.fx2_wrt_elision_v1 import Grammar, code, swap, INTERVALS
from tools.causal_field_parent_coder_v1 import Encoder, Decoder
from tools.wrt_exact import parse_store_bytes, token_index

ROOT = Path(__file__).resolve().parents[1]


def feed(g, data):
    for c in data:
        for bit in range(7, -1, -1):
            y = c >> bit & 1
            forced = g.forced()
            if forced is not None and forced != y:
                raise AssertionError('incorrect forced bit')
            g.observe(y)


class ElisionTests(unittest.TestCase):
    def test_involution_and_all_binary_intervals(self):
        for c in range(256):
            self.assertEqual(swap(swap(c)), c)
        for p in range(1, 512):
            depth = p.bit_length() - 1
            expected = [c for c in range(256) if (256 + c) >> (8 - depth) == p]
            self.assertEqual([c for c in range(256) if INTERVALS[p] >> c & 1], expected)

    def test_all_source_dictionary_codes(self):
        g = Grammar(44880, set(range(256)))
        feed(g, b'\x07')
        for i in range(44880):
            self.assertEqual(token_index(code(i)), i)
            feed(g, bytes(map(swap, code(i))))
        g.finish()

    def test_short_dictionary_boundaries(self):
        for n in (1, 79, 80, 81, 3919, 3920, 3921, 44880):
            g = Grammar(n, set(range(256)))
            feed(g, b'\x07' + bytes(map(swap, code(n - 1))))
            g.finish()
            if n < 44880:
                bad = Grammar(n, set(range(256)))
                with self.assertRaises((ValueError, AssertionError)):
                    feed(bad, b'\x07' + bytes(map(swap, code(n))))

    def test_native_encoder_language_and_independent_inverse(self):
        native = ROOT / 'results/fx2_attention_window250k_v2/work/native/src/preprocess'
        harness = '''#include "dictionary.h"
#include <cstdio>
int main(int n,char**v){if(n!=5)return 2;FILE*d=fopen(v[1],"rb"),*i=fopen(v[2],"rb"),*o=fopen(v[3],"wb");
preprocessor::Dictionary x(d,true,false);fseek(i,0,SEEK_END);int z=ftell(i);rewind(i);x.Encode(i,z,o);fclose(o);}
'''
        with tempfile.TemporaryDirectory(prefix='wrt-language-') as tmp:
            p = Path(tmp); (p/'main.cpp').write_text(harness)
            subprocess.run(['/usr/bin/g++', '-O2', '-std=c++17', '-I'+str(native), str(p/'main.cpp'),
                            str(native/'dictionary.cpp'), '-o', str(p/'encoder')], check=True)
            words = [b'the', b'compression', b'reusable']
            (p/'dict').write_bytes(b'\n'.join(words)+b'\n')
            rng = random.Random(9271)
            raw = bytes(range(256)) + b' THE Compression REUSABLElower aaaaaabbbbbcccccc ' + bytes(rng.randrange(256) for _ in range(10000))
            (p/'raw').write_bytes(raw)
            subprocess.run([str(p/'encoder'), str(p/'dict'), str(p/'raw'), str(p/'encoded'), 'unused'], check=True)
            body = b'\x07' + bytes(map(swap, (p/'encoded').read_bytes()))
            g = Grammar(len(words), set(body)); feed(g, body); g.finish()
            decoded = parse_store_bytes(b'\x07'+len(raw).to_bytes(4,'big')+body, words).decoded
            self.assertEqual(decoded, raw)
            # Independent arithmetic decoder receives only counts and already
            # decoded prefixes. Forced outcomes never consume coded bits.
            counts = [rng.randrange(1, 65536) for _ in range(len(body)*8)]
            enc = Encoder(max_bits=len(counts), max_payload_bytes=10*len(body))
            g = Grammar(len(words), set(body)); skipped = 0
            for i, c in enumerate(counts):
                forced = g.forced(); y = body[i//8] >> (7-i%8) & 1
                if forced is None: enc.encode(y, c)
                else: self.assertEqual(forced, y); skipped += 1
                g.observe(y)
            archive = enc.finish(); self.assertGreater(skipped, 0)
            dec = Decoder(archive, max_bits=len(counts), max_payload_bytes=10*len(body))
            g = Grammar(len(words), set(body)); restored = bytearray(len(body))
            for i, c in enumerate(counts):
                forced = g.forced(); y = dec.decode(c) if forced is None else forced
                restored[i//8] = (restored[i//8]<<1)|y; g.observe(y)
            g.finish(); self.assertEqual(restored, body)

    def test_truncation_and_pretruth_rejection(self):
        for suffix in (bytes([12]), bytes([64]), bytes([208]), bytes([240, 208])):
            g = Grammar(44880, set(range(256))); feed(g, b'\x07'+bytes(map(swap, suffix)))
            with self.assertRaises(ValueError): g.finish()
        g = Grammar(44880, set(range(256))); feed(g, b'\x07\x0c')
        with self.assertRaises((ValueError, AssertionError)): feed(g, b'a')

    def test_separate_replay_without_source_truth(self):
        body = bytes([7, 128, 32, 64, 128, 10]); raw = b'the The\n'
        vocabulary = set(body)
        vocab = bytes(sum(1 << j for j in range(8) if 8*i+j in vocabulary) for i in range(32))
        prefix = b'GFV1\x07'+len(raw).to_bytes(4,'big')+((1<<39)+len(body)).to_bytes(5,'big')+vocab
        counts = struct.pack('<H', 32768)*8*len(body)
        sha = lambda b: hashlib.sha256(b).hexdigest()
        with tempfile.TemporaryDirectory(prefix='wrt-replay-') as tmp:
            root = Path(tmp); out = root/'out'; out.mkdir()
            dictionary = root/'results/fx2_residual_features250k_v3/work/native/dictionary/english.dic'
            dictionary.parent.mkdir(parents=True); dictionary.write_bytes(b'the\n')
            (out/'prefix.bin').write_bytes(prefix); (out/'parent.q16').write_bytes(counts)
            (out/'projection.json').write_text(json.dumps(dict(modeled_bytes=len(body), raw_bytes=len(raw),
                raw_sha256=sha(raw), modeled_sha256=sha(body), parent_count_sha256=sha(counts), word_count=1)))
            results = {}
            for arm in ('K','V','D'):
                (out/'population.modeled').write_bytes(body)
                for operation in ('encode','decode','repeat'):
                    if operation == 'decode': (out/'population.modeled').unlink()
                    subprocess.run([sys.executable, str(ROOT/'tools/fx2_wrt_elision250k_v1.py'),
                                    str(root), str(out), operation, arm], check=True,
                                   env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'tools')},
                                   stdout=subprocess.DEVNULL)
                    result = json.loads((out/(arm+'-'+operation+'.json')).read_text())
                    result.pop('operation')
                    if operation == 'encode': results[arm] = result
                    else: self.assertEqual(result, results[arm])
                self.assertEqual((out/(arm+'-decode.raw')).read_bytes(), raw)
            self.assertEqual(results['K']['grammar_state_sha256'], results['D']['grammar_state_sha256'])
            self.assertGreater(results['D']['elided_events'], results['V']['elided_events'])


if __name__ == '__main__': unittest.main()
