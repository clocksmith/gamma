"""Replay integer certificates and witnesses; build metadata-only evidence."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'fraction-capacity-v1'))
import dual as d
analyze=d.analyze
sys.path.insert(0,str(HERE))
import pool as shared_pool
import occurrence
d.Graph=occurrence.Graph
d.independent_certificate=occurrence.independent_certificate


def main(folder,work):
    c=json.loads((HERE/'contract.json').read_text())
    if not (folder/'results.json').exists():
        failure=json.loads((folder/'failure.json').read_text())
        clean_failure={k:failure[k] for k in ('exception','seconds','complete','partial_certificates_promoted','validation_loaded')}
        assert clean_failure['complete'] is False and clean_failure['partial_certificates_promoted'] is False and clean_failure['validation_loaded'] is False
        result={'schema':'gamma.all-length-fraction.incomplete.v1','failure':clean_failure,'predictions':{k:None for k in ('A1','A2','A3','A4','A5')},'status':'incomplete; no complete experiment certificate accepted','failure_sha256':analyze.sha((folder/'failure.json').read_bytes())}
        (HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',result)
        (HERE/'README.md').write_text('# All-length shared-pool fraction certificate\n\n[Freeze](FREEZE.md); [prelaunch amendment](AMENDMENT-1.md); [metadata evidence](evidence/results.json).\n\nThe bounded run failed before both arms completed. No complete experiment certificate or prediction verdict is accepted. Partial artifacts remain private; no pool truncation or validation access occurred. See the failure type and elapsed time in the evidence.\n')
        return
    raw=(folder/'results.json').read_bytes();r=json.loads(raw)
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes()) and r['validation_loaded'] is False
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    qualification_path=LIT/'binding-descent-v1/evidence/results.json'
    qualification=json.loads(qualification_path.read_text())
    assert {(a['cohort'],a['mode']) for a in r['arms']}=={('R','flex256'),('naming','flex256')} and len(r['arms'])==2
    for a in r['arms']:
        assert a['capacity']==256 and a['mandatory_entries']==0
        root=folder/f'{a["cohort"]}-{a["mode"]}';texts=json.loads((work/c['cohorts'][a['cohort']]/'fit-sources.json').read_text())
        assert set(texts)=={str(i) for i in c['fit_ids']} and len(texts)==300
        assert a['fit_source_sha256']==c['private_files'][c['cohorts'][a['cohort']]+'/fit-sources.json']
        qualified=next(x for x in qualification['arms'] if x['arm']==('control' if a['cohort']=='R' else 'scope_joint') and x['width']==8)
        for pid,text in texts.items():
            assert analyze.sha(text.encode())==qualified['per_problem'][pid]['source_sha256']
            assert qualified['qualification'][pid]['passed'] is True
        a['qualification_source_hashes_rechecked']=True
        pool=json.loads((root/'pool.json').read_text());q=np.load(root/'certificate-q.npy',allow_pickle=False);cert=a['optimization']['certificate'];mandatory=d.ALPHABET if a['mode']=='fixed96' else []
        assert a['validation_loaded'] is False and analyze.sha((root/'pool.json').read_bytes())==a['pool_sha256']
        assert analyze.sha((root/'certificate-q.npy').read_bytes())==cert['q_sha256']
        assert cert['denominator']==c['search']['denominator']
        assert cert['integer_lower_bound']==-(-cert['numerator']//cert['denominator'])
        assert cert['excludes_ten_percent']==(cert['integer_lower_bound']>0)
        banned=d.sel.forbidden_strings(texts)
        seed=json.loads((work/c['cohorts'][a['cohort']]/'dictionary.json').read_text())
        shared=shared_pool.build_pool(texts,banned);extras=sorted({s for s in seed if len(s)>1}-set(shared))
        expected_pool=sorted(set(shared)|set(extras)|set(d.ALPHABET))
        assert pool==expected_pool and not set(pool)&banned
        assert len(shared)==a['shared_learned_entries'] and len(extras)==a['seed_extra_entries']
        assert analyze.sha(json.dumps(extras,ensure_ascii=True).encode())==a['seed_extras_sha256']
        assert len(pool)==a['pool_entries'] and max(map(len,pool),default=0)==a['maximum_entry_length']
        a['seed_legacy_pool_additions']=len(extras);a['pool_rebuilt']=True
        assert d.independent_certificate(texts,pool,mandatory,q,a['capacity'],cert['denominator'])==cert['numerator']
        assert sum(cert['per_program_path_numerators'])==cert['relaxed_paths_numerator']
        assert cert['relaxed_paths_numerator']-cert['top_capacity_numerator']==cert['numerator']
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
                assert row['actions']==len(seq)+1 and row['packet_bytes']==len(packet)
                assert row['one_program_package_bytes']==len(db)+len(packet)
                assert row['one_program_with_decoder']==len(db)+len(packet)+c['decoder_dependency_bytes']
            assert sum(x['objective'] for x in w['per_problem'].values())==w['objective']>=cert['integer_lower_bound']
            assert w['objective']==10*w['characters']-w['selections']['total']
            assert w['selections']==analyze.distribution([row['selections'] for row in w['per_problem'].values()])
            assert w['actions']==analyze.distribution([row['actions'] for row in w['per_problem'].values()])
            assert w['characters']==sum(row['characters'] for row in w['per_problem'].values())
            assert w['character_fraction']==w['characters']/w['selections']['total']
            assert w['entries']==len(vocab) and w['character_entries']==sum(len(word)==1 for word in vocab)
            assert w['dictionary_bytes']==len(db)
            assert w['package_bytes']==len(db)+sum(row['packet_bytes'] for row in w['per_problem'].values())
            assert w['package_with_decoder_sources']==w['package_bytes']+c['decoder_dependency_bytes']
            assert w['amortized_package_bytes']==w['package_bytes']/len(texts)
            assert w['framing_bytes']==41*len(texts) and w['payload_bits']==8*w['selections']['total'] and w['padding_bits']==0
            w['ten_percent_witness']=w['objective']<=0
        a['certificate_replayed']=True;a['body_audit_clean']=True
        a['bound_scope']='All 300 fixed fit sources together; any segmentation and <=256-entry dictionary from all-length shared substrings excluding fit bodies/sources, plus pinned seed exceptions and 96 optional characters. No arbitrary one-owner strings beyond seed exceptions, other sources, subsets, quantiles or the 500-program population.'
    old_path=LIT/'fraction-capacity-v1/evidence/results.json';old=json.loads(old_path.read_text())
    assert old['contract_sha256']==c['parent_contract_sha256']
    old_counts={a['cohort']:a['pool_entries'] for a in old['arms'] if a['mode']=='flex256'}
    assert set(old_counts)=={'R','naming'}
    r['item25_evidence_sha256']=analyze.sha(old_path.read_bytes())
    r['item25_optional_pool_counts']=old_counts
    r['predictions']={'A1':all(a['certificate_replayed'] and a['optimization']['certificate']['integer_lower_bound']<=a['witnesses']['best']['objective'] for a in r['arms']),
        'A2':all(a['pool_entries']>old_counts[a['cohort']] for a in r['arms']),
        'A3':any(not a['optimization']['certificate']['excludes_ten_percent'] for a in r['arms']),
        'A4':all(not a['witnesses'].get('generated',{}).get('ten_percent_witness',False) for a in r['arms']),
        'A5':all(a['body_audit_clean'] and a['pool_rebuilt'] and all(len(w['per_problem'])==300 for w in a['witnesses'].values()) for a in r['arms'])}
    r.update(private_results_sha256=analyze.sha(raw),decoder_dependency_bytes=c['decoder_dependency_bytes'],offline_encoder_bytes=c['offline_encoder_bytes'],offline_encoder_scope=c['offline_encoder_scope'],decoded_packets=sum(len(w['per_problem']) for a in r['arms'] for w in a['witnesses'].values()))
    def clean(x):
        if isinstance(x,dict):
            assert not {'vocab','sources','pool','tokens','q','cases','args','failures'}&set(x)
            for value in x.values():clean(value)
        elif isinstance(x,list):
            for value in x:clean(value)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# All-length shared-pool character-fraction certificate','','[Freeze](FREEZE.md); [prelaunch amendment](AMENDMENT-1.md); [metadata evidence](evidence/results.json). Private pools, multipliers, dictionaries, sources and packets are not published.','',
        'This diagnostic bounds F=10C−N over all segmentations and all capacity-feasible dictionaries in each stated pool. A strictly positive integer lower bound excludes a 10% character fraction for that complete 300-program fit cohort/model. A nonpositive bound is inconclusive unless a decoded feasible witness reaches F<=0. These are fixed-source/pool bounds, not M1-wide impossibility or source-rewriting conclusions. No validation source values were loaded.','',
        '| Cohort | Model | Pool / occurrence edges | Exact numerator / denominator | Integer lower bound | Best feasible F | Excludes 10% | Iterations / stop / seconds |','| --- | --- | --- | --- | ---: | ---: | --- | --- |']
    for a in r['arms']:
        o=a['optimization'];cert=o['certificate'];lines.append(f'| {a["cohort"]} | {a["mode"]} | {a["pool_entries"]}/{a["occurrences"]} | {cert["numerator"]}/{cert["denominator"]} | {cert["integer_lower_bound"]} | {o["best_objective"]} | {cert["excludes_ten_percent"]} | {o["iterations"]}/{o["stop"]}/{o["seconds"]:.2f} |')
    lines+=['','The pool includes shared substrings of every length >= 2, plus pinned seed learned entries and 96 optional characters, excluding fit whole-source/body bans. flex256 permits any 256 entries and relaxes item 24 reserved-character constraints. Bounds do not cover arbitrary one-owner strings beyond seed exceptions, banned strings, source alternatives, arbitrary program subsets, quantile requirements, held-out data or 400-of-500 coverage. Both pools were independently rebuilt from pinned fit inputs before certificate replay. Exact-string bans still permit near-whole shared strings such as a body minus one character. This enlarged relaxation makes a positive lower bound valid, but its witnesses are not claims of M1-legal representations.','',
        '| Cohort/model | Witness | Entries / character entries | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | F | Raw / decoder-source package |','| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |']
    for a in r['arms']:
        for name,w in a['witnesses'].items():
            s=w['selections'];lines.append(f'| {a["cohort"]}/{a["mode"]} | {name} | {w["entries"]}/{w["character_entries"]} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {w["actions"]["total"]} | {w["characters"]}/{100*w["character_fraction"]:.2f}% | {w["objective"]} | {w["package_bytes"]}/{w["package_with_decoder_sources"]} |')
    lines+=['','Witnesses minimize F within their own dictionaries, then N and lexicographic IDs. This is not minimum ratio or canonical minimum-N segmentation. Every stored packet decodes exactly; one Finish, eight-bit selections, 41-byte frames, full dictionary and per-program/amortized storage count. Qualified source hashes are reused from item 13; no fresh runtime qualification or autonomous solving is claimed. Item 23 retained its later unchanged-source exit 137 failure.','',
        '| Cohort/model | Primal proposals / coverage failures | Legacy seed pool additions | Max entry length | Pool / total arm seconds |','| --- | --- | ---: | ---: | ---: |']
    for a in r['arms']:
        o=a['optimization'];lines.append(f'| {a["cohort"]}/{a["mode"]} | {o["primal_attempts"]}/{o["primal_infeasible"]} | {a["seed_legacy_pool_additions"]} | {a["maximum_entry_length"]} | {a["pool_seconds"]:.2f}/{a["seconds"]:.2f} |')
    lines+=['','Generated witnesses are retained separately even when worse than the seed; missing optional coverage proposals are discarded as infeasible and counted, without repair. Floating bounds guide search only. Quantized nonnegative multipliers, integer shortest paths, top-capacity entry sums and separate forward replay establish each reported certificate.','',
        '| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'{r["decoded_packets"]} final witness packets decode; total run wall time {r["seconds"]:.2f} seconds. Six pool tests include 500 exhaustive shared-pool instances and 300 suffix-array/LCP comparisons; four occurrence tests compare 150 old/new graphs and 100 brute-force match sets; five unchanged dual tests include 60 dictionary-bound and 60 path instances; compile/import/help and identity checks passed. Reporting rebuilds both pools, verifies pinned qualification source hashes, and replays exact certificates with the independent Aho-Corasick forward matcher, all witness packets and full cost aggregates without optimization.','',
        'No selected successor or readiness decision. Component intent preserved; canonical decoder and production boundaries unchanged. Training, held-out/protected opening, independent confirmation, publishing private sources, deployment and human studies remain owner-gated. Full installed runtime storage remains unmeasured.','',
        'Rebuild with the pinned NumPy Python: `python -B projects/algorithm_solver/literals/all-length-fraction-v1/report.py --run /private/all-length-fraction/run-v1 --work /private/literal-admission500-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
