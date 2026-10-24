"""Tiny invented correctness and actual process fault tests; no large measurement."""
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import synthetic as s

STUB='''import json,os,subprocess,sys,time
from pathlib import Path
out=Path(sys.argv[1]);mode=sys.argv[2]
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
(out/'processes.json').write_text(json.dumps({'child':child.pid,'worker':os.getpid(),'group':os.getpgrp()}))
r={'complete':True,'spec_sha256':'invented','input_spec_sha256':'input','worker_seconds':.01,'computation_seconds':.01,'oracle_seconds':0,'fixtures':[{'name':n,'complete':True,'independent_all257_agree':True,'historical53_saved_fields_agree':True,'historical57_saved_fields_agree':True,'all_forward_recurrences_checked':True} for n in ['a','b']]}
(out/'worker-results.json').write_text(json.dumps(r))
(out/'results.json').write_text(json.dumps({'complete':True}))
if mode=='failure':sys.exit(4)
if mode=='timeout':time.sleep(30)
'''


def alive(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0] not in ('Z','X')
    except (FileNotFoundError,ProcessLookupError):return False

class SyntheticTests(unittest.TestCase):
    def test_oracle_inventory_is_exactly_the_registered19(self):
        counts=[unittest.defaultTestLoader.loadTestsFromName(name).countTestCases()
                for name in ('test_proof','test_caps','test_independent')]
        self.assertEqual(counts,[6,8,5])

    def tiny(self):
        import caps as p
        import independent
        old=s.original();texts={'0000':'ababc','0001':'abacd'};banned=set(texts.values())
        alphabet=list(old.ALPHABET);pool=sorted(set(p.parent.full._suffix.build_pool(texts,banned))|set(alphabet))
        q,transitions=old.generate_q(texts,pool)
        kwargs=dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=alphabet,alphabet=alphabet,D=old.D,
                    expected_source_hashes=p.parent.source_hashes(texts),expected_old_banned=banned)
        cert=p.check(**kwargs)
        checked=independent.check(**kwargs,expected_price_prefix_schedule=cert['price_prefix_schedule'],
            expected_count_streams=cert['count_streams'],expected_price_caps=cert['price_caps'],
            expected_base57_prefix_schedule=cert['base57']['owner_prefix_schedule'])
        base=checked['base57']['base'];lifted=base['lifted']
        earlier=json.loads(json.dumps({k:lifted[k] for k in ('old_charge','old_numerator','old_occurrences','occurrence_sha256','class_counts')}))
        earlier.update(path_numerator=sum(lifted['path_numerators'].values()),geometry=base['geometry'],
                          rows50=lifted['rows'],rows53=base['tightened']['rows'],
                          digests=base['digests'],reductions=base['reductions'],deltas=base['deltas'],
                          new_only_class_counts={str(k):v for k,v in base['new_only_class_counts'].items()})
        historical={key:earlier[key] for key in ('old_charge','old_numerator','old_occurrences','occurrence_sha256',
            'class_counts','path_numerator','geometry','rows50','rows53')}
        historical.update(rows57=cert['base57']['rows'],deltas_vs53=cert['base57']['deltas_vs53'],
            owner_caps=cert['base57']['owner_caps'],owner_entry_counts=cert['base57']['owner_entry_counts'],
            base_digests=base['digests'],digests=cert['base57']['digests'],
            independent_digests=checked['base57']['digests'],denominator=old.D)
        historical.update(pool_entries=len(pool),pool_string_bytes=sum(len(x.encode()) for x in pool),
            pool_sha256=old.digest(pool),q_generation_trie_transitions=transitions,q_sha256=old.digest(q))
        return old,texts,banned,cert,checked,historical,earlier

    def test_tiny_all257_comparison_and_corruption(self):
        old,texts,banned,cert,checked,historical,earlier=self.tiny()
        self.assertTrue(s.compare(cert,checked,historical,earlier)['independent_all257_agree'])
        transported=[json.loads(json.dumps(value)) for value in (cert,checked,historical,earlier)]
        self.assertEqual(s.compare(*transported),s.compare(cert,checked,historical,earlier))
        self.assertEqual(s.digest(cert),s.digest(transported[0]))
        for field in ('rows','price_caps','count_streams','forward','positions','arcs'):
            bad=copy.deepcopy(checked)
            if field=='rows':bad['rows'][0]['charge']+=1
            elif field=='price_caps':bad['price_caps']['0000'][0]+=1
            elif field=='count_streams':bad['count_streams']['0000'][0]['arcs']+=1
            elif field=='positions':bad['work']['production_forward_positions_checked']-=1
            elif field=='arcs':bad['work']['production_forward_candidates']-=1
            else:bad['production_forward_schedule_checked']=False
            with self.assertRaises(AssertionError):s.compare(cert,bad,historical,earlier)
        for key in ('rows50','rows53','rows57'):
            bad=copy.deepcopy(historical);bad[key][256]['integer_lower_bound']+=1
            with self.assertRaises(AssertionError):s.compare(cert,checked,bad,earlier)
        bad=copy.deepcopy(historical);bad['digests']['owner_top_entries_sha256']='0'*64
        with self.assertRaises(AssertionError):s.compare(cert,checked,bad,earlier)
        with self.assertRaises(AssertionError):s.same(0,False)

    def test_tiny_worker_full_pipeline(self):
        old,texts,banned,cert,checked,historical,earlier=self.tiny()
        fixtures=[('tiny_a',texts,banned),('tiny_b',texts,banned)]
        config={'input_spec_sha256':'invented-input','oracle_modules':['unused'],'oracle_tests':19}
        histories=[]
        for name,ts,bs in fixtures:
            histories.append(dict(historical,**old.fixture_metadata(name,ts,bs)))
        read=s.read
        def reading(path):
            if path==s.PARENT/'synthetic-results.json':return {'fixtures':histories}
            if path==s.EARLIER/'synthetic-results.json':return {'fixtures':[earlier,earlier]}
            return read(path)
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            try:
                with patch.object(s,'STARTED',time.monotonic()),patch.object(s,'verify',return_value=config),\
                     patch.object(s,'original',return_value=old),patch.object(old,'fixtures',return_value=fixtures),\
                     patch.object(s,'read',side_effect=reading),patch.object(s,'oracles',return_value=19),\
                     patch.object(s,'resources'):
                    s.worker(output,time.monotonic()+10,'invented')
            finally:signal.setitimer(signal.ITIMER_REAL,0)
            result=read(output/'worker-results.json')
            self.assertTrue(result['complete']);self.assertEqual(len(result['fixtures']),2)
            self.assertTrue(all(row['historical57_saved_fields_agree'] for row in result['fixtures']))
            self.assertEqual(len(result['fixtures'][0]['rows63']),257)
            self.assertEqual(result['fixtures'][0]['price_caps'],json.loads(json.dumps(cert['price_caps'])))

    def exercise(self,mode='success',fault=None):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'out';script=root/'stub.py';script.write_text(STUB)
            config={'input_spec_sha256':'input','inputs':{'fixtures':[{'name':'a'},{'name':'b'}]}}
            write=s.write;open_path=Path.open;unlink=Path.unlink;closes=[];failure_calls=[];unlink_calls=[];handles=[]
            class Log:
                def __init__(self,handle):self.handle=handle
                def fileno(self):return self.handle.fileno()
                def close(self):
                    closes.append(time.monotonic());self.handle.close()
                    if fault=='log':raise OSError('invented')
                    if fault=='cleanup':time.sleep(1)
            def opening(path,*a,**kw):
                handle=open_path(path,*a,**kw)
                if path.name=='worker.log':handles.append(handle)
                return Log(handle) if path.name=='worker.log' else handle
            def writing(path,value):
                if fault=='slow_failure' and path.name=='failure.json':failure_calls.append(path);time.sleep(1)
                if fault=='slow_failure' and failure_calls:raise AssertionError('No I/O after expired failure budget')
                write(path,value)
                if fault=='publication' and path.name=='results.json' and value['complete']:raise OSError('after complete write')
                if fault=='receipt' and path.name=='supervisor.json' and value['complete']:raise OSError('receipt')
            def unlinking(path,*args,**kwargs):
                if fault=='unlink' and path==out/'REPORT.md':
                    unlink_calls.append(path);time.sleep(1)
                return unlink(path,*args,**kwargs)
            cap=.25 if mode=='timeout' else 3
            try:
                with patch.object(s,'STARTED',time.monotonic()),patch.object(s,'SECONDS',cap),patch.object(s,'EMERGENCY',.1),\
                     patch.object(s,'verify',return_value=config),patch.object(s,'command',return_value=[sys.executable,str(script),str(out),mode]),\
                     patch.object(s,'write',side_effect=writing),patch.object(Path,'open',opening),patch.object(Path,'unlink',unlinking):
                    if mode!='success' or fault:
                        with self.assertRaisesRegex(RuntimeError,'incomplete'):s.main(out,'invented')
                    else:self.assertTrue(s.main(out,'invented')['complete'])
                ids=s.read(out/'processes.json');until=time.monotonic()+1
                while any(alive(ids[k]) for k in ('worker','child')) and time.monotonic()<until:time.sleep(.01)
                self.assertFalse(any(alive(ids[k]) for k in ('worker','child')))
                if mode!='success' or fault:
                    for name in ('results.json','supervisor.json'):
                        if (out/name).exists():self.assertFalse(s.read(out/name)['complete'])
                    if (out/'REPORT.md').exists():self.assertIn('No accepted',(out/'REPORT.md').read_text())
                if fault=='cleanup':self.assertEqual(len(closes),1)
                if fault=='slow_failure':self.assertEqual(len(failure_calls),1)
                if fault=='unlink':self.assertEqual(len(unlink_calls),1);self.assertFalse(closes)
            finally:
                for handle in handles:handle.close()
                if (out/'processes.json').exists():
                    try:os.killpg(s.read(out/'processes.json')['group'],signal.SIGKILL)
                    except ProcessLookupError:pass

    def test_actual_success_kills_descendants(self):self.exercise()
    def test_worker_failure_withdraws_partial_success(self):self.exercise('failure')
    def test_timeout_kills_group(self):self.exercise('timeout')
    def test_log_close_failure(self):self.exercise(fault='log')
    def test_cleanup_clock_is_not_refreshed(self):self.exercise(fault='cleanup')
    def test_slow_failure_write_does_not_continue(self):self.exercise('failure','slow_failure')
    def test_partial_complete_publication_withdrawn(self):self.exercise(fault='publication')
    def test_blocked_cleanup_unlink_cannot_leave_live_child(self):self.exercise(fault='unlink')
    def test_receipt_failure(self):self.exercise(fault='receipt')
    def test_import_time_is_inside_whole_guard(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(s,'STARTED',time.monotonic()-700),patch.object(s,'verify') as verify:
            with self.assertRaises(RuntimeError):s.main(Path(folder)/'out','invented')
            verify.assert_not_called()
    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(s,'STARTED',time.monotonic()),patch.object(s,'verify',return_value={}):
            path=Path(folder);s.write(path/'results.json',{'complete':True})
            with self.assertRaises(RuntimeError):s.main(path,'invented')
            self.assertTrue(s.read(path/'results.json')['complete'])

if __name__=='__main__':unittest.main()
