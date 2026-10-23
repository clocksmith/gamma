"""Sanitized certificate/cost report; independently replay packets and zero-cost proofs."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from run import HERE,LIT,analyze,ratio


def main(folder,work):
    raw=(folder/'results.json').read_bytes();r=json.loads(raw);c=json.loads((HERE/'contract.json').read_text())
    assert r['contract_sha256']==analyze.sha((HERE/'contract.json').read_bytes())
    arms={(a['seed'],a['policy']):a for a in r['arms']};certs={(x['seed'],x['split']):x for x in r['certificates']}
    assert len(arms)==9 and len(certs)==6
    for seed in c['seeds']:
        root=work/seed['relative_path'];vocab=json.loads((root/'dictionary.json').read_text());texts=json.loads((root/'sources.json').read_text());db=analyze.dictionary_bytes(vocab)
        assert analyze.sha((root/'dictionary.json').read_bytes())==c['private_files'][seed['relative_path']+'/dictionary.json']
        assert analyze.sha((root/'sources.json').read_bytes())==c['private_files'][seed['relative_path']+'/sources.json']
        for policy in ('canonical','min_char','min_fraction'):
            a=arms[seed['name'],policy];private=folder/f'{seed["name"]}-{policy}';seqs=json.loads((private/'sequences.json').read_text())
            assert set(a['per_problem'])==set(texts)==set(seqs)
            for pid,row in a['per_problem'].items():
                packet=(private/f'{pid}.bin').read_bytes();seq=seqs[pid];text=texts[pid]
                assert analyze.encode(vocab,seq,seed['width'])==packet and analyze.decode(db,packet)==text
                assert analyze.sha(packet)==row['packet_sha256'] and analyze.sha(text.encode())==row['source_sha256']
                assert ratio.counts(vocab,seq)==(row['single_characters'],row['selections'])
                row['one_program_package_bytes']=len(db)+len(packet);row['one_program_with_decoder']=len(db)+len(packet)+c['decoder_dependency_bytes']
            a['contrasts']={}
            for split in ('fit','validation'):
                d=a[split];a['contrasts'][split]={}
                for comparator in ('canonical','min_char'):
                    b=arms[seed['name'],comparator][split]
                    a['contrasts'][split][comparator]={'extra_actions':d['actions']['total']-b['actions']['total'],
                        'extra_action_fraction':d['actions']['total']/b['actions']['total']-1,
                        'character_delta':d['single_character_codes']-b['single_character_codes'],
                        'fraction_delta':d['single_character_fraction']-b['single_character_fraction']}
        for split,key in [('fit','dev_fit'),('validation','dev_val')]:
            cert=certs[seed['name'],split];subset={str(i):texts[str(i)] for i in c['partition'][key]}
            proof=ratio.certificate(subset,vocab,cert['p'],cert['q'])
            assert proof==cert['per_problem'] and sum(x['minimum_transformed_cost'] for x in proof.values())==0
            assert sum(x['minimum_selections_at_cost'] for x in proof.values())==cert['selections']
            d=arms[seed['name'],'min_fraction'][split]
            assert (d['single_character_codes'],d['selections']['total'])==(cert['characters'],cert['selections'])
            assert Fraction(cert['characters'],cert['selections'])==Fraction(cert['p'],cert['q'])
            cert['ten_percent_reachable']=10*cert['p']<=cert['q']
            b=arms[seed['name'],'min_char'][split]
            assert Fraction(cert['p'],cert['q'])<=Fraction(b['single_character_codes'],b['selections']['total'])
    old={(a['arm'],a['width']):a for a in json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())['arms']}
    r['predictions']={'F1':all(arms[s['name'],'canonical'][split]['selections']['total']==old[s['arm'],s['width']][split]['selections']['total'] for s in c['seeds'] for split in ('fit','validation')),
        'F2':r['decodes']==3600 and all(x['certified'] and x['independent_minimum_sum']==0 for x in certs.values()),
        'F3':all(Fraction(certs[n,'validation']['p'],certs[n,'validation']['q'])<Fraction(arms[n,'min_char']['validation']['single_character_codes'],arms[n,'min_char']['validation']['selections']['total']) for n in ('R256','naming256')),
        'F4':not any(x['ten_percent_reachable'] for (n,s),x in certs.items() if s=='validation'),
        'F5':all(arms[n,'min_fraction']['validation']['actions']['total']>1.05*arms[n,'canonical']['validation']['actions']['total'] for n in ('R256','naming256'))}
    r['private_results_sha256']=analyze.sha(raw);r['offline_tooling_bytes']=c['offline_tooling_bytes'];r['decoder_dependency_bytes']=c['decoder_dependency_bytes']
    def clean(v):
        if isinstance(v,dict):
            assert not {'vocab','sources','sequences','tokens','text'}&set(v)
            for x in v.values():clean(x)
        elif isinstance(v,list):
            for x in v:clean(x)
    clean(r);(HERE/'evidence').mkdir(exist_ok=True);analyze.write(HERE/'evidence/results.json',r)
    lines=['# Exact minimum character fraction for fixed dictionaries','','[Freeze](FREEZE.md) pushed as `c956bb322`; [review/run receipt](REVIEW.md); [evidence](evidence/results.json). Private source, dictionary and sequence artifacts remain private.','',
        'This diagnostic minimizes the aggregate ratio C/N over every segmentation of each fixed source/codebook pair. It uses consumed development sources to choose separate coefficients for each split. It is not a transferable fitted encoder, a new candidate or a change to previous canonical results.','',
        'None of these fixed validation source/codebook pairs can reach the 10% character-fraction gate under any segmentation. The exact optima and their additional action costs are below; changing sources or dictionaries is outside this conclusion.','',
        '| Seed | Split | Exact minimum C/N | Minimum fraction | 10% reachable? | Actions at optimum | Extra actions vs canonical | Iterations | Independent minimum sum |',
        '| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |']
    for (name,split),x in certs.items():
        a=arms[name,'min_fraction'];d=a[split];lines.append(f'| {name} | {split} | {x["p"]}/{x["q"]} | {100*x["p"]/x["q"]:.2f}% | {x["ten_percent_reachable"]} | {d["actions"]["total"]} | {a["contrasts"][split]["canonical"]["extra_actions"]} | {len(x["iterations"])} | {x["independent_minimum_sum"]} |')
    lines+=['','At the final p/q, every path has summed transformed cost q*C-p*N at least zero, and the decoded witness attains zero. A separate forward DAG replays that minimum with integer arithmetic. The witness also has the fewest total selections among paths attaining this ratio. This proves only the fixed-source, fixed-dictionary fraction optimum; other dictionaries or source rewrites are outside the certificate.','',
        '| Seed | Policy | Split | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |',
        '| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |']
    for (name,policy),a in arms.items():
        for split in ('fit','validation'):
            d=a[split];s=d['selections'];lines.append(f'| {name} | {policy} | {split} | {s["total"]} | {s["median"]}/{s["p90"]}/{s["p95"]}/{s["worst"]} | {s["within_32"]}/{s["within_96"]} | {d["actions"]["total"]} | {d["single_character_codes"]}/{100*d["single_character_fraction"]:.2f}% | {d["package_bytes"]} | {d["package_with_decoder_dependencies"]} |')
    lines+=['','All rows cover and reuse exact-source qualification for 300 fit or 100 validation programs. Every literal selection, one Finish, unchanged seven/eight-bit width, dictionary, 41-byte frame and padding are charged. Full runtime installation storage is unmeasured. Lowering the fraction can consume more learned-symbol selections without removing character selections; the action and storage cost is part of the result.','',
        '| Seed | Minimum-ratio validation contrast | Extra actions | Action change | Character-code delta | Fraction change (percentage points) |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for seed in c['seeds']:
        for base,d in arms[seed['name'],'min_fraction']['contrasts']['validation'].items():
            lines.append(f'| {seed["name"]} | vs {base} | {d["extra_actions"]} | {100*d["extra_action_fraction"]:.2f}% | {d["character_delta"]} | {100*d["fraction_delta"]:.2f} |')
    lines+=['','| Prediction | Met |','| --- | --- |']+[f'| {k} | {v} |' for k,v in r['predictions'].items()]
    lines+=['',f'All {r["decodes"]:,} packets and six certificates replay during reporting. Measured run time: {r["seconds"]:.2f} seconds. Five focused tests include100 exhaustive paired-text examples and denominator/tie/cap checks. Qualification is hash reuse, not fresh execution.','',
        'No promotion or canonical encoder change. Component intent preserved; no M1 thresholds, production behavior or owner gates changed. No training, protected opening, source publication, deployment, human study or ledger/catalog/claim write.','',
        'Rebuild: `python3 -B projects/algorithm_solver/literals/fraction-certificate-v1/report.py --run /private/fraction-certificate/run-v1 --work /private/literal-admission500-v1`.','']
    (HERE/'README.md').write_text('\n'.join(lines))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();main(a.run,a.work)
