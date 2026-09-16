#!/usr/bin/env python3
"""Compare original and repaired native auxiliary packages under a lab gate.

This checks fixed auxiliary assets, actual extraction subprocesses, and a
matched opening-prefix core archive. It does not execute the full enwik9
split/PHDA/reorder pipeline or establish a complete submission score.
"""
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from lib.fx2_trim_auxiliary_pack_v1 import assemble, ASSETS
from tools.fx2_expert_release250k_v3 import equal, source_zip
from tools.fx2_trim_scale10m_v1 import members, clean_scratch

ID = 'fx2_trim_auxiliary_ppm_v1'
PLAN = 'operations/provenance/' + ID + '_plan.json'
PROFILE = 'operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RUNTIME = 'operations/provenance/fx2_trim_auxiliary_runtime_20260916.json'
RELEASE = 'results/fx2_expert_release250k_v3/'
ZIPS = {'P': RELEASE + 'original-source.zip',
        'D': 'results/fx2_trim_auxiliary_preflight_v1/D-source.zip'}
FIXTURE = 'results/fx2_weight_native_transfer250k_q0_v1/'
RAW = FIXTURE + 'work/native/opening.raw'
ARCHIVE = FIXTURE + 'opening/P/archive.bin'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=16000000000, wall_seconds=7200)


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain = json.loads(self.buffers[PROFILE])
        super().verify()
        runtime = json.loads(self.buffers[RUNTIME])
        for row in [*runtime['providers'].values(), runtime['shell'], runtime['bwrap'], runtime['python']]:
            p = Path(row['resolved_path'])
            require(p.is_file() and sha(p) == row['sha256'] and
                    p.stat().st_size == row['bytes'], 'runtime provider changed: ' + str(p))


def sandbox(runtime, directory, helper, command):
    """Expose only one fresh work directory, the harness, shell and five ELF files."""
    cmd = [runtime['bwrap']['resolved_path'], '--unshare-all', '--die-with-parent',
           '--new-session', '--clearenv', '--dir', '/runtime', '--dir', '/runtime/lib',
           '--dir', '/lib64', '--dir', '/bin', '--dir', '/test', '--dev', '/dev',
           '--bind', str(directory), '/work', '--ro-bind', str(helper), '/test/extract',
           '--ro-bind', runtime['shell']['resolved_path'], '/bin/sh',
           '--setenv', 'LD_LIBRARY_PATH', '/runtime/lib', '--setenv', 'LC_ALL', 'C',
           '--setenv', 'PATH', '/bin', '--chdir', '/work']
    for name, row in sorted(runtime['providers'].items()):
        cmd += ['--ro-bind', row['resolved_path'], '/runtime/lib/' + name]
    cmd += ['--symlink', '/runtime/lib/ld-linux-x86-64.so.2',
            '/lib64/ld-linux-x86-64.so.2', '--', *command]
    return cmd


def test_archive(binary, dictionary, weights, payload, target):
    """Assemble the upstream decoder layout for an explicit bootstrap fixture."""
    require(not target.exists(), 'bootstrap archive already exists')
    inputs = [binary, dictionary, weights, payload]
    sizes = [p.stat().st_size for p in inputs]
    require(all(p.is_file() and p.resolve() == p for p in inputs), 'aliased fixture member')
    require(all(0 < n <= 2147483647 for n in sizes[1:]), 'footer member outside bounds')
    with target.open('xb') as out:
        for p in inputs:
            with p.open('rb') as source:
                shutil.copyfileobj(source, out)
        out.write(struct.pack('<iiii', sizes[1], 0, sizes[3], sizes[2]))
    target.chmod(0o755)


def run_clean(g, label, command, cap, directory):
    try:
        return g.run(label, command, cap, work=directory)
    finally:
        clean_scratch(g, directory, label)


def execute(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['caps'] == CAPS, 'resource contract differs')
    require(len(g.buffers[RAW]) == 250000, 'prefix scope differs')
    runtime = json.loads(g.buffers[RUNTIME])
    require(set(runtime['providers']) == {'libstdc++.so.6', 'libm.so.6',
            'libgcc_s.so.1', 'libc.so.6', 'ld-linux-x86-64.so.2'}, 'runtime set differs')
    arms = {}
    for arm in 'PD':
        sources = members(g.buffers[ZIPS[arm]])
        native = g.work / arm
        native.mkdir()
        for name, data in sources.items():
            p = native / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        source_zip(g.result / (arm + '-source.zip'), sources)
        equal(g.result / (arm + '-source.zip'), ROOT / ZIPS[arm])
        for name, expected in ASSETS.items():
            require(sha(native / name) == expected, 'fixed asset changed')
        command = plan['compile_command']
        g.run(arm + '-build', command, 360, work=native)
        first = (native / 'cmix').read_bytes()
        g.run(arm + '-clean', ['/usr/bin/make', 'clean'], 30, work=native)
        g.run(arm + '-build-repeat', command, 360, work=native)
        require((native / 'cmix').read_bytes() == first, 'clean build repeat differs')
        binary = native / 'cmix'
        if arm == 'P':
            require(sha(binary) == '08b9e9cf3734ad5952b7a3a5eb403fdc1c4cbb1a853cda613392d52f0a77bea0',
                    'original reference executable differs')
        g.binaries[str(binary)] = sha(binary)
        g.copy(RAW, native / 'population.raw')
        for phase in ['encode', 'decode', 'repeat']:
            if phase == 'decode':
                args = ['-d', 'dictionary/english.dic', 'encode.arc', 'restored.raw']
            else:
                args = ['-c', 'dictionary/english.dic',
                        'restored.raw' if phase == 'repeat' else 'population.raw', phase + '.arc']
            run_clean(g, arm + '-main-' + phase,
                      [str(binary), *args, '--transformer', 'models/6m-q4-fp32.tfwc2'], 300, native)
            if phase == 'decode': equal(native / 'restored.raw', native / 'population.raw')
            if phase == 'repeat': equal(native / 'repeat.arc', native / 'encode.arc')
        equal(native / 'encode.arc', ROOT / ARCHIVE)
        if arm == 'P':
            assets = native / 'assets'
            assets.mkdir()
            for label, name in [('dict', 'dictionary/english.dic'),
                                ('order', 'src/readalike_prepr/data/new_article_order')]:
                for phase in ['encode', 'decode', 'repeat']:
                    if phase == 'decode':
                        args = ['-d', str(assets / (label + '.comp')), str(assets / (label + '.restored'))]
                    else:
                        src = assets / (label + '.restored') if phase == 'repeat' else native / name
                        target = assets / (label + ('.repeat' if phase == 'repeat' else '.comp'))
                        args = ['-c', str(src), str(target)]
                    run_clean(g, arm + '-' + label + '-' + phase,
                              [str(binary), *args], 360, native)
                equal(assets / (label + '.restored'), native / name)
                equal(assets / (label + '.repeat'), assets / (label + '.comp'))
            assembled = native / 'assembled'
            assembled.mkdir()
            assemble(binary, assets / 'dict.comp', assets / 'order.comp',
                     native / 'models/6m-q4-fp32.tfwc2', assembled / 'cmix')
        else:
            assembled = native / 'assembled'
            try:
                g.run('D-delivered-packager', [sys.executable, str(native / 'gamma_pack_auxiliary.py'),
                      '--binary', str(binary), '--work', str(assembled)], 1800, work=native)
            finally:
                if (assembled / 'native').is_dir():
                    clean_scratch(g, assembled / 'native', 'D-delivered-packager')
            assets = assembled / 'native'
            equal(assets / 'cmix', binary)
            calls = json.loads((assembled / 'commands.json').read_text())
            require(len(calls) == 4 and all(c['returncode'] == 0 for c in calls), 'packager child evidence incomplete')
            for label, name in [('dict', 'dictionary/english.dic'),
                                ('order', 'src/readalike_prepr/data/new_article_order')]:
                equal(assets / (label + '.restored'), native / name)
                run_clean(g, 'D-' + label + '-repeat', [str(binary), '-c',
                          str(assets / (label + '.restored')), str(assets / (label + '.repeat')),
                          '--ppmd-only'], 360, native)
                equal(assets / (label + '.repeat'), assets / (label + '.comp'))
        # The standalone fixture calls the exact bound header's extraction
        # functions; its children execute the actual newly built native binary.
        fixture = native / 'bootstrap.cpp'
        fixture.write_text('#include <cstring>\n#include "src/readalike_prepr/self_extract.h"\n'
                           'int main(int argc,char** argv){if(argc!=2)return 91;'
                           'if(!strcmp(argv[1],"C"))return selfextract_comp();'
                           'if(!strcmp(argv[1],"D"))return selfextract_decomp();return 92;}\n')
        helper = native / 'bootstrap'
        g.run(arm + '-bootstrap-build', ['/usr/bin/g++', '-std=c++17', '-O2',
              str(fixture), '-o', str(helper)], 60, work=native)
        compressor_dir, decoder_dir = native / 'isolated-compressor', native / 'isolated-decoder'
        compressor_dir.mkdir(); decoder_dir.mkdir()
        shutil.copyfile(assembled / 'cmix', compressor_dir / 'cmix')
        (compressor_dir / 'cmix').chmod(0o755)
        test_archive(binary, assets / 'dict.comp', native / 'models/6m-q4-fp32.tfwc2',
                     native / 'encode.arc', decoder_dir / 'archive9')
        for mode, directory in [('C', compressor_dir), ('D', decoder_dir)]:
            run_clean(g, arm + '-bootstrap-' + mode,
                      sandbox(runtime, directory, helper, ['/test/extract', mode]), 900, directory)
            equal(directory / '.dict', native / 'dictionary/english.dic')
            equal(directory / '.tfweights', native / 'models/6m-q4-fp32.tfwc2')
        equal(compressor_dir / '.new_article_order', native / 'src/readalike_prepr/data/new_article_order')
        equal(compressor_dir / '.decomp_bin', binary)
        equal(decoder_dir / '.ready4cmix_decomp', native / 'encode.arc')
        run_clean(g, arm + '-isolated-main-decode', sandbox(runtime, decoder_dir, helper,
                  ['./archive9', '-d', '.dict', '.ready4cmix_decomp', 'restored.raw',
                   '--transformer', '.tfweights']), 300, decoder_dir)
        equal(decoder_dir / 'restored.raw', native / 'population.raw')
        arms[arm] = dict(binary=g.artifact(binary), source_zip=g.artifact(g.result / (arm + '-source.zip')),
                         dictionary=g.artifact(assets / 'dict.comp'), order=g.artifact(assets / 'order.comp'),
                         model=g.artifact(native / 'models/6m-q4-fp32.tfwc2'),
                         compressor_container=g.artifact(assembled / 'cmix'),
                         bootstrap_archive_fixture=g.artifact(decoder_dir / 'archive9'),
                         main_archive=g.artifact(native / 'encode.arc'),
                         restored=g.artifact(decoder_dir / 'restored.raw'),
                         all_inverses_and_repeats_pass=True,
                         clean_build_repeat_identical=True, restricted_bootstrap_and_decode_pass=True,
                         bootstrap_fixture_is_submission=False)
        g.write('completed-arms.json', dict(arms=arms, complete=False))
    # Two explicit component forms; invocation/build/runtime/licensing remain
    # outside these diagnostic subtotals, and no official total is claimed.
    forms = {}
    for arm, row in arms.items():
        forms[arm] = dict(
            executable_pair_bytes=row['compressor_container']['bytes'] + row['bootstrap_archive_fixture']['bytes'],
            source_and_fixture_bytes=row['source_zip']['bytes'] + row['bootstrap_archive_fixture']['bytes'])
    margins = {k: forms['P'][k] - forms['D'][k] for k in forms['P']}
    require(len(g.commands) == 29, 'native phase count differs')
    return dict(status='passed', arms=arms, main_archive_gain_bytes=0,
                auxiliary_roundtrip_pass=True, restricted_bootstrap_and_decode_pass=True,
                diagnostic_component_forms=forms, component_improvements_bytes=margins,
                best_component_improvement_bytes=max(margins.values()),
                component_economics_positive=any(n > 0 for n in margins.values()),
                verdict='Auxiliary/main correctness and package-component comparison closed; complete submission and full-corpus gain remain unproved.')


def main():
    validate = sys.argv[1:] == ['--validate']
    require(validate or not sys.argv[1:], 'unsupported arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed', inputs=len(g.inputs))))
        return 0
    result = dict(schema='gamma.enwiki9.trim-auxiliary-native.v1', candidate_id=ID,
                  experiment=g.reference, objective_credit_bytes=0, raw_bytes=250000,
                  complete_submission_package=False, full_corpus_score_bytes=None,
                  scope='Auxiliary assets and native core only; no full split/PHDA/reorder corpus execution.',
                  larger_gate_authorized=False)
    try:
        result.update(execute(g)); g.verify()
    except Exception as exc:
        result.update(status='execution_failed', failure_class=getattr(exc, 'category', 'correctness_or_evidence_failure'),
                      error=str(exc), verdict='Incomplete packaging gate; retain completed evidence.')
    try:
        for p in g.work.rglob('ppm.temp'):
            clean_scratch(g, p.parent, 'terminal-' + str(p.parent.relative_to(g.work)).replace('/', '-'))
        g.closure(); g.verify(); result['child_closure_ok'] = True
    except Exception as exc:
        result.update(status='execution_failed', cleanup_error=str(exc), child_closure_ok=False)
    result['commands'] = g.commands
    g.write('artifacts.json', dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*'))
                                         if p.is_file() and p.name != 'ppm.temp'], errors=[]))
    result['artifacts'] = g.artifact(g.result / 'artifacts.json')
    g.write('decision.json', result)
    print(json.dumps({k: result[k] for k in ['status', 'error', 'component_improvements_bytes'] if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
