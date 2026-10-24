"""Item54 independent replay with old-parser batching, never execution caching."""
import argparse
from collections import Counter,defaultdict
import json
import math
import os
from pathlib import Path
import resource
import signal
import statistics
import tempfile
import time
import common as c
from ban_replay import BanReplay

p=c.p
POLICIES=('canonical','shortest_min_char')
ANCHORS=('24','43N','43W')
SECONDS=1800
MEMORY=8*1024**3


def number(value,maximum):
    assert type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum
    return value


def encode(text,vocab,policy='shortest_min_char'):
    """Independent forward DP; retain supplied IDs and the full sequence tie."""
    assert policy in POLICIES and 1<=len(vocab)==len(set(vocab))<=256 and all(vocab)
    by_first=defaultdict(list)
    for i,word in enumerate(vocab):by_first[word[0]].append((i,word))
    best=[None]*(len(text)+1);best[0]=(0,0,())
    for start,char in enumerate(text):
        if best[start] is None:continue
        n,chars,ids=best[start]
        for i,word in by_first[char]:
            if text.startswith(word,start):
                end=start+len(word);candidate=(n+1,chars+(len(word)==1 if policy=='shortest_min_char' else 0),ids+(i,))
                if best[end] is None or candidate<best[end]:best[end]=candidate
    if best[-1] is None:raise ValueError('unrepresentable')
    return list(best[-1][2])


def state(texts,vocab):
    """No ordering/sorting wrapper: parent literal IDs are immutable."""
    assert isinstance(vocab,list) and 1<=len(vocab)==len(set(vocab))<=256 and all(vocab)
    plans={pid:[vocab[i] for i in encode(text,vocab)] for pid,text in texts.items()}
    n=sum(map(len,plans.values()));chars=sum(len(w)==1 for words in plans.values() for w in words)
    db=len(c.analyze.dictionary_bytes(vocab))
    return {'sources':dict(texts),'vocab':list(vocab),'plans':plans,'N':n,'C':chars,
            'package_bytes':db+41*len(texts)+n,'dictionary_bytes':db,'source_bytes':sum(len(t.encode()) for t in texts.values())}


def cost(s):return s['N'],s['C'],s['package_bytes']
def tie(s):return cost(s),s['source_bytes'],tuple(s['vocab']),tuple(sorted(s['sources'].items()))


def local_matches(text,record,pattern):
    if record['unsafe'] or not text.isascii():return []
    matches=[]
    for variable in record['variables']:
        if not variable['eligible']:continue
        fragment=''.join(variable['name'] if part is None else part for part in pattern)
        for start in range(len(text)-len(fragment)+1):
            if text.startswith(fragment,start) and p.pattern_at(text,variable['spans'],start,start+len(fragment))==pattern:
                matches.append(variable['id']);break
    return matches


def check_geometry(group,texts,records):
    assert set(group['updates'])=={g['pid'] for g in group['geometry']} and len(group['geometry'])==len(group['updates'])
    for g in group['geometry']:
        pid=g['pid'];text=texts[pid];record=records[pid];variable=record['variables'][g['binding']]
        assert text.isascii() and not record['unsafe'] and variable['eligible']
        assert g['from']==variable['name'] and g['to']==group['target'] and g['from']!=g['to']
        assert g['spans']==variable['spans'] and g['before_sha256']==c.sha(text.encode())
        colors=[v['name'] for v in record['variables']];colors[g['binding']]=g['to'];assert c.rewrite.legal(record,colors)
        actual=text
        for start,end in reversed(sorted(g['spans'])):
            assert text[start:end]==g['from'];actual=actual[:start]+g['to']+actual[end:]
        assert actual==group['updates'][pid] and c.sha(actual.encode())==g['after_sha256']


class Ledger:
    def __init__(self,initial=None,ban_parser=None):
        self.ban_parser=p.banned if ban_parser is None else ban_parser
        self.variants={} if initial is None else dict(initial['variants'])
        self.bans=set() if initial is None else set(initial['banned'])
        self.encounters=[] if initial is None else list(initial['encounters'])
        self.pending=None
    def encounter(self,texts,phase,dictionaries):
        fresh={}
        for pid,text in texts.items():
            key=f'{pid}:{c.sha(text.encode())}'
            if key not in self.variants:self.variants[key]=text;fresh[key]=text
        if fresh:
            self.bans.update(self.ban_parser(fresh));self.encounters.append({'phase':phase,'variant_keys':list(fresh)})
        assert not any(set(vocab)&self.bans for vocab in dictionaries.values()),'Encountered ban invalidates fixed dictionary'
    def receipt(self):return {'variants':self.variants,'banned':sorted(self.bans),'encounters':self.encounters,'last_rendered_group':self.pending}


def derive_menu(texts,vocab):
    current=state(texts,vocab);records=c.rewrite.records(texts)
    return {'names':p.names(vocab,records),'contexts':p.contexts(current,records),
            'source_sha256':p.digest_sources(texts),'dictionary_binary_sha256':c.sha(c.analyze.dictionary_bytes(vocab))}


def replay_apply(got,texts,vocab,menu,dictionaries,initial=None,phase='fit',proposal_cap=153600,worker_seconds=1800,ban_parser=None):
    """Reconstruct every offered group and score, not just accepted transitions."""
    assert set(got)=={'complete','original','selected','vocab','names','contexts','trace','ledger','initial_coverage_failures','proposals','accepted','seconds'}
    assert got['complete'] is True and got['original']==texts and got['vocab']==vocab
    assert got['names']==menu['names'] and got['contexts']==menu['contexts']
    assert len(menu['names'])<=12 and len(menu['contexts'])<=16
    number(got['seconds'],worker_seconds)
    selected=dict(texts);ledger=Ledger(initial,ban_parser);ledger.encounter(texts,phase+':initial',dictionaries)
    failures=[];trace=[];count=0;accepted=[]
    for pid in sorted(texts,key=int):
        try:current=state({pid:texts[pid]},vocab)
        except ValueError:failures.append(pid);continue
        for pass_no in range(2):
            records=c.rewrite.records(current['sources']);record=records[pid];best=None
            row={'pid':pid,'pass':pass_no,'trials':[],'accepted':None};trace.append(row)
            for context in menu['contexts']:
                local={'pattern':context['pattern'],'matches':[[pid,bid] for bid in local_matches(current['sources'][pid],record,context['pattern'])]}
                for target in menu['names']:
                    group=p.make_group(current['sources'],records,local,target,min_support=1)
                    if group is None:continue
                    count+=1;assert count<=proposal_cap
                    check_geometry(group,current['sources'],records);ledger.pending=group
                    ledger.encounter(group['updates'],f'{phase}:{pid}:{pass_no}:{group["id"]}',dictionaries)
                    try:candidate=state(group['updates'],vocab)
                    except ValueError:candidate=None
                    row['trials'].append({'group':group,'before_score':list(cost(current)),
                        'score':None if candidate is None else list(cost(candidate)),'coverage':candidate is not None})
                    if candidate is not None and cost(candidate)<cost(current) and (best is None or tie(candidate)<tie(best[0])):
                        best=(candidate,len(row['trials'])-1)
            if best is None:break
            candidate,winner=best;group=row['trials'][winner]['group'];row['accepted']=winner
            for geom in group['geometry']:
                accepted.append({'pid':pid,'pass':pass_no,'binding':geom['binding'],'occurrences':len(geom['spans']),
                    'before_sha256':geom['before_sha256'],'after_sha256':geom['after_sha256'],
                    'old_name_bytes':len(geom['from'].encode()),'new_name_bytes':len(geom['to'].encode()),
                    'new_name_sha256':c.sha(geom['to'].encode()),'before_score':list(cost(current)),'after_score':list(cost(candidate)),
                    'source_byte_delta':candidate['source_bytes']-current['source_bytes']})
            current=candidate;selected[pid]=current['sources'][pid]
    assert got['selected']==selected and got['trace']==trace and got['initial_coverage_failures']==failures
    assert got['ledger']==ledger.receipt() and got['proposals']==count and got['accepted']==sum(row['accepted'] is not None for row in trace)
    summary={'proposals':count,'accepted_passes':got['accepted'],'accepted_bindings':len(accepted),
      'distinct_accepted_bindings':len({(r['pid'],r['binding']) for r in accepted}),
      'accepted_binding_occurrences':sum(r['occurrences'] for r in accepted),
      'coverage_failed_proposals':sum(not trial['coverage'] for row in trace for trial in row['trials']),
      'initial_coverage_failures':failures,'changed_programs':sum(selected[pid]!=texts[pid] for pid in texts),
      'source_byte_delta':sum(len(selected[pid].encode())-len(text.encode()) for pid,text in texts.items()),
      'accepted':accepted,'seconds':got['seconds'],'encountered_variants':len(ledger.variants),'ban_count':len(ledger.bans)}
    return selected,ledger,summary


def global_union(ledgers,dictionaries,ban_parser=None):
    variants={};bans=set();origins=[]
    for anchor,ledger in ledgers:
        for key,text in ledger['variants'].items():
            assert key.endswith(':'+c.sha(text.encode())) and (key not in variants or variants[key]==text)
            variants[key]=text
        bans.update(ledger['banned']);origins.append({'anchor':anchor,'ledger_sha256':c.sha(c.canonical(ledger).encode())})
    parser=p.banned if ban_parser is None else ban_parser
    assert bans==parser(variants),'Global source/body union differs from complete encountered variant union'
    illegal={anchor:sorted(c.sha(w.encode()) for w in set(vocab)&bans) for anchor,vocab in dictionaries.items()}
    return {'variants':variants,'banned':sorted(bans),'origins':origins,'illegal_entry_sha256':illegal,'legal':not any(illegal.values())}


def distribution(values):
    values=sorted(values);assert values
    return {'n':len(values),'total':sum(values),'median':statistics.median(values),
      'p90':values[math.ceil(.9*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],
      'worst':values[-1],'within_32':sum(v<=32 for v in values),'within_96':sum(v<=96 for v in values)}


def aggregate(rows,ids,db,decoder):
    selected=[rows[str(pid)] for pid in ids];good=[row for row in selected if row['encodable']]
    n=sum(row['selections'] for row in good);chars=sum(row['single_characters'] for row in good);package=db+sum(row['packet_bytes'] for row in good)
    return {'coverage_complete':len(good)==len(ids),'distribution_scope':'all programs' if len(good)==len(ids) else 'covered programs only; incomplete denominator',
      'problems':len(ids),'covered':len(good),'failed_ids':[str(pid) for pid in ids if not rows[str(pid)]['encodable']],
      'qualified':sum(row['encodable'] and row['qualified_source'] for row in selected),
      'selections':distribution([row['selections'] for row in good]) if good else None,
      'actions':distribution([row['actions'] for row in good]) if good else None,
      'single_character_codes':chars,'single_character_fraction':chars/n if n else None,
      'source_bytes':sum(row['source_bytes'] for row in selected),'framing_bytes':41*len(good),'payload_bits':8*n,'padding_bits':0,
      'package_bytes':package,'package_with_decoder_dependencies':package+decoder,
      'package_scope':'encoded programs only; failed programs retained in coverage denominator'}


def spelling(texts):
    names=Counter();occurrences=Counter()
    for record in c.rewrite.records(texts).values():
        for variable in record['variables']:
            if variable['eligible']:
                key=str(len(variable['name'].encode()));names[key]+=1;occurrences[key]+=len(variable['spans'])
    return {'eligible_binding_spelling_byte_lengths':dict(names),'eligible_occurrence_spelling_byte_lengths':dict(occurrences)}


def measured(folder,view,policy,texts,vocab,bans,config,original,receipts):
    assert c.read(folder/'sources.json')==texts and c.read(folder/'dictionary.json')==vocab
    assert 1<=len(vocab)==len(set(vocab))<=256
    binary=c.analyze.dictionary_bytes(vocab);assert (folder/'dictionary.bin').read_bytes()==binary
    rows={};qualification={};good=set()
    for pid,text in sorted(texts.items()):
        row={'source_sha256':c.sha(text.encode()),'source_bytes':len(text.encode()),'source_byte_delta':len(text.encode())-len(original[pid].encode())}
        try:ids=encode(text,vocab,policy)
        except ValueError:row['encodable']=False
        else:
            blob=(folder/policy/f'{pid}.bin').read_bytes();good.add(pid)
            assert blob==c.analyze.encode(vocab,ids,8) and c.analyze.decode(binary,blob)==text
            row.update(encodable=True,selections=len(ids),actions=len(ids)+1,single_characters=sum(len(vocab[i])==1 for i in ids),
              packet_bytes=len(blob),packet_sha256=c.sha(blob),one_program_package_bytes=len(binary)+len(blob),
              one_program_package_with_decoder_dependencies=len(binary)+len(blob)+config['decoder_dependency_bytes'])
        key=f'{pid}:{row["source_sha256"]}';qualification[pid]=receipts[key];row['qualified_source']=receipts[key]['passed'];rows[pid]=row
    assert {path.stem for path in (folder/policy).glob('*.bin')}==good
    result={'arm':view,'policy':policy,'width':8,'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab),
      'dictionary_bytes':len(binary),'dictionary_sha256':c.hashfile(folder/'dictionary.json'),'dictionary_binary_sha256':c.sha(binary),
      'illegal_entry_sha256':sorted(c.sha(w.encode()) for w in set(vocab)&bans),'spelling':spelling(texts),'per_problem':rows,'qualification':qualification}
    for split,key in (('fit','dev_fit'),('validation','dev_val')):result[split]=aggregate(rows,config['partition'][key],len(binary),config['decoder_dependency_bytes'])
    return result


def complete(arm,config):
    return all(arm[split]['covered']==arm[split]['qualified']==len(config['partition'][key]) for split,key in (('fit','dev_fit'),('validation','dev_val')))


def gates(a,b,config,initial=False):
    ids=list(map(str,config['partition']['dev_val']));coverage=all(complete(x,config) for x in (a,b));clean=all(x['entries']<=256 and not x['illegal_entry_sha256'] for x in (a,b))
    better=sum(a['per_problem'][pid]['encodable'] and (not b['per_problem'][pid]['encodable'] or a['per_problem'][pid]['actions']<b['per_problem'][pid]['actions']) for pid in ids)
    worse=sum(b['per_problem'][pid]['encodable'] and (not a['per_problem'][pid]['encodable'] or a['per_problem'][pid]['actions']>b['per_problem'][pid]['actions']) for pid in ids)
    checks={'coverage_and_qualification':coverage,'legal_dictionary':clean}
    if not coverage:checks.update({key:False for key in ('actions','median','p90','breadth','fraction','package')})
    else:
        x,y=a['validation'],b['validation'];ax,by=x['actions'],y['actions'];xn=x['selections']['total'];yn=y['selections']['total'];xc=x['single_character_codes'];yc=y['single_character_codes']
        checks.update(actions=100*ax['total']<=95*by['total'] if initial else ax['total']<by['total'],
          median=ax['median']<by['median'] if initial else ax['median']<=by['median'],p90=ax['p90']<by['p90'] if initial else ax['p90']<=by['p90'],
          breadth=worse<=25 and (not initial or better>=60),fraction=xc*yn<=yc*xn,package=100*x['package_bytes']<=105*y['package_bytes'])
    return {'checks':checks,'passed':all(checks.values()),'paired':{'better':better,'same':len(ids)-better-worse,'worse':worse}}


def transfer(a,b,config):
    coverage=complete(a,config) and complete(b,config);clean=all(x['entries']<=256 and not x['illegal_entry_sha256'] for x in (a,b))
    assert a['dictionary_binary_sha256']==b['dictionary_binary_sha256']
    checks={'coverage_and_qualification':coverage,'legal_fixed_dictionary':clean}
    if not coverage:checks.update({key:False for key in ('actions','median','p90','strict_fraction','package')})
    else:
        x,y=a['validation'],b['validation'];ax,by=x['actions'],y['actions']
        checks.update(actions=ax['total']<=by['total'],median=ax['median']<=by['median'],p90=ax['p90']<=by['p90'],
          strict_fraction=x['single_character_codes']*y['selections']['total']<y['single_character_codes']*x['selections']['total'],
          package=x['package_bytes']<=y['package_bytes'])
    return {'checks':checks,'passed':all(checks.values()),'scope':'Consumed validation predicates; full fit+validation coverage/qualification and legality prerequisites.',
      'paired_diagnostics':{split:paired_delta(a,b,config['partition'][key],split) for split,key in [('fit','dev_fit'),('validation','dev_val')]}}



def paired_delta(a,b,ids,split):
    rowsa=a['per_problem'];rowsb=b['per_problem'];ids=list(map(str,ids))
    better=sum(rowsa[i]['encodable'] and (not rowsb[i]['encodable'] or rowsa[i]['actions']<rowsb[i]['actions']) for i in ids)
    worse=sum(rowsb[i]['encodable'] and (not rowsa[i]['encodable'] or rowsa[i]['actions']>rowsb[i]['actions']) for i in ids)
    full=all(rowsa[i]['encodable'] and rowsb[i]['encodable'] for i in ids);x=a[split];y=b[split]
    return {'better':better,'same':len(ids)-better-worse,'worse':worse,'full_pair_coverage':full,
      'actions_delta':x['actions']['total']-y['actions']['total'] if full else None,
      'selections_delta':x['selections']['total']-y['selections']['total'] if full else None,
      'character_codes_delta':x['single_character_codes']-y['single_character_codes'] if full else None,
      'character_fraction_delta':x['single_character_fraction']-y['single_character_fraction'] if full else None,
      'raw_package_delta':x['package_bytes']-y['package_bytes'] if full else None,
      'decoder_inclusive_package_delta':x['package_with_decoder_dependencies']-y['package_with_decoder_dependencies'] if full else None,
      'source_bytes_delta':x['source_bytes']-y['source_bytes']}

def check_seal(folder,name,files,flag):
    value=c.read(folder/name)
    assert set(value)=={'files',flag} and value[flag] is False and set(value['files'])==set(files)
    assert all(c.hashfile(folder/rel)==digest for rel,digest in value['files'].items())


def parser_receipt(got,phase,row,config,banproof,previous=None):
    """Rebuild successful request counts/bytes from independently parsed variants."""
    keys=('schema phase complete implementation_sha256 limits worker_pid worker_process_group '
          'worker_core_affinity service_pid service_process_group service_core_affinity '
          'started_monotonic finished_monotonic absolute_deadline spawn_seconds request_seconds '
          'close_seconds lifetime_seconds requests_attempted requests_completed failed_requests '
          'request_bytes_total response_bytes_total max_request_bytes max_response_bytes '
          'service_peak_rss_kib_observed closed returncode error_type').split()
    assert set(got)==set(keys)
    assert got['schema']=='gamma.persistent-spelling-parser-receipt.v1' and got['phase']==phase
    assert got['complete'] is True and got['closed'] is True and got['error_type'] is None
    assert got['implementation_sha256']==config['parser']['implementation_sha256']
    assert got['limits']==config['parser']['limits']
    for name in ('worker_pid','worker_process_group','service_pid','service_process_group'):
        assert type(got[name]) is int and got[name]>0
    assert got['worker_pid']!=got['service_pid']
    assert got['worker_process_group']==got['service_process_group']
    affinity=config['arm_cores'][row['anchor']]
    assert got['worker_core_affinity']==got['service_core_affinity']==affinity
    assert type(got['returncode']) is int and got['returncode'] in (0,-9)
    deadline=row['anchor_deadline'] if phase=='fit' else previous['anchor_deadline']
    assert got['absolute_deadline']==deadline
    for name in ('started_monotonic','finished_monotonic','absolute_deadline'):
        number(got[name],1e15)
    assert row['started_monotonic']<=got['started_monotonic']<=got['finished_monotonic']<=row['finished_monotonic']<=deadline
    assert got['lifetime_seconds']==got['finished_monotonic']-got['started_monotonic']
    for name in ('spawn_seconds','request_seconds','close_seconds','lifetime_seconds'):
        number(got[name],row['worker_seconds'])
    assert got['spawn_seconds']+got['request_seconds']+got['close_seconds']<=got['lifetime_seconds']
    for name in ('requests_attempted','requests_completed','failed_requests','request_bytes_total',
                 'response_bytes_total','max_request_bytes','max_response_bytes','service_peak_rss_kib_observed'):
        assert type(got[name]) is int and got[name]>=0
    ledger=row['ledger'];encounters=ledger['encounters']
    if previous is not None:
        prefix=previous['ledger']['encounters']
        assert encounters[:len(prefix)]==prefix
        encounters=encounters[len(prefix):]
    sizes=[];replies=[];ident=0
    for encounter in encounters:
        variants=encounter['variant_keys'];assert variants and len(set(variants))==len(variants)
        for offset in range(0,len(variants),512):
            chunk=variants[offset:offset+512];ident+=1
            texts={key:ledger['variants'][key] for key in chunk}
            banproof.banned(texts)  # exact key/hash/text check, independently parsed
            sizes.append(len(json.dumps({'id':ident,'texts':texts},separators=(',',':'),ensure_ascii=True).encode()))
            bodies={key:banproof.bodies[key] for key in chunk}
            replies.append(len(json.dumps({'id':ident,'ok':True,'bodies':bodies},separators=(',',':'),ensure_ascii=False).encode())+1)
    assert got['requests_attempted']==got['requests_completed']==ident and got['failed_requests']==0
    assert got['request_bytes_total']==sum(sizes) and got['response_bytes_total']==sum(replies)
    assert got['max_request_bytes']==max(sizes,default=0)<=got['limits']['request_bytes']
    assert got['max_response_bytes']==max(replies,default=0)<=got['limits']['response_bytes']
    assert 0<got['service_peak_rss_kib_observed']<=config['limits']['address_space_bytes']//1024
    return dict(got, memory_scope='Worker and observed service peaks are separate; their sum is not a simultaneous aggregate peak.',
                sum_of_separate_observed_peaks_kib=row['peak_rss_kib']+got['service_peak_rss_kib_observed'])


def public_inputs(config):
    """Reconstruct passing ID/hash authorities from hash-bound public evidence."""
    parents={};contracts={}
    for anchor in ANCHORS:
        binding=config['parent_evidence'][anchor]
        parents[anchor]=c.checked_read(c.LIT,binding)
        path=c.LIT/binding['contract_path'];assert c.hashfile(path)==binding['contract_sha256']
        contracts[anchor]=c.read(path)
    e43=parents['43N'];assert e43==parents['43W']
    assert e43['contract_sha256']==config['parent_evidence']['43N']['contract_sha256']
    assert not e43['failed_arms'] and e43['exit_codes']=={'nonregress':0,'unweighted':0}
    assert sorted(e43['replayed_arms'])==['nonregress','unweighted'] and e43['all_sources_qualified_by_receipt'] is True
    e24=parents['24'];optional=next(a for a in e24['arms'] if a['arm']=='optional')
    assert e24['contract_sha256']==config['parent_evidence']['24']['contract_sha256']
    assert contracts['24']['partition']==config['partition']
    assert contracts['43N']['seed']['relative_path']==contracts['24']['seed_relative_path']
    for split,name in [('fit','fit-sources.json'),('all','sources.json')]:
        rel=contracts['24']['seed_relative_path']+'/'+name
        digest=contracts['24']['private_files'][rel]
        assert contracts['43N']['seed']['private_sha256'][name]==digest
        assert config['sources'][split]=={'path':rel,'sha256':digest}
    assert optional['dictionary_sha256']==config['dictionaries']['24']['sha256']==contracts['43N']['seed']['dictionary_sha256']
    assert optional['dictionary_binary_sha256']==config['dictionaries']['24']['binary_sha256']
    for anchor in ('43N','43W'):
        arm=e43['arms'][config['parent_evidence'][anchor]['arm']]
        assert arm['dictionary_sha256']==config['dictionaries'][anchor]['sha256'] and not arm['illegal_entry_sha256']
        assert arm['coverage']=={'fit':len(config['partition']['dev_fit']),'validation':len(config['partition']['dev_val'])}
        assert arm['decoded']==sum(map(len,config['partition'].values()))
    qpath=c.LIT/contracts['43N']['qualification_receipt']
    assert c.hashfile(qpath)==contracts['43N']['qualification_receipt_sha256']
    q13=next(a for a in c.read(qpath)['arms'] if a['arm']=='scope_joint' and a['width']==8)
    ids={str(pid) for values in config['partition'].values() for pid in values}
    assert len(ids)==sum(map(len,config['partition'].values())) and set(optional['per_problem'])==set(q13['per_problem'])==ids
    known={};sourceq={}
    for pid in sorted(ids):
        h=q13['per_problem'][pid]['source_sha256'];q=q13['qualification'][pid]
        assert h==optional['per_problem'][pid]['source_sha256'] and q['passed'] is True
        assert optional['per_problem'][pid]['encodable'] and optional['per_problem'][pid]['qualified_source']
        sourceq[pid]={'source_sha256':h,'passed':True}
        known[f'{pid}:{h}']={'passed':True,'reused':True,'receipt':q,'source_arm':'item24/item43 original scope_joint','source_policy':'canonical'}
    assert sourceq==config['source_qualification']
    path=c.LIT/'atomic-naming-entry-v1/evidence/results.json'
    assert c.hashfile(path)==config['code_hashes'][str(path.relative_to(c.LIT))]
    e41=c.read(path);assert e41['complete'] is True and e41['independent_replay'] is True
    assert e41['contract_sha256']==c.hashfile(c.LIT/'atomic-naming-entry-v1/contract.json')
    for arm in e41['arms']:
        assert set(arm['per_problem'])==ids
        for pid,row in arm['per_problem'].items():
            q=arm['qualification'][pid]
            if q['passed']:
                known.setdefault(f'{pid}:{row["source_sha256"]}',{'passed':True,'reused':True,'receipt':q,
                    'source_arm':'item41/'+arm['arm'],'source_policy':arm['policy']})
    assert known==config['known_receipts'],'Reused qualifications must match passing parent ID/hash receipts exactly'
    standing=c.checked_read(c.LIT,config['standing_reference_evidence'])
    assert standing['private_results_sha256']==config['standing_reference_evidence']['private_results_sha256']
    references={}
    for name in ('R','seed13','best24','N','NCP'):
        for policy in POLICIES:
            rows=[a for a in standing['arms'] if a['arm']==name and a['policy']==policy];assert len(rows)==1
            arm=rows[0];assert set(arm['per_problem'])==ids
            for split,key in (('fit','dev_fit'),('validation','dev_val')):
                assert arm[split]['problems']==len(config['partition'][key])
                expected=aggregate(arm['per_problem'],config['partition'][key],arm['dictionary_bytes'],config['decoder_dependency_bytes'])
                # Older published schema has extra diagnostics; require all common accounting fields.
                assert all(arm[split][k]==v for k,v in expected.items() if k in arm[split])
            references[name,policy]=arm
    return known,references,parents


def apply_payload(row,phase):
    extras={'anchor','worker_seconds','peak_rss_kib'}
    extras.update({'menu','anchor_deadline'} if phase=='fit' else {'cumulative_worker_seconds'})
    # Absolute timestamps, when retained, are checked separately below.
    extras.update({'started_monotonic','finished_monotonic','anchor_deadline'})
    return {k:v for k,v in row.items() if k not in extras}


def qualify_replay(folder,config,private,known,expected_summary):
    expected={f'{pid}:{c.sha(text.encode())}':(pid,text) for texts in private.values() for pid,text in texts.items()
              if f'{pid}:{c.sha(text.encode())}' not in known}
    q=c.read(folder/'qualification-private.json')
    assert set(q)=={'complete','expected_keys','receipts','failures'} and q['complete'] is True
    assert q['expected_keys']==sorted(expected) and set(q['receipts'])==set(expected) and set(q['failures'])<=set(expected)
    raw=folder/'raw-qualification'
    assert ({p.name for p in raw.iterdir()} if raw.exists() else set())=={key.replace(':','-') for key in expected}
    receipts=dict(known)
    for key,(pid,text) in expected.items():
        fresh=q['receipts'][key]
        assert fresh['reused'] is False and type(fresh['passed']) is bool
        assert type(fresh['checks_passed']) is int and type(fresh['cases']) is int and 0<=fresh['checks_passed']<=fresh['cases']
        checked,bad=c.prior('report').replay_qualification(folder,config,pid,text,fresh)
        assert checked==fresh
        assert (q['failures'].get(key)==(bad or {'passed':False})) if not fresh['passed'] else key not in q['failures']
        receipts[key]=checked
    summary={'distinct_new_sources':len(expected),'passed':sum(r['passed'] for r in q['receipts'].values()),
      'checks':sum(r['cases'] for r in q['receipts'].values()),'checks_passed':sum(r['checks_passed'] for r in q['receipts'].values()),'failed_sources':len(q['failures'])}
    assert summary==expected_summary
    return receipts,summary


_external_banproof=None

def external_original_bans(texts):
    assert _external_banproof is not None, 'External comparator requires active independent replay'
    variants={f'{pid}:{c.sha(text.encode())}':text for pid,text in texts.items()}
    _external_banproof.extend(variants)
    return _external_banproof.banned(variants)


def current_best(binding,config,index):
    import current_best as adapter
    import sys
    return adapter.resolve(binding,config,index,sys.modules[__name__])


def anchor_current_best(binding,config,index):
    if binding is None:return None,{'resolved':False,'reason':'No record-time current-best binding; no replacement verdict.'}
    assert set(binding)=={'recorded_commit','recorded_label','evidence','comparison'}
    assert isinstance(binding['recorded_commit'],str) and len(binding['recorded_commit'])>=7 and isinstance(binding['recorded_label'],str) and binding['recorded_label']
    comparison=binding['comparison'];assert set(comparison)=={'kind','anchor'} and comparison['kind']=='anchor'
    anchor=comparison['anchor'];assert anchor in ANCHORS
    expected=config['parent_evidence'][anchor]
    assert binding['evidence']=={k:expected[k] for k in ('path','sha256')}
    assert c.hashfile(c.LIT/expected['path'])==expected['sha256']
    return {policy:index[anchor+'-U',policy] for policy in POLICIES},{'resolved':True,**binding,
      'binding_sha256':c.sha(c.canonical(binding).encode()),'comparison_scope':'Exact parent source/dictionary identity, independently re-encoded under both fixed policies.'}


def decisions(arms,references,config,best_binding=None):
    index={(a['arm'],a['policy']):a for a in arms};best,bestmeta=current_best(best_binding,config,index)
    verdicts={}
    for anchor in ANCHORS:
        perpolicy={}
        for policy in POLICIES:
            candidate=index[anchor+'-S',policy];untouched=index[anchor+'-U',policy]
            comparison={name:gates(candidate,references[name,policy],config,initial=name=='R') for name in ('R','seed13','best24','N','NCP')}
            comparison['record_time_best']=None if best is None else gates(candidate,best[policy],config)
            transferred=transfer(candidate,untouched,config)
            ready=best is not None and transferred['passed'] and all(v['passed'] for v in comparison.values())
            perpolicy[policy]={'transfer':transferred,'comparisons':comparison,'successor':ready}
        verdicts[anchor+'-S']={'policies':perpolicy,'transfer':all(x['transfer']['passed'] for x in perpolicy.values()),
          'successor':all(x['successor'] for x in perpolicy.values()),'replacement_status':'resolved' if best is not None else 'unresolved'}
    passing=[label for label,v in verdicts.items() if v['successor']]
    passing.sort(key=lambda label:(index[label,'canonical']['validation']['actions']['total'],
      index[label,'canonical']['validation']['package_with_decoder_dependencies'],label))
    predictions={'P1':all(complete(a,config) and not a['illegal_entry_sha256'] for a in arms),
      'P2':any(all(complete(index[anchor+'-S',policy],config) and complete(index[anchor+'-U',policy],config)
          and index[anchor+'-S',policy]['validation']['actions']['total']==index[anchor+'-U',policy]['validation']['actions']['total']
          and transfer(index[anchor+'-S',policy],index[anchor+'-U',policy],config)['checks']['strict_fraction'] for policy in POLICIES) for anchor in ANCHORS),
      'P3':any(verdicts[a+'-S']['transfer'] for a in ('43N','43W')),'P4':not passing if best is not None else None}
    gaps={}
    for arm in arms:
        rows=arm['per_problem'];overall=aggregate(rows,[*config['partition']['dev_fit'],*config['partition']['dev_val']],arm['dictionary_bytes'],config['decoder_dependency_bytes'])
        covered=overall['coverage_complete'];selections=overall['selections']
        gaps[arm['arm']+'/'+arm['policy']]={'admission_400_of_500':False,'admission_scope':'400 reused development sources; population admission/500 and independent confirmation unestablished.',
          'entries_at_most_256':arm['entries']<=256,'median_selections_at_most_32':covered and selections['median']<=32,
          'p95_selections_at_most_96':covered and selections['p95']<=96,'character_fraction_at_most_10_percent':covered and 10*overall['single_character_codes']<=selections['total'],
          'zero_whole_body_entries':not arm['illegal_entry_sha256'],'aggregate_400':overall,'M1_qualified':False}
    return {'verdicts':verdicts,'record_time_best':bestmeta,'ranked_passing_candidates':passing,
      'selected_successor':passing[0] if passing else None,'predictions':predictions,'M1_gaps':gaps}


def replay(folder,config,best_binding=None,deadline=None):
    deadline=time.monotonic()+SECONDS if deadline is None else deadline
    folder=Path(folder);c.verify_public(config)
    assert sum(Path(path).stat().st_size for path in config['decoder_dependencies'])==config['decoder_dependency_bytes']
    assert not list(folder.rglob('failure.json')),'Execution failure dominates completed artifacts'
    assert c.read(folder/'status.json')=={'phase':'complete','complete':True}
    supervisor=c.read(folder/'supervisor-receipt.json')
    assert supervisor['complete'] is True and supervisor['outer_timeout'] is False and type(supervisor['exit_code']) is int and supervisor['exit_code']==0
    elapsed=number(supervisor['elapsed'],config['limits']['overall_seconds']+config['limits']['cleanup_seconds']+1)
    raw=c.read(folder/'results.json');assert raw['complete'] is True and raw['contract_sha256']==c.hashfile(c.HERE/'contract.json')
    number(raw['seconds'],min(elapsed,config['limits']['overall_seconds'])+1)
    known,references,parents=public_inputs(config)
    dictionaries={anchor:c.dictionary(config['work'],anchor,config) for anchor in ANCHORS}
    for anchor,binding in config['dictionaries'].items():
        if binding.get('parent_seal'):
            seal=c.read(Path(config['work'])/binding['parent_seal'])
            assert seal['dictionary_sha256']==binding['sha256'] and seal['validation_loaded'] is False
    fitbase=c.checked_read(config['work'],config['sources']['fit']);c.check_sources(fitbase,config['partition']['dev_fit'],config)
    allfit=c.read(folder/'all-fit-sealed.json')
    assert set(allfit)=={'validation_loaded','arms','global_ledger_sha256'} and allfit['validation_loaded'] is False
    assert allfit['arms']==raw['fit_summaries'] and [r['anchor'] for r in allfit['arms']]==list(ANCHORS)
    fitrows={};fitselected={};fitledgers={};search={}
    banproof=BanReplay(c.LIT/'tail-search-v1/structure.cjs',deadline,c.HardDeadline)
    # Read only sealed fit variants here; validation remains behind fit replay.
    for anchor in ANCHORS:
        sub=folder/'fit'/anchor
        check_seal(sub,'fit-seal.json',['fit.json','menu.json','fit-parser.json'],'validation_loaded')
        banproof.extend(c.read(sub/'fit.json')['ledger']['variants'])
    for anchor,fs in zip(ANCHORS,allfit['arms']):
        sub=folder/'fit'/anchor;check_seal(sub,'fit-seal.json',['fit.json','menu.json','fit-parser.json'],'validation_loaded')
        fit=c.read(sub/'fit.json');fitrows[anchor]=fit;assert fit['anchor']==anchor
        assert fs=={'anchor':anchor,'seconds':fit['worker_seconds'],'proposals':fit['proposals'],'accepted':fit['accepted'],'fit_seal_sha256':c.hashfile(sub/'fit-seal.json'),'anchor_deadline':fit['anchor_deadline']}
        number(fit['worker_seconds'],config['limits']['worker_seconds']);number(fit['anchor_deadline'],1e15)
        number(fit['peak_rss_kib'],config['limits']['address_space_bytes']//1024)
        assert fit['seconds']<=fit['worker_seconds']
        number(fit['started_monotonic'],1e15);number(fit['finished_monotonic'],1e15)
        assert fit['worker_seconds']==fit['finished_monotonic']-fit['started_monotonic']
        assert fit['anchor_deadline']==fit['started_monotonic']+config['limits']['worker_seconds'] and fit['finished_monotonic']<=fit['anchor_deadline']
        service=parser_receipt(c.read(sub/'fit-parser.json'),'fit',fit,config,banproof)
        menu=derive_menu(fitbase,dictionaries[anchor]);assert fit['menu']==c.read(sub/'menu.json')==menu
        selected,ledger,diagnostic=replay_apply(apply_payload(fit,'fit'),fitbase,dictionaries[anchor],menu,dictionaries,
          proposal_cap=config['proposal_cap'],worker_seconds=config['limits']['worker_seconds'],ban_parser=banproof.banned)
        fitselected[anchor]=selected;fitledgers[anchor]=ledger.receipt();search[anchor]={'fit':diagnostic,'menu_sha256':c.hashfile(sub/'menu.json'),
          'name_count':len(menu['names']),'context_count':len(menu['contexts']),'fit_worker_seconds':fit['worker_seconds'],'fit_peak_rss_kib':fit['peak_rss_kib']}
        search[anchor]['fit_parser']=service
    gf=global_union([(anchor,fitledgers[anchor]) for anchor in ANCHORS],dictionaries,banproof.banned)
    assert gf==c.read(folder/'global-fit-ledger.json') and gf['legal'] is True
    assert allfit['global_ledger_sha256']==c.hashfile(folder/'global-fit-ledger.json')
    # Combined carrier contents and hash are deferred until every fit trace/seal is verified.
    original=c.checked_read(config['work'],config['sources']['all'])
    c.check_sources(original,[*config['partition']['dev_fit'],*config['partition']['dev_val']],config)
    assert fitbase=={str(pid):original[str(pid)] for pid in config['partition']['dev_fit']}
    valbase={str(pid):original[str(pid)] for pid in config['partition']['dev_val']}
    for binding in config.get('deferred_parent_artifacts',[]):c.checked_read(config['work'],binding)
    allval=c.read(folder/'all-validation-sealed.json')
    assert set(allval)=={'qualification_started','arms','global_ledger_sha256'} and allval['qualification_started'] is False
    assert allval['arms']==raw['validation_summaries'] and [r['anchor'] for r in allval['arms']]==list(ANCHORS)
    private={};valledgers={};unqualified={}
    for anchor in ANCHORS:
        sub=folder/'fit'/anchor
        check_seal(sub,'validation-seal.json',['validation.json','unqualified-arms.json','validation-parser.json'],'qualification_started')
        banproof.extend(c.read(sub/'validation.json')['ledger']['variants'])
    for anchor,vs in zip(ANCHORS,allval['arms']):
        sub=folder/'fit'/anchor;check_seal(sub,'validation-seal.json',['validation.json','unqualified-arms.json','validation-parser.json'],'qualification_started')
        val=c.read(sub/'validation.json');fit=fitrows[anchor];assert val['anchor']==anchor
        assert vs=={'anchor':anchor,'seconds':val['worker_seconds'],'proposals':val['proposals'],'accepted':val['accepted'],'validation_seal_sha256':c.hashfile(sub/'validation-seal.json')}
        number(val['worker_seconds'],config['limits']['worker_seconds']);number(val['cumulative_worker_seconds'],config['limits']['worker_seconds'])
        number(val['peak_rss_kib'],config['limits']['address_space_bytes']//1024)
        assert val['cumulative_worker_seconds']==fit['worker_seconds']+val['worker_seconds'] and val['seconds']<=val['worker_seconds']
        number(val['started_monotonic'],1e15);number(val['finished_monotonic'],1e15)
        assert val['started_monotonic']>=fit['finished_monotonic'] and val['finished_monotonic']<=fit['anchor_deadline']
        assert val['worker_seconds']==val['finished_monotonic']-val['started_monotonic']
        assert val['proposals']+fit['proposals']<=config['proposal_cap']
        service=parser_receipt(c.read(sub/'validation-parser.json'),'validation',val,config,banproof,fit)
        selected,ledger,diagnostic=replay_apply(apply_payload(val,'validation'),valbase,dictionaries[anchor],fit['menu'],dictionaries,
          fitledgers[anchor],'validation',config['proposal_cap']-fit['proposals'],config['limits']['worker_seconds'],ban_parser=banproof.banned)
        private[anchor+'-U']=original;private[anchor+'-S']={**fitselected[anchor],**selected};valledgers[anchor]=ledger.receipt()
        unqualified[anchor]=c.read(sub/'unqualified-arms.json')
        search[anchor].update(validation=diagnostic,validation_worker_seconds=val['worker_seconds'],cumulative_worker_seconds=val['cumulative_worker_seconds'],validation_peak_rss_kib=val['peak_rss_kib'])
        search[anchor]['validation_parser']=service
    gv=global_union([(anchor,valledgers[anchor]) for anchor in ANCHORS],dictionaries,banproof.banned)
    assert gv==c.read(folder/'global-ledger.json') and gv['legal'] is True
    assert allval['global_ledger_sha256']==raw['global_ledger_sha256']==c.hashfile(folder/'global-ledger.json')
    # Only after both barriers: open cases/baselines/raw observations for exact rejudge.
    receipts,fresh=qualify_replay(folder,config,private,known,raw['fresh_qualification_summary'])
    arms=[]
    for anchor in ANCHORS:
        group=[]
        for suffix in ('U','S'):
            view=anchor+'-'+suffix
            for policy in POLICIES:
                measured_arm=measured(folder/'artifacts'/view,view,policy,private[view],dictionaries[anchor],set(gv['banned']),config,original,receipts)
                arms.append(measured_arm)
                before={k:v for k,v in measured_arm.items() if k not in ('fit','validation','qualification')}
                before['per_problem']={pid:{k:v for k,v in row.items() if k!='qualified_source'} for pid,row in measured_arm['per_problem'].items()}
                group.append(before)
        assert unqualified[anchor]==group
    assert raw['arms']==arms and raw['decoded_packets']==sum(a['fit']['covered']+a['validation']['covered'] for a in arms)
    global _external_banproof
    _external_banproof=banproof
    try:verdict=decisions(arms,references,config,best_binding)
    finally:_external_banproof=None
    return {'complete':True,'independent_replay':True,'promotion_allowed':False,'contract_sha256':raw['contract_sha256'],
      'private_results_sha256':c.hashfile(folder/'results.json'),'arms':arms,'search':search,**verdict,
      'fresh_qualification_summary':fresh,'decoded_packets':raw['decoded_packets'],'runner_seconds':raw['seconds'],'supervisor_seconds':elapsed,
      'report_ban_replay':banproof.receipt(),
      'global_ledger_sha256':raw['global_ledger_sha256'],'global_variant_count':len(gv['variants']),'global_ban_count':len(gv['banned']),
      'parent_evidence':config['parent_evidence'],'parent_dictionary_bindings':config['dictionaries'],
      'standing_reference_evidence':config['standing_reference_evidence'],'decoder_dependency_bytes':config['decoder_dependency_bytes'],
      'offline_encoder_bytes':config.get('offline_encoder_bytes'),'model_bytes':0,'training_steps':0,
      'runtime_footprint':'Installed runtime footprint unmeasured.','peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'production_peak_rss_kib':number(raw['peak_rss_kib'],config['limits']['address_space_bytes']//1024),
      'scope':'Consumed development spelling transfer with fixed ordered dictionaries; no independent confirmation, M1 qualification or promotion.',
      'replay_scope':'All menus, every offered fit/validation proposal, exact complete-ID policy packets, accumulated cross-arm bans, and fresh raw strict observations independently replayed. Old parser calls are batched in groups of16 on sealed phase variants; cached per-key/hash bans are consumed in the independently reconstructed encounter order. No persistent execution parser is used by reporting.'}


def markdown(result):
    lines=['# Fixed-dictionary spelling transfer','',result['scope'],'',
      '| View | Policy | Split | Covered | Qualified | Actions | Median | p90 | C/N | Raw package | Decoder-inclusive |',
      '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        for split in ('fit','validation'):
            row=arm[split];full=row['coverage_complete'];actions=row['actions'] or {}
            lines.append(f"| {arm['arm']} | {arm['policy']} | {split} | {row['covered']}/{row['problems']} | {row['qualified']} | {actions.get('total') if full else 'partial'} | {actions.get('median') if full else None} | {actions.get('p90') if full else None} | {row['single_character_fraction'] if full else None} | {row['package_bytes']} | {row['package_with_decoder_dependencies']} |")
    lines+=['','Actions include Finish. Full dictionary, framing and payload are charged once per cohort; decoder-inclusive totals add the pinned decoder inventory. Partial costs describe covered programs only and cannot satisfy readiness.','']
    for label,row in result['verdicts'].items():
        lines.append(f"- {label}: transfer={row['transfer']}; successor={row['successor']}; record-time comparison={row['replacement_status']}.")
        for policy,view in row['policies'].items():
            failed=['transfer:'+k for k,v in view['transfer']['checks'].items() if not v]
            for ref,comparison in view['comparisons'].items():
                failed.extend([ref+':unresolved'] if comparison is None else [ref+':'+k for k,v in comparison['checks'].items() if not v])
            lines.append('  '+policy+' failed predicates: '+(', '.join(failed) or 'none')+'.')
    lines+=['','Predeclared ranking winner: '+str(result['selected_successor'])+'. This is a development comparison, with promotion prohibited.',
      '','Predictions: '+', '.join(f'{key}={value}' for key,value in result['predictions'].items())+'.','',result['replay_scope'],'',
      'Transfer/readiness predicates use the consumed validation 100, with full400 coverage, qualification and legality prerequisites. Fit metrics are separate diagnostics. Source-byte deltas and spelling-length counts distinguish character-label reclassification from action or source-size improvements.',
      '','M1 thresholds remain unchanged; its admission and confirmation gaps remain open. Finite qualification is not a semantic equivalence proof. No protected sources or final heldout are used.','']
    return '\n'.join(lines)


def failure_guard(deadline):
    if deadline is not None:
        remaining=deadline-time.monotonic()
        if remaining<=0:raise c.HardDeadline('Failure publication deadline')
        signal.setitimer(signal.ITIMER_REAL,remaining)


def remove_success(output,deadline=None):
    for name in ('results.json','REPORT.md'):
        failure_guard(deadline)
        try:(Path(output)/name).unlink(missing_ok=True)
        except Exception:pass


def withdraw(output,error,deadline=None):
    # An enclosing supervisor may own the alarm. Never replace or swallow it
    # unless main explicitly supplies its one absolute emergency deadline.
    output=Path(output);remove_success(output,deadline)
    failed={'complete':False,'independent_replay':False,'promotion_allowed':False,'verdicts':None,'selected_successor':None,
      'predictions':{key:None for key in ('P1','P2','P3','P4')},'error_type':type(error).__name__,
      'reason':'Incomplete execution, replay or publication; no verdict.'}
    for name,payload in [('REPORT.md','# Fixed-dictionary spelling transfer\n\n**No verdict.** Incomplete execution, replay or publication; previous success withdrawn.\n'),
                         ('results.json',json.dumps(failed,sort_keys=True,indent=2)+'\n')]:
        path=output/name
        try:
            failure_guard(deadline);output.mkdir(parents=True,exist_ok=True)
            temporary=path.with_name(path.name+'.withdraw.tmp')
            failure_guard(deadline);temporary.write_text(payload)
            failure_guard(deadline);temporary.replace(path)
        except Exception:
            failure_guard(deadline)
            try:path.unlink(missing_ok=True)
            except Exception:pass
    failure_guard(deadline)
    return failed


def publish(folder,config,output,best_binding=None,started=None):
    started=time.monotonic() if started is None else started;output=Path(output)
    try:
        result=replay(folder,config,best_binding,started+config['limits']['report_seconds']);result['replay_seconds']=time.monotonic()-started
        prose=markdown(result);output.mkdir(parents=True,exist_ok=True)
        # No context-manager cleanup after an expired one-shot alarm. Failed
        # staging artifacts remain private; the explicit emergency path owns I/O.
        stage=Path(tempfile.mkdtemp(prefix='.report-stage-',dir=output))
        c.write(stage/'results.json',result);(stage/'REPORT.md').write_text(prose)
        number(time.monotonic()-started,config['limits']['report_seconds'])
        (stage/'REPORT.md').replace(output/'REPORT.md');(stage/'results.json').replace(output/'results.json')
        number(time.monotonic()-started,config['limits']['report_seconds'])
        stage.rmdir()
        number(time.monotonic()-started,config['limits']['report_seconds'])
        return result
    except BaseException as error:
        emergency=min(time.monotonic()+10,started+config['limits']['report_seconds']+10)
        error._gamma_failure_deadline=emergency
        try:remove_success(output,emergency)
        except BaseException as cleanup_error:
            cleanup_error._gamma_failure_deadline=emergency
            raise
        raise


def main(folder,output,best_path=None):
    started=time.monotonic();folder=Path(folder).resolve();output=Path(output).resolve();safe=False
    def expired(*_):raise c.HardDeadline('Whole independent report deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        # Refuse input overlap before any output mutation; outer supervisor owns
        # the process group and withdraws its separate final publication on error.
        assert output!=folder and folder not in output.parents and output not in folder.parents
        assert c.LIT not in output.parents and output!=c.LIT
        safe=True
        resource.setrlimit(resource.RLIMIT_AS,(MEMORY,MEMORY));os.sched_setaffinity(0,{0,1,2,3})
        config=c.read(c.HERE/'contract.json');c.verify_public(config)
        assert config['limits']['report_seconds']==SECONDS and config['limits']['address_space_bytes']==MEMORY
        assert config['all_cores']==[0,1,2,3]
        # Parent/private inputs must never be overwritten by a report destination.
        work=Path(config['work']).resolve();safe=False
        for binding in [*config['sources'].values(),*config['dictionaries'].values()]:
            source=(work/binding['path']).resolve();assert output!=source and output not in source.parents
        safe=True
        binding=None if best_path is None else c.read(Path(best_path))
        number(time.monotonic()-started,SECONDS)
        signal.setitimer(signal.ITIMER_REAL,max(.001,SECONDS-(time.monotonic()-started)))
        result=publish(folder,config,output,binding,started)
        number(time.monotonic()-started,SECONDS);signal.setitimer(signal.ITIMER_REAL,0)
        return result
    except BaseException as error:
        if safe:withdraw(output,error,getattr(error,'_gamma_failure_deadline',min(time.monotonic()+10,started+SECONDS+10)))
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--record-time-best',type=Path);args=ap.parse_args();main(args.run,args.output,args.record_time_best)
