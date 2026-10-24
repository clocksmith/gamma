"""Invented inputs only; copied historical fixture supplies canonical receipts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import common as c
import adapter

class Fixture:
    def __init__(self,root):
        self.old=c.shared('test_current_best');self.f=self.old.Fixture(root,'51','flat')
        f=self.f;vocab=['a','b','c','d'];raw=json.dumps(vocab,separators=(',',':')).encode()
        path=f.work/adapter.SEED;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);h=c.sha(raw)
        f.parent['seed']['dictionary_sha256']=h;f.config['dictionaries']['43N']['sha256']=h
        binary=f.r.c.analyze.dictionary_bytes(vocab);rewritten=(json.dumps(vocab,sort_keys=True,indent=2)+'\n').encode()
        base={'dictionary_sha256':c.sha(rewritten),'dictionary_binary_sha256':c.sha(binary),'dictionary_bytes':len(binary),
          'entries':4,'character_entries':4,'per_problem':f.seedrows}
        f.index={(view,policy):copy.deepcopy(base) for view in ('43N-U','43N-S') for policy in adapter.POLICIES}
        f.seal();self.reads=[];self.allowed={adapter.SEED,adapter.SOURCE+'/sources.json',f.paths['dictionary'],f.paths['private_results']}
    def reader(self,base,path,h):
        if Path(base)==self.f.work:
            assert path in self.allowed;self.reads.append(path)
        else:assert Path(base)==self.f.public
        return self.old.cb.read(base,path,h)
    def run(self):return adapter.external(self.f.binding,self.f.config,self.f.index,self.f.r,self.reader)

class AdapterTests(unittest.TestCase):
    def test_carrier_chain_and_independent_minC(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp));policies,meta=f.run()
            self.assertTrue(meta['resolved']);self.assertEqual(set(f.reads),f.allowed);self.assertEqual(len(f.reads),4)
            identity=meta['seed_carrier_identity'];self.assertNotEqual(identity['original_json_sha256'],identity['item54_rewritten_json_sha256'])
            self.assertEqual(policies['canonical']['validation']['single_character_codes'],100)
            self.assertEqual(policies['shortest_min_char']['validation']['single_character_codes'],0)
            self.assertEqual(policies['canonical']['validation']['actions']['total'],300)
            self.assertEqual(meta['decoded_policy_packets'],800)
    def test_each_identity_and_order_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i,key in enumerate(('dictionary_sha256','dictionary_binary_sha256','dictionary_bytes','character_entries','entries')):
                f=Fixture(Path(tmp)/str(i));row=f.f.index['43N-U','canonical'];row[key]='0'*64 if isinstance(row[key],str) else row[key]+1
                with self.assertRaises(AssertionError):f.run()
            f=Fixture(Path(tmp)/'reorder');original=f.reader
            def reorder(base,path,h):
                value=original(base,path,h)
                return list(reversed(value)) if path==adapter.SEED else value
            f.reader=reorder
            with self.assertRaises(AssertionError):f.run()
    def test_public_acceptance_blocks_all_private_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp));f.f.evidence['record_time_best']['replacement_allowed']=False;f.f.seal()
            with self.assertRaises(AssertionError):f.run()
            self.assertEqual(f.reads,[])
    def test_canonical_character_receipts_strict_not_minC(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i,edit in enumerate((lambda f:f.raw.__setitem__('final_characters',0),lambda f:f.raw.__setitem__('start_characters',0),lambda f:f.raw['per_problem']['0'].__setitem__('single_characters',0),lambda f:f.evidence['arms']['flat']['validation'].__setitem__('single_character_fraction',0))):
                f=Fixture(Path(tmp)/str(i));edit(f.f);f.f.seal()
                with self.assertRaises(AssertionError):f.run()
    def test_body_bans_and_duplicate_dictionary_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Fixture(Path(tmp)/'bans');f.f.r.external_original_bans=lambda texts:{'ab'}
            with self.assertRaises(AssertionError):f.run()
            f=Fixture(Path(tmp)/'dup');original=f.reader
            def duplicate(base,path,h):
                value=original(base,path,h)
                return [*value,value[0]] if path==adapter.SEED else value
            f.reader=duplicate
            with self.assertRaises(AssertionError):f.run()

if __name__=='__main__':unittest.main()
