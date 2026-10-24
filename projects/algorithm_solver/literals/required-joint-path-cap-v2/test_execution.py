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
    # Frozen60 kernels produce invented receipts ONLY; execution never loads them.
    script='''import json,caps,independent
from test_caps import fixture
kw=fixture({'0':'abcde','1':'fghij','2':'klmno'},{'abcde','fghij','klmno'})
p=caps.check(**kw);i=independent.check(**kw,expected_prefix_schedule=p['all_prefix_schedule'],expected_base57_prefix_schedule=p['base57']['owner_prefix_schedule'])
print(json.dumps({'p':p,'i':i,'texts':kw['texts'],'pool':kw['old_pool'],'banned':sorted(kw['banned'])}))'''
    child=subprocess.run([sys.executable,'-B','-c',script],cwd=b.LIT/'joint-path-cap-v1',capture_output=True,text=True,check=True,timeout=20)
    f=b.parse(child.stdout);p60,i60=f['p'],f['i'];p,i=p60['base57'],i60['base57'];base=p['base'];tight=base['tightened'];texts=f['texts']
    geometry={'source_characters':sum(map(len,texts.values())),'full_groups':max(g for es in p['owner_top_entries'].values() for _,g,_ in es)+1,
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
    helper=b.module('required64_fixture_shape60','joint-path-cap-v1/report.py')
    raw60={**raw,'schema':'gamma.joint-path-cap.arm.v1','proof':p60,
        'bindings':{'source_hashes_sha256':b.digest(hashes),'bans_sha256':b.digest(f['banned'])}}
    exp['parent_certificate_sha256']='invented'
    context={**c,'parent57_evidence':{'sha256':'old'}}
    exp60=helper.summary('R',raw60,i60,context)
    c['parent60_arms']={'R':exp60}
    old_alloc=b.module('required64_fixture61','required-owner-cap-v1/allocation.py')
    rows61=old_alloc.independent(p['capped_prefixes'],p['shared_prefix'],cov['forced_source_ids'],exp['path_numerator'],exp['denominator'])['rows']
    c['parent61_arms']={'R':{'rows':rows61}}
    inputs['parent']=raw60
    return inputs,i60,c


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=fixture()

    def test_inherited_roles_and_fresh_pipeline(self):
        inputs,ind,c=copy.deepcopy(self.data);e=c['parent60_arms']['R']
        a=pr.validate(inputs['parent'],'production',e,c['parent57_arms']['R'],'old',set(inputs['texts']))
        z=pr.validate(ind,'report',e,c['parent57_arms']['R'],'old',set(inputs['texts']));self.assertEqual(a,z)
        proof=run.execute(inputs,c,'R');self.assertIn('12',proof['allocation']['owner57_prefix']);self.assertIn('12',proof['allocation']['owner61_prefix']);raw={'proof':proof,'contract_sha256':'new','seconds':1,'peak_rss_kib':1,'phase_seconds':{'input':.1,'proof':.2}}
        inputs['parent']=ind
        inputs['reads']=[{'path':rel,'sha256':'h','bytes':1} for rel in (b.SOURCES['R'],b.POOLS['R'],b.PARENTS['report']['R'])]
        checked=report.replay('R',inputs,raw,c);result=report.summary('R',raw,checked,c)
        self.assertEqual(result['empty_budgets'],[0,1,2]);self.assertEqual(len(result['rows']),257)
        self.assertFalse(result['fresh_item60_full_graph_replay']);self.assertTrue(result['all_forward_recurrences_checked'])
        raw['proof']['allocation']['rows'][3]['charge']+=1
        with self.assertRaises(AssertionError):report.replay('R',inputs,raw,c)

    def test_complete_publication_and_failure_dominance(self):
        inputs,ind,c=copy.deepcopy(self.data);c['fit_ids']=[0,1,2]
        for key in ('parent50_arms','parent56_arms','parent57_arms','parent59_arms','parent60_arms','parent61_arms'):
            c[key]['naming']=copy.deepcopy(c[key]['R'])
        c['parent57_arms']['naming']['cohort']='naming';c['parent60_arms']['naming']['cohort']='naming'
        for role in b.ROLES:
            c['role_private_files'][role].update({rel:'h' for rel in (b.SOURCES['naming'],b.POOLS['naming'],b.PARENTS[role]['naming'])})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);production=root/'production';out=root/'report';production.mkdir();out.mkdir()
            b.write(root/'contract.json',{});ch=b.sha(root/'contract.json');raws=[];checked_rows=[]
            for cohort in b.COHORTS:
                supplied=copy.deepcopy(inputs);supplied['parent']['cohort']=cohort
                raw={'schema':'gamma.required-joint-path-cap.arm.v2','cohort':cohort,'complete':True,'validation_loaded':False,
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
                self.assertEqual(set(result['arms'][0]['curves']),{'57','60','61','64'})
                for split in result['arms'][0]['split_rows']:
                    self.assertEqual(set(split),set(report.SPLIT_PUBLIC))
                    self.assertTrue(all(type(v) is int or v is None for v in split.values()))
                self.assertIn('Naming largest positive budget exceeds4',report.markdown(result))
                retained=b.read(out/'R.json');b.write(out/'R.json',dict(retained,source_text='unexpected'))
                with self.assertRaises(AssertionError):report.combine(production,out,c,4,[0,0])
                b.write(out/'R.json',retained)
                with self.assertRaises(AssertionError):report.combine(production,out,c,4,[False,0])
                b.write(production/'failure.json',{'complete':False})
                with self.assertRaises(AssertionError):report.combine(production,out,c,4,[0,0])

    def test_corrupt_ancestral_proof_and_bool_are_rejected(self):
        inputs,ind,c=copy.deepcopy(self.data);e=c['parent60_arms']['R']
        for field in ('all_caps','local_shared_prefixes'):
            bad=copy.deepcopy(ind);bad[field]['0']=True
            with self.assertRaises(AssertionError):pr.validate(bad,'report',e,c['parent57_arms']['R'],'old',set(inputs['texts']))
        bad=copy.deepcopy(inputs['parent']);bad['complete']=1
        with self.assertRaises(AssertionError):pr.validate(bad,'production',e,c['parent57_arms']['R'],'old',set(inputs['texts']))

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
            rel=b.SOURCES['R'];path=root/rel;path.parent.mkdir(parents=True);path.write_text('{"x":1}')
            c['role_private_files']['report'][rel]=b.sha(path)
            reader=b.Reader(c,root,'report','R');self.assertEqual(reader.read(rel),{'x':1})
            with patch.object(b,'MAX_BYTES',2):
                with self.assertRaises(AssertionError):reader.read(rel)
                with self.assertRaises(AssertionError):b.write(root/'oversize.json',{'x':1})
            self.assertFalse((root/'oversize.json').exists())
            path.write_text('{"x":2}')
            with self.assertRaises(AssertionError):reader.read(rel)
            actual=root/'actual.json';actual.write_text('{"x":1}');path.unlink();path.symlink_to(actual)
            with self.assertRaises(AssertionError):reader.read(rel)

    def test_actual_public_lineage_without_binder_or_private_reads(self):
        # Read-only accepted metadata; build(), Reader and private roots are not used.
        values={key:b.read(b.LIT/rel) for key,rel in b.PUBLIC.items()}
        arms={n:{row['cohort']:row for row in values[n]['arms']} for n in ('50','56','57','59','60','61')}
        c={'public_files':{rel:b.sha(b.LIT/rel) for rel in b.PUBLIC.values()},
            'fit_ids':values['50contract']['fit_ids'],'source_hashes':values['50contract']['source_hashes'],
            'denominator':1000000,'role_private_files':{role:{} for role in b.ROLES},
            **{'parent'+n+'_arms':rows for n,rows in arms.items()}}
        for role in b.ROLES:
            for cohort in b.COHORTS:
                for rel in (b.SOURCES[cohort],b.POOLS[cohort]):
                    c['role_private_files'][role][rel]=values['50contract']['private_files'][rel]
                c['role_private_files'][role][b.PARENTS[role][cohort]]=arms['60'][cohort][
                    'production_arm_sha256' if role=='production' else 'independent_receipt_sha256']
        with patch.object(b,'Reader',side_effect=AssertionError('No private reader')):
            b.public_inputs(c)
            bad=copy.deepcopy(c);bad['parent61_arms']['naming']['rows'][3]['charge']+=1
            with self.assertRaises(AssertionError):b.public_inputs(bad)

    def test_existing_direct_worker_artifacts_are_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'R-proof.json';target.write_text('existing proof')
            with patch.object(report.resource,'setrlimit'),patch.object(report.os,'sched_setaffinity'),patch.object(b,'load_inputs') as load:
                with self.assertRaises(AssertionError):report.worker('R',root,root/'run',root,time.monotonic()+20)
                load.assert_not_called()
            self.assertEqual(target.read_text(),'existing proof');self.assertFalse((root/'R-failure.json').exists())

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

    def test_public_production_corruption_rejected_before_ancestral_read(self):
        inputs,_,c=copy.deepcopy(self.data);c['fit_ids']=[0,1,2]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);production=root/'production';(production/'R').mkdir(parents=True)
            b.write(root/'contract.json',c);contract=b.sha(root/'contract.json')
            raw={'schema':'gamma.required-joint-path-cap.arm.v2','cohort':'R','complete':True,'validation_loaded':False,
                'contract_sha256':contract,'proof':run.execute(inputs,c,'R'),'seconds':1,'peak_rss_kib':1,
                'phase_seconds':{'input':.1,'proof':.2},'read_receipts':[{'path':rel,'sha256':'h','bytes':1}
                    for rel in (b.SOURCES['R'],b.POOLS['R'],b.PARENTS['production']['R'])]}
            b.write(production/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':contract,
                'elapsed':3,'cleanup_seconds':.1,'returncodes':[0,0]})
            for index,field in enumerate(('parent_scientific_proof_sha256','source_identity_sha256','banned_set_sha256','allocation','prefix_value','prefix_key')):
                corrupt=copy.deepcopy(raw)
                if field=='allocation':corrupt['proof'][field]['rows'][3]['charge']+=1
                elif field=='prefix_value':corrupt['proof']['allocation']['owner57_prefix']['12']+=1
                elif field=='prefix_key':
                    values=corrupt['proof']['allocation']['owner61_prefix'];values['012']=values.pop('12')
                else:corrupt['proof'][field]='0'*64
                b.write(production/'R/results.json',corrupt)
                b.write(production/'results.json',{'complete':True,'validation_loaded':False,'contract_sha256':contract,
                    'seconds':2,'arms':[corrupt]})
                output=root/str(index);output.mkdir()
                # Constrain this guard fixture to one otherwise valid arm. A
                # malformed second arm must not mask a removed pre-read guard.
                with patch.object(report,'HERE',root),patch.object(report,'config_limits'),patch.object(b,'check_contract'),\
                     patch.object(report,'COHORTS',('R',)),\
                     patch.object(b,'public_inputs'),patch.object(report.resource,'setrlimit'),\
                     patch.object(report.os,'sched_setaffinity'),\
                     patch.object(b,'load_inputs',side_effect=RuntimeError('ancestral reader must not be reached')) as load:
                    with self.assertRaises(AssertionError):report.worker('R',root,production,output,time.monotonic()+20)
                    load.assert_not_called()
                self.assertFalse((output/'R.json').exists())

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
