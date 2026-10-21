"""Bounded synthetic qualification of the harness itself; never runs source programs."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import resource
import time
import unittest

import harness as h
from fixtures import synthetic_dataset, comparison_pool
from tiny_reference import support_and_reference


def write_new(path, value):
    raw=h.canonical(value)+b'\n'
    with path.open('xb') as stream:stream.write(raw)
    return h.raw_hash(raw)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,help='New directory inside this lane; never overwrite evidence.')
    args=parser.parse_args()
    output=Path(args.output).resolve()
    if output.parent!=h.ROOT or output.exists():raise ValueError('output must be a new direct child of this lane')
    if os.sched_getaffinity(0)!={13}:raise ValueError('run with taskset -c 13')
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(20,20))
    existing_lane_bytes=sum(path.stat().st_size for path in h.ROOT.rglob('*') if path.is_file())
    output.mkdir()
    started=datetime.now(timezone.utc).isoformat();cpu=time.process_time();wall=time.monotonic()
    data,seeds=synthetic_dataset()
    data_sha=write_new(output/'dataset.synthetic.json',data)
    seeds_sha=write_new(output/'human-seeds.json',seeds)
    frozen=h.load_dataset(output/'dataset.synthetic.json',data_sha)
    prepared=[]
    for width in (6,7,8):
        for track in h.TRACKS:
            for seed_policy in ('designed-only','mined-only','human-plus-mined'):
                pieces,state=comparison_pool(frozen,seeds,track,seed_policy,width)
                moves=list(h.neighbors(frozen,pieces,state,limit=8))
                states=[state]+[candidate for _,candidate in moves]
                arm_id=f'{track}-{seed_policy}-{width}'
                candidates_sha=write_new(output/(arm_id+'-candidates.json'),{'pieces':{key:asdict(piece) for key,piece in sorted(pieces.items())},'states':[asdict(s) for s in states],'moves':[move for move,_ in moves]})
                prepared.append((arm_id,track,seed_policy,width,pieces,state,moves,states,candidates_sha))
    # Freeze source pool, split, candidates, moves and bounds before observing their costs.
    plan={'schema':'gamma.energy-predeclaration.v1','started_at':started,'data_sha256':data_sha,'seeds_sha256':seeds_sha,
          'evidence_class':'synthetic_fixture_only','cpu_affinity':[13],'memory_limit_bytes':512*1024**2,'cpu_limit_seconds':20,
          'candidate_policy':'lines plus recurrent 2/4/8-codepoint strings; single-character coverage control; distinct-problem support',
          'human_policy':'exact witnessed count-map lines plus full 155-byte runtime helper; not yet qualified real alternatives',
          'initial_state_policy':'observed characters for compression; full exact lines for readable; add explicit human seeds only in human-plus-mined',
          'move_policy':'deterministic round-robin add/delete/swap/source-alternative rewrite; first eight distinct bounded neighbors',
          'max_states_per_arm':9,'tracks':['compression','readable'],'widths':[6,7,8],'seeds':['designed-only','mined-only','human-plus-mined'],
          'designed_only_policy':'exact concrete human seeds only; no implicit alphabet or framing strings; retain unrepresentable problems in denominator',
          'candidate_manifests':{row[0]:row[-1] for row in prepared},
          'tiny_reference':{'width':6,'track':'compression','human_candidates_max':3,'enumerated_states_max':32,'scope':'all subsets of the concrete helper/allocation/increment additions and all synthetic validation source choices'},
          'evaluation_split':'validation','evaluation_problems':['fixture-a','fixture-b'],
          'scorer':'exact-package-cost baseline only; no trained or demonstration model',
          'candidate_execution':False,'training':False,
          'code_sha256':{path.name:h.raw_hash(path.read_bytes()) for path in sorted(h.ROOT.glob('*.py'))},
          'dependencies':{str(h.CORE.relative_to(h.LITERALS)):h.CORE_SHA,str(h.CODEC.relative_to(h.LITERALS)):h.CODEC_SHA}}
    plan_sha=write_new(output/'predeclaration.json',plan)
    log=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(h.ROOT),pattern='test_harness.py')
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (output/'tests.txt').write_text(log.getvalue())
    test_receipt={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful(),'candidate_execution':False}
    write_new(output/'tests.json',test_receipt)
    if not result.wasSuccessful():
        print(log.getvalue());raise SystemExit(1)
    arms=[]
    for arm_id,track,seed_policy,width,pieces,state,moves,states,candidates_sha in prepared:
        if time.process_time()-cpu>=15:raise RuntimeError('bounded experiment stopped before next arm')
        receipt=h.compare(frozen,pieces,states,None,max_evaluations=9,max_cpu_seconds=min(2,15-(time.process_time()-cpu)))
        receipt.update(track=track,seed_policy=seed_policy,width=width,candidate_count=len(pieces),
                       candidate_manifest_sha256=candidates_sha,
                       initial_state_id=h.state_identity(state),moves=[move for move,_ in moves],predeclaration_sha256=plan_sha)
        sha=write_new(output/(arm_id+'.json'),receipt)
        best=next((row['labels'] for row in receipt['records'] if row['state_id']==receipt['exact_best']),None)
        arms.append({'id':arm_id,'receipt_sha256':sha,'candidates':len(pieces),'attempts':receipt['exact_evaluation_attempts'],
                     'eligible':receipt['eligible'],'rejected':len(receipt['rejected']),'initial_entries':len(state.piece_ids),
                     'entries':best['entries'] if best else None,'coverage':receipt['best_coverage'],'coverage_denominator':receipt['coverage_denominator'],
                     'selections':best['selections'] if best else None,'input_bits':best['input_bits'] if best else None,'package_bits':best['package_bits'] if best else None,
                     'reused_noncharacter_entries':best['reused_noncharacter_entries'] if best else None,'character_selections':best['character_selections'] if best else None})
    if time.process_time()-cpu>=15:raise RuntimeError('bounded experiment stopped before tiny reference')
    combined,initial=comparison_pool(frozen,seeds,'compression','human-plus-mined',6)
    _,basis=comparison_pool(frozen,seeds,'compression','mined-only',6)
    additions=tuple(sorted(set(initial.piece_ids)-set(basis.piece_ids)))
    reference=support_and_reference(frozen,combined,basis,additions)
    reference_sha=write_new(output/'tiny-reference.json',reference)
    total_files=sum(path.stat().st_size for path in h.ROOT.rglob('*') if path.is_file())
    new_files_bytes=total_files-existing_lane_bytes
    if new_files_bytes>4*1024**2:raise RuntimeError('new-file budget exceeded')
    summary={'schema':'gamma.energy-smoke.v1','started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),
             'predeclaration_sha256':plan_sha,'data_sha256':data_sha,'human_seed_sha256':seeds_sha,
             'tiny_reference_sha256':reference_sha,'tiny_reference_states':reference['enumerated_states'],
             'tests':test_receipt,'arms':arms,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,
             'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'cpu_affinity':sorted(os.sched_getaffinity(0)),
             'lane_files_bytes_before_summary':total_files,'existing_lane_bytes':existing_lane_bytes,'new_files_bytes_before_summary':new_files_bytes,'new_file_budget_bytes':4*1024**2,'candidate_programs_executed':0,'training_performed':False,
             'model_supplied':False,'qualified_real_problems':0,
             'limitations':['Two synthetic validation strings; no real problem solving evidence.',
                            'Reported seed witnesses are unqualified successors requiring root qualification.',
                            'Readable arm contains exact lines, some partial blocks, plus complete count helpers; not all units are balanced statements.',
                            'Finite bounded neighborhood best is not a global optimum; width/track objectives remain separate.',
                            'No learned model is trained or benchmarked; learned interface is tested with constant spies only.']}
    digest=write_new(output/'summary.json',summary)
    print(json.dumps({'summary':str(output/'summary.json'),'sha256':digest,'tests':test_receipt,'arms':len(arms),'cpu_seconds':summary['cpu_seconds'],'max_rss_bytes':summary['max_rss_bytes']}))


if __name__=='__main__':main()
