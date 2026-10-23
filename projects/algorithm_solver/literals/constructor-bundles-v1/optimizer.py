"""Bounded matched atomic search; exact item32 encoder and safe key-based cache."""
from collections import Counter, defaultdict
import importlib.util
import json
from itertools import combinations, zip_longest
from pathlib import Path
import time
import codec

_spec=importlib.util.spec_from_file_location('bundle_base_search',Path(__file__).resolve().parent.parent/'stacking-structured-v1/search.py')
base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(base)
Budget,evaluate=base.Budget,base.evaluate


def operands(text,node,kind):
    return [text[a:b] for a,b in node['holes']] if kind=='P' else node['args'][:]


def pool(texts,nodes,forbidden):
    constructors,literals,support=base.pool(texts,nodes,forbidden)
    allowed={k for ks in constructors.values() for k in ks}
    owners=defaultdict(set);scores=Counter();instances=[]
    for pid,text in texts.items():
        for kind,family in (('P','prefix'),('I','identifier')):
            for node in nodes[pid][family]:
                if node['key'] not in allowed:continue
                args=operands(text,node,kind)
                generated=sum(map(len,node['spec']['parts'])) if kind=='P' else node['free_bytes']
                instances.append({'pid':pid,'constructor':node['key'],'kind':kind,'operands':args,'generated_bytes':generated})
                for word in args:
                    if 2<=len(word)<=160 and word not in forbidden:
                        owners[word].add(pid);scores[word]+=len(word)-1
    operand_pool=sorted((w for w in owners if len(owners[w])>=2),key=lambda w:(-scores[w],len(w),w))[:256]
    return {'constructors':constructors,'literal_pool':literals,'support':support,
            'operand_pool':operand_pool,'operand_support':{w:len(owners[w]) for w in operand_pool},'instances':instances}


def constructor_bundles(state,pools):
    present=set(state['keys']);eligible=set(pools['operand_pool']);by_kind={'P':{},'I':{}}
    for row in pools['instances']:
        args=row['operands']
        if any(codec.literal(w) not in present and w not in eligible for w in args):continue
        additions=tuple(codec.order({row['constructor'],*map(codec.literal,args)}-present))
        if not additions or len(additions)>5:continue
        item=by_kind[row['kind']].setdefault(additions,{'additions':list(additions),'kind':row['kind'],
             'owners':set(),'generated_bytes':0,'constructors':set()})
        item['owners'].add(row['pid']);item['generated_bytes']+=row['generated_bytes'];item['constructors'].add(row['constructor'])
    ranked={kind:sorted(rows.values(),key=lambda r:(-len(r['owners']),-r['generated_bytes'],tuple(r['additions'])))[:12]
            for kind,rows in by_kind.items()}
    out=[]
    for pair in zip_longest(ranked['P'],ranked['I']):
        for r in pair:
            if r is not None:out.append({**r,'owners':sorted(r['owners'],key=int),'constructors':sorted(r['constructors'])})
    return out


def streams(texts,state,pools,forbidden,arm):
    present=set(state['keys'])
    literals=base.proposals(texts,state,pools['literal_pool'],[],forbidden)
    literals += [codec.literal(w) for w in pools['operand_pool'] if codec.literal(w) not in present and codec.literal(w) not in literals][:24]
    bundles=constructor_bundles(state,pools)
    packs=[];seen=set()
    for row in bundles:
        keys=tuple(k for k in row['additions'] if k[0]=='L')
        if len(keys)>=2 and keys not in seen:seen.add(keys);packs.append(list(keys))
    literal_bundles=[];seen=set()
    for size in range(2,6):
        for start in range(min(8,max(0,len(literals)-size+1))):
            keys=tuple(codec.order(literals[start:start+size]))
            if keys not in seen:seen.add(keys);literal_bundles.append(list(keys))
    for pack in packs:
        keys=tuple(codec.order(pack))
        if keys not in seen:seen.add(keys);literal_bundles.append(list(keys))
    typed=arm in ('T1','TB');atomic=arm in ('LB','TB')
    constructors=[]
    for pair in zip_longest(pools['constructors']['P'],pools['constructors']['I']):
        constructors += [k for k in pair if k is not None and k not in present]
    groups=[('literal_single', [{'additions':[k]} for k in literals]),
            ('literal_bundle',[{'additions':ks} for ks in literal_bundles] if atomic else []),
            ('constructor_single',[{'additions':[k]} for k in constructors] if typed else []),
            ('constructor_bundle',bundles if arm=='TB' else [])]
    for index in range(max(map(lambda pair:len(pair[1]),groups),default=0)):
        for kind,rows in groups:
            if index<len(rows):yield {'stream':kind,**rows[index]}


def removal_sets(keys,additions,loss):
    need=max(0,len(keys)+len(additions)-256)
    if not need:return [()]
    ranked=sorted(loss,key=lambda k:(loss[k],k))[:12]
    candidates=list(combinations(ranked,need))
    candidates.sort(key=lambda ks:(sum(loss[k] for k in ks),tuple(sorted(ks))))
    return [tuple(sorted(ks)) for ks in candidates[:12]]


def cost(state,typed):
    db=codec.dictionary(state['keys']) if typed else codec.literal_dictionary(state['keys'])
    return state['selections'],len(db)+41*len(state['rows'])+state['selections'],tuple(state['keys'])


def uses(state):
    return sum(row['constructor_codes'] for row in state['rows'].values())


def used_operand_literals(state):
    answer=set()
    for row in state['rows'].values():
        tokens=row['tokens'];pos=0
        def consume(argument=False):
            nonlocal pos
            key=tokens[pos];pos+=1
            if key[0]=='L':
                if argument:answer.add(key)
                return
            spec=json.loads(key[1:]);arity=len(spec['paths']) if key[0]=='P' else spec['arity']
            for _ in range(arity):consume(True)
        while pos<len(tokens):consume()
    return answer


def optimize(texts,nodes,initial,pools,forbidden,limits,arm,checkpoint=None):
    budget=Budget(limits['trials'],limits['seconds']);state=evaluate(texts,nodes,initial,budget)
    initial_trial_seconds=time.monotonic()-budget.start
    if state is None:raise ValueError('initial D11 dictionary lacks coverage')
    if checkpoint:checkpoint(state,[],budget.trials)
    mandatory={k for k in initial if k[0]=='L' and len(k)==2}
    log=[];round_no=0;stop='bounded_neighborhood_no_improvement';typed=arm in ('T1','TB')
    counts=Counter();accepted=[]
    while not budget.expired():
        best=None;tested=set();round_start=len(log);loss={}
        def trial(additions,removals,kind,proposal=None):
            nonlocal best
            keys=codec.order((set(state['keys'])-set(removals))|set(additions));signature=tuple(keys)
            if signature in tested:return None
            if budget.expired():return None
            assert mandatory<=set(keys) and len(keys)<=256 and not set(additions)&set(removals)
            assert not any(k[0]=='L' and k[1:] in forbidden for k in keys)
            trial_started=time.monotonic()
            got=evaluate(texts,nodes,keys,budget,state);counts[kind]+=1;tested.add(signature)
            trial_seconds=time.monotonic()-trial_started
            row={'trial':budget.trials,'round':round_no,'kind':kind,'additions':codec.order(additions),
                 'removals':codec.order(removals),'coverage':got is not None,'trial_seconds':trial_seconds,
                 'selections':None if got is None else got['selections'],
                 'package_bytes':None if got is None else cost(got,typed)[1]}
            if proposal and kind=='constructor_bundle':row['target_constructors']=proposal['constructors']
            log.append(row)
            if got is not None and got['selections']<state['selections']:
                score=cost(got,typed)
                if best is None or score<best[0]:best=(score,got,row)
            return got
        for key in state['keys']:
            if key in mandatory:continue
            if budget.expired():break
            got=trial([], [key], 'remove')
            loss[key]=float('inf') if got is None else got['selections']-state['selections']
        if not budget.expired():
            for proposal in streams(texts,state,pools,forbidden,arm):
                if budget.expired():break
                additions=proposal['additions']
                for removals in removal_sets(state['keys'],additions,loss):
                    if budget.expired():break
                    trial(additions,removals,proposal['stream'],proposal)
        if best is None:
            stop=budget.stop() if budget.expired() else 'bounded_neighborhood_no_improvement';break
        winner=best[2];addition_set=set(winner['additions'])
        singles=[r['trial'] for r in log[round_start:] if 'trial' in r and len(r['additions'])==1 and set(r['additions'])<addition_set]
        new=best[1]
        admission={'accepted_round':round_no+1,'accepted_trial':winner['trial'],'before_selections':state['selections'],
                   'selections':new['selections'],'dictionary':new['keys'],'kind':winner['kind'],
                   'additions':winner['additions'],'removals':winner['removals'],
                   'constructor_uses_before':uses(state),'constructor_uses_after':uses(new),
                   'proper_singleton_trials':singles,'untested_subsets':'unknown',
                   'singleton_removals_may_differ':True,
                   'missing_operand_literals':codec.order(set(winner['additions']) & used_operand_literals(new))}
        log.append(admission);accepted.append(admission);state=new;round_no+=1
        if checkpoint:checkpoint(state,log,budget.trials)
    else:stop=budget.stop()
    return state,{'trials':budget.trials,'seconds':time.monotonic()-budget.start,'stop':stop,'rounds':round_no,
                  'coverage_failures':budget.coverage_failures,'trial_composition':dict(counts),'trace':log,
                  'initial_trial_seconds':initial_trial_seconds,'search_seconds_budget':limits['seconds'],'deadline_check':'between_exact_dictionary_trials',
                  'budget_overrun_seconds':max(0,time.monotonic()-budget.start-limits['seconds']),
                  'longest_recorded_trial_seconds':max([initial_trial_seconds]+[r['trial_seconds'] for r in log if 'trial' in r]),
                  'accepted_atomic_moves':sum(len(r['additions'])>1 for r in accepted),
                  'accepted_operand_installations':sum(bool(r['missing_operand_literals']) for r in accepted)}
