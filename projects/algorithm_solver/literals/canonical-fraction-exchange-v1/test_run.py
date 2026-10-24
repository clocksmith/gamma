"""Invented runner fixtures; no population files or sandbox execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import common as c
import codec
import run
import search


def fixture(root):
    texts={str(i):'abx' if i%2 else 'cdx' for i in range(4)}
    pool=['a','ab','b','c','cd','d','x','xy'];seed=['a','b','c','d','x'];bans=set(texts.values())
    g=search.CheckedGraph(texts,pool,seed,capacity=6,banned=bans,decoder_bytes=13010)
    parent=codec.measure(g,seed,root/'parent-seed',13010)
    caps={p:{'source_sha256':hashlib.sha256(t.encode()).hexdigest(),'N':g.caps[p]} for p,t in texts.items()}
    source_sha=c.digest(texts)
    rows={p:{'source_sha256':r['source_sha256'],'N':r['selections'],'C':r['characters'],'packet_sha256':r['packet_sha256']} for p,r in parent['per_problem'].items()}
    shadow={'arms':[{'cohort':'R','source_sha256':source_sha,'witnesses':{'seed':{'canonical_min_N':{'per_problem':rows}}}}]}
    c.write(root/'shadow.json',shadow)
    contract={'active':True,'limits':{'production_seconds':1200,'address_space_bytes':8*1024**3,'arm_cores':{'R':[4],'naming':[5]}},
              'pool':{'capacity':6},'construction':{},'canonical_seed_caps':{'R':caps},'decoder_dependency_bytes':13010,
              'canonical_parent_evidence':'shadow.json','search':{'seconds':600,'evaluations':1000,'epochs':2,'shortlist':4,'expected_free_slots':1}}
    inputs={'texts':texts,'candidates':pool,'seed':seed,'bans':bans,'parent_arm':{'arcs':g.arcs,'transitions':g.transitions},
            'bindings':{'source_sha256':source_sha},'pool_counts':{'entries':len(pool)},'original_reference_hashes':{'seed':c.sha(root/'parent-seed/dictionary.json')}}
    return contract,inputs


class RunnerTests(unittest.TestCase):
    def test_invented_full_worker_packet_outputs_and_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config,inputs=fixture(root);c.write(root/'contract.json',config);out=root/'out';out.mkdir()
            with patch.object(c,'HERE',root),patch.object(c,'LIT',root),patch.object(c,'check_contract'),patch.object(c,'load_cohort',return_value=inputs):
                run.arm('R',root,out,time.monotonic()+10)
            result=json.loads((out/'R/results.json').read_text());self.assertTrue(result['complete']);self.assertFalse(result['validation_loaded'])
            self.assertEqual(result['search']['final_score'],result['incumbents'][-1]['witness']['score'])
            self.assertGreater(len(result['incumbents']),1)
            for item in result['incumbents']:
                w=item['witness'];self.assertEqual(w['seed_cap_regressions'],0)
                for p,row in w['per_problem'].items():self.assertLessEqual(row['selections'],config['canonical_seed_caps']['R'][p]['N'])
            self.assertEqual(result['seed_caps_sha256'],c.sha(out/'R/seed-caps.json'))
            self.assertFalse((out/'R/failure.json').exists())

    def test_wrong_seed_cap_identity_stops_before_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config,inputs=fixture(root);config['canonical_seed_caps']['R']['0']['N']+=1
            c.write(root/'contract.json',config);out=root/'out';out.mkdir()
            with patch.object(c,'HERE',root),patch.object(c,'LIT',root),patch.object(c,'check_contract'),patch.object(c,'load_cohort',return_value=inputs),patch.object(search,'execute',side_effect=AssertionError('search must not start')) as optimizer:
                with self.assertRaises(AssertionError):run.arm('R',root,out,time.monotonic()+10)
                optimizer.assert_not_called()
            self.assertEqual(json.loads((out/'R/failure.json').read_text())['phase'],'graph');self.assertFalse((out/'R/results.json').exists())

    def test_refused_existing_worker_preserves_old_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'out';(out/'R').mkdir(parents=True);c.write(out/'R/results.json',{'old_complete':True})
            old=(out/'R/results.json').read_bytes()
            with self.assertRaises(FileExistsError):run.arm('R',root,out,time.monotonic()+10)
            self.assertEqual((out/'R/results.json').read_bytes(),old);self.assertFalse((out/'R/failure.json').exists())


if __name__=='__main__':unittest.main()
