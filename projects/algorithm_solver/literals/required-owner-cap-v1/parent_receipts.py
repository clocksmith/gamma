"""Pure validation of inherited57 receipts; never imports57 kernels/loaders."""
import binding as b
COMMON=('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
BASE=('schema','lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')


def normalized(value):return b.parse(__import__('json').dumps(value,allow_nan=False))


def validate(value,role,expected,contract_hash,ids):
    """Hash-pinned receipt parser. Validity of full geometry/q is inherited."""
    assert role in b.ROLES
    if role=='production':
        assert set(value)=={'schema','cohort','complete','validation_loaded','contract_sha256','bindings','full_shape','proof','seconds','peak_rss_kib','phase_seconds'}
        assert value['schema']=='gamma.owner-path-cap.arm.v1' and value['cohort']==expected['cohort']
        assert value['complete'] is True and value['validation_loaded'] is False and value['contract_sha256']==contract_hash
        b.exact(value['full_shape'],expected['geometry']);assert b.digest(value['bindings'])==expected['bindings_sha256']
        b.number(value['seconds'],600);b.integer(value['peak_rss_kib'],1,8*1024**2)
        b.exact(value['seconds'],expected['production_seconds']);b.exact(value['peak_rss_kib'],expected['production_peak_rss_kib'])
        assert set(value['phase_seconds'])=={'input','proof'}
        for seconds in value['phase_seconds'].values():b.number(seconds,value['seconds'])
        assert sum(value['phase_seconds'].values())<=value['seconds']
        assert b.digest(value['phase_seconds'])==expected['production_phase_seconds_sha256']
        proof=value['proof'];assert b.digest(proof)==expected['production_proof_sha256']
        extras={'base','owner_prefix_schedule','digests','work'};direction='owner_prefix_schedule'
    else:
        proof=value;direction='owner_suffix_schedule'
        extras={'base',direction,'digests','work','shared_dependency','scalar_replay','production_forward_schedule_checked','production_forward_schedule_sha256'}
        assert proof['production_forward_schedule_checked'] is True
        assert proof['production_forward_schedule_sha256']==expected['production_prefix_schedule_sha256']
    assert set(proof)==set(COMMON)|extras and proof['schema']=='gamma.owner-path-cap.supplied.v1'
    base=proof['base'];assert set(BASE)<=set(base)
    assert base['schema']=='gamma.potential-tightening.supplied.v1'
    scientific={key:proof[key] for key in COMMON}|{'base':{key:base[key] for key in BASE}}
    assert b.digest(scientific)==expected['scientific_proof_sha256']
    assert b.digest({key:base[key] for key in BASE})==expected['baseline53_proof_sha256']
    b.exact(base['digests'],expected['baseline53_paired_digests'])
    assert b.digest(base['tightened']['top_entries'])==expected['baseline53_top_entries_sha256']
    p=base['tightened'];b.exact(p['rows'],expected['baseline53_rows'])
    assert set(p['path_numerators'])==set(ids)
    for v in p['path_numerators'].values():assert type(v) is int
    assert sum(p['path_numerators'].values())==expected['path_numerator']
    b.integer(p['denominator'],1);assert p['denominator']==expected['denominator']
    b.exact(p['class_counts'],expected['class_counts']);b.exact(p['old_occurrences'],expected['old_occurrences'])
    assert set(proof['digests'])=={key+'_sha256' for key in set(COMMON)-{'schema'}|{direction}}|{'base_paired_sha256'}
    for key in set(COMMON)-{'schema'}:
        assert proof['digests'][key+'_sha256']==b.digest(proof[key])
        if key+'_sha256' in expected:assert b.digest(proof[key])==expected[key+'_sha256']
    assert proof['digests']['base_paired_sha256']==b.digest({key:base[key] for key in BASE if key!='schema'})
    assert proof['digests'][direction+'_sha256']==b.digest(proof[direction])
    assert b.digest(proof[direction])==expected['production_prefix_schedule_sha256' if role=='production' else 'independent_suffix_schedule_sha256']
    for key in ('owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',direction):assert set(proof[key])==set(ids)
    total=positions=0;tops=[];marginals=[]
    for pid in sorted(ids):
        cap=b.integer(proof['owner_caps'][pid]);count=b.integer(proof['owner_entry_counts'][pid]);total+=count
        entries=proof['owner_top_entries'][pid];assert type(entries) is list and len(entries)==min(256,count)
        for entry in entries:
            assert type(entry) is list and len(entry)==3
            w,g,n=entry;b.integer(w);b.integer(g,0,expected['geometry']['full_groups']-1);b.integer(n,1)
        assert entries==sorted(entries,key=lambda x:(-x[0],x[1],x[2]))
        assert len({(g,n) for _,g,n in entries})==len(entries);tops.extend(entries)
        prefix=[0]
        for w,_,_ in entries:prefix.append(prefix[-1]+w)
        b.exact(proof['owner_prefixes'][pid],prefix);capped=[min(v,cap) for v in prefix]
        b.exact(proof['capped_prefixes'][pid],capped)
        delta=[y-x for x,y in zip(capped,capped[1:])];assert delta==sorted(delta,reverse=True)
        marginals.extend((v,pid,j) for j,v in enumerate(delta,1))
        vector=proof[direction][pid];assert type(vector) is list and len(vector)>1
        for v in vector:b.integer(v)
        positions+=len(vector)-1
        if role=='production':assert vector[0]==0 and vector[-1]==cap and vector==sorted(vector)
        else:assert vector[-1]==0 and vector[0]==cap and vector==sorted(vector,reverse=True)
    assert positions==expected['geometry']['source_characters'] and total==p['class_counts']['1']
    assert len({(g,n) for _,g,n in tops})==len(tops)
    b.exact(sorted(tops,key=lambda x:(-x[0],x[1],x[2]))[:256],p['top_entries']['1'])
    chosen=sorted(marginals,key=lambda v:(-v[0],v[1],v[2]))[:256]
    b.exact(proof['marginal_choices'],[[pid,rank,v] for v,pid,rank in chosen]);one=[0]
    for v,_,_ in chosen:one.append(one[-1]+v)
    b.exact(proof['one_owner_prefix'],one);shared=[0]
    for w,g,n in p['top_entries']['2']:b.integer(w);shared.append(shared[-1]+w)
    b.exact(proof['shared_prefix'],shared)
    rows=[];L=expected['path_numerator'];D=expected['denominator']
    for k in range(257):
        charge,negative=max((one[j]+shared[min(256-j,len(shared)-1)],-j) for j in range(min(k,len(one)-1)+1))
        rows.append({'k':k,'charge':charge,'one_owner_slots':-negative,'shared_slots':min(256+negative,len(shared)-1),
                     'numerator':L-charge,'integer_lower_bound':-(-(L-charge)//D)})
    b.exact(proof['rows'],rows);b.exact(rows,expected['rows']);b.exact(proof['deltas_vs53'],expected['deltas_vs53'])
    for row,old,delta in zip(rows,p['rows'],proof['deltas_vs53']):
        b.exact(delta,{'k':row['k'],'charge_reduction':old['charge']-row['charge'],'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
        assert delta['charge_reduction']>=0
    aggregates={'owners':len(ids),'positive_caps':sum(v>0 for v in proof['owner_caps'].values()),
        'cap_sum':sum(proof['owner_caps'].values()),'cap_max':max(proof['owner_caps'].values(),default=0),
        'top_entries_retained':len(tops),'full_one_owner_entries':total,
        'owners_with_clipped_prefix':sum(proof['owner_prefixes'][pid][-1]>proof['owner_caps'][pid] for pid in ids)}
    # This list is the exact accepted57 aggregate schema.
    b.exact(aggregates,expected['owner_aggregates'])
    return {'capped_prefixes':proof['capped_prefixes'],'shared_prefix':shared,'owner_caps':proof['owner_caps'],
            'owner_entry_counts':proof['owner_entry_counts'],'L':L,'D':D,'baseline_rows':rows,
            'scientific_proof_sha256':expected['scientific_proof_sha256']}


def coverage_check(proof,inputs,config,cohort,direction):
    expected=config['parent56_arms'][cohort];old=config['parent50_arms'][cohort]
    helper=b.coverage_report();helper.proof_shape(proof,old,set(inputs['texts']),direction)
    assert len(proof['owner_classes'])==len(inputs['pool'])
    for key,public in (('source_success','source_success_sha256'),('owner_classes','owner_classes_sha256'),
        ('shared_entry_ids','shared_entry_ids_sha256'),('forced_source_ids','forced_source_ids_sha256'),
        ('private_character_source_ids','private_character_source_ids_sha256')):
        assert b.digest(proof[key])==expected[public]
    b.exact(proof['occurrences'],expected['occurrences']);assert proof['occurrence_sha256']==expected['occurrence_sha256']
    b.exact(len(proof['forced_source_ids']),expected['coverage_floor']);assert expected['coverage_floor']==3
    b.exact(proof['private_character_entries'],expected['private_character_entries'])
    return proof['forced_source_ids']
