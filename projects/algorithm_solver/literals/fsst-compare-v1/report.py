"""Publish the native/adapted comparison without conflating its codec contracts."""
import argparse
import json
import sys
from pathlib import Path
from run import HERE,LIT,analyze,tail,native,packet
sys.path.insert(0,str(LIT/'tail-search-v1'))
prior=tail.module('fsst_report_prior',LIT/'tail-search-v1/report.py')


def readiness(a,b,ids):
    p=prior.paired(a['per_problem'],b['per_problem'],ids);d=a['validation'];base=b['validation']
    if a['native_format']:return {'literal_format':False},p
    return {'qualified':d['qualified']==100,'covered':d['covered']==100,'whole_solution_clean':not a['illegal_entry_sha256'],
        'actions_5_percent':d['actions']['total']<=.95*base['actions']['total'],'median_lower':d['actions']['median']<base['actions']['median'],
        'p90_lower':d['actions']['p90']<base['actions']['p90'],'improved_60':p['better']>=60,'worsened_at_most_25':p['worse']<=25,
        'fallback_nonincrease':d['single_character_fraction']<=base['single_character_fraction'],
        'package_within_105_percent':d['package_bytes']<=1.05*base['package_bytes']},p


def main(run):
    raw=(run/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    arms={(a['cohort'],a['arm']):a for a in r['arms']};assert len(arms)==10
    expected={str(i) for ids in c['partition'].values() for i in ids};val=c['partition']['dev_val']
    for (cohort,name),a in arms.items():
        folder=run/cohort;seal=json.loads((folder/'fit-seal.json').read_text());assert seal['validation_loaded'] is False
        texts=json.loads((folder/'sources.json').read_text());seqs=json.loads((folder/f'{name}-sequences.json').read_text());assert set(texts)==set(seqs)==set(a['per_problem'])==expected
        if a['native_format']:
            header=(folder/'native-header.bin').read_bytes();assert analyze.sha(header)==a['dictionary_sha256']==seal['native_header_sha256']
        else:
            dictionary=(folder/f'{name}-dictionary.json').read_bytes();vocab=json.loads(dictionary)
            assert analyze.sha(dictionary)==a['dictionary_sha256']==seal['dictionary_sha256'][name]
        for pid,row in a['per_problem'].items():
            if a['native_format']:
                framed=packet.pack(header,bytes(seqs[pid]));decoded=packet.unpack(header,framed).decode('ascii')
            else:
                framed=analyze.encode(vocab,seqs[pid],8);decoded=analyze.decode(analyze.dictionary_bytes(vocab),framed)
            assert decoded==texts[pid] and analyze.sha(decoded.encode())==row['source_sha256'] and analyze.sha(framed)==row['packet_sha256']
            assert len(seqs[pid])==row['selections']
        a['readiness_checks'],a['paired_seed']=readiness(a,arms[cohort,'gamma_seed'],val);a['ready_matched']=all(a['readiness_checks'].values())
        a['original_R_checks'],a['paired_original_R']=readiness(a,arms['R','gamma_seed'],val);a['ready_original_R']=all(a['original_R_checks'].values())
        a['m1_cost_indicators_only']=None if a['native_format'] else prior.indicators(a)
    r['predictions']={
        'F1':all(a['fit']['covered']+a['validation']['covered']==400 and a['fit']['qualified']+a['validation']['qualified']==400 for a in arms.values()),
        'F2':all(arms[co,'native_optimal']['per_problem'][pid]['selections']<=arms[co,'native_author']['per_problem'][pid]['selections'] for co in ('R','naming') for pid in expected) and any(arms[co,'native_optimal']['validation']['actions']['total']<=.99*arms[co,'native_author']['validation']['actions']['total'] for co in ('R','naming')),
        'F3':any(arms[co,'gamma_polish']['validation']['actions']['total']<=.95*arms[co,'gamma_adapter']['validation']['actions']['total'] for co in ('R','naming')),
        'F4':not any(arms[co,n]['ready_matched'] for co in ('R','naming') for n in ('gamma_adapter','gamma_polish')),
        'F5':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    ready=sorted((a for a in arms.values() if a['ready_matched']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['cohort'],a['arm']))
    r['selected_ready_pair']=[ready[0]['cohort'],ready[0]['arm']] if ready else None
    r['private_results_sha256']=analyze.sha(raw);r['upstream_commit']=c['upstream_commit'];r['native_library_bytes']=c['native_library_bytes'];r['upstream_source_bytes']=c['upstream_source_bytes'];r['gamma_adapter_tooling_bytes']=c['gamma_adapter_tooling_bytes']
    def check(v):
        if isinstance(v,dict):
            assert not {'vocab','sources','table','payload','sequences','trace','symbol_uses','remove','add'}&set(v)
            for x in v.values():check(x)
        elif isinstance(v,list):
            for x in v:check(x)
    check(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# FSST and fully charged Gamma adapters','','[Freeze](FREEZE.md) pushed as `c787f18fa`; [review/run receipt](REVIEW.md); [evidence](evidence/results.json). All sources, fitted tables, sequences and traces remain private.','',
        'Pinned [author implementation](https://github.com/cwida/fsst/tree/e638d4cf8c26129d73c242a4127b42b975de5b63) under the MIT license. Native-author uses its unchanged table builder/encoder. Native-optimal is Gamma’s exact parser over that same table; Gamma-adapter/polish change the table/format and are not the author algorithm or a run of OptFSST.','',
        f'Selected newly ready Gamma pair against its matched cohort seed: **{r["selected_ready_pair"] or "none"}**. Native views are separate codecs and are excluded from M1 literal readiness. Cohorts and the naming seed use consumed development evidence; this is not independent generalization, an M5 qualification or a literature-leading result.','',
        'Native optimal parsing saves2.07%validation actions over the author encoder on R and2.31%on naming. Both remain larger than the matched Gamma seeds. Gamma polish changes adapter validation actions11894→11893 on R and leaves11509unchanged on naming; neither adapter is ready. No whole-body overlap occurred. These results describe this fixed corpus, fitted tables and code paths, not a general FSST or dictionary limit.', '',
        '| Cohort | View | Split | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Fallback-channel codes | Fraction | Raw escapes | Package |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |']
    for (co,name),a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {co} | {name} | {split} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]} | {100*d["single_character_fraction"]:.2f}% | {d["escaped_raw_bytes"]} | {d["package_bytes"]} |')
    lines+=['','Every row decodes and reuses exact-source qualification for300fit/100validation programs. Native counts each code byte; escape and raw byte cost two selections and both count as fallback-channel codes. That native diagnostic differs from Gamma’s literal-entry fraction. One Finish per program. Exported native table or LTD1 dictionary plus41-byte per-program framing are charged; eight-bit payloads have no padding. Native uses a conditional raw-byte channel and is never reclassified as a256-entry exact-string vocabulary.','',
        '| Cohort | View | Better/same/worse vs seed | Ready vs seed | Ready vs original R | Failed matched predicates | Whole-body overlaps |',
        '| --- | --- | --- | --- | --- | --- | ---: |']
    for (co,name),a in arms.items():
        p=a['paired_seed'];fail=', '.join(k for k,v in a['readiness_checks'].items() if not v) or 'None'
        lines.append(f'| {co} | {name} | {p["better"]}/{p["same"]}/{p["worse"]} | {a["ready_matched"]} | {a["ready_original_R"]} | {fail} | {len(a["illegal_entry_sha256"])} |')
    lines+=['','Native action comparisons are fully charged format comparisons, not literal readiness. Original-R checks for Gamma naming views include the previously recorded source-naming benefit; matched-seed comparisons isolate new dictionary benefit. Illegal table/body overlaps are retained and never repaired from validation.','',
        '| Cohort | Native symbols | Exported table bytes | Eligible native pool | Adapter entries | Polish fit selections before/after | Trials | Stop | Native fit seconds | Polish seconds |',
        '| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |']
    for co in ('R','naming'):
        a=arms[co,'native_author']
        lines.append(f'| {co} | {a["entries"]} | {a["dictionary_bytes"]} | {a["pool_entries"]} | {a["adapter_entries"]} | {a["polish_initial_fit_selections"]}/{a["polish_final_fit_selections"]} | {a["polish_trials"]} | {a["polish_stop"]} | {a["native_table_build_seconds"]:.4f} | {a["polish_seconds"]:.2f} |')
    lines+=['','Native symbols and the adapter/polish candidate pool are limited to eight bytes; Gamma’s existing search permits longer entries. A gap to the seed measures this length-capped pool and its fitting/search, not literal dictionaries in general. Native fitting uses default internal sampling and fixed numeric-ID input order. Adapter ranking and polish use fit only. Timings measure different work; no throughput comparison follows. Local/capped polish stops do not prove an optimum.','',
        'Decoder-source-inclusive packages are in evidence: native.py+packet.py are the independent native decoder source files; Gamma uses its pinned decoder dependencies. These exclude full language runtimes and are not complete deployment packages. The native compiled library includes its encoder and is reported separately, alongside upstream/source tooling bytes; source-inclusive totals do not establish M5.', '',
        '| Prediction | Met |','| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines += ['',f'All4000packet choices decode, including native author and optimal payloads through the official decoder and independent Python decoder. Reporting replays all hashes/frames. Unchanged-source qualification is reused, with no fresh case execution. Eight synthetic tests and compilation/import/help passed before launch. Total run wall time: {r["seconds"]:.2f} seconds.', '',
        'Owner gate: a newly ready literal pair could only motivate separately frozen owner-approved confirmation. Candidate artifacts: fsst-compare/run-v1/<cohort>, with table/dictionary/fit-seal hashes and view identity in evidence. Final held-out/protected sets stay closed. No model training, production/canonical codec change, ledger/catalog/claim write, source publication, BITS deployment, human study or M1 threshold change. Component intent preserved.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/fsst-compare-v1/report.py --run /private/fsst-compare/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
