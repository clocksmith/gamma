"""Publish counts and hashes for the fixed-source segmentation objectives."""
import argparse
import json
from pathlib import Path
from run import HERE,LIT,analyze,segment


def main(run,work):
    raw=(run/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    arms={(a['seed'],a['policy']):a for a in r['arms']};seeds={s['name']:s for s in c['seeds']};val=c['partition']['dev_val']
    assert len(arms)==16
    for (name,policy),a in arms.items():
        seed=seeds[name];folder=work/seed['relative_path'];vocab=json.loads((folder/'dictionary.json').read_text());texts=json.loads((folder/'sources.json').read_text())
        seqs=json.loads((run/f'{name}-{policy}-sequences.json').read_text())
        assert analyze.sha((folder/'dictionary.json').read_bytes())==a['dictionary_sha256']
        for pid,row in a['per_problem'].items():
            seq=seqs[pid];packet=analyze.encode(vocab,seq,seed['width']);text=analyze.decode(analyze.dictionary_bytes(vocab),packet)
            assert text==texts[pid] and analyze.sha(text.encode())==row['source_sha256']
            assert len(seq)==row['selections'] and sum(len(vocab[i])==1 for i in seq)==row['single_characters']
            assert analyze.sha(packet)==row['packet_sha256']
        base=arms[name,'canonical'];pairs={}
        for split,ids in [('fit',c['partition']['dev_fit']),('validation',val)]:
            pairs[split]={metric:{'better':sum(a['per_problem'][str(i)][metric]<base['per_problem'][str(i)][metric] for i in ids),
                  'same':sum(a['per_problem'][str(i)][metric]==base['per_problem'][str(i)][metric] for i in ids),
                  'worse':sum(a['per_problem'][str(i)][metric]>base['per_problem'][str(i)][metric] for i in ids)} for metric in ('selections','single_characters')}
        a['paired_canonical']=pairs
        d=a['validation'];a['m1_cost_indicators_only']=d['covered']==100 and d['selections']['median']<=32 and d['selections']['p95']<=96 and d['single_character_fraction']<=.1
    b=arms['control256','canonical']['validation'];lo=arms['control256','shortest_min_char']['validation'];mc=arms['control256','min_char']['validation']
    r['predictions']={'T1':r['decodes']==6400,
        'T2':lo['single_character_codes']<=.95*b['single_character_codes'] and lo['actions']['total']==b['actions']['total'],
        'T3':mc['single_character_codes']<=.9*b['single_character_codes'] and mc['actions']['total']>b['actions']['total'],
        'T4':not any(a['m1_cost_indicators_only'] for a in arms.values())}
    r['private_results_sha256']=analyze.sha(raw);r['extra_offline_encoder_bytes']=c['offline_extra_encoder_bytes'];r['decoder_dependency_bytes']=c['decoder_dependency_bytes']
    (HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Fixed-source segmentation and character-tail audit','','[Freeze](FREEZE.md) pushed as `c036ba20c`; [review/run receipt](REVIEW.md), [sanitized evidence](evidence/results.json). Source, dictionary and sequence artifacts remain private.','',
        'This measures exact alternative segmentations of already qualified programs. Historical canonical packets and encoders remain unchanged. Seeds and their selection use consumed development evidence; this is neither independent confirmation nor a new source/dictionary readiness result.','',
        f'At control256, minimizing character codes among shortest paths changes validation codes from {b["single_character_codes"]} to {lo["single_character_codes"]} ({100*(1-lo["single_character_codes"]/b["single_character_codes"]):.2f}% fewer), with {lo["actions"]["total"]} actions unchanged. Minimizing absolute character codes first yields {mc["single_character_codes"]} codes at {mc["actions"]["total"]} actions.','',
        '| Seed | Policy | Split | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Character codes | Character fraction | Package bytes |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |']
    for (name,policy),a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections']
            lines.append(f'| {name} | {policy} | {split} | {s["total"]} | {s["median"]} | {s["p90"]} | {s["p95"]} | {s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]} | {100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} |')
    lines+=['','Each row covers and reuses qualification for all300 fit or100 validation programs. One Finish per program; unchanged7/8-bit width, dictionary bytes,41-byte framing and padding all charged. Decoder-inclusive packages and offline additional encoder bytes are in evidence; full runtime installation storage remains unmeasured.','',
        '| Seed | Policy | Validation character count better/same/worse | Validation selections better/same/worse |','| --- | --- | --- | --- |']
    for (name,policy),a in arms.items():
        d=a['paired_canonical']['validation'];fmt=lambda x:f'{x["better"]}/{x["same"]}/{x["worse"]}'
        lines.append(f'| {name} | {policy} | {fmt(d["single_characters"])} | {fmt(d["selections"])} |')
    lines+=['','`shortest_min_char` and `shortest_max_char` give the exact character-count range among minimum-selection paths for these fixed sources/dictionaries. At that fixed count, character fraction has the same ordering. `min_char` minimizes absolute character codes, then selections; it does not minimize fraction and cannot bound fraction when a larger denominator is allowed. These are restricted encoding optima, not dictionary-search or representation impossibility results.','',
        '| Prediction | Met |','| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'All {r["decodes"]:,} packets independently decode and are rechecked during reporting; canonical sequences exactly reproduce the existing encoder and published N/C counts. Every per-program objective inequality passed. Source qualification and whole-source/body legality are reused from item13 with unchanged hashes, not freshly executed cases. Measured wall time: {r["seconds"]:.2f} seconds. Four focused tests include150 exhaustive tiny examples under all four policies.', '',
        'No new candidate promotion is requested by this audit. Changing the canonical encoder or promoting an alternative needs a separate freeze and review; owner-approved independent confirmation remains required for broader claims. Final held-out/protected sets stay closed. No source rewrite, training, deployment, publication, human study, ledger/catalog/claim write or M1 threshold change. Component intent and production boundaries preserved.','',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/segmentation-audit-v1/report.py --run /private/segmentation-audit/run-v1 --work /private/literal-admission500-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
