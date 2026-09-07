#!/usr/bin/env python3
"""Audit one explicitly authorized closed field replay; never run a codec.

Do not invoke until ROOT supplies the closed job identity and bound digests.
Only this helper's JSON output is written, outside the project.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import stat
import struct
import sys
import time
import traceback

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
CANDIDATE = 'fx2_causal_field_wrt_replay250k_q0_v1'
RESULT = ROOT / 'results' / CANDIDATE
ARMS = 'PKTRS'
OPS = ('encode', 'decode', 'repeat')
CAPS = {'cpus': [2], 'memory_bytes': 1073741824, 'scratch_bytes': 268435456,
        'swap_bytes': 0, 'wall_seconds': 900}
MEANINGFUL = ('arm', 'raw_bytes', 'raw_sha256', 'modeled_bytes', 'modeled_sha256',
 'archive_bytes', 'archive_sha256', 'prefix_bytes', 'payload_bytes', 'probability_digest',
 'synchronization_digest', 'synchronization_rows', 'adapter_state_digest', 'mixture_state_digest',
 'changed_probability_bits', 'donor_present_bits', 'adapter', 'external_parent_q16_bytes',
 'external_parent_q16_sha256', 'exact_raw_inverse', 'standalone_decoder', 'objective_credit_bytes',
 'complete_package_bytes', 'full_corpus_score_bytes', 'source_sha256', 'dictionary_sha256',
 'synchronization_file_sha256')
KERNEL_PINS = {
 'tools/fx2_causal_field_replay_v1.py': 'a722f84df5a6ddda454039bfcf859692217e24144b085b17349ca3ee300a36c3',
 'tools/causal_field_wrt_adapter_v1.py': '649acd80af3ac10e8c2273bde3c2007e07d677bd2941c939494bd0ab76f7c89a',
 'tools/causal_field_parent_coder_v1.py': '6c6f8311b6fda0bbf5fdbd0a45a52ea9f145ebc1fe9d506e1af1923478d5abb8',
 'tools/causal_field_dependency_v1.py': 'f34a42054ba151219c67060cf3420e06fb1e1aff8ea9f01aa408e116b495ec0a',
 'tools/wrt_exact.py': 'ae08246ee8b4708904f78aa5f694111834d6420deece34957c61d6fea3a9797a'}
READ_CAP = 1073741824
read_bytes = 0
bindings = {}

def require(ok, message):
 if not ok:
  raise ValueError(message)

def sha(data):
 return hashlib.sha256(data).hexdigest()

def normalized(value):
 value = value.removeprefix('sha256:')
 require(len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'invalid digest')
 return value

def local(name):
 p = Path(name)
 p = p if p.is_absolute() else ROOT / p
 require(p.is_relative_to(ROOT) and p.resolve() == p and '..' not in p.parts, 'noncanonical local path')
 require(stat.S_ISREG(p.lstat().st_mode), 'not a regular file: ' + str(p))
 return p

def bounded_read(handle, count):
 global read_bytes
 data = handle.read(count)
 read_bytes += len(data)
 require(read_bytes <= READ_CAP, 'terminal audit I/O cap exceeded')
 return data

def fingerprint(name):
 p = local(name)
 with p.open('rb') as f:
  before = os.fstat(f.fileno())
  h = hashlib.sha256()
  while data := bounded_read(f, 1048576):
   h.update(data)
  after = os.fstat(f.fileno())
 identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
 require(identity(before) == identity(after) == identity(p.stat()), 'file changed while hashing')
 ref = {'path': str(p.relative_to(ROOT)), 'bytes': before.st_size, 'sha256': h.hexdigest()}
 old = bindings.get(ref['path'])
 require(old is None or old == ref, 'previously read file changed')
 bindings[ref['path']] = ref
 return ref

def verify(ref):
 found = fingerprint(ref['path'])
 require(found['sha256'] == normalized(ref['sha256']), 'hash mismatch: ' + ref['path'])
 require('bytes' not in ref or found['bytes'] == ref['bytes'], 'byte mismatch: ' + ref['path'])
 return found

def load(name, cap=4194304):
 p = local(name)
 require(p.stat().st_size <= cap, 'JSON exceeds bound')
 with p.open('rb') as f:
  data = bounded_read(f, cap + 1)
 require(len(data) <= cap, 'JSON exceeds bound')
 row = json.loads(data)
 ref = fingerprint(p)
 require(ref['sha256'] == sha(data), 'JSON changed after read')
 return row

def equal(names):
 paths = [local(name) for name in names]
 require(len({p.stat().st_size for p in paths}) == 1, 'file lengths differ')
 streams = [p.open('rb') for p in paths]
 try:
  while True:
   blocks = [bounded_read(f, 1048576) for f in streams]
   require(all(b == blocks[0] for b in blocks), 'exact artifact bytes differ: ' + str(names))
   if not blocks[0]:
    break
 finally:
  for f in streams:
   f.close()

def result(name):
 return RESULT / name

def no_score(row):
 require(row['objective_credit_bytes'] == 0 and row['complete_package_bytes'] is None
         and row['full_corpus_score_bytes'] is None, 'invalid package/score claim')

def expected_outputs(inputs):
 paths = {'projection.json', 'package.json', 'comparison.json', 'stage-decision.json',
  'artifacts.json', 'artifact-index-diagnostics.json', 'work/raw.bin', 'work/modeled.bin',
  'work/q16.bin', 'work/dictionary.bin'}
 for arm in ARMS:
  paths.update(arm + '/' + n for n in ('archive.bin', 'restored.bin', 'repeat.bin', 'result.json'))
  paths.add(arm + '-synchronization.json')
  for op in OPS:
   paths.update(arm + '-' + op + s for s in ('.stdout', '.stderr', '.execution.json'))
   paths.update('work/' + arm + '-' + op + s for s in ('.bin', '.sync'))
 for name in inputs:
  if Path(name).suffix in ('.py', '.cpp', '.h', '.hpp') or Path(name).name == 'LICENSE':
   paths.add('work/source/' + name)
 return paths

def audit(args, output):
 job_path = local(args.closed_job)
 require(job_path.parent in (ROOT / 'operations/adaptive/completed', ROOT / 'operations/adaptive/failed'), 'job is not canonically terminal')
 verify({'path': str(job_path.relative_to(ROOT)), 'sha256': args.job_sha256})
 job = load(job_path)
 require(job['job_id'] == args.job_id and job['candidate_id'] == CANDIDATE, 'closed job identity differs')
 require(job['state'] in ('completed', 'failed') and job.get('finished_at'), 'job lacks terminal state')
 require(not list((ROOT / 'operations/adaptive/running').glob('*' + args.job_id + '.json')), 'job remains in running directory')
 require(job['execution_mode'] == 'discovery', 'wrong mode')
 for key, value in CAPS.items():
  require(job['resource_budget'][key] == value and job['execution_resources']['budget'][key] == value, 'job cap differs: ' + key)
 resources = job['execution_resources']
 require(resources['cleanup_complete'] is True and not resources.get('cleanup_errors'), 'cleanup incomplete')
 require(not job.get('residual_processes_terminated'), 'residual children required termination')
 require(not job.get('wall_budget_exceeded') and not resources.get('abort_reason'), 'outer controller aborted')
 for group in resources['groups']:
  require(not Path(group['path']).exists(), 'owned cgroup remains after terminal cleanup')
 require(resources['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'audit host boot differs')
 worker = Path('/proc') / str(job['worker_pid']) / 'stat'
 if worker.exists():
  fields = worker.read_text().rsplit(')', 1)[1].split()
  require(int(fields[19]) != job['worker_proc_start_ticks'] or fields[0] in ('Z', 'X', 'x'), 'same worker remains live')
 for key in ('runner', 'execution_guard', 'candidate_revision', 'experiment'):
  verify(job[key])
 require(normalized(job['experiment']['sha256']) == normalized(args.experiment_sha256), 'experiment authorization differs')
 contract = load(job['experiment']['path'])
 require(contract['experimentId'] == CANDIDATE and contract['status'] == 'frozen', 'contract is not frozen')
 require(contract['objective']['targetScoreBytes'] == 99000000, 'objective differs')
 revision = load(job['candidate_revision']['path'])
 require(revision['candidateId'] == CANDIDATE and revision['candidateTreeSha256'] == job['candidate_tree_sha256'], 'candidate revision differs')
 inputs = {row['path']: row for row in contract['inputs']}
 require(len(inputs) == len(contract['inputs']), 'duplicate contract inputs')
 plan_refs = [r for r in contract['inputs'] if r.get('id') == 'field-wrt-gate-plan']
 require(len(plan_refs) == 1, 'execution plan is not unique')
 verify(plan_refs[0])
 plan = load(plan_refs[0]['path'])
 require(plan['resources'] == CAPS, 'plan caps differ')
 for name, value in KERNEL_PINS.items():
  require(name in inputs and normalized(inputs[name]['sha256']) == value, 'reviewed kernel differs')
 guard = load(resources['guard_path'])
 require(guard['label'] == job['job_id'] and guard['phase'] == 'diagnostic', 'guard ownership differs')
 require(guard['status'] == 'complete' and guard['returncode'] == job['returncode'], 'guard closure differs')
 require(guard['cgroup']['path'] == resources['cgroup_path'] and guard['cgroup']['inode'] == resources['cgroup_inode'], 'guard group identity differs')
 require(guard['cgroup']['joined_before_exec'] is True and guard['cgroup']['requested_memory_max_bytes'] == CAPS['memory_bytes'], 'guard memory admission differs')
 require(guard['temporary_disk_limit_bytes'] == CAPS['scratch_bytes'] and guard['max_logical_cpus'] == 1, 'guard caps differ')
 require(guard['wall_time_limit_seconds'] is None and guard['geekbench5_single_core_score'] is None, 'unexpected diagnostic calibration contract')
 require(0 <= guard['elapsed_s'] <= CAPS['wall_seconds'] and 0 <= job['elapsed_seconds'] <= CAPS['wall_seconds'] + 5, 'aggregate deadline exceeded')
 require(guard['latest_sample']['processes'] == [] and guard['latest_sample']['tree_live_threads'] == 0, 'guard final process list nonempty')
 require(guard['sample_count'] > 0 and all(guard['measurements'].values()), 'resource measurement incomplete')
 require(not any(guard['guards'].values()), 'a resource guard failed')
 require(not any(guard['cgroup_events']['delta'].get(k, 0) for k in ('max', 'oom', 'oom_kill', 'oom_group_kill')), 'cgroup limit events occurred')
 for key in ('cgroup_memory_peak_bytes', 'max_sampled_cgroup_current_bytes'):
  require(guard['peaks'][key] <= CAPS['memory_bytes'], 'memory peak exceeds cap')
 for key in ('max_sampled_scratch_logical_bytes', 'max_sampled_scratch_allocated_bytes'):
  require(guard['peaks'][key] <= CAPS['scratch_bytes'], 'scratch peak exceeds cap')
 require(guard['peaks']['max_sampled_allowed_cpu_count'] == 1, 'CPU count exceeds cap')
 require(sha(b'\0'.join(os.fsencode(x) for x in guard['command'])) == guard['command_sha256'], 'guard child command digest differs')
 require(str(ROOT / job['tool']) in guard['command'], 'guard child command does not invoke bound runner')
 # Reconstruct the canonical outer guard argv from the same frozen envelope.
 prefix = [str(ROOT / job['execution_guard']['path']), '--limit-kib', str(CAPS['memory_bytes'] // 1024),
  '--official-decimal-limit-kib', str(CAPS['memory_bytes'] // 1024), '--limit-mode', 'tree',
  '--cgroup-path', resources['cgroup_path'], '--cgroup-memory-max-bytes', str(CAPS['memory_bytes']),
  '--temporary-disk-limit-bytes', str(CAPS['scratch_bytes']), '--phase-marker-path', guard['phase_marker_path'],
  '--max-logical-cpus', '1', '--guard-json', str(ROOT / resources['guard_path']), '--label', job['job_id'], '--phase', 'diagnostic']
 for path in guard['scratch_paths']:
  prefix.extend(['--scratch-path', path])
 prefix.extend(['--', *guard['command']])
 aliases = ['/usr/bin/python3', plan['python_executable']]
 require(any(sha(b'\0'.join(os.fsencode(x) for x in [python, *prefix])) == resources['guard_command_sha256'] for python in aliases), 'canonical outer guard command digest differs')
 output['closed_job_and_guard'] = {'job': fingerprint(job_path), 'guard': fingerprint(resources['guard_path']),
  'cleanup_complete': True, 'cgroups_absent': True, 'closed_processes_empty': True,
  'guard_argv_reconstructed': True, 'resources': {'elapsed_seconds': guard['elapsed_s'], 'peaks': guard['peaks'], 'measurements': guard['measurements']}}
 require(job['state'] == 'completed' and job['returncode'] == 0, 'terminal job did not succeed; no positive table audit')
 # This point is reached only after an explicit closed-job authorization and
 # successful canonical resource closure. Result/input payload reads begin here.
 output['payload_boundary_crossed_after_closed_identity'] = True
 for ref in contract['inputs']:
  verify(ref)
 for ref in plan['runtime_files']:
  p = Path(ref['path'])
  require(p.is_absolute() and p.resolve() == p and p.stat().st_size == ref['bytes'], 'runtime path/length differs')
  with p.open('rb') as f:
   h = hashlib.sha256()
   while block := bounded_read(f, 1048576): h.update(block)
  require(h.hexdigest() == normalized(ref['sha256']), 'runtime hash differs')
 stage = load(result('stage-decision.json'))
 require(stage['candidate_id'] == CANDIDATE and stage['experiment'] == job['experiment'] and stage['status'] == 'passed', 'stage not passed/bound')
 require(stage['child_closure_ok'] is True, 'stage child closure failed')
 no_score(stage)
 for key in ('artifacts', 'artifact_index_diagnostics', 'comparison'):
  verify(stage[key])
 index = load(stage['artifacts']['path'])
 diagnostics = load(stage['artifact_index_diagnostics']['path'])
 require(diagnostics['complete'] and not diagnostics['errors'], 'artifact index incomplete')
 excludes = {'artifacts.json', 'artifact-index-diagnostics.json', 'stage-decision.json', 'comparison.json'}
 require(set(diagnostics['index_metadata_excluded']) == excludes, 'artifact exclusions differ')
 names = {row['path'] for row in index}
 require(len(names) == len(index) == diagnostics['indexed_files'], 'duplicate/missing indexed artifact')
 actual = set()
 for p in RESULT.rglob('*'):
  require(not p.is_symlink(), 'symlink in result tree')
  if p.is_file() and p.relative_to(RESULT).as_posix() not in excludes:
   actual.add(p.relative_to(ROOT).as_posix())
 require(actual == names, 'result inventory is not complete')
 require(all((RESULT / name).is_file() for name in expected_outputs(inputs)), 'mandatory declared output absent')
 for ref in index: verify(ref)
 for name, ref in inputs.items():
  if Path(name).suffix in ('.py', '.cpp', '.h', '.hpp') or Path(name).name == 'LICENSE':
   verify({**ref, 'path': str((RESULT / 'work/source' / name).relative_to(ROOT))})
 package = load(result('package.json'))
 require(package['counted_files'] == plan['local_package_files'], 'package inventory differs')
 require({r['path'] for r in package['counted_files']} == set(KERNEL_PINS), 'required local package closure differs')
 require(package['counted_bytes'] == sum(r['bytes'] for r in package['counted_files']) == 66054, 'source cost differs')
 require(package['dependency_closure_complete'] is False, 'incomplete external decoder presented as complete')
 no_score(package)
 for ref in package['external_decode_dependencies']: verify(ref)
 require(package['external_decode_dependency_bytes'] == sum(r['bytes'] for r in package['external_decode_dependencies']), 'external dependencies undercounted')
 pop = plan['population']
 equal([result('work/raw.bin'), ROOT / pop['raw_path']])
 equal([result('work/dictionary.bin'), ROOT / pop['dictionary_path']])
 modeled = local(result('work/modeled.bin'))
 with local(pop['stored_path']).open('rb') as f:
  head = bounded_read(f, 10)
  stored_body = bounded_read(f, 151211)
 require(head == b'\x80\0\0\0\0\7' + (250000).to_bytes(4, 'big'), 'WRT prefix differs')
 with modeled.open('rb') as f: modeled_body = bounded_read(f, 151211)
 require(stored_body == modeled_body and len(modeled_body) == 151210 and modeled_body[0] == 7, 'modeled coordinates differ')
 qref = fingerprint(result('work/q16.bin'))
 require(qref['bytes'] == len(modeled_body) * 16 == 2419360, 'external Q16 length differs')
 # Audit projection only: extract native Q16 words and truth bits; no arithmetic
 # encoding, decoding, predictor execution, or scientific opportunity replay.
 records = 0
 with local(pop['trace_path']).open('rb') as trace, local(result('work/q16.bin')).open('rb') as q:
  while block := bounded_read(trace, 28 * 4096):
   require(len(block) % 28 == 0, 'native record truncation')
   projected = bytearray()
   for fp, value, lo, hi, alo, ahi, truth in struct.iter_unpack('<7I', block):
    require(1 <= value <= 65535, 'invalid projected Q16')
    require(truth == ((modeled_body[records // 8] >> (7 - records % 8)) & 1), 'native truth coordinate differs')
    projected.extend(struct.pack('<H', value))
    records += 1
   require(bytes(projected) == bounded_read(q, len(projected)), 'Q16 stream is not exact truth-free projection')
  require(not bounded_read(q, 1), 'Q16 trailing bytes')
 require(records == len(modeled_body) * 8, 'projection record count differs')
 projection = load(result('projection.json'))
 require(projection['native_intervals_and_payload_exact'] is True and projection['decoder_receives_truth_trace'] is False, 'native projection failed')
 require(projection['records'] == records and projection['q16_sha256'] == qref['sha256'], 'projection report differs')
 parent_ref = fingerprint(pop['parent_archive_path'])
 require(parent_ref['bytes'] == 33429 and projection['parent_archive_sha256'] == parent_ref['sha256'], 'parent archive binding differs')
 with local(pop['parent_archive_path']).open('rb') as f: native_prefix = bounded_read(f, 46)
 comparison = load(stage['comparison']['path'])
 no_score(comparison)
 phases = [arm + '-' + op for arm in ARMS for op in OPS]
 require([row['phase'] for row in stage['commands']] == phases, 'stage phase order/count differs')
 markers = [(row['phase'], row['event']) for row in guard['phase_markers'] if row['event'] in ('start', 'end')]
 require(markers == [(phase, event) for phase in phases for event in ('start', 'end')], 'guard phase markers differ')
 output['phases'] = []
 output['arms'] = {}
 for arm in ARMS:
  reports = []
  for op in OPS:
   phase = arm + '-' + op
   command = load(result(phase + '.execution.json'))
   require(command == stage['commands'][phases.index(phase)], 'phase receipt differs from stage')
   require(command['returncode'] == 0 and not command['launch_error'], 'phase failed')
   require(0 < command['elapsed_cap_seconds'] <= 180 and 0 <= command['elapsed_seconds'] <= command['elapsed_cap_seconds'] + 2, 'phase deadline differs')
   source = result('work/' + arm + '-encode.bin') if op == 'decode' else modeled
   expected = [plan['python_executable'], '-B', str(ROOT / 'tools/fx2_causal_field_replay_v1.py'), op,
    str(source), str(result('work/' + phase + '.bin')), '--sync', str(result('work/' + phase + '.sync')),
    '--q16', str(result('work/q16.bin')), '--dictionary', str(result('work/dictionary.bin')),
    '--arm', arm, '--prefix', native_prefix.hex(), '--raw-bytes', '250000', '--raw-sha256', pop['raw_sha256']]
   require(command['command'] == ['/usr/bin/timeout', '--signal=TERM', '--kill-after=2', str(command['elapsed_cap_seconds']), *expected], 'child process arguments differ')
   report = load(result(phase + '.stdout'))
   require(report['operation'] == op and report['arm'] == arm and report['cpu_affinity'] == [2], 'child identity differs')
   no_score(report)
   require(report['standalone_decoder'] is False and report['exact_raw_inverse'] is True, 'child scope/inverse failed')
   require(report['raw_bytes'] == 250000 and report['raw_sha256'] == pop['raw_sha256'], 'raw report differs')
   require(report['modeled_bytes'] == 151210 and report['modeled_sha256'] == sha(modeled_body), 'modeled report differs')
   require(report['source_sha256'] == KERNEL_PINS['tools/fx2_causal_field_replay_v1.py'], 'child core source differs')
   require(report['dictionary_sha256'] == normalized(inputs[pop['dictionary_path']]['sha256']), 'child dictionary differs')
   require(report['external_parent_q16_bytes'] == qref['bytes'] and report['external_parent_q16_sha256'] == qref['sha256'], 'child Q16 dependency differs')
   require(0 <= report['changed_probability_bits'] <= report['donor_present_bits'] <= records, 'invalid activity counters')
   require(report['prefix_bytes'] == 46 and report['archive_bytes'] == report['payload_bytes'] + 46, 'complete archive accounting differs')
   require(0 <= report['cpu_seconds'] <= 120 and 0 <= report['peak_rss_kib'] * 1024 <= 536870912, 'child resource limit differs')
   sync = fingerprint(result('work/' + phase + '.sync'))
   require(sync['bytes'] == len(modeled_body) * 32 and sync['sha256'] == report['synchronization_file_sha256'], 'state chain fingerprint differs')
   with local(sync['path']).open('rb') as f:
    f.seek(-32, 2)
    require(bounded_read(f, 32).hex() == report['synchronization_digest'], 'final chain state differs')
   reports.append(report)
   output['phases'].append({'phase': phase, 'execution': fingerprint(result(phase + '.execution.json')),
    'report': fingerprint(result(phase + '.stdout')), 'cpu_seconds': report['cpu_seconds'],
    'wall_seconds': command['elapsed_seconds'], 'peak_rss_kib': report['peak_rss_kib'], 'separate_cli_arguments_verified': True})
  require(all({k: report[k] for k in MEANINGFUL} == {k: reports[0][k] for k in MEANINGFUL} for report in reports), 'within-arm state/probability reports differ')
  equal([result('work/' + arm + '-' + op + '.sync') for op in OPS])
  equal([result('work/raw.bin'), result('work/' + arm + '-decode.bin'), result(arm + '/restored.bin')])
  archives = [result(arm + '/archive.bin'), result(arm + '/repeat.bin'), result('work/' + arm + '-encode.bin'), result('work/' + arm + '-repeat.bin')]
  if arm in 'PK': archives.append(ROOT / pop['parent_archive_path'])
  equal(archives)
  archive = fingerprint(archives[0])
  require(archive['bytes'] == reports[0]['archive_bytes'] and archive['sha256'] == reports[0]['archive_sha256'], 'archive report differs')
  with local(archives[0]).open('rb') as f: require(bounded_read(f, 46) == native_prefix, 'full native prefix differs')
  require(comparison['reports'][arm] == reports[0], 'comparison embeds different encode report')
  driver = load(result(arm + '/result.json'))
  require(driver['program_id'] == CANDIDATE and driver['run_scope_label'] == 'opening250k-' + arm, 'driver identity differs')
  require(driver['roundtrip_ok'] is True and driver['determinism']['single_host_byte_equal'] is True, 'driver exact/repeat failed')
  require(driver['data_sha256'] == pop['raw_sha256'] and driver['compressed_sha256'] == archive['sha256'], 'driver content binding differs')
  require(driver['program_size'] == 66054 and driver['hutter_score'] == 66054 + archive['bytes'], 'driver local cost differs')
  require(driver['prize_claimable'] is False and driver['score_accounting_complete'] is False, 'driver proxy promoted to score')
  synchronization = load(result(arm + '-synchronization.json'))
  require(synchronization['every_modeled_byte_identical'] and synchronization['report_projection_identical'] and synchronization['records'] == len(modeled_body), 'state summary differs')
  output['arms'][arm] = {'archive': archive, 'archive_bytes': archive['bytes'], 'changed_probability_bits': reports[0]['changed_probability_bits'],
   'selected_values': reports[0]['adapter']['selected_values'], 'exact_inverse': True, 'repeat_identical': True,
   'every_byte_state_chain_identical': True, 'probability_digest': reports[0]['probability_digest']}
 p, k, t = (output['arms'][arm] for arm in 'PKT')
 require(p['archive'] ['sha256'] == k['archive']['sha256'] and p['probability_digest'] == k['probability_digest'], 'P/K parent identity differs')
 require(p['changed_probability_bits'] == k['changed_probability_bits'] == 0, 'P/K injected specialist')
 active = {arm: output['arms'][arm]['changed_probability_bits'] > 0 and output['arms'][arm]['selected_values'] > 0 for arm in 'TRS'}
 saved = p['archive_bytes'] - t['archive_bytes']
 beats = all(t['archive_bytes'] < output['arms'][arm]['archive_bytes'] for arm in 'RS')
 classification = ('inconclusive_inactive_opportunities_or_controls' if not all(active.values()) else
                   'failed_causal_controls' if not beats else 'weak_compression' if saved <= 0 else 'conditional_archive_gain')
 require(stage['failure_class'] == comparison['failure_class'] == classification, 'scientific classification differs')
 require(comparison['required_controls_active'] == active and comparison['treatment_beats_controls'] == beats, 'active-control report differs')
 require(comparison['archive_saved_bytes'] == saved and comparison['local_source_paying'] == (saved > 66054), 'cost decision differs')
 require(comparison['external_decode_dependency_bytes'] == package['external_decode_dependency_bytes'], 'dependency accounting differs')
 output['classification'] = classification
 output['source_bindings'] = {'all_inputs_match': True, 'input_count': len(inputs), 'retained_sources_match': True}
 output['artifact_index'] = {'complete': True, 'indexed_files': len(index), 'metadata_exclusions': sorted(excludes)}
 output['accounting'] = {'archive_saved_bytes': saved, 'local_source_bytes': 66054,
  'external_q16_bytes': qref['bytes'], 'external_dictionary_bytes': 411996,
  'external_decode_dependency_bytes': package['external_decode_dependency_bytes'],
  'complete_package_bytes': None, 'full_corpus_score_bytes': None, 'objective_credit_bytes': 0,
  'standalone_decoder': False, 'native_parent_probability_execution': False}
 if args.reflection:
  reflection = load(args.reflection)
  require(reflection['candidateId'] == CANDIDATE and normalized(reflection['job']['sha256']) == normalized(args.job_sha256), 'reflection job identity differs')
  require(reflection['objective'] == contract['objective'] and reflection['validity']['valid'] is True, 'reflection validity differs')
  verify(reflection['job'])
  output['reflection'] = {'path': fingerprint(args.reflection), 'decision': reflection['decision'], 'validity': reflection['validity'],
   'scope': 'Checked existing bound JSON fields; no reflection validator or state transition was invoked.'}
 else:
  output['reflection'] = {'status': 'not_supplied', 'transition_authority': False,
   'required_next': 'Canonical terminal reflection must bind this closed job and retained audit and pass its existing validator before any scientific transition.'}
 output['status'] = 'passed_closed_evidence_audit'

def main():
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--closed-job', required=True)
 parser.add_argument('--job-id', required=True)
 parser.add_argument('--job-sha256', required=True)
 parser.add_argument('--experiment-sha256', required=True)
 parser.add_argument('--reflection')
 parser.add_argument('--output-name', default='terminal-audit.json')
 args = parser.parse_args()
 require(Path(args.output_name).name == args.output_name, 'output must remain in reviewer directory')
 target = OUT / args.output_name
 require(not target.exists(), 'audit output already exists')
 resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
 resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
 resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
 signal.alarm(90)
 started = time.monotonic()
 output = {'schema': 'gamma.enwiki9.independent-field-terminal-audit.v1', 'status': 'failed',
  'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()), 'script_sha256': sha(Path(__file__).read_bytes()),
  'authorization': {'closed_job': args.closed_job, 'job_id': args.job_id, 'job_sha256': args.job_sha256,
                    'experiment_sha256': args.experiment_sha256},
  'payload_boundary_crossed_after_closed_identity': False, 'new_codec_runs': 0,
  'source_edits': False, 'process_control': False, 'new_monitor': False, 'launch_authorized': False,
  'limits': {'cpu': [3], 'memory_bytes': 536870912, 'cpu_seconds': 60, 'wall_seconds': 90,
             'scratch_bytes': 33554432, 'input_read_bytes': READ_CAP}}
 try:
  require(os.sched_getaffinity(0) == {3}, 'terminal reviewer must run on CPU3')
  audit(args, output)
 except Exception as error:
  output['error'] = type(error).__name__ + ': ' + str(error)
  output['traceback'] = traceback.format_exc()
 finally:
  output['bindings'] = list(bindings.values())
  output['read_bytes'] = read_bytes
  output['elapsed_seconds'] = time.monotonic() - started
  output['cpu_seconds'] = time.process_time()
  output['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  output['observed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
  with target.open('x') as f:
   json.dump(output, f, sort_keys=True, indent=2, allow_nan=False)
   f.write('\n')
 print(json.dumps({'status': output['status'], 'output': str(target), 'error': output.get('error')}, sort_keys=True))
 return 0 if output['status'] == 'passed_closed_evidence_audit' else 1

if __name__ == '__main__':
 raise SystemExit(main())
