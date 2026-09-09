"""Direct-loader synthetic parity; callers provide bounded prebuilt tools."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import fx2_weight_marginal_fixtures_v1 as reference
import fx2_weight_adaptive_loader_v1 as loader


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ['FX2_LOADER_TMP'])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.codec = os.environ['FX2_LOADER_CODEC']
        self.old = os.environ['FX2_LOADER_OLD']
        self.new = os.environ['FX2_LOADER_NEW']
        self.compare = os.environ['FX2_LOADER_COMPARE']

    def call(self, args, success=True):
        p = subprocess.run(list(map(str,args)),capture_output=True,timeout=30)
        self.assertEqual(p.returncode,0 if success else 1,p.stderr.decode(errors='replace'))
        return p

    def fixture(self, name, tensors):
        root=self.root/name;root.mkdir()
        raw=root/'raw';raw.write_bytes(reference.raw_reference(tensors))
        parent=root/'P';parent.write_bytes(reference.encode_reference(tensors))
        fixed=root/'F';fixed.write_bytes(reference.encode_reference(tensors,'D'))
        adaptive=root/'A';self.call([self.codec,'D',parent,adaptive])
        for model in (parent,fixed):
            old=self.call([self.old,raw,model]);new=self.call([self.new,raw,model])
            self.assertEqual(old.stdout,new.stdout)
        a=self.call([self.new,raw,adaptive])
        self.assertEqual(a.stdout,new.stdout)
        compared=json.loads(self.call([self.compare,parent,adaptive]).stdout)
        self.assertTrue(compared['exact_byte_comparison'])
        self.assertEqual(compared['tensor_count'],len(tensors))
        self.assertEqual(compared['reference_digest_hex'],compared['target_digest_hex'])
        return raw,adaptive

    def test_all_existing_populations(self):
        for name,tensors in reference.valid_populations().items():
            with self.subTest(name=name):self.fixture(name,tensors)

    def test_rescale_and_reset(self):
        self.fixture('rescale',[reference.tensor('a',0,[70000],1,[0]*70000),
                                reference.tensor('b',0,[70000],1,[7]*70000)])

    def test_invalid_adaptive_streams(self):
        raw,adaptive=self.fixture('invalid',[reference.tensor('a',0,[4],1,[-7,0,7,0])])
        data=adaptive.read_bytes()
        for index,changed in enumerate((data[:-1],data+b'\0',data[:8]+b'\xff'*4+data[12:])):
            bad=self.root/f'bad{index}';bad.write_bytes(changed)
            p=self.call([self.new,raw,bad],False)
            self.assertIn(b'weights_io_compressed:',p.stderr)

    def test_source_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,'parent differs'):loader.patch(b'changed')

    def test_source_output_exclusive(self):
        target=self.root/'sealed';target.write_bytes(b'keep')
        p=self.call([sys.executable,ROOT/'tools/fx2_weight_adaptive_loader_v1.py','--source',
                     os.environ['FX2_LOADER_SOURCE'],'--output',target],False)
        self.assertEqual(target.read_bytes(),b'keep')
        self.assertIn(b'FileExistsError',p.stderr)


if __name__=='__main__':unittest.main()
