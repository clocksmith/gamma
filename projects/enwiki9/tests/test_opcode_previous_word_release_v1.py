"""Synthetic treatment parity and standalone two-file release replay."""
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import subprocess
import sys
import tempfile
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_previous_word_release_build_v1 as release
from tools import opcode_previous_word_compact_build_v1 as compact
from tools import opcode_previous_word_build_v1 as original
from tools import opcode_previous_word_observe_v1 as observe
from tools import opcode_previous_word_compact_observe_v1 as compact_observe
from test_opcode_previous_word_compact_v1 import FIXTURES

# The isolated child imports only the delivered loader and the standard library.
# No project paths, diagnostic shims or observer modules enter its namespace.
STANDALONE = '''import importlib.util,json,pathlib,resource,sys,time
begin,cpu=time.monotonic(),time.process_time()
loader,operation,source,output=sys.argv[1:]
spec=importlib.util.spec_from_file_location('delivered_codec',loader)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
result=getattr(module,operation)(pathlib.Path(source).read_bytes())
with open(output,'xb') as stream:stream.write(result)
print(json.dumps(dict(output_bytes=len(result),cpu_seconds=time.process_time()-cpu,
 elapsed_seconds=time.monotonic()-begin,peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
'''


def reference(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write_json(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, sort_keys=True, indent=2); stream.write('\n')


def diagnostic_module(module):
    def namespace(arm):
        if arm != 'D': raise ValueError('release diagnostic supports D only')
        ns = module.namespace(); ns['_arm'] = 'D'
        return ns
    return types.SimpleNamespace(namespace=namespace)


class ReleaseWordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(FIXTURES) != 6 or sum(map(len, FIXTURES.values())) != 1173:
            raise ValueError('frozen synthetic fixtures differ')
        retained = os.environ.get('GAMMA_PREVIOUS_WORD_RELEASE_UNIT_RESULTS')
        if retained:
            cls.directory = Path(retained); cls.directory.mkdir(parents=True, exist_ok=False)
        else:
            tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='previous_word_release_unit_')
            cls.addClassCleanup(tmp.cleanup); cls.directory = Path(tmp.name)
        names = ['tests/test_opcode_previous_word_release_v1.py',
                 'tests/test_opcode_previous_word_compact_v1.py',
                 'tools/opcode_previous_word_release_build_v1.py',
                 'tools/opcode_previous_word_compact_build_v1.py',
                 'tools/opcode_previous_word_build_v1.py',
                 'lib/opcode_previous_word_v1.py',
                 'tools/opcode_previous_word_observe_v1.py',
                 'tools/opcode_previous_word_compact_observe_v1.py',
                 'tools/opcode_field_compact_observe_v1.py',
                 'tools/opcode_field_repair_cli_v1.py',
                 compact.PARENT, release.SOURCE, release.LOADER]
        cls.inputs = [reference(ROOT / name) for name in names]
        write_json(cls.directory / 'source-inputs.json', cls.inputs)
        cls.started = time.monotonic()
        write_json(cls.directory / 'resource-start.json', dict(
            allowed_cpus=sorted(os.sched_getaffinity(0)),
            address_space_limit=list(resource.getrlimit(resource.RLIMIT_AS)),
            cpu_limit=list(resource.getrlimit(resource.RLIMIT_CPU)),
            file_limit=list(resource.getrlimit(resource.RLIMIT_FSIZE)),
            tmpdir=os.environ.get('TMPDIR'),
            interpreter=dict(path=str(Path(sys.executable).resolve()),
                             sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()),
            scope='Observed process limits and diagnostic resources; no continuous cgroup qualification.'))
        cls.modules = {}
        for name, builder in (('release', release), ('compact', compact), ('original', original)):
            output = cls.directory / name; builder.write_bundle(output)
            cls.modules[name] = observe.load(output / 'program.py')
        cls.release_diagnostic = diagnostic_module(cls.modules['release'])

    @classmethod
    def tearDownClass(cls):
        for row in cls.inputs:
            if reference(ROOT / row['path']) != row:
                raise ValueError('source changed during synthetic suite')
        own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        write_json(cls.directory / 'resource-end.json', dict(
            elapsed_seconds=time.monotonic()-cls.started,
            process_user_cpu_seconds=own.ru_utime, process_system_cpu_seconds=own.ru_stime,
            process_peak_rss_kib=own.ru_maxrss,
            child_user_cpu_seconds=children.ru_utime, child_system_cpu_seconds=children.ru_stime,
            cumulative_child_peak_rss_kib=children.ru_maxrss,
            original_inputs_unchanged=True, corpus_executed=False))

    def test_exact_release_compact_and_original_D_parity(self):
        for name, raw in FIXTURES.items():
            kept = self.directory / name; kept.mkdir(); (kept / 'input.raw').write_bytes(raw)
            rows = {}
            for version in ('original', 'compact', 'release'):
                module = self.release_diagnostic if version == 'release' else self.modules[version]
                execute = observe.execute if version == 'original' else compact_observe.execute
                with self.subTest(fixture=name, version=version):
                    archive, audit = execute(module, 'encode', raw, 'D')
                    restored, decoded = execute(module, 'decode', archive, 'D')
                    repeat, repeated = execute(module, 'encode', restored, 'D')
                    if version == 'release':
                        plain = self.modules['release'].compress(raw)
                        plain_raw = self.modules['release'].decompress(archive)
                    else:
                        plain, _ = execute(module, 'encode', raw, 'D', False)
                        plain_raw, _ = execute(module, 'decode', archive, 'D', False)
                    self.assertEqual(raw, restored); self.assertEqual(raw, plain_raw)
                    self.assertEqual(archive, repeat); self.assertEqual(archive, plain)
                    observe.compare_audits(audit, decoded); observe.compare_audits(audit, repeated)
                    self.assertEqual(sum(audit['updates_by_mode']), 8*audit['parent']['modeled_bytes'])
                    rows[version] = archive, audit
                    for suffix, value in (('arc', archive), ('raw', restored), ('repeat.arc', repeat), ('plain.arc', plain)):
                        (kept / f'{version}.{suffix}').write_bytes(value)
                    for suffix, value in (('encode', audit), ('decode', decoded), ('repeat', repeated)):
                        write_json(kept / f'{version}-{suffix}.audit.json', value)
            self.assertEqual(rows['original'][0], rows['compact'][0]); self.assertEqual(rows['original'][0], rows['release'][0])
            observe.compare_audits(rows['original'][1], rows['compact'][1])
            observe.compare_audits(rows['original'][1], rows['release'][1])
            if name == 'overlap': self.assertGreater(sum(rows['release'][1]['updates_by_mode'][1:]), 0)
            print(json.dumps(dict(fixture=name, raw_bytes=len(raw), archive_bytes=len(rows['release'][0]),
                                  archive_sha256=hashlib.sha256(rows['release'][0]).hexdigest(),
                                  all_three_representations_identical=True)))

    def test_fresh_process_relocated_actual_two_file_codec(self):
        directory = self.directory / 'standalone'; directory.mkdir()
        relocated = directory / 'relocated'; release.write_bundle(relocated)
        original_bundle = self.directory / 'release'
        for path in (relocated, original_bundle):
            self.assertEqual({p.name for p in path.iterdir()}, {'p', 'program.py'})
        records = []
        for name, raw in FIXTURES.items():
            source = directory / (name+'.input'); source.write_bytes(raw)
            outputs = {}
            for label, operation in (('encode','compress'),('decode','decompress'),('repeat','compress')):
                incoming = source if label == 'encode' else outputs['encode' if label == 'decode' else 'decode']
                output = directory / f'{name}-{label}.bin'
                package = original_bundle if label == 'encode' else relocated
                argv = [sys.executable, '-I', '-S', '-B', '-c', STANDALONE,
                        str(package / 'program.py'), operation, str(incoming), str(output)]
                started = time.monotonic()
                with (directory / f'{name}-{label}.stdout').open('xb') as stdout, (directory / f'{name}-{label}.stderr').open('xb') as stderr:
                    completed = subprocess.run(argv, cwd=package, stdout=stdout, stderr=stderr,
                        timeout=20, env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},
                        start_new_session=True)
                record = dict(fixture=name, phase=label, argv=argv, cwd=str(package),
                              returncode=completed.returncode, elapsed_seconds=time.monotonic()-started,
                              output=reference(output) if output.exists() else None)
                if completed.returncode == 0:
                    record['codec_resources'] = json.loads((directory / f'{name}-{label}.stdout').read_text())
                write_json(directory / f'{name}-{label}.execution.json', record); records.append(record)
                self.assertEqual(completed.returncode, 0, (directory / f'{name}-{label}.stderr').read_text())
                outputs[label] = output
            self.assertEqual(outputs['decode'].read_bytes(), raw)
            self.assertEqual(outputs['encode'].read_bytes(), outputs['repeat'].read_bytes())
            expected, _ = observe.execute(self.modules['original'], 'encode', raw, 'D', False)
            self.assertEqual(outputs['encode'].read_bytes(), expected)
        self.assertEqual(len(records), 18)
        write_json(directory / 'commands.json', records)

    def test_prefix_costs_and_no_runtime_arm_requirement(self):
        with self.assertRaises(ValueError): self.release_diagnostic.namespace('P')
        for name, raw in FIXTURES.items():
            costs = []
            for version, module in self.modules.items():
                ns = module.namespace() if version == 'release' else module.namespace('D')
                if version == 'release': self.assertNotIn('_arm', ns)
                modeled = ns['oe'](raw); ns['_limit'] = len(modeled)
                costs.append(ns['lit_prefix'](modeled))
            with self.subTest(fixture=name): self.assertEqual(costs[0], costs[1]); self.assertEqual(costs[0], costs[2])

    def test_malformed_guards(self):
        raw = FIXTURES['boundaries']; archive = self.modules['release'].compress(raw)
        for malformed in (b'', archive[:8], archive[:-1], archive+b'x', struct.pack('>II',0,1)+b'\x80'):
            for version, module in self.modules.items():
                with self.subTest(version=version, malformed_bytes=len(malformed)), self.assertRaises(ValueError):
                    if version == 'release': module.decompress(malformed)
                    else: compact_observe.execute(module, 'decode', malformed, 'D', False)

    def test_bundle_determinism_refuse_overwrite_and_source_authentication(self):
        files = release.bundle(); self.assertEqual(files, release.bundle())
        self.assertEqual(set(files), {'p', 'program.py'}); self.assertEqual(sum(map(len,files.values())),5856)
        for name, value in files.items(): self.assertEqual((self.directory / 'release' / name).read_bytes(), value)
        with self.assertRaises(FileExistsError): release.write_bundle(self.directory / 'release')
        for label, altered in (('source',release.SOURCE),('loader',release.LOADER)):
            root = self.directory / ('changed-'+label)
            for name in (release.SOURCE,release.LOADER):
                path = root / name; path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes()+(b'changed' if name == altered else b''))
            with self.assertRaises(ValueError): release.bundle(root)


if __name__ == '__main__':
    unittest.main()
