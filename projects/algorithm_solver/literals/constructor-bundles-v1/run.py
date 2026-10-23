"""Four matched structured coding arms on a later hash-bound D11 source cohort.

No source is executed or rewritten here. Activation requires a completed,
qualified flat stacking run and a new reviewed/pushed structured freeze.
"""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Assertion validation requires normal Python mode; PYTHONOPTIMIZE/-O is forbidden')

import argparse
import concurrent.futures
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import platform
import resource
import sys
import time
import codec
import optimizer

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
spec = importlib.util.spec_from_file_location('structured_stack_analyze',LIT/'cost-decomposition-v1/analyze.py')
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)
ARMS = {'L1':set(), 'T1':{'P','I'}, 'LB':set(), 'TB':{'P','I'}}


def read(path):
    return json.loads(Path(path).read_text())


def fit(job):
    started = time.monotonic()
    arm, source_root, out, c, cores = job
    os.sched_setaffinity(0,set(cores))
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)
    source_root, out = Path(source_root),Path(out)
    texts = read(source_root/'fit/D11/fit-sources.json')
    assert set(texts) == {str(i) for i in c['partition']['dev_fit']}
    nodes = codec.extract(texts)
    forbidden = {body for group in nodes.values() for body in group['bodies']}
    pools = optimizer.pool(texts,nodes,forbidden)
    initial = [codec.literal(word) for word in read(source_root/'artifacts/D11/dictionary.json')]
    assert not any(k[1:] in forbidden for k in initial)
    folder = out/arm
    folder.mkdir()
    analyze.write(folder/'fit-nodes.json',nodes)
    analyze.write(folder/'pool.json',pools)
    analyze.write(folder/'fit-banned.json',sorted(forbidden))
    def checkpoint(state,trace,trials):
        path=folder/'partial-search.json'
        temporary=folder/'partial-search.tmp'
        analyze.write(temporary,{'complete':False,'promotion_allowed':False,'trials':trials,
                                'dictionary':state['keys'],'fit_selections':state['selections'],'trace':trace})
        temporary.replace(path)
    state,info = optimizer.optimize(texts,nodes,initial,pools,forbidden,c['search'],arm,checkpoint)
    analyze.write(folder/'dictionary.json',state['keys'])
    analyze.write(folder/'fit-plans.json',state['rows'])
    analyze.write(folder/'fit-nodes.json',nodes)
    analyze.write(folder/'fit-banned.json',sorted(forbidden))
    analyze.write(folder/'pool.json',pools)
    analyze.write(folder/'trace.json',info.pop('trace'))
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'source_fit_sha256':c['private_files']['fit/D11/fit-sources.json'],
        'initial_dictionary_sha256':c['private_files']['artifacts/D11/dictionary.json'],
        'files':{p.name:analyze.sha(p.read_bytes()) for p in folder.iterdir() if p.is_file()}})
    result = {'arm':arm,'fit_selections':state['selections'],'search':info,
              'fit_wall_seconds':time.monotonic()-started,
              'fit_seal_sha256':analyze.sha((folder/'fit-seal.json').read_bytes()),
              'prefix_pool':len(pools['constructors']['P']),'identifier_pool':len(pools['constructors']['I']),
              'literal_pool':len(pools['literal_pool']),'operand_pool':len(pools['operand_pool']),'pool_sha256':analyze.sha((folder/'pool.json').read_bytes())}
    analyze.write(folder/'fit-summary.json',result)
    print(json.dumps({'arm':arm,'fit_selections':state['selections'],'search':info}),flush=True)
    return result


def aggregate(rows,ids,db,decoder_bytes):
    all_rows = [rows[str(i)] for i in ids]
    good = [r for r in all_rows if r['encodable']]
    n = sum(r['selections'] for r in good)
    costs = lambda field: analyze.distribution([r[field] for r in good]) if good else {}
    return {'problems':len(ids),'covered':len(good),'qualified':sum(r['qualified_source'] for r in good),
            'failed_ids':[int(i) for i in ids if not rows[str(i)]['encodable']],
            'selections':costs('selections'),'actions':costs('actions'),
            'single_character_codes':sum(r['single_characters'] for r in good),
            'single_character_fraction':sum(r['single_characters'] for r in good)/n if n else None,
            'prefix_codes':sum(r['prefix_codes'] for r in good),
            'identifier_codes':sum(r['identifier_codes'] for r in good),
            'argument_codes':sum(r['argument_codes'] for r in good),
            'generated_bytes':sum(r['generated_bytes'] for r in good),
            'prefix_fixed_bytes':sum(r['prefix_fixed_bytes'] for r in good),
            'identifier_fixed_bytes':sum(r['identifier_fixed_bytes'] for r in good),
            'repeated_identifier_bytes':sum(r['repeated_identifier_bytes'] for r in good),
            'eligible_programs':sum(r['eligible'] for r in all_rows),
            'arm_eligible_programs':sum(r['arm_eligible'] for r in all_rows),
            'used_programs':sum(r['prefix_codes']+r['identifier_codes'] > 0 for r in good),
            'source_bytes':sum(r['source_bytes'] for r in all_rows),
            'framing_bytes':41*len(good),'payload_bits':8*n,'padding_bits':0,
            'dictionary_bytes':len(db),'packet_bytes':41*len(good)+n,
            'package_bytes':len(db)+41*len(good)+n,
            'package_with_decoder_dependencies':len(db)+41*len(good)+n+decoder_bytes,
            'full_cohort_cost_available':len(good)==len(ids)}


def measure(arm,texts,nodes,keys,pools,folder,c):
    typed = arm in ('T1','TB')
    db = codec.dictionary(keys) if typed else codec.literal_dictionary(keys)
    (folder/'dictionary.bin').write_bytes(db)
    packets = folder/'packets'
    packets.mkdir()
    plans,rows,decoded = {},{},{}
    eligibility = set(key for values in pools.values() for key in values)
    arm_eligibility = {key for key in eligibility if key[0] in ARMS.get(arm,set())}
    banned = {body for group in nodes.values() for body in group['bodies']}
    illegal = sorted(analyze.sha(k[1:].encode()) for k in keys if k[0]=='L' and k[1:] in banned)
    for pid,text in sorted(texts.items()):
        receipt = c['source_qualification'][pid]
        assert receipt['passed'] and receipt['source_sha256'] == analyze.sha(text.encode())
        common = {'source_sha256':receipt['source_sha256'],'source_bytes':len(text.encode()),
                  'qualified_source':True,'qualification_reused':True,
                  'arm_eligible':any(n['key'] in arm_eligibility for family in ('prefix','identifier') for n in nodes[pid][family]),
                  'eligible':any(n['key'] in eligibility for family in ('prefix','identifier') for n in nodes[pid][family])}
        try:
            plan = codec.encode_source(text,nodes[pid],keys)
        except ValueError:
            rows[pid] = {**common,'encodable':False}
            continue
        plans[pid] = plan
        if typed:
            packet = codec.packet(keys,plan['tokens'])
        else:
            vocab = [k[1:] for k in keys]
            ids = {k:i for i,k in enumerate(keys)}
            packet = analyze.encode(vocab,[ids[k] for k in plan['tokens']],8)
            decoded[pid] = analyze.decode(db,packet)
            assert len(analyze.shortest_encode(text,vocab))==plan['selections']
        (packets/f'{pid}.bin').write_bytes(packet)
        rows[pid] = {**common,'encodable':True,'selections':plan['selections'],'actions':plan['selections']+1,
                     'packet_sha256':analyze.sha(packet),'packet_bytes':len(packet),
                     **{k:plan[k] for k in ('single_characters','prefix_codes','identifier_codes','argument_codes',
                                          'prefix_fixed_bytes','identifier_fixed_bytes','repeated_identifier_bytes','generated_bytes')}}
    # An invalid generated packet is an experiment failure, not a fallback to
    # its literal encoding. No trial dictionary is selected from decode results.
    if typed and plans:
        decoded = codec.decode_many(keys,plans)
    assert set(decoded)==set(plans)
    for pid,actual in decoded.items():
        decoded_hash=analyze.sha(actual.encode())
        assert actual==texts[pid] and decoded_hash==c['source_qualification'][pid]['source_sha256']
        rows[pid]['decoded_source_sha256']=decoded_hash
    analyze.write(folder/'sources.json',texts)
    analyze.write(folder/'plans.json',plans)
    result = {'arm':arm,'representation':'flat_literal' if not typed else 'structured_2c',
              'encoder':'canonical_minN_then_IDs','entries':len(keys),
              'prefix_entries':sum(k[0]=='P' for k in keys),'identifier_entries':sum(k[0]=='I' for k in keys),
              'dictionary_sha256':analyze.sha(db),'dictionary_bytes':len(db),'illegal_entry_sha256':illegal,
              'per_problem':rows,'decoder_dependency_bytes':c['decoder_bytes']['typed' if typed else 'literal']}
    for split,group in (('fit','dev_fit'),('validation','dev_val')):
        result[split] = aggregate(rows,c['partition'][group],db,result['decoder_dependency_bytes'])
    return result


def main(source_root,out):
    c = read(HERE/'contract.json')
    assert c['source_bound'] and c['source_run'] == str(source_root.resolve())
    assert platform.python_version() == c['python_version']
    assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    os.sched_setaffinity(0,set(c['all_cores']))
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],c['limits']['address_space_bytes']))
    for path,digest in c['runtime_files'].items():
        assert analyze.sha(Path(path).read_bytes()) == digest,path
    for rel,digest in c['code_hashes'].items():
        assert analyze.sha((LIT/rel).read_bytes()) == digest,rel
    for rel,digest in c['private_files'].items():
        if rel=='artifacts/D11/sources.json':continue
        assert analyze.sha((source_root/rel).read_bytes()) == digest,rel
    out.mkdir(parents=True,exist_ok=False)
    analyze.write(out/'status.json',{'complete':False,'phase':'fit'})
    started = time.monotonic()
    jobs = [(arm,str(source_root),str(out),c,cores) for arm,cores in zip(ARMS,c['cores'])]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
        summaries = list(pool.map(fit,jobs))
    pools_seen = {summary['pool_sha256'] for summary in summaries}
    assert len(pools_seen) == 1
    for arm in ARMS:
        folder = out/arm
        seal = read(folder/'fit-seal.json')
        assert not seal['validation_loaded']
        for name,digest in seal['files'].items():
            assert analyze.sha((folder/name).read_bytes()) == digest,(arm,name)
    analyze.write(out/'all-fit-sealed.json',{'validation_loaded':False,'arms':summaries})
    # Validation source values are first read after every fitted dictionary seals.
    analyze.write(out/'status.json',{'complete':False,'phase':'validation'})
    assert analyze.sha((source_root/'artifacts/D11/sources.json').read_bytes())==c['private_files']['artifacts/D11/sources.json']
    texts = read(source_root/'artifacts/D11/sources.json')
    expected = {str(i) for ids in c['partition'].values() for i in ids}
    assert set(texts) == set(c['source_qualification']) == expected
    nodes = codec.extract(texts)
    results = []
    for arm in ARMS:
        folder = out/arm
        keys = read(folder/'dictionary.json')
        pools = read(folder/'pool.json')['constructors']
        result = measure(arm,texts,nodes,keys,pools,folder,c)
        result['fit_search'] = next(s for s in summaries if s['arm']==arm)
        assert result['fit']['selections']['total'] == result['fit_search']['fit_selections']
        analyze.write(folder/'results.json',result)
        results.append(result)
    folder = out/'D11-reference'
    folder.mkdir()
    seed = codec.order(codec.literal(s) for s in read(source_root/'artifacts/D11/dictionary.json'))
    analyze.write(folder/'dictionary.json',seed)
    reference = measure('D11',texts,nodes,seed,pools,folder,c)
    analyze.write(folder/'results.json',reference)
    results.append(reference)
    analyze.write(out/'all-validation-sealed.json',{
        'all_fit_seal_sha256':analyze.sha((out/'all-fit-sealed.json').read_bytes()),
        'source_file_sha256':c['private_files']['artifacts/D11/sources.json'],
        'arms':{arm['arm']:{'results_sha256':analyze.sha((out/('D11-reference' if arm['arm']=='D11' else arm['arm'])/'results.json').read_bytes()),
                           'dictionary_sha256':arm['dictionary_sha256']} for arm in results}})
    analyze.write(out/'results.json',{'arms':results,'seconds':time.monotonic()-started,
                                     'source_receipt_sha256':c['private_files']['results.json'],
                                     'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),
                                     'source_qualification_reused':True,'fresh_case_executions':0})
    analyze.write(out/'status.json',{'complete':True,'phase':'complete'})


def guarded_main(source_root,out):
    assert not out.exists(), 'refuse existing output'
    try:
        return main(source_root,out)
    except BaseException as error:
        out.mkdir(parents=True,exist_ok=True)
        status=read(out/'status.json') if (out/'status.json').exists() else {'phase':'setup'}
        analyze.write(out/'failure.json',{'phase':status['phase'],'error_type':type(error).__name__,
                      'message':str(error),'complete':False,'promotion_allowed':False})
        analyze.write(out/'status.json',{'complete':False,'phase':status['phase'],'failed':True})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    guarded_main(args.source_run.resolve(),args.output.resolve())
