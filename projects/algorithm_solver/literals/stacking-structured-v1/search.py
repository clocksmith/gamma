"""Matched bounded dictionary search over the same literal/P/I fit pools."""
from collections import Counter,defaultdict
import time
import codec


class Budget:
    def __init__(self, trials, seconds):
        self.cap, self.seconds = trials, seconds
        self.trials = self.coverage_failures = 0
        self.start = time.monotonic()
    def expired(self):
        return self.trials >= self.cap or time.monotonic()-self.start >= self.seconds
    def stop(self):
        return 'trial_limit' if self.trials >= self.cap else 'time_limit'


def pool(texts, nodes, forbidden):
    support = defaultdict(set)
    scores = Counter()
    literal_owners = defaultdict(set)
    literal_scores = Counter()
    for pid,text in texts.items():
        for family in ('prefix','identifier'):
            for n in nodes[str(pid)][family]:
                piece = text[n['start']:n['end']]
                maximum = 64 if family == 'prefix' else 160
                if 2 <= len(piece) <= maximum and piece not in forbidden:
                    literal_owners[piece].add(pid)
                    literal_scores[piece] += len(piece)-1
                if n['key']:
                    support[n['key']].add(pid)
                    scores[n['key']] += (sum(len(x) for x in n['spec']['parts'])-1
                                           if family == 'prefix' else n['free_bytes']-1)
    constructors = {}
    for kind, cap in (('P',32),('I',64)):
        constructors[kind] = sorted((key for key in support if key[0] == kind and len(support[key]) >= 2),
                                    key=lambda key:(-scores[key],key))[:cap]
    literals = sorted((word for word in literal_owners if len(literal_owners[word]) >= 2),
                      key=lambda word:(-literal_scores[word],len(word),word))[:256]
    return constructors, literals, {key:len(support[key]) for keys in constructors.values() for key in keys}


def evaluate(texts,nodes,keys,budget,parent=None):
    budget.trials += 1
    keys = codec.order(keys)
    if not 1 <= len(keys) <= 256:
        raise ValueError('joint dictionary capacity')
    delta = set(keys)^set(parent['keys']) if parent else None
    rows = {}
    try:
        for pid,text in texts.items():
            changed = parent is None or any((k[0]=='L' and k[1:] in text) or
                (k[0] in ('P','I') and any(n['key']==k for family in ('prefix','identifier')
                                          for n in nodes[str(pid)][family])) for k in delta)
            rows[pid] = codec.encode_source(text,nodes[str(pid)],keys) if changed else parent['rows'][pid]
    except ValueError:
        budget.coverage_failures += 1
        return None
    return {'keys':keys,'rows':rows,'selections':sum(row['selections'] for row in rows.values())}


def proposals(texts,state,literal_pool,constructors,forbidden):
    counts, owners = Counter(), defaultdict(set)
    for pid,row in state['rows'].items():
        spans = row['literal_spans']
        for i,(start,end,_) in enumerate(spans):
            stop = end
            for j in range(i+1,min(i+6,len(spans))):
                left,right,_ = spans[j]
                if left != stop:
                    break
                stop = right
                word = texts[pid][start:stop]
                if len(word) > 160:
                    break
                if word not in forbidden:
                    counts[word] += j-i
                    owners[word].add(pid)
    present = set(state['keys'])
    ranked = sorted((word for word in counts if len(owners[word]) >= 2 and codec.literal(word) not in present),
                    key=lambda word:(-counts[word],len(word),word))[:24]
    extra = [word for word in literal_pool if codec.literal(word) not in present and word not in ranked][:24]
    return [codec.literal(word) for word in ranked+extra]+[key for key in constructors if key not in present]


def optimize(texts,nodes,initial,constructors,literal_pool,forbidden,limits,typed):
    budget = Budget(limits['trials'],limits['seconds'])
    state = evaluate(texts,nodes,initial,budget)
    if state is None:
        raise ValueError('initial D11 fit dictionary lacks coverage')
    # Preserve exactly the seed character subset, not an assumed 96-entry fallback.
    mandatory = {key for key in initial if key.startswith('L') and len(key[1:]) == 1}
    log, round_no, stop = [], 0, 'local_optimum'
    while not budget.expired():
        candidates = proposals(texts,state,literal_pool,constructors,forbidden)
        removable = [key for key in state['keys'] if key not in mandatory]
        loss, best, tested = [], None, set()
        def trial(keys,kind,addition=None,removal=None):
            nonlocal best
            keys = codec.order(keys)
            signature = tuple(keys)
            if budget.expired() or signature in tested or len(keys) > 256 or not mandatory <= set(keys):
                return None
            tested.add(signature)
            got = evaluate(texts,nodes,keys,budget,state)
            log.append({'round':round_no,'kind':kind,'addition':addition,'removal':removal,
                        'selections':None if got is None else got['selections'],'coverage':got is not None})
            if got is None:
                return None
            db = codec.dictionary(keys) if typed else codec.literal_dictionary(keys)
            package = len(db)+sum(41+row['selections'] for row in got['rows'].values())
            score = (got['selections'],package,signature)
            if got['selections'] < state['selections'] and (best is None or score < best[0]):
                best = score,got
            return got
        for key in removable:
            got = trial(set(state['keys'])-{key},'remove',removal=key)
            loss.append((10**12 if got is None else got['selections']-state['selections'],key))
        # Infeasible deletion-only entries remain eligible, but the bounded
        # twelve-entry removal shortlist may screen them out.
        removals = [key for _,key in sorted(loss)[:12]]
        for key in candidates:
            if len(state['keys']) < 256:
                trial(set(state['keys'])|{key},'add',addition=key)
            for remove in removals:
                trial((set(state['keys'])-{remove})|{key},'swap',addition=key,removal=remove)
        if best is None:
            stop = budget.stop() if budget.expired() else 'local_optimum'
            break
        state = best[1]
        round_no += 1
        log.append({'accepted_round':round_no,'selections':state['selections'],'dictionary':state['keys']})
    else:
        stop = budget.stop()
    return state, {'trials':budget.trials,'seconds':time.monotonic()-budget.start,'stop':stop,
                   'rounds':round_no,'coverage_failures':budget.coverage_failures,'trace':log}
