"""Rerunnable stack report; no optimization, source rewrite or test execution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICIES = ('canonical', 'shortest_min_char')
CANDIDATES = ('N', 'NC', 'NP', 'NCP', 'D00', 'D01', 'D10', 'D11')


def paired(a, b, ids):
    counts = {'better': 0, 'same': 0, 'worse': 0}
    for pid in map(str, ids):
        x, y = a['per_problem'][pid], b['per_problem'][pid]
        if not x['encodable']:
            counts['worse'] += 1
        elif not y['encodable']:
            counts['better'] += 1
        else:
            counts['better' if x['actions'] < y['actions'] else 'worse' if x['actions'] > y['actions'] else 'same'] += 1
    return counts


def checks(a, b, ids, *, initial=False):
    x, y = a['validation'], b['validation']
    coverage = (a['fit']['covered'] == a['fit']['qualified'] == 300 and
                x['covered'] == x['qualified'] == 100 and
                b['fit']['covered'] == b['fit']['qualified'] == 300 and
                y['covered'] == y['qualified'] == 100)
    audit = (a['entries'] <= 256 and not a['illegal_entry_sha256']
             and b['entries'] <= 256 and not b['illegal_entry_sha256'])
    relation = paired(a, b, ids)
    if not coverage:
        return {'coverage_and_qualification': False, 'legal_dictionary': audit,
                'actions': False, 'median': False, 'p90': False,
                'breadth': False, 'fraction': False, 'package': False}
    ax, by = x['actions'], y['actions']
    return {'coverage_and_qualification': coverage, 'legal_dictionary': audit,
            'actions': ax['total'] <= .95*by['total'] if initial else ax['total'] < by['total'],
            'median': ax['median'] < by['median'] if initial else ax['median'] <= by['median'],
            'p90': ax['p90'] < by['p90'] if initial else ax['p90'] <= by['p90'],
            'breadth': relation['worse'] <= 25 and (not initial or relation['better'] >= 60),
            'fraction': x['single_character_fraction'] <= y['single_character_fraction'],
            'package': x['package_bytes'] <= 1.05*y['package_bytes']}


def build(result, contract):
    result = copy.deepcopy(result)
    index = {(a['arm'], a['policy']): a for a in result['arms']}
    ids = contract['partition']['dev_val']
    by_policy = {}
    for policy in POLICIES:
        for name in ('R', 'seed13', 'best24', *CANDIDATES):
            a = index[name, policy]
            a['paired'] = {ref: paired(a, index[ref, policy], ids) for ref in ('R', 'seed13', 'best24', 'N', 'NCP')}
            a['readiness_checks'] = checks(a, index['R', policy], ids, initial=True)
            refs = ['seed13', 'best24', 'N']
            if name.startswith('D'):
                refs += ['NCP']
                if name.endswith('1'):
                    refs += [name[:2]+'0']
            a['incremental_checks'] = {ref: checks(a, index[ref, policy], ids) for ref in dict.fromkeys(refs)}
            a['ready'] = all(a['readiness_checks'].values())
            a['successor'] = (name in CANDIDATES and a['ready'] and
                              all(all(v.values()) for v in a['incremental_checks'].values()))
            a['failed_predicates'] = ([f'R:{k}' for k, v in a['readiness_checks'].items() if not v] +
                                      [f'{ref}:{k}' for ref, cs in a['incremental_checks'].items() for k, v in cs.items() if not v])
        eligible = [index[n, policy] for n in CANDIDATES if index[n, policy]['successor']]
        eligible.sort(key=lambda a: (a['validation']['actions']['total'], a['validation']['package_bytes'],
                                     a['validation']['single_character_fraction'], CANDIDATES.index(a['arm'])))
        by_policy[policy] = eligible[0]['arm'] if eligible else None
    selected = by_policy['shortest_min_char']
    result['selected_successor'] = selected
    result['selected_by_policy'] = by_policy
    result['retained_default'] = None if selected else {'arm': 'best24', 'policy': 'canonical'}
    p = 'shortest_min_char'
    valid = lambda n: index[n, p]['validation']['covered'] == 100
    action = lambda n: index[n, p]['validation']['actions']['total']
    result['predictions'] = {
        'S1_references_and_all_packets_replay': True,  # verified by main below
        'S2_coupled_improves_actions_vs_ordinary': valid('NC') and valid('N') and action('NC') < action('N'),
        'S3_compiler_improves_combined_vs_coupled': valid('NCP') and valid('NC') and action('NCP') < action('NC'),
        'S4_optional_improves_vs_fixed': valid('D10') and valid('D00') and action('D10') < action('D00'),
        'S5_character_penalty_lowers_C_without_extra_actions': any(
            valid(n) and valid(n[:2]+'0') and
            index[n,p]['validation']['single_character_codes'] < index[n[:2]+'0',p]['validation']['single_character_codes'] and
            action(n) <= action(n[:2]+'0') for n in ('D01','D11')),
        'S6_new_ready_successor_over_best24': selected is not None,
    }
    return result


def replay_arm(a, sources, vocab, dictionary, packet_dir, banned, c, e, known, fresh):
    """Reconstruct every measured row and verdict from immutable input artifacts."""
    ids={str(pid) for group in c['partition'].values() for pid in group}
    assert set(sources)==set(a['per_problem'])==set(a['qualification'])==ids
    assert a['policy'] in POLICIES and a['width']==8
    assert len(vocab)==len(set(vocab))<=256 and all(isinstance(word,str) and word for word in vocab)
    assert dictionary==e.analyze.dictionary_bytes(vocab)
    assert a['entries']==len(vocab) and a['character_entries']==sum(len(word)==1 for word in vocab)
    assert a['dictionary_bytes']==len(dictionary) and a['dictionary_binary_sha256']==e.analyze.sha(dictionary)
    illegal=sorted(e.analyze.sha(word.encode()) for word in set(vocab)&set(banned))
    assert a['illegal_entry_sha256']==illegal,'whole-source/body audit differs'
    replay={}
    for pid,text in sorted(sources.items()):
        row={'source_sha256':e.analyze.sha(text.encode()),'source_bytes':len(text.encode())}
        try:
            expected_seq=e.segment.encode(text,vocab,a['policy'])
        except ValueError:
            row['encodable']=False
            assert not (packet_dir/f'{pid}.bin').exists(),'packet exists for uncovered source'
        else:
            packet=(packet_dir/f'{pid}.bin').read_bytes()
            assert packet[4]==8 and e.analyze.decode(dictionary,packet)==text
            # At eight bits each actual payload byte is exactly one selected ID.
            sequence=list(packet[41:])
            assert sequence==expected_seq,'stored packet violates named encoding policy'
            assert packet==e.analyze.encode(vocab,sequence,8)
            if a['policy']=='canonical':assert sequence==e.analyze.shortest_encode(text,vocab)
            row.update(encodable=True,selections=len(sequence),actions=len(sequence)+1,
                       single_characters=sum(len(vocab[i])==1 for i in sequence),
                       packet_bytes=len(packet),packet_sha256=e.analyze.sha(packet),
                       one_program_package_bytes=len(dictionary)+len(packet))
        key=(pid,row['source_sha256'])
        q=known[key] if key in known else fresh[f'{pid}:{key[1]}']
        assert a['qualification'][pid]==q,'qualification differs from hash-bound receipt'
        row['qualified_source']=q['passed']
        assert a['per_problem'][pid]==row,'stored per-program cost/qualification mismatch'
        replay[pid]=row
    for split,partition in (('fit','dev_fit'),('validation','dev_val')):
        group=c['partition'][partition]
        expected=e.tail.aggregate(replay,group,len(dictionary))
        good=[replay[str(pid)] for pid in group if replay[str(pid)]['encodable']]
        expected.update(single_character_codes=sum(row['single_characters'] for row in good),
                        source_bytes=sum(replay[str(pid)]['source_bytes'] for pid in group),
                        framing_bytes=41*len(good),padding_bits=0,
                        payload_bits=8*sum(row['selections'] for row in good),
                        package_with_decoder_dependencies=expected['package_bytes']+c['decoder_dependency_bytes'],
                        qualified=sum(replay[str(pid)]['encodable'] and replay[str(pid)]['qualified_source'] for pid in group))
        assert a[split]==expected,'stored aggregate cost/qualification mismatch'
    return replay


def qualification_authority(folder,c,e):
    known={}
    for label,rel,armname in (('item13_R','binding-descent-v1/evidence/results.json','control'),
                              ('item15_seed','lns-naming-v1/evidence/results.json','seed_fixed_seed')):
        payload=(e.LIT/rel).read_bytes()
        assert e.analyze.sha(payload)==c['code_hashes'][rel]
        candidates=json.loads(payload)['arms']
        source=next(a for a in candidates if a['arm']==armname and (armname!='control' or a['width']==8))
        for pid,row in source['per_problem'].items():
            assert source['qualification'][pid]['passed']
            known[pid,row['source_sha256']]={'passed':True,'reused':True,'receipt_source':label}
    path=folder/'qualification-private.json'
    data=json.loads(path.read_text())  # initialized even when no new source needs execution
    fresh,failures=data['receipts'],data['failures']
    assert set(failures)<=set(fresh)
    for key,q in fresh.items():
        assert q['reused'] is False and 0<=q['checks_passed']<=q['cases']
        assert q['passed']==(q['checks_passed']==q['cases'] and not failures.get(key))
    return known,fresh,failures


def verify_reference_inputs(name, sources_raw, vocab_raw, c, work=None):
    """Pin original bytes, then compare exact source values and ordered entries.

    The optional no-work path preserves the existing synthetic replay API: it
    accepts only artifacts whose serialization itself matches the pinned hash.
    Production main always supplies the original work root.
    """
    reference_name = 'seed13' if name == 'best24' else name
    source_rel = c['references'][reference_name]+'/sources.json'
    vocab_rel = c['references'][name]+'/dictionary.json'
    originals = []
    for rel, artifact in ((source_rel, sources_raw), (vocab_rel, vocab_raw)):
        original = (Path(work)/rel).read_bytes() if work is not None else artifact
        assert hashlib.sha256(original).hexdigest() == c['private_files'][rel], rel
        originals.append(json.loads(original))
    sources, vocab = json.loads(sources_raw), json.loads(vocab_raw)
    assert isinstance(sources, dict) and all(type(pid) is str and type(text) is str for pid, text in sources.items())
    assert isinstance(vocab, list) and all(type(word) is str for word in vocab)
    assert sources == originals[0], 'reference source values differ from pinned original'
    assert vocab == originals[1], 'reference vocabulary order or values differ from pinned original'


def verify_run_artifacts(folder,raw,c,e,work=None):
    assert not (folder/'failure.json').exists(),'incomplete run cannot be promoted'
    assert json.loads((folder/'status.json').read_text())['complete']
    assert json.loads((folder/'supervisor-receipt.json').read_text())['complete']
    for rel,digest in c['code_hashes'].items():assert e.analyze.sha((e.LIT/rel).read_bytes())==digest,rel
    decoder_files=('literals.py','pass2/working/bitpack.py')
    assert c['decoder_dependency_bytes']==sum((e.LIT/rel).stat().st_size for rel in decoder_files)>0
    assert all(rel in c['code_hashes'] for rel in decoder_files)
    expected={(name,policy) for name in ('R','seed13','best24',*CANDIDATES) for policy in POLICIES}
    assert len(raw['arms'])==len(expected) and {(a['arm'],a['policy']) for a in raw['arms']}==expected
    known,fresh,failures=qualification_authority(folder,c,e)
    allfit=json.loads((folder/'all-fit-sealed.json').read_text());assert allfit['validation_loaded'] is False
    validations=json.loads((folder/'all-validation-sealed.json').read_text());assert validations['qualification_started'] is False
    assert allfit['arms']==raw['fit_summaries'] and allfit['repairs']==raw['repair_summaries']
    fit_receipts={x['arm']:x['fit_seal_sha256'] for x in raw['fit_summaries']}
    for name in CANDIDATES:
        root=folder/'fit'/name;seal_raw=(root/'fit-seal.json').read_bytes()
        assert e.analyze.sha(seal_raw)==fit_receipts[name]
        seal=json.loads(seal_raw);assert seal['validation_loaded'] is False
        for filename,digest in seal['files'].items():assert e.analyze.sha((root/filename).read_bytes())==digest
    used_fresh=set()
    for a in raw['arms']:
        base=folder/'artifacts'/a['arm'];sources=json.loads((base/'sources.json').read_text())
        vocab_raw=(base/'dictionary.json').read_bytes();vocab=json.loads(vocab_raw)
        assert e.analyze.sha(vocab_raw)==a['dictionary_sha256']
        dictionary=(base/'dictionary.bin').read_bytes()
        banned=e.base.sel.forbidden_strings(sources)
        if a['arm'] in CANDIDATES:
            fitroot=folder/'fit'/a['arm'];source_arm=a['arm'] if a['arm'] in e.SOURCE_ARMS else 'NCP';valroot=folder/'fit'/source_arm
            assert vocab==json.loads((fitroot/'dictionary.json').read_text())
            fit=json.loads((fitroot/'fit-sources.json').read_text());validation=json.loads((valroot/'validation-sources.json').read_text())
            assert sources=={**fit,**validation}
            valseal=json.loads((valroot/'validation-seal.json').read_text())
            assert valseal['qualification_started'] is False and valseal['source_sha256']==e.digest(validation)
            assert valseal['dictionary_sha256']==e.analyze.sha((valroot/'dictionary.json').read_bytes())
            assert set(valseal['files'])=={'validation-sources.json','validation-variants.json','all-banned.json'}
            for filename,digest in valseal['files'].items():assert e.analyze.sha((valroot/filename).read_bytes())==digest
            fit_banned=set(json.loads((fitroot/'fit-banned.json').read_text()))
            val_banned=set(json.loads((valroot/'all-banned.json').read_text()))
            # Check available retained alternatives, and bind the cumulative bans
            # from earlier unselected variants to the recorded fit/validation seals.
            for variants_file,ban in ((fitroot/'fit-variants.json',fit_banned),(valroot/'validation-variants.json',val_banned)):
                if variants_file.exists():assert e.forbidden(json.loads(variants_file.read_text()))<=ban
            assert e.base.sel.forbidden_strings(fit)<=fit_banned
            assert e.base.sel.forbidden_strings(validation)<=val_banned
            banned|=fit_banned|val_banned
        else:
            # measure() reserializes JSON. Original bytes remain hash-pinned;
            # dictionary order and every source string must still match exactly.
            verify_reference_inputs(a['arm'], (base/'sources.json').read_bytes(), vocab_raw, c, work)
        replay_arm(a,sources,vocab,dictionary,base/a['policy'],banned,c,e,known,fresh)
        for pid,row in a['per_problem'].items():
            if (pid,row['source_sha256']) not in known:used_fresh.add(f'{pid}:{row["source_sha256"]}')
    assert used_fresh==set(fresh),'extra or missing fresh qualification receipts'
    summary={'distinct_new_sources':len(fresh),'passed':sum(q['passed'] for q in fresh.values()),
             'checks_passed':sum(q['checks_passed'] for q in fresh.values()),'checks':sum(q['cases'] for q in fresh.values()),
             'failed_sources':len(failures)}
    assert raw['fresh_qualification_summary']==summary
    assert raw['decoded_packets']==sum(a['fit']['covered']+a['validation']['covered'] for a in raw['arms'])
    return summary


def display_cost_row(a):
    d=a['validation'];q=d['selections'] or {};actions=d['actions'] or {}
    quantiles='/'.join(str(q.get(k,'unavailable')) for k in ('median','p90','p95'))
    frac=d['single_character_fraction'];fracstr='unavailable' if frac is None else f'{100*frac:.4f}%'
    return (f"| {a['arm']} | {a['policy']} | {a['fit']['qualified']}/300; {d['qualified']}/100 | "
            f"{actions.get('total','unavailable')} | {quantiles} | {d['single_character_codes']}/{fracstr} | {d['package_bytes']} | {a['successor']} |")

def main(folder, work=None):
    c = json.loads((HERE/'contract.json').read_text())
    raw = json.loads((folder/'results.json').read_text())
    assert raw['contract_sha256'] == hashlib.sha256((HERE/'contract.json').read_bytes()).hexdigest()
    # Independent replay verifies encoding policy, full costs and qualification.
    import engine as e
    verify_run_artifacts(folder,raw,c,e,folder.parents[1] if work is None else work)
    for name, pinned in c['reference_validation'].items():
        actual = next(a for a in raw['arms'] if a['arm'] == name and a['policy'] == 'canonical')['validation']
        for key, value in pinned.items():
            if key == 'actions':
                assert actual['actions']['total'] == value
            elif key == 'selections':
                assert actual['selections']['total'] == value
            else:
                assert actual[key] == value
    # S1 includes both fit and validation reference counts, not only the
    # validation headline pinned in the convenience contract table.
    reference_specs=(('R','binding-descent-v1/evidence/results.json','control'),
                     ('seed13','binding-descent-v1/evidence/results.json','scope_joint'),
                     ('best24','character-slots-v1/evidence/results.json','optional'))
    for name,rel,old_name in reference_specs:
        payload=(e.LIT/rel).read_bytes();assert e.analyze.sha(payload)==c['code_hashes'][rel]
        old=next(a for a in json.loads(payload)['arms'] if a['arm']==old_name and (old_name=='optional' or a['width']==8))
        new=next(a for a in raw['arms'] if a['arm']==name and a['policy']=='canonical')
        assert new['entries']==old['entries'] and new['dictionary_bytes']==old['dictionary_bytes']
        for split in ('fit','validation'):
            for key in ('selections','actions','single_character_fraction','package_bytes'):
                assert new[split][key]==old[split][key],(name,split,key)
    result = build(raw, c)
    result['private_results_sha256'] = e.analyze.sha((folder/'results.json').read_bytes())
    result['decoder_dependency_bytes'] = c['decoder_dependency_bytes']
    result['offline_encoder_bytes'] = c['offline_encoder_bytes']
    result['offline_encoder_scope'] = c['offline_encoder_scope']
    for a in result['arms']:
        for row in a['per_problem'].values():
            row['one_program_package_with_decoder_dependencies']=(row['one_program_package_bytes']+c['decoder_dependency_bytes']) if row['encodable'] else None
    # Search summaries contain numeric metadata only. Full name/proposal traces
    # and case failure payloads are stored privately and never copied here.
    evidence = HERE/'evidence'
    evidence.mkdir(exist_ok=True)
    e.analyze.write(evidence/'results.json', result)
    lines = ['# Stacking source and dictionary components', '',
             '[Freeze](FREEZE.md); [review](REVIEW.md); [metadata evidence](evidence/results.json).', '',
             f"Selected new flat successor: **{result['selected_successor'] or 'none'}**. " +
             ('The previously selected item24 optional dictionary remains the default.' if not result['selected_successor'] else
              'Selection uses the frozen matched minimum-selection/minimum-character policy.'), '',
             'Consumed-development offline representation evidence only; no M1 qualification, independent confirmation or autonomous assembly.', '',
             '| Arm | Encoder | Fit/validation qualified | Actions | Selection median/p90/p95 | Character codes/fraction | Raw package | Successor |',
             '| --- | --- | --- | ---: | --- | --- | ---: | --- |']
    for a in result['arms']:
        lines.append(display_cost_row(a))
    lines += ['', 'All eight outputs start from item13 for attribution; current-best24 is retained as a separately replayed matched reference.',
              'Source-factor controls precede two shared repair trajectories and weighted finishing forks. Deep arms use identical NCP source bytes.', '',
              '| Arm/encoder | Better/same/worse vs24 | Failed predicates |', '| --- | --- | --- |']
    for a in result['arms']:
        if a['arm'] in CANDIDATES:
            counts = '/'.join(str(a['paired']['best24'][k]) for k in ('better','same','worse'))
            lines.append(f"| {a['arm']}/{a['policy']} | {counts} | {', '.join(a['failed_predicates']) or 'none'} |")
    lines += ['', 'Canonical and minN/minC comparisons always use the same policy for both sides. Historical results and packets remain unchanged.',
              'All selected bytes, one Finish, dictionary,41-byte framing and padding are charged. Decoder-source and offline tooling costs are separate; complete installed runtime storage is unmeasured.',
              'Every coverage or qualification failure remains in its denominator; no retry, source replacement or hidden escape. Structured2c sidecars were not executed.', '',
              f"Fresh qualification: {result['fresh_qualification_summary']}. Measured wall time: {result['seconds']:.2f} seconds.", '',
              'Item25 bounds remain restricted to its fixed sources and declared pools. No universal impossibility, threshold change, protected opening, training, source publication or deployment follows.', '',
              '| Prediction | Met |', '| --- | --- |']
    lines += [f'| {k} | {v} |' for k,v in result['predictions'].items()]
    lines += ['', 'Component intent preserved; flat codec and production boundaries unchanged.', '',
              'Rebuild: `python -B projects/algorithm_solver/literals/stacking-v1/report.py --run /private/stacking/run-v1`.']
    (HERE/'README.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--work', type=Path, help='Original pinned input root; defaults to run directory parents[1]')
    args = parser.parse_args()
    main(args.run, args.work)
