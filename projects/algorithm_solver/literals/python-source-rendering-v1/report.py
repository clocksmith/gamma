"""Independent deterministic menu/cost/packet/seal/observation replay; no search."""
import argparse
import copy
import json
import os
from pathlib import Path
import resource
import signal
import time
from common import (HERE,LIT,engine,render,analyze,write,sha,contract,verify,checked,texts_checked,authority,
                    identity,variants_for,evaluate,seal_files,check_files)
from run import FIT_FILES,CHOICE_FILES,check_all_fit
import qualification

def paired(a,b,ids):
    better=worse=0
    for pid in map(str,ids):
        x,y=a['per_problem'][pid],b['per_problem'][pid]
        if not x['encodable'] and not y['encodable']:continue
        if not x['encodable']:worse+=1
        elif not y['encodable']:better+=1
        elif x['actions']<y['actions']:better+=1
        elif x['actions']>y['actions']:worse+=1
    return {'better':better,'same':len(ids)-better-worse,'worse':worse}

def gates(a,b,c,incremental=False):
    ids=c['partition']['dev_val'];v,z=a['validation'],b['validation'];pairs=paired(a,b,ids)
    complete=v['covered']==z['covered']==len(ids)
    checks={'all_qualified':a['qualified']==b['qualified']==36,'fit_coverage':a['fit']['covered']==b['fit']['covered']==27,
        'validation_coverage':complete,'audit_clean':not a['illegal_entry_sha256'] and not b['illegal_entry_sha256'],
        'entry_budget':a['entries']<=2**a['width'] and b['entries']<=2**b['width'],
        'actions':complete and (v['actions']['total']<z['actions']['total'] if incremental else v['actions']['total']<=.95*z['actions']['total']),
        'median':complete and (v['actions']['median']<=z['actions']['median'] if incremental else v['actions']['median']<z['actions']['median']),
        'p90':complete and (v['actions']['p90']<=z['actions']['p90'] if incremental else v['actions']['p90']<z['actions']['p90']),
        'improved':incremental or pairs['better']>=6,'worsened':pairs['worse']<=2,
        'character_fraction':complete and v['single_character_fraction']<=z['single_character_fraction'],
        'package':complete and v['package_bytes']<=1.05*z['package_bytes']}
    return {'passed':all(checks.values()),'checks':checks,'paired':pairs,
            'comparison_qualified':checks['all_qualified'] and checks['fit_coverage'] and checks['validation_coverage'] and checks['audit_clean']}

def verdicts(arms,c):
    out={}
    for width in (7,8):
        candidates={}
        for name in ('S','J'):
            a=arms[width,name]
            checks={ref:gates(a,arms[width,ref],c,incremental=incremental)
                    for ref,incremental in [('R',False),('D',False),('U',True)]}
            if name=='J':checks['S']=gates(a,arms[width,'S'],c,incremental=True)
            candidates[name]={'ready':all(x['passed'] for x in checks.values()),'comparisons':checks}
        out[str(width)]=candidates
    return out

def verify_menus(texts,stored):
    groups,expected=engine.source_menus(texts)
    assert set(stored)==set(expected)
    for pid in texts:
        assert stored[pid]['candidates']==expected[pid]['candidates']
        assert render.public_summary(stored[pid])==render.public_summary(expected[pid])
    return groups,expected

def verify_packets(folder,texts,vocab,width,rows):
    db=analyze.dictionary_bytes(vocab);assert (folder/'dictionary.bin').read_bytes()==db
    good={pid for pid,row in rows.items() if row['encodable']}
    assert {path.stem for path in (folder/'packets').glob('*.bin')}==good
    for pid in good:
        packet=(folder/'packets'/f'{pid}.bin').read_bytes()
        decoded=analyze.decode(db,packet)
        assert decoded==texts[pid] and sha(decoded.encode())==rows[pid]['source_sha256']
        assert packet==analyze.encode(vocab,analyze.shortest_encode(texts[pid],vocab),width)

def augment_costs(a,texts,c):
    for row in a['per_problem'].values():
        row['standalone_package_bytes']=a['dictionary_bytes']+row['packet_bytes'] if row['encodable'] else None
        row['standalone_with_decoder_source']=row['standalone_package_bytes']+c['decoder_source_bytes'] if row['encodable'] else None
    for split,key in [('fit','dev_fit'),('validation','dev_val')]:
        ids=list(map(str,c['partition'][key]));rows=[a['per_problem'][pid] for pid in ids if a['per_problem'][pid]['encodable']]
        a[split].update(source_bytes=sum(len(texts[pid].encode()) for pid in ids),framing_bytes=41*len(rows),
            payload_bits=a['width']*sum(row['selections'] for row in rows),
            padding_bits=sum(8*(row['packet_bytes']-41)-a['width']*row['selections'] for row in rows),
            single_character_codes=sum(row['single_characters'] for row in rows),
            package_with_decoder_source=a[split]['package_bytes']+c['decoder_source_bytes'])
        complete=len(rows)==len(ids)
        a[split].update(full_cohort_cost_available=complete,
            aggregate_scope='full_cohort' if complete else 'encoded_rows_only; incomplete cohort',
            full_cohort_actions=a[split]['actions'] if complete else None,
            full_cohort_selections=a[split]['selections'] if complete else None,
            full_cohort_character_fraction=a[split]['single_character_fraction'] if complete else None,
            full_cohort_package_bytes=a[split]['package_bytes'] if complete else None)

def replay(folder,c):
    verify(c)
    assert not list(folder.rglob('failure.json')),'failed execution'
    assert json.loads((folder/'status.json').read_text())['complete'] is True
    supervisor=json.loads((folder/'supervisor-receipt.json').read_text())
    assert supervisor['complete'] and supervisor['exit_code']==0 and not supervisor['outer_timeout']
    digest=sha((HERE/'contract.json').read_bytes())
    assert supervisor['contract_sha256']==digest
    assert json.loads((folder/'run-binding.json').read_text())=={'contract_sha256':digest}
    result=json.loads((folder/'results.json').read_text());assert result['contract_sha256']==digest
    arm_map={(a['width'],a['arm']):a for a in result['arms']}
    assert len(result['arms'])==10 and set(arm_map)=={(w,a) for w in (7,8) for a in (*engine.ARMS,'R')}
    allfit=check_all_fit(folder);allchoice=json.loads((folder/'all-choices-seal.json').read_text())
    assert allchoice['case_data_loaded'] is False
    assert allchoice['all_fit_seal_sha256']==sha((folder/'all-fit-seal.json').read_bytes())
    assert set(allchoice['arms'])==set(allfit['arms']) and set(allchoice['references'])=={'7','8'}
    ids=set(map(str,c['partition']['dev_fit']+c['partition']['dev_val']))
    specs={str(row['id']):row for row in c['sources']};qjobs={};private={}
    for width in (7,8):
        parent=texts_checked(c,width);seed=checked(c['inputs'][str(width)]['seed_dictionary'])
        fitbase={str(pid):parent[str(pid)] for pid in c['partition']['dev_fit']}
        valbase={str(pid):parent[str(pid)] for pid in c['partition']['dev_val']}
        assert fitbase==texts_checked(c,width,fit_only=True)
        for name in (*engine.ARMS,'R'):
            arm=folder/f'w{width}'/name;a=arm_map[width,name]
            sources=json.loads((arm/'sources.json').read_text());vocab=json.loads((arm/'dictionary.json').read_text())
            assert set(sources)==ids and len(set(vocab))==len(vocab)<=2**width
            assert set(render.ALPHABET)<=set(vocab) and vocab==engine.parent.v3.joint.order(vocab)
            if name=='R':
                assert sources==texts_checked(c,width,original=True)
                assert vocab==checked(c['inputs'][str(width)]['baseline_dictionary'])
                check_files(arm,allchoice['references'][str(width)])
                assert set(allchoice['references'][str(width)])=={'sources.json','dictionary.json','unqualified-results.json'}
                menus={pid:{'candidates':{'original':text}} for pid,text in sources.items()}
                old=sources;menu_summary=None
            else:
                old=parent;key=identity(width,name);summary=allchoice['arms'][key]
                assert summary['width']==width and summary['arm']==name
                assert summary['choices_seal_sha256']==sha((arm/'choices-seal.json').read_bytes())
                seal=json.loads((arm/'choices-seal.json').read_text())
                assert seal['case_data_loaded'] is False and set(seal['files'])==set(CHOICE_FILES);check_files(arm,seal['files'])
                fg,fm=verify_menus(fitbase,json.loads((arm/'fit-menus.json').read_text()))
                vg,vm=verify_menus(valbase,json.loads((arm/'validation-menus.json').read_text()))
                menus={**fm,**vm}
                fv=variants_for(name,fitbase,fg);vv=variants_for(name,valbase,vg)
                assert json.loads((arm/'fit-variants.json').read_text())==fv
                assert json.loads((arm/'validation-variants.json').read_text())==vv
                fit_choice,ft=engine.choose(fitbase,fv,vocab,width);val_choice,vt=engine.choose(valbase,vv,vocab,width)
                assert sources=={**fit_choice,**val_choice}
                assert json.loads((arm/'fit-sources.json').read_text())==fit_choice
                assert json.loads((arm/'validation-choices.json').read_text())==vt
                record=json.loads((arm/'fit-record.json').read_text())
                assert record['arm']==name and record['validation_loaded'] is False and record['case_data_loaded'] is False
                assert record['source_choices']==ft and record['fit_selections']==sum(x['selections'] for x in ft.values())
                assert len(record['search'])==(2 if name in ('D','J') else 1)
                assert all(0<r['trials']<=c['search']['trials'] for r in record['search'])
                assert record['search'][-1]['selections']==record['fit_selections']
                if name in ('U','S'):assert vocab==seed
                if name in ('U','D'):assert sources==parent
                menu_summary={pid:render.public_summary(m) for pid,m in menus.items()}
            expected=evaluate(sources,vocab,width,c,menus)
            expected.update(arm=name,source_choice_count=sum(sources[pid]!=old[pid] for pid in ids))
            assert json.loads((arm/'unqualified-results.json').read_text())==expected
            assert {k:v for k,v in a.items() if k not in ('qualification','qualified')}==expected
            if name in ('U','R'):
                prior=authority(c,width) if name=='U' else checked(c['qualification'])['baseline'][str(width)]
                for key in ('entries','dictionary_bytes','per_problem','fit','validation'):
                    if key=='per_problem':
                        assert all(all(prior[key][pid][k]==v for k,v in row.items()) for pid,row in expected[key].items())
                    elif key in ('fit','validation'):
                        assert all(prior[key][k]==expected[key][k] for k in ('covered','selections','actions','single_character_fraction','package_bytes'))
                    else:assert prior[key]==expected[key]
            verify_packets(arm,sources,vocab,width,a['per_problem'])
            for pid,text in sources.items():
                if text!=old[pid]:qjobs[f'{pid}-{sha(text.encode())}']=(specs[pid],text)
            private[width,name]=(sources,old,menu_summary)
    plan=json.loads((folder/'qualification-plan.json').read_text())
    assert plan=={'all_choices_seal_sha256':sha((folder/'all-choices-seal.json').read_bytes()),'keys':sorted(qjobs),
                  'new_sources':len(qjobs),'cases':sum(spec['cases'] for spec,text in qjobs.values())}
    qstored=json.loads((folder/'qualification-private.json').read_text());assert set(qstored)==set(qjobs)
    assert {p.name for p in (folder/'qualification').iterdir()}==set(qjobs) if qjobs else not (folder/'qualification').exists()
    receipts={}
    for key,(spec,text) in qjobs.items():
        receipts[key]=qualification.replay(folder/'qualification'/key,spec,text,c)
        assert receipts[key]==qstored[key]
    assert result['fresh_sources']==len(receipts) and result['fresh_cases']==sum(q['cases'] for q in receipts.values())
    for (width,name),a in arm_map.items():
        sources,old,menu_summary=private[width,name];expected_q={}
        for pid,text in sources.items():
            if text==old[pid]:q={'passed':True,'reused':True,'receipt_sha256':c['qualification']['sha256']}
            else:
                key=f'{pid}-{sha(text.encode())}';receipt=receipts[key]
                q={'passed':receipt['passed'],'reused':False,'checks_passed':receipt['checks_passed'],'cases':receipt['cases'],
                   'receipt_sha256':sha((folder/'qualification'/key/'receipt.json').read_bytes())}
            expected_q[pid]=q
        assert a['qualification']==expected_q and a['qualified']==sum(q['passed'] for q in expected_q.values())
        a['source_menu_summary']=menu_summary
        a['changed_sources_by_split']={key:sum(sources[str(pid)]!=old[str(pid)] for pid in c['partition'][split])
            for key,split in [('fit','dev_fit'),('validation','dev_val')]}
        if name!='R':
            record=json.loads((folder/identity(width,name)/'fit-record.json').read_text())
            a['search_rounds']=[{key:r[key] for key in ('trials','seconds','selections','stop')} for r in record['search']]
        else:a['search_rounds']=[]
        a['representation_eligible']=not a['illegal_entry_sha256']
        a['full_cohort_qualified']=a['qualified']==36 and a['fit']['covered']==27 and a['validation']['covered']==9
        a['costs_scope']='Per-split coverage determines cost scope. Incomplete encoded-row costs are explicitly partial; no eligible-candidate claim if coverage, legality or qualification fails.'
        augment_costs(a,sources,c)
    result['verdicts_by_width']=verdicts(arm_map,c)
    def less(width,a,b):
        x,y=arm_map[width,a],arm_map[width,b]
        return x['full_cohort_qualified'] and y['full_cohort_qualified'] and x['representation_eligible'] and y['representation_eligible'] and x['validation']['actions']['total']<y['validation']['actions']['total']
    result['predictions']={
        'P1':all(a['full_cohort_qualified'] and a['representation_eligible'] for a in arm_map.values()),
        'P2':any(less(w,'S','U') for w in (7,8)), 'P3':any(less(w,'J','D') for w in (7,8)),
        'P4':any(less(w,'J','S') for w in (7,8)),
        'P5':not any(v['ready'] for width in result['verdicts_by_width'].values() for v in width.values())}
    result.update(complete=True,prediction_definitions=c['predictions'],independent_replay=True,
        decoder_source_bytes=c['decoder_source_bytes'],offline_encoder_bytes=c['offline_encoder_bytes'],
        runtime_footprint='Installed Python and standard library footprint unmeasured; no deployment-size claim.',
        offline_model_bytes=0,training_compute=0,cross_width_selection=False,
        fit_seconds_by_arm={key:value['elapsed'] for key,value in allfit['arms'].items()},
        supervisor_elapsed=supervisor['elapsed'],fresh_qualification_failed=sum(not q['passed'] for q in receipts.values()),
        fresh_qualification_batch_wall_seconds=sum(b['wall_seconds'] for q in receipts.values() for b in q['batches']),
        claim_scope='Python 27 fit / 9 consumed validation, own-width item31 scope_joint sources. Not M1 qualification.')
    return result

def failure(folder,error):
    receipt={'complete':False,'independent_replay':False,'promotion_allowed':False,'verdicts_by_width':None,
             'phase':'report_verification','error_type':type(error).__name__,
             'reason':'Incomplete execution or artifact verification failure; no verdict.'}
    if folder.is_dir():write(folder/'report-failure.json',receipt)
    return receipt

def publish(folder,c,output):
    started=time.monotonic()
    try:result=replay(folder,c)
    except (Exception,KeyboardInterrupt) as error:
        result=failure(folder,error);output.mkdir(parents=True,exist_ok=True);write(output/'results.json',result)
        raise
    result['independent_replay_seconds']=time.monotonic()-started
    output.mkdir(parents=True,exist_ok=True);write(output/'results.json',result)
    lines=['# Python source rendering and dictionary stack','',
        'Exact item31 development panel: 27 fit and nine consumed validation problems. Widths have separate verdicts. Full costs remain descriptive when any coverage, qualification or legality gate fails.','',
        '| Entries | Arm | Split | Covered | Qualified / 36 | Actions | Median | p90 | Character fraction | Package |',
        '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        for split in ('fit','validation'):
            d=arm[split];a=d['full_cohort_actions'] or {k:None for k in ('total','median','p90')}
            lines.append(f"| {2**arm['width']} | {arm['arm']} | {split} | {d['covered']}/{d['problems']} | {arm['qualified']} | {a['total']} | {a['median']} | {a['p90']} | {d['full_cohort_character_fraction']} | {d['full_cohort_package_bytes']} |")
    for width,arms in result['verdicts_by_width'].items():
        for name,verdict in arms.items():
            failed=[f'{reference}:{gate}' for reference,group in verdict['comparisons'].items() for gate,passed in group['checks'].items() if not passed]
            lines+=['',f"{2**int(width)} {name} ready: **{verdict['ready']}**. Failed gates: {', '.join(failed) or 'none'}."]
    lines+=['','| Prediction | Observed |','| --- | --- |']+[f"| {key}: {c['predictions'][key]} | {value} |" for key,value in result['predictions'].items()]
    lines+=['','Every package charges the full shared dictionary once, all packets, 41-byte headers, padding and one Finish per program. Decoder-inclusive columns add pinned decoder sources; offline encoder inventory and wall time are separate. Runtime footprint remains unmeasured.','',
        'No final-heldout or closed Python14 data was used. Strict finite qualification is not a semantic equivalence proof. These results cannot establish M1 or independent generalization.','']
    (output/'REPORT.md').write_text('\n'.join(lines))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,default=HERE/'evidence');args=ap.parse_args()
    c=contract();os.sched_setaffinity(0,{c['cores'][0]})
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)
    def deadline(signum,frame):raise TimeoutError('frozen report deadline')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(c['limits']['report_seconds'])
    try:publish(args.run,c,args.output)
    finally:signal.alarm(0)
if __name__=='__main__':main()
