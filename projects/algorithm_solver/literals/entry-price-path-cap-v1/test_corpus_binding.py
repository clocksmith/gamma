"""Invented carrier/loader checks and accepted public metadata; no binder run."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
import binding as b
import make_contract as contract


class BindingTests(unittest.TestCase):
    def test_json_roundtrip_types_and_key_collisions(self):
        values={i:i*i for i in range(16)}
        self.assertEqual(b.digest(values),b.digest(json.loads(json.dumps(values))))
        with self.assertRaises(AssertionError):b.strict_equal(0,False)
        with self.assertRaises(AssertionError):b.normalized({1:0,'1':1})
        with self.assertRaises(AssertionError):b.parse('{"a":1,"a":2}')
        with self.assertRaises(ValueError):b.parse('{"a":NaN}')

    def test_distinct_carrier_limits_hash_and_write_preservation(self):
        self.assertEqual(b.MAX_BYTES,64*1024**2)
        self.assertEqual(b.CARRIER_MAX_BYTES,256*1024**2)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'carrier.json';raw=b'{"value":"12345678"}'
            path.write_bytes(raw)
            c={'active':True,'work':str(root),'private_files':{'carrier.json':hashlib.sha256(raw).hexdigest()}}
            with patch.object(b,'WORK',str(root)),patch.object(b,'MAX_BYTES',8),patch.object(b,'CARRIER_MAX_BYTES',64):
                self.assertEqual(b.read(path),{'value':'12345678'})
                self.assertEqual(b.sha(path),hashlib.sha256(raw).hexdigest())
                with self.assertRaises(AssertionError):b.checked_bytes(c,root,'carrier.json')
                before=path.read_bytes()
                with self.assertRaises(AssertionError):b.write(path,{'value':'x'*100})
                self.assertEqual(path.read_bytes(),before);self.assertFalse(path.with_name(path.name+'.tmp').exists())
            with patch.object(b,'CARRIER_MAX_BYTES',8):
                with self.assertRaises(AssertionError):b.read(path)
                with self.assertRaises(AssertionError):b.sha(path)

    def test_wrong_root_precedes_private_stat_or_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            c={'active':True,'work':str(root),'private_files':{'allowed.json':'0'*64}}
            with patch.object(b,'WORK',str(root)),patch.object(Path,'resolve') as resolve,patch.object(Path,'open') as opened:
                with self.assertRaises(AssertionError):b.checked_bytes(c,root/'wrong','allowed.json')
                resolve.assert_not_called();opened.assert_not_called()
            path=root/'allowed.json';actual=root/'other.json';actual.write_text('{}');path.symlink_to(actual)
            with patch.object(b,'WORK',str(root)):
                with self.assertRaises(AssertionError):b.checked_bytes(c,root,'allowed.json')
                with self.assertRaises(AssertionError):b.checked_bytes(c,root,'undeclared.json')

    def test_loader_exact_five_invented_files_and_signed_q(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);pool=sorted(b.ALPHABET);texts={'1':'ab'};seed=['a','b']
            paths={'sources':'sources.json','seed':'seed.json','pool':'pool.json','q':'q.npy'}
            for name,value in (('sources.json',texts),('seed.json',seed),('pool.json',pool)):b.write(root/name,value)
            q=io.BytesIO();np.save(q,np.array([3,4],dtype=np.int64));(root/'q.npy').write_bytes(q.getvalue())
            private={name:b.sha(root/name) for name in paths.values()}
            certificate={'invented':1}
            old={'cohort':'R','mode':'flex256','capacity':256,'mandatory_entries':0,'validation_loaded':False,
                'fit_source_sha256':private['sources.json'],'pool_sha256':private['pool.json'],'pool_entries':len(pool),
                'maximum_entry_length':1,'occurrences':2,'shared_learned_entries':0,'seed_extra_entries':0,
                'seed_extras_sha256':b.digest([]),'optimization':{'certificate':certificate}}
            expected={key:old[key] for key in ('fit_source_sha256','pool_sha256','pool_entries','maximum_entry_length',
                'occurrences','shared_learned_entries','seed_extra_entries','seed_extras_sha256')}
            expected['certificate']=certificate
            b.write(root/'old.json',{'contract_sha256':'old','validation_loaded':False,'arms':[old,{'cohort':'naming'}]})
            private['old.json']=b.sha(root/'old.json')
            hashes={'1':hashlib.sha256(b'ab').hexdigest()};banned={'ab'}
            bindings={'source_sha256':private['sources.json'],'seed_sha256':private['seed.json'],
                'pool_sha256':private['pool.json'],'q_sha256':private['q.npy'],'old_private_results_sha256':private['old.json'],
                'source_hashes_sha256':b.digest(hashes),'bans_sha256':b.digest(['ab']),'banned_entries':1,
                'old_evidence_sha256':'e28','full_evidence_sha256':'e35'}
            c={'active':True,'work':str(root),'cohorts':{'R':paths},'private_files':private,'old_private_results':'old.json',
                'parent_contracts':{'28':{'sha256':'old'}},'old_arms':{'R':expected},'fit_ids':[1],'source_hashes':{'R':hashes},
                'denominator':1000000,'full_shape':{'R':{}},'parent50_arms':{'R':{'bindings_sha256':b.digest(bindings),'banned_set_sha256':b.digest(['ab'])}},
                'public_files':{'all-length-fraction-v1/evidence/results.json':'e28','length-sensitive-fraction-v1/evidence/results.json':'e35'}}
            with patch.object(b,'WORK',str(root)),patch.object(b,'check_contract'),patch.object(b,'parse_bans',return_value=banned),\
                 patch.object(b,'checked_bytes',wraps=b.checked_bytes) as reads:
                got=b.load_inputs(c,root,'R',time.monotonic()+10)
                self.assertEqual([call.args[2] for call in reads.call_args_list],['old.json','sources.json','seed.json','pool.json','q.npy'])
                self.assertEqual(got['q'],[3,4]);self.assertEqual(got['bindings'],bindings)
            for dtype in (np.uint64,np.int32):
                raw=io.BytesIO();np.save(raw,np.array([3,4],dtype=dtype))
                with self.assertRaises(AssertionError):b.load_q(raw.getvalue(),2)
            with self.assertRaises(AssertionError):b.load_q(q.getvalue()+b'trailing',2)

    def test_parser_deadline_kills_without_waiting(self):
        class Deadline(BaseException):pass
        proc=Mock();proc.communicate.side_effect=Deadline()
        with patch.object(b.subprocess,'Popen',return_value=proc):
            with self.assertRaises(Deadline):b.parse_bans({'p':'invented'},time.monotonic()+1)
        proc.kill.assert_called_once();proc.wait.assert_not_called()

    def test_accepted_synthetic_public_receipts_and_corruptions(self):
        spec=b.read(b.HERE/'synthetic-spec.json');result=b.read(b.HERE/'synthetic-results.json')
        sup=b.read(b.HERE/'synthetic-supervisor.json');h=b.sha(b.HERE/'synthetic-spec.json')
        b.accepted_synthetic(spec,result,sup,h)
        for key,value in (('exit_code',False),('seconds',float('nan')),('complete',False),('spec_sha256','0'*64)):
            bad=copy.deepcopy(sup);bad[key]=value
            with self.assertRaises(AssertionError):b.accepted_synthetic(spec,result,bad,h)
        bad=copy.deepcopy(result);bad['fixtures'][0]['all_forward_recurrences_checked']=False
        with self.assertRaises(AssertionError):b.accepted_synthetic(spec,bad,sup,h)

    def test_context61_public_only_and_drift(self):
        c=b.read(b.LIT/'joint-path-cap-v1/contract.json')
        paths={'context61_contract':'required-owner-cap-v1/contract.json',
               'context61_evidence':'required-owner-cap-v1/evidence/results.json'}
        for key,rel in paths.items():
            c[key]={'path':rel,'sha256':b.sha(b.LIT/rel)};c['public_files'][rel]=c[key]['sha256']
        for name in ('production-supervisor.json','report-supervisor.json'):
            rel='required-owner-cap-v1/evidence/'+name;c['public_files'][rel]=b.sha(b.LIT/rel)
        evidence=b.read(b.LIT/paths['context61_evidence']);c['context61_arms']={a['cohort']:a for a in evidence['arms']}
        with patch.object(b,'checked_bytes',side_effect=AssertionError('no private reads')):
            b.verify_context61(c)
            bad=copy.deepcopy(c);bad['context61_arms']['R']['rows'][3]['charge']+=1
            with self.assertRaises(AssertionError):b.verify_context61(bad)

    def test_exact_activation_and_conflicting_pins(self):
        pending={'active':False,'code_hashes':{},'runtime_files':{},'definition':{i:i for i in range(13)}}
        loaded=json.loads(json.dumps(pending));active=contract.activate(pending,loaded)
        self.assertIs(active['active'],True);self.assertIs(loaded['active'],False)
        for bad in (pending|{'active':True},pending|{'extra':1}):
            with self.assertRaises(AssertionError):contract.activate(bad,loaded)
        with self.assertRaises(AssertionError):contract.merge_pins({'x':'a'},{'x':'b'})


if __name__=='__main__':unittest.main()
