"""Reporting integrity tests: no candidates, case payloads, models or network."""
import copy
import json
import unittest
from pathlib import Path
import milestone_registry as registry

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(registry.REGISTRY.read_text())
    def reject(self, edit):
        edit(self.data)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            registry.validate(self.data)
    def test_current_and_generated_view(self):
        registry.validate(self.data)
        self.assertEqual(registry.render(self.data),registry.VIEW.read_text())
    def test_every_alias_resolves_same_record(self):
        for row in self.data['milestones']:
            for alias in row['aliases']:
                self.assertIs(registry.resolve(self.data,alias),row)
    def test_unknown_alias(self):
        with self.assertRaises(KeyError): registry.resolve(self.data,'not-a-milestone')
    def test_duplicate_ids(self):
        self.reject(lambda d:d['milestones'].append(copy.deepcopy(d['milestones'][0])))
    def test_colliding_alias(self):
        self.reject(lambda d:d['milestones'][1]['aliases'].append(d['milestones'][0]['id']))
    def test_duplicate_evidence(self):
        self.reject(lambda d:d['evidence'].append(copy.deepcopy(d['evidence'][0])))
    def test_missing_evidence(self):
        self.reject(lambda d:d['milestones'][0]['evidence_ids'].append('missing'))
    def test_bad_denominators(self):
        for den in [0,-1,1,float('nan'),float('inf'),True]:
            with self.subTest(den=den):
                d=copy.deepcopy(self.data);d['evidence'][0]['metrics'][0]['denominator']=den
                with self.assertRaises(ValueError):registry.validate(d)
    def test_nonfinite_metrics(self):
        for value in [float('nan'),float('inf'),-1,True]:
            with self.subTest(value=value):
                d=copy.deepcopy(self.data);d['evidence'][0]['metrics'][0]['value']=value
                with self.assertRaises(ValueError):registry.validate(d)
    def test_no_completion_percentages(self):
        self.reject(lambda d:d['evidence'][0]['metrics'][0].update(name='overall_completion_percent'))
    def test_pass_cannot_be_inferred_from_count(self):
        self.reject(lambda d:d['milestones'][0].update(status='passed'))
    def test_reported_evidence_cannot_qualify_pass(self):
        row=self.data['milestones'][0]
        row.update(status='passed',qualification={'evidence_ids':['catalogue-jupiter-reported'],'all_clauses_satisfied':True,'review_authority':'reviewer'})
        with self.assertRaises(ValueError):registry.validate(self.data)
    def test_metadata_verification_cannot_qualify_pass(self):
        row=self.data['milestones'][0]
        row.update(status='passed',qualification={'evidence_ids':['catalogue-v25'],'all_clauses_satisfied':True,'review_authority':'reviewer'})
        with self.assertRaises(ValueError):registry.validate(self.data)
    def test_undefined_is_not_failed_or_passed(self):
        for status in ['failed','passed']:
            d=copy.deepcopy(self.data)
            row=next(r for r in d['milestones'] if r['gate']['readiness']=='undefined')
            row['status']=status
            with self.assertRaises(ValueError):registry.validate(d)
    def test_dependency_cycles(self):
        self.reject(lambda d:d['milestones'][0]['gate']['requires'].append(d['milestones'][0]['id']))
        d=copy.deepcopy(self.data);d['milestones'][0]['gate']['requires']=['D2'];d['milestones'][1]['gate']['requires']=['D1']
        with self.assertRaises(ValueError):registry.validate(d)
    def test_pass_requires_all_clauses_and_authority(self):
        row=self.data['milestones'][0];e=self.data['evidence'][0]
        e['verification']='independently_qualified'
        row.update(status='passed',qualification={'evidence_ids':[e['id']],'all_clauses_satisfied':False,'review_authority':'reviewer'})
        with self.assertRaises(ValueError):registry.validate(self.data)
        row['qualification']['all_clauses_satisfied']=True
        with self.assertRaises(ValueError):registry.validate(self.data)
        row['qualification'].update(gate_sha256=row['gate_sha256'],verified_at='2026-10-26',clause_evidence={str(i):[e['id']] for i in range(len(row['gate']['all_of']))})
        e['observed_at']='2026-10-25'
        registry.validate(self.data)
        row['qualification']['review_authority']=''
        with self.assertRaises(ValueError):registry.validate(self.data)
    def test_missing_canonical_milestone(self):
        self.reject(lambda d:d['milestones'].pop())
    def test_missing_legacy_alias(self):
        self.reject(lambda d:d['milestones'][0].update(aliases=[]))
    def test_gate_weakening_without_version(self):
        self.reject(lambda d:d['milestones'][4]['gate'].update(all_of=['Correctness checked.']))
    def test_invalid_dates(self):
        self.reject(lambda d:d['evidence'][0].update(recorded_at='yesterday'))
    def test_incomplete_clause_evidence(self):
        row=self.data['milestones'][0];e=self.data['evidence'][0]
        e.update(verification='independently_qualified',observed_at='2026-10-25')
        row.update(status='passed',qualification={'evidence_ids':[e['id']],'all_clauses_satisfied':True,'review_authority':'reviewer','gate_sha256':row['gate_sha256'],'verified_at':'2026-10-26','clause_evidence':{}})
        with self.assertRaises(ValueError):registry.validate(self.data)
    def test_render_reports_not_promotes(self):
        rendered=registry.render(self.data)
        self.assertIn('owner_reported_unverified',rendered)
        self.assertIn('943/4081 (23.107% measured ratio)',rendered)
        self.assertIn('518/4081 (12.693% measured ratio)',rendered)
        self.assertNotIn('**passed**',rendered)
    def test_measurement_does_not_change_status(self):
        original=[r['status'] for r in self.data['milestones']]
        self.data['evidence'][0]['metrics'][0]['value']=4081
        registry.render(self.data)
        self.assertEqual(original,[r['status'] for r in self.data['milestones']])

if __name__=='__main__':unittest.main()
