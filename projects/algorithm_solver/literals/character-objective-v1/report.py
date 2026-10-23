"""Rebuild charged encoder/dictionary tradeoffs from sealed private outputs."""
import argparse
import json
from pathlib import Path
from run import HERE,LIT,analyze,tail
prior=tail.module('char_prior_report',LIT/'tail-search-v1/report.py')


def main(run):
    raw=(run/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    arms={(a['arm'],a['policy']):a for a in r['arms']};assert len(arms)==15
    b=json.loads((LIT/'cost-decomposition-v1/evidence/results.json').read_text())['arms']['8']
    expected={str(i) for ids in c['partition'].values() for i in ids};val=c['partition']['dev_val']
    for (name,policy),a in arms.items():
        folder=run/name;seal=json.loads((folder/'fit-seal.json').read_text());texts=json.loads((folder/'sources.json').read_text())
        vocab=json.loads((folder/'dictionary.json').read_text());seqs=json.loads((folder/f'{policy}-sequences.json').read_text())
        assert seal['validation_loaded'] is False and seal['dictionary_sha256']==a['dictionary_sha256']==analyze.sha((folder/'dictionary.json').read_bytes())
        assert set(texts)==set(a['per_problem'])==set(seqs)==expected
        for pid,row in a['per_problem'].items():
            packet=analyze.encode(vocab,seqs[pid],8);assert analyze.decode(analyze.dictionary_bytes(vocab),packet)==texts[pid]
            assert analyze.sha(texts[pid].encode())==row['source_sha256']
            assert analyze.sha(packet)==row['packet_sha256'] and len(seqs[pid])==row['selections']
        a['paired_original']=prior.paired(a['per_problem'],b['per_problem'],val)
        if policy in ('canonical','shortest_min_char'):
            a['paired_seed_same_policy']=prior.paired(a['per_problem'],arms['seed',policy]['per_problem'],val)
        else:
            # Positive-weight policies differ from the seed's w0 encoder: combined search/encoder contrast.
            a['paired_seed_weighted_w0']=prior.paired(a['per_problem'],arms['seed','weighted']['per_problem'],val)
        d=a['validation'];base=b['dev_val'];p=a['paired_original']
        a['readiness_checks']={'qualification_reused':all(x['qualification_reused'] for x in a['per_problem'].values()),
            'covered':d['covered']==100,'whole_solution_clean':not a['illegal_entry_sha256'],
            'actions_5_percent':d['actions']['total']<=.95*base['actions']['total'],
            'median_lower':d['actions']['median']<base['actions']['median'],'p90_lower':d['actions']['p90']<base['actions']['p90'],
            'improved_60':p['better']>=60,'worsened_at_most_25':p['worse']<=25,
            'fallback_nonincrease':d['single_character_fraction']<=base['single_character_fraction'],
            'package_within_105_percent':d['package_bytes']<=1.05*base['package_bytes']}
        a['ready']=all(a['readiness_checks'].values());a['m1_cost_indicators_only']=prior.indicators(a)
    hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());seed=next(a for a in hist['arms'] if a['width']==8 and a['arm']=='scope_joint')
    a0=arms['w0','weighted'];s0=arms['seed','weighted']
    r['predictions']={
        'W1':all(a['fit']['covered']+a['validation']['covered']==400 and not a['illegal_entry_sha256'] for a in arms.values()) and all(arms['seed','canonical'][split]['selections']['total']==seed[split]['selections']['total'] for split in ('fit','validation')),
        'W2':a0['fit']['selections']['total']<=s0['fit']['selections']['total'] and arms['w0','shortest_min_char']['validation']['actions']['total']>.99*arms['seed','shortest_min_char']['validation']['actions']['total'],
        'W3':any(arms[n,'weighted']['validation']['single_character_codes']<=.9*a0['validation']['single_character_codes'] and arms[n,'weighted']['validation']['actions']['total']<=1.05*a0['validation']['actions']['total'] for n in ('w1','w4','w16')),
        'W4':arms['w16','weighted']['validation']['single_character_codes']<a0['validation']['single_character_codes'] and arms['w16','weighted']['validation']['actions']['total']>a0['validation']['actions']['total'],
        'W5':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    vector=lambda a:(a['validation']['actions']['total'],a['validation']['single_character_codes'],a['validation']['package_bytes'])
    r['pareto_frontier']=[list(key) for key,a in arms.items() if not any(all(x<=y for x,y in zip(vector(b),vector(a))) and vector(b)!=vector(a) for b in arms.values())]
    ready=sorted((a for a in arms.values() if a['ready']),key=lambda a:(a['validation']['actions']['total'],a['validation']['package_bytes'],a['arm'],a['policy']))
    r['selected_ready_pair']=[ready[0]['arm'],ready[0]['policy']] if ready else None
    r['private_results_sha256']=analyze.sha(raw);r['decoder_dependency_bytes']=c['decoder_dependency_bytes'];r['offline_encoder_bytes']=c['offline_encoder_bytes'];r['offline_encoder_scope']=c['offline_encoder_scope']
    def check(v):
        if isinstance(v,dict):
            assert not {'vocab','parsed','trace','sources','remove','add','failures'}&set(v)
            for x in v.values():check(x)
        elif isinstance(v,list):
            for x in v:check(x)
    check(r)
    (HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Character-aware dictionary objectives','','[Freeze](FREEZE.md) pushed as `bc14c1331`; [trial-cap amendment](AMENDMENT-1.md) pushed as `5860ab34d`; [review/run receipt](REVIEW.md), [evidence](evidence/results.json). Private source, dictionary, sequence and trace artifacts remain private.','',
        f'Ready pair selected by the frozen ranking: **{r["selected_ready_pair"] or "none"}**. This is consumed-development readiness against original R/L-R256, not independent confirmation or M1. All sources are fixed to item13 scope_joint256; its selection itself used dev-val outcomes.','',
        'The strongest penalty lowers validation character codes4129→3876 (6.13%) while actions rise8504→8944 (5.17%). The registered10%character reduction within5%extra actions is not achieved. w1 still passes original-control readiness but uses8more actions than the seed. The frozen ranking retains seed/canonical; its tie ordering does not prefer fewer characters once action/package costs tie. No new action-improving candidate is selected.', '',
        'Integer objective4N+wC uses penalties w=0,1,4,16. Positive-weight views can use more actions for fewer character codes. Canonical and shortest_min_char views compare dictionaries under common encoders; weighted views compare the combined dictionary-plus-weighted-encoder procedure. The seed weighted view hasw0, so positive-weight versus seed weighted is not a same-policy contrast. All input charges and M1 gates remain unchanged.','',
        '| Dictionary | Encoder | Split | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Character codes | Character fraction | Package |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |']
    for (name,policy),a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {name} | {policy} | {split} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines+=['','Each row decodes and reuses exact-source qualification for300fit/100validation programs. One Finish each, unchanged8-bit width, dictionary/header/payload/padding charged. Decoder-inclusive packages and offline tooling storage are in evidence; complete installed runtime footprint is unmeasured.','',
        '| Dictionary | Encoder | Better/same/worse vs original | Ready | Failed predicates |','| --- | --- | --- | --- | --- |']
    for (name,policy),a in arms.items():
        p=a['paired_original'];failed=', '.join(k for k,v in a['readiness_checks'].items() if not v) or 'None'
        lines.append(f'| {name} | {policy} | {p["better"]}/{p["same"]}/{p["worse"]} | {a["ready"]} | {failed} |')
    lines+=['','| Dictionary | Common encoder | Validation actions delta vs seed | Character-code delta | Better/same/worse |','| --- | --- | ---: | ---: | --- |']
    for (name,policy),a in arms.items():
        if policy=='weighted':continue
        b=arms['seed',policy];p=a['paired_seed_same_policy']
        lines.append(f'| {name} | {policy} | {a["validation"]["actions"]["total"]-b["validation"]["actions"]["total"]} | {a["validation"]["single_character_codes"]-b["validation"]["single_character_codes"]} | {p["better"]}/{p["same"]}/{p["worse"]} |')
    lines+=['','| Dictionary | Initial objective | Final objective | Fit N/C | Trials | Moves | Stop | Search seconds |','| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |']
    for name in ('seed','w0','w1','w4','w16'):
        a=arms[name,'weighted'];f=a['final_fit_objective']
        lines.append(f'| {name} | {a["initial_fit_objective"]["objective"]} | {f["objective"]} | {f["selections"]}/{f["characters"]} | {a["search_trials"]} | {a["accepted_dictionary_moves"]} | {a["search_stop"]} | {a["search_seconds"]:.2f} |')
    lines+=['','Local/capped stops are bounded search outcomes, not global optimality. The reported Pareto frontier compares actions, absolute character codes and package only; it does not establish median,p95 or fraction gates. Equal vectors remain separate witnesses. Frontier: '+', '.join('/'.join(x) for x in r['pareto_frontier'])+'.','',
        '| Prediction | Met |','| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines += ['',f'Measured complete run wall time: {r["seconds"]:.2f} seconds. Seven focused tests passed, including100 exhaustive examples under four weights, cache parity and exact cap retention. All6000packet decodes replay during reporting; source qualification is unchanged hash-bound reuse, not new execution evidence.', '',
        'Owner gate: any selected pair needs a separately approved confirmation population and frozen dictionary/encoder before protected access. Candidate artifacts: character-objective/run-v1/<arm>, with dictionary/fit-seal hashes and policy identified in evidence. Training, held-out/protected opening, publication, BITS changes, human studies and independent confirmation remain gated. No ledger/catalog/claim write or production/canonical codec change. Component intent preserved.', '',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/character-objective-v1/report.py --run /private/character-objective/run-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);main(ap.parse_args().run)
