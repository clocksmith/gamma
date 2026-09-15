import ctypes
from fractions import Fraction
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

from lib.fx2_wrt_mass_v1 import half_mass, row_masses, prefixes, branch_masses, corrected_count, Q, SCALE, MINIMUM
ROOT=Path(__file__).resolve().parents[1]
# The retained replay helper imports its sibling modules by their CLI names.
sys.path.insert(0,str(ROOT/'tools'))
from tools.fx2_wrt_mass250k_v1 import feature_row


class MassTests(unittest.TestCase):
    def test_every_nonnegative_half_against_binary32_guard(self):
        minimum=struct.unpack('<f',struct.pack('<f',1e-6))[0]
        self.assertEqual(Fraction(minimum)*SCALE,MINIMUM)
        for h in range(0x3c01):
            f=struct.unpack('<e',struct.pack('<H',h))[0]
            self.assertEqual(half_mass(h),Fraction(max(minimum,f))*SCALE)
        self.assertEqual(half_mass(0x8000),MINIMUM)
        for h in (0x7c00,0xfc00,0x7c01,0x3c01,0xbc00):
            with self.assertRaises(ValueError):half_mass(h)

    def test_all_binary_prefix_masses(self):
        rng=random.Random(415);vocab=list(range(256))
        ws=[rng.randrange(1,10000) for _ in vocab];total=sum(ws)
        row=b''.join(struct.pack('<e',w/total) for w in ws)
        masses=row_masses(row,vocab);mask=sum(1<<c for c in vocab if c%3)
        cdf,legal=prefixes(masses,mask)
        for p in range(1,256):
            depth=p.bit_length()-1
            for k,table in [(False,cdf),(True,legal)]:
                sums=[0,0]
                for c in range(256):
                    if (256+c)>>(8-depth)==p and (not k or (mask>>c)&1):
                        sums[(c>>(7-depth))&1]+=masses[c]
                self.assertEqual(branch_masses(p,table),tuple(sums))

    def test_exact_bayesian_identity_and_null(self):
        # When expert and parent agree, the odds correction is precisely
        # conditioning on the legal subset; this does not assume actual CMIX
        # and its neural expert agree.
        for c0,c1,a0,a1 in [(8,12,3,9),(19,3,2,1),(1,1,1,1)]:
            p=Fraction(c1,c0+c1)
            corrected=(p*Fraction(a1,c1))/(p*Fraction(a1,c1)+(1-p)*Fraction(a0,c0))
            self.assertEqual(corrected,Fraction(a1,a0+a1))
        for p in range(1,65536):
            self.assertEqual(corrected_count(p,37,113,37,113),p)
            self.assertEqual(corrected_count(p,74,226,37,113),p)

    def test_native_uint128_boundary_and_random_vectors(self):
        rng=random.Random(3301)
        with tempfile.TemporaryDirectory(prefix='wrt-mass-native-') as tmp:
            library=Path(tmp)/'probe.so'
            subprocess.run(['/usr/bin/g++','-O2','-std=c++17','-shared','-fPIC',str(ROOT/'tools/fx2_wrt_mass_probe_v1.cpp'),'-o',str(library)],check=True)
            f=ctypes.CDLL(str(library)).gamma_mass;f.argtypes=[ctypes.c_uint]+[ctypes.c_uint64]*4;f.restype=ctypes.c_uint
            vectors=[(p,c0,c1,a0,a1) for p in (1,32768,65535) for c0,c1,a0,a1 in [(SCALE,SCALE,1,SCALE),(SCALE,SCALE,SCALE,1),(1,1,1,1),(SCALE,SCALE,SCALE,SCALE)]]
            for _ in range(5000):
                c0=rng.randrange(1,SCALE+1);c1=rng.randrange(1,SCALE+1)
                vectors.append((rng.randrange(1,65536),c0,c1,rng.randrange(1,c0+1),rng.randrange(1,c1+1)))
            for v in vectors:self.assertEqual(f(*v),corrected_count(*v))
            for v in [(0,1,1,1,1),(1,0,1,1,1),(1,1,1,0,1),(1,SCALE*2,SCALE*2,1,1)]:
                self.assertEqual(f(*v),0)
                with self.assertRaises(ValueError):corrected_count(*v)

    def test_previous_row_only_and_noninvertible_control(self):
        class Stream:
            def __init__(self):self.keys=[]
            def __getitem__(self,key):self.keys.append(key);return b'x'*(key.stop-key.start)
        s=Stream();self.assertIsNone(feature_row(s,0,410));self.assertEqual(s.keys,[])
        feature_row(s,19,410);self.assertEqual((s.keys[-1].start,s.keys[-1].stop),(18*410,19*410))
        row=struct.pack('<eee',.125,.25,.625)
        a=row_masses(row,[7,64,128]);b=row_masses(row,[7,64,128],True)
        self.assertEqual(sorted(a),sorted(b));self.assertNotEqual(a,b)
        # There is no fitting stage that could undo the label rotation.
        with self.assertRaises(ValueError):row_masses(struct.pack('<eee',1.,1.,1.),[7,64,128])

    def test_independent_replay_without_truth_file(self):
        body=bytes([7,128,32,64,97,98,99,10,64,128,10]);raw=b'the Abc\nThe\n'
        vocab=sorted(set(body));bits=bytes(sum(1<<j for j in range(8) if i*8+j in vocab) for i in range(32))
        prefix=b'GFV1\x07'+len(raw).to_bytes(4,'big')+((1<<39)+len(body)).to_bytes(5,'big')+bits
        counts=struct.pack('<H',32768)*8*len(body);sha=lambda b:hashlib.sha256(b).hexdigest()
        rng=random.Random(719);rows=[]
        for _ in body:
            ws=[rng.randrange(1,100) for _ in vocab];total=sum(ws)
            rows.append(b''.join(struct.pack('<e',w/total) for w in ws))
        neural=b''.join(rows)
        with tempfile.TemporaryDirectory(prefix='wrt-mass-replay-') as tmp:
            root=Path(tmp);out=root/'out';out.mkdir()
            (root/'dictionary').write_bytes(b'the\n');(root/'neural').write_bytes(neural)
            (out/'prefix.bin').write_bytes(prefix);(out/'parent.q16').write_bytes(counts)
            (out/'projection.json').write_text(json.dumps(dict(modeled_bytes=len(body),raw_bytes=len(raw),raw_sha256=sha(raw),modeled_sha256=sha(body),parent_count_sha256=sha(counts),word_count=1,vocabulary=vocab,neural_path='neural',neural_bytes=len(neural),neural_sha256=sha(neural),dictionary_path='dictionary')))
            reports={}
            for arm in ('K','M','S'):
                (out/'population.modeled').write_bytes(body)
                for phase in ('encode','decode','repeat'):
                    if phase=='decode':(out/'population.modeled').unlink()
                    subprocess.run([sys.executable,str(ROOT/'tools/fx2_wrt_mass250k_v1.py'),str(root),str(out),phase,arm],check=True,stdout=subprocess.DEVNULL,env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'tools')})
                    r=json.loads((out/(arm+'-'+phase+'.json')).read_text());r.pop('operation')
                    if phase=='encode':reports[arm]=r
                    else:self.assertEqual(r,reports[arm])
                self.assertEqual((out/(arm+'-decode.raw')).read_bytes(),raw)
            self.assertEqual(len({r['grammar_state_sha256'] for r in reports.values()}),1)
            self.assertEqual(len({r['causal_feature_sha256'] for r in reports.values()}),1)
            self.assertEqual(reports['K']['changed_counts'],0)
            self.assertGreater(reports['M']['changed_counts'],0)
            self.assertNotEqual(reports['M']['action_sha256'],reports['S']['action_sha256'])


if __name__=='__main__':unittest.main()
