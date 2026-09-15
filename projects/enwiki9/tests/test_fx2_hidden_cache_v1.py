import collections
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest

from lib.fx2_hidden_cache_v1 import Model
from tools.causal_field_parent_coder_v1 import Encoder, Decoder

ROOT = Path(__file__).resolve().parents[1]
MASS = 1 << 32


def signature(rng):
    return sum(rng.choice((1, 2)) << (2*j) for j in range(32))


def distance(a, b):
    return sum((a >> (2*j) & 3) != (b >> (2*j) & 3) for j in range(32))


class Reference:
    def __init__(self, arm):
        self.arm = arm; self.history = collections.deque(maxlen=4096)
        self.weights = [[MASS//2, MASS//2] for _ in range(8)]
        self.clock = 0; self.prefix = 0; self.previous = None

    def predict(self, c, sig, valid):
        self.row = self.clock % 8
        if self.row == 0:
            self.sig = sig; self.valid = valid
            near = sorted((distance(sig, s), age, label)
                          for age, (s, label) in enumerate(reversed(self.history))
                          if valid and sig and distance(sig, s) <= 8)[:32]
            self.hist = collections.Counter()
            for d, _, label in near: self.hist[label] += 9-d
        low = self.prefix << (8-self.row); mid = low + (1 << (7-self.row)); high = mid + (1 << (7-self.row))
        total = sum(v for k, v in self.hist.items() if low <= k < high)
        ones = sum(v for k, v in self.hist.items() if mid <= k < high)
        e = (3*c + (65536*ones + total//2)//total + 2)//4 if total else c
        self.c, self.e = c, e
        w = self.weights[self.row]
        q = (w[0]*c + w[1]*e + MASS//2)//MASS
        return c if self.arm == 'K' else q

    def observe(self, y):
        w = self.weights[self.row]
        if self.c != self.e:
            values = [w[0]*(self.c if y else 65536-self.c), w[1]*(self.e if y else 65536-self.e)]
            den = sum(values); divisions = [divmod((MASS-2)*v, den) for v in values]
            updated = [1+r[0] for r in divisions]
            if sum(updated) < MASS: updated[int(divisions[1][1] > divisions[0][1])] += 1
            w[:] = updated
        self.prefix = self.prefix*2 + y; self.clock += 1
        if self.clock % 8 == 0:
            if self.valid and self.sig:
                label = self.previous if self.arm == 'S' and self.previous is not None else self.prefix
                self.history.append((self.sig, label))
            self.previous = self.prefix; self.prefix = 0


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='hidden-cache-unit-', dir='/run/user/1000')
        cls.lib = Path(cls.tmp.name)/'cache.so'
        subprocess.run(['g++','-std=c++17','-O2','-shared','-fPIC','-fno-exceptions','-fno-rtti',
                        str(ROOT/'tools/fx2_hidden_cache_bridge_v1.cpp'),'-o',str(cls.lib)], check=True)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_ternary_distance(self):
        rng = random.Random(7101)
        with Model(self.lib, 'D') as model:
            for _ in range(1000):
                a = sum(rng.randrange(3) << (2*j) for j in range(32))
                b = sum(rng.randrange(3) << (2*j) for j in range(32))
                self.assertEqual(model.lib.cache_distance(a, b), distance(a, b))

    def test_independent_prediction_and_posterior(self):
        rng = random.Random(7102); keys = [signature(rng) for _ in range(16)]
        for arm in 'KDS':
            ref = Reference(arm)
            with Model(self.lib, arm) as model:
                for i in range(160):
                    valid = i % 17 != 0; sig = rng.choice(keys) if valid else 0
                    byte = rng.randrange(256)
                    for bit in range(8):
                        p = rng.choice((1, 65535, rng.randrange(1, 65536)))
                        q = model.predict(p, sig, int(valid))
                        self.assertEqual(q, ref.predict(p, sig, valid))
                        y = byte >> (7-bit) & 1
                        model.observe(y); ref.observe(y)
                        state = model.state()
                        self.assertEqual(struct.unpack_from('<16Q', state, 34), tuple(v for r in ref.weights for v in r))

    def test_nearest_newest_ties_and_fifo(self):
        key = 0x5555555555555555
        with Model(self.lib, 'D') as model:
            for i in range(4100):
                for r in range(8):
                    model.predict(32768, key, 1); model.observe((i >> (7-r)) & 1)
            state = model.state()
            self.assertEqual(struct.unpack_from('<II', state, 8), (4, 4096))
            model.predict(32768, key, 1)
            state = model.state(); cdf = struct.unpack_from('<257I', state, 37026)
            expected = collections.Counter((i & 255) for i in range(4100-32, 4100))
            self.assertEqual([cdf[i+1]-cdf[i] for i in range(256)], [9*expected[i] for i in range(256)])

    def test_k_d_state_and_independent_inverse(self):
        rng = random.Random(7103); keys = [signature(rng) for _ in range(8)]
        data = [rng.randrange(8) for _ in range(512)]
        enc = Encoder(); states = hashlib.sha256()
        with Model(self.lib, 'D') as d, Model(self.lib, 'K') as k:
            for n in data:
                for r in range(8):
                    q = d.predict(32768, keys[n], 1)
                    self.assertEqual(k.predict(32768, keys[n], 1), 32768)
                    y = (n*31) >> (7-r) & 1; enc.encode(y, q); d.observe(y); k.observe(y)
                    self.assertEqual(k.state(), d.state()); states.update(d.state())
        payload = enc.finish(); self.assertLess(len(payload), len(data)-100)
        dec = Decoder(payload); repeated = Encoder(); check = hashlib.sha256()
        with Model(self.lib, 'D') as model:
            for n in data:
                for r in range(8):
                    q = model.predict(32768, keys[n], 1); y = dec.decode(q)
                    self.assertEqual(y, (n*31) >> (7-r) & 1)
                    repeated.encode(y, q); model.observe(y); check.update(model.state())
        self.assertEqual(payload, repeated.finish()); self.assertEqual(states.digest(), check.digest())

    def test_causality_and_delayed_labels(self):
        key = 0x5555555555555555
        with Model(self.lib, 'D') as d, Model(self.lib, 'S') as s:
            for byte in (17, 204):
                for r in range(8):
                    d.predict(32768, key, 1); s.predict(32768, key, 1)
                    self.assertEqual(struct.unpack_from('<I', d.state(), 12)[0], int(byte == 204))
                    y = byte >> (7-r) & 1; d.observe(y); s.observe(y)
            self.assertEqual(d.state()[32930:32932], bytes((17, 204)))
            self.assertEqual(s.state()[32930:32932], bytes((17, 17)))

    def test_invalid_order_and_missing_features(self):
        with Model(self.lib, 'D') as model:
            with self.assertRaises(ValueError): model.observe(0)
            with self.assertRaises(ValueError): model.predict(32768, 3, 1)
            with self.assertRaises(ValueError): model.predict(32768, 1, 0)
            for r in range(8):
                self.assertEqual(model.predict(32768, 0, 0), 32768)
                with self.assertRaises(ValueError): model.predict(32768, 0, 0)
                model.observe(r & 1)
            self.assertEqual(struct.unpack_from('<I', model.state(), 12)[0], 0)

    def test_cli_separate_process_inverse_and_dependency_integrity(self):
        # Predeclared periodic fixture/signatures; no corpus information is used.
        raw = b'abcd ' * 100
        modeled = b'\x07' + raw
        counts = struct.pack('<H', 32768) * (len(modeled)*8)
        rng = random.Random(7104)
        keys = [signature(rng) for _ in range(5)]
        signatures = b''.join(struct.pack('<QB', 0 if i == 0 else keys[(i-1)%5], int(i != 0))
                              for i in range(len(modeled)))
        with tempfile.TemporaryDirectory(dir=self.tmp.name) as directory:
            root = Path(directory); out = root/'out'; out.mkdir()
            dictionary = root/'results/fx2_residual_features250k_v3/work/native/dictionary/english.dic'
            dictionary.parent.mkdir(parents=True); dictionary.write_bytes(b'')
            digest = lambda data: hashlib.sha256(data).hexdigest()
            prefix = (b'GFV1\x07'+len(raw).to_bytes(4,'big')+
                      ((1<<39)+len(modeled)).to_bytes(5,'big')+b'\xff'*32)
            for name, data in [('population.modeled', modeled), ('parent.q16', counts),
                               ('signatures.bin', signatures), ('prefix.bin', prefix)]:
                (out/name).write_bytes(data)
            (out/'projection.json').write_text(json.dumps(dict(raw_bytes=len(raw), raw_sha256=digest(raw),
                modeled_bytes=len(modeled), modeled_sha256=digest(modeled),
                parent_count_sha256=digest(counts), signature_sha256=digest(signatures))))
            env = {**os.environ, 'PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'tools')}
            command = [sys.executable, str(ROOT/'tools/fx2_hidden_cache250k_v1.py'), str(root), str(out)]
            rows = {}
            for arm in 'KDS':
                for operation in ('encode', 'decode', 'repeat'):
                    run = subprocess.run(command+[operation, arm, str(self.lib)], env=env,
                                         capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    row = json.loads((out/(arm+'-'+operation+'.json')).read_text())
                    row.pop('operation')
                    if operation == 'encode': rows[arm] = row
                    else: self.assertEqual(row, rows[arm])
                self.assertEqual((out/(arm+'-decode.raw')).read_bytes(), raw)
                self.assertEqual((out/(arm+'-decode.modeled')).read_bytes(), modeled)
                self.assertEqual((out/(arm+'-encode.arc')).read_bytes(), (out/(arm+'-repeat.arc')).read_bytes())
            self.assertEqual(rows['K']['controller_state_sha256'], rows['D']['controller_state_sha256'])
            self.assertEqual(rows['K']['probability_sha256'], digest(counts))
            self.assertLess(rows['D']['archive_bytes'], rows['K']['archive_bytes'])
            (out/'parent.q16').write_bytes(bytes((counts[0]^1,))+counts[1:])
            run = subprocess.run(command+['encode','D',str(self.lib)], env=env, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('conditional input digest differs', run.stderr)


if __name__ == '__main__': unittest.main()
