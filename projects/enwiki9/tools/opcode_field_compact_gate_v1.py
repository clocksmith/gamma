#!/usr/bin/env python3
"""Bounded replay of compact source against retained archives and shared state."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_gate_v1 as phase
from tools import opcode_field_repair_gate_v2 as binding

CID = 'opcode_field_compact_v1'
SELF = 'tools/opcode_field_compact_gate_v1.py'
CLI = 'tools/opcode_field_compact_observe_v1.py'
CAPS = dict(cpus=[2], memory_bytes=12884901888, scratch_bytes=2147483648,
            swap_bytes=0, wall_seconds=12000)
PHASES = dict(phase_cpu_seconds=1200, phase_wall_seconds=1500, phase_address_bytes=8589934592)
POPULATIONS = [('development',250000,'665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'),
               ('validation',250000,'4c6b839c77999f9da19c0f856c40cceb1262aefb536ecc7e7f54e37f694c9b8b'),
               ('confirmation',1000000,'20b4d8d7e140ccf799ed9af127d03a42af006efc97bd38e3cf2528cd611aaf13')]
require = phase.require


def validate_plan(plan):
    require(plan['candidate_id']==CID and plan['resources']==CAPS and plan['phase_resources']==PHASES,
            'plan identity or resource bounds differ')
    require([(r['name'],r['input']['bytes'],r['input']['sha256']) for r in plan['populations']]==POPULATIONS,
            'population selection differs')
    sources = {r['path'] for r in plan['source_files']}
    require({SELF,CLI,'tools/opcode_field_repair_cli_v1.py','tools/dualstream_grammar_gate_v1.py',
             'tools/dualstream_grammar_v1.py','tools/opcode_field_repair_gate_v2.py',
             'tests/test_opcode_field_compact_gate_v1.py','tools/research_contracts.py'} <= sources,
            'source closure missing')
    require({Path(r['path']).name for r in plan['package_files']}=={'p','program.py'}
            and len(plan['package_files'])==2, 'required compact source differs')
    require(all(r['path'].startswith('programs/'+CID+'/') for r in plan['package_files']),
            'package belongs to another candidate')
    require(plan['runtime_files'] and plan['evidence'], 'runtime or evidence inventory missing')


def authenticate(validate_only=False):
    contract_path=ROOT/'operations/adaptive/experiments'/f'{CID}.json'
    contract=phase.read_json(contract_path)
    reference=dict(path=str(contract_path.relative_to(ROOT)),sha256='sha256:'+phase.sha(contract_path))
    require(contract['experimentId']==CID and contract['status']=='frozen'
            and contract['registrationTiming']=='prospective','contract authority differs')
    bound={}
    for row in contract['inputs']:
        path=ROOT/row['path']
        require(path.resolve()==path and phase.sha(path)==row['sha256'].removeprefix('sha256:'),
                'changed contract input: '+row['path'])
        bound[row['path']]=row['sha256'].removeprefix('sha256:')
    snapshot=ROOT/'programs'/CID if validate_only else Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    plan=phase.read_json(snapshot/'gate-plan.json');validate_plan(plan)
    for row in plan['populations']:
        for key in ('input','archive','audit'):
            binding.check_file(row[key])
            require(bound.get(row[key]['path'])==row[key]['sha256'],'unfrozen comparison input')
    for key in ('source_files','evidence'):
        for row in plan[key]:binding.check_file(row)
    for row in plan['runtime_files']:binding.check_file(row,absolute=True)
    for row in plan['package_files']:binding.check_file(row,snapshot=snapshot,candidate=CID)
    require(sum(r['bytes'] for r in plan['package_files'])==5746,'sealed compact source size differs')
    if not validate_only:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])==reference
                and os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID']==CID,'canonical invocation absent')
        marker=Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS']);jid=marker.parent.name.removesuffix('.resources')
        jobs=list((ROOT/'operations/adaptive/running').glob('*'+jid+'.json'))
        require(len(jobs)==1,'ambiguous running job')
        job=phase.read_json(jobs[0])
        require(job['candidate_id']==CID and job['experiment']==reference and job['execution_mode']=='discovery'
                and all(job['resource_budget'][k]==v for k,v in CAPS.items()),'job authority differs')
        revision_path=ROOT/job['candidate_revision']['path']
        require(phase.sha(revision_path)==job['candidate_revision']['sha256'].removeprefix('sha256:'),'revision changed')
        binding.verify_snapshot(snapshot,phase.read_json(revision_path))
        group=Path(job['execution_resources']['cgroup_path'])
        membership=next(x[3:] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
        require(group==Path('/sys/fs/cgroup'+membership) and group.stat().st_ino==job['execution_resources']['cgroup_inode']
                and (group/'memory.max').read_text().strip()==str(CAPS['memory_bytes'])
                and (group/'memory.swap.max').read_text().strip()=='0' and os.sched_getaffinity(0)=={2},
                'resource enforcement differs')
    return reference,plan,snapshot


class BudgetStop(RuntimeError):
    pass


def require_phase(record, stderr=''):
    if record['timeout'] or record['returncode'] in (-9,-24,-25,124,137) or (
            record['returncode'] != 0 and 'MemoryError' in stderr.splitlines()):
        raise BudgetStop('codec phase exceeded its execution limit')
    if record['error'] is not None:
        raise OSError(record['error'])
    require(record['returncode']==0,'codec phase failed')


def difference(left,right,path='$'):
    if type(left)!=type(right):return dict(path=path,expected_type=type(left).__name__,actual_type=type(right).__name__)
    if isinstance(left,dict):
        if left.keys()!=right.keys():return dict(path=path,expected_keys=sorted(left),actual_keys=sorted(right))
        for key in left:
            result=difference(left[key],right[key],path+'.'+key)
            if result:return result
    elif isinstance(left,list):
        if len(left)!=len(right):return dict(path=path,expected_length=len(left),actual_length=len(right))
        for i,(a,b) in enumerate(zip(left,right)):
            result=difference(a,b,f'{path}[{i}]')
            if result:return result
    elif left!=right:return dict(path=path,expected=left,actual=right)
    return None


def compare(left,right,directory,label):
    if left==right:return
    if isinstance(left,bytes):
        first=next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),min(len(left),len(right)))
        detail=dict(first_divergence_byte=first,expected_bytes=len(left),actual_bytes=len(right),
                    expected_window_hex=left[max(0,first-16):first+17].hex(),
                    actual_window_hex=right[max(0,first-16):first+17].hex())
    else:detail=difference(left,right)
    phase.write_json(directory/(label+'.divergence.json'),detail)
    raise ValueError(label+' differs; retained first-divergence diagnostic')


def run_population(directory,row,snapshot,marker,limits=PHASES):
    name=row['name'];source=ROOT/row['input']['path'];reference=ROOT/row['archive']['path']
    expected_audit=phase.read_json(ROOT/row['audit']['path']);commands=[]
    outputs={k:directory/(name+suffix) for k,suffix in
             [('plain','.plain.arc'),('encode','.arc'),('decode','.raw'),('repeat','.repeat.arc')]}
    audits={k:directory/(name+'-'+k+'.audit.json') for k in ('encode','decode','repeat')}
    for label,operation,src in [('plain','encode',source),('encode','encode',source),
                                ('decode','decode',outputs['encode']),('repeat','encode',outputs['decode'])]:
        command=[sys.executable,str(ROOT/CLI),operation,str(src),str(outputs[label]),'--candidate-root',str(snapshot)]
        if label!='plain':command+=['--audit',str(audits[label])]
        record=phase.run_phase(directory,name+'-'+label,command,limits,marker)
        require_phase(record,(directory/(name+'-'+label+'.stderr')).read_text(errors='replace'))
        try:
            record['codec_resources']=phase.read_json(directory/(name+'-'+label+'.stdout'))
        except (OSError,ValueError) as error:
            record['codec_resources']=None
            record['missing_diagnostics']=['optional CLI resource report: '+str(error)]
        commands.append(record)
        compare(source.read_bytes() if label=='decode' else reference.read_bytes(),outputs[label].read_bytes(),
                directory,name+'-'+label+'-bytes')
        if label!='plain':compare(expected_audit,phase.read_json(audits[label]),directory,name+'-'+label+'-state')
    return dict(name=name,input=row['input'],status='passed',archive_bytes=outputs['encode'].stat().st_size,
                retained_archive_identity=True,unobserved_observed_identity=True,exact_inverse=True,
                deterministic_repeat=True,complete_state_witness_identity=True,commands=commands,
                artifacts={k:phase.artifact(p) for k,p in outputs.items()},
                audits={k:phase.artifact(p) for k,p in audits.items()})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args();reference,plan,snapshot=authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass',codec_executed=False)));return 0
    directory=ROOT/'results'/CID
    require(directory.is_dir() and not any(directory.iterdir()),'result directory must be empty')
    stage=dict(schema='gamma.enwiki9.opcode-field-compact-parity.v1',candidate_id=CID,experiment=reference,
               status='running',populations=[],correctness_pass=False,objective_credit_bytes=0,
               complete_package_bytes=None,full_corpus_score_bytes=None,resource_qualified=False,
               package_files=plan['package_files'],local_source_bytes=5746,local_source_saving_bytes=9657,
               source_delta_from_original_parent_bytes=905,
               note='Implementation parity on reused measured populations; not fresh prediction confirmation. Package multiplicities, options and runtime closure remain unqualified.')
    try:
        for row in plan['populations']:
            stage['populations'].append(run_population(directory,row,snapshot,Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate();stage.update(status='passed',correctness_pass=True,frozen_inputs_reverified=True)
    except Exception as error:
        kind='budget-exhausted' if isinstance(error,(BudgetStop,MemoryError)) else 'infrastructure-failure' if isinstance(error,OSError) else 'implementation-failure'
        stage.update(status='failed',failure_class=kind,error=type(error).__name__+': '+str(error))
    phase.write_json(directory/'artifacts.json',dict(complete=stage['correctness_pass'],
        files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory/'stage-decision.json',stage)
    print(json.dumps(dict(status=stage['status'],populations_closed=len(stage['populations']))))
    return 0 if stage['correctness_pass'] else 1


if __name__=='__main__':
    raise SystemExit(main())
