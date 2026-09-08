#!/usr/bin/env python3
"""Reuse measured Deflate and FX2 codecs on two frozen raw populations."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_gate_v1 as phase
from tools import fx2_cmix_transformer_transfer250k_q0_v2 as fx
from tools import opcode_field_repair_gate_v2 as binding

CID = 'matched_frontier_reserved_q0_v1'
SELF = 'tools/matched_frontier_reserved_v1.py'
CAPS = dict(cpus=[2], memory_bytes=10737418240, scratch_bytes=16000000000,
            swap_bytes=0, wall_seconds=3000)
POPULATIONS = [('validation', 250000, '4c6b839c77999f9da19c0f856c40cceb1262aefb536ecc7e7f54e37f694c9b8b'),
               ('confirmation', 1000000, '20b4d8d7e140ccf799ed9af127d03a42af006efc97bd38e3cf2528cd611aaf13')]
require = phase.require


def authenticate(validate_only=False):
    contract_path = ROOT/'operations/adaptive/experiments'/f'{CID}.json'
    contract = phase.read_json(contract_path)
    reference = dict(path=str(contract_path.relative_to(ROOT)), sha256='sha256:'+phase.sha(contract_path))
    require(contract['experimentId'] == CID and contract['status'] == 'frozen'
            and contract['registrationTiming'] == 'prospective', 'contract authority differs')
    for row in contract['inputs']:
        path = ROOT/row['path']
        require(path.resolve() == path and path.is_file()
                and phase.sha(path) == row['sha256'].removeprefix('sha256:'), 'changed input: '+row['path'])
    snapshot = ROOT/'programs'/CID if validate_only else Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    plan = phase.read_json(snapshot/'gate-plan.json')
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS, 'plan authority differs')
    require([(r['name'], r['bytes'], r['sha256']) for r in plan['populations']] == POPULATIONS, 'population selection differs')
    for row in plan['populations']:
        binding.check_file({k:row[k] for k in ('path','bytes','sha256')})
    require({SELF, 'tests/test_matched_frontier_reserved_v1.py', 'lib/driver.py',
             'tools/fx2_cmix_transformer_transfer250k_q0_v2.py',
             'tools/dualstream_grammar_v1.py', 'tools/dualstream_grammar_gate_v1.py',
             'tools/opcode_field_repair_gate_v2.py'} <= {r['path'] for r in plan['source_files']}, 'source closure missing')
    for key in ('source_files', 'evidence'):
        for row in plan[key]: binding.check_file(row)
    for row in plan['runtime_files']: binding.check_file(row, absolute=True)
    package = phase.read_json(ROOT/plan['package_path'])
    for row in package['runtime_members'] + package['source_members']: binding.check_file(row)
    if not validate_only:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) == reference
                and os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID'] == CID, 'canonical invocation absent')
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        jid = marker.parent.name.removesuffix('.resources')
        jobs = list((ROOT/'operations/adaptive/running').glob('*'+jid+'.json'))
        require(len(jobs) == 1, 'ambiguous running job')
        job = phase.read_json(jobs[0])
        require(job['candidate_id'] == CID and job['experiment'] == reference and job['execution_mode'] == 'discovery'
                and all(job['resource_budget'][k] == v for k,v in CAPS.items()), 'job authority differs')
        revision = phase.read_json(ROOT/job['candidate_revision']['path'])
        require(phase.sha(ROOT/job['candidate_revision']['path']) == job['candidate_revision']['sha256'].removeprefix('sha256:'), 'revision changed')
        binding.verify_snapshot(snapshot, revision)
        group = Path(job['execution_resources']['cgroup_path'])
        membership = next(x[3:] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
        require(group == Path('/sys/fs/cgroup'+membership) and group.stat().st_ino == job['execution_resources']['cgroup_inode']
                and (group/'memory.max').read_text().strip() == str(CAPS['memory_bytes'])
                and (group/'memory.swap.max').read_text().strip() == '0' and os.sched_getaffinity(0) == {2}, 'resource enforcement differs')
    return reference, plan, package


def mapping(storage, vocabulary):
    require(storage[:5] == b'\x80\0\0\0\0', 'unexpected native storage header')
    payload = storage[5:]
    allowed = frozenset(vocabulary)
    bad = [(i,b) for i,b in enumerate(payload[5:],5) if b not in allowed]
    return dict(supported=len(payload) >= 10005 and payload[0] == 7 and not bad,
                preprocessed_bytes=len(payload), first_block_header_hex=payload[:5].hex(),
                out_of_alphabet_count=len(bad), first_out_of_alphabet_positions=bad[:16])


def check_archive_header(archive, storage, vocabulary):
    payload = storage[5:]
    require(len(archive) >= 46 and archive[:4] == b'GFV1' and archive[4:9] == payload[:5]
            and archive[14:46].hex() == vocabulary['vocabulary_bitmap_hex'] and archive[9] & 128
            and (int.from_bytes(archive[9:14], 'big') & ((1 << 39)-1)) == len(payload)-5,
            'native archive header differs')


def plain_arm(directory, name, source, marker):
    cli = ROOT/'tools/dualstream_grammar_v1.py'
    archive, restored, repeat = (directory/(name+s) for s in ('.arc','.raw','.repeat.arc'))
    runs = []
    for operation, src, dst, label in [('encode',source,archive,'encode'), ('decode',archive,restored,'decode'), ('encode',restored,repeat,'repeat')]:
        command = [sys.executable,str(cli),operation,str(src),str(dst),'--mode','plain','--frame-size','65536']
        record = phase.run_phase(directory,name+'-'+label,command,
            dict(phase_cpu_seconds=60,phase_address_bytes=536870912,phase_wall_seconds=90),marker)
        if record['timeout'] or record['returncode'] in (-9,-24,-25):
            raise BudgetStop('Deflate phase exceeded its execution limit')
        require(record['returncode'] == 0 and not record['timeout'] and record['error'] is None, 'Deflate phase failed')
        record['codec_resources'] = phase.read_json(directory/(name+'-'+label+'.stdout'))
        runs.append(record)
    require(source.read_bytes() == restored.read_bytes() and archive.read_bytes() == repeat.read_bytes(), 'Deflate inverse or repeat differs')
    return dict(codec='Deflate', status='passed', archive_bytes=archive.stat().st_size,
                exact_inverse=True, deterministic_repeat=True, commands=runs,
                artifacts={k:phase.artifact(p) for k,p in [('archive',archive),('restored',restored),('repeat',repeat)]})


class Native(fx.NativeCodec):
    def execute(self, operation, arguments, cap=600):
        return super().execute(operation, arguments, cap)


class BudgetStop(RuntimeError):
    pass


def failure_class(error):
    if isinstance(error, (MemoryError, BudgetStop)): return 'budget-exhausted'
    if isinstance(error, OSError): return 'infrastructure-failure'
    if isinstance(error, RuntimeError) and any(' exited '+str(c) in str(error) for c in (124,137)):
        return 'budget-exhausted'
    return 'implementation-failure'


def inventory(package, sources):
    # One entry per exact content object; aliases are disclosed, not free hidden assets.
    objects = {}
    for row in package['runtime_members'] + package['source_members'] + sources:
        item = objects.setdefault(row['sha256'], dict(bytes=row['bytes'], paths=[]))
        require(item['bytes'] == row['bytes'], 'inconsistent object size')
        if row['path'] not in item['paths']: item['paths'].append(row['path'])
    counted = [('sha256:'+h, item['bytes']) for h,item in sorted(objects.items())]
    return counted, dict(accounting_class='content-deduplicated-inventory-only',
        objects=objects, dependency_closure_complete=False, complete_package_bytes=None,
        unresolved=['Alias materialization, required options, compiler/runtime licensing and accepted package accounting remain unqualified.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    reference, plan, package = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False))); return 0
    from lib import driver
    directory = ROOT/'results'/CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    work = directory/'work'; work.mkdir()
    fx.RESULT = directory  # Existing native subprocess logger is isolated in this worker.
    stage = dict(schema='gamma.enwiki9.matched-frontier.v1', candidate_id=CID, experiment=reference,
                 status='running', populations=[], objective_credit_bytes=0, complete_package_bytes=None,
                 resource_qualified=False, full_corpus_score_bytes=None,
                 package_inventory=package, note='External FX2 assets and cold-slice framing; no inherited Gamma gains.')
    try:
        for row,name in zip(package['runtime_members'],('cmix','english.dic','weights.tfwc2'),strict=True):
            shutil.copyfile(ROOT/row['path'],work/name)
            (work/name).chmod(0o555 if name == 'cmix' else 0o444)
            require(phase.sha(work/name) == row['sha256'], 'copied native asset differs')
        vocabulary = phase.read_json(ROOT/plan['vocabulary_path'])
        counted = inventory(package, plan['source_files'])
        stage['inventory'] = counted[1]
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        for population in plan['populations']:
            name = population['name']; source = ROOT/population['path']
            row = dict(name=name, input=phase.artifact(source), arms=[]); stage['populations'].append(row)
            row['arms'].append(plain_arm(directory,name+'-P',source,marker))
            native = Native(work,name,package['runtime_members'][0]['sha256'])
            native.execute('preprocess',['-s','english.dic',str(source),str(directory/(name+'.stored'))],30)
            storage = (directory/(name+'.stored')).read_bytes()
            info = mapping(storage,vocabulary['vocabulary_bytes']); row['mapping'] = info
            if not info['supported']:
                row['arms'].append(dict(codec='FX2',status='unsupported-frontend',commands=native.commands)); continue
            result = driver.run(CID,source,population['bytes'],check_determinism=True,module=native,
                artifact_dir=directory/(name+'-FX2'),run_purpose='diagnostic',run_scope_label=name,
                run_context='Matched unchanged external FX2 comparator; package accounting remains incomplete.',
                run_source='canonical-tool',package_inventory=counted)
            check_archive_header((directory/(name+'-FX2/archive.bin')).read_bytes(),storage,vocabulary)
            require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'], 'native inverse or repeat differs')
            row['arms'].append(dict(codec='FX2',status='passed',archive_bytes=result['compressed_size'],
                exact_inverse=True,deterministic_repeat=True,commands=native.commands,
                result=phase.artifact(directory/(name+'-FX2/result.json')),
                per_phase_memory_bytes=None, memory_note='Use closed aggregate cgroup measurement; native per-phase maximum missing.'))
        authenticate()
        stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed',failure_class=failure_class(error),error=type(error).__name__+': '+str(error))
    finally:
        shutil.rmtree(work)  # Owned copied assets and sparse scratch only; durable archives are outside work.
    stage['supported_arms'] = sum(a['status']=='passed' for r in stage['populations'] for a in r['arms'])
    phase.write_json(directory/'artifacts.json',dict(complete=stage['status']=='passed',
        files=[phase.artifact(p) for p in sorted(directory.rglob('*')) if p.is_file()]))
    phase.write_json(directory/'stage-decision.json',stage)
    print(json.dumps(dict(status=stage['status'],supported_arms=stage['supported_arms'])))
    return 0 if stage['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
