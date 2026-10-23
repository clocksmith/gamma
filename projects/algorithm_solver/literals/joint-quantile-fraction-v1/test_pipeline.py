"""Invented two-character inputs only; no real source/q loader is called."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import common as c
import report
import run


class PipelineTests(unittest.TestCase):
    def test_six_points_and_independent_replay(self):
        texts={str(p):'ab' for p in range(300)}
        q={p:[[i+1]*11 for i in range(2)] for p in texts}
        index=c.mechanism.parent.Index(texts,set());D=1000
        prior={'certificate':index.certificate(q,256,D)}
        counts={'pool_entries':index.distinct_allowed_entries,'implicit_groups':len(index.base.groups),
                'length_pieces':len(index.pieces),'source_characters':len(index.base.positions),'exact_ban_occurrences':0}
        contract={'active':True,'limits':{'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10,
                    'arm_cores':{'R':[4],'naming':[5]},'address_space_bytes':8*1024**3},
                  'denominator':D,'sources':{'R':'source','naming':'source'},'parent_q':{'R':'q','naming':'q'},
                  'private_files':{'source':'source-hash','q':'q-hash'}}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'worker';source.mkdir();out=root/'replay';out.mkdir()
            c.write(root/'contract.json',contract)
            with patch.object(c,'HERE',root),patch.object(c,'check_contract'),patch.object(c,'load_cohort',return_value=(index,q,prior,counts)):
                start=time.monotonic();run.arm('R',root,source,start+60)
                a=json.loads((source/'R/results.json').read_text())
                self.assertEqual(len(a['points']),6)
                # The second arm is never loaded in this focused worker replay.
                other={**a,'cohort':'naming'}
                raw={'complete':True,'validation_loaded':False,'contract_sha256':c.sha(root/'contract.json'),
                     'seconds':time.monotonic()-start,'arms':[a,other]}
                c.write(source/'results.json',raw)
                c.write(source/'supervisor.json',{'complete':True,'phase':'production','contract_sha256':raw['contract_sha256'],
                        'elapsed':raw['seconds']+.1,'cleanup_seconds':.01,'returncodes':[0,0]})
                report.replay_arm('R',root,source,out,time.monotonic()+60)
                replay=json.loads((out/'R.json').read_text())
                self.assertTrue(replay['independent_cardinality_assignment_and_pool_replay'])
                self.assertEqual(len(replay['points']),6)
                self.assertTrue(all(p['joint_integer_lower_bound']==p['unrestricted_integer_lower_bound'] for p in replay['points']))
                # Even a hash-rebound missing median case must fail the pure checker.
                path=source/'R/point-0.json';proof=json.loads(path.read_text());proof['assignments']['median_cases'].pop()
                c.write(path,proof);a['points'][0]['proof_sha256']=c.sha(path)
                c.write(source/'R/results.json',a);raw['arms'][0]=a;c.write(source/'results.json',raw)
                with self.assertRaises(AssertionError):report.replay_arm('R',root,source,out,time.monotonic()+60)
                self.assertTrue((out/'R-failure.json').exists())


if __name__=='__main__':unittest.main()
