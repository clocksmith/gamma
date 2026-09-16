import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zipfile

from lib.fx2_trim_auxiliary_ppm_v1 import materialize, RUNNER, SELF, HELPERS
from lib.fx2_trim_auxiliary_pack_v1 import assemble

ROOT = Path(__file__).resolve().parents[1]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROOT / 'results/fx2_expert_release250k_v3/P-source.zip') as z:
            cls.parent = {n: z.read(n) for n in z.namelist()}
        cls.child = materialize(cls.parent, (ROOT / 'lib/fx2_trim_auxiliary_pack_v1.py').read_bytes())
        cls.tmp = tempfile.TemporaryDirectory(dir='/run/user/1000', prefix='gamma-aux-test-')
        cls.directory = Path(cls.tmp.name)
        cls.executables = {}
        for arm, sources in [('P', cls.parent), ('D', cls.child)]:
            text = sources[RUNNER].decode()
            options = text[text.index('struct ExtractionOptions {'):
                           text.index('[[noreturn]] void UsageError')]
            policies = text[text.index('ExtractionOptions ParseExtractionOptions('):
                            text.index('size_t getFileSize(')]
            header = sources[SELF].decode()
            layout = header[header.index('struct HeaderInfo {'):header.index('void write(')]
            source = cls.directory / (arm + '.cpp')
            source.write_text('''#include <string>
#include <stdexcept>
#include <iostream>
#include <cstdarg>
#include <cstdio>
[[noreturn]] void UsageError(const char* fmt, ...) {
  char message[2048]; va_list args; va_start(args,fmt);
  vsnprintf(message,sizeof(message),fmt,args); va_end(args);
  throw std::runtime_error(message);
}
void RequireReadableFile(const char*, const std::string&) {}
''' + options + policies + layout + '''
static_assert(sizeof(HeaderInfo)==16, "native four-int header size");
int main(int argc, char** argv) {
  if (argc < 2) return 90;
  const char mode = argv[1][0] == '0' ? 0 : argv[1][0];
  int n=argc-1;
  try {
    auto options=ParseExtractionOptions(&n,argv+1);
    ValidateExtractionOptions(options,mode);
    std::cout << options.ppmd_only << options.transformer_only;
    return 0;
  } catch (const std::runtime_error& error) {
    std::cerr << error.what(); return 2;
  }
}
''')
            binary = cls.directory / arm
            result = subprocess.run(['/usr/bin/g++', '-std=c++17', '-O0', str(source), '-o', str(binary)],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.executables[arm] = binary

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_policy(self, arm, args):
        return subprocess.run([str(self.executables[arm]), *args], capture_output=True,
                              text=True, timeout=5)

    def test_existing_auxiliary_decode_is_rejected_new_one_is_accepted(self):
        p = self.run_policy('P', ['d', '--ppmd-only'])
        d = self.run_policy('D', ['d', '--ppmd-only'])
        self.assertEqual(p.returncode, 2)
        self.assertIn('can only be used', p.stderr)
        self.assertEqual((d.returncode, d.stdout), (0, '10'))

    def test_permission_does_not_enable_other_decode_modes(self):
        cases = [
            ['d', '--ppmd-only', '--transformer', 'unused'],
            ['d', '--ppmd-only', '--bytes-only'],
            ['d', '--ppmd-only', '--transformer-only'],
            ['d', '--ppmd-only', '--save-ppmd-bytes', 'unused'],
            ['d', '--ppmd-only', '--save-article-boundaries', 'unused'],
            ['d', '--ppmd-only', '--save-ppmd-probs', 'unused'],
            ['d', '--ppmd-only', '--load-transformer-probs', 'unused'],
            ['d', '--ppmd-only', '--save-transformer-probs', 'unused'],
            ['d', '--ppmd-only', '--ppmd-only'],
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertNotEqual(self.run_policy('D', args).returncode, 0)

    def test_original_main_and_other_option_policies_remain_identical(self):
        cases = [['c', '--transformer', 'unused'], ['n', '--transformer', 'unused'],
                 ['d', '--transformer', 'unused'], ['e'], ['0'], ['d'],
                 ['c', '--ppmd-only'], ['n', '--ppmd-only'], ['0', '--ppmd-only'],
                 ['d', '--bytes-only'], ['c', '--invalid'], ['s', '--ppmd-only']]
        for args in cases:
            with self.subTest(args=args):
                p, d = self.run_policy('P', args), self.run_policy('D', args)
                self.assertEqual((p.returncode, p.stdout, p.stderr),
                                 (d.returncode, d.stdout, d.stderr))

    def test_changed_source_and_helper_set_is_exact(self):
        self.assertEqual(set(self.child)-set(self.parent), {'gamma_pack_auxiliary.py'})
        self.assertEqual({n for n in self.parent if self.parent[n] != self.child[n]},
                         {RUNNER, SELF})
        for command in HELPERS:
            self.assertIn(('RunSubprocess("'+command+' --ppmd-only")').encode(), self.child[SELF])
            self.assertNotIn(('RunSubprocess("'+command+'")').encode(), self.child[SELF])
        for name in ['src/predictor.cpp','src/coder/encoder.cpp','src/coder/decoder.cpp',
                     'models/6m-q4-fp32.tfwc2','dictionary/english.dic']:
            self.assertEqual(self.parent[name],self.child[name])

    def test_changed_parent_and_double_application_fail_closed(self):
        changed=dict(self.parent);changed[RUNNER]+=b'\n'
        with self.assertRaises(ValueError): materialize(changed,b'x')
        with self.assertRaises(ValueError): materialize(self.child,b'x')

    def test_assembly_layout_and_native_header_sizes(self):
        with tempfile.TemporaryDirectory(dir=self.directory) as td:
            root=Path(td);parts=[]
            values=[b'ELF-test\x00',b'dictionary compressed',b'order compressed',b'weight data']
            for i,data in enumerate(values):
                p=root/str(i);p.write_bytes(data);parts.append(p)
            target=root/'cmix';row=assemble(*parts,target)
            expected=b''.join(values)+struct.pack('<iiii',len(values[1]),len(values[2]),0,len(values[3]))
            self.assertEqual(target.read_bytes(),expected)
            self.assertEqual(row['bytes'],sum(map(len,values))+16)
            self.assertEqual(target.stat().st_mode & 0o111,0o111)
            with self.assertRaises(ValueError): assemble(*parts,target)
            link=root/'link';link.symlink_to(parts[0])
            with self.assertRaises(ValueError): assemble(link,*parts[1:],root/'bad')
            parts[1].write_bytes(b'')
            with self.assertRaises(ValueError): assemble(*parts,root/'empty')


if __name__ == '__main__':
    unittest.main()
