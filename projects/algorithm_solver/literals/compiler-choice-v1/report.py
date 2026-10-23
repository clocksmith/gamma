"""Sanitized compiler-choice results; failed choices remain in every denominator."""
import argparse
from collections import Counter
import json
from pathlib import Path
from run import HERE,LIT,analyze,tail
prior=tail.module('compiler_tail_report',LIT/'tail-search-v1/report.py')


def main(folder):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text());ids=parent['partition']['dev_val']
    expected={str(row['id']):row['sha256'] for row in parent['sources']}
    baseline=json.loads((LIT/'cost-decomposition-v1/evidence/results.json').read_text())['arms']
    arms={(a['width'],a['arm']):a for a in r['arms']}
    assert set(arms)=={(w,n) for w in (7,8) for n in ('control','bytes','select','joint')}
    for (w,n),a in arms.items():
        private=folder/f'{n}-{2**w}';seal=json.loads((private/'fit-seal.json').read_text())
        assert seal['validation_loaded'] is False
        assert seal['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((private/'dictionary.json').read_bytes())
        assert seal['fit_sources_sha256']==analyze.sha((private/'fit-sources.json').read_bytes())
        assert seal['fit_variants_sha256']==analyze.sha((private/'fit-variants.json').read_bytes())
        sources=json.loads((private/'sources.json').read_text());vocab=json.loads((private/'dictionary.json').read_text());db=analyze.dictionary_bytes(vocab)
        assert set(a['per_problem'])==set(a['qualification'])==set(expected)
        for pid,row in a['per_problem'].items():
            assert row['source_sha256']==analyze.sha(sources[pid].encode())
            assert row['original_sha256']==expected[pid]
            row['source_bytes']=len(sources[pid].encode())
            if row['encodable']:
                seq=analyze.shortest_encode(sources[pid],vocab);packet=analyze.encode(vocab,seq,w)
                assert len(seq)==row['selections'] and analyze.decode(db,packet)==sources[pid]
                row['packet_sha256']=analyze.sha(packet);row['payload_bits']=len(seq)*w
                row['padding_bits']=8*(len(packet)-41)-len(seq)*w
                row['one_program_package_bytes']=len(db)+len(packet)
                row['one_program_package_with_decoder_dependencies']=len(db)+len(packet)+c['decoder_dependency_bytes']
        a['fit_seal_sha256']=analyze.sha((private/'fit-seal.json').read_bytes())
        for key in ('fit_compiler','validation_compiler'):
            for stats in a[key].values():
                stats['error_sha256']={p:analyze.sha(message.encode()) for p,message in stats.pop('errors').items()}
        for split,part in [('fit',parent['partition']['dev_fit']),('validation',ids)]:
            d=a[split];rows=[a['per_problem'][str(i)] for i in part];good=[x for x in rows if x['encodable']]
            d['source_bytes']=sum(x['source_bytes'] for x in rows);d['changed']=sum(x['source_sha256']!=x['original_sha256'] for x in rows)
            d['profiles']=dict(Counter(x['chosen_profile'] for x in rows));d['qualified']=sum(a['qualification'][str(i)]['passed'] for i in part)
            d['qualification_failed_ids']=[i for i in part if not a['qualification'][str(i)]['passed']]
            d['dictionary_bytes']=len(db);d['packet_bytes']=sum(x['packet_bytes'] for x in good);d['framing_bytes']=41*len(good)
            d['payload_bits']=sum(x['payload_bits'] for x in good);d['padding_bits']=sum(x['padding_bits'] for x in good)
            d['package_with_decoder_dependencies']=d['package_bytes']+c['decoder_dependency_bytes']
            stats=a['fit_compiler' if split=='fit' else 'validation_compiler']
            d['compiler_skips']=sum(bool(x['skip']) for x in stats.values());d['compiler_failed_variants']=sum(len(x['error_sha256']) for x in stats.values())
        a['paired_control']=prior.paired(a['per_problem'],arms[w,'control']['per_problem'],ids)
        a['paired_baseline']=prior.paired(a['per_problem'],baseline[str(w)]['per_problem'],ids)
        a['m1_cost_indicators_only']=prior.indicators(a)
    for (w,n),a in arms.items():
        v,b=a['validation'],arms[w,'control']['validation'];p=a['paired_control']
        a['readiness_checks']={'coverage':v['covered']==100,'qualification':v['qualified']==100,
            'audits_clean':not a['illegal_entry_sha256'],'actions_5_percent':v['actions']['total']<=.95*b['actions']['total'],
            'median_lower':v['actions']['median']<b['actions']['median'],'p90_lower':v['actions']['p90']<b['actions']['p90'],
            'improved_60':p['better']>=60,'worsened_at_most_25':p['worse']<=25,
            'fallback_nonincrease':v['single_character_fraction']<=b['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*b['package_bytes']}
        a['ready']=n!='control' and all(a['readiness_checks'].values())
    comparisons={str(w):prior.paired(arms[w,'select']['per_problem'],arms[w,'bytes']['per_problem'],ids) for w in (7,8)}
    # Control keeps every source unchanged, so its source bytes are the original R denominator.
    original_bytes=arms[7,'control']['validation']['source_bytes']
    r['predictions']={'C1':all(arms[w,'control']['fit']['selections']['total']==baseline[str(w)]['dev_fit']['selections']['total'] and
        arms[w,'control']['validation']['selections']['total']==baseline[str(w)]['dev_val']['selections']['total'] for w in (7,8)),
        'C2':all(arms[w,'bytes']['validation']['source_bytes']<=.95*original_bytes and
            .95*baseline[str(w)]['dev_val']['actions']['total']<arms[w,'bytes']['validation']['actions']['total']<baseline[str(w)]['dev_val']['actions']['total'] for w in (7,8)),
        'C3':all(p['worse']==0 and p['better']>=20 for p in comparisons.values()),
        'C4':arms[8,'joint']['validation']['actions']['total']<=.95*arms[8,'control']['validation']['actions']['total'] and arms[8,'joint']['paired_control']['better']>=60 and arms[8,'joint']['paired_control']['worse']<=25,
        'C5':all(a['qualified']==400 and a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'C6':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    r['select_vs_bytes']=comparisons;r['offline_encoder_tooling_bytes']=c['offline_encoder_bytes'];r['decoder_dependency_bytes']=c['decoder_dependency_bytes']
    r['private_results_sha256']=analyze.sha(raw)
    qpath=folder/'qualification-private.json';qs=json.loads(qpath.read_text()) if qpath.exists() else {}
    r['qualification_receipt_sha256']=analyze.sha(qpath.read_bytes()) if qpath.exists() else None
    r['fresh_qualification']={'distinct_sources':len(qs),'passed':sum(q['passed'] for q in qs.values()),'checks_passed':sum(q['checks_passed'] for q in qs.values()),'checks_total':sum(q['cases'] for q in qs.values())}
    ready=sorted((a for a in arms.values() if a['ready']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['width'],a['arm']))
    r['selected_input_candidate']=([ready[0]['arm'],2**ready[0]['width']] if ready else None)
    def clean(v):
        if isinstance(v,dict):
            assert not {'errors','failures','sources','dictionary','trace','tokens','vocab','text','code'}&set(v)
            for x in v.values():clean(x)
        elif isinstance(v,list):
            for x in v:clean(x)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Compiler alternatives and vocabulary-aware selection','',
        '[Freeze](FREEZE.md) pushed in `fe0cb9290`; [review/run receipt](REVIEW.md); [sanitized evidence](evidence/results.json).', '',
        f'Input candidate: **{r["selected_input_candidate"] or "none"}**. These are consumed-development source-plus-encoder results. They do not establish M1 qualification, independent generalization or autonomous assembly.', '',
        'The 128-entry joint arm saves 745 of 14,114 validation actions (5.28%), improves 81 programs and worsens 11, and reduces raw package bytes from 17,225 to 16,577. Its only failed readiness predicate is single-character fraction, which rises from 78.67% to 81.95% even though absolute character codes fall from 11,025 to 10,874. Total selections shrink faster than character codes, so this is a ratio effect; the frozen predicate still fails. At 256 entries joint saves only 14 actions (0.15%). Byte-minimum sources are 9.45% shorter on validation but cost more inputs under the initial dictionaries: 2.88% more at 128 and 13.19% more at 256. Source-byte minimization and literal-input minimization differ.', '',
        '## Costs and qualification','',
        '| Entries | Arm | Split | Source bytes | Decode / qualify | Changed | Selections | Median / p90 / p95 / worst | <=32 / <=96 | Actions | Single-char | Package bytes |',
        '| ---: | --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |']
    for (w,n),a in sorted(arms.items()):
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {2**w} | {n} | {split} | {d["source_bytes"]} | {d["covered"]}/{d["qualified"]} of {d["problems"]} | {d["changed"]} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines+=['','Every final packet independently decodes to the selected source hash. Changed final sources undergo all original cases and strict observation parity; unchanged R sources reuse qualification. No retry, candidate repair or test-driven fallback. Any failure stays in the denominator and invalidates readiness. One Finish is included per program; framing, padding and dictionary bytes are charged.', '',
        f'Canonical decoder dependencies add {c["decoder_dependency_bytes"]:,} source-file bytes per package. Offline compiler/generator tooling is {c["offline_encoder_bytes"]:,} bytes, reported separately from decoder/input storage. Installed Node/CPython/stdlib footprints remain unmeasured. Per-program and amortized storage, framing/padding and action distributions are in the evidence.', '',
        '## Paired validation and readiness', '',
        '| Entries | Arm | Better / same / worse vs searched control | vs pinned R | Ready | Failed predicates |',
        '| ---: | --- | --- | --- | --- | --- |']
    for (w,n),a in sorted(arms.items()):
        p,b=a['paired_control'],a['paired_baseline'];failed=', '.join(k for k,v in a['readiness_checks'].items() if not v)
        lines.append(f'| {2**w} | {n} | {p["better"]}/{p["same"]}/{p["worse"]} | {b["better"]}/{b["same"]}/{b["worse"]} | {a["ready"]} | {failed or "none"} |')
    lines+=['', 'The bytes/select contrast uses the same fixed initial dictionary. Joint/select adds dictionary adaptation; joint/control compares complete source-plus-dictionary optimization against continued original-source search. Validation sources are optimized under already sealed dictionaries.', '',
        '## Source choices and search', '',
        '| Entries | Arm | Validation profile counts | Skips / failed variants | Trials | Stop | Search seconds |',
        '| ---: | --- | --- | --- | ---: | --- | ---: |']
    for (w,n),a in sorted(arms.items()):
        d=a['validation'];s=a['search'];lines.append(f'| {2**w} | {n} | {json.dumps(d["profiles"],sort_keys=True)} | {d["compiler_skips"]}/{d["compiler_failed_variants"]} | {s["trials"]} | {s["stop"]} | {s["seconds"]:.2f} |')
    lines+=['', 'Compiler skips retain the unchanged original and full denominator. Compiler failures remove only that generated alternative before selection; final qualification failures never trigger replacement. Local or budget-limited termination is not a global optimum.', '',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['', 'C3’s no-worsening clause is a consistency check by construction: select minimizes the same fixed-dictionary cost over a superset containing the byte-minimum choice. Its requirement of at least 20 strict improvements per width is empirical.']
    q=r['fresh_qualification'];lines+=['',f'Independent execution: {q["passed"]}/{q["distinct_sources"]} distinct changed programs, {q["checks_passed"]:,}/{q["checks_total"]:,} checks. Measured total run wall time: {r["seconds"]:.2f} seconds. Seven compiler checks, three choice checks and compilation/import passed before launch. The unchanged judge/lane infrastructure retains A’s 37 checks.', '',
        'Source bodies, dictionaries, variants, sequences, errors and cases remain private. A ready input candidate only motivates a separately frozen owner-approved confirmation. No held-out opening, training, source publication, BITS deployment, human study or M1 threshold change. Component intent preserved; canonical decoder and production interfaces unchanged.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/compiler-choice-v1/report.py --run /private/path/to/compiler-choice/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
