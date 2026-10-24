"""Invented400-source fixtures; no corpus or external evidence is read."""
import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import current_best as cb
import report


def put(root,path,value):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(value,sort_keys=True).encode();target.write_bytes(raw)
    return cb.digest(raw)


class Fixture:
    def __init__(self,root,stage='48',arm=None):
        self.public=root/'public';self.work=root/'private';self.stage=stage
        component,private,arms=cb.STAGES[stage];self.arm=arm or arms[0]
        self.paths={'evidence':component+'/evidence/results.json','parent_contract':component+'/contract.json',
                    'dictionary':private+'/run-v1/'+self.arm+'/dictionary.json','private_results':private+'/run-v1/results.json'}
        self.partition={'dev_fit':list(range(300)),'dev_val':list(range(300,400))}
        self.texts={str(i):'abcd' for i in range(400)}
        self.vocab=['a','bcd','ab','cd','b','c','d']
        seed_vocab=['a','b','c','d'];seed_sha=cb.digest(json.dumps(seed_vocab).encode())
        sourceq={pid:{'source_sha256':cb.digest(t.encode()),'passed':True} for pid,t in self.texts.items()}
        q={'arms':[{'arm':'scope_joint','width':8,'per_problem':copy.deepcopy(sourceq),
                    'qualification':{pid:{'passed':True} for pid in self.texts}}]}
        qhash=put(self.public,cb.QUAL,q)
        allhash=put(self.work,cb.SOURCE+'/sources.json',self.texts)
        fithash=cb.digest(b'opaque unaccessed fit carrier')
        phash=put(self.public,'cost-decomposition-v1/contract.json',{'partition':self.partition})
        self.parent={'parent_contract_sha256':phash,'qualification_receipt':cb.QUAL,
          'qualification_receipt_sha256':qhash,'seed':{'relative_path':cb.SOURCE,'dictionary':cb.SEED,
            'dictionary_sha256':seed_sha,'private_sha256':{'sources.json':allhash,'fit-sources.json':fithash}},
          'tail_quantile':.85,'tail_weight':10,'char_scale':32768}
        self.config={'active':True,'source_bound':True,'work':str(self.work),'partition':self.partition,
          'sources':{'all':{'path':cb.SOURCE+'/sources.json','sha256':allhash},
                     'fit':{'path':cb.SOURCE+'/fit-sources.json','sha256':fithash}},
          'dictionaries':{'43N':{'path':cb.SEED,'sha256':seed_sha}},'source_qualification':sourceq,
          'decoder_dependency_bytes':17}
        self.r=types.SimpleNamespace(c=types.SimpleNamespace(LIT=self.public,analyze=report.c.analyze),
          external_original_bans=lambda texts:set(texts.values()),encode=report.encode,aggregate=report.aggregate,
          anchor_current_best=report.anchor_current_best)
        self.seedrows=self.rows(seed_vocab)
        self.index={('43N-U','canonical'):{'dictionary_sha256':seed_sha,'per_problem':self.seedrows}}
        dictsha=put(self.work,self.paths['dictionary'],self.vocab)
        rows=self.rows(self.vocab);db=len(report.c.analyze.dictionary_bytes(self.vocab))
        minimal={pid:{k:row[k] for k in ('encodable','selections','actions','single_characters','packet_bytes')} for pid,row in rows.items()}
        recon={'start_fit':1200,'final_fit':600,'fit_programs_worse_than_start':0,'fit_programs_better_than_start':300}
        if stage=='48':recon.update(tail_programs=300 if self.arm=='tail' else 0,final_objective=6000 if self.arm=='tail' else 600)
        else:recon.update(start_characters=1200,final_characters=300,final_objective=32768*600+300 if self.arm=='lexnc' else 600)
        self.raw={'arm':self.arm,'dictionary_sha256':dictsha,'decoded':400,'illegal_entry_sha256':[],
                  'dictionary_bytes':db,'per_problem':minimal,**recon}
        public={'dictionary_sha256':dictsha,'decoded':400,'illegal_entry_sha256':[],**recon,
          'coverage':{'fit':300,'validation':100},'successor':True,'ready_vs_R':{'passed':True},'incremental_vs_seed':{'passed':True},
          'per_problem_validation_actions':{str(pid):3 for pid in self.partition['dev_val']}}
        for split,key in (('fit','dev_fit'),('validation','dev_val')):
            public[split]=cb.summary(report.aggregate(rows,self.partition[key],db,17))
        self.evidence={'schema':'gamma.'+component+'.evidence.v1','qualification_reused':cb.QUAL,
          'all_sources_qualified_by_receipt':True,'arms':{self.arm:public},'failed_arms':{},'replayed_arms':[self.arm],
          'exit_codes':{self.arm:0},'decoder_dependency_bytes':{'literals.py':11,'pass2/working/bitpack.py':6},
          'record_time_best':{'resolved':True,'replacement_allowed':True,'selected':self.arm,'eligible':[self.arm],
            'per_candidate':{self.arm:{'resolved':True,'passes':True,'checks':{'passed':True}}}}}
        self.retained={'exit_codes':{self.arm:0},'arms':[self.raw]}
        self.binding={'recorded_commit':'abcdef123','recorded_label':'invented selected arm',
          'comparison':{'kind':'external','stage':stage,'arm':self.arm}}
        self.seal()

    def rows(self,vocab):
        rows={}
        for pid,text in self.texts.items():
            ids=report.encode(text,vocab,'canonical');packet=report.c.analyze.encode(vocab,ids,8)
            rows[pid]={'encodable':True,'qualified_source':True,'source_sha256':cb.digest(text.encode()),'source_bytes':4,
              'selections':len(ids),'actions':len(ids)+1,'single_characters':sum(len(vocab[i])==1 for i in ids),'packet_bytes':len(packet)}
        return rows

    def seal(self):
        h=put(self.public,self.paths['parent_contract'],self.parent)
        self.retained['contract_sha256']=self.evidence['contract_sha256']=h
        self.evidence['results_sha256']=put(self.work,self.paths['private_results'],self.retained)
        put(self.public,self.paths['evidence'],self.evidence)
        for key,path in self.paths.items():
            root=self.public if key in ('evidence','parent_contract') else self.work
            self.binding[key]={'path':path,'sha256':cb.digest((root/path).read_bytes())}

    def resolve(self):return cb.resolve(self.binding,self.config,self.index,self.r)


class CurrentBestTests(unittest.TestCase):
    def test_two_policies_preserve_order_and_canonical_receipts_all_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            for stage,arm in (('48','tail'),('48','flat'),('51','lexnc'),('51','flat')):
                with self.subTest(stage=stage,arm=arm):
                    f=Fixture(Path(tmp)/(stage+arm),stage,arm);policies,meta=f.resolve()
                    self.assertTrue(meta['resolved'],meta);self.assertEqual(meta['decoded_policy_packets'],800)
                    a=policies['canonical'];b=policies['shortest_min_char']
                    self.assertEqual(a['validation']['actions']['total'],300)
                    self.assertEqual(a['validation']['single_character_codes'],100)
                    self.assertEqual(b['validation']['single_character_codes'],0)
                    self.assertNotEqual(a['per_problem']['0']['packet_sha256'],b['per_problem']['0']['packet_sha256'])
                    self.assertEqual(a['dictionary_sha256'],b['dictionary_sha256'])
                    self.assertEqual(a['fit']['package_with_decoder_dependencies'],a['fit']['package_bytes']+17)

    def test_corrupt_receipts_source_caps_and_acceptance_fail_closed(self):
        edits=[lambda f:f.raw['per_problem']['0'].__setitem__('single_characters',0),
               lambda f:f.raw.__setitem__('decoded',True),
               lambda f:f.evidence['exit_codes'].__setitem__(f.arm,False),
               lambda f:f.evidence['record_time_best'].__setitem__('selected','flat'),
               lambda f:f.evidence['record_time_best'].__setitem__('replacement_allowed',False),
               lambda f:f.evidence['failed_arms'].__setitem__(f.arm,{'failed':True}),
               lambda f:f.evidence['arms'][f.arm]['validation'].__setitem__('actions',301),
               lambda f:f.evidence['arms'][f.arm]['per_problem_validation_actions'].__setitem__('300',4),
               lambda f:f.config['source_qualification']['0'].__setitem__('source_sha256','0'*64),
               lambda f:f.index[('43N-U','canonical')]['per_problem']['0'].__setitem__('selections',1),
               lambda f:f.parent['seed'].__setitem__('dictionary_sha256','0'*64),
               lambda f:f.evidence['decoder_dependency_bytes'].__setitem__('literals.py',12)]
        with tempfile.TemporaryDirectory() as tmp:
            for i,edit in enumerate(edits):
                with self.subTest(i=i):
                    f=Fixture(Path(tmp)/str(i));edit(f);f.seal();policies,meta=f.resolve()
                    self.assertIsNone(policies);self.assertFalse(meta['resolved'])

    def test_paths_missing_unknown_and_hash_mismatch_no_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp));binding=copy.deepcopy(f.binding)
            for update in ({'comparison':{'kind':'external','stage':'99','arm':'tail'}},
                           {'dictionary':{'path':'../heldout.json','sha256':'0'*64}}):
                f.binding={**binding,**update}
                with patch.object(Path,'read_bytes',side_effect=AssertionError('must not read')):
                    self.assertIsNone(f.resolve()[0])
            f.binding=copy.deepcopy(binding);f.binding['evidence']['sha256']='0'*64
            self.assertIsNone(f.resolve()[0])
            f.binding=binding;(f.work/f.paths['dictionary']).unlink()
            self.assertIsNone(f.resolve()[0])
            self.assertEqual(cb.resolve(None,f.config,f.index,f.r)[1]['resolved'],False)
            f.binding=copy.deepcopy(binding);f.binding['comparison']={'kind':'anchor','anchor':'missing'}
            self.assertIsNone(f.resolve()[0])

    def test_anchor_delegation_and_baseexception_deadline(self):
        called=[]
        r=types.SimpleNamespace(anchor_current_best=lambda *args:(called.append(args) or {'anchor':'exact'}, {'resolved':True}))
        anchor={'comparison':{'kind':'anchor','anchor':'43N'}}
        self.assertEqual(cb.resolve(anchor,{}, {},r)[0],{'anchor':'exact'});self.assertEqual(len(called),1)
        class Deadline(BaseException):pass
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp))
            with patch.object(Path,'read_bytes',side_effect=Deadline('expired')):
                with self.assertRaises(Deadline):f.resolve()

    def test_reordered_dictionary_and_exact_body_ban_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp)/'order')
            reordered=['ab','cd','a','bcd','b','c','d']
            h=put(f.work,f.paths['dictionary'],reordered)
            f.raw['dictionary_sha256']=f.evidence['arms'][f.arm]['dictionary_sha256']=h
            f.seal()
            # Same set/N/package but different canonical C: stale parent rows
            # must fail even when every file identity is consistently rebound.
            self.assertIsNone(f.resolve()[0])
            f=Fixture(Path(tmp)/'ban');seen=[]
            def forbidden(texts):
                self.assertEqual(texts,f.texts);seen.append(len(texts));return {'ab'}
            f.r.external_original_bans=forbidden
            self.assertIsNone(f.resolve()[0]);self.assertEqual(seen,[400])


if __name__=='__main__':unittest.main()
