"""Public schema and invented transport checks; never opens private corpus."""
import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import adapter
import binding
import common as c
import decisions
import make_contract

class BindingTests(unittest.TestCase):
    def public_config(self):
        parent=c.read(c.LIT/binding.PUBLIC[0]);pins=copy.deepcopy(parent['code_hashes'])
        authorities={p:c.hashfile(c.LIT/p) for p in binding.PUBLIC};pins.update(authorities)
        return {'code_hashes':pins,'authorities':authorities,'private_inputs':{},'work':'/not-an-authorized-private-root'}
    def test_actual_public_parent_schema_and_character_provenance(self):
        config=self.public_config();parent,e,refs=binding.public_inputs(config)
        self.assertEqual(len(refs),10);self.assertEqual(len(e['arms']),12)
        ev=c.read(c.LIT/'lexfrac-v1/evidence/results.json')['arms']['flat']
        old=next(a for a in e['arms'] if a['arm']=='43N-U' and a['policy']=='canonical')
        self.assertEqual(ev['start_characters'],old['fit']['single_character_codes'])
        self.assertEqual(ev['start_fit'],old['fit']['selections']['total'])
        self.assertEqual(ev['final_characters'],round(ev['fit']['single_character_fraction']*ev['final_fit']))
        self.assertNotEqual(old['dictionary_sha256'],parent['dictionaries']['43N']['sha256'])
    def test_actual_adapter_public_prefix_reaches_only_declared_seed_boundary(self):
        cfg=self.public_config();parent,e,_=binding.public_inputs(cfg)
        bound=c.read(c.LIT/binding.PUBLIC[4]);index={(a['arm'],a['policy']):a for a in e['arms']}
        class PrivateBoundary(BaseException):pass
        reader=c.Reader(cfg);seen=[]
        def public_only(base,path,h):
            if Path(base).resolve()!=c.LIT.resolve():seen.append(path);raise PrivateBoundary()
            return reader(base,path,h)
        with self.assertRaises(PrivateBoundary):adapter.external(bound,parent,index,types.SimpleNamespace(c=types.SimpleNamespace(LIT=c.LIT)),public_only)
        self.assertEqual(seen,[adapter.SEED]);self.assertEqual(reader.private_reads,[])

    def test_unknown_top_field_rejected(self):
        config=self.public_config();original=c.Reader.__call__
        def read(reader,base,path,h):
            value=original(reader,base,path,h)
            if path==binding.PUBLIC[1]:value['private_debug']='invented'
            return value
        with patch.object(c.Reader,'__call__',read):
            with self.assertRaises(AssertionError):binding.public_inputs(config)
    def test_exact_reader_allowlist_hash_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=b'["invented"]';(root/'allowed.json').write_bytes(raw);h=c.sha(raw)
            r=c.Reader({'work':str(root),'code_hashes':{},'private_inputs':{'allowed.json':h}})
            self.assertEqual(r(root,'allowed.json',h),['invented'])
            for path in ('other.json','../allowed.json','/allowed.json'):
                with self.assertRaises(AssertionError):r(root,path,h)
            with self.assertRaises(AssertionError):r(root,'allowed.json','0'*64)
            (root/'allowed.json').unlink();(root/'target.json').write_bytes(raw);(root/'allowed.json').symlink_to(root/'target.json')
            with self.assertRaises(AssertionError):r(root,'allowed.json',h)
    def test_exact_activation_no_drift(self):
        value={'active':False,'historical_only':True};self.assertTrue(make_contract.activate(value,copy.deepcopy(value))['active'])
        with self.assertRaises(AssertionError):make_contract.activate({**value,'new':'drift'},value)
    def test_all_predicates_match_frozen54_on_public_arms(self):
        parent,e,refs=binding.public_inputs(self.public_config());r=c.shared('report')
        for a in e['arms']:
            anchor=a['arm'].split('-')[0];old=next(x for x in e['arms'] if x['arm']==anchor+'-U' and x['policy']==a['policy'])
            self.assertEqual(decisions.transfer(a,old,parent),r.transfer(a,old,parent))
            for name in ('R','seed13','best24','N','NCP'):
                self.assertEqual(decisions.gates(a,refs[name,a['policy']],parent,initial=name=='R'),r.gates(a,refs[name,a['policy']],parent,initial=name=='R'))
if __name__=='__main__':unittest.main()
