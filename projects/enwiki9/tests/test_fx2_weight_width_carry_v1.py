"""Synthetic exact-model inverses and pre-truth count-state agreement."""
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_weight_marginal_fixtures_v1 as reference
import fx2_weight_width_carry_v1 as adapter


class WidthCarryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=os.environ['FX2_CARRY_TMP'])
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.probe = os.environ['FX2_CARRY_PROBE']
        self.parent = os.environ['FX2_CARRY_PARENT']

    def command(self, binary, mode, source, target, trace=None, success=True):
        args = [binary, mode, str(source), str(target)]
        if trace is not None:
            args.append(str(trace))
        child = subprocess.run(args, capture_output=True, timeout=30)
        self.assertEqual(child.returncode == 0, success, child.stderr.decode())

    def compare(self, tensors):
        original = self.root / 'original'
        original.write_bytes(reference.encode_reference(tensors))
        for arm in ('P', 'K', 'D'):
            archive, restored, repeat = [self.root/(arm+s) for s in ('.arc', '.raw', '.repeat')]
            enc_trace = self.root/'encode.trace' if arm == 'D' else None
            dec_trace = self.root/'decode.trace' if arm == 'D' else None
            self.command(self.probe, arm, original, archive, enc_trace)
            self.command(self.probe, 'restore', archive, restored, dec_trace)
            self.command(self.probe, arm, original, repeat)
            self.assertEqual(original.read_bytes(), restored.read_bytes())
            self.assertEqual(archive.read_bytes(), repeat.read_bytes())
        self.command(self.parent, 'D', original, self.root/'parent.arc')
        self.assertEqual((self.root/'P.arc').read_bytes(), (self.root/'parent.arc').read_bytes())
        self.assertEqual((self.root/'P.arc').read_bytes(), (self.root/'K.arc').read_bytes())
        self.assertEqual((self.root/'encode.trace').read_bytes(), (self.root/'decode.trace').read_bytes())
        return list(struct.iter_unpack('<16IB', (self.root/'encode.trace').read_bytes()))

    def test_all_encodings_and_empty_tensor(self):
        self.compare([reference.tensor('int4',0,[2,3],1,[-7,0,7,1,-2,4]),
                      reference.tensor('raw',0,[4],0,[0,255,128,10]),
                      reference.tensor('bf16',1,[2],2,[255,255,0,128]),
                      reference.tensor('f32',2,[2],3,[255,255,255,127,0,0,0,128]),
                      reference.tensor('empty',0,[0,3],1,[])])

    def test_empty_document(self):
        self.assertEqual(self.compare([]), [])

    def test_same_width_carries_counts_before_truth(self):
        rows = self.compare([reference.tensor('a',0,[2,3],1,[-7]*6),
                             reference.tensor('b',0,[1,3],1,[7]*3)])
        self.assertEqual(rows[0][1:16], (1,)*15)
        self.assertEqual(rows[6][1:16], (7,)+(1,)*14)
        self.assertEqual(rows[6][-1], 14)
        self.assertEqual(rows[7][15], 2)

    def test_different_width_and_return_to_bank(self):
        rows = self.compare([reference.tensor('a',0,[2],1,[-7]*2),
                             reference.tensor('b',0,[3],1,[7]*3),
                             reference.tensor('c',0,[1,2],1,[-7]*2)])
        self.assertEqual(rows[2][1:16], (1,)*15)
        self.assertEqual(rows[5][1:16], (3,)+(1,)*14)

    def test_rescale_and_opposite_distributions(self):
        rows = self.compare([reference.tensor('a',0,[70000],1,[-7]*70000),
                             reference.tensor('b',0,[70000],1,[7]*70000)])
        self.assertTrue(all(15 <= sum(row[1:16]) < 65536 for row in rows))
        self.assertGreater(rows[70000][1], 1)
        self.assertGreater(rows[-1][15], 1)

    def test_corruption_and_existing_output_rejected(self):
        self.compare([reference.tensor('a',0,[3],1,[-7,0,7])])
        archive=self.root/'D.arc'; sealed=archive.read_bytes()
        self.command(self.probe,'D',self.root/'original',archive,success=False)
        self.assertEqual(archive.read_bytes(), sealed)
        for i, data in enumerate((sealed[:-1],sealed+b'\0',b'BROKEN!!'+sealed[8:],sealed[:8]+b'\xff'*4+sealed[12:])):
            source=self.root/f'bad{i}';source.write_bytes(data)
            target=self.root/f'bad{i}.restored'
            self.command(self.probe,'restore',source,target,success=False)
            self.assertFalse(target.exists())

    def test_adapter_rejects_parent_mutation_and_output_replacement(self):
        with self.assertRaisesRegex(ValueError, 'sealed adaptive parent'):
            adapter.render(adapter.PARENT.read_bytes()+b'\n')
        target=self.root/'header';adapter.materialize(target);sealed=target.read_bytes()
        with self.assertRaises(FileExistsError):
            adapter.materialize(target)
        self.assertEqual(target.read_bytes(), sealed)


if __name__ == '__main__':
    unittest.main()
