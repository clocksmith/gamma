#!/usr/bin/env python3
"""Source-bound native tensor parity and build cost; never run corpus inference."""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import time
from fx2_weight_neighbor_model_audit_v1 import binding

ROOT=Path(__file__).resolve().parents[1]
FAST='-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections'


def phase(output,name,cmd,bounds,deadline,work=None):
    remaining=min(bounds['phase_elapsed_seconds'],deadline-time.monotonic())
    if remaining<=0:raise TimeoutError('aggregate elapsed stop')
    def limits():
        for key,value in ((resource.RLIMIT_AS,bounds['address_space_bytes']),
                          (resource.RLIMIT_CPU,bounds['cpu_seconds_per_phase']),
                          (resource.RLIMIT_FSIZE,bounds['per_file_bytes'])):
            resource.setrlimit(key,(value,value))
    started=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    with (output/(name+'.stdout')).open('xb') as stdout,(output/(name+'.stderr')).open('xb') as stderr:
        child=subprocess.Popen(list(map(str,cmd)),stdout=stdout,stderr=stderr,cwd=work,
                               env=dict(os.environ,TMPDIR=str((output/'tmp').resolve())),
                               preexec_fn=limits,start_new_session=True)
        try:code=child.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise TimeoutError('phase elapsed stop: '+name)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    row=dict(name=name,command=list(map(str,cmd)),returncode=code,elapsed_seconds=time.monotonic()-started,
             cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
             cumulative_child_peak_rss_kib=after.ru_maxrss)
    with (output/'commands.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
    if code:raise ValueError('phase failed: '+name)
    if sum(p.stat().st_blocks*512 for p in output.rglob('*') if p.is_file())>bounds['scratch_bytes']:
        raise ValueError('scratch stop')
    return (output/(name+'.stdout')).read_text()


def run(plan,inputs,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    (output/'tmp').mkdir()
    deadline=time.monotonic()+plan['bounds']['elapsed_seconds']
    def invoke(name,cmd,work=None):return phase(output,name,cmd,plan['bounds'],deadline,work)
    original=ROOT/plan['models']['original']['path']
    reports=[]
    for name,comparator,target in [('P',plan['comparators']['parent'],plan['models']['parent']),
                                   ('D',plan['comparators']['adaptive'],plan['models']['adaptive']),
                                   ('D-repeat',plan['comparators']['adaptive'],plan['models']['adaptive'])]:
        report=json.loads(invoke('tensors-'+name,[ROOT/comparator['path'],original,ROOT/target['path']]))
        if not (report['exact_byte_comparison'] and report['tensor_count']==434 and report['payload_bytes']==39588806):
            raise ValueError('native tensor evidence differs')
        reports.append(report)
    if any(r['reference_digest_hex']!=reports[0]['reference_digest_hex'] or
           r['target_digest_hex']!=reports[0]['target_digest_hex'] for r in reports):
        raise ValueError('native tensor replay differs')
    builds={}
    for arm in ('P','D'):
        tree=output/arm;tree.mkdir()
        for row in inputs['native_sources']:
            target=tree/row['relative'];target.parent.mkdir(parents=True,exist_ok=True)
            source=ROOT/(plan['patched_loader']['path'] if arm=='D' and row['relative']=='cpp_infer/src/weights_io_compressed.cpp' else row['path'])
            with target.open('xb') as stream:stream.write(source.read_bytes())
        invoke('build-'+arm,['/usr/bin/make','-j1','cmix','CC=/usr/bin/g++',
               'CPPFLAGS_PART-THAT-SHOULD-BE-FAST='+FAST+' -O3',
               'CPPFLAGS_PART-THAT-CAN-BE-SLOW='+FAST+' -Os'],tree)
        builds[arm]=binding(tree/'cmix')
    for key in ('bytes','sha256'):
        if builds['P'][key]!=plan['native_parent'][key]:raise ValueError('native parent rebuild differs')
    needed={}
    for arm in ('P','D'):
        report=invoke('dependencies-'+arm,['/usr/bin/objdump','-p',builds[arm]['path']])
        needed[arm]=re.findall(r'^\s+NEEDED\s+(\S+)',report,re.M)
    if needed['P']!=needed['D']:raise ValueError('native dependencies changed')
    disassembly=invoke('disassemble-D',['/usr/bin/objdump','-d','--insn-width=16',builds['D']['path']])
    if re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ',disassembly):
        raise ValueError('forbidden reciprocal or AVX512 instruction')
    model_delta=plan['models']['adaptive']['bytes']-plan['models']['parent']['bytes']
    binary_delta=builds['D']['bytes']-builds['P']['bytes']
    parent_loader=next(r for r in inputs['native_sources'] if r['relative']=='cpp_infer/src/weights_io_compressed.cpp')
    source_delta=plan['patched_loader']['bytes']-parent_loader['bytes']
    result=dict(schema='gamma.enwiki9.adaptive-native-loader.v1',tensor_reports=reports,native_builds=builds,
                needed_libraries=needed,model_delta_per_copy=model_delta,binary_delta_per_copy=binary_delta,
                raw_source_delta=source_delta,option_delta_bytes=0,
                runtime_pair_delta=2*(model_delta+binary_delta),
                source_compressor_plus_decoder_delta=2*model_delta+binary_delta+source_delta,
                full_corpus_score_bytes=None,complete_package_bytes=None,objective_credit_bytes=0)
    temp=output/'receipt.partial';temp.write_text(json.dumps(result,indent=2)+'\n');temp.rename(output/'receipt.json')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','admission','output'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    plan=json.loads((ROOT/'operations/provenance/fx2_weight_adaptive_loader_gate_v1_plan.json').read_text())
    admission=json.loads(Path(args.admission).read_text())
    if admission.get('id')!=plan['id'] or admission.get('admitted') is not True:raise ValueError('matching admission required')
    if sorted(os.sched_getaffinity(0))!=plan['bounds']['cpu_set']:raise ValueError('CPU assignment differs')
    inputs=json.loads(Path(args.inputs).read_text())
    for row in inputs['inputs']+inputs['native_sources']+list(plan['models'].values())+list(plan['comparators'].values())+[plan['native_parent'],plan['patched_loader']]:
        actual=binding(ROOT/row['path'])
        if any(actual[k]!=row[k] for k in ('bytes','sha256')):raise ValueError('changed input: '+row['path'])
    result=run(plan,inputs,args.output)
    print(json.dumps({k:result[k] for k in ('model_delta_per_copy','binary_delta_per_copy','runtime_pair_delta','source_compressor_plus_decoder_delta')}))


if __name__=='__main__':main()
