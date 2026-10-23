"""Rebuild a sanitized cost and conditional-attribution report from private receipts."""
import argparse
import json
from pathlib import Path
from run import HERE,LIT,analyze


def paired(a,b,ids):
    delta=[a[str(i)]['actions']-b[str(i)]['actions'] for i in ids]
    return {'n':len(ids),'better':sum(d<0 for d in delta),'same':sum(d==0 for d in delta),
        'worse':sum(d>0 for d in delta),'action_delta':sum(delta),
        'typed_actions':sum(a[str(i)]['actions'] for i in ids),'literal_actions':sum(b[str(i)]['actions'] for i in ids)}


def main(folder):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw)
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    c=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text());ids=c['partition']['dev_val']
    sources={str(x['id']):x['sha256'] for x in c['sources']}
    arms={(a['width'],a['arm']):a for a in r['arms']}
    assert set(arms)=={(w,n) for w in (7,8) for n in ('literal','typed')}
    for (w,n),a in arms.items():
        private=folder/f'{n}-{2**w}';seal=json.loads((private/'fit-seal.json').read_text())
        assert seal['validation_loaded'] is False
        assert seal['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((private/'dictionary.bin').read_bytes())
        assert seal['dictionary_json_sha256']==analyze.sha((private/'dictionary.json').read_bytes())
        assert seal['pool_sha256']==analyze.sha((private/'pool.json').read_bytes())
        assert set(a['per_problem'])==set(sources)
        keys=json.loads((private/'dictionary.json').read_text())
        usage=[{'fit_programs':0,'validation_programs':0,'fit_codes':0,'validation_codes':0} for _ in keys]
        for pid,row in a['per_problem'].items():
            assert row['source_sha256']==sources[pid]
            packet=(private/'packets'/f'{pid}.bin').read_bytes()
            assert row['packet_sha256']==analyze.sha(packet)
            bitstring=int.from_bytes(packet[41:],'big');padding=row['padding_bits']
            codes=[(bitstring>>(padding+w*i))&((1<<w)-1) for i in range(row['selections'])]
            split='fit' if int(pid) in c['partition']['dev_fit'] else 'validation'
            from collections import Counter
            for code,count in Counter(codes).items():
                usage[code][split+'_programs']+=1;usage[code][split+'_codes']+=count
            row['one_program_package_bytes']=a['dictionary_bytes']+row['packet_bytes']
            row['one_program_package_with_decoder_dependencies']=row['one_program_package_bytes']+a['decoder_dependency_bytes']
        a['entry_metadata']=[{'key_sha256':analyze.sha(key.encode()),'kind':key[0],
            'literal_bytes':len(key[1:].encode()) if key[0]=='L' else None,
            'constructor_spec_bytes':len(key[1:].encode()) if key[0]=='C' else None,**u} for key,u in zip(keys,usage)]
        a['full_400_package_bytes']=a['dictionary_bytes']+sum(x['packet_bytes'] for x in a['per_problem'].values())
        a['full_400_package_with_decoder_dependencies']=a['full_400_package_bytes']+a['decoder_dependency_bytes']
        a['fit_seal_sha256']=analyze.sha((private/'fit-seal.json').read_bytes())
        v=a['validation']
        a['m1_cost_indicators_only']=(v['covered']==100 and not a['illegal_entry_sha256'] and
            v['selections']['median']<=32 and v['selections']['p95']<=96 and v['single_character_fraction']<=.1)
    for w in (7,8):
        a,b=arms[w,'typed'],arms[w,'literal'];v,bv=a['validation'],b['validation']
        assert a['validation_eligible_ids']==b['validation_eligible_ids']
        eligible=a['validation_eligible_ids'];other=[i for i in ids if i not in eligible]
        a['paired']={n:paired(a['per_problem'],b['per_problem'],part) for n,part in [('all',ids),('eligible',eligible),('complement',other)]}
        p=a['paired']['all']
        a['readiness_checks']={'coverage':v['covered']==100,'audits_clean':not a['illegal_entry_sha256'],
            'actions_5_percent':v['actions']['total']<=.95*bv['actions']['total'],
            'median_lower':v['actions']['median']<bv['actions']['median'],'p90_lower':v['actions']['p90']<bv['actions']['p90'],
            'improved_60':p['better']>=60,'worsened_at_most_25':p['worse']<=25,
            'fallback_nonincrease':v['single_character_fraction']<=bv['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*bv['package_bytes']}
        a['ready']=all(a['readiness_checks'].values())
    baseline=json.loads((LIT/'cost-decomposition-v1/evidence/results.json').read_text())['arms']
    r['predictions']={'X1':all(a['initial_fit_selections']==baseline[str(w)]['dev_fit']['selections']['total'] and
            a['initial_validation_selections']==baseline[str(w)]['dev_val']['selections']['total'] for (w,n),a in arms.items()),
        'X2':.95*arms[8,'literal']['validation']['actions']['total']<arms[8,'typed']['validation']['actions']['total']<arms[8,'literal']['validation']['actions']['total'],
        'X3':arms[7,'typed']['validation']['actions']['total']>=arms[7,'literal']['validation']['actions']['total'],
        'X4':all(a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'X5':all(arms[w,'typed']['validation']['package_with_decoder_dependencies']>arms[w,'literal']['validation']['package_with_decoder_dependencies'] for w in (7,8)),
        'X6':not any(arms[w,'typed']['m1_cost_indicators_only'] for w in (7,8))}
    ready=sorted((a for a in arms.values() if a.get('ready')),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_with_decoder_dependencies'],a['width']))
    r['selected_input_candidate_width']=2**ready[0]['width'] if ready else None
    r['private_results_sha256']=analyze.sha(raw)
    def clean(v):
        if isinstance(v,dict):
            assert not {'keys','tokens','trace','sources','constructors','expression_literals','parts','spec','dictionary'}&set(v)
            for x in v.values():clean(x)
        elif isinstance(v,list):
            for x in v:clean(x)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Prefix expression constructors on fixed R sources','',
        '[Freeze](FREEZE.md) pushed in `9e83e182c`; [review and run receipt](REVIEW.md); [sanitized evidence](evidence/results.json).', '',
        f'Input candidate: **{r["selected_input_candidate_width"] or "none"}**. Goal 2c is a separate representation track. These consumed-development results do not qualify M1 or autonomous assembly.', '',
        'The 128-entry typed arm saves 181 validation actions (1.28%) versus its searched literal control; the 256-entry arm saves 42 (0.46%). Neither passes the frozen readiness criteria. The 128-entry literal search itself regresses by 80 validation actions versus the pinned baseline, so its typed gain is 101 actions versus that baseline. Conditional eligibility covers 99 of 100 validation programs; actual constructor use is narrower. These are small measured benefits, not an impossibility finding.', '',
        '## Costs', '',
        '| Entries | Arm | Split | Selections | Median / p90 / p95 / worst | <=32 / <=96 | Actions | Single-char | Constructor codes / programs | Raw package | With decoder dependencies |',
        '| ---: | --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: |']
    for (w,n),a in sorted(arms.items()):
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {2**w} | {n} | {split} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {100*d["single_character_fraction"]:.2f}% | {d["constructor_codes"]}/{d["constructor_programs"]} | {d["package_bytes"]} | {d["package_with_decoder_dependencies"]} |')
    lines+=['', 'All four arms decode 400/400 packets exactly to their pinned source hashes. Source bytes are unchanged; existing qualification is reused. No fresh execution, unseen-correctness or generalization claim. One Finish is included per program. Every constructor and child consumes a code; prefix arity supplies boundaries. Dictionary metadata, 41-byte headers and padding are charged.', '',
        'Decoder dependencies count the typed decoder and Acorn source, or canonical literals.py and bitpack.py. Complete installed Node/CPython/stdlib footprints remain unmeasured. Raw and decoder-inclusive costs are separate; neither establishes storage dominance without its relevant accounting scope.', '',
        '## Conditional validation contrasts', '',
        'Eligibility is any match from the sealed fit constructor pool, before dictionary selection outcomes. Actual constructor use is reported separately above. All contrasts are typed minus the matched searched literal arm.', '',
        '| Entries | Subset | Programs | Typed / literal actions | Delta | Better / same / worse |',
        '| ---: | --- | ---: | --- | ---: | --- |']
    for w in (7,8):
        for n,p in arms[w,'typed']['paired'].items():
            lines.append(f'| {2**w} | {n} | {p["n"]} | {p["typed_actions"]}/{p["literal_actions"]} | {p["action_delta"]} | {p["better"]}/{p["same"]}/{p["worse"]} |')
    lines+=['', '## Search and readiness', '',
        '| Entries | Arm | Constructor entries | Trials | Rounds | Stop | Search seconds | Decoder bytes |',
        '| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for (w,n),a in sorted(arms.items()):
        s=a['search'];lines.append(f'| {2**w} | {n} | {a["constructor_entries"]} | {s["trials"]} | {s["rounds"]} | {s["stop"]} | {s["seconds"]:.2f} | {a["decoder_dependency_bytes"]} |')
    lines+=['', 'Matched arms share starting dictionaries, proposal rules and the fixed expression-literal pool. Their selected-span merge proposals can diverge with their parses. A time or trial cap limits the search contrast; termination does not establish global optimality or constructor impossibility.', '']
    for w in (7,8):
        a=arms[w,'typed'];fail=', '.join(k for k,v in a['readiness_checks'].items() if not v) or 'none'
        gain=100*(1-a['validation']['actions']['total']/arms[w,'literal']['validation']['actions']['total'])
        lines.append(f'- {2**w}: {gain:.2f}% fewer validation actions; ready={a["ready"]}; failed predicates: {fail}.')
    lines+=['', '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'Measured run wall time: {r["seconds"]:.2f} seconds. Nine synthetic tests and Python compilation passed before launch. Initial literal parsing reproduces both pinned baselines. Per-program packet/source hashes and one-program storage, full action distributions, pool eligibility, entry size/reuse, framing and padding are in the evidence. Search traces, source bodies, dictionaries, packets and cases remain private.', '',
        'Next work must be separately frozen. Any confirmation opening, training, publication of source rewrites, BITS deployment or human study remains owner-gated. Component: algorithm_solver literal research; intent preserved. The new decoder grammar is isolated from canonical literals and production. No M1 threshold, ledger/catalog/claim or live-profile change.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/expression-prefix-v1/report.py --run /private/path/to/expression-prefix/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
