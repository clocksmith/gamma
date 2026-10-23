"""Replay integer certificates and witnesses; build metadata-only evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
import dual as d
HERE=d.HERE;LIT=d.LIT;analyze=d.analyze


def main(folder,work):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes()) and r['validation_loaded'] is False
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h
    for a in r['arms']:
        root=folder/f'{a["cohort"]}-{a["mode"]}';texts=json.loads((work/c['cohorts'][a['cohort']]/'fit-sources.json').read_text())
        pool=json.loads((root/'pool.json').read_text());q=np.load(root/'certificate-q.npy',allow_pickle=False);cert=a['optimization']['certificate'];mandatory=d.ALPHABET if a['mode']=='fixed96' else []
        assert a['validation_loaded'] is False and analyze.sha((root/'pool.json').read_bytes())==a['pool_sha256']
        assert analyze.sha((root/'certificate-q.npy').read_bytes())==cert['q_sha256']
        assert d.independent_certificate(texts,pool,mandatory,q,a['capacity'],cert['denominator'])==cert['numerator']
        assert cert['integer_lower_bound']==-(-cert['numerator']//cert['denominator'])
        assert cert['excludes_ten_percent']==(cert['integer_lower_bound']>0)
        banned=d.sel.forbidden_strings(texts)
        a['seed_legacy_pool_additions']=len({s for s in json.loads((work/c['cohorts'][a['cohort']]/'dictionary.json').read_text()) if len(s)>1}-set(d.sel.build_pool(texts,banned,c['max_length'])))
        for name,w in a['witnesses'].items():
            private=root/name;vocab=json.loads((private/'dictionary.json').read_text());db=(private/'dictionary.bin').read_bytes()
            assert len(vocab)==len(set(vocab))<=256 and set(mandatory)<=set(vocab) and set(vocab)<=set(pool)|set(mandatory)
            assert len(set(vocab)-set(mandatory))<=a['capacity'] and not set(vocab)&banned
            assert db==analyze.dictionary_bytes(vocab) and analyze.sha((private/'dictionary.json').read_bytes())==w['dictionary_sha256']
            assert set(w['per_problem'])==set(texts)
            for pid,row in w['per_problem'].items():
                packet=(private/'packets'/f'{pid}.bin').read_bytes();text=texts[pid];value,seq=d.encode_objective(text,vocab)
                assert analyze.decode(db,packet)==text and packet==analyze.encode(vocab,seq,8) and analyze.sha(packet)==row['packet_sha256']
                assert value==row['objective'] and row['selections']==len(seq) and row['characters']==sum(len(vocab[i])==1 for i in seq)
                assert analyze.sha(text.encode())==row['source_sha256']
            assert sum(x['objective'] for x in w['per_problem'].values())==w['objective']>=cert['integer_lower_bound']
            assert w['objective']==10*w['characters']-w['selections']['total']
            w['ten_percent_witness']=w['objective']<=0
        a['certificate_replayed']=True;a['body_audit_clean']=True
        a['bound_scope']='All300 fixed fit sources together; any segmentation and capacity-feasible dictionary from the specified shared2-64-plus-seed pool. No other sources, strings, subsets, quantiles or500population.'
    r['predictions']={'B1':all(a['certificate_replayed'] and a['optimization']['certificate']['integer_lower_bound']<=a['witnesses']['best']['objective'] for a in r['arms']),
        'B2':all(a['optimization']['certificate']['excludes_ten_percent'] for a in r['arms'] if a['mode']=='fixed96'),
        'B3':all(not a['optimization']['certificate']['excludes_ten_percent'] for a in r['arms'] if a['mode']=='flex256'),
        'B4':all(not a['witnesses'].get('generated',{}).get('ten_percent_witness',False) for a in r['arms']),
        'B5':any(a['optimization']['generated_objective'] is not None and a['optimization']['generated_objective']<a['optimization']['seed_objective'] for a in r['arms']),
        'B6':all(a['body_audit_clean'] and all(len(w['per_problem'])==300 for w in a['witnesses'].values()) for a in r['arms'])}
    r.update(private_results_sha256=analyze.sha(raw),decoder_dependency_bytes=c['decoder_dependency_bytes'],offline_encoder_bytes=c['offline_encoder_bytes'],offline_encoder_scope=c['offline_encoder_scope'],decoded_packets=sum(len(w['per_problem']) for a in r['arms'] for w in a['witnesses'].values()))
    def clean(x):
        if isinstance(x,dict):
            assert not {'vocab','sources','pool','tokens','q','cases','args','failures'}&set(x)
            for value in x.values():clean(value)
        elif isinstance(x,list):
            for value in x:clean(value)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Capacity-aware character-fraction certificate','','[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Private pools, multipliers, dictionaries, sources and packets are not published.','',
        'This diagnostic bounds F=10C−N over all segmentations and all capacity-feasible dictionaries in each stated pool. A strictly positive integer lower bound excludes a10%character fraction for that complete300-program fit cohort/model. A nonpositive bound is inconclusive unless a decoded feasible witness reaches F<=0. These are fixed-source/pool bounds, not M1-wide impossibility or source-rewriting conclusions. No validation source values were loaded.','',
        '| Cohort | Model | Pool / occurrence edges | Exact numerator / denominator | Integer lower bound | Best feasible F | Excludes10% | Iterations / stop / seconds |','| --- | --- | --- | --- | ---: | ---: | --- | --- |']
    for a in r['arms']:
        o=a['optimization'];cert=o['certificate'];lines.append(f'| {a["cohort"]} | {a["mode"]} | {a["pool_entries"]}/{a["occurrences"]} | {cert["numerator"]}/{cert["denominator"]} | {cert["integer_lower_bound"]} | {o["best_objective"]} | {cert["excludes_ten_percent"]} | {o["iterations"]}/{o["stop"]}/{o["seconds"]:.2f} |')
    lines+=['','The pool is shared2–64byte strings plus pinned seed learned entries, with fit whole-source/body exclusions. fixed96 reserves96characters and permits160learned entries. flex256 permits any256entries from learned pool plus all96characters; it relaxes item24 reserved-character constraints. Bounds do not cover excluded/longer/unshared strings beyond seed exceptions, source alternatives, arbitrary program subsets, quantile requirements, held-out data or400of500coverage.','',
        '| Cohort/model | Witness | Entries / character entries | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | F | Raw / decoder-source package |','| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |']
    for a in r['arms']:
        for name,w in a['witnesses'].items():
            s=w['selections'];lines.append(f'| {a["cohort"]}/{a["mode"]} | {name} | {w["entries"]}/{w["character_entries"]} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {w["actions"]["total"]} | {w["characters"]}/{100*w["character_fraction"]:.2f}% | {w["objective"]} | {w["package_bytes"]}/{w["package_with_decoder_sources"]} |')
    lines+=['','Witnesses minimizeF within their own dictionaries, then N and lexicographic IDs. This is not minimum ratio or canonical minimumN segmentation. Every stored packet decodes exactly; one Finish, eight-bit selections,41-byte frames, full dictionary and per-program/amortized storage count. Qualified source hashes are reused from item13; no fresh runtime qualification or autonomous solving is claimed. Item23 retained its later unchanged-source exit137 failure.','',
        '| Cohort/model | Primal proposals / coverage failures | Legacy seed pool additions | Total arm seconds |','| --- | --- | ---: | ---: |']
    for a in r['arms']:
        o=a['optimization'];lines.append(f'| {a["cohort"]}/{a["mode"]} | {o["primal_attempts"]}/{o["primal_infeasible"]} | {a["seed_legacy_pool_additions"]} | {a["seconds"]:.2f} |')
    lines+=['','Generated witnesses are retained separately even when worse than the seed; missing optional coverage proposals are discarded as infeasible and counted, without repair. Floating bounds guide search only. Quantized nonnegative multipliers, integer shortest paths, top-capacity entry sums and separate forward replay establish each reported certificate.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'{r["decoded_packets"]} final witness packets decode; total run wall time {r["seconds"]:.2f} seconds. Five tests include60exhaustive dictionary-bound instances and60exhaustive path comparisons; compile/import/help and identity checks passed. Reporting replays all exact certificates and witnesses without optimization.','',
        'No selected successor or readiness decision. Component intent preserved; canonical decoder and production boundaries unchanged. Training, held-out/protected opening, independent confirmation, publishing private sources, deployment and human studies remain owner-gated. Full installed runtime storage remains unmeasured.','',
        'Rebuild with the pinned NumPy Python: `python -B projects/algorithm_solver/literals/fraction-capacity-v1/report.py --run /private/fraction-capacity/run-v1 --work /private/literal-admission500-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
