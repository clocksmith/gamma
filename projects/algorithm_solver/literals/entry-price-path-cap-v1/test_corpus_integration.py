"""Independent supplied-input pipeline/corruption checks; no private inputs."""
import copy
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import binding as b
import caps
import independent
import production
import report


def fixture(root):
    # Unchanged invented predecessor helper:300 numeric-looking source IDs,
    # original+paired+owner proof authorities, no saved corpus artifact.
    with patch.dict(sys.modules,{'report':report.prior,'caps':caps.prior,'independent':independent.parent}):
        helper=report.module('item63_fixture57',b.LIT/'owner-path-cap-v1/test_report.py')
        f=helper.fixture(root)
    i=f.inputs;args=(i['texts'],i['banned'],i['pool'],i['q'],i['seed'],i['alphabet'],i['denominator'])
    kwargs={'expected_source_hashes':i['source_hashes'],'expected_old_banned':i['banned'],
            'expected_old_certificate':i['parent_certificate']}
    p=report.shaped(caps.check(*args,**kwargs))
    checked=report.shaped(independent.check(*args,**kwargs,
        expected_base57_prefix_schedule=p['base57']['owner_prefix_schedule'],
        expected_price_prefix_schedule=p['price_prefix_schedule'],
        expected_count_streams=p['count_streams'],expected_price_caps=p['price_caps']))
    parents=[]
    for raw in f.production['arms']:
        parents.append(report.prior.public_arm(raw['cohort'],raw,checked['base57'],f.config['parent53_arms'][raw['cohort']]))
    b.write(root/'parent57.json',{'complete':True,'arms':parents});b.write(root/'parent57-contract.json',{'invented':True})
    contexts={}
    for cohort in report.COHORTS:
        rows=copy.deepcopy(p['base57']['rows'])
        # Actual61 schema explicitly has null values below the coverage floor.
        for row in rows[:3]:
            row.update(empty=True,charge=None,numerator=None,integer_lower_bound=None)
        contexts[cohort]={'cohort':cohort,'rows':rows,'source_identity_sha256':b.digest(i['source_hashes'])}
    b.write(root/'context61.json',{'complete':True,'arms':list(contexts.values())})
    f.config.update(full_shape={cohort:i['geometry'] for cohort in report.COHORTS},
        parent57_arms={a['cohort']:a for a in parents},
        parent57_evidence={'path':str(root/'parent57.json'),'sha256':b.sha(root/'parent57.json')},
        parent57_contract={'path':str(root/'parent57-contract.json'),'sha256':b.sha(root/'parent57-contract.json')},
        context61_arms=contexts,context61_evidence={'path':str(root/'context61.json'),'sha256':b.sha(root/'context61.json')},
        carrier_limits=b.CARRIER_LIMITS,lambda_family=p['lambda_family'],price_diagnostics=b.PRICE_DIAGNOSTICS)
    b.write(root/'contract.json',f.config);f.contract_hash=b.sha(root/'contract.json')
    for raw in f.production['arms']:
        raw.update(schema='gamma.entry-price-path-cap.arm.v1',proof=copy.deepcopy(p),contract_sha256=f.contract_hash)
        b.write(f.run/raw['cohort']/'results.json',raw)
    for value,name in ((f.production,'results.json'),(f.supervisor,'supervisor.json')):
        value['contract_sha256']=f.contract_hash;b.write(f.run/name,value)
    # Retained transport is real, not comparison of the original Python maps.
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
        self.patches += [patch.object(b,key) for key in ('verify_parent50','verify_parent53','verify_parent57','verify_feasibility','verify_context61')]
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

    def test_actual_json_whole_pipeline_and_public_allowlist(self):
        result=self.combined();report.publish(self.f.output,result)
        self.assertTrue(b.read(self.f.output/'results.json')['complete'])
        self.assertEqual(self.loads,['R','naming']);self.assertTrue(result['predictions']['P1'])
        self.assertTrue(result['context61_descriptive_only']);self.assertFalse(result['required_owner_constraint_applied'])
        for arm in result['arms']:
            self.assertEqual(set(arm),report.ARM_FIELDS);self.assertEqual(len(arm['rows']),257)
            self.assertEqual(arm['report_work']['production_forward_positions_checked'],15*900)
            self.assertEqual(arm['baseline57_report_work']['production_forward_positions_checked'],900)
            self.assertEqual(arm['context61']['largest_positive_k'],report.positive(self.f.config['context61_arms'][arm['cohort']]['rows']))
        raw=self.f.production['arms'][0]['proof']
        self.assertIn('10',raw['count_streams']);self.assertIn('299',raw['price_prefix_schedule'])
        self.assertEqual(len(raw['price_caps']['299']),15)
        self.assertEqual(report.digest(raw),report.digest(json.loads(json.dumps(raw))))
        serialized=json.dumps(result)
        for field in ('"owner_caps"','"owner_top_entries"','"price_prefix_schedule"','"price_suffix_schedule"',
                      '"count_streams"','"price_caps"','"priced_prefixes"','"marginal_choices"','"path_numerators"','"aaa"','"abx"','"q"'):
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

    def test_rehashed_intermediate_vectors_count_and_cap_corruption(self):
        original=self.f.production['arms'][0]
        for kind in ('price_vector','owner_vector','count_hash','numeric_cap','cap_bool'):
            raw=copy.deepcopy(original);p=raw['proof']
            if kind=='price_vector':
                p['price_prefix_schedule']['299'][1][2]+=1
                p['digests']['price_prefix_schedule_sha256']=report.digest(p['price_prefix_schedule'])
            elif kind=='owner_vector':
                p['base57']['owner_prefix_schedule']['299'][2]+=1
                p['base57']['digests']['owner_prefix_schedule_sha256']=report.digest(p['base57']['owner_prefix_schedule'])
                p['price_prefix_schedule']['299'][0][2]+=1
                p['digests']['price_prefix_schedule_sha256']=report.digest(p['price_prefix_schedule'])
            elif kind=='count_hash':
                p['count_streams']['299'][0]['sha256']='0'*64
                p['digests']['count_streams_sha256']=report.digest(p['count_streams'])
            elif kind=='numeric_cap':
                p['price_caps']['299'][1]+=1
                p['price_prefix_schedule']['299'][1][-1]+=1
                p['digests']['price_caps_sha256']=report.digest(p['price_caps'])
                p['digests']['price_prefix_schedule_sha256']=report.digest(p['price_prefix_schedule'])
            else:
                p['price_caps']['299'][0]=False
                p['digests']['price_caps_sha256']=report.digest(p['price_caps'])
            if kind!='cap_bool':report.shape(p,raw['full_shape'])
            with self.subTest(kind=kind),self.assertRaises(AssertionError):
                report.replay('R',self.f.inputs,raw,independent,self.f.config)

    def test_all_ancestral_science_reconciled_in_production(self):
        c=self.f.config;i=self.f.inputs
        args=[c['old_arms']['R'],c['parent50_arms']['R'],c['parent53_arms']['R'],c['parent57_arms']['R']]
        fresh,shape=production.execute(i,*args)
        report.exact(report.shaped(fresh),self.f.production['arms'][0]['proof']);report.exact(shape,i['geometry'])
        mutations=[(0,'occurrences'),(1,'old_occurrence_order_sha256'),(2,'checked_proof_sha256'),(3,'scientific_proof_sha256')]
        for index,key in mutations:
            bad=copy.deepcopy(args);bad[index][key]=bad[index][key]+1 if type(bad[index][key]) is int else '0'*64
            with self.subTest(ancestor=index),self.assertRaises(AssertionError):production.execute(i,*bad)

    def test_failed_or_malformed_production_precedes_ancestral_load(self):
        original=copy.deepcopy((self.f.production,self.f.supervisor))
        for kind in ('false_exit','incomplete','bad_shape','lineage','failure_marker'):
            self.f.production,self.f.supervisor=copy.deepcopy(original)
            if kind=='false_exit':self.f.supervisor['returncodes']=[False,0]
            elif kind=='incomplete':self.f.production['complete']=False
            elif kind=='bad_shape':self.f.production['arms'][0]['proof']['price_caps']['299'][0]=False
            elif kind=='lineage':self.f.production['arms'][0]['bindings']['source_hashes_sha256']='0'*64
            else:(self.f.run/'failure.json').write_text('{}')
            self.save()
            with self.subTest(kind=kind),self.assertRaises(AssertionError):self.worker('R')
            self.assertEqual(self.loads,[]);self.assertFalse((self.f.output/'R.json').exists())
            (self.f.run/'failure.json').unlink(missing_ok=True)
        target=self.f.output/'naming-proof.json';target.write_text('existing authority')
        with self.assertRaises(AssertionError):self.worker('naming')
        self.assertEqual(target.read_text(),'existing authority');self.assertEqual(self.loads,[])

    def test_checked_private_receipt_and_diagnostics_dominate_public_claims(self):
        self.combined()
        proof_path=self.f.output/'R-proof.json';proof=b.read(proof_path)
        bad=copy.deepcopy(proof);bad['price_suffix_schedule']['299'][1][0]+=1;b.write(proof_path,bad)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])
        b.write(proof_path,proof)
        path=self.f.output/'R.json';arm=b.read(path);arm['price_diagnostics']['denominator']+=1;b.write(path,arm)
        with self.assertRaises(AssertionError):report.combine(self.f.run,self.f.output,self.f.config,20,[0,0])

    def test_complete_carrier_read_write_and_publication_size_boundary(self):
        target=self.root/'size.json';payload={'value':'abcdefghij'}
        b.write(target,payload);encoded=target.read_bytes()
        with patch.object(b,'CARRIER_MAX_BYTES',len(encoded)):
            self.assertEqual(b.read(target),payload);b.write(target,payload)
        with patch.object(b,'CARRIER_MAX_BYTES',len(encoded)-1):
            with self.assertRaises(AssertionError):b.read(target)
            with self.assertRaises(AssertionError):b.write(target,payload)
            self.assertEqual(target.read_bytes(),encoded)
        result=self.combined()
        with patch.object(b,'CARRIER_MAX_BYTES',20):
            with self.assertRaises(AssertionError):report.publish(self.f.output,result)
        self.assertFalse((self.f.output/'results.json').exists())
        self.assertFalse((self.f.output/'REPORT.md').exists())


class DiagnosticTests(unittest.TestCase):
    def test_ties_zero_denominator_and_index_categories(self):
        prices=[0]+[2**r for r in range(14)]
        # rank1: tie index0/1 at10; rank2: index0 unique. A's third
        # increment is zero and MUST NOT contribute to the denominator.
        proof={'lambda_family':prices,'base57':{'owner_prefixes':{'private':[0,11,20,20]}},
               'price_caps':{'private':[10,9]+[100]*13}}
        got=report.diagnostics(proof)
        self.assertEqual(got['denominator'],2);self.assertEqual(got['histogram'],[2]+[0]*14)
        self.assertEqual(got['tied_rank_count'],1);self.assertEqual(got['minimizer_count'],3)
        self.assertEqual(got['affine_strict_below_A'],2)
        proof['base57']['owner_prefixes']['private']=[0,0]
        zero=report.diagnostics(proof)
        self.assertEqual(zero['denominator'],0);self.assertTrue(all(v is None for v in zero['category_shares'].values()))
        proof={'lambda_family':prices,'base57':{'owner_prefixes':{'a':[0,10],'b':[0,20000]}},
               'price_caps':{'a':[100,100,0]+[100]*12,'b':[100000]*14+[0]}}
        got=report.diagnostics(proof)
        self.assertEqual(got['histogram'][2],1);self.assertEqual(got['histogram'][14],1)
        self.assertEqual(got['category_counts'],{'zero':0,'interior':1,'maximum':1})
        self.assertEqual(got['category_shares'],{'zero':0.,'interior':.5,'maximum':.5})
        self.assertNotIn('private',json.dumps(got))

if __name__=='__main__':unittest.main()
