"""Item66 checker: shared AC global counts, owner Z, all-entry path prices.

No production66 import, loader, optimizer or file output. Shares unchanged57
independent baseline and33 Index/verifier; separately reconstructs old q/d and
AC ownership. Shared denominators use fresh global AC totals; owner counts use Z.
"""
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
_spec=importlib.util.spec_from_file_location('global66_independent_parent57',Path(__file__).resolve().parents[1]/'owner-path-cap-v1/independent.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)
BASE57_FIELDS=('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
    'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
BASE53_FIELDS=('schema','lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')
COMMON_FIELDS=('lambda_family','shared_counts','count_streams','price_caps','unpriced_caps',
    'price_rows','selected_price_index','global_charge','rows','deltas_vs57')


def normalized(value):
    if type(value) is dict:
        assert all(type(k) in (str,int) for k in value)
        out={str(k):normalized(v) for k,v in value.items()};assert len(out)==len(value);return out
    if type(value) in (tuple,list):return [normalized(v) for v in value]
    assert type(value) in (str,int,bool,type(None));return value


def digest(value):
    return hashlib.sha256(json.dumps(normalized(value),sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def scientific57(value):
    return {key:value[key] for key in BASE57_FIELDS}|{'base':{key:value['base'][key] for key in BASE53_FIELDS}}


def scientific(value):
    return {'schema':value['schema'],'base57':scientific57(value['base57']),**{key:value[key] for key in COMMON_FIELDS}}


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


def check(texts,banned,old_pool,old_q,seed,alphabet,D,*,expected_source_hashes,
          expected_old_banned,expected_old_certificate=None,expected_occurrence_sha256=None,
          capacity=256,expected_base57_prefix_schedule=None,expected_price_prefix_schedule=None,
          expected_count_streams=None,expected_price_caps=None,expected_shared_counts=None,
          expected_price_rows=None,expected_unpriced_prefix_schedule=None):
    if not __debug__:raise RuntimeError('normal assertions required')
    same_bans=banned is expected_old_banned
    banned=set(banned)
    expected_old_banned=banned if same_bans else set(expected_old_banned)
    base57=parent.check(texts,banned,old_pool,old_q,seed,alphabet,D,
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
    # Complete shared catalogue has unique(group,length) identities and the
    # exact count at EVERY shared compressed group, not just a pool label.
    shared_eids=[eid for eid in range(len(old_pool)) if len(owners[eid])>=2]
    shared_words=[old_pool[eid] for eid in shared_eids]
    shared_matcher=AC(shared_words);shared_totals=[0]*len(shared_words)
    shared_owners=[set() for _ in shared_words];shared_ac_occurrences=0
    for pid,text in sorted(texts.items()):
        for start,end,sid in shared_matcher.matches(text):
            shared_totals[sid]+=1;shared_owners[sid].add(pid);shared_ac_occurrences+=1
    for sid,eid in enumerate(shared_eids):
        assert shared_totals[sid]==occurrences[eid]>0
        assert shared_owners[sid]==owners[eid] and len(shared_owners[sid])>=2
    shared_counts=[[eid,shared_totals[sid]] for sid,eid in enumerate(shared_eids)]
    assert len(shared_counts)==sum(g['multiplicity'] for gid,g in enumerate(index.groups) if supports[gid]==2)
    prices=[0]+[D*2**r for r in range(14)];K=len(prices)
    assert K==15 and prices==sorted(set(prices))
    if expected_price_prefix_schedule is not None:
        assert type(expected_price_prefix_schedule) is dict and expected_price_prefix_schedule.keys()==texts.keys()
        for pid,text in texts.items():
            vectors=expected_price_prefix_schedule[pid]
            assert type(vectors) is list and len(vectors)==K
            for vector in vectors:
                assert type(vector) is list and len(vector)==len(text)+1 and vector[0]==0
                assert all(type(v) is int and v>=0 for v in vector)
    if expected_unpriced_prefix_schedule is not None:
        assert type(expected_unpriced_prefix_schedule) is dict and expected_unpriced_prefix_schedule.keys()==texts.keys()
        for pid,text in texts.items():
            vector=expected_unpriced_prefix_schedule[pid]
            assert type(vector) is list and len(vector)==len(text)+1 and vector[0]==0
            assert all(type(v) is int and v>=0 for v in vector)
    count_streams={};price_caps={};suffixes={};unpriced_caps={};unpriced_suffixes={}
    z_symbols=z_comparisons=z_histogram_cells=0
    ac_replayed=old_owned_checked=endpoints=banned_skips=shared_admitted=owner_admitted=0
    backward_candidates=forward_candidates=forward_positions=0
    unpriced_candidates=unpriced_forward_candidates=unpriced_forward_positions=0
    trie_transitions=trie_hits=0;shared_arc_counts=[0]*len(shared_words)
    ban_matcher=AC(sorted(banned));banned_occurrences=0
    for pid,text in sorted(texts.items()):
        n=len(text);codes=list(map(ord,text));shared_depth=[0]*n;old_owned=[{} for _ in text]
        for start,end,eid in matcher.matches(text):
            ac_replayed+=1
            if len(owners[eid])>=2:shared_depth[start]=max(shared_depth[start],end-start)
            else:
                assert owners[eid]=={pid};old_owned[start][end]=eid
        bans=[set() for _ in text]
        for start,end,_ in ban_matcher.matches(text):bans[start].add(end);banned_occurrences+=1
        assert bans==index.banned_ends[pid]
        backward=[[0]*(n+1) for _ in prices];unpriced=[0]*(n+1)
        if expected_price_prefix_schedule is not None:
            supplied=expected_price_prefix_schedule[pid];audit=[[0]+vector[:-1] for vector in supplied]
        if expected_unpriced_prefix_schedule is not None:
            supplied_unpriced=expected_unpriced_prefix_schedule[pid];audit_unpriced=[0]+supplied_unpriced[:-1]
        streams=[None]*n;d=potentials[pid]
        for start in range(n-1,-1,-1):
            multiplicities,work=z_counts(codes,start)
            z_symbols+=work['symbols'];z_comparisons+=work['comparisons'];z_histogram_cells+=work['histogram_cells']
            stream=hashlib.sha256();arcs=0;node=0
            for a in range(K):backward[a][start]=backward[a][start+1]
            unpriced[start]=unpriced[start+1]
            for end in range(start+1,n+1):
                endpoints+=1;length=end-start;sid=None
                # Exact prefix lookup follows ordinary trie edges only. Once
                # dead, every longer prefix is absent; no dense arc map exists.
                if node is not None:
                    trie_transitions+=1;node=shared_matcher.children[node].get(text[end-1])
                    if node is not None:sid=shared_matcher.hit[node]
                if end in bans[start]:
                    assert sid is None
                    banned_skips+=1;continue
                assert (sid is not None)==(length<=shared_depth[start]),'shared catalogue partition'
                if sid is not None:
                    count=shared_totals[sid];shared_admitted+=1;trie_hits+=1;shared_arc_counts[sid]+=1
                    assert type(count) is int and count>=2
                else:
                    count=multiplicities[length];owner_admitted+=1
                    assert type(count) is int and 1<=count<=n
                    if end in old_owned[start]:
                        eid=old_owned[start][end];assert count==occurrences[eid];old_owned_checked+=1
                stream.update((json.dumps([end,count],separators=(',',':'))+'\n').encode('ascii'));arcs+=1
                penalty=max(0,d[start]-d[end]-(9 if length==1 else -1)*D)
                unpriced[start]=max(unpriced[start],penalty+unpriced[end]);unpriced_candidates+=1
                if expected_unpriced_prefix_schedule is not None:
                    audit_unpriced[end]=max(audit_unpriced[end],supplied_unpriced[start]+penalty)
                    unpriced_forward_candidates+=1
                for a,price in enumerate(prices):
                    residual=max(0,penalty-price//count)
                    backward[a][start]=max(backward[a][start],residual+backward[a][end]);backward_candidates+=1
                    if expected_price_prefix_schedule is not None:
                        audit[a][end]=max(audit[a][end],supplied[a][start]+residual);forward_candidates+=1
            streams[start]={'arcs':arcs,'sha256':stream.hexdigest()}
        caps=[vector[0] for vector in backward]
        assert backward[0]==unpriced and caps[0]==unpriced[0]
        if expected_price_prefix_schedule is not None:
            for a in range(K):
                assert audit[a]==supplied[a],('price forward recurrence',pid,a)
                assert supplied[a][-1]==caps[a];forward_positions+=n
        if expected_unpriced_prefix_schedule is not None:
            assert audit_unpriced==supplied_unpriced,('unpriced forward recurrence',pid)
            assert supplied_unpriced[-1]==unpriced[0];unpriced_forward_positions+=n
            if expected_price_prefix_schedule is not None:assert supplied_unpriced==supplied[0]
        count_streams[pid]=streams;price_caps[pid]=caps;suffixes[pid]=backward
        unpriced_caps[pid]=unpriced[0];unpriced_suffixes[pid]=unpriced
    assert ac_replayed==cursor
    assert old_owned_checked==sum(occurrences[eid] for eid in range(len(old_pool)) if len(owners[eid])==1)
    expected_owner=sum((g['hi']-g['lo'])*g['multiplicity'] for gid,g in enumerate(index.groups) if supports[gid]==1)
    expected_shared=sum((g['hi']-g['lo'])*g['multiplicity'] for gid,g in enumerate(index.groups) if supports[gid]==2)
    assert owner_admitted==expected_owner and shared_admitted==expected_shared==shared_ac_occurrences
    assert shared_arc_counts==shared_totals and trie_hits==shared_admitted
    admitted=owner_admitted+shared_admitted
    assert endpoints==sum(len(t)*(len(t)+1)//2 for t in texts.values())
    assert banned_skips==sum(len(ends) for rows in index.banned_ends.values() for ends in rows)
    assert endpoints==admitted+banned_skips
    if expected_count_streams is not None:
        assert normalized(expected_count_streams)==count_streams and digest(expected_count_streams)==digest(count_streams)
    if expected_shared_counts is not None:
        assert normalized(expected_shared_counts)==shared_counts and digest(expected_shared_counts)==digest(shared_counts)
    if expected_price_caps is not None:
        assert type(expected_price_caps) is dict and expected_price_caps.keys()==price_caps.keys()
        for values in expected_price_caps.values():assert type(values) is list and all(type(v) is int for v in values)
        assert expected_price_caps==price_caps
    combined=combine(base57,prices,price_caps,capacity,D)
    if expected_price_rows is not None:
        assert normalized(expected_price_rows)==combined['price_rows'] and digest(expected_price_rows)==digest(combined['price_rows'])
    result={'schema':'gamma.global-entry-price-cap.supplied.v1','base57':base57,'lambda_family':prices,
        'shared_counts':shared_counts,'count_streams':count_streams,'price_caps':price_caps,
        'price_suffix_schedule':suffixes,'unpriced_caps':unpriced_caps,'unpriced_suffix_schedule':unpriced_suffixes,**combined,
        'production_forward_schedule_checked':expected_price_prefix_schedule is not None,
        'production_forward_schedule_sha256':digest(expected_price_prefix_schedule) if expected_price_prefix_schedule is not None else None,
        'production_unpriced_forward_checked':expected_unpriced_prefix_schedule is not None,
        'production_unpriced_forward_sha256':digest(expected_unpriced_prefix_schedule) if expected_unpriced_prefix_schedule is not None else None,
        'work':{'baseline57_reconstructions':1,'additional_old_contexts':1,'old_occurrences_replayed':cursor,
            'old_bellman_edges_checked':bellman,'support_suffix_positions_checked':len(positions),'support_groups_classified':len(index.groups),
            'shared_catalogue_entries':len(shared_counts),'shared_catalogue_ac_occurrences':shared_ac_occurrences,
            'shared_catalogue_trie_nodes':len(shared_matcher.children),'shared_trie_transitions':trie_transitions,
            'shared_terminal_hits':trie_hits,'old_occurrences_reclassified':ac_replayed,'old_owned_occurrence_counts_checked':old_owned_checked,
            'banned_occurrences_matched':banned_occurrences,'z_input_symbols':z_symbols,'z_character_comparisons':z_comparisons,
            'z_histogram_cells':z_histogram_cells,'endpoints_inspected':endpoints,'banned_endpoints_skipped':banned_skips,
            'shared_occurrences':shared_admitted,'one_owner_occurrences':owner_admitted,'count_records':admitted,
            'q_evaluations':admitted,'price_residual_evaluations':K*admitted,'multiplicity_divisions':K*admitted,
            'backward_candidates':backward_candidates,'production_forward_candidates':forward_candidates,
            'production_forward_positions_checked':forward_positions,'unpriced_backward_candidates':unpriced_candidates,
            'unpriced_production_forward_candidates':unpriced_forward_candidates,
            'unpriced_production_forward_positions_checked':unpriced_forward_positions},
        'shared_dependency':'Unchanged57 independent baseline and33 Index/partition verifier; additional AC old q/d/support reconstruction.',
        'scalar_replay':'Fresh shared-catalogue AC global totals, root-trie lookup and numeric Z owner counts; all-entry backward schedules and every supplied forward recurrence.'}
    result['digests']={key+'_sha256':digest(result[key]) for key in (*COMMON_FIELDS,'price_suffix_schedule','unpriced_suffix_schedule')}
    result['digests']['base57_sha256']=digest(scientific57(base57))
    return result


def combine(base,prices,caps,B,D):
    """Independent global price scan and explicit same-q57 minimum."""
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(B) is int and B>=0 and type(D) is int and D>0
    assert type(prices) is list and prices==[0]+[D*2**r for r in range(14)]
    assert all(type(v) is int for v in prices)
    assert caps.keys()==base['owner_caps'].keys()
    assert all(type(values) is list and len(values)==15 and all(type(v) is int and v>=0 for v in values) for values in caps.values())
    L=sum(base['base']['tightened']['path_numerators'].values());price_rows=[]
    for index,price in enumerate(prices):
        residual=sum(values[index] for values in caps.values());charge=price*B+residual
        numerator=L-charge;lower,remainder=divmod(numerator,D)
        price_rows.append({'lambda':price,'entry_charge':price*B,'residual_cap':residual,'charge':charge,
            'numerator':numerator,'integer_lower_bound':lower+int(remainder!=0)})
    selected=0
    for index in range(1,len(prices)):
        if price_rows[index]['charge']<price_rows[selected]['charge']:selected=index
    global_charge=price_rows[selected]['charge'];rows=[];deltas=[]
    for k,old in enumerate(base['rows']):
        charge=min(global_charge,old['charge']);numerator=L-charge;lower,remainder=divmod(numerator,D)
        row={'k':k,'charge':charge,'baseline57_charge':old['charge'],'global_charge':global_charge,
             'numerator':numerator,'integer_lower_bound':lower+int(remainder!=0),'charge_reduction_vs57':old['charge']-charge}
        rows.append(row);deltas.append({'k':k,'charge_reduction':old['charge']-charge,
            'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
    return {'price_rows':price_rows,'selected_price_index':selected,'global_charge':global_charge,'rows':rows,'deltas_vs57':deltas}


def z_counts(codes,start):
    """Exact within-source overlapping occurrence counts, transient O(n) state."""
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(codes) is list and codes and all(type(v) is int and v>=0 for v in codes)
    assert type(start) is int and 0<=start<len(codes)
    remaining=len(codes)-start;sequence=codes[start:]+[-1]+codes;z=[0]*len(sequence)
    left=right=comparisons=0
    for at in range(1,len(sequence)):
        if at<right:z[at]=min(right-at,z[at-left])
        while at+z[at]<len(sequence):
            comparisons+=1
            if sequence[z[at]]!=sequence[at+z[at]]:break
            z[at]+=1
        if at+z[at]>right:left,right=at,at+z[at]
    histogram=[0]*(remaining+1);offset=remaining+1
    for at in range(len(codes)):
        length=z[offset+at];assert 0<=length<=min(remaining,len(codes)-at)
        histogram[length]+=1
    counts=[0]*(remaining+1);total=0
    for length in range(remaining,0,-1):total+=histogram[length];counts[length]=total
    assert counts[remaining]>=1
    return counts,{'symbols':len(sequence),'comparisons':comparisons,'histogram_cells':len(histogram)}
