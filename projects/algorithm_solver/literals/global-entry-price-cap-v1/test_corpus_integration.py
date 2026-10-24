"""Actual invented 300-ID JSON integration and corruption; no private inputs."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import signal
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import binding as b
import caps
import independent
import production
import report
import integration as integ


def ancestor_fixture(root):
    # Adapted immutable53 invented-authority construction. No ancestor fixture
    # file is executed and no historical corpus artifact is read.
    report53 = globals()["report"].prior.prior
    report = report53
    tighten = caps.parent
    texts = {str(pid): 'aaa' if pid < 297 else ('abx','aby','abz')[pid-297] for pid in range(300)}
    banned = set(texts.values())
    alphabet = [chr(i) for i in range(32, 127)]+['\n']
    seed = alphabet+['zz']
    shared = ['aa','ab']; extras = ['zz']
    pool = sorted(set(alphabet+shared+extras))
    q = [0 for pid, text in sorted(texts.items()) for start in range(len(text))
         for end in range(start+1, len(text)+1) if text[start:end] in pool]
    source_hashes = {pid: hashlib.sha256(text.encode()).hexdigest() for pid, text in texts.items()}
    lift = tighten.Tighten(texts, banned, pool, q, seed, alphabet, 1000000,
                          old_source_hashes=source_hashes, old_banned=banned)
    paired = report.shaped(lift.certificate()); proof = paired['lifted']
    cert = {'denominator': 1000000, 'numerator': proof['old_numerator'],
            'integer_lower_bound': -(-proof['old_numerator']//1000000),
            'relaxed_paths_numerator': sum(proof['path_numerators'].values()),
            'top_capacity_numerator': proof['old_charge'],
            'per_program_path_numerators': [proof['path_numerators'][pid] for pid in sorted(texts)]}
    old = {'pool_entries': len(pool), 'maximum_entry_length': max(map(len, pool)),
           'shared_learned_entries': len(shared), 'seed_extra_entries': len(extras),
           'seed_extras_sha256': hashlib.sha256(json.dumps(extras, ensure_ascii=True).encode()).hexdigest(),
           'occurrences': len(q), 'certificate': cert}
    index = lift.index
    geometry = {'source_characters': len(index.positions), 'full_groups': len(index.groups),
                'full_distinct_entries': index.distinct_allowed_entries,
                'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows)}
    bindings = {key: 'a'*64 for key in ('source_sha256', 'seed_sha256', 'pool_sha256',
                'q_sha256', 'old_private_results_sha256', 'old_evidence_sha256', 'full_evidence_sha256')}
    bindings.update(source_hashes_sha256=report.digest(source_hashes),
                    bans_sha256=report.digest(sorted(banned)), banned_entries=len(banned))
    inputs = dict(texts=texts, banned=banned, pool=pool, q=q, seed=seed, alphabet=alphabet,
                  denominator=1000000, source_hashes=source_hashes, parent_certificate=cert,
                  geometry=geometry, bindings=bindings)
    config = {'active': True, 'fit_ids': list(range(300)), 'limits': {
        'worker_seconds': 600, 'production_seconds': 1200, 'report_seconds': 1200,
        'cleanup_seconds': 10, 'address_space_bytes': 8*1024**3,
        'arm_cores': {'R': [6], 'naming': [7]}},
        'old_arms': {cohort: copy.deepcopy(old) for cohort in report.COHORTS},
        'source_hashes': {cohort: source_hashes for cohort in report.COHORTS}}
    report.write(root/'parent50-contract.json', {'invented': True})
    parent_hash=report.sha(root/'parent50-contract.json')
    parent_arms=[]
    for cohort in report.COHORTS:
        parent_arms.append({'cohort':cohort,'complete':True,'validation_loaded':False,'contract_sha256':parent_hash,
            'all257_independently_replayed':True,'old_certificate_independently_replayed':True,'suffix_potential_proof_checked':True,
            'bindings_sha256':report.digest(bindings),'source_identity_sha256':report.digest(source_hashes),
            'banned_set_sha256':report.digest(sorted(banned)),'parent_certificate_sha256':report.digest(cert),
            'old_occurrence_order_sha256':proof['occurrence_sha256'],
            'old_path_terms_sha256':report.digest([proof['path_numerators'][pid] for pid in sorted(texts)]),
            'fit_problems':300,'old_pool_entries':len(pool),'seed_entries':len(seed),'old_occurrences':len(q),
            'geometry':geometry,'denominator':1000000,'path_numerator':sum(proof['path_numerators'].values()),
            'old_charge':proof['old_charge'],'old_numerator':proof['old_numerator'],
            'old_integer_lower_bound':-(-proof['old_numerator']//1000000),'class_counts':proof['class_counts'],
            'rows':proof['rows'],'checked_proof_sha256':report.digest(proof),
            'top_entries_sha256':report.digest(proof['top_entries']),'largest_positive_k':report.positive_k(proof)})
    parent={'schema':'gamma.potential-lift.report.v1','complete':True,'contract_sha256':parent_hash,
        'validation_loaded':False,'validation_or_cases_opened':False,
        'verdicts':{'all257_replayed':True,'k0_preserves_old_bound':True},'arms':parent_arms}
    report.write(root/'parent50.json',parent)
    config.update(parent50_arms={a['cohort']:copy.deepcopy(a) for a in parent_arms},
        parent50_evidence={'path':root.name+'/parent50.json','sha256':report.sha(root/'parent50.json')},
        parent50_contract={'path':root.name+'/parent50-contract.json','sha256':parent_hash})
    report.write(root/'contract.json', config)
    ch = report.sha(root/'contract.json')
    arms = [{'schema': 'gamma.potential-tightening.arm.v1', 'complete': True, 'validation_loaded': False,
             'cohort': cohort, 'contract_sha256': ch, 'bindings': bindings,
             'full_shape': geometry, 'proof': copy.deepcopy(paired), 'seconds': .1,
             'peak_rss_kib': 1024, 'phase_seconds': {'input': .01, 'proof': .02}}
            for cohort in report.COHORTS]
    run, output = root/'run', root/'report'
    run.mkdir(); output.mkdir()
    for arm in arms:
        (run/arm['cohort']).mkdir()
        report.write(run/arm['cohort']/'results.json', arm)
    production = {'complete': True, 'validation_loaded': False, 'contract_sha256': ch,
                  'seconds': .2, 'arms': arms}
    supervisor = {'complete': True, 'phase': 'production', 'contract_sha256': ch,
                  'elapsed': .3, 'cleanup_seconds': .01, 'returncodes': [0, 0]}
    report.write(run/'results.json', production); report.write(run/'supervisor.json', supervisor)
    return SimpleNamespace(inputs=inputs, config=config, run=run, output=output,
                           production=production, supervisor=supervisor, contract_hash=ch)


def fixture(root):
    f=ancestor_fixture(root);i=f.inputs
    args=(i['texts'],i['banned'],i['pool'],i['q'],i['seed'],i['alphabet'],i['denominator'])
    kwargs=dict(expected_source_hashes=i['source_hashes'],expected_old_banned=i['banned'],
                expected_old_certificate=i['parent_certificate'])
    p=report.shaped(caps.check(*args,**kwargs))
    checked=report.shaped(independent.check(*args,**kwargs,
        expected_base57_prefix_schedule=p['base57']['owner_prefix_schedule'],
        expected_price_prefix_schedule=p['price_prefix_schedule'],
        expected_unpriced_prefix_schedule=p['unpriced_prefix_schedule'],
        expected_count_streams=p['count_streams'],expected_price_caps=p['price_caps'],
        expected_shared_counts=p['shared_counts'],expected_price_rows=p['price_rows']))
    parents53=[];parents57=[]
    for raw in f.production['arms']:
        a=report.prior.prior.sanitize(raw['cohort'],i,raw,checked['base57']['base'],i['geometry'])
        parents53.append(a)
        raw57=dict(raw,schema='gamma.owner-path-cap.arm.v1',proof=p['base57'])
        parents57.append(report.prior.public_arm(raw['cohort'],raw57,checked['base57'],a))
    cov=integ.coverage.production(i['texts'],i['pool'],i['banned'])
    reverse=integ.coverage.replay(i['texts'],i['pool'],i['banned'])
    base=p['base57'];L=sum(base['base']['tightened']['path_numerators'].values())
    required=report.shaped(integ.allocation.allocate(base['capped_prefixes'],base['shared_prefix'],
                                                    cov['forced_source_ids'],L,i['denominator']))
    assert cov['forced_source_ids']==['297','298','299']
    assert cov['private_character_entries']==3
    c56={key+'_sha256':report.digest(cov[key]) for key in ('source_success','owner_classes',
        'shared_entry_ids','forced_source_ids','private_character_source_ids')}
    c56.update(occurrences=cov['occurrences'],occurrence_sha256=cov['occurrence_sha256'],coverage_floor=3,
        private_character_entries=3,production_prefix_sha256=report.digest(cov['prefix_reachable']),
        independent_suffix_sha256=report.digest(reverse['suffix_reachable']))
    contexts={}
    for cohort in report.COHORTS:
        ctx=dict(c56,cohort=cohort,denominator=i['denominator'],path_numerator=L,
            source_identity_sha256=report.digest(i['source_hashes']),banned_set_sha256=report.digest(sorted(i['banned'])),
            parent_scientific_proof_sha256=report.digest(caps.scientific57(base)),
            inherited_capped_prefixes_sha256=report.digest(base['capped_prefixes']),
            inherited_owner_caps_sha256=report.digest(base['owner_caps']),
            inherited_shared_prefix_sha256=report.digest(base['shared_prefix']),
            coverage_occurrences=cov['occurrences'],coverage_occurrence_sha256=cov['occurrence_sha256'],
            mandatory_value=required['mandatory_value'],allocation_sha256=report.digest(required),
            remaining_marginal_choices_sha256=report.digest(required['remaining_marginal_choices']),
            final_owner_counts_sha256=report.digest(required['final_owner_counts']),
            rows=required['rows'],baseline57_rows=base['rows'],
            largest_positive_k=report.positive(required['rows']))
        ctx['deltas_vs57']=[{'k':x['k'],'empty_by_required_owners':x['empty_by_required_owners'],
            'charge_reduction':None if x['empty_by_required_owners'] else y['charge']-x['charge'],
            'integer_bound_gain':None if x['empty_by_required_owners'] else x['integer_lower_bound']-y['integer_lower_bound']}
            for x,y in zip(required['rows'],base['rows'])]
        contexts[cohort]=ctx
    f.config.update(full_shape={cohort:i['geometry'] for cohort in report.COHORTS},
        parent53_arms={a['cohort']:a for a in parents53},parent57_arms={a['cohort']:a for a in parents57},
        parent56_arms={cohort:copy.deepcopy(c56) for cohort in report.COHORTS},context61_arms=contexts,
        carrier_limits=b.CARRIER_LIMITS,lambda_family=p['lambda_family'],price_diagnostics=b.PRICE_DIAGNOSTICS)
    for key,arms in (('parent53',parents53),('parent57',parents57),('parent56',list(f.config['parent56_arms'].values())),
                     ('context61',list(contexts.values()))):
        path=root/(key+'.json');b.write(path,{'complete':True,'arms':arms})
        contract=root/(key+'-contract.json');b.write(contract,{'invented':True})
        f.config[key+'_evidence']={'path':str(path),'sha256':b.sha(path)}
        f.config[key+'_contract']={'path':str(contract),'sha256':b.sha(contract)}
    f.config['feasibility59']={'path':str(root/'feasibility59.json'),'sha256':'f'*64}
    b.write(root/'contract.json',f.config);f.contract_hash=b.sha(root/'contract.json')
    # Execute the actual integration builder, then retain actual JSON bytes.
    proof,shape=production.execute(i,f.config,'R')
    for raw in f.production['arms']:
        raw.update(schema='gamma.global-entry-price-cap.arm.v1',proof=copy.deepcopy(proof),
                   full_shape=shape,contract_sha256=f.contract_hash)
        b.write(f.run/raw['cohort']/'results.json',raw)
    for value,name in ((f.production,'results.json'),(f.supervisor,'supervisor.json')):
        value['contract_sha256']=f.contract_hash;b.write(f.run/name,value)
    f.production=b.read(f.run/'results.json');f.supervisor=b.read(f.run/'supervisor.json')
    f.config=b.read(root/'contract.json');f.checked=checked
    return f


class CorpusIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.f=fixture(self.root);self.loads=[]
        def load(*args):self.loads.append(args[2]);return copy.deepcopy(self.f.inputs)
        self.patches=[patch.object(report,'HERE',self.root),patch.object(b,'check_contract'),
            patch.object(b,'load_inputs',side_effect=load),patch.object(report,'module',return_value=independent),
            patch.object(report.resource,'setrlimit'),patch.object(report.os,'sched_setaffinity')]
        self.patches += [patch.object(b,key) for key in ('verify_parent50','verify_parent53','verify_parent57',
                         'verify_parent56','verify_feasibility','verify_context61')]
        for item in self.patches:item.start()

    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        signal.setitimer(signal.ITIMER_REAL,0);self.tmp.cleanup()

    def worker(self,cohort):return report.worker(cohort,self.root/'invented',self.f.run,self.f.output,time.monotonic()+30)

    def save(self):
        for raw in self.f.production['arms']:b.write(self.f.run/raw['cohort']/'results.json',raw)
        b.write(self.f.run/'results.json',self.f.production);b.write(self.f.run/'supervisor.json',self.f.supervisor)

    def combined(self):
        for cohort in report.COHORTS:self.worker(cohort)
        return report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])

    def test_actual_300_id_json_pipeline_and_public_allowlist(self):
        result=self.combined();report.publish(self.f.output,result)
        self.assertIs(b.read(self.f.output/'results.json')['complete'],True)
        self.assertEqual(self.loads,['R','naming']);self.assertIs(result['predictions']['P1'],True)
        self.assertIs(result['required_owner_constraint_applied'],True)
        for arm in result['arms']:
            self.assertEqual(set(arm),report.ARM_FIELDS);self.assertEqual(len(arm['rows']),257)
            for row in arm['rows'][:3]:
                self.assertIs(row['empty_by_required_owners'],True)
                self.assertTrue(all(v is None for k,v in row.items() if k not in ('k','empty_by_required_owners')))
            self.assertTrue(all(not x['empty_by_required_owners'] for x in arm['rows'][3:]))
            self.assertEqual(arm['report_work']['production_forward_positions_checked'],15*900)
            self.assertEqual(arm['report_work']['unpriced_production_forward_positions_checked'],900)
            self.assertEqual(arm['baseline57_report_work']['production_forward_positions_checked'],900)
        raw=self.f.production['arms'][0]['proof'];g=raw['global']
        self.assertIn('10',g['count_streams']);self.assertIn('299',g['price_prefix_schedule'])
        self.assertEqual(len(g['price_caps']['299']),15)
        self.assertEqual(report.digest(raw),report.digest(json.loads(json.dumps(raw))))
        serialized=json.dumps(result)
        for field in ('"owner_caps"','"owner_top_entries"','"price_prefix_schedule"','"price_suffix_schedule"',
                      '"unpriced_prefix_schedule"','"unpriced_suffix_schedule"','"count_streams"','"price_caps"',
                      '"shared_counts"','"remaining_marginal_choices"','"path_numerators"',
                      '"forced_source_ids"','"prefix_reachable"','"suffix_reachable"','"aaa"','"abx"','"q"'):
            self.assertNotIn(field,serialized)
        for flag in ('m1_claim','promotion_allowed','current_best_changed','validation_loaded','validation_or_cases_opened'):
            self.assertIs(result[flag],False)
        self.assertEqual(result['new_packets'],0);self.assertEqual(result['new_qualification_jobs'],0)
        saved=b.read(self.f.output/'R.json')
        for key,value in (('source_text','forbidden'),('report_peak_rss_kib',0),('minimum_feasible_one_owner_budget',2)):
            bad=copy.deepcopy(saved);bad[key]=value;b.write(self.f.output/'R.json',bad)
            with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])
            b.write(self.f.output/'R.json',saved)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[False,0])

    def test_rehashed_intermediate_graph_coverage_and_allocation_corruption(self):
        original=self.f.production['arms'][0]
        for kind in ('price_vector','unpriced_vector','owner_vector','count_hash','shared_count','numeric_cap',
                     'cap_bool','price_row','coverage_bit','forced_owner','required_value','required_rank'):
            raw=copy.deepcopy(original);p=raw['proof'];g=p['global']
            if kind=='price_vector':g['price_prefix_schedule']['299'][1][2]+=1
            elif kind=='unpriced_vector':
                g['unpriced_prefix_schedule']['299'][2]+=1;g['price_prefix_schedule']['299'][0][2]+=1
            elif kind=='owner_vector':g['base57']['owner_prefix_schedule']['299'][2]+=1
            elif kind=='count_hash':g['count_streams']['299'][0]['sha256']='0'*64
            elif kind=='shared_count':g['shared_counts'][0][1]+=1
            elif kind=='numeric_cap':
                g['price_caps']['299'][1]+=1;g['price_prefix_schedule']['299'][1][-1]+=1
                # Repair every dependent scalar, curve and commitment. The
                # resulting carrier is arithmetically self-consistent; only
                # fresh occurrence/schedule replay can establish its cap.
                base=g['base57'];L=sum(base['base']['tightened']['path_numerators'].values())
                D=base['base']['tightened']['denominator']
                for index,price in enumerate(g['lambda_family']):
                    residual=sum(values[index] for values in g['price_caps'].values())
                    charge=price*256+residual;num=L-charge
                    g['price_rows'][index]={'lambda':price,'entry_charge':price*256,'residual_cap':residual,
                        'charge':charge,'numerator':num,'integer_lower_bound':-(-num//D)}
                winner=min(range(15),key=lambda index:(g['price_rows'][index]['charge'],index))
                g['selected_price_index']=winner;G=g['global_charge']=g['price_rows'][winner]['charge']
                for index,old in enumerate(base['rows']):
                    charge=min(old['charge'],G);num=L-charge;bound=-(-num//D)
                    g['rows'][index]={'k':index,'charge':charge,'baseline57_charge':old['charge'],'global_charge':G,
                        'numerator':num,'integer_lower_bound':bound,'charge_reduction_vs57':old['charge']-charge}
                    g['deltas_vs57'][index]={'k':index,'charge_reduction':old['charge']-charge,
                        'integer_bound_gain':bound-old['integer_lower_bound']}
                ident=integ.identity(g,self.f.inputs['source_hashes'],self.f.inputs['banned'])
                p['rows']=integ.combine(g,p['required'],global_identity=ident,required_identity=ident)
            elif kind=='cap_bool':g['price_caps']['299'][0]=False
            elif kind=='price_row':g['price_rows'][1]['charge']+=1
            elif kind=='coverage_bit':p['coverage']['prefix_reachable']['0'][1]=False
            elif kind=='forced_owner':p['coverage']['forced_source_ids'][0]='296'
            elif kind=='required_value':p['required']['mandatory_value']+=1
            elif p['required']['remaining_marginal_choices']:
                p['required']['remaining_marginal_choices'][0][1]+=1
            else:
                p['required']['final_owner_counts']['297']+=1
            for field in caps.COMMON+('price_prefix_schedule','unpriced_prefix_schedule'):
                g['digests'][field+'_sha256']=report.digest(g[field])
            g['base57']['digests']['owner_prefix_schedule_sha256']=report.digest(g['base57']['owner_prefix_schedule'])
            for field in ('global','coverage','required','rows'):p['digests'][field+'_sha256']=report.digest(p[field])
            # These interior changes preserve scalar/cap shapes; prove rejection
            # by fresh replay rather than relying only on a stale digest.
            if kind in ('price_vector','unpriced_vector','owner_vector','count_hash','coverage_bit','numeric_cap'):
                report.shape(p,raw['full_shape'])
            with self.subTest(kind=kind),self.assertRaises(AssertionError):
                report.replay('R',self.f.inputs,raw,independent,self.f.config)

    def test_every_ancestral_scientific_authority_is_bound(self):
        c=self.f.config;i=self.f.inputs
        proof,shape=production.execute(i,c,'R')
        report.exact(report.shaped(proof),self.f.production['arms'][0]['proof']);report.exact(shape,i['geometry'])
        for parent,key in (('old_arms','occurrences'),('parent50_arms','old_occurrence_order_sha256'),
                           ('parent53_arms','checked_proof_sha256'),('parent57_arms','scientific_proof_sha256'),
                           ('parent56_arms','forced_source_ids_sha256'),('context61_arms','allocation_sha256')):
            bad=copy.deepcopy(c);old=bad[parent]['R'][key];bad[parent]['R'][key]=old+1 if type(old) is int else '0'*64
            with self.subTest(parent=parent),self.assertRaises(AssertionError):production.execute(i,bad,'R')

    def test_failed_or_malformed_production_precedes_ancestral_load(self):
        original=copy.deepcopy((self.f.production,self.f.supervisor))
        for kind in ('false_exit','incomplete','bad_shape','lineage','failure_marker'):
            self.f.production,self.f.supervisor=copy.deepcopy(original)
            if kind=='false_exit':self.f.supervisor['returncodes']=[False,0]
            elif kind=='incomplete':self.f.production['complete']=False
            elif kind=='bad_shape':self.f.production['arms'][0]['proof']['global']['price_caps']['299'][0]=False
            elif kind=='lineage':self.f.production['arms'][0]['bindings']['source_hashes_sha256']='0'*64
            else:(self.f.run/'failure.json').write_text('{}')
            self.save()
            with self.subTest(kind=kind),self.assertRaises(AssertionError):self.worker('R')
            self.assertEqual(self.loads,[]);self.assertFalse((self.f.output/'R.json').exists())
            (self.f.run/'failure.json').unlink(missing_ok=True)
        target=self.f.output/'naming-proof.json';target.write_text('existing authority')
        with self.assertRaises(AssertionError):self.worker('naming')
        self.assertEqual(target.read_text(),'existing authority');self.assertEqual(self.loads,[])

    def test_retained_proof_and_public_diagnostics_are_reconciled(self):
        self.combined()
        path=self.f.output/'R-proof.json';proof=b.read(path)
        bad=copy.deepcopy(proof);bad['global']['price_suffix_schedule']['299'][1][0]+=1;b.write(path,bad)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])
        b.write(path,proof)
        path=self.f.output/'R.json';arm=b.read(path)
        arm['rows'][3]['active_bound']='fabricated';b.write(path,arm)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])

    def test_carrier_boundary_and_publication_failure_withdraw(self):
        target=self.root/'size.json';payload={'value':'abcdefghij'};b.write(target,payload);encoded=target.read_bytes()
        with patch.object(b,'CARRIER_MAX_BYTES',len(encoded)):
            self.assertEqual(b.read(target),payload);b.write(target,payload)
        with patch.object(b,'CARRIER_MAX_BYTES',len(encoded)-1):
            with self.assertRaises(AssertionError):b.read(target)
            with self.assertRaises(AssertionError):b.write(target,payload)
            self.assertEqual(target.read_bytes(),encoded)
        result=self.combined()
        with patch.object(b,'CARRIER_MAX_BYTES',20):
            with self.assertRaises(AssertionError):report.publish(self.f.output,result)
        self.assertFalse((self.f.output/'results.json').exists());self.assertFalse((self.f.output/'REPORT.md').exists())


class CombinationTests(unittest.TestCase):
    def test_actual_q_tiny_covering_paths_and_identity_rejection(self):
        from test_caps import fixture as tiny
        def paths(text,words):
            if not text:return [()]
            return [(w,)+rest for w in words if text.startswith(w) for rest in paths(text[len(w):],words)]
        for texts in ({'p':'ab','s':'ac'},{'p':'aaa','s':'aba'}):
            kw=tiny(texts,set(texts.values()),D=3);g=caps.check(**kw,capacity=3)
            cov=integ.coverage.production(texts,kw['old_pool'],kw['banned']);base=g['base57']
            L=sum(base['base']['tightened']['path_numerators'].values());forced=cov['forced_source_ids']
            required=integ.allocation.allocate(base['capped_prefixes'],base['shared_prefix'],forced,L,3,3)
            ident=integ.identity(g,kw['expected_source_hashes'],kw['banned'],3)
            rows=integ.combine(g,required,global_identity=ident,required_identity=dict(ident))
            allwords={text[i:j] for text in texts.values() for i in range(len(text)) for j in range(i+1,len(text)+1)}-kw['banned']
            owners={w:{p for p,t in texts.items() if w in t} for w in allwords}
            covered=0
            for size in range(4):
                for words in itertools.combinations(sorted(allwords),size):
                    choices=[paths(t,words) for t in texts.values()]
                    if not all(choices):continue
                    covered+=1;k=sum(len(owners[w])==1 for w in words)
                    self.assertFalse(rows[k]['empty_by_required_owners'])
                    for selected in itertools.product(*choices):
                        F=sum(10*sum(len(w)==1 for w in seq)-len(seq) for seq in selected)
                        self.assertGreaterEqual(F,rows[k]['integer_lower_bound'])
            self.assertGreater(covered,0)
            for field in ident:
                bad=dict(ident);value=bad[field];bad[field]=value+1 if type(value) is int else '0'*64
                with self.subTest(field=field),self.assertRaises(AssertionError):
                    integ.combine(g,required,global_identity=ident,required_identity=bad)

    def test_zero_capacity_forced_overcapacity_and_finite_slots(self):
        from test_caps import fixture as tiny
        seen=set()
        for texts,B in (({'p':'ab','s':'ab'},0),({'p':'ab','s':'ac'},1),
                        ({'p':'ab','s':'ac'},2),({'p':'ab','s':'ac'},16),({'p':'aaaa','s':'aaab'},3)):
            kw=tiny(texts,set(texts.values()),D=3)
            if B==16:kw['old_q']=[0]*len(kw['old_q'])
            g=caps.check(**kw,capacity=B)
            base=g['base57'];cov=integ.coverage.production(texts,kw['old_pool'],kw['banned'])
            L=sum(base['base']['tightened']['path_numerators'].values());forced=cov['forced_source_ids']
            required=integ.allocation.allocate(base['capped_prefixes'],base['shared_prefix'],forced,L,3,B)
            sorted_required=integ.allocation.independent(base['capped_prefixes'],base['shared_prefix'],forced,L,3,B)
            report.exact(report.shaped(required),report.shaped(sorted_required))
            identity=integ.identity(g,kw['expected_source_hashes'],kw['banned'],B)
            rows=integ.combine(g,required,global_identity=identity,required_identity=identity)
            self.assertEqual(rows,report.combined_rows(g,required))
            self.assertEqual(len(rows),B+1)
            for row in rows:
                self.assertEqual(row['empty_by_required_owners'],row['k']<len(forced))
                if row['empty_by_required_owners']:
                    self.assertTrue(all(v is None for k,v in row.items() if k not in ('k','empty_by_required_owners')))
                else:
                    seen.add(row['active_bound'])
                    self.assertNotIn('one_owner_slots',row);self.assertNotIn('shared_slots',row)
                    self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//3))
            if B>len(forced):
                finite=sum(len(x)-1 for x in base['capped_prefixes'].values())
                self.assertLessEqual(len(required['remaining_marginal_choices'])+len(forced),finite)
            if B==0:self.assertEqual(forced,[])
            if B==16:
                self.assertEqual(required['mandatory_value'],0)
                self.assertTrue(forced)
                self.assertTrue(all(row['one_owner_slots']>=len(forced) for row in required['rows'] if not row['empty_by_required_owners']))
            if len(forced)>B:self.assertTrue(all(row['empty_by_required_owners'] for row in rows))
        self.assertEqual(seen,{'global','required-owner','tie'})

    def test_global_diagnostic_ties_categories_and_empty_denominator(self):
        for winner,category in ((0,'zero'),(4,'interior'),(14,'maximum')):
            prices=[{'charge':20,'integer_lower_bound':-2} for _ in range(15)]
            prices[winner]={'charge':19,'integer_lower_bound':-2}
            proof={'global':{'price_rows':prices,'global_charge':19},'rows':[
                {'empty_by_required_owners':True,'active_bound':None},
                *({'empty_by_required_owners':False,'active_bound':x} for x in ('global','required-owner','tie'))]}
            got=report.diagnostics(proof)
            self.assertEqual(got['selected_price_index'],winner);self.assertEqual(got['selected_category'],category)
            self.assertEqual(got['minimizing_indices'],[winner]);self.assertFalse(got['tied'])
            self.assertEqual(got['defined_budget_denominator'],3)
            self.assertEqual(got['active_bound_counts'],{'global':1,'required-owner':1,'tie':1})
            self.assertTrue(all(v==1/3 for v in got['active_bound_shares'].values()))
            # Raw unit improvement can leave an integer ceiling unchanged.
            self.assertEqual(got['integer_bound_gain_vs_lambda0'],0)
            self.assertEqual(got['charge_reduction_vs_lambda0'],0 if winner==0 else 1)
        prices[0]={'charge':19,'integer_lower_bound':-2}
        proof['rows']=[{'empty_by_required_owners':True,'active_bound':None}]
        got=report.diagnostics(proof)
        self.assertEqual(got['minimizing_indices'],[0,14]);self.assertTrue(got['tied'])
        self.assertEqual(got['selected_price_index'],0);self.assertEqual(got['minimizer_count'],2)
        self.assertEqual(got['defined_budget_denominator'],0)
        self.assertTrue(all(v is None for v in got['active_bound_shares'].values()))


if __name__=='__main__':unittest.main()
