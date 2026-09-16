"""Exercise real header extraction and sandbox wiring with an explicit copy stub.

The stub is not PPM, a compressor, or evidence of native probability parity.
Only embedded layout, command plumbing, dictionary checking and isolation are
tested here. The subsequent admitted corpus/asset gate must use actual cmix.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from lib.fx2_trim_auxiliary_pack_v1 import assemble
from tools.fx2_trim_auxiliary_ppm_v1 import sandbox, test_archive as assemble_test_archive, RUNTIME

ROOT = Path(__file__).resolve().parents[1]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir='/run/user/1000', prefix='gamma-bootstrap-unit-')
        cls.root = Path(cls.temp.name)
        cls.runtime = json.loads((ROOT / RUNTIME).read_text())
        with zipfile.ZipFile(ROOT / 'results/fx2_trim_auxiliary_preflight_v1/D-source.zip') as z:
            cls.dictionary = z.read('dictionary/english.dic')
            (cls.root / 'self_extract.h').write_bytes(z.read('src/readalike_prepr/self_extract.h'))
        (cls.root / 'extract.cpp').write_text('#include <cstring>\n#include "self_extract.h"\n'
            'int main(int argc,char**argv){if(argc!=2)return 91;'
            'if(!strcmp(argv[1],"C"))return selfextract_comp();'
            'if(!strcmp(argv[1],"D"))return selfextract_decomp();return 92;}\n')
        (cls.root / 'copy.cpp').write_text('''#include <fstream>
#include <cstring>
int main(int argc,char**argv) {
 if(argc!=5 || strcmp(argv[1],"-d") || strcmp(argv[4],"--ppmd-only"))return 93;
 std::ifstream in(argv[2],std::ios::binary);
 std::ofstream out(argv[3],std::ios::binary);
 if(!in || !out)return 94;
 out << in.rdbuf(); out.close(); return out.fail()?95:0;
}
''')
        for name in ['extract', 'copy']:
            r = subprocess.run(['/usr/bin/g++', '-std=c++17', '-O0',
                                str(cls.root / (name + '.cpp')), '-o', str(cls.root / name)],
                               capture_output=True, text=True, timeout=60)
            if r.returncode: raise AssertionError(r.stderr)
        cls.helper, cls.binary = cls.root / 'extract', cls.root / 'copy'
        cls.dict = cls.root / 'dict'; cls.dict.write_bytes(cls.dictionary)
        cls.order = cls.root / 'order'; cls.order.write_bytes(b'12\n7\n31\n')
        cls.weights = cls.root / 'weights'; cls.weights.write_bytes(b'synthetic weight payload\0\xff')
        cls.payload = cls.root / 'payload'; cls.payload.write_bytes(b'synthetic arithmetic payload\0\xfe')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_sandbox(self, work, mode):
        return subprocess.run(sandbox(self.runtime, work, self.helper, ['/test/extract', mode]),
                              capture_output=True, text=True, timeout=15)

    def test_compressor_extracts_only_its_embedded_assets(self):
        work = self.root / 'compressor'; work.mkdir()
        assemble(self.binary, self.dict, self.order, self.weights, work / 'cmix')
        r = self.run_sandbox(work, 'C')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((work / '.dict').read_bytes(), self.dictionary)
        self.assertEqual((work / '.new_article_order').read_bytes(), self.order.read_bytes())
        self.assertEqual((work / '.tfweights').read_bytes(), self.weights.read_bytes())
        self.assertEqual((work / '.decomp_bin').read_bytes(), self.binary.read_bytes())

    def test_decoder_extracts_exact_dictionary_weights_and_payload(self):
        work = self.root / 'decoder'; work.mkdir()
        assemble_test_archive(self.binary, self.dict, self.weights, self.payload, work / 'archive9')
        r = self.run_sandbox(work, 'D')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((work / '.dict').read_bytes(), self.dictionary)
        self.assertEqual((work / '.tfweights').read_bytes(), self.weights.read_bytes())
        self.assertEqual((work / '.ready4cmix_decomp').read_bytes(), self.payload.read_bytes())

    def test_wrong_dictionary_fails_the_real_header_check(self):
        work = self.root / 'wrong'; work.mkdir()
        wrong = self.root / 'wrong-dict'; wrong.write_bytes(self.dictionary[:-1])
        assemble_test_archive(self.binary, wrong, self.weights, self.payload, work / 'archive9')
        r = self.run_sandbox(work, 'D')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('dictionary decompressed to', r.stderr)
        self.assertFalse((work / '.ready4cmix_decomp').exists())

    def test_host_assets_and_repository_are_not_visible(self):
        work = self.root / 'visibility'; work.mkdir()
        # Use shell builtins only; no /usr or test utility is supplied.
        command = ['/bin/sh', '-c',
                   'test ! -e "$1" && test ! -e /usr && test ! -e /etc/ld.so.cache',
                   'visibility-probe', str(ROOT)]
        r = subprocess.run(sandbox(self.runtime, work, self.helper, command),
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__':
    unittest.main()
