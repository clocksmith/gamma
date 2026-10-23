"""Bounded exact-cost selection over literal entries and short expression constructors."""
from collections import Counter,defaultdict
import time
import codec


class Budget:
    def __init__(self,trials,seconds):self.cap=trials;self.seconds=seconds;self.trials=0;self.start=time.monotonic()
    def expired(self):return self.trials>=self.cap or time.monotonic()-self.start>=self.seconds
    def stop(self):return 'trial_limit' if self.trials>=self.cap else 'time_limit'


def pool(texts,nodes,forbidden):
    owners=defaultdict(set);counts=Counter();specs={}
    expr_owners=defaultdict(set);expr_counts=Counter()
    for pid,text in texts.items():
        for n in nodes[str(pid)]:
            piece=text[n['start']:n['end']]
            if 2<=len(piece)<=64 and piece not in forbidden:
                expr_owners[piece].add(pid);expr_counts[piece]+=1
            if n['key']:
                owners[n['key']].add(pid);counts[n['key']]+=1;specs[n['key']]=n['spec']
    constructors=sorted((k for k in owners if len(owners[k])>=2),key=lambda k:(-counts[k]*(sum(len(x) for x in specs[k]['parts'])-1),k))[:32]
    literals=sorted((x for x in expr_owners if len(expr_owners[x])>=2),key=lambda x:(-expr_counts[x]*(len(x)-1),len(x),x))[:256]
    return constructors,literals,{k:len(owners[k]) for k in constructors}


def evaluate(texts,nodes,keys,budget,parent=None):
    budget.trials+=1;keys=codec.order(keys);delta=set(keys)^set(parent['keys']) if parent else None;rows={}
    for pid,text in texts.items():
        if parent and not any((k[0]=='L' and k[1:] in text) or (k[0]=='C' and any(n['key']==k for n in nodes[str(pid)])) for k in delta):
            rows[pid]=parent['rows'][pid]
        else:rows[pid]=codec.encode_source(text,nodes[str(pid)],keys)
    return {'keys':keys,'rows':rows,'selections':sum(r['selections'] for r in rows.values())}


def proposals(texts,state,expr_pool,constructors,forbidden):
    counts=Counter();owners=defaultdict(set)
    for pid,row in state['rows'].items():
        spans=row['literal_spans']
        for i,(start,end,key) in enumerate(spans):
            stop=end
            for j in range(i+1,min(i+6,len(spans))):
                s,e,_=spans[j]
                if s!=stop:break
                stop=e;piece=texts[pid][start:stop]
                if len(piece)>64:break
                if piece not in forbidden:
                    counts[piece]+=j-i;owners[piece].add(pid)
    present=set(state['keys'])
    ranked=sorted((x for x in counts if len(owners[x])>=2 and codec.literal(x) not in present),key=lambda x:(-counts[x],len(x),x))[:24]
    expr=[x for x in expr_pool if codec.literal(x) not in present and x not in ranked][:24]
    return [codec.literal(x) for x in ranked+expr]+[k for k in constructors if k not in present]


def optimize(texts,nodes,initial,width,constructors,expr_pool,forbidden,limits,typed=True):
    budget=Budget(limits['trials'],limits['seconds']);state=evaluate(texts,nodes,initial,budget)
    mandatory={codec.literal(s) for s in codec.ALPHABET};log=[];round_no=0
    while not budget.expired():
        candidates=proposals(texts,state,expr_pool,constructors,forbidden)
        removable=[k for k in state['keys'] if k not in mandatory];loss=[];best=None
        tested=set()
        def trial(keys,kind,addition=None,removal=None):
            nonlocal best
            keys=codec.order(keys);signature=tuple(keys)
            if budget.expired() or signature in tested:return None
            tested.add(signature);got=evaluate(texts,nodes,keys,budget,state)
            log.append({'round':round_no,'kind':kind,'addition':addition,'removal':removal,'selections':got['selections']})
            db=codec.dictionary(keys) if typed else codec.literal_dictionary(keys)
            package=len(db)+sum(41+(r['selections']*width+7)//8 for r in got['rows'].values())
            score=(got['selections'],package,signature)
            if got['selections']<state['selections'] and (best is None or score<best[0]):best=(score,got)
            return got
        for key in removable:
            got=trial(set(state['keys'])-{key},'remove',removal=key)
            if got is not None:loss.append((got['selections']-state['selections'],key))
        removals=[key for _,key in sorted(loss)[:12]]
        for key in candidates:
            if len(state['keys'])<2**width:trial(set(state['keys'])|{key},'add',addition=key)
            for remove in removals:trial((set(state['keys'])-{remove})|{key},'swap',addition=key,removal=remove)
        if best is None:
            stop=budget.stop() if budget.expired() else 'local_optimum';break
        state=best[1];round_no+=1
        log.append({'accepted_round':round_no,'selections':state['selections'],'dictionary':state['keys']})
    else:stop=budget.stop()
    return state,{'trials':budget.trials,'stop':stop,'seconds':time.monotonic()-budget.start,'rounds':round_no,'trace':log}
