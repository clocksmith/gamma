"""Full-model synthetic inverses using independently spawned codecs."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fx2_weight_marginal_fixtures_v1 as reference


class ContainerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=os.environ['FX2_CONTAINER_TMP'])
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.probe = os.environ['FX2_CONTAINER_PROBE']
        self.fixed = os.environ['FX2_CONTAINER_FIXED']

    def command(self, binary, mode, source, target, success=True):
        result = subprocess.run([binary, mode, str(source), str(target)], capture_output=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr.decode())
        else:
            self.assertNotEqual(result.returncode, 0)

    def compare(self, tensors):
        original = self.root / 'original'
        original.write_bytes(reference.encode_reference(tensors))
        for arm in ('P','K','D'):
            archive, restored, repeat = [self.root / (arm+s) for s in ('.arc','.raw','.repeat')]
            self.command(self.probe, arm, original, archive)
            self.command(self.probe, 'restore', archive, restored)
            self.command(self.probe, arm, original, repeat)
            self.assertEqual(restored.read_bytes(), original.read_bytes())
            self.assertEqual(repeat.read_bytes(), archive.read_bytes())
        self.command(self.fixed,'P',original,self.root/'fixed.arc')
        self.assertEqual((self.root/'fixed.arc').read_bytes(),(self.root/'P.arc').read_bytes())
        self.assertEqual((self.root/'K.arc').read_bytes(),(self.root/'P.arc').read_bytes())
        return original

    def test_all_tensor_encodings_and_exact_special_bytes(self):
        tensors = [reference.tensor('int4',0,[2,3],1,[-7,0,7,1,-2,4]),
                   reference.tensor('raw',0,[4],0,[0,255,128,10]),
                   reference.tensor('bf16',1,[2],2,[255,255,0,128]),
                   reference.tensor('f32',2,[2],3,[255,255,255,127,0,0,0,128]),
                   reference.tensor('empty',0,[0,4],1,[])]
        self.compare(tensors)

    def test_empty_document(self):
        self.compare([])

    def test_tensor_resets_and_rescaling(self):
        self.compare([reference.tensor('one',0,[70000],1,[0]*70000),
                      reference.tensor('two',0,[70000],1,[7]*70000)])

    def test_corruption_and_exclusive_output(self):
        original=self.compare([reference.tensor('x',0,[4],1,[-7,0,7,0])])
        archive=self.root/'D.arc'; sealed=archive.read_bytes()
        self.command(self.probe,'D',original,archive,False)
        self.assertEqual(archive.read_bytes(),sealed)
        for i,data in enumerate((sealed[:-1],sealed+b'\0',b'BROKEN!!'+sealed[8:],sealed[:8]+b'\xff'*4+sealed[12:])):
            bad=self.root/f'bad{i}';bad.write_bytes(data)
            target=self.root/f'restore{i}'
            self.command(self.probe,'restore',bad,target,False)
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
