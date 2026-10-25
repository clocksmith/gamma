"""Joint exact-source/exact-literal search with balanced composable fragments."""
from __future__ import annotations
import argparse
from bisect import bisect_left
from collections import Counter
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import sys
import time
HERE=Path(__file__).resolve().parent
LIT=HERE.parent
PAIRED=LIT/'paired-authoring-v1'
sys.path.insert(0,str(PAIRED))
import verify_baseline
import verify_adapted
b=verify_baseline.replay


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out);return out
compact=module('joint_compact',LIT/'compact-search-v1/search.py')
compare=compact.compare
ALPHABET=compact.ALPHABET
BUCKETS=((2,4),(5,8),(9,16),(17,32),(33,64))
CONFIG={'pool_per_bucket':300,'rounds':4,'evaluations':512,'cpu_seconds':300,'additions_per_bucket':4,'single_removals':8,'pair_removals':4,'pair_proposals':12}


def bucket(piece):
    return next((i for i,(low,high) in enumerate(BUCKETS) if low<=len(piece)<=high),None)


def banned_strings(texts):
    banned=compact.forbidden(texts)
    for text in texts.values():
        tokens=compact.lexical_tokens(text)
        for at in range(len(tokens)-2):
            if tokens[at][0]!='class' or tokens[at+1][0]!='Solution' or tokens[at+2][0]!='{':continue
            cursor=at+3;depth=1
            while cursor<len(tokens) and depth:
                token,start,end=tokens[cursor]
                if depth==1 and cursor+1<len(tokens) and tokens[cursor+1][0]=='(':
                    first=cursor;cursor+=1;parens=0
                    while cursor<len(tokens):
                        parens+=(tokens[cursor][0]=='(')-(tokens[cursor][0]==')');cursor+=1
                        if parens==0:break
                    if cursor>=len(tokens) or tokens[cursor][0]!='{':raise ValueError('unsupported Solution method syntax')
                    opening=tokens[cursor][1];braces=0
                    while cursor<len(tokens):
                        braces+=(tokens[cursor][0]=='{')-(tokens[cursor][0]=='}');closing=tokens[cursor][2];cursor+=1
                        if braces==0:break
                    if braces:raise ValueError('unclosed Solution method')
                    body=text[opening:closing];definition=text[tokens[first][1]:closing]
                    banned.update((definition,body,body[1:-1],body[1:-1].strip()))
                    continue
                depth+=(token=='{')-(token=='}');cursor+=1
    return banned


def build_pool(texts,owners,banned,per_bucket=300):
    """Suffix adjacency witnesses support across distinct problems, not variants."""
    suffixes=sorted((text[i:i+64],owners[key]) for key,text in texts.items() for i in range(len(text)-1))
    witnessed=set()
    for (left,pid),(right,qid) in zip(suffixes,suffixes[1:]):
        if pid==qid:continue
        length=0
        while length<min(len(left),len(right)) and left[length]==right[length]:length+=1
        for end in range(2,length+1):
            piece=left[:end]
            if piece not in banned:witnessed.add(piece)
    keys=[s for s,_ in suffixes]
    scores={piece:(bisect_left(keys,piece+chr(0x10ffff))-bisect_left(keys,piece))*(len(piece)-1) for piece in witnessed}
    result=[];stats=[]
    for i,bounds in enumerate(BUCKETS):
        items=sorted((piece for piece in witnessed if bucket(piece)==i),key=lambda piece:(-scores[piece],len(piece),piece))
        result.extend(items[:per_bucket]);stats.append({'lengths':list(bounds),'eligible':len(items),'retained':min(len(items),per_bucket)})
    return sorted(result),stats


def select_sources(rows,groups,references):
    chosen={};selected={}
    for pid,keys in groups.items():
        key=min(keys,key=lambda k:(rows[k]['selections'],rows[k]['characters'],k!=references[pid],k))
        chosen[pid]=key;selected[pid]=rows[key]
    return chosen,selected


def objective(rows,arm):return compact.objective(rows,arm)


def pair_joins(graph,left,right):
    a=graph.occurrence(left);z=graph.occurrence(right);total=0
    for key in a.keys()&z.keys():
        starts=set(z[key]);total+=sum(at+len(left) in starts for at in a[key])
    return total


def optimize(texts,groups,references,initial,pool,capacity,arm,config=CONFIG):
    if arm not in ('selection','character-budget') or capacity not in (128,256):raise ValueError('unsupported arm')
    started=time.process_time();graph=compact.Graph(texts)
    vocab=ALPHABET+sorted(initial[96:]);rows=graph.score(vocab)
    choices,selected=select_sources(rows,groups,references)
    initial_objective=objective(selected,arm)
    ceiling=sum(rows[key]['selections'] for key in references.values())
    evaluations=0;trace=[];termination='round-cap'
    for round_index in range(config['rounds']):
        current=objective(selected,arm)
        usage=Counter(piece for row in selected.values() for piece in row['used'])
        removals=sorted(vocab[96:],key=lambda p:(usage[p],-len(p),p))[:config['single_removals']]
        def proposal_score(piece):
            values={}
            for key,starts in graph.occurrence(piece).items():
                pid=key.split(':',1)[0]
                gain=len(starts)*(len(piece)-1) if arm=='selection' else sum(sum(at<=position<at+len(piece) for position in rows[key]['character_positions']) for at in starts)
                values[pid]=max(values.get(pid,0),gain)
            return sum(values.values())
        score_cache={p:proposal_score(p) for p in pool if p not in vocab}
        by_bucket=[sorted((p for p in score_cache if bucket(p)==i),key=lambda p:(-score_cache[p],len(p),p))[:config['additions_per_bucket']] for i in range(len(BUCKETS))]
        additions=[items[j] for j in range(config['additions_per_bucket']) for items in by_bucket if j<len(items)]
        pairs=sorted(combinations(additions,2),key=lambda pair:(-(pair_joins(graph,*pair)+pair_joins(graph,*reversed(pair))),-sum(score_cache[p] for p in pair),pair))[:config['pair_proposals']]
        moves=[]
        # Interleave complementary pairs with singles so neither is starved by caps.
        singles=[((p,),tuple() if removed is None else (removed,)) for p in additions for removed in ([None] if len(vocab)<capacity else [])+removals]
        pair_moves=[]
        for pair in pairs:
            need=max(0,len(vocab)+2-capacity)
            remove_sets=[()] if need==0 else [(p,) for p in removals[:config['pair_removals']]] if need==1 else list(combinations(removals[:config['pair_removals']],2))
            pair_moves.extend((pair,removed) for removed in remove_sets)
        for i in range(max(len(singles),len(pair_moves))):
            if i<len(singles):moves.append(singles[i])
            if i<len(pair_moves):moves.append(pair_moves[i])
        best=None
        for additions_now,removed in moves:
            if evaluations>=config['evaluations']:break
            if time.process_time()-started>config['cpu_seconds']:raise TimeoutError('frozen arm CPU budget exhausted; no partial arm accepted')
            learned=(set(vocab[96:])-set(removed))|set(additions_now)
            candidate=ALPHABET+sorted(learned)
            if len(candidate)>capacity:continue
            candidate_rows=graph.score(candidate,rows,(*additions_now,*removed));evaluations+=1
            candidate_choices,candidate_selected=select_sources(candidate_rows,groups,references)
            score=objective(candidate_selected,arm)
            if score>=current or (arm=='character-budget' and sum(r['selections'] for r in candidate_selected.values())>ceiling):continue
            rank=(score,tuple(candidate),tuple(sorted(candidate_choices.items())))
            if best is None or rank<best[0]:best=(rank,candidate,candidate_rows,candidate_choices,candidate_selected,additions_now,removed)
        if best is not None:
            rank,vocab,rows,choices,selected,additions_now,removed=best
            for key,text in texts.items():
                expected=[vocab[i] for i in compare.scorer.shortest_encode(text,vocab)]
                if expected!=rows[key]['used']:raise AssertionError('joint cached DAG differs from canonical scorer')
            trace.append({'round':round_index,'before':current,'after':rank[0],'add':list(additions_now),'remove':list(removed),'adapted_choices':sum(choices[p]!=references[p] for p in choices)})
        if evaluations>=config['evaluations']:termination='evaluation-cap';break
        if best is None:termination='no-improving-proposed-move';break
    if time.process_time()-started>config['cpu_seconds']:raise TimeoutError('frozen arm CPU budget exhausted; no partial arm accepted')
    return vocab,choices,{'initial_objective':initial_objective,'final_objective':objective(selected,arm),'evaluations':evaluations,'trace':trace,'termination':termination,'cpu_seconds':time.process_time()-started,'reference_selection_ceiling':ceiling}


def pins():
    files=[HERE/'search.py',HERE/'FREEZE.md',HERE/'test_search.py',LIT/'compact-search-v1/search.py',PAIRED/'verify_baseline.py',PAIRED/'verify_adapted.py',PAIRED/'baseline_replay.py',PAIRED/'adapted_candidates.py',PAIRED/'qualify.py',LIT/'readable-joint-blocks-v1/compare.py',LIT/'readable-joint-blocks-v1/transfer.py',compare.CODEC_FILE,compare.SCORER_FILE]
    return {str(p.relative_to(LIT)):b.sha(p.read_bytes()) for p in files}


def pool_gate(root,baseline,adapted_reports):
    spec=compact.policy();compact.check_receipt(root,spec)
    baseline_proof=verify_baseline.verify(root,baseline,allow_failed=True)
    if baseline_proof['problems']!=400:raise ValueError('full400 baseline replay required')
    population={str(pid):[] for pid in spec['partition']['dev_fit']+spec['partition']['dev_val']}
    entries={r['id']:r for r in spec['files'] if r['kind']=='source'}
    for pid in baseline_proof['eligible_ids']:
        row=entries[pid];population[str(pid)].append({'label':'original','path':str(root/row['path']),'sha256':row['sha256'],'evidence':'baseline'})
    adapted_proofs=[]
    for path in adapted_reports:
        proof=verify_adapted.verify(root,path);adapted_proofs.append({'report':str(path),'report_sha256':proof['report_sha256'],'qualified':[r['id'] for r in proof['alternatives']]})
        for row in proof['alternatives']:
            if row['id'] not in spec['partition']['dev_fit']:raise ValueError('validation alternatives forbidden')
            pid=str(row['id'])
            if any(r['sha256']==row['adapted_sha256'] for r in population[pid]):continue
            population[pid].append({'label':'adapted-'+row['adapted_sha256'],'path':str(path.parent/row['path']),'sha256':row['adapted_sha256'],'bytes':row['complete_bytes'],'adapter_bytes':row['adapter_bytes'],'evidence':str(path)})
    absent=[pid for pid,rows in population.items() if not rows]
    if absent:raise ValueError('qualified source pool missing frozen IDs: '+','.join(absent))
    references={pid:min(rows,key=lambda row:(row['label']!='original',row.get('bytes',0),row['sha256']))['label'] for pid,rows in population.items()}
    return spec,population,references,baseline_proof,adapted_proofs


def freeze(root,baseline,adapted_reports,output):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private outputs must stay outside repository')
    spec,population,references,proof,adapted=pool_gate(root,baseline,adapted_reports)
    contract={'schema':'gamma.joint-composable.freeze.v1','code_sha256':pins(),'config':CONFIG,'partition':spec['partition'],'population':population,'references':references,'baseline_report':str(baseline),'baseline_report_sha256':proof['report_sha256'],'adapted_reports':adapted,'capacities':[128,256],'arms':['selection','character-budget'],'dictionary_inputs':[r for r in spec['files'] if r['kind']=='dictionary'],'m1_population':500,'permitted_development_population':400,'protected_access':False,'m1_qualified':False}
    output.mkdir(parents=True,exist_ok=False);b.write(output/'contract.json',contract);return contract


def read_sources(population,ids):
    texts={};groups={};owners={}
    for pid_int in ids:
        pid=str(pid_int);groups[pid]=[]
        for row in population[pid]:
            raw=Path(row['path']).read_bytes()
            if b.sha(raw)!=row['sha256']:raise ValueError('frozen source artifact changed')
            key=pid+':'+row['label'];texts[key]=raw.decode('utf-8');groups[pid].append(key);owners[key]=pid
    compare.validate_texts(texts)
    return texts,groups,owners


def measure_profile(texts,vocab,width):
    # measure performs two independent segmentations and independent packet decode.
    summary,artifacts=compare.measure(texts,vocab,width)
    return summary,artifacts


def run(root,frozen,output):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private outputs must stay outside repository')
    contract=json.loads((frozen/'contract.json').read_text())
    if contract['schema']!='gamma.joint-composable.freeze.v1' or contract['code_sha256']!=pins() or contract['config']!=CONFIG:raise ValueError('frozen code/policy drift')
    spec,population,references,proof,adapted=pool_gate(root,Path(contract['baseline_report']),[Path(r['report']) for r in contract['adapted_reports']])
    if population!=contract['population'] or references!=contract['references'] or proof['report_sha256']!=contract['baseline_report_sha256'] or adapted!=contract['adapted_reports'] or spec['partition']!=contract['partition']:raise ValueError('qualification/source pool drift after freeze')
    output.mkdir(parents=True,exist_ok=False);b.write(output/'contract.json',contract)
    report={'schema':'gamma.joint-composable.results.v1','status':'running','contract_sha256':b.sha(b.encoded(contract)),'m1_population':500,'scored_development_population':400,'unscored_final_heldout':100,'protected_access':False,'candidate_execution':False,'m1_qualified':False,'fits':{},'profiles':[]}
    try:
        fit_ids=spec['partition']['dev_fit'];val_ids=spec['partition']['dev_val']
        texts,groups,owners=read_sources(population,fit_ids)
        fit_references={str(pid):str(pid)+':'+references[str(pid)] for pid in fit_ids}
        forbidden=banned_strings(texts);pool,pool_stats=build_pool(texts,owners,forbidden,CONFIG['pool_per_bucket'])
        b.write(output/'pool.json',{'entries':pool,'buckets':pool_stats,'distinct_problem_support_required':2})
        initial={}
        for row in contract['dictionary_inputs']:
            initial[row['width']]=json.loads(compact.verified(root,row))
            if isinstance(initial[row['width']],dict):initial[row['width']]=initial[row['width']].get('literals',initial[row['width']].get('entries'))
            value=initial[row['width']]
            if type(value)is not list or value[:96]!=ALPHABET or len(set(value))!=len(value):raise ValueError('pinned initial dictionary shape mismatch')
            initial[row['width']]=ALPHABET+sorted(value[96:])
        sealed={}
        for capacity in contract['capacities']:
            vocab=initial[capacity]
            if vocab[:96]!=ALPHABET or len(vocab)>capacity or set(vocab)&forbidden:raise ValueError('initial dictionary violates alphabet/capacity/whole-solution policy')
            for arm in contract['arms']:
                name=f'{capacity}-{arm}'
                b.write(output/'progress.json',{'phase':'fit','active_arm':name,'completed_arms':list(sealed),'validation_measured':False})
                dictionary,choices,metrics=optimize(texts,groups,fit_references,vocab,pool,capacity,arm)
                all_choices={**choices,**{str(pid):str(pid)+':'+references[str(pid)] for pid in val_ids}}
                sealed[name]={'dictionary':dictionary,'choices':all_choices,'width':7 if capacity==128 else 8,'capacity':capacity}
                report['fits'][name]=metrics
                b.write(output/'progress.json',{'phase':'fit','completed_arms':list(sealed),'fits':report['fits'],'validation_measured':False})
        # This immutable seal precedes validation source loading and all measurements.
        seal_raw=b.encoded(sealed);(output/'sealed-arms.json').write_bytes(seal_raw);report['sealed_arms_sha256']=b.sha(seal_raw)
        validation,val_groups,val_owners=read_sources(population,val_ids)
        if any(len(keys)!=1 for keys in val_groups.values()):raise ValueError('validation source choice was not fixed')
        all_texts={**texts,**validation};all_forbidden=forbidden|banned_strings(validation)
        reference_texts={pid:all_texts[pid+':'+label] for pid,label in references.items()}
        for name,arm in sealed.items():
            if set(arm['dictionary'])&all_forbidden:raise ValueError('sealed dictionary contains complete validation solution/body')
            chosen_texts={pid:all_texts[key] for pid,key in arm['choices'].items()}
            profiles=[('reference-initial',reference_texts,initial[arm['capacity']]),('source-only',chosen_texts,initial[arm['capacity']]),('dictionary-only',reference_texts,arm['dictionary']),('joint',chosen_texts,arm['dictionary'])]
            for variant,selected,vocabulary in profiles:
                for partition,ids in [('dev_fit',fit_ids),('dev_val',val_ids),('all400',fit_ids+val_ids)]:
                    summary,artifacts=measure_profile({str(pid):selected[str(pid)] for pid in ids},vocabulary,arm['width'])
                    source_choices=arm['choices'] if variant in ('source-only','joint') else {pid:pid+':'+label for pid,label in references.items()}
                    descriptors={pid+':'+row['label']:row for pid,variants in population.items() for row in variants}
                    summary['adapter_source_bytes']=sum(descriptors[source_choices[str(pid)]].get('adapter_bytes',0) for pid in ids)
                    summary['all_helpers_and_adapters_included_in_source']=True
                    summary['uncharged_helper_bytes']=0
                    profile_name=f'{name}-{variant}-{partition}';directory=output/profile_name;directory.mkdir()
                    (directory/'dictionary.bin').write_bytes(artifacts['dictionary'])
                    for pid,packet in artifacts['packets'].items():(directory/(pid+'.packet')).write_bytes(packet)
                    b.write(directory/'measurement.json',summary)
                    report['profiles'].append({'id':profile_name,'arm':name,'variant':variant,'partition':partition,**{k:v for k,v in summary.items() if k!='per_problem'}})
        if contract['code_sha256']!=pins():raise ValueError('code changed during frozen experiment')
        report['reference_originals']=sum(label=='original' for label in references.values());report['reference_required_successors']=400-report['reference_originals'];report['status']='completed'
    except Exception as error:report['status']='failed';report['error']=type(error).__name__+': '+str(error)
    b.write(output/'results.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--inputs',type=Path,required=True);f.add_argument('--baseline',type=Path,required=True);f.add_argument('--adapted',type=Path,action='append',default=[]);f.add_argument('--output',type=Path,required=True)
    r=sub.add_parser('run');r.add_argument('--inputs',type=Path,required=True);r.add_argument('--freeze',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=freeze(a.inputs,a.baseline,a.adapted,a.output) if a.command=='freeze' else run(a.inputs,a.freeze,a.output)
    print(json.dumps({'status':result.get('status','frozen'),'m1_qualified':False}));raise SystemExit(0 if result.get('status','frozen')!='failed' else 2)
