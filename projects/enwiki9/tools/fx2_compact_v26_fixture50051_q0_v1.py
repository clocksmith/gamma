#!/usr/bin/env python3
"""Guarded P/K/D native FXCM block comparison with the fixed FX2 transformer."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate, GateFailure, require, sha

ID = 'fx2_compact_v26_fixture50051_q0_v1'
PARENT = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
ADAPTER = 'operations/provenance/fx2_compact_v26_native_adapter_v1.json'
TRACE_ADAPTER = 'operations/provenance/public_fx2_argmax_native_adapter_v1.json'
REFERENCE_TRACE = 'results/fx2_cmix_transformer_argmax_fixture50051_q0_v1/work/P-encode.trace'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0, scratch_bytes=24000000000, wall_seconds=1200)
FLAGS = '-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections'
COMPACT = '-DFX3_FXCM_V26_GROUP_MASK=23 -DFX3_FXCM_V26_AUX_MASK=1 -DFX3_FXCM_V26_COMPACT_OUTPUTS=1 -DFX3_FXCM_V26_AUDIT_INPUT_COUNT=1'
RAW_SHA = '890b3e1210a24a249768d86bd5a79a1775ce19b2d56984ce3069ee26359ef2e6'
TRACE_BYTES = 32478 * 8 * 28


def exact(left, right):
    require(left.stat().st_size == right.stat().st_size, 'file length differs')
    offset = 0
    with left.open('rb') as a, right.open('rb') as b:
        while chunk := a.read(1 << 20):
            other = b.read(len(chunk))
            if chunk != other:
                first = next(i for i,(x,y) in enumerate(zip(chunk,other)) if x != y)
                raise ValueError('first file divergence at byte ' + str(offset + first))
            offset += len(chunk)


def activation(stderr, arm):
    rows = re.findall(rb'Gamma FXCM arm=([PKD]) outputs=([0-9]+)\r?\n', stderr)
    expected = b'403' if arm == 'D' else b'431'
    require(stderr.count(b'Gamma FXCM arm=') == 1 and rows == [(arm.encode(),expected)],
            'native model activation differs')


def materialize(g, arm, package):
    work = g.work / arm
    for row in package['source_members'] + package['runtime_members']:
        if row['path'].endswith('/cmix'):
            continue
        target = work / row['path'].removeprefix(PARENT+'work/')
        if not target.exists():
            g.copy(row['path'], target)
    g.adapter(ADAPTER, work)
    for row in json.loads(g.buffers[ADAPTER])['added_files']:
        g.copy(row['source']['path'], work / row['target'])
    g.adapter(TRACE_ADAPTER, work, {'src/coder/encoder.cpp', 'src/coder/decoder.cpp'})
    g.copy('tools/fx2_coder_trace_v1.hpp', work / 'src/coder/gamma-coder-trace.h')
    # Each binary links exactly one native FXCM implementation. The original
    # makefile and model sources are retained in frozen inputs, never edited.
    if arm == 'D':
        path = work / 'makefile'
        text = path.read_text()
        for suffix in ('.h','.cpp','.o'):
            before = 'fxcmv1'+suffix
            require(text.count(before) == 1, 'makefile source selection ambiguous')
            text = text.replace(before, 'fxcm_v26'+suffix)
        path.write_text(text)
    return work


def execute(g):
    package = json.loads(g.buffers[PARENT+'package.json'])
    raw = g.buffers[PARENT+'work/prof_input/input']
    require(len(raw) == 50051 and hashlib.sha256(raw).hexdigest() == RAW_SHA, 'raw fixture identity differs')
    rows = {}
    for index, arm in enumerate(('P','K','D')):
        work = materialize(g, arm, package)
        # The raw fixture is supplied only for encoder phases in this cwd.
        (work / 'prof_input/input').unlink()
        files = [p for p in sorted(work.rglob('*')) if p.is_file()]
        source_refs = [g.artifact(p) for p in files]
        frozen_local = {p: sha(p) for p in files}
        flags = FLAGS + ' -DGAMMA_FXCM_ARM=' + str(index) + (' '+COMPACT if arm == 'D' else '')
        g.run(arm+'-compile', ['/usr/bin/make', '-j1', 'cmix', 'CC=/usr/bin/g++',
              'CPPFLAGS_PART-THAT-SHOULD-BE-FAST='+flags+' -O3',
              'CPPFLAGS_PART-THAT-CAN-BE-SLOW='+flags+' -Os'], 180, work=work)
        binary = g.artifact(work / 'cmix')
        g.binaries[str(work / 'cmix')] = binary['sha256']
        g.run(arm+'-disassemble', ['/usr/bin/objdump','-d','--insn-width=16','cmix'],30,work=work)
        assembly = (g.result/(arm+'-disassemble.stdout')).read_text()
        require(not re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ',assembly), 'nonportable arithmetic instructions')
        g.run(arm+'-dependencies', ['/usr/bin/objdump','-p','cmix'],15,work=work)
        needed = re.findall(r'^\s+NEEDED\s+(\S+)',(g.result/(arm+'-dependencies.stdout')).read_text(),re.M)
        options = '-c dictionary/english.dic input archive --transformer models/6m-q4-fp32.tfwc2\n-d dictionary/english.dic archive output --transformer models/6m-q4-fp32.tfwc2\n'+flags+' -O3 -Os\n'
        inventory = dict(source_and_asset_files=source_refs, native_binary=binary,
                         required_options=options, dynamic_libraries=needed,
                         raw_source_and_asset_bytes=sum(r['bytes'] for r in source_refs),
                         overlapping_local_inventory_bytes=sum(r['bytes'] for r in source_refs)+binary['bytes']+len(options.encode()),
                         complete_submission_package=False, complete_package_bytes=None,
                         unresolved=package['unresolved'], scope='Conservative source/assets plus selected binary and options; includes control source, not other arms binaries. Not an official counted package.')
        g.write(arm+'-package.json',inventory)
        require(inventory['overlapping_local_inventory_bytes'] <= 10000000,'local package budget exceeded')
        def invoke(phase,args,traced=True):
            env = {'GAMMA_FX2_CODER_TRACE':str(work/(phase+'.trace'))} if traced else {}
            result = g.run(arm+'-'+phase,[str(work/'cmix'),*args,'--transformer','models/6m-q4-fp32.tfwc2'],120,env=env,work=work)
            activation((g.result/(arm+'-'+phase+'.stderr')).read_bytes(),arm)
            return result
        (work/'input').write_bytes(raw)
        enc = invoke('encode',['-c','dictionary/english.dic','input','archive'])
        require(0 < (work/'archive').stat().st_size <= 100000,'archive budget exceeded')
        (work/'input').unlink()
        dec = invoke('decode',['-d','dictionary/english.dic','archive','restored'])
        require((work/'restored').read_bytes() == raw,'independent inverse differs')
        rep = invoke('repeat',['-c','dictionary/english.dic','restored','repeat'])
        exact(work/'archive',work/'repeat')
        traces = [g.compare_trace(work/'encode.trace',work/(phase+'.trace'),TRACE_BYTES) for phase in ('decode','repeat')]
        if arm in ('P','K'):
            exact(work/'archive',ROOT/(PARENT+'work/fixture.cmix'))
            traces.append(g.compare_trace(ROOT/REFERENCE_TRACE,work/'encode.trace',TRACE_BYTES))
        if arm == 'K':
            traces.append(g.compare_trace(g.work/'P/encode.trace',work/'encode.trace',TRACE_BYTES))
        invoke('plain',['-c','dictionary/english.dic','restored','plain'],traced=False)
        exact(work/'archive',work/'plain')
        require(all(sha(p) == h for p,h in frozen_local.items()), 'materialized source changed')
        # Delete only the closed transient PPM backing file owned by this arm.
        # Archive, restored bytes, traces and materialized sources stay retained.
        g.closure()
        transient = work/'ppm.temp'
        removed = None
        if transient.is_file():
            removed = dict(path=str(transient.relative_to(g.result)),bytes=transient.stat().st_size)
            transient.unlink()
        rows[arm] = dict(archive=g.artifact(work/'archive'), restored=g.artifact(work/'restored'),
                         repeat=g.artifact(work/'repeat'), raw_bytes=len(raw), raw_sha256=RAW_SHA,
                         exact_inverse=True, exact_repeat=True, trace_comparisons=traces,
                         unobserved_archive_identical=True, binary=binary,
                         package=g.artifact(g.result/(arm+'-package.json')),
                         overlapping_local_inventory_bytes=inventory['overlapping_local_inventory_bytes'],
                         phases=dict(encode=enc,decode=dec,repeat=rep), transient_cleanup=removed)
        g.write(arm+'-result.json',rows[arm])
    saving = rows['P']['archive']['bytes']-rows['D']['archive']['bytes']
    package_delta = rows['D']['overlapping_local_inventory_bytes']-rows['P']['overlapping_local_inventory_bytes']
    return dict(arms=rows,correctness_pass=True,archive_saving_bytes=saving,
                overlapping_local_inventory_delta_bytes=package_delta,
                conditional_local_net_saving_bytes=saving-package_delta,
                native_coder_trace_parity=True,full_predictor_state_trace='unmeasured',
                complete_package_bytes=None,larger_gate_authorized=False)


def main():
    require(sys.argv[1:] in ([],['--validate-only']),'unexpected arguments')
    g = NativeGate(ROOT,ID,CAPS,validate_only=bool(sys.argv[1:]))
    if sys.argv[1:]:
        print(json.dumps(dict(frozen_inputs_verified=len(g.inputs),native_executed=False)))
        return 0
    stage = dict(schema='gamma.enwiki9.native-block-stage.v1',candidate_id=ID,
                 objective_credit_bytes=0,full_corpus_score_bytes=None)
    try:
        stage.update(execute(g))
        g.verify()
        g.closure()
        stage['status'] = 'passed'
    except Exception as error:
        stage.update(status='failed',failure_class=getattr(error,'category','implementation_or_evidence_failure'),error=str(error))
    try:
        g.closure()
        removed = []
        for arm in ('P','K','D'):
            transient = g.work/arm/'ppm.temp'
            if transient.is_file():
                removed.append(dict(path=str(transient.relative_to(g.result)),bytes=transient.stat().st_size))
                transient.unlink()
        stage['closed_failure_transient_cleanup'] = removed
    except Exception as error:
        stage.update(status='failed',cleanup_error=str(error))
        g.write('stage-decision.json',stage)
        return 1
    stage['commands'] = g.commands
    g.write('artifacts.json',dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file()]))
    g.write('stage-decision.json',stage)
    return 0 if stage['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
