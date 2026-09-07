#!/usr/bin/env python3
"""Independent synthetic event-span oracle and separate-process replay audit."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import resource
import shutil
import signal
import struct
import subprocess
import sys
import time
import traceback
import unittest

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
EXPECTED = {
 'tools/causal_field_wrt_adapter_v1.py': '649acd80af3ac10e8c2273bde3c2007e07d677bd2941c939494bd0ab76f7c89a',
 'tests/test_causal_field_wrt_adapter_v1.py': '430da8bf7d3481f385ce768ae8569763da9965b5d3f864ad51435ecd70c65d2c',
 'tools/causal_field_parent_coder_v1.py': '6c6f8311b6fda0bbf5fdbd0a45a52ea9f145ebc1fe9d506e1af1923478d5abb8',
 'tools/fx2_causal_field_replay_v1.py': 'a722f84df5a6ddda454039bfcf859692217e24144b085b17349ca3ee300a36c3',
 'tests/test_fx2_causal_field_replay_v1.py': '52d450ce3af740e60068cfb192ea3794cdd29525c1ea183b2ed131485df606fc',
}
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
signal.alarm(90)
START = time.monotonic()
receipt = {'status': 'running', 'synthetic_only': True, 'corpus_bytes': 0,
 'command': ['taskset', '-c', '3', 'python3', '-B', str(Path(__file__))],
 'cwd': str(ROOT), 'source_hashes': EXPECTED, 'affinity': sorted(os.sched_getaffinity(0)),
 'limits': {'address_space_bytes': 536870912, 'cpu_seconds': 60, 'wall_seconds': 90,
            'scratch_bytes': 33554432, 'raw_bytes_max': 8192},
 'unit_tests': [], 'segmentation_cases': [], 'cli_cases': [], 'rejection_cases': []}

def sha(data):
 return hashlib.sha256(data).hexdigest()

def save(name, value):
 path = OUT / name
 with path.open('x') as f:
  json.dump(value, f, sort_keys=True, indent=2)
  f.write('\n')
 return {'path': str(path), 'sha256': sha(path.read_bytes())}

def cpu3():
 return [int(x) for row in Path('/proc/stat').read_text().splitlines()
         if row.startswith('cpu3 ') for x in row.split()[1:]]

def reject(name, function):
 try:
  function()
 except ValueError as error:
  receipt['rejection_cases'].append({'name': name, 'error': str(error)})
 else:
  raise AssertionError('accepted malformed fixture: ' + name)

try:
 assert os.sched_getaffinity(0) == {3}
 before = cpu3()
 time.sleep(0.25)
 after = cpu3()
 total = sum(after) - sum(before)
 idle = sum(after[3:5]) - sum(before[3:5])
 receipt['resource_sample'] = {'cpu3_busy_fraction': 1 - idle / total if total else 0,
  'mem_available_bytes': next(int(row.split()[1]) * 1024 for row in Path('/proc/meminfo').read_text().splitlines() if row.startswith('MemAvailable:')),
  'scratch_free_bytes': shutil.disk_usage(OUT).free}
 assert receipt['resource_sample']['cpu3_busy_fraction'] < 0.5
 for name, expected in EXPECTED.items():
  assert sha((ROOT / name).read_bytes()) == expected, name
 os.environ['GAMMA_FIELD_WRT_RETAIN'] = str(OUT / 'adapter-author-tests')
 for name in ('test_causal_field_wrt_adapter_v1', 'test_fx2_causal_field_replay_v1'):
  spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / (name + '.py'))
  unit = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(unit)
  result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(unit))
  receipt['unit_tests'].append({'name': name, 'run': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures)})
  assert result.wasSuccessful()
 import causal_field_wrt_adapter_v1 as adapter_module
 import fx2_causal_field_replay_v1 as replay_module
 from wrt_exact import wrt_byte_transform as transform

 def code(*values):
  return bytes(transform(v) for v in values)

 def token(index):
  if index < 80:
   return code(index + 128)
  index -= 80
  return code(0xd0 + index // 80, 0x80 + index % 80)

 # An independent raw-offset oracle constructs explicit records and every value
 # span, then varies WRT event partitioning without relying on the field parser.
 raw = bytearray()
 records = []
 for first, target, last in ((b'a', b'alpha', b'one'), (b'b', b'beta', b'two'),
                             (b'a', b'alpha', b'one'), (b'c', b'gamma', b'three'),
                             (b'b', b'beta', b'two')):
  raw.extend(b'{{t|a=')
  first_start = len(raw)
  raw.extend(first)
  first_end = len(raw)
  spans = []
  for key, value in ((b'b', target), (b'c', last)):
   raw.extend(b'|' + key + b'=')
   start = len(raw)
   raw.extend(value)
   spans.append((key, value, start, len(raw)))
  raw.extend(b'}}\n')
  records.append((first, first_start, first_end, spans))
 raw = bytes(raw)
 assert len(raw) <= 8192
 rng = random.Random(20260907)
 for case in range(66):
  cuts = [0]
  if case == 0:
   cuts = list(range(len(raw) + 1))
  elif case == 1:
   cuts.append(len(raw))
  elif case == 2:
   cuts = sorted({0, len(raw), *[p for _, a, b, rows in records for p in (a, b)],
                  *[p for _, _, _, rows in records for _, _, a, b in rows for p in (a, b)]})
  else:
   while cuts[-1] < len(raw):
    cuts.append(min(len(raw), cuts[-1] + rng.randrange(1, 12)))
  words = [raw[a:b] for a, b in zip(cuts, cuts[1:])]
  modeled = b'\7' + b''.join(token(i) for i in range(len(words)))
  boundary = {0: 1}
  position = 1
  emissions = {0: b''}
  for i, (a, b) in enumerate(zip(cuts, cuts[1:])):
   for _ in token(i):
    emissions[position] = b''
    position += 1
   emissions[position - 1] = raw[a:b]
   boundary[b] = position
  expected = {}
  for first, fs, fe, rows in records:
   if fs not in boundary or fe not in boundary:
    continue
   for key, value, start, end in rows:
    if start in boundary and end in boundary:
     expected[(b't', b'a', first, key)] = (value, modeled[boundary[start]:boundary[end]], start, end,
                                          boundary[start], boundary[end])
  a = adapter_module.Adapter(words, raw_limit=len(raw))
  output = bytearray()
  for offset, byte in enumerate(modeled):
   emission = a.feed(byte)
   assert emission == emissions[offset], (case, offset)
   output.extend(emission)
  assert bytes(output) == raw
  a.finish()
  actual = {ident: (row['raw'], row['encoded'], row['raw_start'], row['raw_end'], row['wrt_start'], row['wrt_end'])
            for ident, row in a.table.items()}
  assert actual == expected, (case, actual, expected)
  assert a.completed_invocations == len(records)
  receipt['segmentation_cases'].append({'case': case, 'events': len(words), 'associations': len(actual),
    'modeled_bytes': len(modeled), 'modeled_sha256': sha(modeled), 'state_digest': a.state_digest()})
 save('event-segmentation-fixture.json', {'raw_hex': raw.hex(), 'records': [[first.hex(), fs, fe, [[key.hex(), value.hex(), a, b] for key, value, a, b in rows]] for first, fs, fe, rows in records], 'seed': 20260907, 'cases': 66})

 # Actual isolated decoder CLI processes receive no raw, modeled or truth-trace
 # path. Controls occur inside donors; tokens cover one/two/three-byte encodings.
 cli = OUT / 'independent-cli'
 cli.mkdir(exist_ok=False)
 words = [b'unused'] * 3921
 words[0], words[80], words[3920] = b'alpha', b'beta', b'gamma'
 dictionary = b'\n'.join(words) + b'\n'
 (cli / 'dictionary.txt').write_bytes(dictionary)
 def literals(value):
  return b''.join(code(12, b) if b >= 128 or b in (6, 7, 12, 64) else code(b) for b in value)
 def tok(index):
  return token(index) if index < 3920 else code(0xf0, 0xd0, 0x80)
 def record(first, value):
  return literals(b'{{t|a=' + first + b'|b=') + value + literals(b'}}\n')
 value_a = code(64) + tok(0) + code(6) + tok(3920)
 value_b = tok(80)
 modeled = b'\7' + record(b'a', value_a) + record(b'b', value_b) + record(b'a', value_a)
 raw = b'{{t|a=a|b=Alphagamma}}\n{{t|a=b|b=beta}}\n{{t|a=a|b=Alphagamma}}\n'
 assert len(raw) <= 8192
 prefix = b'GFV1\7' + len(raw).to_bytes(4, 'big') + ((1 << 39) + len(modeled)).to_bytes(5, 'big') + b'\xff' * 32
 q16 = b''.join(struct.pack('<H', [1, 65535, 32768, 16000 + (i * 19) % 30000][i % 4]) for i in range(len(modeled) * 8))
 (cli / 'modeled.bin').write_bytes(modeled)
 (cli / 'raw.bin').write_bytes(raw)
 (cli / 'q16.bin').write_bytes(q16)
 reports = {}
 for arm in 'PKTRS':
  for operation in ('encode', 'decode', 'repeat'):
   source = cli / (arm + '-encode.bin') if operation == 'decode' else cli / 'modeled.bin'
   target = cli / (arm + '-' + operation + '.bin')
   sync = cli / (arm + '-' + operation + '.sync')
   command = [sys.executable, '-B', str(ROOT / 'tools/fx2_causal_field_replay_v1.py'), operation,
      str(source), str(target), '--sync', str(sync), '--q16', str(cli / 'q16.bin'),
      '--dictionary', str(cli / 'dictionary.txt'), '--arm', arm, '--prefix', prefix.hex(),
      '--raw-bytes', str(len(raw)), '--raw-sha256', sha(raw)]
   run = subprocess.run(command, cwd=cli, capture_output=True, timeout=20)
   (cli / (arm + '-' + operation + '.stdout')).write_bytes(run.stdout)
   (cli / (arm + '-' + operation + '.stderr')).write_bytes(run.stderr)
   assert run.returncode == 0, (command, run.stderr)
   report = json.loads(run.stdout)
   reports[(arm, operation)] = report
   receipt['cli_cases'].append({'arm': arm, 'operation': operation, 'command': command, 'returncode': run.returncode,
     'output_bytes': target.stat().st_size, 'output_sha256': sha(target.read_bytes()),
     'sync_sha256': sha(sync.read_bytes()), 'report': str(cli / (arm + '-' + operation + '.stdout'))})
  assert (cli / (arm + '-decode.bin')).read_bytes() == raw
  assert (cli / (arm + '-encode.bin')).read_bytes() == (cli / (arm + '-repeat.bin')).read_bytes()
  fields = ('probability_digest', 'synchronization_digest', 'adapter_state_digest', 'mixture_state_digest', 'archive_sha256', 'modeled_sha256')
  for field in fields:
   assert len({reports[(arm, op)][field] for op in ('encode', 'decode', 'repeat')}) == 1
 assert (cli / 'P-encode.bin').read_bytes() == (cli / 'K-encode.bin').read_bytes()
 assert reports[('T', 'encode')]['changed_probability_bits'] > 0
 options = dict(q16=q16, prefix=prefix, words=words, arm='T', raw_bytes=len(raw), raw_sha256=sha(raw))
 archive = (cli / 'T-encode.bin').read_bytes()
 reject('native_payload_extra_zero', lambda: replay_module.replay('decode', archive + b'\0', **options))
 reject('native_payload_missing_flush', lambda: replay_module.replay('decode', archive[:-1], **options))
 reject('wrong_raw_hash', lambda: replay_module.replay('decode', archive, **{**options, 'raw_sha256': '0' * 64}))
 reject('q16_zero', lambda: replay_module.replay('decode', archive, **{**options, 'q16': b'\0\0' + q16[2:]}))
 for name, expected in EXPECTED.items():
  assert sha((ROOT / name).read_bytes()) == expected, name
 receipt['status'] = 'passed'
except BaseException as error:
 receipt['status'] = 'failed'
 receipt['error'] = repr(error)
 traceback.print_exc()
finally:
 receipt['elapsed_seconds'] = time.monotonic() - START
 receipt['self_cpu_seconds'] = time.process_time()
 receipt['child_cpu_seconds'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
 receipt['self_max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 receipt['child_max_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
 receipt['script_sha256'] = sha(Path(__file__).read_bytes())
 receipt['scratch_bytes'] = sum(path.stat().st_size for path in OUT.rglob('*') if path.is_file())
 save('adapter-replay-review.json', receipt)
 print(json.dumps({'status': receipt['status'], 'receipt': str(OUT / 'adapter-replay-review.json')}))
sys.exit(0 if receipt['status'] == 'passed' else 1)
