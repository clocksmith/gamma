"""Independent source/qualification/packet/cost replay; no searches or executions."""
import argparse
import json
from pathlib import Path
from common import HERE,LIT,ALPHABET,analyze,authority,checked,evaluate,sha,write,require_assertions

def predicates(a,b,ids,incremental=False):
    v,z=a['validation'],b['validation'];better=worse=0
    for pid in ids:
        x,y=a['per_problem'][str(pid)],b['per_problem'][str(pid)]
        if not x['encodable'] and not y['encodable']:pass
        elif not x['encodable']:worse+=1
        elif not y['encodable']:better+=1
        elif x['actions']<y['actions']:better+=1
        elif x['actions']>y['actions']:worse+=1
    complete=v['covered']==z['covered']==len(ids)
    checks={'all_qualified':a['qualified']==b['qualified']==36,'fit_coverage':a['fit']['covered']==b['fit']['covered']==27,
            'validation_coverage':complete,'audit_clean':not a['illegal_entry_sha256'] and not b['illegal_entry_sha256'],
            'entry_budget':a['entries']<=2**a['width'],
            'actions':complete and (v['actions']['total']<z['actions']['total'] if incremental else v['actions']['total']<=.95*z['actions']['total']),
            'median':complete and (v['actions']['median']<=z['actions']['median'] if incremental else v['actions']['median']<z['actions']['median']),
            'p90':complete and (v['actions']['p90']<=z['actions']['p90'] if incremental else v['actions']['p90']<z['actions']['p90']),
            'improved':incremental or better>=6,'worsened':worse<=2,
            'character_fraction':complete and v['single_character_fraction']<=z['single_character_fraction'],
            'package':complete and v['package_bytes']<=1.05*z['package_bytes']}
    return checks,{'better':better,'same':len(ids)-better-worse,'worse':worse}

def replay(folder,c):
    require_assertions()
    assert not list(folder.rglob('failure.json')),'failed/partial run cannot promote'
    assert json.loads((folder/'status.json').read_text())['complete']
    assert json.loads((folder/'supervisor-receipt.json').read_text())['complete']
    for rel,h in c['code_hashes'].items():assert sha((LIT/rel).read_bytes())==h
    for rel,d in c['decoder_source_files'].items():
        raw=(LIT/rel).read_bytes();assert sha(raw)==d['sha256'] and len(raw)==d['bytes']
    assert set(c['decoder_source_files'])=={'literals.py','pass2/working/bitpack.py'}
    assert c['decoder_source_bytes']==sum(d['bytes'] for d in c['decoder_source_files'].values())>0
    r=json.loads((folder/'results.json').read_text());assert r['contract_sha256']==sha((HERE/'contract.json').read_bytes())
    allseal=json.loads((folder/'all-fit-sealed.json').read_text());assert allseal['validation_loaded'] is False
    summaries={(s['width'],s['arm']):s for s in allseal['summaries']}
    assert len(allseal['summaries'])==4 and set(summaries)=={(w,m) for w in (7,8) for m in ('fixed96','optional')}
    arms={(a['width'],a['arm']):a for a in r['arms']};assert len(r['arms'])==8 and set(arms)=={(w,m) for w in (7,8) for m in ('R','seed31','fixed96','optional')}
    ids=set(map(str,c['partition']['dev_fit']+c['partition']['dev_val']))
    parent=checked(c['qualification'])
    for (w,name),a in arms.items():
        arm=folder/f'w{w}'/name;inp=c['inputs'][str(w)]
        texts=json.loads((arm/'sources.json').read_text());vocab=json.loads((arm/'dictionary.json').read_text())
        assert set(texts)==ids and texts==checked(inp['original_sources' if name=='R' else 'sources'])
        authority(c,w,'control' if name=='R' else 'scope_joint',texts)
        if name in ('R','seed31'):assert vocab==checked(inp['baseline_dictionary' if name=='R' else 'seed_dictionary'])
        else:
            summary=summaries[w,name];assert summary==json.loads((arm/'fit-summary.json').read_text())
            assert summary['fit_seal_sha256']==sha((arm/'fit-seal.json').read_bytes())
            seal=json.loads((arm/'fit-seal.json').read_text());assert seal['validation_loaded'] is False
            for key,file in [('dictionary_sha256','dictionary.json'),('fit_source_sha256','fit-sources.json'),('pool_sha256','pool.json')]:assert seal[key]==sha((arm/file).read_bytes())
            fit=json.loads((arm/'fit-sources.json').read_text());assert fit==checked(inp['fit'])=={p:texts[p] for p in map(str,c['partition']['dev_fit'])}
            reserved=set(ALPHABET)-set(''.join(fit.values()));assert reserved<=set(vocab)
            if name=='fixed96':assert set(ALPHABET)<=set(vocab)
            assert len(summary['moves'])<=c['search']['moves']
        expected=evaluate(texts,vocab,w,c)
        expected.update(arm=name,dictionary_sha256=sha((arm/'dictionary.json').read_bytes()),sources_sha256=sha((arm/'sources.json').read_bytes()),qualification_receipt_sha256=c['qualification']['sha256'])
        assert a==expected,(w,name,'cost/source/aggregate mismatch')
        if name in ('R','seed31'):
            prior=parent['baseline'][str(w)] if name=='R' else next(x for x in parent['arms'] if x['width']==w and x['arm']=='scope_joint')
            assert a['dictionary_bytes']==prior['dictionary_bytes'] and a['entries']==prior['entries']
            for pid,row in a['per_problem'].items():
                assert all(prior['per_problem'][pid][k]==v for k,v in row.items()),('parent cost mismatch',w,name,pid)
            for split in ('fit','validation'):
                for k in ('covered','selections','actions','single_character_fraction','package_bytes'):
                    assert a[split][k]==prior[split][k],('parent aggregate mismatch',w,name,split,k)
        db=analyze.dictionary_bytes(vocab);assert (arm/'dictionary.bin').read_bytes()==db
        good={pid for pid,row in a['per_problem'].items() if row['encodable']}
        assert {p.stem for p in (arm/'packets').glob('*.bin')}==good
        for pid in good:
            packet=(arm/'packets'/f'{pid}.bin').read_bytes()
            assert analyze.decode(db,packet)==texts[pid]
            # Exact equality verifies selected entry IDs, framing, padding and policy.
            assert packet==analyze.encode(vocab,analyze.shortest_encode(texts[pid],vocab),w)
        if name in ('fixed96','optional'):
            assert a['fit']['covered']==27 and a['fit']['selections']['total']==summaries[w,name]['fit_selections']
        for row in a['per_problem'].values():
            row['standalone_package_bytes']=len(db)+row['packet_bytes'] if row['encodable'] else None
            row['standalone_with_decoder_source']=row['standalone_package_bytes']+c['decoder_source_bytes'] if row['encodable'] else None
        for split,key in [('fit','dev_fit'),('validation','dev_val')]:
            rows=[a['per_problem'][str(pid)] for pid in c['partition'][key]];goodrows=[x for x in rows if x['encodable']]
            a[split].update(source_bytes=sum(len(texts[str(pid)].encode()) for pid in c['partition'][key]),
                framing_bytes=41*len(goodrows),payload_bits=w*sum(x['selections'] for x in goodrows),
                padding_bits=sum(8*(x['packet_bytes']-41)-w*x['selections'] for x in goodrows),
                single_character_codes=sum(x['single_characters'] for x in goodrows),
                package_with_decoder_source=a[split]['package_bytes']+c['decoder_source_bytes'])
    r['verdicts_by_width']={}
    for w in (7,8):
        a=arms[w,'optional'];groups={};paired={}
        for name,incremental in [('R',False),('seed31',True),('fixed96',True)]:
            groups[name],paired[name]=predicates(a,arms[w,name],c['partition']['dev_val'],incremental)
        r['verdicts_by_width'][str(w)]={'optional_successor':all(all(g.values()) for g in groups.values()),'checks':groups,'paired':paired}
    r['predictions']={
        'P1':arms[7,'R']['validation']['actions'] is not None and arms[8,'R']['validation']['actions'] is not None and arms[7,'R']['validation']['actions']['total']==1420 and arms[8,'R']['validation']['actions']['total']==949,
        'P2':any(arms[w,'optional']['fit']['covered']==arms[w,'fixed96']['fit']['covered']==27 and arms[w,'optional']['fit']['selections']['total']<arms[w,'fixed96']['fit']['selections']['total'] for w in (7,8)),
        'P3':not any(v['optional_successor'] for v in r['verdicts_by_width'].values()),
        'P4':all(a['qualified']==36 and a['fit']['covered']+a['validation']['covered']==36 and not a['illegal_entry_sha256'] for a in arms.values())}
    r['prediction_definitions']=c['predictions']
    r.update(decoder_source_bytes=c['decoder_source_bytes'],offline_encoder_bytes=c['offline_encoder_bytes'],
             runtime_footprint='Installed interpreter, NumPy/SciPy/HiGHS and standard library footprint unmeasured; not a deployment package claim.',
             cross_width_selection=False,qualification='Exact source/ID/width/arm passing item31 receipt reuse; zero new source execution.')
    return r

def main(folder):
    c=json.loads((HERE/'contract.json').read_text())
    try:r=replay(folder,c)
    except BaseException as error:
        receipt={'complete':False,'promotion_allowed':False,'verdicts_by_width':None,
                 'phase':'report_verification','error_type':type(error).__name__,
                 'reason':'Execution is incomplete/failed or artifact verification failed. No verdict is issued.'}
        (HERE/'evidence').mkdir(exist_ok=True)
        write(HERE/'evidence/results.json',receipt)
        if folder.is_dir():write(folder/'report-failure.json',receipt)
        (HERE/'README.md').write_text('# Python character slots\n\nReporting incomplete: **no verdict**. [Failure receipt](evidence/results.json).\n')
        raise
    (HERE/'evidence').mkdir(exist_ok=True);write(HERE/'evidence/results.json',r)
    lines=['# Python character slots','', '[Freeze](FREEZE.md); [design](DESIGN.md); [metadata](evidence/results.json).','',
           'Python only, 27 fit and nine consumed validation problems. Two independent width verdicts; no cross-width selection. Item31 is a mechanism anchor, not a ready candidate.','',
           '| Entries | Arm | Split | Covered | Actions | Median | p90 | Character fraction | Package |','| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for a in r['arms']:
        for split in ('fit','validation'):
            d=a[split];actions=d['actions'] or {k:'unavailable' for k in ('total','median','p90')};fraction=d['single_character_fraction']
            lines.append(f"| {2**a['width']} | {a['arm']} | {split} | {d['covered']}/{d['problems']} | {actions['total']} | {actions['median']} | {actions['p90']} | {fraction if fraction is not None else 'unavailable'} | {d['package_bytes']} |")
    for w,v in r['verdicts_by_width'].items():
        failed=[f'{base}:{k}' for base,g in v['checks'].items() for k,passed in g.items() if not passed]
        lines+=['',f"{2**int(w)}-entry optional successor: **{v['optional_successor']}**. Failed gates: {', '.join(failed) or 'none'}."]
    lines+=['','| Prediction | Observed |','| --- | --- |']+[f"| {key}: {c['predictions'][key]} | {value} |" for key,value in r['predictions'].items()]
    lines+=['','Costs charge full dictionary, packets, 41-byte headers, padding and one Finish. Decoder-inclusive costs add both pinned decoder sources; installed runtime footprint remains unmeasured. Failures remain in denominators. Reused finite qualification is not a semantic proof.', '',
            'M1 unchanged: 400/500, at most256entries, median at most32/p95 at most96 selections, at most10% single-character bits, zero whole-solution entries. This36-program development panel cannot qualify M1 or independent generalization.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
