#!/usr/bin/env python3
"""Bounded unchanged-parent calibration attribution using existing phase guards."""
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_wiki_slot_gate_v1 as gate


def configure():
    gate.CID='opcode_calibration_cost_v1'
    gate.SELF='tools/opcode_calibration_gate_v1.py'
    gate.CLI='tools/opcode_calibration_observe_v1.py'
    gate.CAPS=dict(gate.CAPS,wall_seconds=900)
    return gate


def run_comparison(directory,plan,snapshot,marker,limits):
    directory=directory.resolve();snapshot=snapshot.resolve()
    raw=ROOT/plan['input']['path'];expected=raw.read_bytes()
    arc=directory/'K.arc';restored=directory/'K.raw';repeat=directory/'K.repeat.arc'
    commands=[];audits=[]
    for label,operation,source,output in (('encode','encode',raw,arc),
        ('decode','decode',arc,restored),('repeat','encode',restored,repeat)):
        audit=directory/(label+'.audit.json')
        command=[sys.executable,str(ROOT/'tools/opcode_calibration_observe_v1.py'),operation,
                 str(source),str(output),'--candidate-root',str(snapshot),'--audit',str(audit)]
        record=gate.phase.run_phase(directory,label,command,limits,marker)
        gate.require_phase(record,(directory/(label+'.stderr')).read_text(errors='replace'))
        try:record['codec_resources']=gate.phase.read_json(directory/(label+'.stdout'))
        except (OSError,ValueError) as error:
            record['codec_resources']=None;record['missing_diagnostics']=[str(error)]
        commands.append(record);audits.append(gate.phase.read_json(audit))
    gate.compare(expected,restored.read_bytes(),directory,'inverse')
    gate.compare(arc.read_bytes(),repeat.read_bytes(),directory,'repeat')
    gate.compare((ROOT/plan['parent_archive']['path']).read_bytes(),arc.read_bytes(),directory,'parent-archive')
    gate.compare(gate.phase.read_json(ROOT/plan['parent_audit']['path']),audits[0]['parent'],directory,'parent-state')
    for name,audit in zip(('decode','repeat'),audits[1:]):
        gate.compare(audits[0],audit,directory,name+'-state')
    return dict(correctness_pass=True,commands=commands,audit=audits[0],archive_bytes=arc.stat().st_size,
        literal_sse_excess_bits=audits[0]['literal_sse_excess_bits'],archive_saving_bytes=0,
        artifacts={k:gate.phase.artifact(p) for k,p in [('archive',arc),('restored',restored),('repeat',repeat)]})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args();configure();reference,plan,snapshot=gate.authenticate(args.validate_only)
    if args.validate_only:print(json.dumps(dict(status='preflight_pass',codec_executed=False)));return 0
    out=ROOT/'results'/gate.CID
    gate.require(out.is_dir() and not any(out.iterdir()),'result directory must be empty')
    stage=dict(schema='gamma.enwiki9.opcode-calibration-gate.v1',candidate_id=gate.CID,
        experiment=reference,input=plan['input'],correctness_pass=False,status='running',
        complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0,
        note='Unchanged codec and fixed parse. Positive literal excess may justify a separate exact archive ablation; it is not earned compression.')
    try:
        stage.update(run_comparison(out,plan,snapshot,Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS']),gate.PHASES))
        gate.authenticate();stage.update(status='passed',frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed',failure_class='budget-exhausted' if isinstance(error,(gate.BudgetStop,MemoryError))
            else 'infrastructure-failure' if isinstance(error,OSError) else 'implementation-failure',error=str(error))
    gate.phase.write_json(out/'artifacts.json',dict(complete=stage['status']=='passed',
        files=[gate.phase.artifact(p) for p in sorted(out.iterdir()) if p.is_file()]))
    gate.phase.write_json(out/'stage-decision.json',stage)
    print(json.dumps(dict(status=stage['status'],correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
