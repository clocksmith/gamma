"""New LCD-only typed-development label qualification; no training/reproduction.

Uses approved local training payload and existing authored development graphs.
Historical checkpoint/corpus, frozen vocabulary and protected cases stay intact.
"""
from pathlib import Path
import argparse
from collections import Counter
import json
import time

from ..records import LANE_ROOT, Problem
from ..rebuild_recognition import Monitor, boundary, exclusion, prepare, publish, bound_receipt, sha, digest
from ..rebuild_download import FILES, verify
from ..splits import sibling_base, IndexEntry
from . import typed_codec, typed_development, typed_support, typed_pairs, development_tests, training_pairs, mine

NAME='typed-lcd-suby-development-v1'
ASSET=LANE_ROOT/'data/reconstruction/recognition-rebuild-dev-suby-v1'
OUTPUT=LANE_ROOT/'runs'/NAME


def read(path):return json.loads(path.read_text())


def development_boundary(metadata, manifest, catalog, reservation):
    """Metadata closure before any signature, solution or test parsing."""
    limits=boundary(catalog,reservation)
    keys=set(limits['keys'])|set(manifest['near_duplicates']['dropped_index_entries'])
    uids=set(limits['uids'])|{u for group in manifest['solving'].values() for u in group}
    families=set(limits['families'])
    for q in manifest['recognition']+manifest['recognition_dev']:
        if q.get('target'):families.add(sibling_base(q['target'].removeprefix('lc:')))
        if q.get('problem_uid'):uids.add(q['problem_uid'])
    while True:
        old=(len(keys),len(uids),len(families))
        for row in metadata:
            key='lc:'+row['task_id'];uid='lcd:'+str(row['question_id']);family=sibling_base(row['task_id'])
            if key in keys or uid in uids or family in families:
                keys.add(key);uids.add(uid);families.add(family)
        for pair in manifest['near_duplicates'].get('sibling_pairs_kept',[]):
            if pair['index_key'] in keys or pair['pool_uid'] in uids:
                keys.add(pair['index_key']);uids.add(pair['pool_uid'])
                families.add(sibling_base(pair['index_key'].removeprefix('lc:')))
        if old==(len(keys),len(uids),len(families)):break
    return {'keys':sorted(keys),'uids':sorted(uids),'families':sorted(families)}


def qualify(proposal, problem, imported, entry, identity, *, judge=None):
    from ..validate import judge_problem
    judge=judge or judge_problem
    if proposal['requirements']['unsupported_requirements']:
        return None,{'reason':'unsupported_requirements'}
    if not problem.public_tests or not imported:
        return None,{'reason':'missing_public_or_independent_tests'}
    target=typed_codec.encode(proposal['program'],identity)
    code=typed_codec.render(target,identity,method=problem.entry['method'],params=[p[0] for p in problem.params])
    tests,authority=development_tests.select(proposal['uid'],imported)
    verdicts={}
    for label,cases in [('public',problem.public_tests),('independent',tests),('bound', [proposal['bound_probe']])]:
        verdicts[label]=judge(problem,code,cases).to_dict()
        if not verdicts[label]['passed']:
            return None,{'reason':'qualification_failed','verdicts':verdicts,'test_source':authority}
    pair={'schema':'algsolve.typed-pair.v1','uid':proposal['uid'],'key':entry.key,'variant':proposal['variant'],
        'problem_family':sibling_base(entry.slug),
        'input':{'statement':problem.statement,'starter_code':problem.starter_code,'params':problem.params,'public_examples':problem.public_tests},
        'target':target,'graph_sha256':typed_codec.digest(target),'pattern_sha256':typed_support.pattern(proposal['program']),
        'required_features':typed_support.features(proposal['program']),
        'recipe_usage':[x.removeprefix('recipe:') for x in typed_support.features(proposal['program']) if x.startswith('recipe:')],
        'requirements':proposal['requirements'],
        'provenance':{'license':entry.license,'attribution':entry.attribution,'proposer':proposal['proposer'],
          'source_sha256':typed_codec.digest(code),'problem_sha256':typed_codec.digest(problem.to_json()),
          'independent_tests_sha256':mine.digest(tests),'test_source':authority,
          'public_tests_passed':verdicts['public']['tests_passed'],'independent_tests_passed':verdicts['independent']['tests_passed'],
          'declared_bound_probe_passed':True,'codec_sha256':identity,
          'qualification':'new LCD-only development label; finite test agreement and bound probe, not neural prediction or historical reproduction'}}
    return pair,{'reason':'qualified','verdicts':verdicts,'test_source':authority}


def run(monitor):
    identity=typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
    proposals=typed_development.proposed()
    historical=read(LANE_ROOT/'findings/typed-real-dev-v5/test_integrity.json')
    if {r['uid'] for r in proposals}!=set(historical):raise ValueError('Not the previously permitted development proposals')
    metadata=[]
    for line in (ASSET/'LeetCodeDataset-train.jsonl').open():
        row=json.loads(line);metadata.append({k:row[k] for k in ('task_id','question_id')})
    catalog=read(LANE_ROOT/'findings/known-lookup-release-v2/approved-library.json')
    manifest=read(LANE_ROOT/'contracts/sample_manifest.json');reservation=read(LANE_ROOT/'contracts/typed_confirmation_v1.json')
    limits=development_boundary(metadata,manifest,catalog,reservation)
    selected={r['uid'] for r in proposals};wanted=set()
    for row in metadata:
        if 'lcd:'+str(row['question_id']) in selected:
            if exclusion(row,limits):raise ValueError('Development target intersects reserved metadata')
            wanted.add('lc:'+row['task_id'])
    if len(wanted)!=len(selected):raise ValueError('Missing development source')
    sources={str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')}
    contract={'schema':'algsolve.typed-lcd-suby-preparation.v1','name':NAME,'historical_reproduction':False,
        'original_corpus_sha256':'566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e',
        'codec_sha256':identity,'proposal_sha256':typed_codec.digest(proposals),'sources_sha256':sources,
        'payload':verify(ASSET/'LeetCodeDataset-train.jsonl',FILES['LeetCodeDataset-train.jsonl']),
        'boundaries_sha256':{n:sha(LANE_ROOT/n) for n in ['contracts/sample_manifest.json','contracts/typed_confirmation_v1.json','findings/known-lookup-release-v2/approved-library.json']},
        'exclusions':limits,'target_uids':sorted(selected),'target_keys':sorted(wanted),
        'model_calls':0,'training':False,'protected_scoring':False,'new_assets':False,
        'partition':'Existing connected problem/family/pattern split; every examined row remains development only.',
        'test_policy':'Existing imported source suites; exact-hash-bound historical development oracle replacements only. No output changes or test dropping.',
        'limits':{'threads':4,'rss_bytes':8*1024**3,'disk_bytes':5*1024**3,'wall_seconds':900}}
    publish(OUTPUT/'contract.json',contract)
    def check():
        if sources!={str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')}:raise ValueError('Preparation source drift')
    if (OUTPUT/'summary.json').exists():
        summary=read(OUTPUT/'summary.json')
        if any(sha(OUTPUT/n)!=h for n,h in summary['artifacts_sha256'].items()):raise ValueError('Prepared corpus drift')
        print(json.dumps({'completed_resume':True,'pairs_sha256':summary['artifacts_sha256']['pairs.jsonl']}));return
    inputs=OUTPUT/'inputs';inputs.mkdir(exist_ok=True)
    info=prepare(ASSET,inputs,wanted,wanted,limits,set(catalog['approved'])|set(catalog['excluded']))
    if info['missing_targets']:raise ValueError('Missing selected development sources')
    entries={e['key']:IndexEntry(**e) for e in read(inputs/'entries.json')};ps=read(inputs/'problems.json');tests=read(inputs/'source-tests.json')
    by_uid={e.members[0]:e for e in entries.values()};pairs=[];records=[];test_authorities={}
    receipts=OUTPUT/'qualification';receipts.mkdir(exist_ok=True)
    for i,proposal in enumerate(proposals):
        entry=by_uid[proposal['uid']];problem=Problem.from_dict(ps[entry.key]);spec=tests[entry.key]
        if spec['dropped'] or spec['public_dropped']:raise ValueError('Incomplete selected import: '+entry.key)
        binding={'contract_sha256':sha(OUTPUT/'contract.json'),'proposal_sha256':typed_codec.digest(proposal),
                 'problem_sha256':typed_codec.digest(ps[entry.key]),'tests_sha256':typed_codec.digest(spec)}
        def make():
            pair,verdict=qualify(proposal,problem,spec['tests'],entry,identity)
            return {'pair':pair,'record':dict(verdict,uid=proposal['uid'],variant=proposal['variant'])}
        result=bound_receipt(receipts/f'{i:04d}.json',binding,make);records.append(result['record'])
        if result['pair']:
            pairs.append(result['pair']);selected_tests,authority=development_tests.select(proposal['uid'],spec['tests'])
            test_authorities[proposal['uid']]={'tests':selected_tests,'authority':authority}
        check();print(json.dumps({'proposal':i+1,'total':len(proposals),'uid':proposal['uid'],'reason':result['record']['reason'],**monitor.counters()}),flush=True)
    training_pairs.assign_splits(pairs)
    for pair in pairs:pair['learning_split']='development_fit' if pair['learning_split']=='training' else 'development_audit'
    support=typed_support.audit([p for p in pairs if p['learning_split']=='development_fit'],[p for p in pairs if p['learning_split']=='development_audit'])
    from .typed_scoring import write_bytes_once
    pairs_data=''.join(json.dumps(p,allow_nan=False)+'\n' for p in pairs).encode()
    if (OUTPUT/'pairs.jsonl').exists():
        if (OUTPUT/'pairs.jsonl').read_bytes()!=pairs_data:raise ValueError('Corpus changed')
    else:write_bytes_once(OUTPUT/'pairs.jsonl',pairs_data)
    publish(OUTPUT/'test-authorities.json',test_authorities);publish(OUTPUT/'support.json',support)
    summary={'schema':'algsolve.typed-lcd-suby-preparation-summary.v1','name':NAME,'qualified_pairs':len(pairs),
        'distinct_problems':len({p['uid'] for p in pairs}),'proposals':len(proposals),'codec_sha256':identity,
        'qualification_counts':dict(Counter(r['reason'] for r in records)),
        'public_tests_passed':sum(p['provenance']['public_tests_passed'] for p in pairs),
        'independent_tests_passed':sum(p['provenance']['independent_tests_passed'] for p in pairs),
        'bound_probes_passed':len(pairs),'partitions':dict(Counter(p['learning_split'] for p in pairs)),
        'partition_eligible':support['partition_eligible'],'training_ready':len(pairs)==len(proposals) and support['partition_eligible'],
        'model_calls':0,'student_trained':False,'historical_reproduction':False,'protected_scored':False,
        'resource_counters':monitor.counters(),
        'next_action':'Review/authorize the separately proposed single fixed CPU training run; never use the historical checkpoint/corpus identity for these artifacts.',
        'limitations':['Teacher label qualification only; no new autonomous prediction or generalization evidence.','Only previously authored permitted development proposals, newly imported/qualified against approved LCD snapshot.','Historical raw corpus and checkpoint remain unavailable.']}
    check();summary['artifacts_sha256']={str(p.relative_to(OUTPUT)):sha(p) for p in OUTPUT.rglob('*') if p.is_file() and p.name!='lock' and 'failures' not in p.parts}
    publish(OUTPUT/'summary.json',summary);print(json.dumps(summary,indent=2),flush=True)


def main():
    import fcntl
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--name',choices=[NAME],required=True);parser.parse_args()
    OUTPUT.mkdir(parents=True,exist_ok=True);lock=(OUTPUT/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    monitor=Monitor([ASSET,LANE_ROOT/'runs']);monitor.start()
    print(f'[run-contract] run_name={NAME} pairs_input_spec=approved-LCD-training+existing-permitted-development-graphs resume_from=atomic-qualification-receipts resume_stage=existing decode=none eval_dataset_paths=development-only device=cpu schedule=serial runtime_mode=reviewed-linux-sandbox sweep_mode=none training=none',flush=True)
    try:run(monitor)
    except BaseException as error:
        path=OUTPUT/'failures';path.mkdir(exist_ok=True)
        publish(path/f'{time.time_ns()}.json',{'error_type':type(error).__name__,'detail':str(error),'resources':monitor.counters()});raise
    finally:monitor.stop.set()

if __name__=='__main__':main()
