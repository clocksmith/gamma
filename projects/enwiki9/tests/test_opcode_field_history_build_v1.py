from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_field_history_build_v1 as build
from tools.opcode_field_history_v1 import HistoryAudit, execute, observe


def load(path):
    ns = {'__name__': 'relocated_history', '__file__': str(path / 'program.py')}
    exec(compile((path / 'program.py').read_bytes(), str(path / 'program.py'), 'exec'), ns)
    return ns


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='history_bundle_test_')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.path = self.base / 'codec'
        self.inventory = build.write_bundle(self.path)

    def test_rebuild_and_no_overwrite(self):
        self.assertEqual(build.bundle(), build.bundle())
        self.assertEqual(self.inventory['local_source_bytes'],
                         sum(p.stat().st_size for p in self.path.iterdir()))
        with self.assertRaises(FileExistsError):
            build.write_bundle(self.path)
        self.assertEqual({p.name: p.read_bytes() for p in self.path.iterdir()}, build.bundle())

    def test_all_arms_match_measured_implementation_and_state(self):
        raw = b'<title>A\0B</title><id>12</id><title>C</title>\xff\r\n<broken'
        loader = load(self.path)
        for arm in 'PKDGS':
            expected, witness = execute('encode', raw, arm)
            ns = loader['namespace'](arm)
            captured = observe(ns, HistoryAudit())
            archive = ns['compress'](raw)
            self.assertEqual(archive, expected)
            self.assertEqual(captured['audit'], witness)
            dec = loader['namespace'](arm)
            checked = observe(dec, HistoryAudit())
            restored = dec['decompress'](archive)
            self.assertEqual(restored, raw)
            self.assertEqual(checked['audit'], witness)
            self.assertEqual(loader['namespace'](arm)['compress'](restored), archive)

    def test_isolated_relocation_reproduces_retained_archives(self):
        moved = self.base / 'relocated'
        self.path.rename(moved)
        raw = (ROOT / 'results/opcode_field_history_synthetic_v1/fixture.raw').read_bytes()
        script = '''import hashlib,json
from pathlib import Path
p=Path('program.py');n={'__file__':str(p.resolve()),'__name__':'isolated'}
exec(compile(p.read_bytes(),str(p),'exec'),n)
raw=bytes.fromhex(INPUT_HEX)
result={}
for arm in 'PKDGS':
 a=n['namespace'](arm)['compress'](raw)
 d=n['namespace'](arm)['decompress'](a)
 assert d==raw and n['namespace'](arm)['compress'](d)==a
 result[arm]=hashlib.sha256(a).hexdigest()
print(json.dumps(result))
'''.replace('INPUT_HEX', repr(raw.hex()))
        completed = subprocess.run([sys.executable, '-I', '-c', script], cwd=moved,
                                   capture_output=True, text=True, timeout=120, check=True)
        got = json.loads(completed.stdout)
        for arm in 'PKDGS':
            artifact = ROOT / f'results/opcode_field_history_synthetic_v1/attempt01/{arm}.arc'
            self.assertEqual(got[arm], hashlib.sha256(artifact.read_bytes()).hexdigest())
        self.assertEqual(sorted(p.name for p in moved.iterdir()), ['p', 'program.py'])

    def test_missing_and_replaced_packed_source_rejected(self):
        packed = self.path / 'p'
        original = packed.read_bytes()
        packed.unlink()
        with self.assertRaises(FileNotFoundError):
            load(self.path)
        packed.write_bytes(original + b'x')
        with self.assertRaisesRegex(ValueError, 'packed source identity'):
            load(self.path)

    def test_changed_build_input_rejected(self):
        root = self.base / 'inputs'
        for path in build.INPUTS:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        (root / 'lib/opcode_field_history_v1.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'source identity differs'):
            build.bundle(root)


if __name__ == '__main__':
    unittest.main()
