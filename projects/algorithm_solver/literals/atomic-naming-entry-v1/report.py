"""Independent packet, accepted-transition, ban and qualification receipt replay.

No optimization, qualification execution, source search or publication of private
strings. The source geometry checker is the pinned existing binding authority;
the segmentation DP and scalar accounting below are separate implementations.
"""
import argparse
from collections import Counter, defaultdict
import math
import json
import os
import resource
import signal
from pathlib import Path
import statistics
import time
import tempfile
import core as c

POLICIES=('canonical','shortest_min_char')
ARMS=('D','S','A','J')


def seconds(value, maximum):
    assert type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum
    return value


def encode(text,vocab,policy='shortest_min_char'):
    """Forward DAG DP, retaining exact full ID tuples for independent tie replay."""
    assert policy in POLICIES and len(vocab)==len(set(vocab)) and all(vocab)
    by_first=defaultdict(list)
    for i,word in enumerate(vocab):by_first[word[0]].append((i,word))
    best=[None]*(len(text)+1);best[0]=(0,0,())
    for start,char in enumerate(text):
        if best[start] is None:continue
        n,chars,ids=best[start]
        for i,word in by_first[char]:
            if text.startswith(word,start):
                end=start+len(word)
                got=(n+1,chars+(len(word)==1 if policy=='shortest_min_char' else 0),ids+(i,))
                if best[end] is None or got<best[end]:best[end]=got
    if best[-1] is None:raise ValueError('unrepresentable')
    return list(best[-1][2])


def state(texts,vocab):
    assert vocab==c.order(vocab) and 1<=len(vocab)<=256
    plans={pid:[vocab[i] for i in encode(text,vocab)] for pid,text in texts.items()}
    n=sum(map(len,plans.values()));chars=sum(len(w)==1 for plan in plans.values() for w in plan)
    db=len(c.analyze.dictionary_bytes(vocab))
    return dict(sources=texts,vocab=vocab,plans=plans,N=n,C=chars,package_bytes=db+41*len(texts)+n,
                dictionary_bytes=db,source_bytes=sum(len(t.encode()) for t in texts.values()))


def cost(s):return s['N'],s['C'],s['package_bytes']
def tie(s):return cost(s),s['source_bytes'],tuple(s['vocab']),tuple(sorted(s['sources'].items()))
def brief(s):return {k:s[k] for k in ('N','C','package_bytes','dictionary_bytes','source_bytes')}|{'entries':len(s['vocab'])}


def check_geometry(group,texts,records):
    assert set(group['updates'])=={g['pid'] for g in group['geometry']}
    assert len(group['geometry'])==len(group['updates'])
    for g in group['geometry']:
        pid=g['pid'];text=texts[pid];record=records[pid];variable=record['variables'][g['binding']]
        assert text.isascii() and not record['unsafe'] and variable['eligible']
        assert g['from']==variable['name'] and g['to']==group['target'] and g['from']!=g['to']
        assert g['spans']==variable['spans'] and g['before_sha256']==c.sha(text.encode())
        colors=[v['name'] for v in record['variables']];colors[g['binding']]=g['to'];assert c.rewrite.legal(record,colors)
        actual=text
        for a,b in reversed(sorted(g['spans'])):
            assert text[a:b]==g['from'];actual=actual[:a]+g['to']+actual[b:]
        assert actual==group['updates'][pid] and c.sha(actual.encode())==g['after_sha256']


class Ledger:
    """Rebuild encounter order, deduplication and exact cumulative bans."""
    def __init__(self):self.variants={};self.encounters=[];self.bans=set();self.pending=None;self.new={}
    def encounter(self,texts,phase):
        keys=[]
        for pid,text in texts.items():
            key=f'{pid}:{c.sha(text.encode())}'
            if key not in self.variants:self.variants[key]=text;self.new[key]=text;keys.append(key)
        if keys:self.encounters.append({'phase':phase,'variant_keys':keys})
    def flush(self):
        if self.new:self.bans.update(c.banned(self.new));self.new={}
    def check(self,stored):
        self.flush()
        assert stored=={'variants':self.variants,'banned':sorted(self.bans),'encounters':self.encounters,'last_rendered_group':self.pending}


def replay_fit(got,texts,initial,limits):
    assert got['complete'] is True and got['arm'] in ARMS
    arm=got['arm'];current=state(texts,initial);mandatory={w for w in initial if len(w)==1}
    ledger=Ledger();ledger.encounter(texts,'fit:initial');ledger.flush()
    assert not set(initial)&ledger.bans
    names=c.names(initial,c.rewrite.records(texts));assert got['names']==names
    assert got['initial_character_count']==len(mandatory)
    accepted=[r for r in got['trace'] if 'accepted_trial' in r]
    trials=[r for r in got['trace'] if 'trial' in r]
    assert [r['trial'] for r in trials]==list(range(2,got['trials']+1))
    assert type(got['trials']) is int and 1<=got['trials']<=limits['trials']
    assert got['rounds']==len(accepted)
    assert got['trial_composition']==dict(Counter(r['kind'] for r in trials))
    assert got['coverage_failures']==sum(not r['coverage'] for r in trials)
    assert got['stop'] in ('trial_limit','time_limit','bounded_neighborhood_no_improvement')
    if got['stop']=='trial_limit':assert got['trials']==limits['trials']
    timing=seconds(got['seconds'],limits.get('worker_seconds',900)+1)
    over=seconds(got['overrun_seconds'],timing)
    assert abs(over-max(0,timing-limits['seconds']))<=.01
    if got['stop']=='time_limit':assert timing>=limits['seconds']
    for r in trials:
        seconds(r['trial_seconds'],timing)
        assert type(r['coverage']) is bool and ((r['score'] is None)==(not r['coverage']))
        if r['score'] is not None:assert len(r['score'])==3 and all(type(x) is int and x>=0 for x in r['score'])
    assert sum(r['trial_seconds'] for r in trials)<=timing+.01
    summaries=[]
    for number,menu in enumerate(got['round_menus']):
        assert menu['round']==number and menu['source_state_sha256']==c.digest_sources(current['sources'])
        records=c.rewrite.records(current['sources']);contexts=c.contexts(current,records)
        assert menu['contexts']==contexts
        groups=[];stop=False;rendered=[]
        expected_rendered=menu['rendered_group_ids']
        for context in contexts:
            for name in names:
                group=c.make_group(current['sources'],records,context,name)
                if group is None:continue
                if not menu['complete'] and len(rendered)==len(expected_rendered):stop=True;break
                rendered.append(group['id'])
                check_geometry(group,current['sources'],records)
                ledger.pending=group;ledger.encounter(group['updates'],f'fit:{number}:group:{group["id"]}')
                if group['eligible']:groups.append(group)
            if stop:break
        ledger.flush();assert not set(current['vocab'])&ledger.bans
        assert rendered==expected_rendered
        assert menu['groups']==groups
        assert menu['banned_sha256']==c.sha(c.canonical(sorted(ledger.bans)).encode())
        group_by_id={g['id']:g for g in groups}
        rows=[r for r in trials if r['round']==number]
        winners=[r for r in accepted if r['accepted_round']==number+1]
        assert len(winners)<=1 and (menu['complete'] or not rows and not winners)
        allowed={'remove','dictionary','context_dictionary'} if arm=='D' else {'source'} if arm=='S' else {'remove','dictionary','context_dictionary','source','joint'} if arm=='J' else {'remove','dictionary','context_dictionary','source'}
        ordinary=c.literal_proposals(current,ledger.bans) if arm!='S' else []
        signatures=set()
        def candidate(row):
            group=group_by_id.get(row['group_id'])
            sources={**current['sources'],**group['updates']} if row['kind'] in ('source','joint') else current['sources']
            words=c.order((set(current['vocab'])-set(row['removals']))|set(row['additions']))
            return sources,words
        for row in rows:
            assert row['kind'] in allowed
            assert row['additions']==c.order(row['additions']) and row['removals']==c.order(row['removals'])
            assert not set(row['additions'])&set(current['vocab']) and set(row['removals'])<=set(current['vocab'])-mandatory
            assert len(row['additions'])<=2 and len(row['removals'])<=2
            if row['group_id'] is not None:assert row['group_id'] in group_by_id
            if row['kind'] in ('source','joint','context_dictionary'):assert row['group_id'] is not None
            if row['kind']=='source':assert not row['additions'] and not row['removals']
            if row['kind']=='remove':assert row['group_id'] is None and not row['additions'] and len(row['removals'])==1
            if row['kind']=='dictionary':assert row['group_id'] is None and row['additions'] in ordinary
            if row['kind'] in ('context_dictionary','joint'):
                g=group_by_id[row['group_id']]
                assert row['additions'] in [c.order(set(x)-set(current['vocab'])) for x in ([g['target']],[g['target'],g['fragment']])]
            if row['kind'] not in ('remove','source'):
                assert len(row['removals'])==max(0,len(current['vocab'])+len(row['additions'])-256)
            cs,cv=candidate(row)
            assert len(cv)<=256 and mandatory<=set(cv) and not set(cv)&ledger.bans
            signature=(c.digest_sources(cs),tuple(cv));assert signature not in signatures;signatures.add(signature)
        if not winners:
            assert not any(r['coverage'] and tuple(r['score'])<cost(current) for r in rows)
            assert number==len(got['round_menus'])-1
            continue
        win=winners[0];row=next(r for r in rows if r['trial']==win['accepted_trial'])
        assert row['coverage'] and win['kind']==row['kind']
        assert all(not r['coverage'] or tuple(r['score'])>=tuple(row['score']) for r in rows)
        group=group_by_id.get(row['group_id'])
        updated={**current['sources'],**group['updates']} if row['kind'] in ('source','joint') else current['sources']
        vocab=c.order((set(current['vocab'])-set(row['removals']))|set(row['additions']))
        assert mandatory<=set(vocab) and len(vocab)<=256 and not set(vocab)&ledger.bans
        next_state=state(updated,vocab)
        assert list(cost(next_state))==row['score'] and cost(next_state)<cost(current)
        for tied in rows:
            if tied['trial']!=row['trial'] and tied['score']==row['score']:
                ts,tv=candidate(tied);other=state(ts,tv)
                assert list(cost(other))==tied['score'] and tie(next_state)<=tie(other)
        assert win['before']==brief(current) and win['after']==brief(next_state)
        assert win['dictionary']==vocab and win['source_sha256']==c.digest_sources(updated)
        kind='N_improvement' if next_state['N']<current['N'] else 'C_plateau' if next_state['C']<current['C'] else 'package_plateau'
        assert win['improvement']==kind
        companions=[]
        if row['kind']=='joint':
            for kind2 in ('source','context_dictionary'):
                matching=[r for r in rows if r['kind']==kind2 and r['group_id']==row['group_id'] and
                          (kind2=='source' or (r['additions']==row['additions'] and r['removals']==row['removals']))]
                for companion in matching:
                    cs=updated if kind2=='source' else current['sources']
                    cv=current['vocab'] if kind2=='source' else vocab
                    try:companion_score=list(cost(state(cs,cv)))
                    except ValueError:companion_score=None
                    assert companion_score==companion['score']
                companions.append({'kind':kind2,'observed_scores':[r['score'] for r in matching],
                                   'same_removals':kind2!='source' or not row['removals'],
                                   'status':'recorded evaluated companion' if matching else 'unknown; matching transaction not evaluated'})
        summaries.append({'round':number,'trial':row['trial'],'kind':row['kind'],'improvement':kind,
                          'before':brief(current),'after':brief(next_state),'companions':companions,
                          'changed_programs':sum(updated[p]!=current['sources'][p] for p in updated),
                          'introduced_name_byte_length':len(group['target'].encode()) if row['kind'] in ('source','joint') else None,
                          'introduced_name_sha256':c.sha(group['target'].encode()) if row['kind'] in ('source','joint') else None})
        current=next_state
    assert all(0<=r['round']<len(got['round_menus']) for r in trials)
    assert got['state']==current
    assert got['final_contexts']==c.contexts(current,c.rewrite.records(current['sources']))
    ledger.check(got['ledger'])
    return current,ledger,summaries


def local_matches(text,record,pattern):
    if record['unsafe'] or not text.isascii():return []
    found=[]
    for variable in record['variables']:
        if not variable['eligible']:continue
        word=''.join(variable['name'] if x is None else x for x in pattern)
        for start in range(len(text)-len(word)+1):
            if text.startswith(word,start) and c.pattern_at(text,variable['spans'],start,start+len(word))==pattern:
                found.append(variable['id']);break
    return found


def replay_validation(got,texts,vocab,fit,ledger):
    selected=dict(texts);failures=[];trace=[];ledger.pending=None
    ledger.encounter(texts,'validation:initial');ledger.flush();assert not set(vocab)&ledger.bans
    for pid,text in texts.items():
        try:current=state({pid:text},vocab)
        except ValueError:failures.append(pid);continue
        if fit['arm']=='D':continue
        for pass_no in range(2):
            records=c.rewrite.records(current['sources']);rec=records[pid];rows=[];best=None
            for context in fit['final_contexts']:
                local={'pattern':context['pattern'],'matches':[[pid,bid] for bid in local_matches(current['sources'][pid],rec,context['pattern'])]}
                for name in fit['names']:
                    group=c.make_group(current['sources'],records,local,name,min_support=1)
                    if group is None:continue
                    check_geometry(group,current['sources'],records)
                    ledger.pending=group;ledger.encounter(group['updates'],f'validation:{pid}:{pass_no}:{group["id"]}')
                    try:candidate=state(group['updates'],vocab)
                    except ValueError:candidate=None
                    rows.append({'pid':pid,'pass':pass_no,'group':group,'before_score':list(cost(current)),
                                 'score':None if candidate is None else list(cost(candidate)),'coverage':candidate is not None})
                    if candidate is not None and cost(candidate)<cost(current) and (best is None or tie(candidate)<tie(best[0])):
                        best=(candidate,len(rows)-1)
            ledger.flush();assert not set(vocab)&ledger.bans
            trace.append({'pid':pid,'pass':pass_no,'trials':rows,'accepted':None if best is None else best[1]})
            if best is None:break
            current=best[0];selected[pid]=current['sources'][pid]
    assert got['selected']==selected and got['initial_coverage_failures']==failures and got['trace']==trace
    ledger.check(got['ledger'])
    return selected


def distribution(values):
    values=sorted(values);assert values
    return {'n':len(values),'total':sum(values),'median':statistics.median(values),
            'p90':values[math.ceil(.9*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],
            'worst':max(values),'within_32':sum(x<=32 for x in values),'within_96':sum(x<=96 for x in values)}


def aggregate(rows,ids,db,decoder):
    selected=[rows[str(p)] for p in ids];good=[r for r in selected if r['encodable']]
    n=sum(r['selections'] for r in good);chars=sum(r['single_characters'] for r in good);package=db+sum(r['packet_bytes'] for r in good)
    return {'coverage_complete':len(good)==len(ids),'distribution_scope':'all programs' if len(good)==len(ids) else 'covered programs only; incomplete denominator',
            'problems':len(ids),'covered':len(good),'failed_ids':[str(p) for p in ids if not rows[str(p)]['encodable']],
            'qualified':sum(r['encodable'] and r['qualified_source'] for r in selected),
            'selections':distribution([r['selections'] for r in good]) if good else None,
            'actions':distribution([r['actions'] for r in good]) if good else None,
            'single_character_codes':chars,'single_character_fraction':chars/n if n else None,
            'source_bytes':sum(r['source_bytes'] for r in selected),'framing_bytes':41*len(good),'payload_bits':8*n,'padding_bits':0,
            'package_bytes':package,'package_with_decoder_dependencies':package+decoder,
            'package_scope':'encoded programs only; failed programs retained in coverage denominator'}


def spelling(texts):
    names=Counter();occurrences=Counter()
    for record in c.rewrite.records(texts).values():
        for variable in record['variables']:
            if variable['eligible']:
                key=str(len(variable['name'].encode()));names[key]+=1;occurrences[key]+=len(variable['spans'])
    return {'eligible_binding_spelling_byte_lengths':dict(names),'eligible_occurrence_spelling_byte_lengths':dict(occurrences)}


def measured(folder,arm,policy,sources,vocab,forbidden,config,original,receipts):
    assert vocab==c.order(vocab) and 1<=len(vocab)<=256
    db=c.analyze.dictionary_bytes(vocab);assert (folder/'dictionary.bin').read_bytes()==db
    rows={};qual={};good=set()
    for pid,text in sorted(sources.items()):
        row={'source_sha256':c.sha(text.encode()),'source_bytes':len(text.encode()),
             'source_byte_delta':len(text.encode())-len(original[pid].encode())}
        try:ids=encode(text,vocab,policy)
        except ValueError:row['encodable']=False
        else:
            good.add(pid);packet=(folder/policy/f'{pid}.bin').read_bytes()
            assert packet[4]==8 and list(packet[41:])==ids
            assert c.analyze.decode(db,packet)==text and packet==c.analyze.encode(vocab,ids,8)
            row.update(encodable=True,selections=len(ids),actions=len(ids)+1,single_characters=sum(len(vocab[i])==1 for i in ids),
                       packet_bytes=len(packet),packet_sha256=c.sha(packet),one_program_package_bytes=len(db)+len(packet),
                       one_program_package_with_decoder_dependencies=len(db)+len(packet)+config['decoder_dependency_bytes'])
        key=f'{pid}:{row["source_sha256"]}';qual[pid]=receipts[key];row['qualified_source']=qual[pid]['passed'];rows[pid]=row
    assert {p.stem for p in (folder/policy).glob('*.bin')}==good
    result={'arm':arm,'policy':policy,'width':8,'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab),
            'dictionary_bytes':len(db),'dictionary_sha256':c.sha((folder/'dictionary.json').read_bytes()),
            'dictionary_binary_sha256':c.sha(db),'illegal_entry_sha256':sorted(c.sha(w.encode()) for w in set(vocab)&forbidden),
            'spelling':spelling(sources),'per_problem':rows,'qualification':qual}
    for split,key in (('fit','dev_fit'),('validation','dev_val')):
        result[split]=aggregate(rows,config['partition'][key],len(db),config['decoder_dependency_bytes'])
    return result


def gates(a,b,config,initial=False):
    ids=list(map(str,config['partition']['dev_val']));nf=len(config['partition']['dev_fit']);nv=len(ids)
    coverage=all(x['fit']['covered']==x['fit']['qualified']==nf and x['validation']['covered']==x['validation']['qualified']==nv for x in (a,b))
    clean=all(x['entries']<=256 and not x['illegal_entry_sha256'] for x in (a,b))
    better=sum(a['per_problem'][p]['encodable'] and (not b['per_problem'][p]['encodable'] or a['per_problem'][p]['actions']<b['per_problem'][p]['actions']) for p in ids)
    worse=sum(b['per_problem'][p]['encodable'] and (not a['per_problem'][p]['encodable'] or a['per_problem'][p]['actions']>b['per_problem'][p]['actions']) for p in ids)
    checks={'coverage_and_qualification':coverage,'legal_dictionary':clean}
    if not coverage:checks.update({key:False for key in ('actions','median','p90','breadth','fraction','package')})
    else:
        x,y=a['validation'],b['validation'];ax,by=x['actions'],y['actions']
        xn=sum(a['per_problem'][p]['selections'] for p in ids);yn=sum(b['per_problem'][p]['selections'] for p in ids)
        xc=sum(a['per_problem'][p]['single_characters'] for p in ids);yc=sum(b['per_problem'][p]['single_characters'] for p in ids)
        checks.update(actions=100*ax['total']<=95*by['total'] if initial else ax['total']<by['total'],
                      median=ax['median']<by['median'] if initial else ax['median']<=by['median'],
                      p90=ax['p90']<by['p90'] if initial else ax['p90']<=by['p90'],
                      breadth=worse<=25 and (not initial or better>=60),fraction=xc*yn<=yc*xn,
                      package=100*x['package_bytes']<=105*y['package_bytes'])
    return {'checks':checks,'passed':all(checks.values()),'paired':{'better':better,'same':nv-better-worse,'worse':worse}}


def hashfile(path):return c.sha(Path(path).read_bytes())


def check_seal(folder,name,files,flag):
    seal=c.read(folder/name)
    assert set(seal)=={'files',flag} and seal[flag] is False and set(seal['files'])==set(files)
    for rel,digest in seal['files'].items():assert hashfile(folder/rel)==digest


def known_receipts(parent):
    known={}
    for arm in parent['arms']:
        for pid,row in arm['per_problem'].items():
            q=arm['qualification'][pid]
            if q['passed']:
                known.setdefault(f'{pid}:{row["source_sha256"]}',{'passed':True,'receipt':q,'source_arm':arm['arm'],'source_policy':arm['policy'],'reused':True})
    return known


def replay_qualification(folder,config,pid,text,fresh):
    """Rejudge captured observations; never invokes sandbox.run or an executor."""
    from dataclasses import asdict
    minify=c.module('atomic_report_minify',c.LIT/'minify-control-v1/minify.py')
    from algsolve.judge import sandbox
    from qualify_rules import judge_case
    from verify_execution import strict_object
    style=minify.style;work=Path(config['work'])
    assert hashfile(work/'population500/manifest.json')==config['manifest_sha256']
    spec=next(r for r in c.read(work/'population500/manifest.json')['rows'] if int(r['id'])==int(pid))
    pins=next(r['files'] for r in config['qualification'] if int(r['id'])==int(pid))
    testpath=f'population500/{pid}-tests.json';basepath=f'population500-baseline/qualification/baselines/{pid}.json'
    assert testpath in pins and basepath in pins
    for rel in (testpath,basepath):assert hashfile(work/rel)==pins[rel]
    cases=style.transported(spec,c.read(work/testpath));baseline=c.read(work/basepath)
    assert len(cases)==len(baseline)
    harness=(style.ADM/('harness-exact-integer.cjs' if spec['transport']=='exact-integer' else 'harness.cjs')).read_text()
    rel=Path('raw-qualification')/f'{pid}-{c.sha(text.encode())}'/'receipt.json'
    assert fresh['raw_receipt']==str(rel) and hashfile(folder/rel)==fresh['raw_receipt_sha256']
    raw=c.read(folder/rel);sub=(folder/rel).parent
    assert set(raw)=={'pid','source_sha256','entry','complete','batches','passed','checks_passed','cases','mismatches'}
    assert raw['pid']==pid and raw['source_sha256']==c.sha(text.encode()) and raw['entry']=='solve' and raw['complete'] is True
    limits=sandbox.Limits(cpu_seconds=style.LIMITS['sandbox_cpu_seconds'],wall_seconds=style.LIMITS['sandbox_wall_seconds'],
                          memory_bytes=style.LIMITS['sandbox_memory_bytes'],max_output_bytes=style.LIMITS['max_output_bytes'])
    offsets=list(range(0,len(cases),style.LIMITS['batch_cases']));assert len(raw['batches'])==len(offsets)
    ok=0;bad=[]
    for number,(off,row) in enumerate(zip(offsets,raw['batches'])):
        batch=cases[off:off+style.LIMITS['batch_cases']]
        assert row['offset']==off and row['count']==len(batch) and row['complete'] is True
        assert row['argv']==['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs']
        assert row['limits']==asdict(limits) and row['stdin_sha256']==c.sha(b'')
        inputs=json.dumps({'entry':'solve','calls':[{'args':t['args']} for t in batch]})
        assert row['input_files']=={name:c.sha(value.encode()) for name,value in {'program.js':text,'harness.cjs':harness,'inputs.json':inputs}.items()}
        assert row['stdout']==f'{number}.stdout' and row['stderr']==f'{number}.stderr'
        stdout=(sub/row['stdout']).read_bytes();stderr=(sub/row['stderr']).read_bytes()
        assert c.sha(stdout)==row['stdout_sha256'] and c.sha(stderr)==row['stderr_sha256']
        seconds(row['wall_seconds'],config['limits']['worker_seconds']+1)
        assert type(row['timed_out']) is bool and type(row['output_limit_exceeded']) is bool
        assert row['exit_code'] is None or type(row['exit_code']) is int
        assert row['signal'] is None or type(row['signal']) is int
        actual_ok=row['exit_code']==0 and not row['timed_out'] and not row['output_limit_exceeded']
        assert type(row['ok']) is bool and row['ok']==actual_ok
        try:
            assert actual_ok,f'sandbox failure (exit {row["exit_code"]}, timed out {row["timed_out"]}) {stderr.decode(errors="replace")[-200:]}'
            recs=[json.loads(line,object_pairs_hook=strict_object) for line in stdout.splitlines()]
            assert len(recs)==len(batch)+1 and recs[-1]=={'done':len(batch)},'protocol'
            for k,record in enumerate(recs[:-1]):
                valid,observed=judge_case(batch[k],record);same=style.exact(observed,baseline[off+k])
                if valid and same:ok+=1
                elif len(bad)<3:
                    bad.append({'case':off+k,'oracle':valid,'parity':same,'error':record.get('error'),
                                'observed':{key:observed.get(key) for key in ('result','args_after')},
                                'original':{key:baseline[off+k].get(key) for key in ('result','args_after')}})
        except Exception as error:
            if len(bad)<3:bad.append({'offset':off,'error':str(error)})
    assert sum(r['wall_seconds'] for r in raw['batches'])<=config['limits']['worker_seconds']+1
    passed=ok==len(cases) and not bad
    assert (raw['passed'],raw['checks_passed'],raw['cases'],raw['mismatches'])==(passed,ok,len(cases),bad)
    expected={'passed':bool(passed),'checks_passed':ok,'cases':len(cases),'reused':False,
              'raw_receipt':str(rel),'raw_receipt_sha256':hashfile(folder/rel)}
    assert fresh==expected
    return expected,bad


def replay(folder,config):
    folder=Path(folder)
    assert config['active'] is True,'Pending contract cannot authorize private input replay'
    assert not list(folder.rglob('failure.json')),'execution failure dominates completed artifacts'
    assert c.read(folder/'status.json')=={'phase':'complete','complete':True}
    supervisor=c.read(folder/'supervisor-receipt.json')
    assert supervisor['complete'] is True and supervisor['outer_timeout'] is False and type(supervisor['exit_code']) is int and supervisor['exit_code']==0
    elapsed=seconds(supervisor['elapsed'],config['limits']['overall_seconds']+31)
    for rel,digest in config['code_hashes'].items():assert hashfile(c.LIT/rel)==digest
    for path,digest in config['runtime_files'].items():assert hashfile(path)==digest
    parent_path=c.LIT/config['parent_evidence']['path'];assert hashfile(parent_path)==config['parent_evidence']['sha256']
    parent=c.read(parent_path);assert parent['private_results_sha256']==config['parent_evidence']['private_results_sha256']
    known=known_receipts(parent);assert known==config['known_receipts']
    result=c.read(folder/'results.json')
    assert set(result)=={'arms','fit_summaries','fresh_qualification_summary','seconds','contract_sha256','decoded_packets'}
    assert result['contract_sha256']==hashfile(c.HERE/'contract.json')
    seconds(result['seconds'],min(elapsed,config['limits']['overall_seconds'])+1)
    source=Path(config['source_run'])
    for rel,digest in config['source_carrier']['private_files'].items():assert hashfile(source/rel)==digest
    initial=c.read(source/config['initial_dictionary']['path'])
    assert hashfile(source/config['initial_dictionary']['path'])==config['initial_dictionary']['sha256']
    assert c.sha(c.analyze.dictionary_bytes(initial))==config['initial_dictionary']['binary_sha256']
    assert len(initial)==config['initial_dictionary']['entries'] and sum(len(w)==1 for w in initial)==config['initial_dictionary']['character_entries']
    original=c.read(source/'artifacts/D11/sources.json')
    ids={str(p) for values in config['partition'].values() for p in values};assert set(original)==ids
    for pid,text in original.items():assert c.sha(text.encode())==config['source_qualification'][pid]['source_sha256']
    fitbase=c.read(source/'fit/D11/fit-sources.json')
    assert fitbase=={str(p):original[str(p)] for p in config['partition']['dev_fit']}
    # JSON serialization sorts keys; preserve the exact source-loader order in
    # validation, whose deterministic per-source traces use insertion order.
    valbase={str(p):original[str(p)] for p in config['partition']['dev_val']}
    allfit=c.read(folder/'all-fit-sealed.json');allval=c.read(folder/'all-validation-sealed.json')
    assert set(allfit)=={'validation_loaded','arms'} and allfit['validation_loaded'] is False
    assert set(allval)=={'qualification_started','arms'} and allval['qualification_started'] is False
    assert allfit['arms']==result['fit_summaries']
    assert [a['arm'] for a in allfit['arms']]==[a['arm'] for a in allval['arms']]==list(ARMS)
    private={'D10':(original,initial,c.banned(original))};search={}
    for arm in ARMS:
        sub=folder/'fit'/arm
        check_seal(sub,'fit-seal.json',['fit.json'],'validation_loaded')
        check_seal(sub,'validation-seal.json',['validation.json'],'qualification_started')
        fs=next(a for a in allfit['arms'] if a['arm']==arm);vs=next(a for a in allval['arms'] if a['arm']==arm)
        assert fs['fit_seal_sha256']==hashfile(sub/'fit-seal.json') and vs=={'arm':arm,'validation_seal_sha256':hashfile(sub/'validation-seal.json')}
        fit=c.read(sub/'fit.json');assert fit['arm']==arm
        assert fs=={'arm':arm,**{k:fit[k] for k in ('trials','rounds','stop','seconds','overrun_seconds','trial_composition','coverage_failures')},'fit_seal_sha256':hashfile(sub/'fit-seal.json')}
        current,ledger,moves=replay_fit(fit,fitbase,initial,{**config['search'],'worker_seconds':config['limits']['worker_seconds']})
        val=c.read(sub/'validation.json');selected=replay_validation(val,valbase,current['vocab'],fit,ledger)
        private[arm]=({**current['sources'],**selected},current['vocab'],ledger.bans)
        search[arm]={'accepted_moves':moves,'trials':fit['trials'],'rounds':fit['rounds'],'stop':fit['stop'],'seconds':fit['seconds'],
                     'accepted_improvement_counts':dict(Counter(r['improvement'] for r in moves)),
                     'accepted_transaction_counts':dict(Counter(r['kind'] for r in moves)),
                     'overrun_seconds':fit['overrun_seconds'],'trial_composition':fit['trial_composition'],'coverage_failures':fit['coverage_failures'],
                     'encountered_variant_count':len(ledger.variants),'ban_count':len(ledger.bans),
                     'initial_validation_coverage_failures':val['initial_coverage_failures'],
                     'accepted_validation_moves':sum(r['accepted'] is not None for r in val['trace']),
                     'validation_trials':sum(len(r['trials']) for r in val['trace'])}
    # Qualification is checked only after all fit/validation seals and choices.
    expected={f'{pid}:{c.sha(text.encode())}':(pid,text) for texts,vocab,bans in private.values() for pid,text in texts.items() if f'{pid}:{c.sha(text.encode())}' not in known}
    q=c.read(folder/'qualification-private.json')
    assert q['complete'] is True and q['expected_keys']==sorted(expected) and set(q['receipts'])==set(expected) and set(q['failures'])<=set(expected)
    receipts=dict(known)
    raw_folder=folder/'raw-qualification'
    assert {p.name for p in raw_folder.iterdir()}=={key.replace(':','-') for key in expected} if raw_folder.exists() else not expected
    for key,(pid,text) in expected.items():
        fresh=q['receipts'][key]
        assert fresh['reused'] is False and type(fresh['passed']) is bool
        assert type(fresh['cases']) is int and type(fresh['checks_passed']) is int and 0<=fresh['checks_passed']<=fresh['cases']
        assert fresh['passed']==(fresh['checks_passed']==fresh['cases'] and not q['failures'].get(key))
        # Raw strict-observation rejudge is supplied by the separate capture
        # module, with no sandbox/process execution during replay.
        checked,bad=replay_qualification(folder,config,pid,text,fresh)
        assert checked==fresh
        assert q['failures'].get(key)==(bad or {'passed':False}) if not fresh['passed'] else key not in q['failures']
        receipts[key]=fresh
    fresh_summary={'distinct_new_sources':len(expected),'passed':sum(r['passed'] for r in q['receipts'].values()),
                   'checks':sum(r['cases'] for r in q['receipts'].values()),'checks_passed':sum(r['checks_passed'] for r in q['receipts'].values()),'failed_sources':len(q['failures'])}
    assert result['fresh_qualification_summary']==fresh_summary
    rebuilt=[]
    for arm in ('D10',*ARMS):
        texts,vocab,bans=private[arm];sub=folder/'artifacts'/arm
        assert c.read(sub/'sources.json')==texts and c.read(sub/'dictionary.json')==vocab
        for policy in POLICIES:rebuilt.append(measured(sub,arm,policy,texts,vocab,bans,config,original,receipts))
    assert result['arms']==rebuilt
    assert result['decoded_packets']==sum(a['fit']['covered']+a['validation']['covered'] for a in rebuilt)
    index={(a['arm'],a['policy']):a for a in [*parent['arms'],*rebuilt]}
    verdicts={}
    for policy in POLICIES:
        candidate=index['J',policy]
        checks={ref:gates(candidate,index[ref,policy],config,initial=ref=='R') for ref in ('R','seed13','best24','N','NCP','D10','D','S','A')}
        verdicts[policy]={'ready':all(v['passed'] for v in checks.values()),'comparisons':checks}
    primary=index['J','shortest_min_char'];alternate=index['A','shortest_min_char']
    predictions={'P1':all(a['fit']['covered']==a['fit']['qualified']==len(config['partition']['dev_fit']) and a['validation']['covered']==a['validation']['qualified']==len(config['partition']['dev_val']) for a in rebuilt),
                 'P2':any(x['kind']=='joint' for x in search['J']['accepted_moves']),
                 'P3':primary['validation']['covered']==alternate['validation']['covered']==len(config['partition']['dev_val']) and primary['validation']['actions']['total']<alternate['validation']['actions']['total'],
                 'P4':not verdicts['shortest_min_char']['ready']}
    return {'complete':True,'independent_replay':True,'promotion_allowed':False,'contract_sha256':result['contract_sha256'],
            'private_results_sha256':hashfile(folder/'results.json'),'arms':rebuilt,'search':search,'verdicts':verdicts,
            'predictions':predictions,'fresh_qualification_summary':fresh_summary,'decoded_packets':result['decoded_packets'],
            'runner_seconds':result['seconds'],'supervisor_seconds':elapsed,'decoder_dependency_bytes':config['decoder_dependency_bytes'],
            'offline_encoder_bytes':config.get('offline_encoder_bytes'),'runtime_footprint':'Installed runtime footprint unmeasured.',
            'scope':'Fixed development fit and consumed per-source validation; no independent confirmation, M1 qualification or promotion.',
            'replay_scope':'Every accepted fit move and every validation proposal is independently rescored. Rejected fit trial scores are recorded search evidence, not independently rerun optimization.'}


def markdown(result):
    lines=['# Atomic naming and paid literal entries','',result['scope'],'',
           '| Arm | Policy | Split | Covered | Qualified | Actions | Median | p90 | C/N | Raw package |',
           '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        for split in ('fit','validation'):
            row=arm[split];actions=row['actions'] or {};complete=row['covered']==row['problems']
            lines.append(f"| {arm['arm']} | {arm['policy']} | {split} | {row['covered']}/{row['problems']} | {row['qualified']} | {actions.get('total') if complete else 'partial'} | {actions.get('median') if complete else None} | {actions.get('p90') if complete else None} | {row['single_character_fraction'] if complete else None} | {row['package_bytes']} |")
    lines+=['','Primary J successor gates: **'+str(result['verdicts']['shortest_min_char']['ready'])+'**. No other arm replaces J post hoc.']
    for policy,verdict in result['verdicts'].items():
        failed=[f'{ref}:{name}' for ref,v in verdict['comparisons'].items() for name,ok in v['checks'].items() if not ok]
        lines+=['',policy+' failed gates: '+(', '.join(failed) or 'none')+'.']
    lines+=['','Predictions: '+', '.join(f'{k}={v}' for k,v in result['predictions'].items())+'.','',
            'Actions include one Finish per covered program. Every package charges the complete shared dictionary once, 41 bytes of framing per packet and all eight-bit literal selections. Decoder-inclusive metadata adds 13,010 bytes. Partial coverage costs remain descriptive and cannot satisfy readiness. Source-byte deltas and binding-spelling lengths expose C-only label reclassification separately from action gains.','',
            result['replay_scope'],'','Finite strict qualification is not a semantic equivalence proof. A successful consumed-development comparison still requires separately authorized confirmation. No publication or promotion is authorized.','']
    return '\n'.join(lines)


def withdraw(folder,output,error):
    """Best-effort independent withdrawal of both public files, even after I/O failure.

    If a failure receipt cannot replace an old file, unlink that file so it cannot
    remain an apparent successful report. Persistent filesystem failure is raised.
    """
    folder=Path(folder);output=Path(output)
    failure={'complete':False,'independent_replay':False,'promotion_allowed':False,'verdicts':None,
             'error_type':type(error).__name__,'reason':'Incomplete execution, verification or publication failure; no verdict.'}
    prose='# Atomic naming and paid entries\n\n**No verdict.** Execution is incomplete or report verification/publication failed. Earlier successful conclusions are withdrawn.\n\nSee [failure metadata](results.json).\n'
    failures=[]
    targets=[(output/'results.json',json.dumps(failure,sort_keys=True,indent=2)+'\n'),(output/'README.md',prose)]
    if folder.is_dir():targets.append((folder/'report-failure.json',json.dumps(failure,sort_keys=True,indent=2)+'\n'))
    for path,payload in targets:
        try:
            path.parent.mkdir(parents=True,exist_ok=True)
            temporary=path.with_name(path.name+'.withdraw.tmp');temporary.write_text(payload);temporary.replace(path)
        except BaseException:
            try:path.unlink(missing_ok=True)
            except BaseException:failures.append(path.name)
    if failures:raise OSError('Unable to withdraw report artifacts: '+','.join(failures)) from error
    return failure


def publish(folder,config,output,started=None):
    folder=Path(folder);output=Path(output)
    started=time.monotonic() if started is None else started
    try:
        result=replay(folder,config)
        result['replay_seconds']=time.monotonic()-started
        prose=markdown(result)
        output.mkdir(parents=True,exist_ok=True)
        # Prepare both files before changing either public success artifact.
        # README is replaced first; complete=true metadata is the final commit.
        with tempfile.TemporaryDirectory(prefix='.report-stage-',dir=output) as stage:
            stage=Path(stage)
            c.write(stage/'results.json',result)
            (stage/'README.md').write_text(prose)
            seconds(time.monotonic()-started,config['limits']['report_seconds'])
            (stage/'README.md').replace(output/'README.md')
            (stage/'results.json').replace(output/'results.json')
            seconds(time.monotonic()-started,config['limits']['report_seconds'])
        # A cleanup failure is also a publication failure, never an accepted run.
        seconds(time.monotonic()-started,config['limits']['report_seconds'])
        return result
    except BaseException as error:
        withdraw(folder,output,error)
        raise


def main(args):
    started=time.monotonic()
    try:
        def expired(signum,frame):raise c.HardDeadline('Independent report deadline; no search or qualification execution')
        signal.signal(signal.SIGALRM,expired)
        signal.setitimer(signal.ITIMER_REAL,900)
        config=c.read(c.HERE/'contract.json')
        assert config['limits']['report_seconds']==900
        os.sched_setaffinity(0,set(config['all_cores']))
        resource.setrlimit(resource.RLIMIT_AS,(config['limits']['address_space_bytes'],)*2)
        remaining=config['limits']['report_seconds']-(time.monotonic()-started)
        if remaining<=0:raise c.HardDeadline('Independent report preflight deadline')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        publish(args.run,config,args.output,started=started)
        signal.setitimer(signal.ITIMER_REAL,0)
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        withdraw(args.run,args.output,error)
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,default=c.HERE/'evidence')
    main(parser.parse_args())
