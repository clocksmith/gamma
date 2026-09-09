#!/usr/bin/env python3
"""Decode-only event observation on one frozen development archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_gate_v1 as phase
from tools import opcode_field_repair_gate_v2 as binding
from tools.opcode_field_compact_gate_v1 import BudgetStop, compare, require_phase
from tools.opcode_event_opportunity_observe_v1 import PARENT_SHA256, execute

CID = 'opcode_event_opportunity_decode250k_q0_v1'
SELF = 'tools/' + CID + '.py'
INPUTS = 'operations/provenance/opcode_event_opportunity_decode250k_v1_inputs.json'
SCHEMA = 'gamma.enwiki9.opcode-event-opportunity-inputs.v1'
CAPS = dict(cpus=[3], memory_bytes=2147483648, scratch_bytes=67108864,
            swap_bytes=0, wall_seconds=600)
PHASES = dict(phase_cpu_seconds=120, phase_wall_seconds=180, phase_address_bytes=2147483648)
SOURCES = {SELF, 'tests/test_' + CID + '.py',
           'tools/opcode_event_opportunity_observe_v1.py',
           'tools/opcode_field_compact_observe_v1.py', 'tools/opcode_field_repair_cli_v1.py',
           'tools/opcode_field_compact_gate_v1.py', 'tools/opcode_field_repair_gate_v2.py',
           'tools/dualstream_grammar_gate_v1.py', 'tools/dualstream_grammar_v1.py'}
PRIMARY = ('parent_source', 'parent_archive', 'parent_raw', 'parent_audit')
EXPECTED = {
    'parent_source': ('programs/opcode_field_compact_v1/p', 5423, PARENT_SHA256),
    'parent_archive': ('results/opcode_event_parse250k_q0_v1/P.arc', 67658,
                       'bda617eab7628f7cec6724ca3d82bf505efee9c2be4813dd404dcfa715140e6f'),
    'parent_raw': ('results/opcode_event_parse250k_q0_v1/P.raw', 250000,
                  '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'),
    'parent_audit': ('results/opcode_event_parse250k_q0_v1/P-decode.audit.json', 24889,
                    '7aa2091cc61cf1bc838062df300aff0719d23eec0cfc734508f56d5633356315')}
RECORD = struct.Struct('<16I')
SENTINEL = 0xffffffff
LAYOUT = ['index', 'position', 'f', 'w', 'pg', 'c', 'previous_event', 'event',
          'pre_c0', 'pre_c1', 'pre_c2', 'pre_total', 'post_c0', 'post_c1', 'post_c2', 'post_total']
require = phase.require


def ceil_log2_ratio(numerator, denominator):
    """Smallest integer k with numerator <= denominator*2**k, for ratio >=1."""
    require(type(numerator) is int and type(denominator) is int
            and numerator >= denominator > 0, 'invalid ideal-cost ratio')
    k = max(0, numerator.bit_length() - denominator.bit_length())
    return k + (numerator > denominator << k)


class EventSink:
    """Bounded trace, causal count validation, and exact fixed-parse ceilings."""
    def __init__(self, stream, modeled_bytes, max_events, chunk_events):
        require(type(modeled_bytes) is int and 0 <= modeled_bytes <= 230968
                and type(max_events) is int and 0 <= max_events <= modeled_bytes
                and type(chunk_events) is int and 1 <= chunk_events <= 4096, 'invalid sink bounds')
        self.stream, self.modeled, self.maximum, self.chunk_size = stream, modeled_bytes, max_events, chunk_events
        self.count, self.previous, self.position = 0, None, -1
        self.events, self.thirds = [0]*3, [[0]*3 for _ in range(3)]
        self.transitions = [[0]*3 for _ in range(4)]
        self.contexts, self.rows, self.chunks = {}, {}, []
        self.numerator = self.denominator = 1
        self.chunk_count, self.chunk_third = 0, None
        self.closed = False

    def flush(self):
        if self.chunk_count:
            self.chunks.append(dict(first_event=self.count-self.chunk_count, events=self.chunk_count,
                                    third=self.chunk_third, numerator_hex=format(self.numerator, 'x'),
                                    denominator_hex=format(self.denominator, 'x'),
                                    upper_bits=ceil_log2_ratio(self.numerator, self.denominator)))
        self.numerator = self.denominator = 1
        self.chunk_count = 0

    def __call__(self, row):
        require(not self.closed and self.count < self.maximum, 'event sink limit or closure')
        key, pre, post = tuple(row['key']), tuple(row['pre_counts']), tuple(row['post_counts'])
        event, position = row['event'], row['position']
        require(len(key) == 4 and all(type(v) is int and 0 <= v < n for v, n in zip(key, (7, 4, 5, 8))), 'event key')
        require(type(event) is int and 0 <= event < 3 and type(position) is int
                and self.position < position < self.modeled and (self.count != 0 or position == 0)
                and row['index'] == self.count and row['previous_event'] == self.previous, 'event sequence')
        require(len(pre) == len(post) == 3 and all(type(v) is int and v > 0 for v in pre+post)
                and type(row['pre_total']) is int and sum(pre) == row['pre_total'] <= 4096
                and type(row['post_total']) is int and sum(post) == row['post_total'] <= 4096
                and pre == self.rows.get(key, (1, 1, 1)), 'event count continuity')
        updated = list(pre); updated[event] += 1
        if sum(updated) > 4096:
            updated = [(v+1)//2 for v in updated]
        require(tuple(updated) == post, 'event count update')
        previous = 3 if self.previous is None else self.previous
        third = position*3//self.modeled
        if self.chunk_count and third != self.chunk_third:
            self.flush()
        values = (self.count, position, *key, SENTINEL if previous == 3 else previous, event,
                  *pre, row['pre_total'], *post, row['post_total'])
        require(self.stream.write(RECORD.pack(*values)) == RECORD.size, 'short event write')
        self.events[event] += 1; self.thirds[third][event] += 1
        self.transitions[previous][event] += 1
        self.contexts.setdefault(key, [[0]*3 for _ in range(4)])[previous][event] += 1
        self.rows[key] = post
        self.numerator *= row['pre_total']; self.denominator *= pre[event]
        self.chunk_count += 1; self.chunk_third = third
        self.count += 1; self.previous = event; self.position = position
        if self.chunk_count == self.chunk_size:
            self.flush()

    def finish(self):
        require(not self.closed and (self.count > 0 or self.modeled == 0), 'incomplete or closed event sink')
        self.flush(); self.closed = True
        third_upper = [sum(c['upper_bits'] for c in self.chunks if c['third'] == t) for t in range(3)]
        return dict(schema='gamma.enwiki9.opcode-event-opportunity-summary.v1', record_layout=LAYOUT,
                    record_format='<16I', record_bytes=64, previous_start_sentinel=SENTINEL,
                    modeled_bytes=self.modeled, event_count=self.count, event_bytes=self.count*64,
                    event_counts=self.events, event_counts_by_modeled_third=self.thirds,
                    previous_event_order=[0, 1, 2, None], transition_counts=self.transitions,
                    context_transition_counts=[dict(key=k, counts=v) for k, v in sorted(self.contexts.items())],
                    ideal_event_saving_upper_bits=sum(third_upper), ideal_upper_bits_by_third=third_upper,
                    upper_bound_chunks=self.chunks,
                    bound_scope='Perfect event probabilities on this fixed parse only; not finite archive savings or evidence of previous-event conditioning value.')


def validate_plan(plan):
    require(set(plan) == {'schema', 'candidate_id', 'resources', 'phase_resources', *PRIMARY,
                         'modeled_bytes', 'max_events', 'chunk_events', 'source_files', 'runtime_files', 'evidence'}, 'input-plan fields')
    require(plan['schema'] == SCHEMA and plan['candidate_id'] == CID
            and plan['resources'] == CAPS and plan['phase_resources'] == PHASES
            and plan['modeled_bytes'] == plan['max_events'] == 230968 and plan['chunk_events'] == 4096, 'input-plan identity or bounds')
    for name, (path, size, digest) in EXPECTED.items():
        require(plan[name] == dict(path=path, bytes=size, sha256=digest), 'development input differs: '+name)
    require(SOURCES <= {r['path'] for r in plan['source_files']} and plan['runtime_files'] and plan['evidence'], 'source/runtime/evidence closure')


def verify_inputs(plan):
    for row in [*(plan[name] for name in PRIMARY), *plan['source_files'], *plan['evidence']]:
        binding.check_file(row)
    for row in plan['runtime_files']:
        binding.check_file(row, absolute=True)


def authenticate(validate_only=False):
    contract_path = ROOT/'operations/adaptive/experiments'/f'{CID}.json'
    contract = phase.read_json(contract_path)
    reference = dict(path=str(contract_path.relative_to(ROOT)), sha256='sha256:'+phase.sha(contract_path))
    require(contract['experimentId'] == CID and contract['status'] == 'frozen'
            and contract['registrationTiming'] == 'prospective' and contract['objectiveCreditBytes'] == 0, 'contract authority')
    bound = {r['path']: r['sha256'].removeprefix('sha256:') for r in contract['inputs']}
    require(len(bound) == len(contract['inputs']), 'duplicate contract inputs')
    for name, digest in bound.items():
        path = ROOT/name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and path.resolve() == path and phase.sha(path) == digest, 'changed contract input')
    require(bound.get(INPUTS) == phase.sha(ROOT/INPUTS), 'unfrozen input plan')
    plan = phase.read_json(ROOT/INPUTS); validate_plan(plan); verify_inputs(plan)
    for row in [*(plan[name] for name in PRIMARY), *plan['source_files'], *plan['evidence']]:
        require(bound.get(row['path']) == row['sha256'], 'unfrozen input reference')
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve() for r in plan['runtime_files']), 'current interpreter unbound')
    if not validate_only:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) == reference
                and os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID'] == CID, 'canonical invocation absent')
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        jid = marker.parent.name.removesuffix('.resources')
        jobs = list((ROOT/'operations/adaptive/running').glob('*'+jid+'.json'))
        require(len(jobs) == 1, 'ambiguous running job')
        job = phase.read_json(jobs[0])
        require(job['candidate_id'] == CID and job['experiment'] == reference and job['execution_mode'] == 'discovery'
                and all(job['resource_budget'][k] == v for k, v in CAPS.items()), 'job authority')
        revision = ROOT/job['candidate_revision']['path']
        require(phase.sha(revision) == job['candidate_revision']['sha256'].removeprefix('sha256:'), 'revision changed')
        binding.verify_snapshot(Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT']), phase.read_json(revision))
        group = Path(job['execution_resources']['cgroup_path'])
        member = next(x[3:] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
        require(group == Path('/sys/fs/cgroup'+member) and group.stat().st_ino == job['execution_resources']['cgroup_inode']
                and (group/'memory.max').read_text().strip() == str(CAPS['memory_bytes'])
                and (group/'memory.swap.max').read_text().strip() == '0'
                and os.sched_getaffinity(0) == {3}, 'resource enforcement')
    return reference, plan


def decode_phase(plan, directory, label):
    """Also exercised with explicitly constructed synthetic inputs in tests."""
    require(label in ('P', 'K', 'K-repeat'), 'unknown decode phase')
    for name in ('parent_source', 'parent_archive'):
        binding.check_file(plan[name])
    outputs = [directory/(label+suffix) for suffix in ('.raw', '.audit.json', '.events.bin', '.events.json')]
    require(not any(p.exists() for p in outputs), 'decode output already exists')
    packed = (ROOT/plan['parent_source']['path']).read_bytes()
    archive = (ROOT/plan['parent_archive']['path']).read_bytes()
    require(len(archive) <= 67658, 'archive input bound')
    started, cpu = time.monotonic(), time.process_time()
    if label == 'P':
        output, audit = execute(packed, 'decode', archive)
    else:
        with outputs[2].open('xb') as stream:
            sink = EventSink(stream, plan['modeled_bytes'], plan['max_events'], plan['chunk_events'])
            output, audit = execute(packed, 'decode', archive, emit=sink, max_events=plan['max_events'])
        summary = sink.finish()
        summary.update(arithmetic_operations=audit['arithmetic_events'], literal_predictor_bits=audit['predictor_bits'])
        phase.write_json(outputs[3], summary)
    require(len(output) == plan['parent_raw']['bytes'] and len(output) <= 250000
            and hashlib.sha256(output).hexdigest() == plan['parent_raw']['sha256']
            and audit['modeled_bytes'] == plan['modeled_bytes'], 'decoded input identity')
    with outputs[0].open('xb') as target:
        target.write(output)
    phase.write_json(outputs[1], audit)
    return dict(output_bytes=len(output), cpu_seconds=time.process_time()-cpu,
                elapsed_seconds=time.monotonic()-started,
                peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def run_comparison(directory, plan_path, marker, limits=PHASES):
    plan = phase.read_json(plan_path); verify_inputs(plan)
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    original_plan_sha = phase.sha(plan_path)
    expected = (ROOT/plan['parent_raw']['path']).read_bytes()
    expected_audit = phase.read_json(ROOT/plan['parent_audit']['path'])['parent']
    commands = []
    for label in ('P', 'K', 'K-repeat'):
        command = [sys.executable, str(ROOT/SELF), '--decode-phase', label,
                   '--inputs', str(plan_path), '--output', str(directory)]
        row = phase.run_phase(directory, label, command, limits, marker)
        commands.append(row)
        require_phase(row, (directory/(label+'.stderr')).read_text(errors='replace'))
        try:
            row['codec_resources'] = phase.read_json(directory/(label+'.stdout'))
        except (OSError, ValueError) as error:
            row.update(codec_resources=None, missing_diagnostics=[str(error)])
        compare(expected, (directory/(label+'.raw')).read_bytes(), directory, label+'-inverse')
        compare(expected_audit, phase.read_json(directory/(label+'.audit.json')), directory, label+'-parent-audit')
    require(phase.sha(directory/'K.events.bin') == phase.sha(directory/'K-repeat.events.bin'), 'event repeat differs')
    summary = phase.read_json(directory/'K.events.json')
    compare(summary, phase.read_json(directory/'K-repeat.events.json'), directory, 'event-summary-repeat')
    verify_inputs(plan)
    require(phase.sha(plan_path) == original_plan_sha, 'input plan changed during decoding')
    return dict(commands=commands, correctness_pass=True, controls_equivalent=True,
                frozen_inputs_reverified=True, summary=summary, source_archive=plan['parent_archive'],
                archive_saving_bytes=0, objective_credit_bytes=0,
                interpretation='observation only; no treatment probabilities or new archive')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--decode-phase', choices=('P', 'K', 'K-repeat'))
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.decode_phase:
        require(args.inputs is not None and args.output is not None and not args.validate_only, 'decode phase arguments')
        print(json.dumps(decode_phase(phase.read_json(args.inputs), args.output, args.decode_phase), sort_keys=True))
        return 0
    require(args.inputs is None and args.output is None, 'canonical gate has fixed inputs/output')
    reference, plan = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False)))
        return 0
    directory = ROOT/'results'/CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-event-opportunity-decode-gate.v1', candidate_id=CID,
                 experiment=reference, status='running', correctness_pass=False, objective_credit_bytes=0)
    started = time.monotonic()
    try:
        stage.update(run_comparison(directory, ROOT/INPUTS, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate()
        if time.monotonic()-started > CAPS['wall_seconds']:
            raise BudgetStop('aggregate deadline exceeded')
        stage['status'] = 'passed'
    except Exception as error:
        stage.update(status='failed', correctness_pass=False,
                     failure_class='budget-exhausted' if isinstance(error, (BudgetStop, MemoryError))
                     else 'infrastructure-failure' if isinstance(error, OSError) else 'implementation-failure',
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory/'artifacts.json', dict(complete=stage['status'] == 'passed',
                     files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory/'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
