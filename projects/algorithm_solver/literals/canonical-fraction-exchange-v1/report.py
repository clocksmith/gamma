"""Independent retained-witness/receipt replay; never reruns dictionary search."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import statistics
import struct
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
REPORT_SECONDS=1200
REUSE='not_performed_relaxation_witness_only'
PATH_POLICY='minimum_N_then_complete_sorted_subset_ID_sequence'

class HardDeadline(BaseException):pass

def require_checks():
    if not __debug__ or sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE') not in (None,'','0'):
        raise RuntimeError('Independent report requires normal assertions')

require_checks()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rawsha=lambda data:hashlib.sha256(data).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
digest=lambda value:rawsha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())

def module(name,path):
    before=list(sys.path)
    try:
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    finally:sys.path[:]=before

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    tmp.replace(path)

def number(value,minimum=0,maximum=None):
    assert type(value) in (int,float) and math.isfinite(value)
    assert minimum is None or value>=minimum
    assert maximum is None or value<=maximum
    return value

def integer(value,minimum=0,maximum=None):
    assert type(value) is int and value>=minimum and (maximum is None or value<=maximum)
    return value

def distribution(values):
    values=sorted(values);assert values
    return {'n':len(values),'total':sum(values),'median':statistics.median(values),
            'p90':values[math.ceil(.9*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],
            'worst':values[-1],'within_32':sum(v<=32 for v in values),'within_96':sum(v<=96 for v in values)}

def exact(text,vocab):
    """Independent sliced-string forward DP retaining the entire ID tuple."""
    assert text and len(vocab)==len(set(vocab)) and all(vocab)
    best=[None]*(len(text)+1);best[0]=(0,())
    for start in range(len(text)):
        if best[start] is None:continue
        n,ids=best[start]
        for entry,word in enumerate(vocab):
            end=start+len(word)
            if end<=len(text) and text[start:end]==word:
                candidate=(n+1,ids+(entry,))
                if best[end] is None or candidate<best[end]:best[end]=candidate
    if best[-1] is None:raise ValueError('Unencodable source')
    n,ids=best[-1];chars=sum(len(vocab[i])==1 for i in ids)
    assert ''.join(vocab[i] for i in ids)==text
    return {'C':chars,'N':n,'sequence':list(ids),'words':tuple(vocab[i] for i in ids)}


def dictionary_bytes(vocab):
    assert 1<=len(vocab)==len(set(vocab))<=256 and all(type(w) is str and w for w in vocab)
    return b'LTD1'+struct.pack('>I',len(vocab))+b''.join(struct.pack('>I',len(w.encode()))+w.encode() for w in vocab)

def packet_ids(packet,dictionary,vocab,text):
    assert packet[:5]==b'LTV1\x08' and len(packet)>=41
    assert packet[5:37].hex()==rawsha(dictionary)
    ids=list(packet[41:]);assert len(ids)==int.from_bytes(packet[37:41],'big')
    assert all(i<len(vocab) for i in ids) and ''.join(vocab[i] for i in ids)==text
    return ids

def witness(folder,raw,texts,bans,config,caps,expected_vocab=None):
    """Independent canonical paths, paid bytes, fixed seed caps, support metadata."""
    folder=Path(folder);vocab=read(folder/'dictionary.json')
    assert vocab==sorted(set(vocab)) and len(vocab)<=config['pool']['capacity']
    if expected_vocab is not None:assert vocab==expected_vocab
    assert not set(vocab)&set(bans)
    binary=dictionary_bytes(vocab);assert (folder/'dictionary.bin').read_bytes()==binary
    decoder=config['decoder_dependency_bytes'];rows={};uses=Counter();used_by=[set() for _ in vocab];plans={}
    assert {p.stem for p in (folder/'packets').glob('*.bin')}==set(texts)
    for pid,text in sorted(texts.items()):
        packet=(folder/'packets'/f'{pid}.bin').read_bytes();ids=packet_ids(packet,binary,vocab,text)
        dp=exact(text,vocab);assert ids==dp['sequence'];plans[pid]=dp
        assert dp['N']<=caps[pid]['N'] and rawsha(text.encode())==caps[pid]['source_sha256']
        rows[pid]={'source_sha256':rawsha(text.encode()),'selections':dp['N'],'actions':dp['N']+1,'characters':dp['C'],
          'seed_cap':caps[pid]['N'],'selection_delta_from_seed':dp['N']-caps[pid]['N'],
          'packet_bytes':len(packet),'packet_sha256':rawsha(packet),'one_program_package_bytes':len(binary)+len(packet),
          'one_program_with_decoder':len(binary)+len(packet)+decoder}
        uses.update(ids)
        for entry in set(ids):used_by[entry].add(pid)
    stats=[]
    for entry,word in enumerate(vocab):
        owners=[pid for pid,text in texts.items() if word in text];assert owners
        stats.append({'entry_id':entry,'characters':len(word),'utf8_bytes':len(word.encode()),
          'distinct_program_support':len(owners),'packet_program_use':len(used_by[entry]),'selection_uses':uses[entry],
          'maximum_fraction_of_containing_source':max(len(word)/len(texts[pid]) for pid in owners)})
    n=sum(row['selections'] for row in rows.values());chars=sum(row['characters'] for row in rows.values())
    package=len(binary)+sum(row['packet_bytes'] for row in rows.values())
    rebuilt={'path_policy':PATH_POLICY,'per_problem':rows,'selections':distribution([row['selections'] for row in rows.values()]),
      'actions':distribution([row['actions'] for row in rows.values()]),'characters':chars,'character_fraction':chars/n,
      'exact_fraction':[chars,n],'score':[chars,n,package+decoder],'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab),
      'dictionary_sha256':sha(folder/'dictionary.json'),'dictionary_bytes':len(binary),'package_bytes':package,
      'package_with_decoder_sources':package+decoder,'framing_bytes':41*len(rows),'payload_bits':8*n,'padding_bits':0,
      'seed_cap_regressions':0,'source_bytes':sum(len(text.encode()) for text in texts.values())}
    assert raw==rebuilt,'Stored witness differs from independent canonical decoding/accounting'
    return {**rebuilt,'entry_statistics':stats,'minimum_entry_length':min(map(len,vocab)),
      'median_entry_length':statistics.median(map(len,vocab)),'maximum_entry_length':max(map(len,vocab)),
      'one_owner_entries':sum(s['distinct_program_support']==1 for s in stats),
      'entries_covering_at_least_90_percent_of_a_source':sum(s['maximum_fraction_of_containing_source']>=.9 for s in stats),
      'one_owner_and_near_whole_entries':sum(s['distinct_program_support']==1 and s['maximum_fraction_of_containing_source']>=.9 for s in stats),
      'unused_entries':sum(s['selection_uses']==0 for s in stats),'ten_percent_witness':10*chars<=n,
      'semantic_reuse_audit':REUSE,'exact_packet_ids_and_costs_rechecked':True},vocab,plans


def paired(a,b):
    x=a['per_problem'];y=b['per_problem'];assert set(x)==set(y)
    return {'better':sum(x[p]['selections']<y[p]['selections'] for p in x),
      'same':sum(x[p]['selections']==y[p]['selections'] for p in x),'worse':sum(x[p]['selections']>y[p]['selections'] for p in x),
      'N_delta':a['selections']['total']-b['selections']['total'],'C_delta':a['characters']-b['characters'],
      'fraction_delta':a['character_fraction']-b['character_fraction'],
      'strict_fraction_improvement':a['characters']*b['selections']['total']<b['characters']*a['selections']['total'],
      'full_package_delta':a['package_with_decoder_sources']-b['package_with_decoder_sources']}


def summary(witness,seed=None,previous=None):
    n=witness['selections'];entries=witness['entries'];one=witness['one_owner_entries']
    near=witness['entries_covering_at_least_90_percent_of_a_source'];both=witness['one_owner_and_near_whole_entries']
    result={'path_policy':PATH_POLICY,'programs':n['n'],'C':witness['characters'],'N':n['total'],'exact_fraction':[witness['characters'],n['total']],
      'actions':witness['actions']['total'],'selections':n,'action_quantiles':witness['actions'],
      'median_selections':n['median'],'p90_selections':n['p90'],'p95_selections':n['p95'],'character_fraction':witness['character_fraction'],
      'entries':entries,'character_entries':witness['character_entries'],'dictionary_bytes':witness['dictionary_bytes'],
      'package_bytes':witness['package_bytes'],'package_with_decoder_sources':witness['package_with_decoder_sources'],
      'per_problem':witness['per_problem'],'framing_bytes':witness['framing_bytes'],'payload_bits':witness['payload_bits'],'padding_bits':0,
      'source_bytes':witness['source_bytes'],'seed_cap_regressions':0,'entry_statistics':witness['entry_statistics'],
      'one_owner_entries':one,'one_owner_entry_share':one/entries,'near_whole_entries':near,'near_whole_entry_share':near/entries,
      'one_owner_and_near_whole_entries':both,'one_owner_and_near_whole_entry_share':both/entries,
      'unused_entries':witness['unused_entries'],'minimum_entry_length':witness['minimum_entry_length'],
      'median_entry_length':witness['median_entry_length'],'maximum_entry_length':witness['maximum_entry_length'],
      'near_whole_threshold':.9,'entry_share_denominator':'all_dictionary_entries_including_unused_and_singletons',
      'one_owner_definition':'substring occurs in exactly one distinct source, regardless of packet use',
      'near_whole_definition':'entry_length >= 90% of at least one source containing that entry',
      'entry_share_interpretation':'descriptive counts; not semantic reuse or additional legality tests'}
    if seed is not None:result['relative_to_seed']=paired(witness,seed)
    if previous is not None:result['relative_to_previous']=paired(witness,previous)
    return result


def score_tuple(score):
    chars,n,package=score;integer(chars);integer(n,1);integer(package);assert chars<=n
    return Fraction(chars,n),n,package


def objective(state):return score_tuple(state['witness']['score'])
def serialized(state):return state['witness']['score']


def audit_trace(events,result,texts,pool,states,limits,capacity=256,decoder_bytes=13010,caps=None):
    """Validate recorded opportunity/counter protocol without rerunning search.

    Rejected feasible scores are recorded evidence. Retained states have separate
    full DP/packet proofs; a reported unreachable source is checked directly.
    """
    assert pool==sorted(set(pool)) and set(states)==set(range(result['final_incumbent']+1))
    assert events and [r['event_no'] for r in events]==list(range(len(events)))
    times=[number(r['seconds']) for r in events];assert times==sorted(times)
    assert events[0]['event']=='start' and events[-1]['event']=='stop'
    seconds=number(result['seconds']);assert times[-1]<=seconds;assert result['soft_overrun_seconds']==max(0,seconds-limits['seconds'])
    current=states[0];ids={w:i for i,w in enumerate(pool)}
    active=tuple(ids[w] for w in current['vocab']);free=capacity-len(active)
    assert free==limits['expected_free_slots']==result['initial_free_slots']
    assert events[0]['seed']==current['identity'] and events[0]['score']==serialized(current)
    assert events[0]['seed_entries']==len(active) and events[0]['free_slots']==free
    counts={k:{'attempted':0,'completed':0,'coverage_failures':0,'cap_failures':0,'recomputed_programs':0} for k in ('add','rank','remove','swap','rescore')}
    attempted=completed=0;accepted=[];sweeps=0;epochs=set();a_iters=[];phase='A';next_b=0;next_kind='add'
    best=(objective(current),active,None,None);pending=None;open_sweep=None;last_end=None;scores=[];interrupted_failures=0
    halted=False
    owners={i:{pid for pid,text in texts.items() if word in text} for i,word in enumerate(pool)}
    def candidate(add,remove):return tuple(sorted((set(active)-set(remove))|set(add)))
    for event in events[1:-1]:
        kind=event['event']
        if kind=='sweep_start':
            assert open_sweep is None and pending is None and not halted
            assert event['sweep']==sweeps;sweeps+=1
            assert event['phase'] in ('A','B') and event['kind'] in ('add','rank','remove','swap')
            if event['phase']=='A':
                assert phase=='A' and event['kind']=='add' and event['iteration']==len(a_iters)<free
                if a_iters:assert accepted and accepted[-1]['incumbent']==len(a_iters)
                a_iters.append(event['iteration']);best=(objective(current),active,None,None)
            else:
                if phase=='A':
                    assert best[2] is None
                    assert len(a_iters)==free or len(accepted)<len(a_iters)
                    phase='B';next_b=0;next_kind='rank' if len(active)==capacity else 'add'
                    best=(objective(current),active,None,None)
                assert event['iteration']==next_b and event['kind']==next_kind
                epochs.add(next_b)
            if event['kind'] in ('add','rank'):
                moves=[((i,),()) for i in range(len(pool)) if i not in active];assert event['shortlist']==[];scores=[]
                assert (event['kind']=='rank') is (len(active)==capacity)
            elif event['kind']=='remove':
                moves=[((),(i,)) for i in active];assert event['shortlist']==[]
            else:
                shortlist=[i for score,i in sorted(scores)[:limits['shortlist']]]
                assert event['shortlist']==shortlist
                moves=[((a,),(d,)) for a in shortlist for d in active]
            assert event['opportunities']==len(moves)
            assert event['opportunity_sha256']==digest([[list(add),list(remove)] for add,remove in moves])
            open_sweep={'start':event,'moves':moves,'base_attempted':0,'base_completed':0,'all':0}
        elif kind=='evaluation':
            assert open_sweep is not None and not halted and event['sweep']==open_sweep['start']['sweep']
            assert event['evaluation']==attempted<limits['evaluations'];attempted+=1;open_sweep['all']+=1
            k=event['kind'];assert k in counts;counts[k]['attempted']+=1
            started=number(event['started_seconds']);assert started<limits['seconds'] and started<=event['seconds']
            assert started>=events[event['event_no']-1]['seconds']
            if k=='rescore':
                assert pending is not None and event['add']==event['remove']==[]
                candidate_ids=pending[1];assert event['candidate']==list(candidate_ids)
                affected=sorted(texts)
            else:
                assert pending is None and k==open_sweep['start']['kind'] and event['candidate'] is None
                add,remove=open_sweep['moves'][open_sweep['base_attempted']]
                assert event['add']==list(add) and event['remove']==list(remove)
                open_sweep['base_attempted']+=1;candidate_ids=candidate(add,remove)
                affected=set().union(*(owners[a] for a in add)) if add else set()
                deleted={pool[d] for d in remove}
                affected.update(pid for pid,p in current['plans'].items() if set(p['words'])&deleted);affected=sorted(affected)
            assert event['affected_programs']==len(affected)
            recomputed=integer(event['recomputed_programs'],0,len(affected));counts[k]['recomputed_programs']+=recomputed
            failed=event['failed_pid']
            if failed is not None:
                assert recomputed and failed==affected[recomputed-1]
                try:exact(texts[failed],[pool[i] for i in candidate_ids])
                except ValueError:pass
                else:raise AssertionError('Recorded coverage failure source remains encodable')
            assert type(event['complete']) is bool
            if not event['complete']:
                assert event['outcome']=='interrupted' and event['seconds']>=limits['seconds']
                interrupted_failures+=failed is not None;pending=None;halted=True
                continue
            completed+=1;counts[k]['completed']+=1
            if k!='rescore':open_sweep['base_completed']+=1
            if event['outcome']=='coverage_failure':
                assert k!='rescore' and failed is not None
                counts[k]['coverage_failures']+=1
                assert not any(key in event for key in ('N','C','score','cap_failure_witness','cap_failure_count_search_only'))
                continue
            assert failed is None and recomputed==len(affected)
            assert len(candidate_ids)<=capacity+int(k=='rank') and (k=='rank' or len(candidate_ids)<=capacity)
            n=integer(event['N'],len(texts),sum(map(len,texts.values())));chars=integer(event['C'],0,n)
            package=8+sum(4+len(pool[i].encode()) for i in candidate_ids)+41*len(texts)+n
            assert event['score']==[chars,n,package+decoder_bytes];score=score_tuple(event['score'])
            if event['outcome']=='cap_failure':
                assert k in ('remove','swap') and caps is not None
                proof=event['cap_failure_witness'];assert set(proof)=={'pid','N','cap'} and proof['pid'] in affected
                dp=exact(texts[proof['pid']],[pool[i] for i in candidate_ids])
                assert dp['N']==proof['N']>proof['cap']==caps[proof['pid']]['N']
                integer(event['cap_failure_count_search_only'],1,len(texts));counts[k]['cap_failures']+=1
                continue
            assert event['outcome']==('ranking_only' if len(candidate_ids)>capacity else 'feasible')
            assert 'cap_failure_witness' not in event and 'cap_failure_count_search_only' not in event
            if k=='rescore':
                assert score==pending[0] and len(candidate_ids)<=capacity
                best=(score,candidate_ids,pending[2],event['evaluation']);pending=None
            else:
                if k in ('add','rank'):scores.append((score,event['add'][0]))
                if len(candidate_ids)<=capacity and score<objective(current) and (score,candidate_ids)<best[:2]:
                    pending=(score,candidate_ids,event['evaluation'])
        elif kind=='sweep_end':
            assert open_sweep is not None and event['sweep']==open_sweep['start']['sweep']
            assert event['attempted_probes']==open_sweep['base_attempted']
            assert event['completed_probes']==open_sweep['base_completed'] and event['all_evaluations']==open_sweep['all']
            assert type(event['complete']) is bool
            if event['complete']:
                assert event['stop'] is None and pending is None and event['completed_probes']==len(open_sweep['moves'])
            else:
                assert event['stop'] in ('time_limit','evaluation_limit');halted=True
                if event['stop']=='evaluation_limit':assert attempted==limits['evaluations']
                else:assert event['seconds']>=limits['seconds']
                pending=None
            last_end={**event,'phase':open_sweep['start']['phase'],'iteration':open_sweep['start']['iteration'],'kind':open_sweep['start']['kind']}
            if last_end['phase']=='B' and event['complete']:
                next_kind='remove' if last_end['kind'] in ('add','rank') else 'swap' if last_end['kind']=='remove' else None
            open_sweep=None
        elif kind=='accept':
            assert open_sweep is None and last_end is not None and best[2] is not None and best[3] is not None
            assert last_end['phase']=='A' or last_end['kind']=='swap' or not last_end['complete']
            index=len(accepted)+1;assert event['incumbent']==index and index in states
            assert event['before']==serialized(current) and score_tuple(event['after'])==best[0]
            assert event['origin_evaluation']==best[2] and event['rescore_evaluation']==best[3]
            assert event['partial_sweep'] is (not last_end['complete'])
            after=states[index];new_ids=tuple(ids[w] for w in after['vocab'])
            assert new_ids==best[1] and event['identity']==after['identity']
            assert objective(after)==best[0]<objective(current)
            accepted.append({key:event[key] for key in ('incumbent','origin_evaluation','rescore_evaluation','before','after','identity','partial_sweep')})
            current=after;active=new_ids;best=(objective(current),active,None,None)
            if phase=='B':next_b+=1;next_kind='rank' if len(active)==capacity else 'add'
        else:raise AssertionError('Unexpected search event')
    assert open_sweep is None and pending is None
    assert result['attempted']==attempted and result['completed']==completed and result['counters']==counts
    assert result['sweeps']==sweeps and result['accepted']==accepted and result['final_incumbent']==len(accepted)
    assert result['exchange_epochs_started']==len(epochs)<=limits['epochs']
    assert epochs==set(range(len(epochs))) and len(a_iters)<=free
    assert result['final_score']==serialized(current)
    assert result['stop'] in ('time_limit','evaluation_limit','epoch_limit','no_improving_evaluated_neighbor')
    if result['stop'] in ('time_limit','evaluation_limit'):
        assert last_end and last_end['stop']==result['stop'] and last_end['complete'] is False
    elif result['stop']=='no_improving_evaluated_neighbor':
        assert last_end['phase']=='B' and last_end['kind']=='swap' and last_end['complete']
        assert best[2] is None and next_kind is None
    else:assert len(epochs)==limits['epochs'] and next_b==limits['epochs']
    stop=events[-1]
    assert {k:v for k,v in stop.items() if k not in ('event','event_no','seconds')}=={k:v for k,v in result.items() if k not in ('seconds','soft_overrun_seconds')}
    return {'attempted':attempted,'completed':completed,'counters':counts,'sweeps':sweeps,
            'declared_opportunities':sum(r['opportunities'] for r in events if r['event']=='sweep_start'),
            'sweep_receipts':[{'sweep':a['sweep'],'phase':a['phase'],'kind':a['kind'],'iteration':a['iteration'],
                'opportunities':a['opportunities'],'opportunity_sha256':a['opportunity_sha256'],'shortlist':a['shortlist'],
                'attempted_probes':b['attempted_probes'],'completed_probes':b['completed_probes'],
                'omitted_opportunities':a['opportunities']-b['attempted_probes'],'complete':b['complete'],'stop':b['stop']}
              for a,b in zip([e for e in events if e['event']=='sweep_start'],[e for e in events if e['event']=='sweep_end'])],
            'complete_sweeps':sum(r['event']=='sweep_end' and r['complete'] for r in events),
            'partial_sweeps':sum(r['event']=='sweep_end' and not r['complete'] for r in events),
            'interrupted_probes':attempted-completed,'interrupted_probes_with_observed_coverage_failure':interrupted_failures,
            'accepted_moves':len(accepted),'partial_sweep_acceptances':sum(a['partial_sweep'] for a in accepted),
            'stop':result['stop'],'search_seconds':seconds,'soft_overrun_seconds':result['soft_overrun_seconds'],
            'rejected_score_scope':'Recorded feasible rejected scores; no optimization/search rerun or local-optimum claim.'}


def independent_inputs(config,work,cohort):
    """Separate reconstruction of item40 pool, certificate and reference bindings."""
    assert config['active'] is True and cohort in ('R','naming')
    backend=module('report_canonical_backend40',LIT/'fraction-primal-repair-v1/backend.py')
    builder=module('report_canonical_pool40',LIT/'fraction-primal-repair-v1/pool.py')
    cp=LIT/config['parent_contract'];assert sha(cp)==config['parent_contract_sha256'];parent_contract=read(cp)
    public=read(LIT/config['parent_evidence']);private=read(work/config['parent_private_results'])
    assert public['complete'] is private['complete'] is True
    assert public['validation_loaded'] is private['validation_loaded'] is False
    assert public['contract_sha256']==private['contract_sha256']==sha(cp)
    private_hash=sha(work/config['parent_private_results'])
    assert private_hash==public['private_results_sha256']==config['private_files'][config['parent_private_results']]
    pub=next(a for a in public['arms'] if a['cohort']==cohort);raw=next(a for a in private['arms'] if a['cohort']==cohort)
    texts,seed,q,p35=backend.inputs(parent_contract,work,cohort)
    assert len(texts)==300 and set(texts)==set(map(str,config['fit_ids']))
    assert pub['fit_source_sha256']==raw['fit_source_sha256']==p35['fit_source_sha256']
    assert pub['parent_q_sha256']==raw['parent_q_sha256']==p35['certificate']['q_sha256']
    bans=backend.dual.sel.forbidden_strings(texts);index=builder.implicit.Index(texts,bans)
    cert=index.certificate(q,config['pool']['capacity'],config['pool']['denominator'])
    assert builder.implicit.verify(index,q,config['pool']['capacity'],config['pool']['denominator'])==cert['numerator']
    for key in backend.CERT_KEYS:
        assert cert[key]==p35['certificate'][key]==pub['parent_full_class_certificate'][key]==raw['parent_full_class_certificate'][key]
    candidates,info=builder.build(index,q,seed,config['pool']['denominator'],config['pool']['capacity'],config['pool']['entries'])
    counts={k:v for k,v in info.items() if k!='provenance'}
    assert counts==pub['pool_counts']==raw['pool_counts']
    pp=work/config['parent_pool'][cohort]
    assert read(pp)==candidates==sorted(set(candidates))
    assert sha(pp)==pub['pool_sha256']==raw['pool_sha256']==config['private_files'][config['parent_pool'][cohort]]
    provenance=pp.parent/'pool-provenance.json'
    assert sha(provenance)==raw['pool_provenance_sha256'] and read(provenance)==info
    references={};hashes={}
    for name in ('seed',):
        rel=config['parent_references'][cohort][name];path=work/rel;vocab=read(path)
        assert sha(path)==config['private_files'][rel]==pub['witnesses'][name]['dictionary_sha256']==raw['witnesses'][name]['dictionary_sha256']
        assert len(vocab)==len(set(vocab))<=config['pool']['capacity'] and set(vocab)<=set(candidates) and not set(vocab)&bans
        references[name]=sorted(vocab);hashes[name]=sha(path)
    assert references['seed']==sorted(seed) and len(seed)==config['expected_seed_entries'][cohort]
    assert config['pool']['capacity']-len(seed)==config['search']['expected_free_slots']
    return {'texts':texts,'candidates':candidates,'seed':references['seed'],'references':references,'bans':bans,
            'parent_arm':pub,'pool_counts':counts,'original_reference_hashes':hashes,
            'certificate':{k:cert[k] for k in backend.CERT_KEYS},
            'bindings':{'source_sha256':pub['fit_source_sha256'],'parent_q_sha256':pub['parent_q_sha256'],
                        'pool_sha256':sha(pp),'parent_private_results_sha256':private_hash}}


def occurrence_counts(texts,pool,limits):
    """Independently count the frozen trie walk, without production graph arrays."""
    assert sum(map(len,pool))<=limits['max_pool_characters']
    trie={}
    for word in pool:
        node=trie
        for ch in word:node=node.setdefault(ch,{})
        assert None not in node;node[None]=True
    transitions=arcs=0
    for text in texts.values():
        for start in range(len(text)):
            node=trie
            for ch in text[start:]:
                transitions+=1;assert transitions<=limits['max_transitions']
                node=node.get(ch)
                if node is None:break
                if None in node:arcs+=1;assert arcs<=limits['max_arcs']
    return arcs,transitions


def canonical_parent(config,cohort,source_hash,original_seed_hash):
    path=LIT/config['canonical_parent_evidence']
    assert sha(path)==config['code_hashes'][config['canonical_parent_evidence']]
    shadow=read(path);primarypath=LIT/'direct-fraction-exchange-v1/evidence/results.json';primary=read(primarypath)
    assert sha(primarypath)==config['code_hashes'][str(primarypath.relative_to(LIT))]==shadow['accepted_primary_report_sha256']
    assert primary['complete'] is shadow['complete'] is True and primary['validation_loaded'] is shadow['validation_loaded'] is False
    assert primary['contract_sha256']==shadow['contract_sha256']==sha(LIT/'direct-fraction-exchange-v1/contract.json')
    arm=next(a for a in shadow['arms'] if a['cohort']==cohort)
    assert arm['source_sha256']==source_hash and arm['original_parent_seed_dictionary_sha256']==original_seed_hash
    seed=arm['witnesses']['seed'];caps={pid:{'source_sha256':row['source_sha256'],'N':row['N']} for pid,row in seed['canonical_min_N']['per_problem'].items()}
    assert caps==config['canonical_seed_caps'][cohort]
    return seed


def replay_arm(raw,run,inputs,config,contract_hash):
    cohort=raw['cohort'];folder=Path(run)/cohort;texts=inputs['texts'];pool=inputs['candidates']
    assert cohort in ('R','naming') and raw['complete'] is True and raw['validation_loaded'] is False
    assert raw==read(folder/'results.json') and raw['contract_sha256']==contract_hash
    assert read(folder/'status.json')=={'complete':True,'phase':'complete'} and not (folder/'failure.json').exists()
    assert raw['fit_problems']==len(texts)==len(config['fit_ids'])
    for key in ('bindings','pool_counts'):assert raw[key]==inputs[key]
    assert raw['original_seed_hash']==inputs['original_reference_hashes']['seed']
    assert len(pool)<=config['pool']['entries'] and not set(pool)&inputs['bans']
    arcs,transitions=occurrence_counts(texts,pool,config['construction'])
    assert arcs==raw['arcs']==inputs['parent_arm']['arcs'] and transitions==raw['transitions']==inputs['parent_arm']['transitions']
    caps={pid:{'source_sha256':rawsha(text.encode()),'N':exact(text,inputs['seed'])['N']} for pid,text in texts.items()}
    assert caps==config['canonical_seed_caps'][cohort]==read(folder/'seed-caps.json') and sha(folder/'seed-caps.json')==raw['seed_caps_sha256']
    reference=canonical_parent(config,cohort,inputs['bindings']['source_sha256'],raw['original_seed_hash'])
    states={};last=integer(raw['final_incumbent']);assert [i['index'] for i in raw['incumbents']]==list(range(last+1))
    assert {p.name for p in (folder/'incumbents').iterdir()}=={f'{i:03d}' for i in range(last+1)}
    assert {p.name for p in (folder/'retained-dictionaries').iterdir()}=={f'{i:03d}.json' for i in range(last+1)}
    for row in raw['incumbents']:
        i=row['index'];path=folder/'retained-dictionaries'/f'{i:03d}.json';vocab=read(path)
        assert set(vocab)<=set(pool)
        w,v,p=witness(folder/'incumbents'/f'{i:03d}',row['witness'],texts,inputs['bans'],config,caps,vocab)
        assert sha(path)==w['dictionary_sha256']
        states[i]={'witness':w,'vocab':v,'plans':p,'identity':{'index':i,'dictionary_sha256':sha(path)}}
    assert states[0]['vocab']==inputs['seed']
    seed=states[0]['witness'];parentseed=reference['canonical_min_N']
    assert seed['dictionary_sha256']==reference['sorted_dictionary_sha256']
    for pid,row in seed['per_problem'].items():
        old=parentseed['per_problem'][pid]
        assert (row['source_sha256'],row['selections'],row['characters'],row['packet_sha256'])==(old['source_sha256'],old['N'],old['C'],old['packet_sha256'])
    for key,oldkey in [('characters','C'),('selections','selections'),('actions','action_distribution'),('dictionary_bytes','dictionary_bytes'),
                       ('package_bytes','package_bytes'),('package_with_decoder_sources','package_with_decoder_sources')]:
        assert seed[key]==parentseed[oldkey]
    assert sha(folder/'trace.jsonl')==raw['trace_sha256']
    events=[json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()]
    search=audit_trace(events,raw['search'],texts,pool,states,config['search'],config['pool']['capacity'],config['decoder_dependency_bytes'],caps)
    elapsed=number(raw['seconds'],maximum=config['limits']['production_seconds'])
    setup=number(raw['build_seconds']);packets=number(raw['witness_seconds']);assert setup+packets+search['search_seconds']<=elapsed
    rss=integer(raw['peak_rss_kib'],1);assert rss*1024<=config['limits']['address_space_bytes']
    summaries=[{'index':i,**summary(state['witness'],seed,states[i-1]['witness'] if i else None),
       'sorted_dictionary_sha256':state['identity']['dictionary_sha256']} for i,state in states.items()]
    assert all(s['relative_to_seed']['worse']==0 for s in summaries)
    final=summaries[-1]
    return {'cohort':cohort,'complete':True,'validation_loaded':False,'contract_sha256':contract_hash,
      'bindings':inputs['bindings'],'pool_counts':inputs['pool_counts'],'arcs':arcs,'transitions':transitions,
      'parent_full_class_integer_lower_bound':inputs['certificate']['integer_lower_bound'],
      'parent_full_class_certificate_replayed':True,'bound_interpretation':'Historical unrestricted F certificate only; no canonical-ratio optimality gap.',
      'canonical_parent_evidence':config['canonical_parent_evidence'],'seed_caps_sha256':raw['seed_caps_sha256'],
      'original_parent_seed_dictionary_sha256':raw['original_seed_hash'],'retained':summaries,'final_incumbent':last,'seed':summaries[0],'final':final,
      'search':search,'production_seconds':elapsed,'build_seconds':setup,'witness_seconds':packets,'peak_rss_kib':rss,
      'trace_sha256':raw['trace_sha256'],'private_arm_result_sha256':sha(folder/'results.json'),
      'source_qualification':'Pinned item13 exact source-hash receipts only; no new execution, item23 failure not repaired.',
      'semantic_reuse_audit':REUSE,'local_or_global_optimality_claim':False}


def combine(arms,production,contract,elapsed,run):
    assert contract['active'] is True and production==read(run/'results.json')
    assert production['complete'] is True and production['validation_loaded'] is False and not (run/'failure.json').exists()
    ch=sha(HERE/'contract.json');assert production['contract_sha256']==ch
    supervisor=read(run/'supervisor.json')
    assert supervisor['complete'] is True and supervisor['phase']=='production' and supervisor['contract_sha256']==ch
    assert len(supervisor['returncodes'])==2 and all(type(code) is int and code==0 for code in supervisor['returncodes'])
    cleanup=number(supervisor['cleanup_seconds'],maximum=contract['limits']['cleanup_seconds'])
    number(supervisor['elapsed'],maximum=contract['limits']['production_seconds']+contract['limits']['cleanup_seconds'])
    assert supervisor['elapsed']>=production['seconds']
    number(production['seconds'],maximum=contract['limits']['production_seconds']);number(elapsed,maximum=contract['limits']['report_seconds'])
    assert [a['cohort'] for a in arms]==[a['cohort'] for a in production['arms']]==['R','naming']
    for arm,raw in zip(arms,production['arms']):
        assert arm['complete'] is True and arm['validation_loaded'] is False and arm['contract_sha256']==ch
        assert raw==read(run/arm['cohort']/'results.json')
        assert sha(run/arm['cohort']/'results.json')==arm['private_arm_result_sha256']
        assert arm['production_seconds']<=production['seconds']
        number(arm['report_worker_seconds'],maximum=elapsed)
        integer(arm['report_peak_rss_kib'],1,contract['limits']['address_space_bytes']//1024)
    return {'schema':'gamma.canonical-fraction-exchange.report.v1','complete':True,'population':'fixed300_fit_only',
            'validation_loaded':False,'contract_sha256':ch,'private_results_sha256':sha(run/'results.json'),
            'production_supervisor_sha256':sha(run/'supervisor.json'),'production_seconds':production['seconds'],
            'report_seconds':elapsed,'cleanup_seconds':cleanup,'arms':arms,
            'predictions':{'P1':all(a['final']['seed_cap_regressions']==0 for a in arms),
              'P2':all(a['final']['C']*a['seed']['N']<a['seed']['C']*a['final']['N'] for a in arms),
              'P3':any(10*w['C']<=w['N'] for a in arms for w in a['retained'])},
            'offline_encoder_bytes':contract['offline_encoder_bytes'],'decoder_dependency_bytes':contract['decoder_dependency_bytes'],
            'runtime_footprint':'Installed runtime footprint unmeasured.','model_bytes':0,'training_steps':0,
            'm1_qualification':False,'local_or_global_optimality_claim':False,
            'interpretation':'Fixed-fit canonical-fraction relaxation witnesses with immutable per-source seed caps. Adjacent-incumbent regressions inside those caps remain visible. No M1 qualification or promotion; historical full-substring F bounds are separate.'}


def failure_result(reason):
    return {'complete':False,'population':'fixed300_fit_only','validation_loaded':False,
            'failure_reason':reason,'predictions':{'P1':None,'P2':None,'P3':None},'m1_qualification':False}


def markdown(result):
    if not result['complete']:return '# Item47 incomplete\n\nIndependent replay/publication incomplete; no verdict. Partial witnesses are not promoted.\n'
    lines=['# Item47 capped canonical fraction exchange','',result['interpretation'],'',
      '| Cohort / witness | C | N | C/N | Median / p95 N | Full package bytes | Seed regressions |',
      '| --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for arm in result['arms']:
        for name in ('seed','final'):
            w=arm[name];lines.append(f"| {arm['cohort']} / {name} | {w['C']} | {w['N']} | {w['character_fraction']:.6f} | {w['median_selections']} / {w['p95_selections']} | {w['package_with_decoder_sources']} | {w['seed_cap_regressions']} |")
        s=arm['search'];lines+=['',f"{arm['cohort']}: {s['attempted']} attempted / {s['completed']} completed evaluations; {s['accepted_moves']} retained changes; {s['partial_sweeps']} partial sweeps. Stop: {s['stop']}. Search elapsed {s['search_seconds']:.3f}s, cooperative deadline overrun {s['soft_overrun_seconds']:.3f}s."]
    lines+=['','Predictions: '+json.dumps(result['predictions'],sort_keys=True),'',
      'All paths minimize N then the complete ID sequence, without a character tie or minimum-F path. Objective ratios use exact integers. Each retained source stays within its original canonical seed cap; later transitions may increase a source from below that cap. Those adjacent changes and equal-ratio plateaus remain explicit in results.json.',
      '', 'Packets charge one Finish action, all shared dictionary bytes, 41 framing bytes per program, eight-bit selections and zero padding. Full packages include the pinned decoder files; offline tools and source bytes are separate.',
      '', 'Every retained packet and each rejected coverage/cap witness is independently checked. Other rejected feasible scores and additional cap-violation counts remain recorded search diagnostics. Top-four swaps and partial sweeps establish no local/global optimum.',
      '', 'One-owner and near-whole shares are descriptive, not semantic reuse. No validation, source execution, M1 qualification, new impossibility result or promotion.']
    return '\n'.join(lines)+'\n'


def publish(result,output):
    """Withdraw both public success artifacts after any publication failure."""
    output=Path(output)
    try:
        output.mkdir(parents=True,exist_ok=True)
        if not result['complete']:result={**result,'predictions':{'P1':None,'P2':None,'P3':None}}
        encoded=json.dumps(result,sort_keys=True,indent=2)+'\n';prose=markdown(result)
        (output/'REPORT.md.pending').write_text(prose);(output/'results.json.pending').write_text(encoded)
        (output/'REPORT.md.pending').replace(output/'REPORT.md')
        (output/'results.json.pending').replace(output/'results.json')
        for name in ('REPORT.md.pending','results.json.pending'):(output/name).unlink(missing_ok=True)
    except BaseException:
        failed=failure_result('publication_failure')
        for name,text in [('REPORT.md',markdown(failed)),('results.json',json.dumps(failed,sort_keys=True,indent=2)+'\n')]:
            path=output/name
            try:
                tmp=output/(name+'.failure');tmp.write_text(text);tmp.replace(path)
            except BaseException:
                try:path.unlink(missing_ok=True)
                except BaseException:pass
        raise


def main(cohort,work,run,output,deadline):
    started=time.monotonic();phase='setup';target=Path(output)/(cohort+'.json')
    def expired(*_):raise HardDeadline('report worker deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,min(REPORT_SECONDS,max(.001,deadline-started)))
    try:
        require_checks();resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
        os.sched_setaffinity(0,{'R':{4},'naming':{5}}[cohort]);config=read(HERE/'contract.json')
        assert config['limits']['report_seconds']==REPORT_SECONDS and 0<deadline-started<=REPORT_SECONDS
        assert config['limits']['address_space_bytes']==8*1024**3 and config['limits']['arm_cores']=={'R':[4],'naming':[5]}
        # Common runtime/hash validation is shared; input/certificate reconstruction
        # and retained packet/trace evidence below are independently implemented.
        common=module('canonical_exchange_report_runtime',HERE/'common.py');common.check_contract(config)
        assert not (run/'failure.json').exists()
        production=read(run/'results.json');supervisor=read(run/'supervisor.json')
        assert production['complete'] is supervisor['complete'] is True and supervisor['phase']=='production'
        assert len(supervisor['returncodes'])==2 and all(type(code) is int and code==0 for code in supervisor['returncodes'])
        assert production['contract_sha256']==supervisor['contract_sha256']==sha(HERE/'contract.json')
        assert set(config['decoder_source_files'])=={'literals.py','pass2/working/bitpack.py'}
        for rel,row in config['decoder_source_files'].items():
            assert sha(LIT/rel)==row['sha256'] and (LIT/rel).stat().st_size==row['bytes']
        assert sum(row['bytes'] for row in config['decoder_source_files'].values())==config['decoder_dependency_bytes']
        common.check_contract(config,work)
        phase='input_replay'
        inputs=independent_inputs(config,work,cohort);phase='witness_trace_replay'
        result=replay_arm(read(run/cohort/'results.json'),run,inputs,config,sha(HERE/'contract.json'))
        result['report_worker_seconds']=time.monotonic()-started
        result['report_peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if time.monotonic()>=deadline:raise HardDeadline('report worker deadline')
        write(target,result)
        if time.monotonic()>=deadline:raise HardDeadline('report publication deadline')
    except BaseException as error:
        target.unlink(missing_ok=True)
        write(Path(output)/(cohort+'-failure.json'),{**failure_result('worker_failure'),'phase':phase,
              'exception':type(error).__name__,'seconds':time.monotonic()-started})
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--deadline',type=float,required=True)
    a=ap.parse_args();main(a.cohort,a.work,a.run,a.output,a.deadline)
