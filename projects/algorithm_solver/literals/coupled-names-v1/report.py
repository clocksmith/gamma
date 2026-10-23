"""Rebuild public metadata from sealed private choices, independently decode again."""
import argparse
import json
from pathlib import Path
from run import HERE,LIT,analyze,tail
p=tail.module('coupled_prior_report',LIT/'tail-search-v1/report.py')


def main(run):
    raw=(run/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    arms={a['arm']:a for a in r['arms']};ids=c['partition']['dev_val'];expected={str(i) for split in c['partition'].values() for i in split}
    assert set(arms)=={'control','seed','ordinary','coupled','ordinary_joint','coupled_joint'}
    for name,a in arms.items():
        folder=run/f'{name}-256';seal=json.loads((folder/'fit-seal.json').read_text())
        assert seal['validation_loaded'] is False
        assert seal['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((folder/'dictionary.json').read_bytes())
        assert seal['fit_sources_sha256']==analyze.sha((folder/'fit-sources.json').read_bytes())
        assert set(a['per_problem'])==set(a['qualification'])==expected
        sources=json.loads((folder/'sources.json').read_text());vocab=json.loads((folder/'dictionary.json').read_text())
        for pid,row in a['per_problem'].items():
            text=sources[pid];assert row['source_sha256']==analyze.sha(text.encode())
            assert row['original_sha256']==arms['control']['per_problem'][pid]['source_sha256']
            row['source_bytes']=len(text.encode())
            if row['encodable']:
                seq=analyze.shortest_encode(text,vocab);packet=analyze.encode(vocab,seq,8)
                assert len(seq)==row['selections'] and analyze.decode(analyze.dictionary_bytes(vocab),packet)==text
                row['packet_sha256']=analyze.sha(packet)
                row['one_program_package_bytes']=a['dictionary_bytes']+len(packet)
                row['one_program_package_with_decoder_dependencies']=row['one_program_package_bytes']+c['decoder_dependency_bytes']
        a['fit_seal_sha256']=analyze.sha((folder/'fit-seal.json').read_bytes())
        for split,split_ids in [('fit',c['partition']['dev_fit']),('validation',ids)]:
            rows=[a['per_problem'][str(i)] for i in split_ids];d=a[split]
            d['source_bytes']=sum(x['source_bytes'] for x in rows)
            d['single_character_codes']=sum(x.get('single_characters',0) for x in rows)
            d['package_with_decoder_dependencies']=d['package_bytes']+c['decoder_dependency_bytes']
            d['changed']=sum(x['source_sha256']!=x['original_sha256'] for x in rows)
            d['qualified']=sum(a['qualification'][str(i)]['passed'] for i in split_ids)
            d['qualification_failed_ids']=[i for i in split_ids if not a['qualification'][str(i)]['passed']]
            good=[x for x in rows if x['encodable']];d['framing_bytes']=41*len(good)
            d['payload_bits']=8*sum(x['selections'] for x in good);d['padding_bits']=0
        for bname in ('control','seed','ordinary','ordinary_joint'):
            a['paired_'+bname]=p.paired(a['per_problem'],arms[bname]['per_problem'],ids)
        v=a['validation'];b=arms['control']['validation'];s=arms['seed']['validation'];pair=a['paired_control']
        a['readiness_checks']={
            'qualified':all(x['passed'] for x in a['qualification'].values()),'covered':v['covered']==100,
            'whole_solution_clean':not a['illegal_entry_sha256'],
            'actions_5_percent':v['actions']['total']<=.95*b['actions']['total'],
            'median_lower':v['actions']['median']<b['actions']['median'],'p90_lower':v['actions']['p90']<b['actions']['p90'],
            'improved_60':pair['better']>=60,'worsened_at_most_25':pair['worse']<=25,
            'fallback_nonincrease':v['single_character_fraction']<=b['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*b['package_bytes']}
        a['ready']=all(a['readiness_checks'].values())
        a['successor_checks']={'ready':a['ready'],'actions_lower':v['actions']['total']<s['actions']['total'],
            'median_nonincrease':v['actions']['median']<=s['actions']['median'],'p90_nonincrease':v['actions']['p90']<=s['actions']['p90'],
            'fallback_nonincrease':v['single_character_fraction']<=s['single_character_fraction'],
            'package_within_105_percent':v['package_bytes']<=1.05*s['package_bytes'],
            'worsened_at_most_25':a['paired_seed']['worse']<=25}
        a['successor']=all(a['successor_checks'].values());a['m1_cost_indicators_only']=p.indicators(a)
    hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())
    old={a['arm']:a for a in hist['arms'] if a['width']==8}
    r['predictions']={
        'C1':all(arms[n][s]['selections']['total']==old[o][s]['selections']['total'] for n,o in [('control','control'),('seed','scope_joint')] for s in ('fit','validation')),
        'C2':arms['coupled']['validation']['actions']['total']<arms['ordinary']['validation']['actions']['total'] and arms['coupled']['paired_ordinary']['better']>=10,
        'C3':arms['coupled_joint']['validation']['actions']['total']<=.99*arms['seed']['validation']['actions']['total'],
        'C4':sum(x['coupled']['moves'] for n in ('coupled','coupled_joint') for h in arms[n]['rounds'] for x in h['rewrite'].values())>=20,
        'C5':all(a['qualified']==400 and a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()),
        'C6':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    ready=sorted((a for a in arms.values() if a['successor']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['arm']))
    r['selected_successor']=ready[0]['arm'] if ready else None
    r['offline_encoder_tooling_bytes']=c['offline_encoder_bytes'];r['offline_encoder_scope']=c['offline_encoder_scope'];r['decoder_dependency_bytes']=c['decoder_dependency_bytes']
    r['private_results_sha256']=analyze.sha(raw);qpath=run/'qualification-private.json';qs=json.loads(qpath.read_text())
    r['qualification_receipt_sha256']=analyze.sha(qpath.read_bytes())
    r['fresh_qualification_summary']={'distinct_sources':len(qs),'passed':sum(q['passed'] for q in qs.values()),'checks_passed':sum(q['checks_passed'] for q in qs.values()),'checks_total':sum(q['cases'] for q in qs.values())}
    def check(v):
        if isinstance(v,dict):
            assert not {'_trace','accepted_colors','trace','sources','vocab','failures','changes','name','target'}&set(v)
            for x in v.values():check(x)
        elif isinstance(v,list):
            for x in v:check(x)
    check(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Dictionary-guided coupled names','','[Freeze](FREEZE.md) pushed as `29442036f`; [review and run receipt](REVIEW.md). [Evidence](evidence/results.json) contains sanitized metadata only. Private sources, dictionaries, mappings, traces and cases remain private.','',
        f'Selected incremental successor: **{r["selected_successor"] or "none"}**. Readiness is consumed-development input evidence, not M1 or independent confirmation. This is offline optimization supplied with a known source; it does not establish autonomous composition.','',
        'Coupled naming saves seven validation actions versus the seed and ordinary continuation (5 better/95 same/0 worse). Both coupled arms remain ready versus the original control but fail the incremental successor gate: absolute character codes decline4193→4191 while fraction rises49.89%→49.91% because total selections fall faster. No successor is selected; the frozen fraction rule is unchanged.', '',
        'Historical control/seed are hash-bound replays from item13. The seed was selected by item13’s frozen ranking using dev-val outcomes; further gains are adaptive development evidence, not an independent generalization estimate. Ordinary arms continue naming; coupled arms add simultaneous proposals and additional scoring work. Fixed comparisons share a dictionary; joint comparisons follow different complete source/dictionary trajectories. Validation uses original/seed choices and a frozen naming policy under fit-sealed dictionaries. No validation refit or test-driven repair.','',
        '| Arm | Split | Decoded | Qualified | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Character codes | Character fraction | Raw package |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |']
    for name,a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {name} | {split} | {d["covered"]} | {d["qualified"]} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines+=['','One Finish per program; dictionary, 41-byte packet headers, payload and padding are charged. Source bytes, decoder-inclusive packages and per-program storage are in evidence. Offline tooling bytes are a conservative source dependency inventory, not complete installed runtime storage. Failed candidates remain in cost tables and invalidate readiness.','',
        '| Arm | Better/same/worse vs control | Better/same/worse vs seed | Ready | Successor | Failed readiness | Failed successor |',
        '| --- | --- | --- | --- | --- | --- | --- |']
    for name,a in arms.items():
        fmt=lambda q:f'{q["better"]}/{q["same"]}/{q["worse"]}'
        fail=lambda q:', '.join(k for k,v in q.items() if not v) or 'None'
        lines.append(f'| {name} | {fmt(a["paired_control"])} | {fmt(a["paired_seed"])} | {a["ready"]} | {a["successor"]} | {fail(a["readiness_checks"])} | {fail(a["successor_checks"])} |')
    lines+=['','| Contrast | Validation action delta | Better/same/worse |','| --- | ---: | --- |']
    for n,b in [('ordinary','seed'),('coupled','ordinary'),('ordinary_joint','seed'),('coupled_joint','ordinary_joint'),('coupled_joint','seed')]:
        a=arms[n];pair=a['paired_'+b]
        lines.append(f'| {n} minus {b} | {a["validation"]["actions"]["total"]-arms[b]["validation"]["actions"]["total"]} | {pair["better"]}/{pair["same"]}/{pair["worse"]} |')
    lines+=['','| Arm | Round | Dictionary trials/stop | Ordinary trials/moves | Coupled trials/moves | States/proposals/caps |','| --- | ---: | --- | --- | --- | --- |']
    for name,a in arms.items():
        if a['historical_replay']:continue
        for h in a['rounds']:
            x=list(h['rewrite'].values());t=lambda k:sum(s[k] for s in x);u=lambda k:sum(s['coupled'][k] for s in x)
            lines.append(f'| {name} | {h["round"]+1} | {h["trials"]}/{h["stop"]} | {t("trials")}/{t("moves")} | {u("trials")}/{u("moves")} | {u("states")}/{u("proposals")}/{u("caps")} |')
    lines+=['','Caps count state truncations plus proposal truncations; bounded search is not a global optimum. Validation counters and all stop reasons are in evidence. Historical search counters remain separately attributed to item13.','',
        '| Prediction | Met |','| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in r['predictions'].items()]
    q=r['fresh_qualification_summary'];lines += ['',f'All final choices seal before execution. Distinct changed programs: {q["passed"]}/{q["distinct_sources"]} passed, {q["checks_passed"]:,}/{q["checks_total"]:,} strict case checks; unchanged R reuses its pinned qualification. Finite parity checks and reused development cases do not establish universal equivalence or fresh generalization.', '',
        f'Measured run wall time: {r["seconds"]:.2f} seconds. Nine focused synthetic tests and compilation/import/help checks passed before launch; unchanged judge/lane infrastructure retains A’s 37 passing checks.', '',
        'Owner gate: any selected successor requires a separately frozen confirmation population and explicit permission for protected/held-out access. Candidate artifacts are private coupled-names/run-v1/<selected>-256; dictionary/fit-seal hashes are in evidence. No training, deployment, publication, human study, ledger/catalog/claim write, autonomous-solving claim or M1 threshold change. Component intent preserved, canonical decoder and production boundaries unchanged.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/coupled-names-v1/report.py --run /private/path/to/coupled-names/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
