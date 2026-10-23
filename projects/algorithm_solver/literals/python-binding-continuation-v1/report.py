"""Rebuild sanitized reporting only; never fits, rewrites or qualifies sources."""
import argparse
import json
from pathlib import Path
from backend import HERE,LIT,analyze,tail,banned,parent_qualified_sources

def paired(rows,reference,ids):
    counts={'better':0,'same':0,'worse':0,'failed':0}
    for pid in ids:
        a,b=rows[str(pid)],reference[str(pid)]
        if not a['encodable']:counts['failed']+=1;counts['worse']+=1
        elif not b['encodable']:counts['better']+=1
        else:counts['better' if a['actions']<b['actions'] else 'worse' if a['actions']>b['actions'] else 'same']+=1
    return counts

def indicators(a):
    v=a['validation']
    return (v['covered']==v['problems'] and not a['illegal_entry_sha256'] and a['entries']<=256
            and v['selections']['median']<=32 and v['selections']['p95']<=96
            and v['single_character_fraction'] is not None and v['single_character_fraction']<=.10)

def predicates(a,b,ids,incremental=False):
    v,base=a['validation'],b['validation'];p=paired(a['per_problem'],b['per_problem'],ids)
    complete=v['covered']==base['covered']==len(ids)
    checks={'all_qualified':a['qualified']==36,'coverage':complete,'whole_solution_clean':not a['illegal_entry_sha256'],
            'comparator_qualified':b.get('qualified',36)==36,'comparator_audit_clean':not b['illegal_entry_sha256']}
    checks.update(actions=(complete and (v['actions']['total']<base['actions']['total'] if incremental else v['actions']['total']<=.95*base['actions']['total'])),
        median=(complete and (v['actions']['median']<=base['actions']['median'] if incremental else v['actions']['median']<base['actions']['median'])),
        p90=(complete and (v['actions']['p90']<=base['actions']['p90'] if incremental else v['actions']['p90']<base['actions']['p90'])),
        improved=(True if incremental else p['better']>=6),worsened=p['worse']<=2,
        fallback=(complete and v['single_character_fraction']<=base['single_character_fraction']),
        package=(complete and v['package_bytes']<=1.05*base['package_bytes']))
    return checks,p

def main(folder):
    assert not (folder/'failure.json').exists(),'failed/partial run has no promotion report'
    assert json.loads((folder/'status.json').read_text())['complete']
    assert json.loads((folder/'supervisor-receipt.json').read_text())['complete']
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    qs=json.loads((folder/'qualification-private.json').read_text());passed=parent_qualified_sources(c)
    assert set(c['decoder_source_files'])=={'literals.py','pass2/working/bitpack.py'}
    for rel,receipt in c['decoder_source_files'].items():
        decoder_raw=(LIT/rel).read_bytes()
        assert analyze.sha(decoder_raw)==receipt['sha256'] and len(decoder_raw)==receipt['bytes']
    assert c['decoder_source_bytes']==sum(x['bytes'] for x in c['decoder_source_files'].values())>0
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    all_ids=c['partition']['dev_fit']+c['partition']['dev_val'];ids=c['partition']['dev_val'];entries={x['id']:x['entry'] for x in c['sources']}
    arms={(a['width'],a['arm']):a for a in r['arms']}
    assert set(arms)=={(w,a) for w in (7,8) for a in ('control','global','global_joint','scope','scope_joint')}
    allseal=json.loads((folder/'all-fit-seal.json').read_text());assert allseal['validation_loaded'] is False
    choices=json.loads((folder/'choices-seal.json').read_text());baseline={}
    for w in (7,8):
        wf=folder/f'w{w}';assert analyze.sha((wf/'fit-seal.json').read_bytes())==allseal['widths'][str(w)]
        original={int(k):v for k,v in json.loads((wf/'control/sources.json').read_text()).items()}
        assert set(original)==set(all_ids)
        for row in c['sources']:assert analyze.sha(original[row['id']].encode())==row['sha256']
        vocab=json.loads((wf/'baseline-dictionary.json').read_text())
        baseline_raw=Path(c['baseline_dictionaries'][str(w)]['file']).read_bytes()
        assert analyze.sha(baseline_raw)==c['baseline_dictionaries'][str(w)]['sha256']
        assert vocab==json.loads(baseline_raw)
        rows,illegal=tail.evaluate_output(original,vocab,w,banned({p:{'original':t} for p,t in original.items()},entries));db=len(analyze.dictionary_bytes(vocab))
        for row in rows.values():
            row['standalone_package_bytes']=db+row['packet_bytes'] if row['encodable'] else None
            row['standalone_package_with_decoder_source']=row['standalone_package_bytes']+c['decoder_source_bytes'] if row['encodable'] else None
        baseline[str(w)]={'per_problem':rows,'fit':tail.aggregate(rows,c['partition']['dev_fit'],db),
                         'validation':tail.aggregate(rows,ids,db),'illegal_entry_sha256':illegal,'qualified':36,'dictionary_bytes':db,'entries':len(vocab)}
    for (w,name),a in arms.items():
        arm=folder/f'w{w}'/name;seal=json.loads((folder/f'w{w}/fit-seal.json').read_text())
        for f,h in seal['arms'][name].items():assert analyze.sha((arm/f).read_bytes())==h
        assert a['dictionary_sha256']==seal['arms'][name]['dictionary.json']
        assert analyze.sha((arm/'sources.json').read_bytes())==choices[f'{w}/{name}']
        texts=json.loads((arm/'sources.json').read_text());vocab=json.loads((arm/'dictionary.json').read_text());db=analyze.dictionary_bytes(vocab)
        assert set(texts)==set(a['per_problem'])==set(a['qualification'])==set(map(str,all_ids))
        fitvars={int(k):v for k,v in json.loads((arm/'fit-variants.json').read_text()).items()}
        valvars={int(k):v for k,v in json.loads((arm/'validation-variants.json').read_text()).items()}
        illegal=sorted(analyze.sha(t.encode()) for t in set(vocab)&banned({**fitvars,**valvars},entries))
        assert illegal==a['illegal_entry_sha256']
        replay,again_illegal=tail.evaluate_output({int(k):v for k,v in texts.items()},vocab,w,banned({**fitvars,**valvars},entries))
        assert again_illegal==illegal
        for split,subset in [('fit',c['partition']['dev_fit']),('validation',ids)]:
            assert tail.aggregate(replay,subset,len(db))==a[split],(w,name,split)
        for pid,row in a['per_problem'].items():
            assert row['source_sha256']==analyze.sha(texts[pid].encode())
            assert row['original_sha256']==next(x['sha256'] for x in c['sources'] if str(x['id'])==pid)
            assert {k:v for k,v in row.items() if k!='original_sha256'}==replay[pid]
            if row['encodable']:
                packet=(arm/'packets'/f'{pid}.ltv').read_bytes()
                assert analyze.decode(db,packet)==texts[pid]
                assert packet==analyze.encode(vocab,analyze.shortest_encode(texts[pid],vocab),w)
            if row['source_sha256']==row['original_sha256']:
                assert (pid,row['source_sha256']) in passed
                expected_q={'passed':True,'reused':True,'receipt_sha256':c['parent_results_sha256']}
            else:
                receipt=qs[f'{pid}-{row["source_sha256"]}']
                expected_q={**{k:v for k,v in receipt.items() if k!='failures'},'reused':False}
            assert a['qualification'][pid]==expected_q
        assert a['qualified']==sum(q['passed'] for q in a['qualification'].values())
        for row in a['per_problem'].values():
            row['standalone_package_bytes']=len(db)+row['packet_bytes'] if row['encodable'] else None
            row['standalone_package_with_decoder_source']=row['standalone_package_bytes']+c['decoder_source_bytes'] if row['encodable'] else None
        a['checks_baseline'],a['paired_baseline']=predicates(a,baseline[str(w)],ids)
        a['checks_control'],a['paired_control']=predicates(a,arms[w,'control'],ids)
        a['ready_baseline']=all(a['checks_baseline'].values());a['ready_control']=all(a['checks_control'].values())
        a['scope_successor']=False
        if name.startswith('scope'):
            matched='global_joint' if name.endswith('_joint') else 'global'
            a['checks_matched_global'],a['paired_matched_global']=predicates(a,arms[w,matched],ids,True)
            a['scope_successor']=a['ready_baseline'] and a['ready_control'] and all(a['checks_matched_global'].values())
        a['m1_cost_indicators_only']=indicators(a)
        for split,subset in [('fit',c['partition']['dev_fit']),('validation',ids)]:
            rows=[a['per_problem'][str(pid)] for pid in subset];good=[x for x in rows if x['encodable']]
            a[split].update(qualified=sum(a['qualification'][str(pid)]['passed'] for pid in subset),
                qualification_failed_ids=[pid for pid in subset if not a['qualification'][str(pid)]['passed']],
                changed=sum(x['source_sha256']!=x['original_sha256'] for x in rows),framing_bytes=41*len(good),
                payload_bits=w*sum(x['selections'] for x in good),padding_bits=sum(8*(x['packet_bytes']-41)-w*x['selections'] for x in good),
                source_bytes=sum(len(texts[str(pid)].encode()) for pid in subset),
                single_character_codes=sum(x['single_characters'] for x in good),
                package_with_decoder_source=a[split]['package_bytes']+c['decoder_source_bytes'])
    r['baseline']=baseline;r['predictions']={
        'P1':all(baseline[str(w)]['validation']['covered']==9 for w in (7,8)) and baseline['7']['validation']['actions']['total']==1420 and baseline['8']['validation']['actions']['total']==949,
        'P2':any(arms[w,'scope']['fit']['covered']==arms[w,'global']['fit']['covered']==27 and arms[w,'scope']['fit']['selections']['total']<arms[w,'global']['fit']['selections']['total'] for w in (7,8)),
        'P3':arms[8,'scope_joint']['validation']['covered']==arms[8,'global_joint']['validation']['covered']==9 and arms[8,'scope_joint']['validation']['actions']['total']<arms[8,'global_joint']['validation']['actions']['total'],
        'P4':all(a['qualified']==36 and a['fit']['covered']+a['validation']['covered']==36 and not a['illegal_entry_sha256'] for a in arms.values()),
        'P5':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    eligible=sorted((a for a in arms.values() if a['scope_successor']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['width'],a['arm']))
    r['selected_ready_arm']=[eligible[0]['arm'],2**eligible[0]['width']] if eligible else None
    qraw=(folder/'qualification-private.json').read_bytes();qs=json.loads(qraw)
    r['fresh_qualification_summary']={'distinct_sources':len(qs),'passed':sum(x['passed'] for x in qs.values()),
        'checks_passed':sum(x['checks_passed'] for x in qs.values()),'checks_total':sum(x['cases'] for x in qs.values())}
    r.update(private_results_sha256=analyze.sha(raw),qualification_receipt_sha256=analyze.sha(qraw),
             offline_encoder_bytes=c['offline_encoder_bytes'],offline_encoder_scope=c['offline_encoder_scope'],decoder_source_bytes=c['decoder_source_bytes'],decoder_source_files=c['decoder_source_files'])
    def safe(v):
        if isinstance(v,dict):
            assert not {'trace','_trace','accepted_colors','sources','vocab','failures'}&set(v)
            for item in v.values():safe(item)
        elif isinstance(v,list):
            for item in v:safe(item)
    safe(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Python scope naming continuation', '', '[Freeze](FREEZE.md), [newline amendment](AMENDMENT-1.md), [review receipt](REVIEW.md), [design](DESIGN.md), [metadata evidence](evidence/results.json).', '',
        f'Selected development successor: **{r["selected_ready_arm"] or "none"}**. Python only: 27 fit and nine consumed validation problems. '
        'No protected access, new confirmation, M1 qualification or JS/Python pooled claim.', '',
        '| Entries | Arm | Split | Decode | Qualify | Selections | Median | p90 | p95 | Actions | Character fraction | Package |',
        '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for (w,name),a in sorted(arms.items()):
        for split in ('fit','validation'):
            d=a[split];s=d['selections'] or {k:'unavailable' for k in ('total','median','p90','p95')}
            actions=d['actions']['total'] if d['actions'] is not None else 'unavailable'
            fraction=f"{100*d['single_character_fraction']:.2f}%" if d['single_character_fraction'] is not None else 'unavailable'
            lines.append(f'| {2**w} | {name} | {split} | {d["covered"]}/{d["problems"]} | {d["qualified"]}/{d["problems"]} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {actions} | {fraction} | {d["package_bytes"]} |')
    lines+=['','Costs include encoded candidates; failed qualification invalidates gain claims. Exact packet decoding, full source, dictionary,41-byte headers,padding and one Finish are charged. '
        f'Decoder-source-inclusive costs add {c["decoder_source_bytes"]:,} bytes for the pinned literals.py and pass2/working/bitpack.py; per-program standalone costs charge the whole dictionary and both decoder sources. '
        'Installed Python/stdlib footprint is unmeasured. All eligible locals are compared under the same conservative scope rules; public parameter names and captured names remain fixed.','',
        '| Entries | Arm | Better/same/worse vs baseline | Baseline ready | Searched-control ready | Scope successor | Failed predicates |',
        '| ---: | --- | --- | --- | --- | --- | --- |']
    for (w,name),a in sorted(arms.items()):
        p=a['paired_baseline'];failed=[]
        for group in ('checks_baseline','checks_control','checks_matched_global'):
            failed += [group+':'+k for k,v in a.get(group,{}).items() if not v]
        lines.append(f'| {2**w} | {name} | {p["better"]}/{p["same"]}/{p["worse"]} | {a["ready_baseline"]} | {a["ready_control"]} | {a["scope_successor"]} | {", ".join(failed) or "none"} |')
    lines+=['','| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    q=r['fresh_qualification_summary'];lines+=['',f'Fresh qualification: {q["passed"]}/{q["distinct_sources"]} distinct changed programs, '
        f'{q["checks_passed"]}/{q["checks_total"]} checks passed. Original sources reuse exact-hash passing item6 receipts. No retries or repairs.', '',
        f'Measured run wall time: {r["seconds"]:.2f} seconds. Search/qualification counts, stop reasons and per-ID metadata are in evidence. '
        'The 29 prelaunch synthetic checks establish focused implementation checks, not numerical qualification.', '',
        'M1 remains400/500,<=256entries,median<=32,p95<=96selections,<=10%single-character bits,zero whole-solution entries. '
        'This36-program panel cannot qualify it. Component intent preserved; no production, admission or publication authority changed.', '',
        'Rebuild with `python3 -B projects/algorithm_solver/literals/python-binding-continuation-v1/report.py --run /private/run/path`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
