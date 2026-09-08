#!/usr/bin/env python3
"""Reproduce one pinned compact forge parent using the existing native guard."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ID = 'forge_compact_fixture50051_q0_v1'
UPSTREAM = 'results/forge_parent_source_audit_v1/source-tree/'
AUDIT = 'operations/provenance/forge_parent_source_audit_v1_plan.json'
FX2 = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
CAPS = {'cpus': [2], 'memory_bytes': 9999998976, 'scratch_bytes': 4000000000, 'swap_bytes': 0, 'wall_seconds': 900}
DEFINES = '-DSEED=923 -DUPDATE_LIMIT=3000 -DFX3_LSTM_CELLS=300 -DFX3_LAYER1_LR=0.0001 -DFX3_LSTMEX_BIT_HINT_SCALE=256 -DFX3_LAYER1_BYTE_MIXER_INPUT_SCALE=0 -DFX3_ENABLE_FXCM_V26=1 -DFX3_FXCM_V26_GROUP_MASK=23 -DFX3_FXCM_V26_AUX_MASK=1 -DFX3_FXCM_V26_COMPACT_OUTPUTS=1 -DFX3_FXCM_V26_AUDIT_INPUT_COUNT=1 -DARCHIVE9_DYNAMIC_SPLIT_HEADER -DFX3_ENABLE_HEAP_THP_ADVISE=0 -DFX3_ENABLE_ANON_THP_ADVISE=1 -UFX3_LSTM_CELLS -DFX3_LSTM_CELLS=270'
FLAGS = DEFINES + ' -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections'
RAW_SHA = '890b3e1210a24a249768d86bd5a79a1775ce19b2d56984ce3069ee26359ef2e6'


def load_helpers(validate):
    path = 'operations/adaptive/experiments/' + ID + '.json'
    content = (ROOT / path).read_bytes()
    if not validate:
        expected = {'path': path, 'sha256': 'sha256:' + hashlib.sha256(content).hexdigest()}
        if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) != expected:
            raise ValueError('experiment changed before helper load')
    refs = {r['path']: r['sha256'].removeprefix('sha256:') for r in json.loads(content)['inputs']}
    buffers = {}
    for name in ('tools/' + ID + '.py', 'lib/fx2_native_gate_v1.py', 'lib/artifacts.py'):
        p = ROOT / name
        if p.resolve() != p:
            raise ValueError('aliased bootstrap source')
        buffers[name] = p.read_bytes()
        if hashlib.sha256(buffers[name]).hexdigest() != refs[name]:
            raise ValueError('bootstrap changed')
    namespace = {}
    exec(compile(buffers['lib/fx2_native_gate_v1.py'], str(ROOT / 'lib/fx2_native_gate_v1.py'), 'exec'), namespace)
    globals().update({k: namespace[k] for k in ('NativeGate', 'GateFailure', 'require', 'sha')})


def build_paths(audit):
    """Build source and licenses only; never materialize a shipped executable."""
    wanted = []
    for row in audit['source_tree']:
        name = row['path'].removeprefix(UPSTREAM)
        if name.startswith('src/') or name in ('makefile', 'LICENSE', 'THIRD-PARTY-NOTICES.md', 'dictionary/english.dic'):
            wanted.append(row['path'])
    return wanted


def validate_inputs(gate):
    audit = json.loads(gate.buffers[AUDIT])
    require(audit['commit'] == '11a25d3990460a55fdfd90d46edd82b0ab147e45', 'upstream identity differs')
    require(len(audit['source_tree']) == 120, 'incomplete public source audit')
    for row in audit['source_tree']:
        data = gate.buffers[row['path']]
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], 'source audit differs')
    raw = gate.buffers[UPSTREAM + 'prof_input/input']
    require(len(raw) == 50051 and hashlib.sha256(raw).hexdigest() == RAW_SHA, 'raw population differs')
    require(raw == gate.buffers[FX2 + 'work/prof_input/input'], 'FX2 population differs')
    require(len(gate.buffers[FX2 + 'work/fixture.cmix']) == 3223, 'FX2 reference differs')
    return audit


def execute(gate, audit):
    native = gate.work / 'native'
    paths = build_paths(audit)
    for source in paths:
        gate.copy(source, native / source.removeprefix(UPSTREAM))
    # Kept outside native cwd: each phase receives only its named input there.
    sources = [gate.artifact(native / p.removeprefix(UPSTREAM)) for p in paths]
    gate.run('compile-native', ['/usr/bin/make', '-j1', 'cmix', 'CC=/usr/bin/g++', 'CFLAGS_DEFINES=' + DEFINES, 'CPPFLAGS_PART-THAT-SHOULD-BE-FAST=' + FLAGS + ' -O3', 'CPPFLAGS_PART-THAT-CAN-BE-SLOW=' + FLAGS + ' -Os'], 300, work=native)
    binary = gate.artifact(native / 'cmix')
    gate.binaries[str(native / 'cmix')] = binary['sha256']
    gate.run('disassemble', ['/usr/bin/objdump', '-d', '--insn-width=16', 'cmix'], 30, work=native)
    require(re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ', (gate.result / 'disassemble.stdout').read_text()) is None, 'forbidden reciprocal or AVX512 instruction')
    gate.run('dynamic-dependencies', ['/usr/bin/objdump', '-p', 'cmix'], 15, work=native)
    needed = re.findall(r'^\s+NEEDED\s+(\S+)', (gate.result / 'dynamic-dependencies.stdout').read_text(), re.M)
    options = '-c dictionary input archive\n-d dictionary archive output\n' + FLAGS + ' -O3 -Os\n'
    inventory = {'source_and_asset_files': sources, 'native_binary': binary, 'required_option_text': options, 'raw_source_and_asset_bytes': sum(r['bytes'] for r in sources), 'overlapping_local_inventory_bytes': sum(r['bytes'] for r in sources) + binary['bytes'] + len(options.encode()), 'dynamic_libraries': needed, 'dependency_closure_complete': False, 'full_corpus_score_bytes': None, 'unresolved': ['Compiler and runtime license/distribution closure', 'Official package form and multiplicities', 'Independent host build/replay', 'Qualifying resource calibration'], 'meaning': 'Conservative overlapping local source plus binary inventory; not an official counted package. Public submission bytes are not inherited.'}
    gate.write('package.json', inventory)
    if inventory['overlapping_local_inventory_bytes'] > 10000000:
        raise GateFailure('package_budget_stop', 'local inventory exceeds 10000000 bytes')
    raw = gate.buffers[UPSTREAM + 'prof_input/input']
    gate.copy(UPSTREAM + 'prof_input/input', native / 'input')
    gate.run('encode', [str(native / 'cmix'), '-c', 'dictionary/english.dic', 'input', 'archive'], 180, work=native)
    archive = (native / 'archive').read_bytes()
    require(0 < len(archive) <= 100000, 'archive exceeds fixed fixture budget')
    # The independent decoder process has no raw file in its cwd. The unchanged
    # upstream decoder is source audited; this is not a filesystem sandbox claim.
    (native / 'input').unlink()
    gate.run('decode', [str(native / 'cmix'), '-d', 'dictionary/english.dic', 'archive', 'restored'], 180, work=native)
    require((native / 'restored').read_bytes() == raw, 'exact inverse failed')
    gate.run('reencode', [str(native / 'cmix'), '-c', 'dictionary/english.dic', 'restored', 'repeat'], 180, work=native)
    require((native / 'repeat').read_bytes() == archive, 'deterministic repeat failed')
    for source, expected in zip(paths, sources):
        require(gate.artifact(native / source.removeprefix(UPSTREAM)) == expected, 'native source changed during execution')
    return {'status': 'passed', 'raw_bytes': len(raw), 'raw_sha256': RAW_SHA, 'archive': gate.artifact(native / 'archive'), 'restored': gate.artifact(native / 'restored'), 'repeat': gate.artifact(native / 'repeat'), 'exact_inverse': True, 'exact_repeat': True, 'native_binary': binary, 'retained_fx2_archive_bytes': 3223, 'archive_difference_vs_retained_fx2_bytes': len(archive) - 3223, 'comparison_scope': 'Identical cold public profiling fixture; different native parents. This is not an isolated mechanism ablation or statistical confirmation.', 'introduced_predictor_state': False, 'full_parent_state_trace': 'not measured', 'larger_gate_authorized': False, 'objective_credit_bytes': 0}


def main():
    if sys.argv[1:] not in ([], ['--validate-only']):
        raise ValueError('unexpected arguments')
    validate = bool(sys.argv[1:])
    load_helpers(validate)
    gate = NativeGate(ROOT, ID, CAPS, validate)
    audit = validate_inputs(gate)
    if validate:
        print(json.dumps({'status': 'preflight_pass', 'inputs': len(gate.inputs), 'native_executed': False}))
        return 0
    stage = {'candidate_id': ID, 'experiment': gate.reference, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None, 'continuous_resource_decision': 'pending outer guard closure'}
    try:
        stage.update(execute(gate, audit))
    except Exception as error:
        category = error.category if isinstance(error, GateFailure) else 'missing_or_unreadable_evidence' if isinstance(error, (OSError, KeyError)) else 'invariant_failed'
        stage.update(status='execution_failed', failure_class=category, error=type(error).__name__ + ': ' + str(error))
    try:
        gate.closure()
        gate.verify()
        stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', closure_error=str(error))
    stage['commands'] = gate.commands
    gate.write('artifacts.json', [gate.artifact(p) for p in sorted(gate.result.rglob('*')) if p.is_file()])
    stage['artifacts'] = gate.artifact(gate.result / 'artifacts.json')
    gate.write('stage-decision.json', stage)
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
