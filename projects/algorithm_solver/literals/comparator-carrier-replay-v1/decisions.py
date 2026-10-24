"""Frozen54 pure predicates restated with an explicit historical comparator."""

from adapter import exact

POLICIES=("canonical","shortest_min_char")

ANCHORS=("24","43N","43W")

def complete(arm,config):
    return all(arm[split]['covered']==arm[split]['qualified']==len(config['partition'][key]) for split,key in (('fit','dev_fit'),('validation','dev_val')))

def gates(a,b,config,initial=False):
    ids=list(map(str,config['partition']['dev_val']));coverage=all(complete(x,config) for x in (a,b));clean=all(x['entries']<=256 and not x['illegal_entry_sha256'] for x in (a,b))
    better=sum(a['per_problem'][pid]['encodable'] and (not b['per_problem'][pid]['encodable'] or a['per_problem'][pid]['actions']<b['per_problem'][pid]['actions']) for pid in ids)
    worse=sum(b['per_problem'][pid]['encodable'] and (not a['per_problem'][pid]['encodable'] or a['per_problem'][pid]['actions']>b['per_problem'][pid]['actions']) for pid in ids)
    checks={'coverage_and_qualification':coverage,'legal_dictionary':clean}
    if not coverage:checks.update({key:False for key in ('actions','median','p90','breadth','fraction','package')})
    else:
        x,y=a['validation'],b['validation'];ax,by=x['actions'],y['actions'];xn=x['selections']['total'];yn=y['selections']['total'];xc=x['single_character_codes'];yc=y['single_character_codes']
        checks.update(actions=100*ax['total']<=95*by['total'] if initial else ax['total']<by['total'],
          median=ax['median']<by['median'] if initial else ax['median']<=by['median'],p90=ax['p90']<by['p90'] if initial else ax['p90']<=by['p90'],
          breadth=worse<=25 and (not initial or better>=60),fraction=xc*yn<=yc*xn,package=100*x['package_bytes']<=105*y['package_bytes'])
    return {'checks':checks,'passed':all(checks.values()),'paired':{'better':better,'same':len(ids)-better-worse,'worse':worse}}

def transfer(a,b,config):
    coverage=complete(a,config) and complete(b,config);clean=all(x['entries']<=256 and not x['illegal_entry_sha256'] for x in (a,b))
    assert a['dictionary_binary_sha256']==b['dictionary_binary_sha256']
    checks={'coverage_and_qualification':coverage,'legal_fixed_dictionary':clean}
    if not coverage:checks.update({key:False for key in ('actions','median','p90','strict_fraction','package')})
    else:
        x,y=a['validation'],b['validation'];ax,by=x['actions'],y['actions']
        checks.update(actions=ax['total']<=by['total'],median=ax['median']<=by['median'],p90=ax['p90']<=by['p90'],
          strict_fraction=x['single_character_codes']*y['selections']['total']<y['single_character_codes']*x['selections']['total'],
          package=x['package_bytes']<=y['package_bytes'])
    return {'checks':checks,'passed':all(checks.values()),'scope':'Consumed validation predicates; full fit+validation coverage/qualification and legality prerequisites.',
      'paired_diagnostics':{split:paired_delta(a,b,config['partition'][key],split) for split,key in [('fit','dev_fit'),('validation','dev_val')]}}

def paired_delta(a,b,ids,split):
    rowsa=a['per_problem'];rowsb=b['per_problem'];ids=list(map(str,ids))
    better=sum(rowsa[i]['encodable'] and (not rowsb[i]['encodable'] or rowsa[i]['actions']<rowsb[i]['actions']) for i in ids)
    worse=sum(rowsb[i]['encodable'] and (not rowsa[i]['encodable'] or rowsa[i]['actions']>rowsb[i]['actions']) for i in ids)
    full=all(rowsa[i]['encodable'] and rowsb[i]['encodable'] for i in ids);x=a[split];y=b[split]
    return {'better':better,'same':len(ids)-better-worse,'worse':worse,'full_pair_coverage':full,
      'actions_delta':x['actions']['total']-y['actions']['total'] if full else None,
      'selections_delta':x['selections']['total']-y['selections']['total'] if full else None,
      'character_codes_delta':x['single_character_codes']-y['single_character_codes'] if full else None,
      'character_fraction_delta':x['single_character_fraction']-y['single_character_fraction'] if full else None,
      'raw_package_delta':x['package_bytes']-y['package_bytes'] if full else None,
      'decoder_inclusive_package_delta':x['package_with_decoder_dependencies']-y['package_with_decoder_dependencies'] if full else None,
      'source_bytes_delta':x['source_bytes']-y['source_bytes']}

def decisions(arms,references,config,best,bestmeta,aggregate):
    index={(a['arm'],a['policy']):a for a in arms};assert best is not None and bestmeta['resolved'] is True
    verdicts={}
    for anchor in ANCHORS:
        perpolicy={}
        for policy in POLICIES:
            candidate=index[anchor+'-S',policy];untouched=index[anchor+'-U',policy]
            comparison={name:gates(candidate,references[name,policy],config,initial=name=='R') for name in ('R','seed13','best24','N','NCP')}
            comparison['record_time_best']=None if best is None else gates(candidate,best[policy],config)
            transferred=transfer(candidate,untouched,config)
            ready=best is not None and transferred['passed'] and all(v['passed'] for v in comparison.values())
            perpolicy[policy]={'transfer':transferred,'comparisons':comparison,'successor':ready}
        verdicts[anchor+'-S']={'policies':perpolicy,'transfer':all(x['transfer']['passed'] for x in perpolicy.values()),
          'successor':all(x['successor'] for x in perpolicy.values()),'replacement_status':'resolved' if best is not None else 'unresolved'}
    passing=[label for label,v in verdicts.items() if v['successor']]
    passing.sort(key=lambda label:(index[label,'canonical']['validation']['actions']['total'],
      index[label,'canonical']['validation']['package_with_decoder_dependencies'],label))
    predictions={'P1':all(complete(a,config) and not a['illegal_entry_sha256'] for a in arms),
      'P2':any(all(complete(index[anchor+'-S',policy],config) and complete(index[anchor+'-U',policy],config)
          and index[anchor+'-S',policy]['validation']['actions']['total']==index[anchor+'-U',policy]['validation']['actions']['total']
          and transfer(index[anchor+'-S',policy],index[anchor+'-U',policy],config)['checks']['strict_fraction'] for policy in POLICIES) for anchor in ANCHORS),
      'P3':any(verdicts[a+'-S']['transfer'] for a in ('43N','43W')),'P4':not passing if best is not None else None}
    gaps={}
    for arm in arms:
        rows=arm['per_problem'];overall=aggregate(rows,[*config['partition']['dev_fit'],*config['partition']['dev_val']],arm['dictionary_bytes'],config['decoder_dependency_bytes'])
        covered=overall['coverage_complete'];selections=overall['selections']
        gaps[arm['arm']+'/'+arm['policy']]={'admission_400_of_500':False,'admission_scope':'400 reused development sources; population admission/500 and independent confirmation unestablished.',
          'entries_at_most_256':arm['entries']<=256,'median_selections_at_most_32':covered and selections['median']<=32,
          'p95_selections_at_most_96':covered and selections['p95']<=96,'character_fraction_at_most_10_percent':covered and 10*overall['single_character_codes']<=selections['total'],
          'zero_whole_body_entries':not arm['illegal_entry_sha256'],'aggregate_400':overall,'M1_qualified':False}
    return {'verdicts':verdicts,'record_time_best':bestmeta,'ranked_passing_candidates':passing,
      'selected_successor':passing[0] if passing else None,'predictions':predictions,'M1_gaps':gaps}
