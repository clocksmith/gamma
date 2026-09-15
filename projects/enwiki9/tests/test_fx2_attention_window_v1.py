import ctypes as C
import hashlib
from pathlib import Path
import random
import subprocess
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools.fx2_attention_window_adapter_v1 import CHANGES, mutate
from tools.fx2_expert_release250k_v3 import source_zip
from tools import fx2_attention_window250k_v1 as gate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'results/fx2_expert_release250k_v3/P-source.zip'


class Kernel:
    def __init__(self, library):
        self.lib = C.CDLL(str(library))
        self.lib.window_size.restype = C.c_uint
        self.lib.window_new.restype = C.c_void_p
        self.lib.window_delete.argtypes = [C.c_void_p]
        self.lib.window_step.argtypes = [C.c_void_p, *([C.POINTER(C.c_int8)]*3),
                                        *([C.POINTER(C.c_float)]*3)]
        self.lib.window_step.restype = C.c_uint
        self.pointer = self.lib.window_new()
        assert self.pointer

    def step(self, q, k, v, coef=(1/4096,)*3):
        # Deliberately unaligned foreign output exercises the probe's copy boundary.
        storage = (C.c_char*(192*4+1))()
        out = (C.c_float*192).from_buffer(storage,1)
        n = self.lib.window_step(self.pointer, (C.c_int8*192)(*q),
                                 (C.c_int8*192)(*k), (C.c_int8*192)(*v),
                                 (C.c_float*3)(*coef), (C.c_float*3)(1,1,1), out)
        return n, list(out), bytes(out)

    def close(self): self.lib.window_delete(self.pointer)


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='window-unit-', dir='/run/user/1000')
        cls.root = Path(cls.tmp.name)
        with zipfile.ZipFile(SOURCE) as z: cls.original = {n:z.read(n) for n in z.namelist()}
        cls.changed = mutate(cls.original)
        cls.libraries = {}
        for label, members in [('P',cls.original),('D',cls.changed)]:
            root = cls.root/label; root.mkdir()
            for name, data in members.items():
                p = root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
            lib = root/'probe.so'
            subprocess.run(['g++','-std=c++17','-O3','-shared','-fPIC','-march=x86-64-v3',
                            '-mtune=generic','-mrecip=none','-fno-fast-math','-fno-math-errno',
                            '-I'+str(root), str(ROOT/'tools/fx2_attention_window_probe_v1.cpp'),
                            str(root/'cpp_infer/src/opt/attn.cpp'),'-o',str(lib)],check=True)
            cls.libraries[label] = lib

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_exact_two_member_mutation_and_model_identity(self):
        self.assertEqual(set(self.original), set(self.changed))
        self.assertEqual({n for n in self.original if self.original[n] != self.changed[n]}, set(CHANGES))
        for n in self.original:
            if n not in CHANGES: self.assertEqual(self.original[n], self.changed[n])
        with self.assertRaises(ValueError): mutate(self.changed)

    def test_source_archive_reconstructs_parent_exactly(self):
        dest = self.root/'parent.zip'; source_zip(dest,self.original)
        self.assertEqual(dest.read_bytes(), SOURCE.read_bytes())

    def test_random_prefix_is_bit_identical(self):
        rng = random.Random(20481024); p=Kernel(self.libraries['P']); d=Kernel(self.libraries['D'])
        try:
            self.assertEqual(p.lib.window_size(),1024); self.assertEqual(d.lib.window_size(),2048)
            for i in range(1023):
                vectors = [[rng.randrange(-32,33) for _ in range(192)] for _ in range(3)]
                a=p.step(*vectors); b=d.step(*vectors)
                self.assertEqual(a[0],i+1); self.assertEqual(a[2],b[2],str(i))
        finally: p.close(); d.close()

    def test_uniform_attention_full_ring_and_eviction(self):
        # Independent exact integer sliding sums; zero query makes all scores equal.
        for label, w in [('P',1024),('D',2048)]:
            model=Kernel(self.libraries[label]); values=[]; total=0
            try:
                for i in range(4100):
                    value=64 if (i//1024)%2==0 else -64
                    values.append(value); total += value
                    if len(values)>w: total -= values[-w-1]
                    n, out, _ = model.step([0]*192,[17]*192,[value]*192)
                    self.assertEqual(n,min(i+1,w))
                    expected=total/n
                    for x in out: self.assertAlmostEqual(x,expected,delta=0.00002)
                    if i==2047: self.assertEqual(out,[(-64.0 if label=='P' else 0.0)]*192)
            finally: model.close()

    def test_independent_repeated_trajectory(self):
        checks=[]
        for _ in range(2):
            model=Kernel(self.libraries['D']); rng=random.Random(987)
            h=hashlib.sha256()
            try:
                for i in range(2050):
                    v=[rng.randrange(-8,9) for _ in range(192)]
                    h.update(model.step(v, v[::-1], v)[2])
            finally: model.close()
            checks.append(h.digest())
        self.assertEqual(*checks)

    def test_neural_prefix_and_finite_population_checks(self):
        with tempfile.TemporaryDirectory(dir=self.tmp.name) as directory:
            p=Path(directory)/'P';d=Path(directory)/'D'
            data=bytearray(2051*410);p.write_bytes(data)
            struct.pack_into('<e',data,1023*410,0.5);d.write_bytes(data)
            with patch.object(gate,'N',2051):
                result=gate.neural_compare(p,d,[0])
                self.assertEqual(result['first_changed_row']['predicted_modeled_byte'],1024)
                self.assertEqual(result['same_pre_boundary_rows'],1023)
                data[0:2]=struct.pack('<e',0.25);d.write_bytes(data)
                with self.assertRaisesRegex(ValueError,'before the declared window'):
                    gate.neural_compare(p,d,[0])
                data[0:2]=struct.pack('<e',float('nan'));d.write_bytes(data)
                with self.assertRaisesRegex(ValueError,'nonfinite'):
                    gate.neural_compare(p,d,[0])


if __name__ == '__main__': unittest.main()
