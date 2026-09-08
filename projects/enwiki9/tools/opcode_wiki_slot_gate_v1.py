#!/usr/bin/env python3
"""One bounded P/K/D wiki-slot comparison over the frozen development input."""
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
from tools.opcode_field_compact_gate_v1 import compare, require_phase, BudgetStop

CID = 'opcode_wiki_slot_v1'
SELF = 'tools/opcode_wiki_slot_gate_v1.py'
CLI = 'tools/opcode_wiki_slot_observe_v1.py'
CAPS = dict(cpus=[2], memory_bytes=4294967296, scratch_bytes=1073741824,
            swap_bytes=0, wall_seconds=2400)
PHASES = dict(phase_cpu_seconds=180, phase_wall_seconds=240, phase_address_bytes=2147483648)
require = phase.require


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS and plan['phase_resources'] == PHASES,
            'plan identity or limits differ')
    require(plan['input']['bytes'] == 250000 and plan['input']['sha256'] ==
            '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3', 'development population differs')
    require({SELF, CLI, 'tools/opcode_field_compact_observe_v1.py', 'tools/opcode_field_repair_cli_v1.py',
             'tools/opcode_field_compact_gate_v1.py', 'tools/opcode_field_repair_gate_v2.py',
             'tools/dualstream_grammar_gate_v1.py', 'tools/research_contracts.py',
             'tests/test_opcode_wiki_slot_gate_v1.py'} <= {r['path'] for r in plan['source_files']},
            'source closure missing')
    require(len(plan['package_files']) == 2 and {Path(r['path']).name for r in plan['package_files']} == {'p','program.py'},
            'package members differ')
    require(all(r['path'].startswith('programs/'+CID+'/') for r in plan['package_files']), 'package owner differs')
    require(plan['runtime_files'] and plan['evidence'], 'runtime or evidence missing')


def authenticate(validate_only=False):
    contract_path = ROOT/'operations/adaptive/experiments'/f'{CID}.json'
    contract = phase.read_json(contract_path)
    reference = dict(path=str(contract_path.relative_to(ROOT)), sha256='sha256:'+phase.sha(contract_path))
    require(contract['experimentId'] == CID and contract['status'] == 'frozen'
            and contract['registrationTiming'] == 'prospective', 'contract authority differs')
    bound = {}
    for row in contract['inputs']:
        path = ROOT/row['path']
        require(path.resolve() == path and phase.sha(path) == row['sha256'].removeprefix('sha256:'), 'frozen input changed')
        bound[row['path']] = row['sha256'].removeprefix('sha256:')
    snapshot = ROOT/'programs'/CID if validate_only else Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    plan = phase.read_json(snapshot/'gate-plan.json'); validate_plan(plan)
    for key in ('input','parent_archive','parent_audit'):
        binding.check_file(plan[key])
        require(bound.get(plan[key]['path']) == plan[key]['sha256'], 'unfrozen comparison input')
    for key in ('source_files','evidence'):
        for row in plan[key]:binding.check_file(row)
    for row in plan['runtime_files']:binding.check_file(row, absolute=True)
    for row in plan['package_files']:binding.check_file(row, snapshot=snapshot, candidate=CID)
    if not validate_only:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) == reference
                and os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID'] == CID, 'canonical invocation absent')
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS']); jid = marker.parent.name.removesuffix('.resources')
        jobs = list((ROOT/'operations/adaptive/running').glob('*'+jid+'.json'))
        require(len(jobs) == 1, 'ambiguous running job')
        job = phase.read_json(jobs[0])
        require(job['candidate_id'] == CID and job['experiment'] == reference and job['execution_mode'] == 'discovery'
                and all(job['resource_budget'][k] == v for k,v in CAPS.items()), 'job authority differs')
        revision = ROOT/job['candidate_revision']['path']
        require(phase.sha(revision) == job['candidate_revision']['sha256'].removeprefix('sha256:'), 'revision changed')
        binding.verify_snapshot(snapshot, phase.read_json(revision))
        group = Path(job['execution_resources']['cgroup_path'])
        member = next(x[3:] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
        require(group == Path('/sys/fs/cgroup'+member) and group.stat().st_ino == job['execution_resources']['cgroup_inode']
                and (group/'memory.max').read_text().strip() == str(CAPS['memory_bytes'])
                and (group/'memory.swap.max').read_text().strip() == '0' and os.sched_getaffinity(0) == {2},
                'resource enforcement differs')
    return reference, plan, snapshot


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    directory, snapshot = directory.resolve(), snapshot.resolve()
    raw = ROOT/plan['input']['path']; expected = raw.read_bytes()
    parent_archive = (ROOT/plan['parent_archive']['path']).read_bytes()
    parent_audit = phase.read_json(ROOT/plan['parent_audit']['path'])
    rows = {}; commands = []
    def run(label, operation, src, dst, arm, audit=None):
        command = [sys.executable, str(ROOT/CLI), operation, str(src), str(dst),
                   '--candidate-root', str(snapshot), '--arm', arm]
        if audit is not None:command += ['--audit', str(audit)]
        record = phase.run_phase(directory, label, command, limits, marker)
        require_phase(record, (directory/(label+'.stderr')).read_text(errors='replace'))
        try:record['codec_resources'] = phase.read_json(directory/(label+'.stdout'))
        except (OSError, ValueError) as error:
            record['codec_resources'] = None;record['missing_diagnostics'] = [str(error)]
        commands.append(record)
    for arm in 'PKD':
        arc = directory/(arm+'.arc'); restored = directory/(arm+'.raw'); repeat = directory/(arm+'.repeat.arc')
        audits = {key:directory/(arm+'-'+key+'.audit.json') for key in ('encode','decode','repeat')}
        run(arm+'-encode','encode',raw,arc,arm,audits['encode'])
        run(arm+'-decode','decode',arc,restored,arm,audits['decode'])
        compare(expected, restored.read_bytes(), directory, arm+'-inverse')
        run(arm+'-repeat','encode',restored,repeat,arm,audits['repeat'])
        compare(arc.read_bytes(), repeat.read_bytes(), directory, arm+'-repeat')
        enc = phase.read_json(audits['encode'])
        for label in ('decode','repeat'):
            compare(enc, phase.read_json(audits[label]), directory, arm+'-'+label+'-state')
        if arm == 'P':
            compare(parent_archive, arc.read_bytes(), directory, 'retained-parent-archive')
            compare(parent_audit, enc['parent'], directory, 'retained-parent-state')
        if arm == 'K':
            compare((directory/'P.arc').read_bytes(), arc.read_bytes(), directory, 'PK-archive')
            compare(rows['P']['audit']['parent'], enc['parent'], directory, 'PK-projection')
        rows[arm] = dict(archive_bytes=arc.stat().st_size, audit=enc,
            artifacts=dict(archive=phase.artifact(arc), restored=phase.artifact(restored), repeat=phase.artifact(repeat)),
            audits={k:phase.artifact(p) for k,p in audits.items()}, commands=commands[-3:])
    plain = directory/'D.plain.arc'
    run('D-plain','encode',raw,plain,'D')
    compare((directory/'D.arc').read_bytes(), plain.read_bytes(), directory, 'D-observation')
    gain = rows['P']['archive_bytes'] - rows['D']['archive_bytes']
    return dict(arms=rows, commands=commands, archive_saving_bytes=gain,
                correctness_pass=True, controls_equivalent=True,
                interpretation='archive-gain' if gain > 0 else 'no-activation' if rows['D']['audit']['changed_slot_bytes'] == 0 else 'active-nonpaying',
                prediction_gate_pass=gain > 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--validate-only',action='store_true')
    args = parser.parse_args();reference,plan,snapshot = authenticate(args.validate_only)
    if args.validate_only:print(json.dumps(dict(status='preflight_pass', codec_executed=False)));return 0
    directory = ROOT/'results'/CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-wiki-slot-gate.v1', candidate_id=CID,
        experiment=reference, input=plan['input'], correctness_pass=False, status='running',
        package_files=plan['package_files'], local_source_bytes=sum(r['bytes'] for r in plan['package_files']),
        source_delta_bytes=sum(r['bytes'] for r in plan['package_files'])-5746,
        complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
        note='Development comparison only; archive and source delta are separate. No automatic confirmation or larger launch.')
    try:
        stage.update(run_comparison(directory,plan,snapshot,Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate();stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed', failure_class='budget-exhausted' if isinstance(error,(BudgetStop,MemoryError))
                     else 'infrastructure-failure' if isinstance(error,OSError) else 'implementation-failure',
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory/'artifacts.json', dict(complete=stage['status']=='passed',
                     files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory/'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
