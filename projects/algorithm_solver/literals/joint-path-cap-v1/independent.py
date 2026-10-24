"""Item60 supplied-input replay; no production60 or corpus loader dependency.

The unchanged57 independent checker supplies its complete baseline. A fresh AC
traversal below separately reconstructs original occurrence order, reversed-DAG
potentials and tightened local shared weights. Item33 Index/partition geometry
and accepted full-shared completeness are explicit shared dependencies, not a
new proof independent of those algorithms. Backward all-arc schedules and linear
owner scans differ from production's forward schedule and marginal heap.
"""
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location('joint60_independent_parent57',
    Path(__file__).resolve().parents[1]/'owner-path-cap-v1/independent.py')
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)

COMMON57 = ('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes',
    'capped_prefixes','one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
FIELDS53 = ('schema','lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')
COMMON = ('local_shared_top_entries','local_shared_prefixes','local_shared_counts',
          'all_caps','split_rows','rows','deltas_vs57')


def digest(value):
    def normalize(x):
        if isinstance(x, dict): return {str(k):normalize(v) for k,v in x.items()}
        if isinstance(x, (list,tuple)): return [normalize(v) for v in x]
        return x
    return hashlib.sha256(json.dumps(normalize(value),sort_keys=True,separators=(',',':'),
                                    ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def scientific57(value):
    return {key:value[key] for key in COMMON57} | {'base':{key:value['base'][key] for key in FIELDS53}}


class AC:
    """Fresh terminal-link matcher; emits ends in order, without output copying."""
    def __init__(self, words):
        self.words = words
        self.children, self.fail, self.hit, self.link = [{}], [0], [None], [None]
        for eid, word in enumerate(words):
            node = 0
            for ch in word:
                if ch not in self.children[node]:
                    self.children[node][ch] = len(self.children)
                    self.children.append({}); self.fail.append(0)
                    self.hit.append(None); self.link.append(None)
                node = self.children[node][ch]
            assert self.hit[node] is None
            self.hit[node] = eid
        queue = deque(self.children[0].values())
        while queue:
            node = queue.popleft()
            for ch, child in self.children[node].items():
                fallback = self.fail[node]
                while fallback and ch not in self.children[fallback]: fallback = self.fail[fallback]
                target = self.children[fallback].get(ch,0)
                self.fail[child] = target
                self.link[child] = target if self.hit[target] is not None else self.link[target]
                queue.append(child)

    def matches(self, text):
        node = 0
        for end, ch in enumerate(text,1):
            while node and ch not in self.children[node]: node = self.fail[node]
            node = self.children[node].get(ch,0)
            hit = node if self.hit[node] is not None else self.link[node]
            while hit is not None:
                eid = self.hit[hit]
                yield end-len(self.words[eid]),end,eid
                hit = self.link[hit]


def allocate(base57, local_prefixes, all_caps, B, D):
    """O(P B**2) scan allocation; reconstruct/check increments, no function cube."""
    if not __debug__: raise RuntimeError('independent replay requires assertions')
    assert type(B) is int and B >= 0 and type(D) is int and D > 0
    owners = base57['owner_prefixes']; ids = sorted(owners)
    assert local_prefixes.keys() == all_caps.keys() == owners.keys()
    for pid in ids:
        assert type(all_caps[pid]) is int and all_caps[pid] >= 0
        for prefix in (owners[pid],local_prefixes[pid]):
            assert type(prefix) is list and prefix and prefix[0] == 0
            assert all(type(v) is int and v >= 0 for v in prefix)
            changes = [b-a for a,b in zip(prefix,prefix[1:])]
            assert all(v>=0 for v in changes) and changes == sorted(changes,reverse=True)
    U, H = base57['one_owner_prefix'], base57['shared_prefix']
    assert len(U) == min(B,sum(len(v)-1 for v in owners.values()))+1
    counts = base57['base']['tightened']['class_counts']
    assert len(H) == min(B,counts[2])+1
    splits = []; comparisons = increment_checks = scans = 0
    for j in range(len(U)):
        s = B-j
        offsets = {pid:local_prefixes[pid][min(s,len(local_prefixes[pid])-1)] for pid in ids}
        baseline = sum(min(offsets[pid],all_caps[pid]) for pid in ids)
        for pid in ids:
            previous_value = min(offsets[pid],all_caps[pid]); previous_gain = None
            for raw in owners[pid][1:]:
                value = min(offsets[pid]+raw,all_caps[pid]); gain = value-previous_value
                assert gain >= 0 and (previous_gain is None or gain <= previous_gain)
                previous_value, previous_gain = value, gain
                increment_checks += 1
        assigned = dict.fromkeys(ids,0); choices = []; joint = baseline
        for _ in range(j):
            best = None
            for pid in ids:
                scans += 1
                rank = assigned[pid]+1
                if rank >= len(owners[pid]): continue
                gain = (min(offsets[pid]+owners[pid][rank],all_caps[pid]) -
                        min(offsets[pid]+owners[pid][rank-1],all_caps[pid]))
                candidate = (-gain,pid,rank); comparisons += 1
                if best is None or candidate < best: best = candidate
            assert best is not None
            negative,pid,rank = best
            assigned[pid] = rank; joint -= negative; choices.append((pid,rank,-negative))
        assert sum(assigned.values()) == j
        assert joint == sum(min(offsets[pid]+owners[pid][assigned[pid]],all_caps[pid]) for pid in ids)
        prior = H[min(s,len(H)-1)]+U[j]
        splits.append({'one_owner_slots':j,'shared_slots':s,'shared_slots_available':min(s,counts[2]),
                       'baseline':baseline,'joint_charge':joint,'prior57_charge':prior,'charge':min(joint,prior),
                       'allocation_choices':choices})
    L = sum(base57['base']['tightened']['path_numerators'].values())
    rows, deltas = [], []
    for k in range(B+1):
        selected = max(splits[:min(k,len(splits)-1)+1], key=lambda row:(row['charge'],-row['one_owner_slots']))
        charge = selected['charge']; numerator = L-charge
        lower,remainder = divmod(numerator,D)
        row = {'k':k,'charge':charge,'one_owner_slots':selected['one_owner_slots'],
               'shared_slots':selected['shared_slots_available'],'numerator':numerator,
               'integer_lower_bound':lower+int(remainder!=0)}
        old = base57['rows'][k]
        assert max(x['prior57_charge'] for x in splits[:min(k,len(splits)-1)+1]) == old['charge']
        assert charge <= old['charge'] and row['integer_lower_bound'] >= old['integer_lower_bound']
        rows.append(row)
        deltas.append({'k':k,'charge_reduction':old['charge']-charge,
                       'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
    assert all(a['charge']<=b['charge'] for a,b in zip(rows,rows[1:]))
    return splits,rows,deltas,{'allocation_owner_scans':scans,'allocation_candidates_compared':comparisons,
                              'allocation_increments_checked':increment_checks}


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,expected_occurrence_sha256=None,
          capacity=256,expected_base57_prefix_schedule=None,expected_prefix_schedule=None):
    if not __debug__: raise RuntimeError('independent replay requires assertions')
    base57 = parent.check(texts,banned,old_pool,old_q,seed,alphabet,D,
        expected_source_hashes=expected_source_hashes,expected_old_banned=expected_old_banned,
        expected_old_certificate=expected_old_certificate,expected_occurrence_sha256=expected_occurrence_sha256,
        capacity=capacity,expected_prefix_schedule=expected_base57_prefix_schedule)
    index = parent.full.Index(texts,set(banned))
    parent.full.verify(index,{pid:[0]*len(t) for pid,t in texts.items()},0,1)
    positions = index.positions
    ranks = {position:rank for rank,position in enumerate(positions)}
    groups = {(g['lo'],g['hi']):gid for gid,g in enumerate(index.groups)}
    assert len(groups) == len(index.groups)
    # A suffix interval is one-owner iff it ends inside this same-owner run.
    # Only the 1 / at-least-2 classification is needed, not distinct counts.
    run_end = [0]*len(positions)
    for rank in range(len(positions)-1,-1,-1):
        run_end[rank] = (run_end[rank+1] if rank+1<len(positions) and
                         positions[rank][0]==positions[rank+1][0] else rank+1)
    supports = [1 if g['hi']<=run_end[g['lo']] else 2 for g in index.groups]
    matcher = AC(old_pool)
    owners = [set() for _ in old_pool]
    occurrences = [0]*len(old_pool)
    lows, highs = [len(positions)]*len(old_pool), [-1]*len(old_pool)
    weights = [0]*len(old_pool)
    potentials = {}; cursor = 0; occurrence_hash = hashlib.sha256(); bellman = 0
    for pid,text in sorted(texts.items()):
        outgoing = [[] for _ in text]
        for start,end,eid in matcher.matches(text): outgoing[start].append((end,eid))
        incoming = [[] for _ in range(len(text)+1)]
        for start,matches in enumerate(outgoing):
            assert matches == sorted(matches)
            for end,eid in matches:
                assert cursor < len(old_q)
                q = old_q[cursor]; cursor += 1
                occurrence_hash.update((json.dumps([pid,start,end,eid],separators=(',',':'))+'\n').encode())
                incoming[end].append((start,(9 if end-start==1 else -1)*D+q))
                weights[eid] += q; owners[eid].add(pid); occurrences[eid] += 1
                rank = ranks[pid,start]; lows[eid]=min(lows[eid],rank); highs[eid]=max(highs[eid],rank)
        d = [None]*len(text)+[0]
        for end in range(len(text),0,-1):
            assert d[end] is not None
            for start,cost in incoming[end]:
                value = d[end]+cost
                if d[start] is None or value < d[start]: d[start]=value
        assert all(type(v) is int for v in d)
        for end,edges in enumerate(incoming):
            for start,cost in edges:
                assert d[start] <= d[end]+cost; bellman += 1
        assert d[0] == base57['base']['tightened']['path_numerators'][pid]
        potentials[pid] = d
    assert cursor == len(old_q) == base57['base']['tightened']['old_occurrences']
    assert occurrence_hash.hexdigest() == base57['base']['tightened']['occurrence_sha256']
    assert digest(potentials) == base57['base']['digests']['potentials_sha256']
    assert digest(weights) == base57['base']['digests']['old_weights_sha256']

    identities = {}; mapped_shared = dict.fromkeys(range(len(index.groups)),0)
    for eid,word in enumerate(old_pool):
        if not occurrences[eid]: continue
        assert highs[eid]-lows[eid]+1 == occurrences[eid]
        gid = groups[lows[eid],highs[eid]+1]; g=index.groups[gid]; length=len(word)
        assert g['first'] <= length <= g['last'] and length not in g['excluded_lengths']
        assert supports[gid] == min(2,len(owners[eid]))
        if len(owners[eid]) >= 2:
            assert (gid,length) not in identities
            identities[gid,length] = eid; mapped_shared[gid] += 1
    for gid,g in enumerate(index.groups):
        if supports[gid] >= 2: assert mapped_shared[gid] == g['multiplicity'], 'missing allowed shared identity'
    shared_ids = sorted(identities)
    mshared = len(shared_ids)
    assert mshared == base57['base']['tightened']['class_counts'][2]
    eid_identity = {eid:identity for identity,eid in identities.items()}
    local_tops, local_prefixes, local_counts = {}, {}, {}
    tightened_weights = [0]*len(old_pool); local_occurrences = 0
    for pid,text in sorted(texts.items()):
        local = {}; d = potentials[pid]
        for start,end,eid in matcher.matches(text):
            q53 = max(0,d[start]-d[end]-(9 if end-start==1 else -1)*D)
            tightened_weights[eid] += q53
            if eid in eid_identity:
                local[eid] = local.get(eid,0)+q53; local_occurrences += 1
        values = [(local.get(identities[identity],0),*identity) for identity in shared_ids]
        values.sort(key=lambda v:(-v[0],v[1],v[2]))
        chosen = values[:capacity]; local_tops[pid] = chosen
        prefix = [0]
        for weight,_,_ in chosen: prefix.append(prefix[-1]+weight)
        local_prefixes[pid] = prefix
        local_counts[pid] = {'available':mshared,'occurring':len(local),'positive':sum(v>0 for v in local.values())}
    assert digest(tightened_weights) == base57['base']['digests']['tightened_old_weights_sha256']
    global_shared = sorted(((tightened_weights[eid],*identity) for identity,eid in identities.items()),
                           key=lambda v:(-v[0],v[1],v[2]))[:capacity]
    assert global_shared == base57['base']['tightened']['top_entries'][2]
    shared_prefix = [0]
    for weight,_,_ in global_shared: shared_prefix.append(shared_prefix[-1]+weight)
    assert shared_prefix == base57['shared_prefix']

    bans = {pid:[set() for _ in text] for pid,text in texts.items()}
    banmatcher = AC(sorted(set(banned)))
    for pid,text in sorted(texts.items()):
        for start,end,_ in banmatcher.matches(text): bans[pid][start].add(end)
    assert bans == index.banned_ends
    schedules, caps = {}, {}; inspected = admitted = 0
    for pid,text in sorted(texts.items()):
        d = potentials[pid]; values = [0]*(len(text)+1)
        for start in range(len(text)-1,-1,-1):
            best = values[start+1]
            for end in range(start+1,len(text)+1):
                inspected += 1
                if end in bans[pid][start]: continue
                admitted += 1
                q53 = max(0,d[start]-d[end]-(9 if end-start==1 else -1)*D)
                best = max(best,q53+values[end])
            values[start] = best
        schedules[pid],caps[pid] = values,values[0]
        assert caps[pid] >= base57['owner_caps'][pid]
    checked_positions = checked_endpoints = 0
    if expected_prefix_schedule is not None:
        assert type(expected_prefix_schedule) is dict and expected_prefix_schedule.keys() == texts.keys()
        for pid,text in sorted(texts.items()):
            supplied = expected_prefix_schedule[pid]
            assert type(supplied) is list and len(supplied)==len(text)+1
            assert all(type(v) is int and v>=0 for v in supplied) and supplied[0]==0
            d = potentials[pid]
            for end in range(1,len(text)+1):
                best = supplied[end-1]
                for start in range(end):
                    checked_endpoints += 1
                    if end in bans[pid][start]: continue
                    q53 = max(0,d[start]-d[end]-(9 if end-start==1 else -1)*D)
                    best = max(best,supplied[start]+q53)
                assert supplied[end]==best,('all-arc forward recurrence',pid,end)
                checked_positions += 1
            assert supplied[-1]==caps[pid]
    splits,rows,deltas,allocation_work = allocate(base57,local_prefixes,caps,capacity,D)
    result = {'schema':'gamma.joint-path-cap.supplied.v1','base57':base57,
        'local_shared_top_entries':local_tops,'local_shared_prefixes':local_prefixes,'local_shared_counts':local_counts,
        'all_caps':caps,'all_suffix_schedule':schedules,'split_rows':splits,'rows':rows,'deltas_vs57':deltas,
        'work':{'old_occurrences_replayed':cursor,'old_bellman_edges_checked':bellman,
                'support_suffix_positions_checked':len(positions),'support_groups_classified':len(index.groups),
                'shared_occurrences_aggregated':local_occurrences,'shared_entries_reconciled':mshared,
                'local_shared_entries_sorted':len(texts)*mshared,'schedule_endpoints_inspected':inspected,
                'schedule_occurrences_admitted':admitted,'production_forward_positions_checked':checked_positions,
                'production_forward_endpoints_inspected':checked_endpoints,**allocation_work},
        'production_forward_schedule_checked':expected_prefix_schedule is not None,
        'production_forward_schedule_sha256':digest(expected_prefix_schedule) if expected_prefix_schedule is not None else None,
        'shared_dependency':'unchanged57 independent baseline; item33 Index and partition verifier/full-shared completeness',
        'scalar_replay':'fresh AC/order/q; reversed old DAG; full local sort; backward all-arc schedule; linear owner scan'}
    result['digests'] = {key+'_sha256':digest(result[key]) for key in (*COMMON,'all_suffix_schedule')}
    result['digests']['base57_sha256'] = digest(scientific57(base57))
    return result
