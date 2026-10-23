"""Replay sealed packets and report separate 2c comparisons; no fit or case run."""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Assertion validation requires normal Python mode; PYTHONOPTIMIZE/-O is forbidden')

import argparse
import copy
import json
from pathlib import Path
import codec
import run

HERE=Path(__file__).resolve().parent
NAMES=('literal','prefix','template','union','D11')


def paired(a,b,ids):
    answer={'better':0,'same':0,'worse':0}
    for pid in map(str,ids):
        x,y=a['per_problem'][pid],b['per_problem'][pid]
        label=('same' if not x['encodable'] and not y['encodable'] else 'worse' if not x['encodable'] else 'better' if not y['encodable'] else
               'better' if x['actions']<y['actions'] else 'worse' if x['actions']>y['actions'] else 'same')
        answer[label]+=1
    return answer


def checks(a,b,ids,initial=False):
    x,y=a['validation'],b['validation']
    coverage=all(row['fit']['covered']==row['fit']['qualified']==300 and
                 row['validation']['covered']==row['validation']['qualified']==100 for row in (a,b))
    legal=all(row['entries']<=256 and not row['illegal_entry_sha256'] for row in (a,b))
    answer={'coverage_and_qualification':coverage,'legal_dictionary':legal}
    if not coverage:
        answer.update({k:False for k in ('actions','median','p90','breadth','fraction','package')})
        return answer
    relation=paired(a,b,ids)
    answer.update(actions=x['actions']['total']<=.95*y['actions']['total'] if initial else x['actions']['total']<y['actions']['total'],
                  median=x['actions']['median']<y['actions']['median'] if initial else x['actions']['median']<=y['actions']['median'],
                  p90=x['actions']['p90']<y['actions']['p90'] if initial else x['actions']['p90']<=y['actions']['p90'],
                  breadth=relation['worse']<=25 and (not initial or relation['better']>=60),
                  fraction=x['single_character_fraction']<=y['single_character_fraction'],
                  package=x['package_bytes']<=1.05*y['package_bytes'])
    return answer


def subset_costs(arm,ids):
    """Packets belong to the selected IDs; dictionary/decoder remain global."""
    rows=[arm['per_problem'][pid] for pid in ids]
    covered=[row for row in rows if row['encodable']]
    complete=len(covered)==len(rows)
    n=sum(row['selections'] for row in covered) if complete else None
    chars=sum(row['single_characters'] for row in covered) if complete else None
    actions=sum(row['actions'] for row in covered) if complete else None
    packets=41*len(rows)+n if complete else None
    dictionary=arm['dictionary_bytes']
    decoder=arm['decoder_dependency_bytes']
    return {'count':len(rows),'covered':len(covered),
            'qualified':sum(row['qualified_source'] for row in covered),
            'failed_ids':[pid for pid in ids if not arm['per_problem'][pid]['encodable']],
            'complete_cost_available':complete,'actions':actions,'selections':n,
            'single_character_codes':chars,'single_character_fraction':chars/n if n else None,
            'actions_per_program':actions/len(rows) if complete and rows else None,
            'selections_per_program':n/len(rows) if complete and rows else None,
            'attributed_packet_bytes':packets,'attributed_framing_bytes':41*len(rows) if complete else None,
            'attributed_payload_bits':8*n if complete else None,
            'global_dictionary_bytes':dictionary,'global_decoder_dependency_bytes':decoder,
            'full_dictionary_plus_subset_packets_bytes':dictionary+packets if complete else None,
            'full_dictionary_and_decoder_plus_subset_packets_bytes':dictionary+decoder+packets if complete else None}


def conditional_subsets(candidate,arms,ids):
    ordered=sorted(map(str,ids),key=int)
    rows=candidate['per_problem']
    predicates={
        'common_pool_eligible':lambda r:r['eligible'],
        'arm_pool_eligible':lambda r:r['arm_eligible'],
        'P_used':lambda r:r['encodable'] and r['prefix_codes']>0,
        'I_used':lambda r:r['encodable'] and r['identifier_codes']>0,
        'either_used':lambda r:r['encodable'] and r['prefix_codes']+r['identifier_codes']>0,
        'both_used':lambda r:r['encodable'] and r['prefix_codes']>0 and r['identifier_codes']>0}
    answer={}
    for label,predicate in predicates.items():
        selected=[pid for pid in ordered if predicate(rows[pid])]
        own=subset_costs(candidate,selected)
        references={name:subset_costs(arms[name],selected) for name in ('literal','D11')}
        comparisons={}
        for name,ref in references.items():
            complete=own['complete_cost_available'] and ref['complete_cost_available']
            comparisons[name]={'paired':paired(candidate,arms[name],selected),
                              'complete_paired_cost_available':complete,
                              'candidate_minus_reference':{
                                  field:own[field]-ref[field] if complete else None
                                  for field in ('actions','selections','single_character_codes','attributed_packet_bytes',
                                                'full_dictionary_plus_subset_packets_bytes',
                                                'full_dictionary_and_decoder_plus_subset_packets_bytes')},
                              'fraction_difference':own['single_character_fraction']-ref['single_character_fraction']
                                  if own['single_character_fraction'] is not None and ref['single_character_fraction'] is not None else None}
        answer[label]={'ids':selected,'count':len(selected),'candidate':own,
                       'references':references,'paired_costs':comparisons}
    return {'descriptive_only':True,'promotion_allowed':False,'selection_arm':candidate['arm'],
            'selection_population':'consumed_validation','overlapping_subsets_not_additive':True,
            'package_attribution':'Only packet bytes are assigned to IDs. Dictionary and decoder are global, fully charged without subset discount; overlapping subset packages must not be summed.',
            'subsets':answer}


def build(result,c):
    result=copy.deepcopy(result)
    arms={a['arm']:a for a in result['arms']}
    ids=c['partition']['dev_val']
    for name,a in arms.items():
        a['paired']={ref:paired(a,arms[ref],ids) for ref in NAMES}
        a['conditional_subsets']=conditional_subsets(a,arms,ids)
        a['structured_readiness_checks']=checks(a,arms['literal'],ids,True)
        a['incremental_checks']={ref:checks(a,arms[ref],ids) for ref in ('D11','prefix','template')}
        a['structured_ready']=(name in ('prefix','template','union') and
            all(a['structured_readiness_checks'].values()) and all(a['incremental_checks']['D11'].values()))
    union=arms['union']
    union['stacking_ready']=union['structured_ready'] and all(
        all(union['incremental_checks'][ref].values()) for ref in ('prefix','template'))
    result.update(flat_M1_promotion_allowed=False,representation='separate_structured_2c',
                  selected_structured_candidate='union' if union['stacking_ready'] else None,
                  default_unchanged=True)
    complete=lambda name: all(arms[name][split]['covered']==arms[name][split]['qualified']==count
                             for split,count in (('fit',300),('validation',100)))
    fewer=lambda name,ref: complete(name) and complete(ref) and arms[name]['validation']['actions']['total']<arms[ref]['validation']['actions']['total']
    observations={
        'S1_all_2000_views_decode_and_qualify':all(complete(name) for name in NAMES),
        'S2_prefix_fewer_actions_than_matched_literal':fewer('prefix','literal'),
        'S3_template_fewer_actions_than_matched_literal':fewer('template','literal'),
        'S4_union_fewer_actions_than_both_single_kinds':fewer('union','prefix') and fewer('union','template'),
        'S5_union_does_not_pass_full_stacking_rule':not union['stacking_ready'],
        'S6_prefix_fewer_actions_than_untouched_D11':fewer('prefix','D11'),
        'S7_template_fewer_actions_than_untouched_D11':fewer('template','D11')}
    descriptions={
        'S1':'All 2000 program views decode and qualify.',
        'S2':'Prefix uses fewer validation actions than searched literal.',
        'S3':'Template uses fewer validation actions than searched literal.',
        'S4':'Union uses fewer validation actions than both individual kinds.',
        'S5':'Union does not pass the full stacking rule.',
        'S6':'Prefix uses fewer validation actions than untouched D11.',
        'S7':'Template uses fewer validation actions than untouched D11.'}
    result['predictions']={key:{'expected':True,'observed':value,'correct':value is True}
                           for key,value in observations.items()}
    for key,prediction in result['predictions'].items():
        prediction['statement']=descriptions[key.split('_',1)[0]]
    return result


def replay(folder,a,c,pools):
    keys=run.read(folder/'dictionary.json')
    texts=run.read(folder/'sources.json')
    plans=run.read(folder/'plans.json')
    expected={str(i) for group in c['partition'].values() for i in group}
    assert set(texts)==set(a['per_problem'])==expected
    nodes=codec.extract(texts)
    typed=a['arm'] in ('prefix','template','union')
    assert keys==codec.order(keys) and len(keys)==len(set(keys))<=256
    assert all(key[0] in {'L'}|run.ARMS.get(a['arm'],set()) for key in keys)
    assert a['entries']==len(keys)
    assert a['prefix_entries']==sum(k[0]=='P' for k in keys)
    assert a['identifier_entries']==sum(k[0]=='I' for k in keys)
    kind='typed' if typed else 'literal'
    assert a['decoder_dependency_bytes']==c['decoder_bytes'][kind]
    assert a['representation']==('structured_2c' if typed else 'flat_literal')
    assert a['encoder']=='canonical_minN_then_IDs'
    db=codec.dictionary(keys) if typed else codec.literal_dictionary(keys)
    assert db==(folder/'dictionary.bin').read_bytes()
    assert a['dictionary_sha256']==run.analyze.sha(db)
    assert a['dictionary_bytes']==len(db)
    banned={body for group in nodes.values() for body in group['bodies']}
    eligibility={key for values in pools.values() for key in values}
    arm_eligibility={key for key in eligibility if key[0] in run.ARMS.get(a['arm'],set())}
    assert a['illegal_entry_sha256']==sorted(run.analyze.sha(k[1:].encode()) for k in keys if k[0]=='L' and k[1:] in banned)
    decoded={}
    for pid,text in texts.items():
        row=a['per_problem'][pid]
        for field,allowed in (('eligible',eligibility),('arm_eligible',arm_eligibility)):
            assert row[field]==any(n['key'] in allowed for family in ('prefix','identifier') for n in nodes[pid][family])
        assert row['source_sha256']==run.analyze.sha(text.encode())==c['source_qualification'][pid]['source_sha256']
        assert c['source_qualification'][pid]['passed'] and row['qualified_source'] and row['qualification_reused']
        try:plan=codec.encode_source(text,nodes[pid],keys)
        except ValueError:
            assert not row['encodable'] and pid not in plans and not (folder/'packets'/f'{pid}.bin').exists()
            continue
        assert row['encodable'] and codec.canonical(plan)==codec.canonical(plans[pid])
        packet=(folder/'packets'/f'{pid}.bin').read_bytes()
        if typed:
            assert packet==codec.packet(keys,plan['tokens'])
        else:
            assert packet==run.analyze.encode([k[1:] for k in keys],[keys.index(k) for k in plan['tokens']],8)
            decoded[pid]=run.analyze.decode(db,packet)
        for field in ('selections','single_characters','prefix_codes','identifier_codes','argument_codes',
                      'prefix_fixed_bytes','identifier_fixed_bytes','repeated_identifier_bytes','generated_bytes'):
            assert row[field]==plan[field],(pid,field)
        assert row['actions']==plan['selections']+1 and row['packet_sha256']==run.analyze.sha(packet)
        assert row['packet_bytes']==len(packet) and row['source_bytes']==len(text.encode())
    if typed and plans:
        decoded=codec.decode_many(keys,plans)
    assert set(decoded)==set(plans)
    for pid,actual in decoded.items():
        digest=run.analyze.sha(actual.encode())
        assert actual==texts[pid] and digest==c['source_qualification'][pid]['source_sha256']
        assert a['per_problem'][pid]['decoded_source_sha256']==digest
    for split,group in (('fit','dev_fit'),('validation','dev_val')):
        assert a[split]==run.aggregate(a['per_problem'],c['partition'][group],db,a['decoder_dependency_bytes'])
    used={key for pid in map(str,c['partition']['dev_val']) for key in plans.get(pid,{}).get('tokens',[])}
    a['validation_entry_usage']={'distinct_prefix_entries_used':sum(key[0]=='P' for key in used),
                                'distinct_identifier_entries_used':sum(key[0]=='I' for key in used)}


def main(folder):
    c=run.read(HERE/'contract.json')
    receipt=run.read(folder/'supervisor-receipt.json') if (folder/'supervisor-receipt.json').exists() else None
    if not receipt or not receipt['complete'] or receipt['outer_timeout'] or not receipt['promotion_allowed'] or not (folder/'results.json').exists():
        failure={'status':'incomplete','verdict_available':False,'flat_M1_promotion_allowed':False,
                 'selected_structured_candidate':None,'supervisor_receipt':receipt,
                 'results_present':(folder/'results.json').exists(),
                 'reason':'A complete supervised run and complete results are required; retained partial artifacts carry no verdict.'}
        run.analyze.write(folder/'report.json',failure)
        (folder/'REPORT.md').write_text('# Structured stacking incomplete\n\nNo verdict or promotion is available. See report.json and the retained supervisor receipt and partial artifacts.\n')
        return failure
    result=run.read(folder/'results.json')
    assert result['contract_sha256']==run.analyze.sha((HERE/'contract.json').read_bytes())
    assert c['source_bound'] and result['source_qualification_reused'] and result['fresh_case_executions']==0
    assert result['source_receipt_sha256']==c['private_files']['results.json']
    assert len(result['arms'])==len(NAMES) and {a['arm'] for a in result['arms']}==set(NAMES)
    for rel,digest in c['code_hashes'].items():
        assert run.analyze.sha((HERE.parent/rel).read_bytes())==digest,rel
    for path,digest in c['runtime_files'].items():
        assert run.analyze.sha(Path(path).read_bytes())==digest,path
    for kind,paths in c['decoder_dependencies'].items():
        assert c['decoder_bytes'][kind]==sum(Path(path).stat().st_size for path in paths)
    source_root=Path(c['source_run'])
    for rel,digest in c['private_files'].items():
        assert run.analyze.sha((source_root/rel).read_bytes())==digest,rel
    original=run.read(source_root/'results.json')
    parent=c['parent_evidence']
    assert parent['private_results_sha256']==c['private_files']['results.json']
    assert parent['contract_sha256']==original['contract_sha256']==run.analyze.sha((HERE.parent/'stacking-v1/contract.json').read_bytes())
    public_path=HERE.parent/parent['relative_path']
    assert parent['sha256']==run.analyze.sha(public_path.read_bytes())
    public=run.read(public_path)
    assert public['private_results_sha256']==parent['private_results_sha256'] and public['contract_sha256']==parent['contract_sha256']
    assert public['predictions']['S1_references_and_all_packets_replay'] is True
    original_d11=next(a for a in original['arms'] if a['arm']=='D11' and a['policy']=='canonical')
    for pid,q in c['source_qualification'].items():
        assert q['passed'] and q['source_sha256']==original_d11['per_problem'][pid]['source_sha256']
        assert original_d11['per_problem'][pid]['qualified_source'] and original_d11['per_problem'][pid]['encodable']
        assert q['receipt']==original_d11['qualification'][pid] and q['receipt']['passed']
    original_sources=run.read(source_root/'artifacts/D11/sources.json')
    fit_sources=run.read(source_root/'fit/D11/fit-sources.json')
    assert set(fit_sources)=={str(i) for i in c['partition']['dev_fit']}
    assert fit_sources=={pid:original_sources[pid] for pid in fit_sources}
    initial=codec.order(codec.literal(word) for word in run.read(source_root/'artifacts/D11/dictionary.json'))
    assert initial==run.read(folder/'D11-reference/dictionary.json')
    fit_seal=run.read(folder/'all-fit-sealed.json')
    assert fit_seal['validation_loaded'] is False
    assert len(fit_seal['arms'])==4 and {a['arm'] for a in fit_seal['arms']}==set(run.ARMS)
    assert len({a['pool_sha256'] for a in fit_seal['arms']})==1
    validation_seal=run.read(folder/'all-validation-sealed.json')
    assert validation_seal['all_fit_seal_sha256']==run.analyze.sha((folder/'all-fit-sealed.json').read_bytes())
    assert validation_seal['source_file_sha256']==c['private_files']['artifacts/D11/sources.json']
    assert set(validation_seal['arms'])==set(NAMES)
    for arm in result['arms']:
        root=folder/('D11-reference' if arm['arm']=='D11' else arm['arm'])
        assert run.read(root/'sources.json')==original_sources
        assert run.read(root/'results.json')==arm
        assert validation_seal['arms'][arm['arm']]=={'results_sha256':run.analyze.sha((root/'results.json').read_bytes()),
                                                     'dictionary_sha256':arm['dictionary_sha256']}
        if arm['arm'] in run.ARMS:
            summary=next(a for a in fit_seal['arms'] if a['arm']==arm['arm'])
            assert summary==run.read(root/'fit-summary.json')==arm['fit_search']
            assert summary['fit_seal_sha256']==run.analyze.sha((root/'fit-seal.json').read_bytes())
            seal=run.read(root/'fit-seal.json')
            assert seal['validation_loaded'] is False and seal['source_fit_sha256']==c['private_files']['fit/D11/fit-sources.json']
            assert seal['initial_dictionary_sha256']==c['private_files']['artifacts/D11/dictionary.json']
            assert summary['pool_sha256']==run.analyze.sha((root/'pool.json').read_bytes())
            for name,digest in seal['files'].items():
                assert run.analyze.sha((root/name).read_bytes())==digest,(arm['arm'],name)
            plans=run.read(root/'plans.json')
            fit_plans=run.read(root/'fit-plans.json')
            assert fit_plans=={pid:plans[pid] for pid in fit_sources}
            assert summary['fit_selections']==sum(p['selections'] for p in fit_plans.values())==arm['fit']['selections']['total']
        replay(root,arm,c,run.read(folder/'literal/pool.json')['constructors'])
    result=build(result,c)
    run.analyze.write(folder/'report.json',result)
    lines=['# Structured stacking result','','Separate 2c evidence; no flat M1 promotion.','',
           '| Arm | Validation actions | Median | p90 | C/N | Package bytes | Used programs | Distinct P/I entries used |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        v=arm['validation']
        used=arm['validation_entry_usage']
        entry_usage=f"{used['distinct_prefix_entries_used']}/{used['distinct_identifier_entries_used']}"
        if v['covered']!=100:
            lines.append(f"| {arm['arm']} | incomplete ({v['covered']}/100) | | | | | | {entry_usage} |")
        else:
            lines.append(f"| {arm['arm']} | {v['actions']['total']} | {v['actions']['median']} | {v['actions']['p90']} | {v['single_character_fraction']:.6f} | {v['package_bytes']} | {v['used_programs']} | {entry_usage} |")
    lines += ['',f"Union passes the full structured stacking rule: {result['selected_structured_candidate']=='union'}.",
              'All predicate failures, per-program coverage, pairwise changes, decoder-inclusive bytes and costs are in report.json.']
    lines += ['','| Prediction | Expected | Observed | Correct |','| --- | --- | --- | --- |']
    for name,prediction in result['predictions'].items():
        lines.append(f"| {name.split('_',1)[0]}: {prediction['statement']} | {prediction['expected']} | {prediction['observed']} | {prediction['correct']} |")
    lines += ['','Conditional subsets are descriptive and may overlap. Their exact IDs and paired costs are in report.json. '
              'Each package below retains the entire global dictionary; subsets receive no dictionary discount and must not be summed.',
              '','| Selection arm | Subset | Count | Actions | N | C | C/N | Full dictionary + subset packets |',
              '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        for name,subset in arm['conditional_subsets']['subsets'].items():
            cost=subset['candidate']
            fraction=cost['single_character_fraction']
            fraction_text='null' if fraction is None else f'{fraction:.6f}'
            lines.append(f"| {arm['arm']} | {name} | {subset['count']} | {cost['actions']} | {cost['selections']} | {cost['single_character_codes']} | {fraction_text} | {cost['full_dictionary_plus_subset_packets_bytes']} |")
    (folder/'REPORT.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--run',type=Path,required=True)
    main(p.parse_args().run)
