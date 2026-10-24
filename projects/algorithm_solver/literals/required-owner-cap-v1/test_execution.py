"""Invented inherited carriers and fresh coverage/allocation replay; no corpus."""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import binding as b
import parent_receipts as pr
import run
import report


def fixture():
    # Frozen57 kernels produce invented receipts ONLY; execution never loads them.
    script='''import json,caps,independent
from test_independent import fixture
kw=fixture({'0':'ab','1':'cd','2':'ef'},{'ab','cd','ef'})
p=caps.check(**kw);i=independent.check(**kw,expected_prefix_schedule=p['owner_prefix_schedule'])
print(json.dumps({'p':p,'i':i,'texts':kw['texts'],'pool':kw['old_pool'],'banned':sorted(kw['banned'])}))'''
    child=subprocess.run([sys.executable,'-B','-c',script],cwd=b.LIT/'owner-path-cap-v1',capture_output=True,text=True,check=True,timeout=20)
    f=b.parse(child.stdout);p,i=f['p'],f['i'];base=p['base'];tight=base['tightened'];texts=f['texts']
    geometry={'source_characters':6,'full_groups':max(g for es in p['owner_top_entries'].values() for _,g,_ in es)+1,
              'full_distinct_entries':sum(tight['class_counts'].values()),'exact_ban_occurrences':3}
    hashes={pid:hashlib.sha256(t.encode()).hexdigest() for pid,t in texts.items()}
    raw={'schema':'gamma.owner-path-cap.arm.v1','cohort':'R','complete':True,'validation_loaded':False,'contract_sha256':'old',
         'bindings':{},'full_shape':geometry,'proof':p,'seconds':1,'peak_rss_kib':1,'phase_seconds':{'input':.1,'proof':.2}}
    exp={'cohort':'R','geometry':geometry,'bindings_sha256':b.digest({}),'production_seconds':1,'production_peak_rss_kib':1,
         'production_phase_seconds_sha256':b.digest(raw['phase_seconds']),'production_proof_sha256':b.digest(p),
         'scientific_proof_sha256':b.digest({k:i[k] for k in pr.COMMON}|{'base':{k:base[k] for k in pr.BASE}}),
         'baseline53_proof_sha256':b.digest({k:base[k] for k in pr.BASE}),'baseline53_paired_digests':base['digests'],
         'baseline53_top_entries_sha256':b.digest(tight['top_entries']),'baseline53_rows':tight['rows'],
         'path_numerator':sum(tight['path_numerators'].values()),'denominator':tight['denominator'],
         'class_counts':tight['class_counts'],'old_occurrences':tight['old_occurrences'],
         'production_prefix_schedule_sha256':b.digest(p['owner_prefix_schedule']),
         'independent_suffix_schedule_sha256':b.digest(i['owner_suffix_schedule']),
         'rows':p['rows'],'deltas_vs53':p['deltas_vs53'],
         'source_identity_sha256':b.digest(hashes),'banned_set_sha256':b.digest(f['banned'])}
    for k in pr.COMMON:
        if k!='schema':exp[k+'_sha256']=b.digest(p[k])
    caps=p['owner_caps'];exp['owner_aggregates']={'owners':3,'positive_caps':sum(v>0 for v in caps.values()),'cap_sum':sum(caps.values()),'cap_max':max(caps.values()),
        'top_entries_retained':sum(map(len,p['owner_top_entries'].values())),'full_one_owner_entries':sum(p['owner_entry_counts'].values()),
        'owners_with_clipped_prefix':sum(p['owner_prefixes'][pid][-1]>caps[pid] for pid in caps)}
    inputs={'parent':raw,'texts':texts,'pool':f['pool'],'banned':set(f['banned']),'source_hashes':hashes,'reads':[]}
    cov=b.coverage().production(texts,f['pool'],inputs['banned'])
    old={'old_pool_entries':len(f['pool']),'geometry':geometry,'class_counts':tight['class_counts'],'old_occurrences':cov['occurrences'],'old_occurrence_order_sha256':cov['occurrence_sha256']}
    e56={k+'_sha256':b.digest(cov[k]) for k in ('source_success','owner_classes','shared_entry_ids','forced_source_ids','private_character_source_ids')}
    e56.update(occurrences=cov['occurrences'],occurrence_sha256=cov['occurrence_sha256'],coverage_floor=3,private_character_entries=cov['private_character_entries'])
    c={'parent57_arms':{'R':exp},'parent56_arms':{'R':e56},'parent50_arms':{'R':old},'parent59_arms':{'R':{'minimum_feasible_one_owner_budget':3}},
       'public_files':{v:'old' for v in b.PUBLIC.values()},'role_private_files':{role:{rel:'h' for rel in (b.SOURCES['R'],b.POOLS['R'],b.PARENTS[role]['R'])} for role in b.ROLES}}
    return inputs,i,c


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=fixture()

    def test_inherited_roles_and_fresh_pipeline(self):
        inputs,ind,c=copy.deepcopy(self.data);e=c['parent57_arms']['R']
        a=pr.validate(inputs['parent'],'production',e,'old',set(inputs['texts']))
        z=pr.validate(ind,'report',e,'old',set(inputs['texts']));self.assertEqual(a,z)
        proof=run.execute(inputs,c,'R');raw={'proof':proof,'contract_sha256':'new','seconds':1,'peak_rss_kib':1,'phase_seconds':{'input':.1,'proof':.2}}
        inputs['parent']=ind
        inputs['reads']=[{'path':rel,'sha256':'h','bytes':1} for rel in (b.SOURCES['R'],b.POOLS['R'],b.PARENTS['report']['R'])]
        checked=report.replay('R',inputs,raw,c);result=report.summary('R',raw,checked,c)
        self.assertEqual(result['empty_budgets'],[0,1,2]);self.assertEqual(len(result['rows']),257)
        self.assertFalse(result['fresh_item57_full_graph_replay']);self.assertTrue(result['all_forward_recurrences_checked'])
        raw['proof']['allocation']['rows'][3]['charge']+=1
        with self.assertRaises(AssertionError):report.replay('R',inputs,raw,c)

    def test_complete_publication_and_failure_dominance(self):
        inputs,ind,c=copy.deepcopy(self.data);c['fit_ids']=[0,1,2]
        for key in ('parent50_arms','parent56_arms','parent57_arms','parent59_arms'):
            c[key]['naming']=copy.deepcopy(c[key]['R'])
        c['parent57_arms']['naming']['cohort']='naming'
        for role in b.ROLES:
            c['role_private_files'][role].update({rel:'h' for rel in (b.SOURCES['naming'],b.POOLS['naming'],b.PARENTS[role]['naming'])})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);production=root/'production';out=root/'report';production.mkdir();out.mkdir()
            b.write(root/'contract.json',{});ch=b.sha(root/'contract.json');raws=[];checked_rows=[]
            for cohort in b.COHORTS:
                supplied=copy.deepcopy(inputs);supplied['parent']['cohort']=cohort
                raw={'schema':'gamma.required-owner-cap.arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
                     'contract_sha256':ch,'proof':run.execute(supplied,c,cohort),'seconds':1,'peak_rss_kib':1,
                     'phase_seconds':{'input':.1,'proof':.2},'read_receipts':[{'path':rel,'sha256':'h','bytes':1}
                     for rel in (b.SOURCES[cohort],b.POOLS[cohort],b.PARENTS['production'][cohort])]}
                (production/cohort).mkdir();b.write(production/cohort/'results.json',raw);raws.append(raw)
                supplied['parent']=ind;supplied['reads']=[{'path':rel,'sha256':'h','bytes':1}
                    for rel in (b.SOURCES[cohort],b.POOLS[cohort],b.PARENTS['report'][cohort])]
                checked=report.replay(cohort,supplied,raw,c);checked_rows.append(checked)
                b.write(out/(cohort+'-proof.json'),checked)
            b.write(production/'results.json',{'complete':True,'validation_loaded':False,'contract_sha256':ch,'seconds':2,'arms':raws})
            b.write(production/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':ch,'elapsed':3,'cleanup_seconds':.1,'returncodes':[0,0]})
            for cohort,raw,checked in zip(b.COHORTS,raws,checked_rows):
                result=report.summary(cohort,raw,checked,c)
                result.update(independent_receipt_sha256=b.sha(out/(cohort+'-proof.json')),
                    production_arm_sha256=b.sha(production/cohort/'results.json'),production_results_sha256=b.sha(production/'results.json'),
                    production_supervisor_sha256=b.sha(production/'supervisor.json'),report_worker_seconds=1,report_peak_rss_kib=1)
                b.write(out/(cohort+'.json'),result)
            with patch.object(report,'HERE',root),patch.object(report,'config_limits'),patch.object(b,'public_inputs'):
                result=report.combine(production,out,c,4,[0,0]);self.assertTrue(result['predictions']['P1'])
                report.publish(out,result);self.assertTrue(b.read(out/'results.json')['complete'])
                with self.assertRaises(AssertionError):report.combine(production,out,c,4,[False,0])
                b.write(production/'failure.json',{'complete':False})
                with self.assertRaises(AssertionError):report.combine(production,out,c,4,[0,0])

    def test_corrupt_ancestral_proof_and_bool_are_rejected(self):
        inputs,ind,c=copy.deepcopy(self.data);e=c['parent57_arms']['R']
        for field in ('owner_caps','capped_prefixes'):
            bad=copy.deepcopy(ind);bad[field]['0']=True
            with self.assertRaises(AssertionError):pr.validate(bad,'report',e,'old',set(inputs['texts']))
        bad=copy.deepcopy(inputs['parent']);bad['complete']=1
        with self.assertRaises(AssertionError):pr.validate(bad,'production',e,'old',set(inputs['texts']))

    def test_strict_readers_and_root_before_open(self):
        with self.assertRaises(AssertionError):b.parse('{"a":1,"a":2}')
        with self.assertRaises(ValueError):b.parse('{"a":NaN}')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c={'active':True,'work':str(root),'role_private_files':{'report':{rel:'h' for rel in (b.SOURCES['R'],b.POOLS['R'],b.PARENTS['report']['R'])}}}
            with patch.object(Path,'open',side_effect=AssertionError('must not open')) as opened:
                with self.assertRaises(AssertionError):b.Reader(c,root/'wrong','report','R')
                opened.assert_not_called()
            reader=b.Reader(c,root,'report','R')
            with self.assertRaises(AssertionError):reader.read(b.PARENTS['production']['R'])
            with self.assertRaises(AssertionError):reader.read('../outside')

    def test_failed_production_rejected_before_ancestral_reader(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b.write(root/'contract.json',{})
            with patch.object(report,'HERE',root),patch.object(report,'config_limits'),patch.object(b,'check_contract'), \
                 patch.object(report.resource,'setrlimit'),patch.object(report.os,'sched_setaffinity'), \
                 patch.object(report,'accepted_production',side_effect=AssertionError('failed production')), \
                 patch.object(b,'load_inputs') as load:
                with self.assertRaises(AssertionError):report.worker('R',root,root/'production',root,time.monotonic()+20)
                load.assert_not_called()
            self.assertFalse((root/'R.json').exists())
            self.assertFalse(b.read(root/'R-failure.json')['complete'])

    def test_failure_publication_deadline_no_later_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(report,'write') as write:
                with self.assertRaises(report.HardDeadline):report.withdraw_worker(root/'R.json',{},time.monotonic()-1)
                write.assert_not_called()
            report.publish(root,report.failure_result(ValueError()))
            self.assertIs(b.read(root/'results.json')['complete'],False)
            self.assertIn('No verdict',(root/'REPORT.md').read_text())


if __name__=='__main__':unittest.main()
