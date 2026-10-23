"""Sanitized per-binding descent contrasts and strict source qualification."""
import argparse
import json
from pathlib import Path
from run import HERE, LIT, analyze, tail

prior_report=tail.module('tail_report_for_binding_descent',LIT/'tail-search-v1/report.py')


def main(run):
    raw=(run/'results.json').read_bytes();r=json.loads(raw)
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    c=json.loads((HERE/'contract.json').read_text());ids=c['partition']['dev_val']
    baseline=json.loads((LIT/'cost-decomposition-v1/evidence/results.json').read_text())
    arms={(a['width'],a['arm']):a for a in r['arms']}
    assert set(arms)=={(w,n) for w in (7,8) for n in ('control','global','scope','global_joint','scope_joint')}
    expected={str(pid) for split in c['partition'].values() for pid in split}
    for (w,n),a in arms.items():
        b=baseline['arms'][str(w)];v=a['validation'];bv=arms[w,'control']['validation']
        folder=run/f'{n}-{2**w}'
        seal=json.loads((folder/'fit-seal.json').read_text())
        assert seal['validation_loaded'] is False
        assert seal['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((folder/'dictionary.json').read_bytes())
        assert seal['fit_sources_sha256']==analyze.sha((folder/'fit-sources.json').read_bytes())
        assert set(a['per_problem'])==set(a['qualification'])==expected
        chosen=json.loads((folder/'sources.json').read_text())
        for pid,row in a['per_problem'].items():
            assert row['source_sha256']==analyze.sha(chosen[pid].encode())
            assert row['original_sha256']==b['per_problem'][pid]['source_sha256']
            row['source_bytes']=len(chosen[pid].encode())
            if row['encodable']:
                vocab=json.loads((folder/'dictionary.json').read_text())
                seq=analyze.shortest_encode(chosen[pid],vocab);packet=analyze.encode(vocab,seq,w)
                assert len(seq)==row['selections'] and analyze.decode(analyze.dictionary_bytes(vocab),packet)==chosen[pid]
                row['packet_sha256']=analyze.sha(packet)
                row['one_program_package_bytes']=a['dictionary_bytes']+len(packet)
                row['one_program_package_with_decoder_dependencies']=row['one_program_package_bytes']+c['decoder_dependency_bytes']
        a['fit_seal_sha256']=analyze.sha((folder/'fit-seal.json').read_bytes())
        a['paired_baseline']=prior_report.paired(a['per_problem'],b['per_problem'],ids)
        a['paired_control']=prior_report.paired(a['per_problem'],arms[w,'control']['per_problem'],ids)
        p=a['paired_control']
        a['readiness_checks']=dict(qualification=all(q['passed'] for q in a['qualification'].values()),
            coverage=v['covered']==100,whole_solution_clean=not a['illegal_entry_sha256'],
            actions_5_percent=v['actions']['total']<=.95*bv['actions']['total'],
            median_lower=v['actions']['median']<bv['actions']['median'],p90_lower=v['actions']['p90']<bv['actions']['p90'],
            improved_60=p['better']>=60,worsened_at_most_25=p['worse']<=25,
            fallback_nonincrease=v['single_character_fraction']<=bv['single_character_fraction'],
            package_within_105_percent=v['package_bytes']<=1.05*bv['package_bytes'])
        a['ready']=all(a['readiness_checks'].values())
        a['m1_cost_indicators_only']=prior_report.indicators(a)
        for split,split_ids in [('fit',c['partition']['dev_fit']),('validation',ids)]:
            rows=[a['per_problem'][str(pid)] for pid in split_ids]
            a[split]['source_bytes']=sum(x['source_bytes'] for x in rows)
            a[split]['single_character_codes']=sum(x.get('single_characters',0) for x in rows)
            a[split]['package_with_decoder_dependencies']=a[split]['package_bytes']+c['decoder_dependency_bytes']
            a[split]['changed']=sum(x['source_sha256']!=x['original_sha256'] for x in rows)
            a[split]['qualified']=sum(a['qualification'][str(pid)]['passed'] for pid in split_ids)
            a[split]['qualification_failed_ids']=[pid for pid in split_ids if not a['qualification'][str(pid)]['passed']]
            a[split]['fresh_cases']=sum(a['qualification'][str(pid)].get('cases',0) for pid in split_ids)
            good=[x for x in rows if x['encodable']]
            a[split]['framing_bytes']=41*len(good)
            a[split]['payload_bits']=w*sum(x['selections'] for x in good)
            a[split]['padding_bits']=sum(8*(x['packet_bytes']-41)-w*x['selections'] for x in good)
    r['predictions']={
        'D1':all(arms[w,'control']['fit']['selections']['total']==baseline['arms'][str(w)]['dev_fit']['selections']['total'] and arms[w,'control']['validation']['selections']['total']==baseline['arms'][str(w)]['dev_val']['selections']['total'] for w in (7,8)),
        'D2':all(arms[w,'scope']['validation']['actions']['total']<arms[w,'global']['validation']['actions']['total'] and prior_report.paired(arms[w,'scope']['per_problem'],arms[w,'global']['per_problem'],ids)['better']>=20 for w in (7,8)),
        'D3':arms[8,'scope_joint']['validation']['actions']['total']<=.95*arms[8,'control']['validation']['actions']['total'] and arms[8,'scope_joint']['paired_control']['better']>=60 and arms[8,'scope_joint']['paired_control']['worse']<=25,
        'D4':all(arms[w,'scope_joint']['validation']['actions']['total']<arms[w,'global_joint']['validation']['actions']['total'] for w in (7,8)),
        'D5':all(a['qualified']==400 and a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'D6':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    r['offline_encoder_tooling_bytes']=c['offline_encoder_bytes'];r['offline_encoder_scope']=c['offline_encoder_scope']
    r['decoder_dependency_bytes']=c['decoder_dependency_bytes']
    ready=sorted((a for a in arms.values() if a['ready']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['width'],a['arm']))
    r['selected_ready_arm']=([ready[0]['arm'],2**ready[0]['width']] if ready else None)
    r['private_results_sha256']=analyze.sha(raw)
    receipt=run/'qualification-private.json'
    if receipt.exists():
        r['qualification_receipt_sha256']=analyze.sha(receipt.read_bytes())
        qs=json.loads(receipt.read_text())
        r['fresh_qualification_summary']={'distinct_sources':len(qs),'passed':sum(q['passed'] for q in qs.values()),
             'checks_passed':sum(q['checks_passed'] for q in qs.values()),'checks_total':sum(q['cases'] for q in qs.values())}
    else:
        assert all(q['reused'] for a in arms.values() for q in a['qualification'].values())
        r['qualification_receipt_sha256']=None
        r['fresh_qualification_summary']={'distinct_sources':0,'passed':0,'checks_passed':0,'checks_total':0}
    # An explicit guard against accidental candidate trace/name publication.
    def check(value):
        if isinstance(value,dict):
            assert not {'_trace','accepted_mapping','accepted_colors','trace','sources','vocab','failures','name','target'} & set(value)
            for x in value.values():check(x)
        elif isinstance(value,list):
            for x in value:check(x)
    check(r)
    (HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Per-binding exact-cost naming', '',
        '[Freeze](FREEZE.md) pushed in `c306b899f`; [review/run receipt](REVIEW.md). '
        '[Evidence](evidence/results.json) publishes only metadata. Source bodies, dictionaries, mappings, candidate traces and cases stay private.', '',
        f'Development-ready selection: **{r["selected_ready_arm"] or "none"}**. '
        'This is offline optimization supplied with a known program. It establishes neither autonomous assembly nor fresh generalization.', '',
        'Validation programs are rewritten by the encoder under a dictionary sealed on fit. '
        'The validation comparison is therefore source-plus-encoder optimization versus fixed source, with independent qualification after all choices are sealed.', '',
        'At 256 entries, scope_joint uses 8,504 validation actions versus 9,048 for control (6.01% fewer), with 75 better/21 same/4 worse programs. Single-character fraction falls from 55.14% to 49.89%, and raw package bytes from 15,255 to 14,724. The fixed-dictionary scope arm also passes readiness: 8,576 actions (5.22% fewer), 73 better/27 same/0 worse. Frozen ranking selects scope_joint. Its median/p95 remain 61.5/199 selections and character fraction remains far above M1’s gates; readiness is not M1 qualification.', '',
        '## Costs and qualification', '',
        '| Width | Arm | Split | Decoded | Qualified | Changed | Selections | Median | p90 | p95 | Worst | <=32 / <=96 | Actions | Single-char | Package bytes |',
        '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for (w,n),a in sorted(arms.items()):
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {2**w} | {n} | {split} | {d["covered"]}/{d["problems"]} | {d["qualified"]}/{d["problems"]} | {d["changed"]} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines+=['', 'Costs describe all encoded candidates; any unqualified candidate invalidates readiness and its cost is not a qualified improvement. '
        'Changed final sources undergo all frozen cases with strict observation parity. Unchanged R sources reuse hash-bound qualification. '
        'Case reuse and finite parity checks are development evidence, not universal equivalence or unseen correctness. '
        'Each packet decodes independently to its selected source hash. One Finish is included in actions. Headers are 41 bytes; padding and dictionary storage are charged. Decoder-inclusive and one-program storage plus offline tooling source bytes are in the evidence; complete installed runtime footprint is unmeasured.', '',
        '## Paired validation', '',
        '| Width | Arm | Better/same/worse vs baseline | Better/same/worse vs searched control | Ready | Failed readiness predicates |',
        '| ---: | --- | --- | --- | --- | --- |']
    for (w,n),a in sorted(arms.items()):
        p,q=a['paired_baseline'],a['paired_control']
        failures=', '.join(k for k,v in a['readiness_checks'].items() if not v) or 'None'
        lines.append(f'| {2**w} | {n} | {p["better"]}/{p["same"]}/{p["worse"]} | {q["better"]}/{q["same"]}/{q["worse"]} | {a["ready"]} | {failures} |')
    lines+=['', '## Source/search contrasts', '', '| Width | Contrast | Validation action delta | Better/same/worse |', '| ---: | --- | ---: | --- |']
    for w in (7,8):
        for a,b in [('global','control'),('scope','global'),('global_joint','global'),('scope_joint','scope'),('scope_joint','global_joint')]:
            x,y=arms[w,a],arms[w,b];pair=prior_report.paired(x['per_problem'],y['per_problem'],ids)
            lines.append(f'| {2**w} | {a} minus {b} | {x["validation"]["actions"]["total"]-y["validation"]["actions"]["total"]} | {pair["better"]}/{pair["same"]}/{pair["worse"]} |')
    lines+=['', '## Search accounting', '', '| Width | Arm | Round | Dictionary trials | Stop | Dictionary seconds | Rewrite trials | Rewrite moves |',
            '| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |']
    for (w,n),a in sorted(arms.items()):
        for h in a['rounds']:
            lines.append(f'| {2**w} | {n} | {h["round"]+1} | {h["trials"]} | {h["stop"]} | {h["seconds"]:.2f} | {sum(x["trials"] for x in h["rewrite"].values())} | {sum(x["moves"] for x in h["rewrite"].values())} |')
    lines+=['', 'The global and scope policies share budgets but follow different coordinate paths; the larger scope-local feasible set does not guarantee lower cost from this bounded algorithm. Global_joint versus scope_joint compares complete source/dictionary trajectories, whose proposals can diverge.']
    for width in (7,8):
        old=json.loads((LIT/'name-search-v1/evidence/results.json').read_text())
        h=next(a for a in old['arms'] if a['width']==width and a['arm']=='joint')
        lines.append(f'Historical name-search joint{2**width}: {h["validation"]["actions"]["total"]} actions. Its guards and search differ; this is not a matched arm.')
    lines+=['', 'Dictionary seconds exclude the preceding rewrite call. Total run wall time includes rewriting, validation and qualification. '
        'Time-capped comparisons are budget-limited; local termination is not an optimum. Fixed-dictionary arms do no dictionary search. '
        'Validation rewrite counts, category attributions, full action distributions and framing/padding are retained in evidence.', '',
        '| Prediction | Met |', '| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in r['predictions'].items()]
    q=r['fresh_qualification_summary']
    lines += ['', f'Independent execution passed {q["passed"]}/{q["distinct_sources"]} distinct changed programs and '
        f'{q["checks_passed"]:,}/{q["checks_total"]:,} case checks. No retry or candidate repair.', '',
        f'Measured total wall time: {r["seconds"]:.2f} seconds. Twelve synthetic scope/graph/budget checks and compilation/import passed before launch; '
        'the unchanged judge/lane infrastructure retains A’s 37 passing checks. Source execution is separately recorded above. '
        'No test result fed back into rewriting or vocabulary search; failures receive no repair.', '',
        'Confirmation remains at the owner gate: freeze the exact selected dictionary and encoder on a separately approved population before any protected/held-out opening, with no refit or repair. The private candidate is binding-descent/run-v1/scope_joint-256; its dictionary and fit-seal hashes are in the evidence. Continued development must use a new freeze and does not retroactively confirm this candidate. A ready development arm can only motivate a separately frozen owner-approved confirmation. Final held-out/protected opening, source publication, BITS changes, human studies and training remain gated. '
        'The report is the source of truth for readiness against searched control; every failed predicate is listed above.', '',
        'Component: algorithm_solver literal research. Intent preserved; no production boundary or decoder change, ledger/catalog/claim write, M1 threshold change or autonomous-solving claim.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/binding-descent-v1/report.py --run /private/path/to/binding-descent/run-v1`.', '']
    (HERE/'README.md').write_text('\n'.join(lines))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
